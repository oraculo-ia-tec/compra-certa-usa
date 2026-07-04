"""Painel de Administração Operacional."""
import streamlit as st
from tools.tools import (
    tool_listar_todos_pedidos, tool_atualizar_status_pedido, tool_registrar_chegada_warehouse,
    tool_cotar_frete, tool_listar_pacotes_sem_cotacao, tool_selecionar_cotacao_frete,
    tool_registrar_envio, tool_detalhar_pedido,
)
from components.ui import page_header, status_badge, STATUS_LABELS

page_header("Administração Operacional", "Gestão de pedidos, warehouse e fretes.", "⚙️")

if "admin_autenticado" not in st.session_state:
    st.session_state.admin_autenticado = False

if not st.session_state.admin_autenticado:
    senha_admin = st.text_input("Senha de operador", type="password")
    if st.button("Entrar como operador"):
        senha_correta = st.secrets.get("ADMIN_PASSWORD", "admin123")
        if senha_admin == senha_correta:
            st.session_state.admin_autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()

tab_pedidos, tab_warehouse, tab_frete = st.tabs(["📋 Visão geral", "📦 Chegada no warehouse", "✈️ Frete e envio"])

with tab_pedidos:
    st.subheader("Todos os pedidos")
    filtro_label = st.selectbox("Filtrar por status", options=["Todos"] + list(STATUS_LABELS.values()))
    filtro_status = None
    if filtro_label != "Todos":
        filtro_status = [k for k, v in STATUS_LABELS.items() if v == filtro_label][0]

    resultado = tool_listar_todos_pedidos(filtro_status)
    if resultado.sucesso:
        pedidos = resultado.dados["pedidos"]
        if not pedidos:
            st.info("Nenhum pedido encontrado para este filtro.")
        for p in pedidos:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 2])
                with c1:
                    st.write(f"**Pedido #{p['pedido_id']}** — {p['cliente_nome']} ({p['cliente_email']})")
                    st.caption(f"Criado em {p['criado_em']} | Servico: {p['tipo_servico'].capitalize()}")
                with c2:
                    st.html(status_badge(p["status"]))
                    st.caption(f"{p['qtd_itens']} item(ns) · {p['qtd_pacotes']} pacote(s)")
                with c3:
                    novo_status_label = st.selectbox(
                        "Novo status", options=list(STATUS_LABELS.values()),
                        index=list(STATUS_LABELS.keys()).index(p["status"]),
                        key=f"status_select_{p['pedido_id']}",
                    )
                    if st.button("Atualizar status", key=f"btn_status_{p['pedido_id']}", use_container_width=True):
                        novo_status_key = [k for k, v in STATUS_LABELS.items() if v == novo_status_label][0]
                        r = tool_atualizar_status_pedido(p["pedido_id"], novo_status_key)
                        if r.sucesso:
                            st.success("Status atualizado.")
                            st.rerun()
                        else:
                            st.error(r.erro)
    else:
        st.error(resultado.erro)

with tab_warehouse:
    st.subheader("Registrar chegada no warehouse EUA")
    with st.form("form_chegada_warehouse"):
        pedido_id_wh = st.number_input("ID do pedido", min_value=1, step=1)
        codigo_rastreio_eua = st.text_input("Codigo de rastreio EUA (opcional)")
        peso_kg = st.number_input("Peso (kg)", min_value=0.0, step=0.01)
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            altura_cm = st.number_input("Altura (cm)", min_value=0.0, step=0.5)
        with col_b:
            largura_cm = st.number_input("Largura (cm)", min_value=0.0, step=0.5)
        with col_c:
            comprimento_cm = st.number_input("Comprimento (cm)", min_value=0.0, step=0.5)
        foto = st.file_uploader("Foto do pacote", type=["png", "jpg", "jpeg"])
        submit_wh = st.form_submit_button("Registrar chegada")

        if submit_wh:
            foto_url = None
            if foto is not None:
                import os
                os.makedirs("uploads", exist_ok=True)
                caminho = f"uploads/pacote_{pedido_id_wh}_{foto.name}"
                with open(caminho, "wb") as f_out:
                    f_out.write(foto.getbuffer())
                foto_url = caminho

            r = tool_registrar_chegada_warehouse(
                pedido_id=int(pedido_id_wh), peso_kg=float(peso_kg), altura_cm=float(altura_cm),
                largura_cm=float(largura_cm), comprimento_cm=float(comprimento_cm),
                foto_url=foto_url, codigo_rastreio_eua=codigo_rastreio_eua or None,
            )
            if r.sucesso:
                st.success(f"Pacote registrado com sucesso (ID {r.dados['pacote_id']}).")
            else:
                st.error(r.erro)

with tab_frete:
    st.subheader("Pacotes sem cotacao de frete")
    r_sem_cotacao = tool_listar_pacotes_sem_cotacao()
    if r_sem_cotacao.sucesso:
        pacotes_pendentes = r_sem_cotacao.dados["pacotes"]
        if pacotes_pendentes:
            for pac in pacotes_pendentes:
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"Pacote #{pac['pacote_id']} (Pedido #{pac['pedido_id']}) — {pac['peso_kg'] or 'peso nao informado'} kg")
                with c2:
                    if st.button("Cotar frete", key=f"cotar_{pac['pacote_id']}"):
                        r_cotacao = tool_cotar_frete(pac["pacote_id"])
                        if r_cotacao.sucesso:
                            st.success("Cotacoes geradas.")
                            st.rerun()
                        else:
                            st.error(r_cotacao.erro)
        else:
            st.info("Nenhum pacote pendente de cotacao.")
    else:
        st.error(r_sem_cotacao.erro)

    st.divider()
    st.subheader("Selecionar frete e registrar envio")
    pedido_id_frete = st.number_input("ID do pedido para gerenciar frete", min_value=1, step=1, key="pedido_frete")
    if st.button("Carregar pacotes do pedido"):
        r_detalhe = tool_detalhar_pedido(int(pedido_id_frete))
        if r_detalhe.sucesso:
            st.session_state.pacotes_frete_admin = r_detalhe.dados["pacotes"]
        else:
            st.error(r_detalhe.erro)

    if st.session_state.get("pacotes_frete_admin"):
        for pac in st.session_state.pacotes_frete_admin:
            with st.container(border=True):
                st.write(f"**Pacote #{pac['id']}**")
                if pac["cotacoes"]:
                    opcoes = {f"{c['transportadora']} — US$ {c['valor_usd']:.2f} ({c['prazo_dias']} dias)": c for c in pac["cotacoes"]}
                    escolha = st.selectbox("Cotacoes disponiveis", options=list(opcoes.keys()), key=f"escolha_{pac['id']}")
                    if st.button("Confirmar selecao de frete", key=f"confirmar_{pac['id']}"):
                        cot = opcoes[escolha]
                        r_sel = tool_selecionar_cotacao_frete(pac["id"], cot.get("id", 0))
                        if r_sel.sucesso:
                            st.success(f"Frete selecionado: {r_sel.dados['transportadora']}")
                        else:
                            st.error(r_sel.erro)

                    codigo_rastreio_intl = st.text_input("Codigo de rastreio internacional", key=f"rastreio_{pac['id']}")
                    if st.button("Registrar envio", key=f"enviar_{pac['id']}"):
                        if not codigo_rastreio_intl:
                            st.error("Informe o codigo de rastreio antes de registrar o envio.")
                        else:
                            r_env = tool_registrar_envio(pac["id"], codigo_rastreio_intl)
                            if r_env.sucesso:
                                st.success("Envio registrado com sucesso.")
                            else:
                                st.error(r_env.erro)
                else:
                    st.info("Sem cotacoes para este pacote ainda.")
