"""
Servidor MCP — Compra Certa USA
Expõe todas as tools de negócio via protocolo MCP (JSON-RPC/stdio).
Use com: mcp dev mcp_server.py
"""
import json
import sys
import os
from dataclasses import asdict
from typing import Optional

# Garante que o diretório do projeto está no path
sys.path.insert(0, os.path.dirname(__file__))

from mcp.server.fastmcp import FastMCP
from tools.tools import (
    tool_cadastrar_cliente,
    tool_autenticar_cliente,
    tool_criar_pedido,
    tool_atualizar_status_pedido,
    tool_registrar_chegada_warehouse,
    tool_calcular_orcamento,
    tool_sugerir_divisao_pacotes,
    tool_cotar_frete,
    tool_listar_pedidos_por_cliente,
    tool_detalhar_pedido,
    tool_listar_todos_pedidos,
    tool_listar_pacotes_sem_cotacao,
    tool_selecionar_cotacao_frete,
    tool_registrar_envio,
    tool_rastrear_pedido,
    tool_notificar_mudanca_status,
)

mcp = FastMCP("Compra Certa USA")


def _serializar(resultado) -> str:
    """Converte ToolResult (dataclass) para JSON string."""
    try:
        return json.dumps(asdict(resultado), ensure_ascii=False, indent=2)
    except Exception:
        return json.dumps({"sucesso": False, "erro": str(resultado)}, ensure_ascii=False)


# ── Clientes ──────────────────────────────────────────────────────────────────

@mcp.tool()
def cadastrar_cliente(nome: str, email: str, senha: str, cpf: str = None, telefone: str = None) -> str:
    """Cadastra um novo cliente na plataforma e gera seu endereço suite nos EUA."""
    return _serializar(tool_cadastrar_cliente(nome, email, senha, cpf, telefone))


@mcp.tool()
def autenticar_cliente(email: str, senha: str) -> str:
    """Autentica um cliente pelo e-mail e senha. Retorna dados do cliente se válido."""
    return _serializar(tool_autenticar_cliente(email, senha))


# ── Pedidos ───────────────────────────────────────────────────────────────────

@mcp.tool()
def criar_pedido(cliente_id: int, itens: list, tipo_servico: str = "padrao", observacoes: str = None) -> str:
    """
    Cria um novo pedido para o cliente.
    'itens' deve ser lista de objetos com: url_produto, descricao, quantidade, preco_unitario_usd, loja.
    'tipo_servico' aceita: economico, padrao, expresso.
    """
    return _serializar(tool_criar_pedido(cliente_id, itens, tipo_servico, observacoes))


@mcp.tool()
def atualizar_status_pedido(pedido_id: int, novo_status: str, observacao: str = None) -> str:
    """
    Atualiza o status de um pedido.
    Status válidos: aguardando_compra, comprado, em_transito_eua, no_warehouse,
                    em_transito_brasil, entregue, cancelado.
    """
    return _serializar(tool_atualizar_status_pedido(pedido_id, novo_status, observacao))


@mcp.tool()
def registrar_chegada_warehouse(
    pedido_id: int,
    peso_kg: float,
    altura_cm: float,
    largura_cm: float,
    comprimento_cm: float,
    foto_url: str = None,
    codigo_rastreio_eua: str = None,
) -> str:
    """Registra a chegada física de um pedido no warehouse nos EUA com suas dimensões e peso."""
    return _serializar(
        tool_registrar_chegada_warehouse(
            pedido_id, peso_kg, altura_cm, largura_cm, comprimento_cm, foto_url, codigo_rastreio_eua
        )
    )


@mcp.tool()
def listar_pedidos_por_cliente(cliente_id: int) -> str:
    """Lista todos os pedidos de um cliente específico com status atual."""
    return _serializar(tool_listar_pedidos_por_cliente(cliente_id))


@mcp.tool()
def detalhar_pedido(pedido_id: int) -> str:
    """Retorna detalhes completos de um pedido: itens, pacotes, orçamento e histórico de status."""
    return _serializar(tool_detalhar_pedido(pedido_id))


# ── Orçamento e Frete ─────────────────────────────────────────────────────────

@mcp.tool()
def calcular_orcamento(pedido_id: int, cotacao_dolar: float = None) -> str:
    """
    Calcula orçamento completo do pedido: produtos, taxa de serviço,
    frete estimado e impostos em BRL.
    """
    return _serializar(tool_calcular_orcamento(pedido_id, cotacao_dolar))


@mcp.tool()
def sugerir_divisao_pacotes(pedido_id: int) -> str:
    """Sugere como dividir os itens do pedido em pacotes para otimizar frete."""
    return _serializar(tool_sugerir_divisao_pacotes(pedido_id))


@mcp.tool()
def cotar_frete(pacote_id: int) -> str:
    """Retorna cotações de frete disponíveis para um pacote (econômico, padrão, expresso)."""
    return _serializar(tool_cotar_frete(pacote_id))


# ── Administração ─────────────────────────────────────────────────────────────

@mcp.tool()
def listar_todos_pedidos(status_filtro: str = None) -> str:
    """
    Lista todos os pedidos da plataforma (admin).
    Use 'status_filtro' para filtrar por status específico.
    """
    return _serializar(tool_listar_todos_pedidos(status_filtro))


@mcp.tool()
def listar_pacotes_sem_cotacao() -> str:
    """Lista pacotes que ainda não receberam cotação de frete (fila admin)."""
    return _serializar(tool_listar_pacotes_sem_cotacao())


@mcp.tool()
def selecionar_cotacao_frete(pacote_id: int, cotacao_id: int) -> str:
    """Seleciona uma cotação de frete aprovada para um pacote."""
    return _serializar(tool_selecionar_cotacao_frete(pacote_id, cotacao_id))


@mcp.tool()
def registrar_envio(pacote_id: int, codigo_rastreio_internacional: str) -> str:
    """Registra o envio de um pacote com código de rastreio internacional."""
    return _serializar(tool_registrar_envio(pacote_id, codigo_rastreio_internacional))


# ── Rastreamento ──────────────────────────────────────────────────────────────

@mcp.tool()
def rastrear_pedido(pedido_id: int, cliente_id: int) -> str:
    """Retorna histórico completo de rastreamento de um pedido."""
    return _serializar(tool_rastrear_pedido(pedido_id, cliente_id))


# ── Notificações ──────────────────────────────────────────────────────────────

@mcp.tool()
def notificar_mudanca_status(
    destinatario: str,
    nome_cliente: str,
    pedido_id: int,
    novo_status_label: str,
) -> str:
    """Envia e-mail ao cliente informando mudança de status do pedido."""
    resultado = tool_notificar_mudanca_status(destinatario, nome_cliente, pedido_id, novo_status_label)
    return json.dumps({"sucesso": resultado}, ensure_ascii=False)


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
