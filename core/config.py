"""
AGENTE 2 - CORE-LOGIC
Camada central de configuracao. Le variaveis de ambiente tanto do arquivo .env
(execucao local, via python-dotenv) quanto do st.secrets (Streamlit Cloud),
suportando secrets organizados em secoes (ex: [default], [email]).

Prioridade de leitura: st.secrets (se disponivel) -> variaveis de ambiente (.env).
"""
import os
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import streamlit as st
    _HAS_STREAMLIT_SECRETS = True
except ImportError:
    _HAS_STREAMLIT_SECRETS = False


def _get_secret(chave: str, secao: Optional[str] = None, default: Optional[str] = None) -> Optional[str]:
    """
    Busca uma configuracao por chave (e secao opcional), tentando primeiro
    st.secrets (formato toml com secoes) e depois variaveis de ambiente
    (formato .env, sempre plano, sem secoes).
    """
    if _HAS_STREAMLIT_SECRETS:
        try:
            if secao and secao in st.secrets and chave in st.secrets[secao]:
                return st.secrets[secao][chave]
            if chave in st.secrets:
                return st.secrets[chave]
        except Exception:
            pass

    return os.getenv(chave, default)


class Settings:
    """Configuracoes centralizadas do projeto, carregadas uma unica vez."""

    # ---- Banco de dados ----
    DATABASE_URL: str = _get_secret("DATABASE_URL", default="sqlite:///compra_certa_usa.db") or "sqlite:///compra_certa_usa.db"

    # ---- Aplicacao ----
    APP_BASE_URL: str = _get_secret("APP_BASE_URL", default="http://localhost:8501")
    ADMIN_PASSWORD: str = _get_secret("ADMIN_PASSWORD", default="admin123")

    # ---- IA (Groq) ----
    GROQ_API_KEY: Optional[str] = _get_secret("GROQ_API_KEY")

    # ---- Email SMTP (secao [email]) ----
    EMAIL_HOST: Optional[str] = _get_secret("EMAIL_HOST", secao="email")
    EMAIL_PORT: int = int(_get_secret("EMAIL_PORT", secao="email", default="587") or 587)
    EMAIL_USERNAME: Optional[str] = _get_secret("EMAIL_USERNAME", secao="email")
    EMAIL_PASSWORD: Optional[str] = _get_secret("EMAIL_PASSWORD", secao="email")
    EMAIL_USE_TLS: bool = str(_get_secret("EMAIL_USE_TLS", secao="email", default="true")).lower() == "true"
    EMAIL_USE_SSL: bool = str(_get_secret("EMAIL_USE_SSL", secao="email", default="false")).lower() == "true"
    EMAIL_REMETENTE: Optional[str] = _get_secret("EMAIL_REMETENTE", secao="email")

    # ---- Stripe (preparado, ainda inativo) ----
    STRIPE_API_KEY: Optional[str] = _get_secret("STRIPE_API_KEY")
    STRIPE_API_VERSION: str = _get_secret("STRIPE_API_VERSION", default="2024-06-20")
    STRIPE_TIMEOUT: int = int(_get_secret("STRIPE_TIMEOUT", default="10") or 10)
    STRIPE_MAX_RETRIES: int = int(_get_secret("STRIPE_MAX_RETRIES", default="2") or 2)

    @classmethod
    def email_configurado(cls) -> bool:
        return bool(cls.EMAIL_HOST and cls.EMAIL_USERNAME and cls.EMAIL_PASSWORD)

    @classmethod
    def stripe_configurado(cls) -> bool:
        return bool(cls.STRIPE_API_KEY)

    @classmethod
    def groq_configurado(cls) -> bool:
        return bool(cls.GROQ_API_KEY)


settings = Settings()
