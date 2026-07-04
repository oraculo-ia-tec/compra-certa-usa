"""AGENTE 3 - UI-SYSTEMS - Rastreamento (visao do cliente)."""
import streamlit as st
from tools.tools import tool_rastrear_pedido

st.title("Rastreamento do Pedido")

if not st.session_state.get("cliente_id"):
    st.warning("Faca login na pagina de Onboarding para rastrear seu pedido.")
    st.stop()

etapas_labels = {
    "aguardando_compra": "Pedido registrado", "aguardando_chegada_eua": "Aguardando chegada nos EUA",
    "recebido_warehouse": "Recebido no warehouse EUA", "em_consolidacao": "Em consolidacao",
    "frete_cotado": "Frete selecionado", "enviado": "Enviado para o Brasil",
    "em_transito": "Em transito", "entregue": "Entregue",
}

pedido_id_default = st.session_state.get("ultimo_pedido_id", 1)
pedido_id = st.number_input("ID do pedido", min_value=1, value=int(pedido_id_default), step=1)

if st.button("Rastrear", type="primary"):
    resultado = tool_rastrear_pedido(int(pedido_id), st.session_state.cliente_id)
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
