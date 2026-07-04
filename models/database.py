"""Conexão e sessão do banco (SQLite local ou PostgreSQL no Streamlit Cloud)."""
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from .models import Base
from core.config import settings


def _get_database_url() -> str:
    # 1. Tenta st.secrets (Streamlit Cloud)
    try:
        url = st.secrets["default"]["DATABASE_URL"]
        if url:
            # Normaliza dialeto para psycopg v3 (compatível com Python 3.12+)
            if url.startswith("postgresql+psycopg2://"):
                url = url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
            elif url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg://", 1)
            elif url.startswith("postgresql://") and "+" not in url.split("://")[0]:
                url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            return url
    except Exception:
        pass
    # 2. Tenta settings (variável de ambiente / .env)
    return settings.DATABASE_URL or "sqlite:///compra_certa_usa.db"


DATABASE_URL = _get_database_url()
_is_postgres = "postgresql" in DATABASE_URL or "postgres" in DATABASE_URL

if _is_postgres:
    engine = create_engine(DATABASE_URL, poolclass=NullPool, echo=False)
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()
