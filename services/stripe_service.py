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

def create_checkout_session(
    plano: str,
    user_email: str,
    user_id: int,
    user_name: str = "",
    user_phone: str = "",
) -> str | None:
    """Cria uma Stripe Checkout Session personalizada e retorna a URL de pagamento."""
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

    # Estados brasileiros para o campo UF
    _ESTADOS = [
        {"label": "Acre (AC)",              "value": "AC"},
        {"label": "Alagoas (AL)",           "value": "AL"},
        {"label": "Amapá (AP)",             "value": "AP"},
        {"label": "Amazonas (AM)",          "value": "AM"},
        {"label": "Bahia (BA)",             "value": "BA"},
        {"label": "Ceará (CE)",             "value": "CE"},
        {"label": "Distrito Federal (DF)",  "value": "DF"},
        {"label": "Espírito Santo (ES)",    "value": "ES"},
        {"label": "Goiás (GO)",             "value": "GO"},
        {"label": "Maranhão (MA)",          "value": "MA"},
        {"label": "Mato Grosso (MT)",       "value": "MT"},
        {"label": "Mato Grosso do Sul (MS)","value": "MS"},
        {"label": "Minas Gerais (MG)",      "value": "MG"},
        {"label": "Pará (PA)",              "value": "PA"},
        {"label": "Paraíba (PB)",           "value": "PB"},
        {"label": "Paraná (PR)",            "value": "PR"},
        {"label": "Pernambuco (PE)",        "value": "PE"},
        {"label": "Piauí (PI)",             "value": "PI"},
        {"label": "Rio de Janeiro (RJ)",    "value": "RJ"},
        {"label": "Rio Grande do Norte (RN)","value": "RN"},
        {"label": "Rio Grande do Sul (RS)", "value": "RS"},
        {"label": "Rondônia (RO)",          "value": "RO"},
        {"label": "Roraima (RR)",           "value": "RR"},
        {"label": "Santa Catarina (SC)",    "value": "SC"},
        {"label": "São Paulo (SP)",         "value": "SP"},
        {"label": "Sergipe (SE)",           "value": "SE"},
        {"label": "Tocantins (TO)",         "value": "TO"},
    ]

    try:
        import stripe
        stripe.api_key = api_key
        base_url = get_base_url()
        nome_plano = PLANOS.get(plano, {}).get("nome", plano.capitalize())

        session = stripe.checkout.Session.create(
            # ── Produto e modo ──────────────────────────────
            payment_method_types=["card", "pix"],
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],

            # ── Cliente ───────────────────────────────────
            customer_email=user_email or None,
            customer_creation="always",  # sempre cria/atualiza cliente no Stripe

            # ── Idioma e interface ──────────────────────────
            locale="pt-BR",

            # ── Coleta de dados adicionais ───────────────────
            phone_number_collection={"enabled": True},
            billing_address_collection="auto",

            # ── Campos personalizados (salvos em session.custom_fields) ─
            custom_fields=[
                {
                    "key": "cpf",
                    "label": {"type": "custom", "custom": "CPF (somente números)"},
                    "type": "text",
                    "optional": True,
                    "text": {"minimum_length": 11, "maximum_length": 14},
                },
                {
                    "key": "estado_uf",
                    "label": {"type": "custom", "custom": "Estado de destino"},
                    "type": "dropdown",
                    "optional": True,
                    "dropdown": {"options": _ESTADOS},
                },
            ],

            # ── Textos personalizados ──────────────────────────
            custom_text={
                "submit": {"message": f"Assinar plano {nome_plano} — Compra Certa USA"},
                "after_submit": {"message": "Você será redirecionado após a confirmação do pagamento."},
            },

            # ── Códigos promocionais ───────────────────────────
            allow_promotion_codes=True,

            # ── URLs de retorno ──────────────────────────────
            success_url=(
                f"{base_url}/Planos"
                f"?session_id={{CHECKOUT_SESSION_ID}}&plano={plano}&uid={user_id}"
            ),
            cancel_url=f"{base_url}/Planos?cancelado=1",

            # ── Metadados (salvos no Stripe e acessíveis via API) ──
            metadata={
                "user_id":    str(user_id),
                "plano":      plano,
                "user_name":  user_name,
                "user_email": user_email,
            },
        )
        logger.info(f"[stripe] Checkout criado: user_id={user_id}, plano={plano}")
        return session.url

    except Exception as e:
        logger.error(f"[stripe] Erro ao criar checkout: {e}")
        return None


def verify_checkout_session(session_id: str) -> dict | None:
    """Verifica o status de pagamento e extrai todos os dados coletados."""
    api_key = _get_secret("stripe", "STRIPE_API_KEY")
    if not api_key:
        return None

    try:
        import stripe
        stripe.api_key = api_key
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=["customer", "subscription"],
        )

        if session.payment_status != "paid":
            return {"paid": False}

        # Extrai campos personalizados
        custom = {cf.key: (cf.text.value if cf.type == "text" else cf.dropdown.value)
                  for cf in (session.custom_fields or [])}

        # Dados do cliente Stripe
        customer = session.customer
        stripe_customer_id = customer.id if hasattr(customer, "id") else str(customer)
        phone = getattr(customer, "phone", None) or session.customer_details.phone or ""

        return {
            "paid":               True,
            "plano":              session.metadata.get("plano"),
            "user_id":            int(session.metadata.get("user_id", 0)),
            "customer_email":     session.customer_email,
            "stripe_customer_id": stripe_customer_id,
            "phone":              phone,
            "cpf":                custom.get("cpf", ""),
            "estado_uf":          custom.get("estado_uf", ""),
            "subscription_id":    str(session.subscription) if session.subscription else "",
        }

    except Exception as e:
        logger.error(f"[stripe] Erro ao verificar sessão: {e}")
        return None


def activate_subscription(user_id: int, plano: str, extra: dict | None = None) -> bool:
    """Ativa a assinatura e salva dados extras do checkout no banco."""
    from models.database import get_session
    from models.models import User
    db = get_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        user.subscription_active = True
        user.subscription_plan   = plano
        if extra:
            if extra.get("stripe_customer_id"):
                user.stripe_customer_id = extra["stripe_customer_id"]
            if extra.get("subscription_id"):
                user.stripe_subscription_id = extra["subscription_id"]
            if extra.get("phone"):
                user.telefone = extra["phone"]
            if extra.get("cpf"):
                user.cpf = extra["cpf"]
            if extra.get("estado_uf"):
                user.estado_uf = extra["estado_uf"]
        db.commit()
        logger.info(f"[stripe] Assinatura ativada: user_id={user_id}, plano={plano}, stripe_id={extra.get('stripe_customer_id','') if extra else ''}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"[stripe] Erro ao ativar assinatura: {e}")
        return False
    finally:
        db.close()
