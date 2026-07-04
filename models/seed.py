"""
Seed do superusuário e usuário de teste.
Executa migrações seguras via ALTER TABLE para colunas novas.

OBSERVAÇÃO: O superusuário tem role AI_DEVELOPER com acesso total ao sistema.
Em produção, altere as credenciais via st.secrets ou variável de ambiente.
"""
from datetime import datetime

from loguru import logger
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from models.database import engine, get_session
from models.models import Base, User, UserRole, UserStatus
from services.security import hash_password

# ---------------------------------------------------------------------------
# Credenciais iniciais — troque em produção via secrets/env
# ---------------------------------------------------------------------------
SUPERUSER_EMAIL    = "contato@oraculosia.site"
SUPERUSER_PASSWORD = "admin@2026"

TEST_CLIENT_EMAIL    = "cliente.teste@compracertausa.com"
TEST_CLIENT_PASSWORD = "cliente@2026"

# ---------------------------------------------------------------------------
# Colunas a migrar na tabela users (SQLite usa DATETIME, não TIMESTAMP)
# ---------------------------------------------------------------------------
_MIGRATIONS_USERS = [
    ("is_email_confirmed",           "BOOLEAN DEFAULT 0"),
    ("verification_code",            "TEXT"),
    ("verification_code_expires_at", "DATETIME"),
    ("verification_attempts",        "INTEGER DEFAULT 0"),
    ("last_code_sent_at",            "DATETIME"),
    ("activation_token",             "TEXT"),
    ("activation_token_expires_at",  "DATETIME"),
    ("avatar_url",                   "TEXT"),
    ("is_first_access",              "BOOLEAN DEFAULT 1"),
    ("subscription_active",          "BOOLEAN DEFAULT 0"),
    ("last_login_at",                "DATETIME"),
    ("last_login_ip",                "VARCHAR(45)"),
    ("role",                         "VARCHAR(50) DEFAULT 'client'"),
    ("status",                       "VARCHAR(50) DEFAULT 'pending'"),
    ("created_at",                   "DATETIME"),
]


def _create_all_safe() -> None:
    """Cria tabelas que ainda não existem (não toca nas existentes)."""
    Base.metadata.create_all(bind=engine)
    logger.info("[seed] Tabelas verificadas/criadas.")


def _run_migrations() -> None:
    """Adiciona colunas novas à tabela users sem derrubar dados existentes."""
    with engine.connect() as conn:
        inspector = inspect(engine)
        existing = {col["name"] for col in inspector.get_columns("users")} if inspector.has_table("users") else set()

        for col_name, col_def in _MIGRATIONS_USERS:
            if col_name not in existing:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
                    conn.commit()
                    logger.info(f"[seed] Coluna adicionada: users.{col_name}")
                except Exception as e:
                    logger.warning(f"[seed] Coluna users.{col_name} já existe ou erro: {e}")


def _seed_users() -> None:
    """Cria superusuário (AI_DEVELOPER) e cliente de teste se não existirem."""
    db = get_session()
    try:
        # Superusuário
        if not db.query(User).filter_by(email=SUPERUSER_EMAIL).first():
            superuser = User(
                full_name="Administrador Compra Certa USA",
                email=SUPERUSER_EMAIL,
                hashed_password=hash_password(SUPERUSER_PASSWORD),
                role=UserRole.AI_DEVELOPER,
                status=UserStatus.ACTIVE,
                is_email_confirmed=True,
                is_first_access=False,
                subscription_active=True,
                created_at=datetime.utcnow(),
            )
            db.add(superuser)
            logger.info(f"[seed] Superusuário criado: {SUPERUSER_EMAIL}")
        else:
            logger.info(f"[seed] Superusuário já existe: {SUPERUSER_EMAIL}")

        # Cliente de teste
        if not db.query(User).filter_by(email=TEST_CLIENT_EMAIL).first():
            test_client = User(
                full_name="Cliente Teste",
                email=TEST_CLIENT_EMAIL,
                hashed_password=hash_password(TEST_CLIENT_PASSWORD),
                role=UserRole.CLIENT,
                status=UserStatus.ACTIVE,
                is_email_confirmed=True,
                is_first_access=True,
                subscription_active=False,
                created_at=datetime.utcnow(),
            )
            db.add(test_client)
            logger.info(f"[seed] Cliente de teste criado: {TEST_CLIENT_EMAIL}")
        else:
            logger.info(f"[seed] Cliente de teste já existe: {TEST_CLIENT_EMAIL}")

        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error(f"[seed] IntegrityError no seed de usuários: {e}")
    finally:
        db.close()


def init_db_and_seed() -> None:
    """
    Ponto de entrada principal:
    1. Cria tabelas que não existem
    2. Adiciona colunas novas (migração segura)
    3. Seed de usuários iniciais
    """
    _create_all_safe()
    _run_migrations()
    _seed_users()
    logger.info("[seed] Banco inicializado e seed concluído.")


if __name__ == "__main__":
    init_db_and_seed()
