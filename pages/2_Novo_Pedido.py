"""Novo Pedido."""
import streamlit as st
from tools.tools import tool_criar_pedido
from components.ui import page_header, section_title, user_topbar
from components.session import require_auth, get_user_id

require_auth()
user_topbar()
page_header("Novo Pedido", "Adicione os produtos que deseja importar dos EUA.", "🛒")

cliente_id = get_user_id()

if "itens_pedido" not in st.session_state:
    st.session_state.itens_pedido = []

section_title("Adicionar item")
with st.form("form_item", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        url_produto = st.text_input("Link do produto (URL)")
        descricao = st.text_input("Descricao (opcional)")
        loja = st.text_input("Loja (ex: Amazon, Best Buy)")
    with col2:
        quantidade = st.number_input("Quantidade", min_value=1, value=1, step=1)
        preco_unitario_usd = st.number_input("Preco unitario (USD)", min_value=0.0, value=0.0, step=0.01)
    add_item = st.form_submit_button("Adicionar item ao pedido")

    if add_item:
        if not url_produto:
            st.error("Informe o link do produto.")
        else:
            st.session_state.itens_pedido.append({
                "url_produto": url_produto, "descricao": descricao or None,
                "quantidade": int(quantidade),
                "preco_unitario_usd": float(preco_unitario_usd) if preco_unitario_usd else None,
                "loja": loja or None,
            })
            st.success("Item adicionado.")

section_title("Itens no pedido")
if st.session_state.itens_pedido:
    for idx, item in enumerate(st.session_state.itens_pedido):
        c1, c2, c3 = st.columns([5, 2, 1])
        with c1:
            st.write(f"**{item['descricao'] or item['url_produto']}** ({item['loja'] or 'loja nao informada'})")
        with c2:
            preco = item["preco_unitario_usd"]
            preco_str = f"US$ {preco:.2f}" if preco else "sem preco"
            st.write(f"Qtd: {item['quantidade']} | {preco_str}")
        with c3:
            if st.button("Remover", key=f"remover_{idx}"):
                st.session_state.itens_pedido.pop(idx)
                st.rerun()
else:
    st.info("Nenhum item adicionado ainda.")

section_title("Configuração do pedido")
tipo_servico = st.selectbox("Tipo de servico", options=["economico", "padrao", "expresso"],
                             format_func=lambda x: {"economico": "Economico", "padrao": "Padrao", "expresso": "Expresso"}[x])
observacoes = st.text_area("Observacoes (opcional)")

if st.button("Finalizar pedido", type="primary", disabled=not st.session_state.itens_pedido):
    resultado = tool_criar_pedido(cliente_id=cliente_id, itens=st.session_state.itens_pedido,
                                   tipo_servico=tipo_servico, observacoes=observacoes or None)
    if resultado.sucesso:
        st.session_state.ultimo_pedido_id = resultado.dados["pedido_id"]
        st.session_state.itens_pedido = []
        st.success(f"Pedido criado com sucesso! ID do pedido: {resultado.dados['pedido_id']}")
        st.info("Acesse a pagina de Orcamento para calcular o custo estimado deste pedido.")
    else:
        st.error(resultado.erro)
