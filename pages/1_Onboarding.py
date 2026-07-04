"""Onboarding — redireciona para Login ou Cadastro (novo sistema de auth)."""
import streamlit as st
from components.ui import page_header, inject_css
from components.session import is_logged_in, get_current_user

inject_css()

if is_logged_in():
    user = get_current_user()
    page_header("Bem-vindo de volta!", f"Olá, {user.get('full_name', '')}.", "👋")
    st.success("Você já está autenticado. Use o menu lateral para navegar.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📦 Meus Pedidos", use_container_width=True, type="primary"):
            st.switch_page("pages/4_Meus_Pedidos.py")
    with col2:
        if st.button("➕ Novo Pedido", use_container_width=True):
            st.switch_page("pages/2_Novo_Pedido.py")
else:
    page_header("Bem-vindo à Compra Certa USA", "Faça login ou crie sua conta para começar.", "📦")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🔐 Já tenho conta")
        st.caption("Acesse seus pedidos e acompanhe suas importações.")
        if st.button("Fazer login", use_container_width=True, type="primary"):
            st.switch_page("pages/Login.py")
    with col2:
        st.markdown("### 📝 Sou novo aqui")
        st.caption("Crie sua conta grátis e comece a importar dos EUA.")
        if st.button("Criar conta", use_container_width=True):
            st.switch_page("pages/Cadastro.py")
    st.divider()
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.html('<div style="text-align:center;padding:1rem;"><div style="font-size:2rem;">🛒</div><b>Compre nos EUA</b><p style="color:#64748B;font-size:.85rem;">Informe o link do produto e nós compramos por você.</p></div>')
    with col_b:
        st.html('<div style="text-align:center;padding:1rem;"><div style="font-size:2rem;">📦</div><b>Recebemos no warehouse</b><p style="color:#64748B;font-size:.85rem;">Seu produto chega ao nosso armazém em Miami.</p></div>')
    with col_c:
        st.html('<div style="text-align:center;padding:1rem;"><div style="font-size:2rem;">✈️</div><b>Enviamos ao Brasil</b><p style="color:#64748B;font-size:.85rem;">Escolha o frete e acompanhe o rastreamento.</p></div>')
