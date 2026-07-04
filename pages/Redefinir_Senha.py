"""Tela de redefinição de senha — Compra Certa USA.

Fluxo em 2 passos:
  1. Usuário informa o e-mail → recebe link com token JWT por e-mail
  2. Usuário cola o token (ou chega via URL ?token=...) + nova senha
"""
import re
import streamlit as st
from components.ui import inject_css
from services.auth import request_password_reset, reset_password, AuthError

inject_css()

st.html('<p class="ccu-page-title">🔑 Redefinir senha</p><hr class="ccu-page-divider">')

# Lê token da URL (quando usuário clica no link do e-mail)
url_token = st.query_params.get("token", "")

# Controla em qual passo estamos
if "reset_step" not in st.session_state:
    st.session_state["reset_step"] = 2 if url_token else 1
if "reset_email" not in st.session_state:
    st.session_state["reset_email"] = ""

# ─────────────────────────────────────────────
# PASSO 1 — Solicitar e-mail
# ─────────────────────────────────────────────
if st.session_state["reset_step"] == 1:
    st.markdown('<p class="auth-sub">Informe seu e-mail e enviaremos um link para redefinir sua senha.</p>', unsafe_allow_html=True)

    with st.form("form_solicitar_reset"):
        email = st.text_input("E-mail cadastrado", placeholder="seu@email.com")
        submitted = st.form_submit_button("Enviar link de recuperação", use_container_width=True, type="primary")

    if submitted:
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()):
            st.error("⚠️ E-mail inválido.")
        else:
            with st.spinner("Enviando..."):
                try:
                    request_password_reset(email.strip().lower())
                    st.session_state["reset_email"] = email.strip().lower()
                    st.session_state["reset_step"]  = 2
                    st.success("📧 Se o e-mail estiver cadastrado, você receberá o link em instantes.")
                    st.rerun()
                except AuthError as e:
                    st.error(f"❌ {e.message}")
                except Exception as e:
                    st.error(f"❌ Erro inesperado: {e}")

# ─────────────────────────────────────────────
# PASSO 2 — Token + nova senha
# ─────────────────────────────────────────────
else:
    st.markdown('<p class="auth-sub">Cole o token recebido por e-mail e defina sua nova senha.</p>', unsafe_allow_html=True)

    reset_email = st.session_state.get("reset_email", "")

    with st.form("form_reset_senha"):
        email_input = st.text_input(
            "E-mail cadastrado",
            value=reset_email,
            disabled=bool(reset_email),
            placeholder="seu@email.com",
        )
        token_input = st.text_input(
            "Token de recuperação",
            value=url_token,
            placeholder="Cole aqui o token recebido por e-mail",
            help="O token está no link que você recebeu por e-mail.",
        )
        new_pw  = st.text_input("Nova senha", type="password", placeholder="Mínimo 8 caracteres")
        new_pw2 = st.text_input("Confirmar nova senha", type="password", placeholder="Repita a senha")
        submitted = st.form_submit_button("Redefinir senha", use_container_width=True, type="primary")

    if submitted:
        reset_email_val = (email_input or reset_email).strip().lower()
        token_val       = token_input.strip()
        errors = []

        if not reset_email_val:
            errors.append("Informe o e-mail cadastrado.")
        if not token_val:
            errors.append("Cole o token recebido por e-mail.")
        if len(new_pw) < 8:
            errors.append("A nova senha deve ter ao menos 8 caracteres.")
        if new_pw != new_pw2:
            errors.append("As senhas não coincidem.")

        if errors:
            for err in errors:
                st.error(f"⚠️ {err}")
        else:
            with st.spinner("Redefinindo senha..."):
                try:
                    reset_password(reset_email_val, token_val, new_pw)
                    st.session_state.pop("reset_step",  None)
                    st.session_state.pop("reset_email", None)
                    st.query_params.clear()
                    st.success("✅ Senha redefinida com sucesso! Faça login.")
                    st.switch_page("pages/Login.py")
                except AuthError as e:
                    st.error(f"❌ {e.message}")
                except Exception as e:
                    st.error(f"❌ Erro inesperado: {e}")

    if not url_token:
        st.divider()
        if st.button("← Não recebi o e-mail — tentar novamente", use_container_width=True):
            st.session_state["reset_step"] = 1
            st.rerun()

st.divider()
if st.button("Voltar ao login", use_container_width=True):
    st.switch_page("pages/Login.py")
