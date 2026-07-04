"""
AGENTE 2 - CORE-LOGIC
Contratos internos (DTOs) usando dataclasses.
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class ClienteCreateDTO:
    nome: str
    email: str
    senha: str
    cpf: Optional[str] = None
    telefone: Optional[str] = None


@dataclass
class ItemPedidoDTO:
    url_produto: str
    descricao: Optional[str] = None
    quantidade: int = 1
    preco_unitario_usd: Optional[float] = None
    loja: Optional[str] = None


@dataclass
class PedidoCreateDTO:
    cliente_id: int
    itens: List[ItemPedidoDTO] = field(default_factory=list)
    tipo_servico: str = "padrao"
    observacoes: Optional[str] = None


@dataclass
class OrcamentoResultDTO:
    pedido_id: int
    valor_produtos_usd: float
    taxa_servico_usd: float
    frete_estimado_usd: float
    imposto_estimado_brl: float
    cotacao_dolar: float
    total_estimado_brl: float


@dataclass
class DivisaoPacoteSugestaoDTO:
    pedido_id: int
    pacotes_sugeridos: List[List[int]]
    justificativa: str


@dataclass
class CotacaoFreteDTO:
    transportadora: str
    valor_usd: float
    prazo_dias: int


@dataclass
class ToolResult:
    sucesso: bool
    dados: Optional[dict] = None
    erro: Optional[str] = None
