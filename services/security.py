"""Funções de segurança: hash de senha e JWT.
Usa bcrypt diretamente (passlib é incompatível com Python 3.12+).
"""
import bcrypt
import streamlit as st
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from jose import jwt


def _secret() -> str:
    try:
        base = st.secrets["default"]["APP_BASE_URL"]
        return f"compra-certa-usa-jwt-{base}-2026"
    except Exception:
        return "compra-certa-usa-jwt-dev-fallback-2026"


ALGORITHM = "HS256"
ACCESS_EXPIRE_MINUTES = 30
REFRESH_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """Gera hash bcrypt da senha."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica senha contra hash bcrypt."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_EXPIRE_MINUTES))
    payload = {"sub": str(subject), "exp": expire, "type": "access"}
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def create_refresh_token(subject: Any) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE_DAYS)
    payload = {"sub": str(subject), "exp": expire, "type": "refresh"}
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def create_activation_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {"sub": email, "exp": expire, "type": "activation"}
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def create_password_reset_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {"sub": email, "exp": expire, "type": "password_reset"}
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, _secret(), algorithms=[ALGORITHM])
