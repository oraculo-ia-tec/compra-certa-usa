"""Tela de confirmação de conta — Compra Certa USA."""
import streamlit as st
from components.session import is_logged_in
from services.auth import confirm_account, resend_confirmation, AuthError

st.set_page_config(page_title="Confirmar Conta — Compra Certa USA", page_icon="📧", layout="centered")

# Redireciona se já estiver logado
if is_logged_in():
    st.switch_page("pages/4_Meus_Pedidos.py")

st.markdown("""
<style>
.auth-title {font-size:1.8rem;font-weight:700;color:#1E3A8A;margin-bottom:.25rem;}
.auth-sub   {color:#64748B;margin-bottom:1.5rem;font-size:.95rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="auth-title">📧 Confirme sua conta</p>', unsafe_allow_html=True)
st.markdown('<p class="auth-sub">Digite o código de 8 dígitos enviado para o seu e-mail</p>', unsafe_allow_html=True)

# E-mail pré-preenchido da sessão
pending_email = st.session_state.get("pending_email", "")

with st.form("form_confirmar"):
    email = st.text_input(
        "E-mail cadastrado",
        value=pending_email,
        placeholder="seu@email.com",
        disabled=bool(pending_email),
    )
    code = st.text_input(
        "Código de verificação",
        placeholder="00000000",
        max_chars=8,
        help="Código numérico de 8 dígitos enviado por e-mail",
    )
    submitted = st.form_submit_button("Confirmar conta", use_container_width=True, type="primary")

if submitted:
    email_val = (email or pending_email).strip().lower()
    code_val  = code.strip()

    if not email_val:
        st.error("⚠️ Informe o e-mail cadastrado.")
    elif len(code_val) != 8 or not code_val.isdigit():
        st.error("⚠️ O código deve ter exatamente 8 dígitos numéricos.")
    else:
        with st.spinner("Verificando..."):
            try:
                confirm_account(email_val, code_val)
                st.session_state["verified_success"] = True
                st.session_state.pop("pending_email", None)
                st.success("✅ Conta confirmada! Faça login para continuar.")
                st.switch_page("pages/Login.py")
            except AuthError as e:
                # Exibe dialog de erro conforme fluxo descrito
                @st.dialog("Código inválido")
                def _dialog_erro():
                    st.warning(f"❌ {e.message}")
                    st.info("Verifique o seu e-mail ou solicite um novo código abaixo.")
                    if st.button("Fechar", use_container_width=True):
                        st.rerun()
                _dialog_erro()
            except Exception as e:
                st.error(f"❌ Erro inesperado: {e}")

st.divider()

# --- Reenvio de código ---
st.markdown("**Não recebeu o código?**")
email_reenvio = st.text_input(
    "E-mail para reenvio",
    value=pending_email,
    key="email_reenvio",
    label_visibility="collapsed",
    placeholder="seu@email.com",
    disabled=bool(pending_email),
)

if st.button("🔄 Reenviar código", use_container_width=True):
    email_val = (email_reenvio or pending_email).strip().lower()
    if not email_val:
        st.error("⚠️ Informe o e-mail para reenvio.")
    else:
        with st.spinner("Reenviando..."):
            try:
                resend_confirmation(email_val)
                st.success("📧 Novo código enviado! Verifique sua caixa de entrada.")
            except AuthError as e:
                st.error(f"❌ {e.message}")
            except Exception as e:
                st.error(f"❌ Erro inesperado: {e}")

st.divider()
col1, col2 = st.columns(2)
with col1:
    if st.button("← Voltar ao cadastro", use_container_width=True):
        st.switch_page("pages/Cadastro.py")
with col2:
    if st.button("Ir para o login →", use_container_width=True):
        st.switch_page("pages/Login.py")
