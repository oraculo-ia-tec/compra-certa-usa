"""Assistente IA — Compra Certa USA."""
import base64
from PIL import Image
import streamlit as st
from components.ui import inject_css
from components.session import is_logged_in, get_current_user, get_user_id
from services.assistant import chat

inject_css()

# Ícone CCU como avatar do assistente
_ICON_AVATAR = Image.open("assets/icon.png")

# ── Cabeçalho: ícone centralizado com animação pulse ─────────────────────────
def _load_b64(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

_ICON_B64 = _load_b64("assets/icon.png")

st.html(f"""
<style>
@keyframes chat-icon-pulse {{
    0%   {{ transform: scale(1.00); opacity: 1; }}
    50%  {{ transform: scale(1.06); opacity: 0.88; }}
    100% {{ transform: scale(1.00); opacity: 1; }}
}}
.ccu-chat-icon-outer {{
    width: 180px; height: 180px;
    border-radius: 50%;
    border: none;
    margin: 0 auto 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #fff;
    padding: 0;
}}
.ccu-chat-icon-inner {{
    width: 100%; height: 100%;
    border-radius: 50%;
    overflow: hidden;
}}
.ccu-chat-icon-inner img {{
    width: 100%; height: 100%;
    object-fit: cover;
    display: block;
    animation: chat-icon-pulse 2.4s ease-in-out infinite;
    transform-origin: center center;
}}
</style>
<div style="text-align:center;padding:24px 0 8px;">
  <div class="ccu-chat-icon-outer">
    <div class="ccu-chat-icon-inner">
      <img src="data:image/png;base64,{_ICON_B64}" alt="Compra Certa USA">
    </div>
  </div>
  <p style="margin:0;font-size:.85rem;color:#64748B;">Tire dúvidas sobre compras, taxas e seus pedidos</p>
</div>
""")
st.divider()

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

# ── Sugestões rápidas (só aparecem com histórico vazio) ─────────────────────
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
                st.session_state["pending_question"] = s
                st.rerun()

st.divider()

# ── Exibe histórico de mensagens ──────────────────────────────────────────────
for msg in st.session_state["assistant_messages"]:
    avatar = "🧑" if msg["role"] == "user" else _ICON_AVATAR
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ── Captura entrada: botão de sugestão OU chat_input ─────────────────────────
pending_q  = st.session_state.pop("pending_question", None)
user_input = pending_q or st.chat_input("Digite sua dúvida sobre compras, taxas ou pedidos...")

if user_input:
    st.session_state["assistant_messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar=_ICON_AVATAR):
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
