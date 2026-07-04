"""Conexão e sessão do banco — SQLite (padrão) ou PostgreSQL via secrets."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# SQLite persistido no diretório de trabalho do Streamlit Cloud
DATABASE_URL = "sqlite:///compra_certa_usa.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()
