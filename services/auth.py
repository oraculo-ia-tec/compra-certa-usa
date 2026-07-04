"""Serviço de autenticação rodando diretamente no Streamlit (sem API externa)."""
import random
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from models.models import User, UserStatus
from models.database import get_session
from services.security import (
    verify_password, hash_password,
    create_access_token, create_refresh_token,
    create_password_reset_token, decode_token,
)
from loguru import logger
from jose import JWTError

CODE_EXPIRY_MINUTES = 15
MAX_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 120


def _now() -> datetime:
    """Retorna datetime UTC sem timezone (naive) — compatível com SQLite."""
    return datetime.utcnow()


def _is_expired(expires_at: Optional[datetime]) -> bool:
    """Compara dois datetimes de forma segura, normalizando para naive UTC."""
    if expires_at is None:
        return False
    now = _now()
    if expires_at.tzinfo is not None:
        expires_at = expires_at.replace(tzinfo=None)
    return expires_at < now


class AuthError(Exception):
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code
        super().__init__(message)


def _generate_code() -> str:
    return f"{random.SystemRandom().randint(0, 99_999_999):08d}"


def _hash_code(code: str) -> str:
    return bcrypt.hashpw(code.encode(), bcrypt.gensalt()).decode()


def _verify_code(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def login(email: str, password: str, ip: Optional[str] = None) -> dict:
    db: Session = get_session()
    try:
        user = db.query(User).filter(User.email == email).first()

        if not user or not verify_password(password, user.hashed_password):
            raise AuthError("E-mail ou senha incorretos.", 401)

        if user.status == UserStatus.PENDING:
            raise AuthError("Conta ainda não confirmada. Verifique seu e-mail.", 403)
        if user.status == UserStatus.INACTIVE:
            raise AuthError("Conta desativada. Entre em contato com o suporte.", 403)
        if user.status == UserStatus.BANNED:
            raise AuthError("Conta bloqueada por violação dos termos de uso.", 403)

        user.last_login_at = _now()
        if ip:
            user.last_login_ip = ip
        db.commit()

        return {
            "access_token": create_access_token(user.id),
            "refresh_token": create_refresh_token(user.id),
            "token_type": "bearer",
            "user_id": user.id,
            "full_name": user.full_name,
            "role": user.role.value,
            "status": user.status.value,
            "is_first_access": user.is_first_access,
            "avatar_url": user.avatar_url,
        }
    finally:
        db.close()


def register(full_name: str, email: str, password: str, avatar_b64: Optional[str] = None) -> dict:
    db: Session = get_session()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise AuthError("E-mail já cadastrado. Use outro e-mail ou faça login.", 409)

        code = _generate_code()
        code_hash = _hash_code(code)
        now = _now()

        user = User(
            full_name=full_name,
            email=email,
            hashed_password=hash_password(password),
            status=UserStatus.PENDING,
            is_email_confirmed=False,
            verification_code=code_hash,
            verification_code_expires_at=now + timedelta(minutes=CODE_EXPIRY_MINUTES),
            verification_attempts=0,
            last_code_sent_at=now,
            avatar_url=avatar_b64,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"[auth] Usuário cadastrado: {email}")

        try:
            from services.email_service import send_verification_code_email
            sent = send_verification_code_email(email, full_name, code)
            if not sent:
                logger.warning(f"[auth] E-mail NÃO enviado para {email}")
        except Exception as e:
            logger.error(f"[auth] Exceção ao enviar e-mail para {email}: {e}")

        return {"email": user.email, "full_name": user.full_name}
    finally:
        db.close()


def verify_code(email: str, code: str) -> dict:
    db: Session = get_session()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise AuthError("Usuário não encontrado.", 404)

        if user.status == UserStatus.ACTIVE:
            raise AuthError("Conta já está ativa.", 400)

        if user.verification_attempts >= MAX_ATTEMPTS:
            raise AuthError("Muitas tentativas incorretas. Solicite um novo código.", 429)

        if not user.verification_code:
            raise AuthError("Nenhum código pendente. Solicite um novo código.", 400)

        if _is_expired(user.verification_code_expires_at):
            raise AuthError("Código expirado. Solicite um novo código.", 400)

        if not _verify_code(code.strip(), user.verification_code):
            user.verification_attempts += 1
            remaining = MAX_ATTEMPTS - user.verification_attempts
            db.commit()
            if remaining <= 0:
                raise AuthError("Código incorreto. Limite de tentativas atingido. Solicite um novo código.", 429)
            raise AuthError(f"Código incorreto. {remaining} tentativa(s) restante(s).", 400)

        user.status = UserStatus.ACTIVE
        user.is_email_confirmed = True
        user.verification_code = None
        user.verification_code_expires_at = None
        user.verification_attempts = 0
        db.commit()
        logger.info(f"[auth] Conta ativada: {email}")
        return {"email": user.email, "full_name": user.full_name}
    finally:
        db.close()


def resend_verification_code(email: str) -> dict:
    db: Session = get_session()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise AuthError("E-mail não encontrado.", 404)
        if user.status == UserStatus.ACTIVE:
            raise AuthError("Conta já está ativa.", 400)
        if user.status == UserStatus.BANNED:
            raise AuthError("Conta bloqueada.", 403)

        if user.last_code_sent_at:
            last_sent = user.last_code_sent_at
            if last_sent.tzinfo is not None:
                last_sent = last_sent.replace(tzinfo=None)
            elapsed = (_now() - last_sent).total_seconds()
            if elapsed < RESEND_COOLDOWN_SECONDS:
                wait = int(RESEND_COOLDOWN_SECONDS - elapsed)
                raise AuthError(f"Aguarde {wait} segundos antes de solicitar novo código.", 429)

        code = _generate_code()
        now = _now()
        user.verification_code = _hash_code(code)
        user.verification_code_expires_at = now + timedelta(minutes=CODE_EXPIRY_MINUTES)
        user.verification_attempts = 0
        user.last_code_sent_at = now
        db.commit()
        logger.info(f"[auth] Novo código gerado para {email}")

        try:
            from services.email_service import send_verification_code_email
            send_verification_code_email(email, user.full_name, code)
        except Exception as e:
            logger.error(f"[auth] Erro ao reenviar código para {email}: {e}")

        return {"email": email}
    finally:
        db.close()


def activate_account(token: str) -> dict:
    """Mantido para compatibilidade com seeds admin."""
    db: Session = get_session()
    try:
        try:
            payload = decode_token(token)
            if payload.get("type") != "activation":
                raise AuthError("Token inválido.")
        except JWTError:
            raise AuthError("Token inválido ou expirado.")

        user = db.query(User).filter(User.activation_token == token).first()
        if not user:
            raise AuthError("Token não encontrado ou já utilizado.")

        if _is_expired(user.activation_token_expires_at):
            raise AuthError("Token de ativação expirado.")

        user.status = UserStatus.ACTIVE
        user.is_email_confirmed = True
        user.activation_token = None
        user.activation_token_expires_at = None
        db.commit()
        return {"email": user.email}
    finally:
        db.close()


def get_all_users() -> list:
    db: Session = get_session()
    try:
        users = db.query(User).order_by(User.created_at.desc()).all()
        return [
            {
                "id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "role": u.role.value,
                "status": u.status.value,
                "created_at": str(u.created_at)[:19] if u.created_at else "N/A",
                "last_login_at": str(u.last_login_at)[:19] if u.last_login_at else "N/A",
                "last_login_ip": u.last_login_ip or "N/A",
                "subscription_active": u.subscription_active,
            }
            for u in users
        ]
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Aliases para compatibilidade com as páginas
# ---------------------------------------------------------------------------
confirm_account      = verify_code
resend_confirmation  = resend_verification_code


def request_password_reset(email: str) -> dict:
    """Gera token JWT de reset e envia e-mail com link."""
    db: Session = get_session()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Não revelar se o e-mail existe (segurança)
            return {"email": email}
        if user.status == UserStatus.BANNED:
            raise AuthError("Conta bloqueada. Entre em contato com o suporte.", 403)

        token = create_password_reset_token(email)
        logger.info(f"[auth] Token de reset gerado para {email}")

        try:
            from services.email_service import send_password_reset_email
            send_password_reset_email(email, user.full_name, token)
        except Exception as e:
            logger.error(f"[auth] Erro ao enviar e-mail de reset para {email}: {e}")

        return {"email": email}
    finally:
        db.close()


def reset_password(email: str, token: str, new_password: str) -> dict:
    """Valida token JWT e atualiza a senha do usuário."""
    db: Session = get_session()
    try:
        try:
            payload = decode_token(token)
            if payload.get("type") != "password_reset":
                raise AuthError("Token inválido.", 400)
            token_email = payload.get("sub", "")
        except JWTError:
            raise AuthError("Token inválido ou expirado.", 400)

        if token_email.lower() != email.strip().lower():
            raise AuthError("Token não corresponde ao e-mail informado.", 400)

        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if not user:
            raise AuthError("Usuário não encontrado.", 404)
        if user.status == UserStatus.BANNED:
            raise AuthError("Conta bloqueada.", 403)

        user.hashed_password = hash_password(new_password)
        db.commit()
        logger.info(f"[auth] Senha redefinida para {email}")
        return {"email": user.email}
    finally:
        db.close()
