"""Meus Pedidos."""
import streamlit as st
from tools.tools import tool_listar_pedidos_por_cliente
from components.ui import page_header, status_badge, section_title, user_topbar, STATUS_LABELS
from components.session import require_auth, get_user_id

require_auth()
user_topbar()
page_header("Meus Pedidos", "Acompanhe o status de todas as suas importações.", "📋")

resultado = tool_listar_pedidos_por_cliente(get_user_id())
if not resultado.sucesso:
    st.error(resultado.erro)
    st.stop()

pedidos = resultado.dados["pedidos"]
if not pedidos:
    st.info("Você ainda não tem pedidos. Crie um na página Novo Pedido.")
    col1, _ = st.columns([1, 3])
    with col1:
        if st.button("➕ Criar primeiro pedido", type="primary"):
            st.switch_page("pages/2_Novo_Pedido.py")
    st.stop()

status_options = ["Todos"] + list(STATUS_LABELS.values())
filtro = st.selectbox("Filtrar por status", options=status_options)

for p in pedidos:
    label_status = STATUS_LABELS.get(p["status"], p["status"])
    if filtro != "Todos" and label_status != filtro:
        continue
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        with c1:
            st.markdown(f"**Pedido #{p['pedido_id']}**")
            st.caption(f"Criado em {p['criado_em']}")
        with c2:
            st.html(status_badge(p["status"]))
            st.caption(f"Serviço: {p['tipo_servico'].capitalize()}")
        with c3:
            st.caption(f"{p['qtd_itens']} item(ns) · {p['qtd_pacotes']} pacote(s)")
        with c4:
            if st.button("Detalhes", key=f"detalhe_{p['pedido_id']}", use_container_width=True):
                st.session_state.pedido_detalhe_id = p["pedido_id"]
                st.switch_page("pages/5_Detalhe_Pedido.py")
