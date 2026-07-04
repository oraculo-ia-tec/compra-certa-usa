"""
AGENTE 3 - UI-SYSTEMS
Ponto de entrada Streamlit. Sem FastAPI, sem servidor separado.
"""
import streamlit as st
from models.database import init_db

st.set_page_config(page_title="COMPRA CERTA USA", page_icon="📦", layout="wide")
init_db()

if "cliente_id" not in st.session_state:
    st.session_state.cliente_id = None
if "cliente_nome" not in st.session_state:
    st.session_state.cliente_nome = None

st.markdown("""
<style>
.main-header {font-size: 2rem; font-weight: 700; color: #1E3A8A;}
.sub-header {color: #64748B; margin-bottom: 1.5rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📦 COMPRA CERTA USA</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Redirecionamento de compras dos EUA para o Brasil</div>', unsafe_allow_html=True)

st.info("Use o menu lateral para navegar entre Onboarding, Novo Pedido, Meus Pedidos e Administracao.")

if st.session_state.cliente_id:
    st.success(f"Logado como {st.session_state.cliente_nome}")
else:
    st.warning("Nenhum cliente logado. Acesse a pagina de Onboarding / Login.")
