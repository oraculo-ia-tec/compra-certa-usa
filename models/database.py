"""Conexao e sessao do banco (SQLite inicial, preparado para PostgreSQL futuro)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from core.config import settings

DATABASE_URL = settings.DATABASE_URL or "sqlite:///compra_certa_usa.db"
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()
