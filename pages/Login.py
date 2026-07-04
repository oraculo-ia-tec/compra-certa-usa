"""Tela de login — Compra Certa USA."""
import streamlit as st
from components.session import set_session, is_logged_in
from components.ui import inject_css
from services.auth import login, AuthError

inject_css()

if is_logged_in():
    st.switch_page("pages/4_Meus_Pedidos.py")

st.html('<p class="ccu-page-title">🔐 Entrar na conta</p><p class="ccu-page-subtitle">Acesse seus pedidos e acompanhe suas importações</p><hr class="ccu-page-divider">')

# Banner de conta confirmada com sucesso
if st.session_state.pop("verified_success", False):
    st.success("🎉 Conta verificada com sucesso! Faça login para continuar.")

with st.form("form_login"):
    email    = st.text_input("E-mail", placeholder="seu@email.com")
    password = st.text_input("Senha", type="password", placeholder="Sua senha")

    col1, col2 = st.columns([2, 1])
    with col1:
        submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")
    with col2:
        forgot = st.form_submit_button("Esqueci a senha", use_container_width=True)

if submitted:
    if not email.strip() or not password:
        st.error("⚠️ Preencha e-mail e senha.")
    else:
        with st.spinner("Autenticando..."):
            try:
                resp = login(email.strip().lower(), password)
                set_session(resp)
                st.success("✅ Login realizado com sucesso!")
                st.rerun()
            except AuthError as e:
                st.error(f"❌ {e.message}")
                if e.code == 403 and "confirmada" in e.message:
                    st.session_state["pending_email"] = email.strip().lower()
                    if st.button("Confirmar conta agora →"):
                        st.switch_page("pages/Confirmar_Conta.py")
            except Exception as e:
                st.error(f"❌ Erro inesperado: {e}")

if forgot:
    st.switch_page("pages/Redefinir_Senha.py")

# Redireciona após login bem-sucedido
if is_logged_in():
    if st.session_state.get("user", {}).get("is_first_access"):
        st.switch_page("pages/1_Onboarding.py")
    else:
        st.switch_page("pages/4_Meus_Pedidos.py")

st.divider()
col1, col2 = st.columns(2)
with col1:
    st.caption("Não tem conta?")
    if st.button("Criar conta gratuita", use_container_width=True):
        st.switch_page("pages/Cadastro.py")
with col2:
    st.caption("Conta pendente?")
    if st.button("Confirmar e-mail", use_container_width=True):
        st.switch_page("pages/Confirmar_Conta.py")
