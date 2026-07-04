"""AGENTE 3 - UI-SYSTEMS - Onboarding e login do cliente."""
import streamlit as st
from tools.tools import tool_cadastrar_cliente, tool_autenticar_cliente

st.title("Onboarding do Cliente")
tab_login, tab_cadastro = st.tabs(["Login", "Criar Conta"])

with tab_login:
    with st.form("form_login"):
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")
        if submit:
            resultado = tool_autenticar_cliente(email, senha)
            if resultado.sucesso:
                st.session_state.cliente_id = resultado.dados["cliente_id"]
                st.session_state.cliente_nome = resultado.dados["nome"]
                st.success(f"Bem-vindo, {resultado.dados['nome']}!")
            else:
                st.error(resultado.erro)

with tab_cadastro:
    with st.form("form_cadastro"):
        nome = st.text_input("Nome completo")
        email_c = st.text_input("Email", key="email_cadastro")
        senha_c = st.text_input("Senha", type="password", key="senha_cadastro")
        cpf = st.text_input("CPF (opcional)")
        telefone = st.text_input("Telefone (opcional)")
        submit_c = st.form_submit_button("Criar conta")
        if submit_c:
            resultado = tool_cadastrar_cliente(nome, email_c, senha_c, cpf or None, telefone or None)
            if resultado.sucesso:
                st.success(f"Conta criada! Seu endereco EUA: {resultado.dados['codigo_suite']}")
            else:
                st.error(resultado.erro)
