"""
AGENTE 1 - DBA-ARCH
Modelagem inicial do banco de dados (SQLite via SQLAlchemy).
"""
import enum
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, Text
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column

Base = declarative_base()

_E = dict(native_enum=False)

# ---------------------------------------------------------------------------
# Enums de autenticação
# ---------------------------------------------------------------------------

class UserRole(str, enum.Enum):
    ADMIN        = "admin"
    OPERATOR     = "operator"
    CLIENT       = "client"
    AI_DEVELOPER = "ai_developer"


class UserStatus(str, enum.Enum):
    PENDING  = "pending"
    ACTIVE   = "active"
    INACTIVE = "inactive"
    BANNED   = "banned"


# ---------------------------------------------------------------------------
# Modelo de usuário (autenticação)
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id:              Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    full_name:       Mapped[str]           = mapped_column(String(150), nullable=False)
    email:           Mapped[str]           = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str]           = mapped_column(String(512), nullable=False)
    role:            Mapped[UserRole]      = mapped_column(SAEnum(UserRole,   **_E), default=UserRole.CLIENT)
    status:          Mapped[UserStatus]    = mapped_column(SAEnum(UserStatus, **_E), default=UserStatus.PENDING)

    # Verificação de e-mail
    is_email_confirmed:           Mapped[bool]           = mapped_column(Boolean,      default=False)
    verification_code:            Mapped[str | None]     = mapped_column(String(512),  nullable=True)
    verification_code_expires_at: Mapped[datetime | None] = mapped_column(DateTime,    nullable=True)
    verification_attempts:        Mapped[int]            = mapped_column(Integer,      default=0)
    last_code_sent_at:            Mapped[datetime | None] = mapped_column(DateTime,    nullable=True)

    # Token de ativação (legado / seed admin)
    activation_token:             Mapped[str | None]     = mapped_column(String(512),  nullable=True)
    activation_token_expires_at:  Mapped[datetime | None] = mapped_column(DateTime,    nullable=True)

    # Perfil e acesso
    avatar_url:           Mapped[str | None]  = mapped_column(Text,    nullable=True)
    is_first_access:      Mapped[bool]        = mapped_column(Boolean, default=True)
    subscription_active:      Mapped[bool]        = mapped_column(Boolean, default=False)
    subscription_plan:        Mapped[str | None]   = mapped_column(String(20), nullable=True)
    stripe_customer_id:       Mapped[str | None]   = mapped_column(String(64), nullable=True)
    stripe_subscription_id:   Mapped[str | None]   = mapped_column(String(64), nullable=True)
    telefone:                 Mapped[str | None]   = mapped_column(String(30), nullable=True)
    cpf:                      Mapped[str | None]   = mapped_column(String(14), nullable=True)
    estado_uf:                Mapped[str | None]   = mapped_column(String(2),  nullable=True)
    last_login_at:        Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_login_ip:        Mapped[str | None]  = mapped_column(String(45), nullable=True)
    created_at:           Mapped[datetime]    = mapped_column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Enums de pedidos
# ---------------------------------------------------------------------------

class StatusPedido(PyEnum):
    AGUARDANDO_COMPRA = "aguardando_compra"
    AGUARDANDO_CHEGADA_EUA = "aguardando_chegada_eua"
    RECEBIDO_WAREHOUSE = "recebido_warehouse"
    EM_CONSOLIDACAO = "em_consolidacao"
    FRETE_COTADO = "frete_cotado"
    ENVIADO = "enviado"
    EM_TRANSITO = "em_transito"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"


class TipoServico(PyEnum):
    ECONOMICO = "economico"
    PADRAO = "padrao"
    EXPRESSO = "expresso"


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True)
    nome = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False, unique=True, index=True)
    senha_hash = Column(String(255), nullable=False)
    cpf = Column(String(14), unique=True, nullable=True)
    telefone = Column(String(20), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    ativo = Column(Boolean, default=True)

    endereco_operacional = relationship("EnderecoOperacional", back_populates="cliente", uselist=False)
    pedidos = relationship("Pedido", back_populates="cliente")


class EnderecoOperacional(Base):
    __tablename__ = "enderecos_operacionais"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, unique=True)
    codigo_suite = Column(String(20), nullable=False, unique=True)
    rua = Column(String(120), nullable=False)
    cidade = Column(String(60), nullable=False)
    estado = Column(String(2), nullable=False)
    cep = Column(String(10), nullable=False)
    pais = Column(String(30), default="EUA")

    cliente = relationship("Cliente", back_populates="endereco_operacional")


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    status = Column(Enum(StatusPedido), default=StatusPedido.AGUARDANDO_COMPRA, nullable=False)
    tipo_servico = Column(Enum(TipoServico), default=TipoServico.PADRAO)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    observacoes = Column(Text, nullable=True)

    cliente = relationship("Cliente", back_populates="pedidos")
    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")
    pacotes = relationship("Pacote", back_populates="pedido", cascade="all, delete-orphan")
    orcamento = relationship("Orcamento", back_populates="pedido", uselist=False, cascade="all, delete-orphan")
    historico_status = relationship("StatusHistorico", back_populates="pedido", cascade="all, delete-orphan")


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    url_produto = Column(String(500), nullable=False)
    descricao = Column(String(255), nullable=True)
    quantidade = Column(Integer, default=1)
    preco_unitario_usd = Column(Float, nullable=True)
    loja = Column(String(80), nullable=True)

    pedido = relationship("Pedido", back_populates="itens")


class Pacote(Base):
    __tablename__ = "pacotes"

    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    codigo_rastreio_eua = Column(String(80), nullable=True)
    peso_kg = Column(Float, nullable=True)
    altura_cm = Column(Float, nullable=True)
    largura_cm = Column(Float, nullable=True)
    comprimento_cm = Column(Float, nullable=True)
    foto_url = Column(String(255), nullable=True)
    recebido_em = Column(DateTime, nullable=True)

    pedido = relationship("Pedido", back_populates="pacotes")
    cotacoes = relationship("CotacaoFrete", back_populates="pacote", cascade="all, delete-orphan")
    remessa = relationship("Remessa", back_populates="pacote", uselist=False, cascade="all, delete-orphan")


class Orcamento(Base):
    __tablename__ = "orcamentos"

    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False, unique=True)
    valor_produtos_usd = Column(Float, default=0.0)
    taxa_servico_usd = Column(Float, default=0.0)
    frete_estimado_usd = Column(Float, default=0.0)
    imposto_estimado_brl = Column(Float, default=0.0)
    cotacao_dolar = Column(Float, nullable=True)
    total_estimado_brl = Column(Float, default=0.0)
    criado_em = Column(DateTime, default=datetime.utcnow)

    pedido = relationship("Pedido", back_populates="orcamento")


class CotacaoFrete(Base):
    __tablename__ = "cotacoes_frete"

    id = Column(Integer, primary_key=True)
    pacote_id = Column(Integer, ForeignKey("pacotes.id"), nullable=False)
    transportadora = Column(String(30), nullable=False)
    valor_usd = Column(Float, nullable=False)
    prazo_dias = Column(Integer, nullable=True)
    selecionada = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)

    pacote = relationship("Pacote", back_populates="cotacoes")


class Remessa(Base):
    __tablename__ = "remessas"

    id = Column(Integer, primary_key=True)
    pacote_id = Column(Integer, ForeignKey("pacotes.id"), nullable=False, unique=True)
    transportadora = Column(String(30), nullable=False)
    codigo_rastreio_internacional = Column(String(80), nullable=True)
    status_transportadora = Column(String(80), nullable=True)
    enviado_em = Column(DateTime, nullable=True)
    entregue_em = Column(DateTime, nullable=True)

    pacote = relationship("Pacote", back_populates="remessa")


class StatusHistorico(Base):
    __tablename__ = "status_historico"

    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    status = Column(Enum(StatusPedido), nullable=False)
    observacao = Column(String(255), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    pedido = relationship("Pedido", back_populates="historico_status")
