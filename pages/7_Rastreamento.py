"""Rastreamento do Pedido."""
import streamlit as st
from tools.tools import tool_rastrear_pedido
from components.ui import page_header, user_topbar, STATUS_LABELS
from components.session import require_auth, get_user_id

require_auth()
user_topbar()
page_header("Rastreamento do Pedido", "Acompanhe sua encomenda em tempo real.", "✈️")

etapas_labels = {
    "aguardando_compra":      "Pedido registrado",
    "aguardando_chegada_eua": "Aguardando nos EUA",
    "recebido_warehouse":     "Recebido no warehouse",
    "em_consolidacao":        "Em consolidação",
    "frete_cotado":           "Frete selecionado",
    "enviado":                "Enviado ao Brasil",
    "em_transito":            "Em trânsito",
    "entregue":               "Entregue",
}

pedido_id_default = st.session_state.get("ultimo_pedido_id", 1)
pedido_id = st.number_input("ID do pedido", min_value=1, value=int(pedido_id_default), step=1)

if st.button("Rastrear", type="primary"):
    resultado = tool_rastrear_pedido(int(pedido_id), get_user_id())
    if not resultado.sucesso:
        st.error(resultado.erro)
        st.stop()

    d = resultado.dados

    if d["status_atual"] == "cancelado":
        st.error("Este pedido foi cancelado.")
    else:
        st.subheader("Linha do tempo")
        indice_atual = d["indice_etapa_atual"]
        etapas = d["etapas"]
        cols = st.columns(len(etapas))
        for i, (col, etapa) in enumerate(zip(cols, etapas)):
            with col:
                if i < indice_atual:
                    st.markdown(f"✅ **{etapas_labels.get(etapa, etapa)}**")
                elif i == indice_atual:
                    st.markdown(f"🟦 **{etapas_labels.get(etapa, etapa)}**")
                    st.caption("Etapa atual")
                else:
                    st.markdown(f"⬜ {etapas_labels.get(etapa, etapa)}")
        st.progress((indice_atual + 1) / len(etapas) if indice_atual >= 0 else 0.0)

    st.divider()
    st.subheader("Remessa internacional")
    if d["remessas"]:
        for r in d["remessas"]:
            with st.container(border=True):
                st.write(f"**Transportadora:** {r['transportadora'] or 'ainda nao definida'}")
                st.write(f"**Codigo de rastreio:** {r['codigo_rastreio_internacional'] or 'ainda nao disponivel'}")
                st.caption(f"Status da transportadora: {r['status_transportadora'] or 'aguardando envio'}")
                if r["enviado_em"]:
                    st.caption(f"Enviado em: {r['enviado_em']}")
                if r["entregue_em"]:
                    st.caption(f"Entregue em: {r['entregue_em']}")
    else:
        st.info("Nenhuma remessa gerada ainda. Isso ocorre apos a chegada do pacote no warehouse e selecao do frete.")

    st.divider()
    st.subheader("Historico completo")
    for h in d["historico"]:
        linha = f"- **{h['criado_em']}** — {etapas_labels.get(h['status'], h['status'])}"
        if h["observacao"]:
            linha += f" ({h['observacao']})"
        st.write(linha)
