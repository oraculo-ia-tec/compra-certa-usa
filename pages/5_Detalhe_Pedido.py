"""AGENTE 3 - UI-SYSTEMS - Detalhe do Pedido."""
import streamlit as st
from tools.tools import tool_detalhar_pedido

st.title("Detalhe do Pedido")

if not st.session_state.get("cliente_id"):
    st.warning("Faca login na pagina de Onboarding para ver o detalhe do pedido.")
    st.stop()

pedido_id_default = st.session_state.get("pedido_detalhe_id", 1)
pedido_id = st.number_input("ID do pedido", min_value=1, value=int(pedido_id_default), step=1)

resultado = tool_detalhar_pedido(int(pedido_id))
if not resultado.sucesso:
    st.error(resultado.erro)
    st.stop()

d = resultado.dados

status_labels = {
    "aguardando_compra": "Aguardando compra", "aguardando_chegada_eua": "Aguardando chegada nos EUA",
    "recebido_warehouse": "Recebido no warehouse", "em_consolidacao": "Em consolidacao",
    "frete_cotado": "Frete cotado", "enviado": "Enviado", "em_transito": "Em transito",
    "entregue": "Entregue", "cancelado": "Cancelado",
}

st.subheader(f"Pedido #{d['pedido_id']} — {status_labels.get(d['status'], d['status'])}")
c1, c2, c3 = st.columns(3)
c1.metric("Tipo de servico", d["tipo_servico"].capitalize())
c2.metric("Criado em", d["criado_em"])
c3.metric("Qtd itens", len(d["itens"]))

if d["observacoes"]:
    st.caption(f"Observacoes: {d['observacoes']}")

st.divider()
st.subheader("Itens do pedido")
if d["itens"]:
    for item in d["itens"]:
        with st.container(border=True):
            st.write(f"**{item['descricao'] or item['url_produto']}**")
            preco_txt = f"US$ {item['preco_unitario_usd']:.2f}" if item['preco_unitario_usd'] else "nao informado"
            st.caption(f"Loja: {item['loja'] or 'nao informada'} | Qtd: {item['quantidade']} | Preco unit.: {preco_txt}")
            st.caption(item["url_produto"])
else:
    st.info("Nenhum item cadastrado.")

st.divider()
st.subheader("Pacotes")
if d["pacotes"]:
    for pac in d["pacotes"]:
        with st.container(border=True):
            titulo = f"**Pacote #{pac['id']}**"
            if pac["codigo_rastreio_eua"]:
                titulo += f" — rastreio EUA: {pac['codigo_rastreio_eua']}"
            st.write(titulo)
            st.caption(f"Peso: {pac['peso_kg'] or 'nao informado'} kg | Recebido em: {pac['recebido_em'] or 'ainda nao recebido'}")
            if pac["foto_url"]:
                st.image(pac["foto_url"], width=200, caption="Foto do pacote no warehouse")
            if pac["cotacoes"]:
                st.write("Cotacoes de frete:")
                for cot in pac["cotacoes"]:
                    marcador = "✅" if cot["selecionada"] else "▫️"
                    st.write(f"{marcador} {cot['transportadora']}: US$ {cot['valor_usd']:.2f} — {cot['prazo_dias']} dia(s)")
            if pac["remessa"]:
                r = pac["remessa"]
                st.write("Remessa internacional:")
                st.caption(f"{r['transportadora']} | Rastreio: {r['codigo_rastreio_internacional'] or 'pendente'} | "
                           f"Status: {r['status_transportadora'] or 'aguardando envio'}")
else:
    st.info("Nenhum pacote registrado ainda para este pedido.")

st.divider()
st.subheader("Orcamento")
if d["orcamento"]:
    o = d["orcamento"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Produtos (USD)", f"US$ {o['valor_produtos_usd']:.2f}")
    c2.metric("Frete (USD)", f"US$ {o['frete_estimado_usd']:.2f}")
    c3.metric("Taxa servico (USD)", f"US$ {o['taxa_servico_usd']:.2f}")
    st.metric("Total estimado (BRL)", f"R$ {o['total_estimado_brl']:.2f}")
else:
    st.info("Orcamento ainda nao calculado. Acesse a pagina Orcamento.")

st.divider()
st.subheader("Historico de status")
if d["historico"]:
    for h in d["historico"]:
        linha = f"- **{h['criado_em']}** — {status_labels.get(h['status'], h['status'])}"
        if h["observacao"]:
            linha += f" ({h['observacao']})"
        st.write(linha)
else:
    st.info("Sem historico registrado.")
