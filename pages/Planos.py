"""Página de Planos de Assinatura — Compra Certa USA."""
import streamlit.components.v1 as components
import streamlit as st
from components.ui import page_header, inject_css
from components.session import is_logged_in, get_current_user, get_user_id
from services.stripe_service import (
    PLANOS, create_checkout_session, verify_checkout_session,
    activate_subscription, stripe_configurado,
)
from services.email_service import send_payment_success_email

inject_css()

# ── Verificar retorno do Stripe ───────────────────────────────────────────────
params = st.query_params
session_id = params.get("session_id")
cancelado  = params.get("cancelado")

if session_id:
    with st.spinner("Verificando pagamento..."):
        resultado = verify_checkout_session(session_id)
    if resultado and resultado.get("paid"):
        plano   = resultado["plano"]
        user_id = resultado["user_id"]
        activate_subscription(user_id, plano, extra=resultado)
        # Atualiza sessão se for o usuário atual
        if is_logged_in() and get_user_id() == user_id:
            st.session_state["user"]["subscription_active"] = True
            st.session_state["user"]["subscription_plan"]   = plano
        # Envia e-mail de confirmação
        try:
            user = get_current_user()
            send_payment_success_email(
                to_email=resultado.get("customer_email", user.get("email", "")),
                full_name=user.get("full_name", ""),
                plan_name=PLANOS.get(plano, {}).get("nome", plano.capitalize()),
            )
        except Exception:
            pass
        st.query_params.clear()
        st.success(
            f"🎉 Pagamento confirmado! Plano **{PLANOS.get(plano, {}).get('nome', plano)}** ativo. "
            "Um e-mail de confirmação foi enviado."
        )
    else:
        st.query_params.clear()
        st.error("❌ Não foi possível confirmar o pagamento. Tente novamente.")

elif cancelado:
    st.query_params.clear()
    st.info("ℹ️ Pagamento cancelado. Você pode escolher um plano quando quiser.")

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
page_header("Planos de Assinatura", "Escolha o plano ideal para suas importações.", "📦")

# ── Status atual ──────────────────────────────────────────────────────────────
if is_logged_in():
    user = get_current_user()
    if user.get("subscription_active"):
        plano_atual = user.get("subscription_plan", "")
        nome_plano  = PLANOS.get(plano_atual, {}).get("nome", plano_atual.capitalize() if plano_atual else "Ativo")
        st.success(f"✅ Você já tem o plano **{nome_plano}** ativo.")

# ── Cards dos planos ──────────────────────────────────────────────────────────
cols = st.columns(3)
for i, (slug, plano) in enumerate(PLANOS.items()):
    destaque = plano.get("destaque", False)
    cor      = plano["cor"]

    with cols[i]:
        with st.container(border=True):
            st.html(f"""
            <div style="text-align:center;padding:8px 0;">
              <div style="font-size:2.5rem;">{plano['emoji']}</div>
              <p style="margin:8px 0 4px;font-weight:800;font-size:1.2rem;color:{cor};">
                {plano['nome']}
              </p>
              <p style="margin:0;font-size:1.6rem;font-weight:700;color:#0F172A;">
                R$ {plano['preco_brl']:.2f}
                <span style="font-size:.8rem;font-weight:400;color:#64748B;">/mês</span>
              </p>
              <p style="margin:8px 0 4px;font-size:.85rem;color:#475569;font-weight:600;">
                {plano['pedidos']}
              </p>
              <hr style="border:none;border-top:1px solid #E2E8F0;margin:10px 0;">
              <p style="margin:0;font-size:.8rem;color:#64748B;">Fretes disponíveis:</p>
            </div>
            """)

            for frete in plano["fretes"]:
                st.write(f"✅ {frete}")

            st.caption(plano["descricao"])

            if destaque:
                st.html(
                    '<div style="text-align:center;margin:4px 0;">'
                    '<span style="background:#1E3A8A;color:#fff;border-radius:99px;'
                    'padding:3px 14px;font-size:.72rem;font-weight:700;">✨ Mais popular</span>'
                    '</div>'
                )

            btn_type = "primary" if destaque else "secondary"
            btn_label = f"Assinar {plano['nome']}"

            if st.button(btn_label, use_container_width=True,
                         key=f"plano_page_{slug}", type=btn_type):
                if not is_logged_in():
                    st.warning("Faça login para assinar.")
                    st.switch_page("pages/Login.py")
                elif not stripe_configurado():
                    st.error("Stripe não configurado. Contate o suporte.")
                else:
                    user = get_current_user()
                    url = create_checkout_session(
                        plano=slug,
                        user_email=user.get("email", ""),
                        user_id=get_user_id() or 0,
                    )
                    if url:
                        components.html(
                            f'<script>window.top.location.href="{url}";</script>',
                            height=0,
                        )
                    else:
                        st.error("Erro ao criar sessão de pagamento.")

# ── FAQ ───────────────────────────────────────────────────────────────────────
st.divider()
with st.expander("❓ Perguntas frequentes sobre os planos"):
    st.markdown("""
**Posso cancelar a qualquer momento?**
Sim. O cancelamento é feito direto pelo portal do Stripe, sem multa.

**Os pedidos são acumulativos?**
Não. Os pedidos reiniciam no início de cada ciclo mensal.

**Quais cartões são aceitos?**
Visa, Mastercard, Elo e American Express via Stripe (pagamento seguro).

**O plano inclui o endereço nos EUA?**
Sim. Todos os planos incluem seu endereço exclusivo em Miami (suite CCU).

**Posso mudar de plano?**
Sim. O upgrade é imediato e o downgrade entra no próximo ciclo.
""")

if not stripe_configurado():
    st.warning(
        "⚠️ **Modo de demonstração** — Stripe não configurado. "
        "Adicione as chaves nos Secrets do Streamlit Cloud para ativar os pagamentos.",
        icon="⚙️",
    )
