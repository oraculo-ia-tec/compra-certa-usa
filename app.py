"""
COMPRA CERTA USA — Ponto de entrada Streamlit.
Inicializa banco de dados, migrações e seed na primeira execução.
"""
import streamlit as st
from models.seed import init_db_and_seed
from components.session import is_logged_in, get_current_user, clear_session

st.set_page_config(page_title="COMPRA CERTA USA", page_icon="📦", layout="wide")

# Inicializa tabelas + migrações + seed (seguro executar em todo cold start)
init_db_and_seed()

st.markdown("""
<style>
.main-header {font-size: 2rem; font-weight: 700; color: #1E3A8A;}
.sub-header {color: #64748B; margin-bottom: 1.5rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📦 COMPRA CERTA USA</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Redirecionamento de compras dos EUA para o Brasil</div>', unsafe_allow_html=True)

if is_logged_in():
    user = get_current_user()
    col1, col2 = st.columns([4, 1])
    with col1:
        st.success(f"Olá, **{user.get('full_name', '')}**! Use o menu lateral para navegar.")
    with col2:
        if st.button("Sair", use_container_width=True):
            clear_session()
            st.rerun()
else:
    st.info("Use o menu lateral para navegar entre as páginas.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔐 Fazer login", use_container_width=True, type="primary"):
            st.switch_page("pages/Login.py")
    with col2:
        if st.button("📝 Criar conta", use_container_width=True):
            st.switch_page("pages/Cadastro.py")
