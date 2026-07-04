"""Controle de sessão do usuário — Compra Certa USA."""
import streamlit as st


def set_session(token_response: dict):
    st.session_state["access_token"]  = token_response.get("access_token")
    st.session_state["refresh_token"] = token_response.get("refresh_token")
    st.session_state["user"] = {
        "id":              token_response.get("user_id"),
        "full_name":       token_response.get("full_name"),
        "email":           token_response.get("email"),
        "role":            token_response.get("role"),
        "status":          token_response.get("status"),
        "is_first_access": token_response.get("is_first_access"),
        "avatar_url":      token_response.get("avatar_url"),
    }


def is_logged_in() -> bool:
    return bool(st.session_state.get("access_token"))


def is_verified() -> bool:
    """Conta ativa = e-mail confirmado (status == 'active')."""
    user = st.session_state.get("user", {})
    return user.get("status") == "active"


def get_current_user() -> dict:
    return st.session_state.get("user", {})


def get_user_id() -> int | None:
    """Retorna o ID do User autenticado (novo sistema JWT)."""
    return get_current_user().get("id")


def require_auth():
    """Bloqueia a página se o usuário não estiver autenticado E com conta ativa."""
    if not is_logged_in():
        st.switch_page("pages/Login.py")
        st.stop()
    if not is_verified():
        st.warning("Sua conta ainda não foi verificada.")
        st.switch_page("pages/Confirmar_Conta.py")
        st.stop()


def clear_session():
    for key in ["access_token", "refresh_token", "user"]:
        st.session_state.pop(key, None)


def get_current_user() -> dict | None:
    if not is_logged_in():
        return None
    return {
        "user_id":   st.session_state.get("user_id"),
        "full_name": st.session_state.get("user_nome"),
        "role":      st.session_state.get("user_role"),
        "status":    st.session_state.get("user_status"),
    }


def require_login():
    if not is_logged_in():
        st.warning("Você precisa estar logado para acessar esta página.")
        st.switch_page("pages/Login.py")
        st.stop()


def logout():
    for key in ["user_id", "user_nome", "user_role", "user_status",
                "access_token", "refresh_token", "pending_email"]:
        st.session_state.pop(key, None)
