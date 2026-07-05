"""Assistente IA — Compra Certa USA."""
import base64
import streamlit.components.v1 as components
from PIL import Image
import streamlit as st
from components.ui import inject_css
from components.session import is_logged_in, get_current_user, get_user_id
from services.assistant import chat
from services.stripe_service import PLANOS, create_checkout_session, stripe_configurado

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

# ── Contexto de assinatura do usuário logado ────────────────────────────────
user_id   = get_user_id() if is_logged_in() else None
user_name = get_current_user().get("full_name") if is_logged_in() else None
_user_ctx = get_current_user() if is_logged_in() else {}
sub_active = bool(_user_ctx.get("subscription_active"))
sub_plan   = _user_ctx.get("subscription_plan")

if is_logged_in():
    st.caption(f"👤 Logado como **{user_name}**" + (f" — Plano **{sub_plan.capitalize()}**" if sub_plan else "") + " — posso consultar seus pedidos.")
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
                subscription_active=sub_active,
                subscription_plan=sub_plan,
            )
        st.markdown(resposta)

    st.session_state["assistant_messages"].append({"role": "assistant", "content": resposta})

# ── Widget de planos (ativado pelo LLM) ───────────────────────────────────────
def render_plans_widget():
    flow = st.session_state.get("flow_state")
    if flow not in ("mostrar_planos", "upgrade_premium", "upgrade_pro"):
        return

    plano_sugerido = st.session_state.get("plano_sugerido", "pro")
    is_upgrade = flow in ("upgrade_premium", "upgrade_pro")

    if flow == "upgrade_premium":
        planos_exibir = {"premium": PLANOS["premium"]}
    elif flow == "upgrade_pro":
        planos_exibir = {"pro": PLANOS["pro"]}
    else:
        planos_exibir = PLANOS

    with st.container(border=True):
        if flow == "upgrade_premium":
            st.markdown("### ⬆️ Upgrade: Pro → Premium")
            st.html("""
            <div style="display:flex;gap:12px;margin-bottom:12px;">
              <div style="flex:1;background:#F1F5F9;border-radius:8px;padding:12px;">
                <p style="margin:0;font-weight:700;color:#64748B;">Seu plano atual — Pro</p>
                <p style="margin:4px 0 0;font-size:.85rem;color:#64748B;">
                  10 pedidos/mês · Econômico + Padrão<br>R$ 59,90/mês
                </p>
              </div>
              <div style="display:flex;align-items:center;font-size:1.5rem;">→</div>
              <div style="flex:1;background:#EFF6FF;border:2px solid #D97706;border-radius:8px;padding:12px;">
                <p style="margin:0;font-weight:700;color:#D97706;">👑 Premium</p>
                <p style="margin:4px 0 0;font-size:.85rem;color:#475569;">
                  Pedidos ilimitados · + Expresso (5-10 dias)<br>R$ 99,90/mês
                </p>
              </div>
            </div>
            """)
        elif flow == "upgrade_pro":
            st.markdown("### ⬆️ Upgrade: Starter → Pro")
        else:
            st.markdown("### 📦 Planos de Assinatura — Compra Certa USA")
            st.caption("Escolha o plano ideal para suas importações")

        ncols = max(len(planos_exibir), 1)
        cols  = st.columns(ncols) if ncols > 1 else st.columns([1, 2, 1])
        col_list = [cols[1]] if ncols == 1 else cols

        for i, (slug, plano) in enumerate(planos_exibir.items()):
            destaque = True if is_upgrade else (plano.get("destaque", False) or slug == plano_sugerido)
            cor   = plano["cor"]
            borda = cor if destaque else "#E2E8F0"
            fundo = "#EFF6FF" if destaque else "#F8FAFC"

            with col_list[i]:
                st.html(f"""
                <div style="border:2px solid {borda};border-radius:12px;
                            padding:18px 12px;background:{fundo};text-align:center;margin-bottom:4px;">
                  <div style="font-size:2rem;">{plano['emoji']}</div>
                  <p style="margin:6px 0 2px;font-weight:800;font-size:1.05rem;color:{cor};">
                    {plano['nome']}
                  </p>
                  <p style="margin:0;font-size:1.4rem;font-weight:700;color:#0F172A;">
                    R$ {plano['preco_brl']:.2f}
                    <span style="font-size:.75rem;font-weight:400;color:#64748B;">/mês</span>
                  </p>
                  <p style="margin:6px 0 4px;font-size:.8rem;color:#475569;">{plano['pedidos']}</p>
                  <p style="margin:0;font-size:.72rem;color:#94A3B8;">{" · ".join(plano['fretes'])}</p>
                </div>
                """)
                btn_label = f"Fazer upgrade para {plano['nome']}" if is_upgrade else f"Assinar {plano['nome']}"
                if st.button(btn_label, use_container_width=True, key=f"btn_plano_{slug}", type="primary"):
                    if not is_logged_in():
                        # Salva plano escolhido e redireciona para cadastro
                        st.session_state["pending_plan"] = slug
                        st.switch_page("pages/Cadastro.py")
                    elif not stripe_configurado():
                        st.error("⚠️ Stripe não configurado. Adicione STRIPE_API_KEY nos Secrets.")
                    else:
                        user = get_current_user()
                        checkout_url = create_checkout_session(
                            plano=slug, user_email=user.get("email", ""), user_id=get_user_id() or 0,
                        )
                        if checkout_url:
                            st.session_state["flow_state"] = None
                            components.html(f'<script>window.top.location.href="{checkout_url}";</script>', height=0)
                        else:
                            st.error("Erro ao criar sessão de pagamento.")

        st.divider()
        if st.button("✕ Fechar", key="fechar_widget_planos"):
            st.session_state["flow_state"] = None
            st.rerun()

render_plans_widget()

# ── Rodapé com botão de limpar ────────────────────────────────────────────────
if st.session_state["assistant_messages"]:
    if st.button("🗑️ Limpar conversa", use_container_width=False, key="btn_limpar_conversa"):
        st.session_state["assistant_messages"] = []
        st.session_state["flow_state"] = None
        st.rerun()
