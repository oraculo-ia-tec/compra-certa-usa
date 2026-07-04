"""
Camada de compatibilidade: redireciona chamadas para os services locais.
Não usa conexão externa.
"""
import streamlit as st
from services import auth as auth_service
from models.models import UserRole


def api_post(path: str, data: dict) -> dict | None:
    """Simula POST para o backend localmente."""
    try:
        if path == "/auth/login":
            return auth_service.login(data["email"], data["password"])
        if path == "/auth/register":
            return auth_service.register(data["full_name"], data["email"], data["password"])
        if path == "/auth/verify-code":
            return auth_service.verify_code(data["email"], data["code"])
        if path == "/auth/resend-code":
            return auth_service.resend_verification_code(data["email"])
        if path == "/auth/activate":
            return auth_service.activate_account(data["token"])
        if path == "/auth/request-reset":
            return auth_service.request_password_reset(data["email"])
        if path == "/auth/reset-password":
            return auth_service.reset_password(data["email"], data["token"], data["new_password"])
    except auth_service.AuthError as e:
        st.error(f"❌ {e.message}")
        return None
    except Exception as e:
        st.error(f"❌ Erro inesperado: {e}")
        return None


def api_get(path: str) -> dict | list | None:
    """Simula GET para o backend localmente."""
    try:
        if path == "/dev/users":
            return auth_service.get_all_users()
    except Exception as e:
        st.error(f"❌ Erro inesperado: {e}")
        return None
