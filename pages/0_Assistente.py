"""Assistente IA — Compra Certa USA."""
import streamlit as st
from components.ui import inject_css
from components.session import is_logged_in, get_current_user, get_user_id
from services.assistant import chat

inject_css()

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.html("""
<div style="display:flex;align-items:center;gap:.75rem;margin-bottom:.5rem;">
  <div style="background:#1E3A8A;border-radius:12px;width:48px;height:48px;
              display:flex;align-items:center;justify-content:center;font-size:24px;">🤖</div>
  <div>
    <p style="margin:0;font-size:1.4rem;font-weight:700;color:#1E3A8A;">Assistente Compra Certa USA</p>
    <p style="margin:0;font-size:.85rem;color:#64748B;">Tire dúvidas sobre compras, taxas e seus pedidos</p>
  </div>
</div>
<hr style="border:none;border-top:2px solid #E2E8F0;margin:.5rem 0 1rem;">
""")

# ── Contexto do usuário ────────────────────────────────────────────────────────
user_id   = get_user_id() if is_logged_in() else None
user_name = get_current_user().get("full_name") if is_logged_in() else None

if is_logged_in():
    st.caption(f"👤 Logado como **{user_name}** — posso consultar seus pedidos diretamente.")
else:
    st.info("💡 Faça login para que eu possa consultar seus pedidos e dar respostas personalizadas.")

# ── Inicializa histórico de mensagens ─────────────────────────────────────────
if "assistant_messages" not in st.session_state:
    st.session_state["assistant_messages"] = []

# ── Sugestões rápidas ─────────────────────────────────────────────────────────
if not st.session_state["assistant_messages"]:
    st.markdown("**Perguntas frequentes — clique para começar:**")
    sugestoes = [
        "Como funciona o processo de compra?",
        "Qual o imposto para uma compra de USD 200?",
        "Quais são os tipos de frete disponíveis?",
        "Quais produtos não podem ser enviados?",
    ]
    cols = st.columns(2)
    for i, s in enumerate(sugestoes):
        with cols[i % 2]:
            if st.button(s, use_container_width=True, key=f"sugestao_{i}"):
                st.session_state["assistant_messages"].append({"role": "user", "content": s})
                st.rerun()

st.divider()

# ── Exibe histórico de mensagens ──────────────────────────────────────────────
for msg in st.session_state["assistant_messages"]:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])

# ── Input do usuário ──────────────────────────────────────────────────────────
if prompt := st.chat_input("Digite sua dúvida sobre compras, taxas ou pedidos..."):
    st.session_state["assistant_messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Analisando..."):
            resposta = chat(
                messages=st.session_state["assistant_messages"],
                user_id=user_id,
                user_name=user_name,
            )
        st.markdown(resposta)

    st.session_state["assistant_messages"].append({"role": "assistant", "content": resposta})

# ── Rodapé com botão de limpar ────────────────────────────────────────────────
if st.session_state["assistant_messages"]:
    if st.button("🗑️ Limpar conversa", use_container_width=False):
        st.session_state["assistant_messages"] = []
        st.rerun()
