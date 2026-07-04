"""
AGENTE 2 - CORE-LOGIC
Tools internas (padrao MCP) executadas no mesmo processo do Streamlit.
"""
from models.database import get_session
from services.schemas import ClienteCreateDTO, PedidoCreateDTO, ItemPedidoDTO
from services.services import (
    ClienteService, PedidoService, OrcamentoService, DivisaoPacoteService, FreteService,
    ConsultaPedidoService, AdminService, RastreamentoService
)


def tool_cadastrar_cliente(nome: str, email: str, senha: str, cpf: str = None, telefone: str = None):
    session = get_session()
    try:
        dto = ClienteCreateDTO(nome=nome, email=email, senha=senha, cpf=cpf, telefone=telefone)
        return ClienteService(session).criar_cliente(dto)
    finally:
        session.close()


def tool_autenticar_cliente(email: str, senha: str):
    session = get_session()
    try:
        return ClienteService(session).autenticar(email, senha)
    finally:
        session.close()


def tool_criar_pedido(cliente_id: int, itens: list, tipo_servico: str = "padrao", observacoes: str = None):
    session = get_session()
    try:
        itens_dto = [ItemPedidoDTO(**item) for item in itens]
        dto = PedidoCreateDTO(cliente_id=cliente_id, itens=itens_dto, tipo_servico=tipo_servico, observacoes=observacoes)
        return PedidoService(session).criar_pedido(dto)
    finally:
        session.close()


def tool_atualizar_status_pedido(pedido_id: int, novo_status: str, observacao: str = None):
    session = get_session()
    try:
        return PedidoService(session).atualizar_status(pedido_id, novo_status, observacao)
    finally:
        session.close()


def tool_registrar_chegada_warehouse(pedido_id: int, peso_kg: float, altura_cm: float,
                                      largura_cm: float, comprimento_cm: float,
                                      foto_url: str = None, codigo_rastreio_eua: str = None):
    session = get_session()
    try:
        return PedidoService(session).registrar_chegada_warehouse(
            pedido_id, peso_kg, altura_cm, largura_cm, comprimento_cm, foto_url, codigo_rastreio_eua
        )
    finally:
        session.close()


def tool_calcular_orcamento(pedido_id: int, cotacao_dolar: float = None):
    session = get_session()
    try:
        return OrcamentoService(session).calcular_orcamento(pedido_id, cotacao_dolar)
    finally:
        session.close()


def tool_sugerir_divisao_pacotes(pedido_id: int):
    session = get_session()
    try:
        return DivisaoPacoteService(session).sugerir_divisao(pedido_id)
    finally:
        session.close()


def tool_cotar_frete(pacote_id: int):
    session = get_session()
    try:
        return FreteService(session).cotar_frete(pacote_id)
    finally:
        session.close()


def tool_listar_pedidos_por_cliente(cliente_id: int):
    session = get_session()
    try:
        return ConsultaPedidoService(session).listar_pedidos_por_cliente(cliente_id)
    finally:
        session.close()


def tool_detalhar_pedido(pedido_id: int):
    session = get_session()
    try:
        return ConsultaPedidoService(session).detalhar_pedido(pedido_id)
    finally:
        session.close()


def tool_listar_todos_pedidos(status_filtro: str = None):
    session = get_session()
    try:
        return AdminService(session).listar_todos_pedidos(status_filtro)
    finally:
        session.close()


def tool_listar_pacotes_sem_cotacao():
    session = get_session()
    try:
        return AdminService(session).listar_pacotes_sem_cotacao()
    finally:
        session.close()


def tool_selecionar_cotacao_frete(pacote_id: int, cotacao_id: int):
    session = get_session()
    try:
        return AdminService(session).selecionar_cotacao_frete(pacote_id, cotacao_id)
    finally:
        session.close()


def tool_registrar_envio(pacote_id: int, codigo_rastreio_internacional: str):
    session = get_session()
    try:
        return AdminService(session).registrar_envio(pacote_id, codigo_rastreio_internacional)
    finally:
        session.close()


def tool_rastrear_pedido(pedido_id: int, cliente_id: int):
    session = get_session()
    try:
        return RastreamentoService(session).rastrear_pedido(pedido_id, cliente_id)
    finally:
        session.close()


def tool_notificar_mudanca_status(destinatario: str, nome_cliente: str, pedido_id: int, novo_status_label: str):
    """Objetivo: enviar email ao cliente informando mudanca de status do pedido."""
    from services.email_service import EmailService
    return EmailService().notificar_mudanca_status(destinatario, nome_cliente, pedido_id, novo_status_label)
