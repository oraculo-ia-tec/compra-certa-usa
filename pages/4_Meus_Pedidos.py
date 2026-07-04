"""AGENTE 3 - UI-SYSTEMS - Meus Pedidos."""
import streamlit as st
from tools.tools import tool_listar_pedidos_por_cliente

st.title("Meus Pedidos")

if not st.session_state.get("cliente_id"):
    st.warning("Faca login na pagina de Onboarding para ver seus pedidos.")
    st.stop()

resultado = tool_listar_pedidos_por_cliente(st.session_state.cliente_id)
if not resultado.sucesso:
    st.error(resultado.erro)
    st.stop()

pedidos = resultado.dados["pedidos"]
if not pedidos:
    st.info("Voce ainda nao tem pedidos. Crie um na pagina Novo Pedido.")
    st.stop()

status_labels = {
    "aguardando_compra": "Aguardando compra", "aguardando_chegada_eua": "Aguardando chegada nos EUA",
    "recebido_warehouse": "Recebido no warehouse", "em_consolidacao": "Em consolidacao",
    "frete_cotado": "Frete cotado", "enviado": "Enviado", "em_transito": "Em transito",
    "entregue": "Entregue", "cancelado": "Cancelado",
}

status_options = ["Todos"] + list(status_labels.values())
filtro = st.selectbox("Filtrar por status", options=status_options)

for p in pedidos:
    label_status = status_labels.get(p["status"], p["status"])
    if filtro != "Todos" and label_status != filtro:
        continue
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        with c1:
            st.write(f"**Pedido #{p['pedido_id']}**")
            st.caption(f"Criado em {p['criado_em']}")
        with c2:
            st.write(f"Status: **{label_status}**")
            st.caption(f"Servico: {p['tipo_servico'].capitalize()}")
        with c3:
            st.write(f"{p['qtd_itens']} item(ns)")
            st.caption(f"{p['qtd_pacotes']} pacote(s)")
        with c4:
            if st.button("Ver detalhes", key=f"detalhe_{p['pedido_id']}"):
                st.session_state.pedido_detalhe_id = p["pedido_id"]
                st.switch_page("pages/5_Detalhe_Pedido.py")
