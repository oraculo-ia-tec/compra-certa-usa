"""
Integração com Stripe — assinaturas da Compra Certa USA.
"""
import streamlit as st
from loguru import logger

# ── Definição dos planos ───────────────────────────────────────────────────────
PLANOS = {
    "starter": {
        "nome":       "Starter",
        "emoji":      "🌱",
        "preco_brl":  29.90,
        "pedidos":    "3 pedidos / mês",
        "fretes":     ["Econômico"],
        "cor":        "#64748B",
        "descricao":  "Ideal para começar a importar",
        "destaque":   False,
    },
    "pro": {
        "nome":       "Pro",
        "emoji":      "⭐",
        "preco_brl":  59.90,
        "pedidos":    "10 pedidos / mês",
        "fretes":     ["Econômico", "Padrão"],
        "cor":        "#1E3A8A",
        "descricao":  "O mais popular — equilíbrio perfeito",
        "destaque":   True,
    },
    "premium": {
        "nome":       "Premium",
        "emoji":      "👑",
        "preco_brl":  99.90,
        "pedidos":    "Ilimitado",
        "fretes":     ["Econômico", "Padrão", "Expresso"],
        "cor":        "#D97706",
        "descricao":  "Para quem importa com frequência",
        "destaque":   False,
    },
}


def _get_secret(section: str, key: str) -> str | None:
    for getter in [
        lambda: st.secrets[section][key],
        lambda: st.secrets["default"][key],
        lambda: st.secrets[key],
    ]:
        try:
            val = getter()
            if val:
                return val
        except Exception:
            pass
    return None


def stripe_configurado() -> bool:
    return bool(_get_secret("stripe", "STRIPE_API_KEY"))


def get_base_url() -> str:
    url = _get_secret("default", "APP_BASE_URL") or "http://localhost:8501"
    return url.rstrip("/")


def create_checkout_session(plano: str, user_email: str, user_id: int) -> str | None:
    """Cria uma Stripe Checkout Session e retorna a URL de pagamento."""
    api_key = _get_secret("stripe", "STRIPE_API_KEY")
    if not api_key:
        logger.error("[stripe] STRIPE_API_KEY não configurada")
        return None

    key_map = {
        "starter": "STRIPE_PRICE_STARTER",
        "pro":     "STRIPE_PRICE_PRO",
        "premium": "STRIPE_PRICE_PREMIUM",
    }
    price_id = _get_secret("stripe", key_map.get(plano, ""))
    if not price_id:
        logger.error(f"[stripe] Price ID não configurado para plano: {plano}")
        return None

    try:
        import stripe
        stripe.api_key = api_key
        base_url = get_base_url()

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=user_email or None,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=(
                f"{base_url}/Planos"
                f"?session_id={{CHECKOUT_SESSION_ID}}&plano={plano}&uid={user_id}"
            ),
            cancel_url=f"{base_url}/Planos?cancelado=1",
            metadata={"user_id": str(user_id), "plano": plano},
        )
        logger.info(f"[stripe] Checkout criado: user_id={user_id}, plano={plano}")
        return session.url

    except Exception as e:
        logger.error(f"[stripe] Erro ao criar checkout: {e}")
        return None


def verify_checkout_session(session_id: str) -> dict | None:
    """Verifica o status de pagamento após retorno do Stripe."""
    api_key = _get_secret("stripe", "STRIPE_API_KEY")
    if not api_key:
        return None

    try:
        import stripe
        stripe.api_key = api_key
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == "paid":
            return {
                "paid":           True,
                "plano":          session.metadata.get("plano"),
                "user_id":        int(session.metadata.get("user_id", 0)),
                "customer_email": session.customer_email,
            }
        return {"paid": False}

    except Exception as e:
        logger.error(f"[stripe] Erro ao verificar sessão: {e}")
        return None


def activate_subscription(user_id: int, plano: str) -> bool:
    """Ativa a assinatura do usuário no banco de dados."""
    from models.database import get_session
    from models.models import User
    db = get_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        user.subscription_active = True
        user.subscription_plan   = plano
        db.commit()
        logger.info(f"[stripe] Assinatura ativada: user_id={user_id}, plano={plano}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"[stripe] Erro ao ativar assinatura: {e}")
        return False
    finally:
        db.close()
