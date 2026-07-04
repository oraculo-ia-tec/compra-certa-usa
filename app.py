"""
COMPRA CERTA USA — Ponto de entrada Streamlit.
Usa st.navigation() para controlar quais páginas aparecem no menu
conforme o estado de autenticação do usuário.
"""
import streamlit as st
from models.seed import init_db_and_seed
from components.session import is_logged_in, get_current_user, clear_session

st.set_page_config(
    page_title="COMPRA CERTA USA",
    page_icon="📦",
    layout="wide",
)

# Init DB + migrações + seed (idempotente, seguro a cada cold start)
if "db_initialized" not in st.session_state:
    init_db_and_seed()
    st.session_state["db_initialized"] = True

# ── Páginas públicas (não requerem login) ──────────────────────────────
login_page    = st.Page("pages/Login.py",          title="Login",           icon="🔐", default=True)
cadastro_page = st.Page("pages/Cadastro.py",        title="Cadastro",        icon="📝")
confirm_page  = st.Page("pages/Confirmar_Conta.py", title="Confirmar Conta", icon="📧")
reset_page    = st.Page("pages/Redefinir_Senha.py", title="Redefinir Senha", icon="🔑")

# ── Páginas protegidas ─────────────────────────────────────────────────
home_page     = st.Page("pages/1_Onboarding.py",    title="Início",            icon="🏠", default=True)
pedido_page   = st.Page("pages/2_Novo_Pedido.py",    title="Novo Pedido",       icon="🛒")
orcamento_page= st.Page("pages/3_Orcamento.py",      title="Orçamento",         icon="💰")
meus_page     = st.Page("pages/4_Meus_Pedidos.py",   title="Meus Pedidos",      icon="📋")
detalhe_page  = st.Page("pages/5_Detalhe_Pedido.py", title="Detalhe do Pedido", icon="📄")
admin_page    = st.Page("pages/6_Administracao.py",  title="Administração",     icon="⚙️")
rastreio_page = st.Page("pages/7_Rastreamento.py",   title="Rastreamento",      icon="✈️")

if is_logged_in():
    user  = get_current_user()
    role  = user.get("role", "client")
    name  = user.get("full_name", "")

    menu_principal = [home_page, pedido_page, orcamento_page, meus_page, detalhe_page, rastreio_page]
    pages = {"📦 Menu": menu_principal}

    if role in ("admin", "operator", "ai_developer"):
        pages["🔧 Gestão"] = [admin_page]

    # Barra do usuário na sidebar
    with st.sidebar:
        st.markdown(f"**{name}**")
        role_label = {"admin": "👑 Admin", "operator": "🔧 Operador",
                      "client": "👤 Cliente", "ai_developer": "🤖 Dev IA"}.get(role, role)
        st.caption(role_label)
        st.divider()
        if st.button("Sair", use_container_width=True, key="_sidebar_logout"):
            clear_session()
            st.rerun()
else:
    pages = {"🔐 Acesso": [login_page, cadastro_page, confirm_page, reset_page]}

pg = st.navigation(pages)
pg.run()
