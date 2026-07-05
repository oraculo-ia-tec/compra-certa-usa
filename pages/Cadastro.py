"""Tela de cadastro — Compra Certa USA."""
import re
import base64
import streamlit as st
from components.session import is_logged_in
from components.ui import inject_css
from services.auth import register, AuthError

inject_css()

if is_logged_in():
    st.switch_page("pages/4_Meus_Pedidos.py")

# Banner quando veio da seleção de plano
_pending_plan = st.session_state.get("pending_plan")
if _pending_plan:
    from services.stripe_service import PLANOS
    _nome_plano = PLANOS.get(_pending_plan, {}).get("nome", _pending_plan.capitalize())
    st.info(f"💳 Você escolheu o plano **{_nome_plano}**! Crie sua conta para continuar com o pagamento.")

st.html('<p class="ccu-page-title">📦 Compra Certa USA</p><p class="ccu-page-subtitle">Crie sua conta para começar a importar dos EUA</p><hr class="ccu-page-divider">')

# Link para login
col_l, col_r = st.columns([3, 1])
with col_r:
    if st.button("Já tenho conta", use_container_width=True):
        st.switch_page("pages/Login.py")

st.divider()

with st.form("form_cadastro", clear_on_submit=False):
    full_name = st.text_input("Nome completo *", placeholder="Ex: Maria da Silva")
    email     = st.text_input("E-mail *", placeholder="seu@email.com")

    col1, col2 = st.columns(2)
    with col1:
        password  = st.text_input("Senha *", type="password", placeholder="Mínimo 8 caracteres")
    with col2:
        password2 = st.text_input("Confirmar senha *", type="password", placeholder="Repita a senha")

    avatar_file = st.file_uploader(
        "Foto de perfil (opcional)", type=["jpg", "jpeg", "png"],
        help="Tamanho máximo: 2 MB"
    )

    submitted = st.form_submit_button("Criar conta", use_container_width=True, type="primary")

if submitted:
    errors = []

    if len(full_name.strip()) < 3:
        errors.append("Nome deve ter ao menos 3 caracteres.")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()):
        errors.append("E-mail inválido.")
    if len(password) < 8:
        errors.append("Senha deve ter ao menos 8 caracteres.")
    if password != password2:
        errors.append("As senhas não coincidem.")
    if avatar_file and avatar_file.size > 2 * 1024 * 1024:
        errors.append("A foto deve ter no máximo 2 MB.")

    if errors:
        for err in errors:
            st.error(f"⚠️ {err}")
    else:
        avatar_b64 = None
        if avatar_file:
            avatar_b64 = base64.b64encode(avatar_file.read()).decode("utf-8")

        try:
            register(
                full_name=full_name.strip(),
                email=email.strip().lower(),
                password=password,
                avatar_b64=avatar_b64,
            )
            st.session_state["pending_email"] = email.strip().lower()
            st.success("✅ Conta criada! Verifique seu e-mail para ativar o acesso.")
            st.balloons()
            st.switch_page("pages/Confirmar_Conta.py")
        except AuthError as e:
            st.error(f"❌ {e.message}")
        except Exception as e:
            st.error(f"❌ Erro inesperado: {e}")

st.divider()
st.caption("Ao criar uma conta, você concorda com nossos termos de uso e política de privacidade.")
