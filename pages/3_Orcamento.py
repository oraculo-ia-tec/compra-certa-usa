"""Orçamento do Pedido."""
import streamlit as st
from tools.tools import tool_calcular_orcamento, tool_sugerir_divisao_pacotes
from components.ui import page_header, section_title, user_topbar
from components.session import require_auth

require_auth()
user_topbar()
page_header("Orçamento do Pedido", "Calcule o custo estimado da sua importação.", "💰")

pedido_id_default = st.session_state.get("ultimo_pedido_id", 1)
pedido_id = st.number_input("ID do pedido", min_value=1, value=int(pedido_id_default), step=1)

col1, col2 = st.columns(2)
with col1:
    usar_cotacao_manual = st.checkbox("Informar cotacao do dolar manualmente")
    cotacao_dolar = None
    if usar_cotacao_manual:
        cotacao_dolar = st.number_input("Cotacao USD/BRL", min_value=0.0, value=5.40, step=0.01)
with col2:
    st.caption("Se nao informar, o sistema usa uma cotacao de fallback (5.40) ate a integracao com API de cambio.")

if st.button("Calcular orcamento", type="primary"):
    resultado = tool_calcular_orcamento(pedido_id=int(pedido_id), cotacao_dolar=cotacao_dolar)
    if resultado.sucesso:
        dados = resultado.dados
        st.success("Orcamento calculado com sucesso.")
        m1, m2, m3 = st.columns(3)
        m1.metric("Valor dos produtos (USD)", f"US$ {dados['valor_produtos_usd']:.2f}")
        m2.metric("Frete estimado (USD)", f"US$ {dados['frete_estimado_usd']:.2f}")
        m3.metric("Taxa de servico (USD)", f"US$ {dados['taxa_servico_usd']:.2f}")
        m4, m5 = st.columns(2)
        m4.metric("Imposto estimado (BRL)", f"R$ {dados['imposto_estimado_brl']:.2f}")
        m5.metric("Cotacao do dolar usada", f"R$ {dados['cotacao_dolar']:.2f}")
        st.metric("Total estimado (BRL)", f"R$ {dados['total_estimado_brl']:.2f}")
        st.caption("Regra de imposto e frete sao estimativas provisorias, a validar com a operacao.")
    else:
        st.error(resultado.erro)

st.divider()
section_title("Sugestão de divisão de pacotes (perfil econômico)")
if st.button("Sugerir divisao de pacotes"):
    resultado_div = tool_sugerir_divisao_pacotes(pedido_id=int(pedido_id))
    if resultado_div.sucesso:
        dados = resultado_div.dados
        st.write(f"Sugestao para o pedido {dados['pedido_id']}:")
        for i, grupo in enumerate(dados["pacotes_sugeridos"], start=1):
            st.write(f"- Pacote {i}: itens {grupo}")
        st.caption(dados["justificativa"])
    else:
        st.error(resultado_div.erro)
