"""
AGENTE 2 - CORE-LOGIC
Services de negocio.
"""
from datetime import datetime
from typing import Optional
import hashlib
import random
import string

from sqlalchemy.orm import Session

from models.models import (
    Cliente, EnderecoOperacional, Pedido, ItemPedido, Pacote,
    Orcamento, CotacaoFrete, Remessa, StatusHistorico, StatusPedido, TipoServico
)
from services.schemas import ClienteCreateDTO, PedidoCreateDTO, ToolResult


def _hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def _gerar_codigo_suite() -> str:
    sufixo = "".join(random.choices(string.digits, k=5))
    return f"CCU-{sufixo}"


class ClienteService:
    def __init__(self, session: Session):
        self.session = session

    def criar_cliente(self, dto: ClienteCreateDTO) -> ToolResult:
        existente = self.session.query(Cliente).filter_by(email=dto.email).first()
        if existente:
            return ToolResult(sucesso=False, erro="Email ja cadastrado")

        cliente = Cliente(
            nome=dto.nome, email=dto.email, senha_hash=_hash_senha(dto.senha),
            cpf=dto.cpf, telefone=dto.telefone,
        )
        self.session.add(cliente)
        self.session.flush()

        endereco = EnderecoOperacional(
            cliente_id=cliente.id, codigo_suite=_gerar_codigo_suite(),
            rua="1234 Warehouse Blvd", cidade="Miami", estado="FL", cep="33101", pais="EUA",
        )
        self.session.add(endereco)
        self.session.commit()

        return ToolResult(sucesso=True, dados={"cliente_id": cliente.id, "codigo_suite": endereco.codigo_suite})

    def autenticar(self, email: str, senha: str) -> ToolResult:
        cliente = self.session.query(Cliente).filter_by(email=email).first()
        if not cliente or cliente.senha_hash != _hash_senha(senha):
            return ToolResult(sucesso=False, erro="Credenciais invalidas")
        return ToolResult(sucesso=True, dados={"cliente_id": cliente.id, "nome": cliente.nome})


class PedidoService:
    def __init__(self, session: Session):
        self.session = session

    def criar_pedido(self, dto: PedidoCreateDTO) -> ToolResult:
        cliente = self.session.query(Cliente).get(dto.cliente_id)
        if not cliente:
            return ToolResult(sucesso=False, erro="Cliente nao encontrado")

        pedido = Pedido(cliente_id=dto.cliente_id, tipo_servico=TipoServico(dto.tipo_servico), observacoes=dto.observacoes)
        self.session.add(pedido)
        self.session.flush()

        for item in dto.itens:
            self.session.add(ItemPedido(
                pedido_id=pedido.id, url_produto=item.url_produto, descricao=item.descricao,
                quantidade=item.quantidade, preco_unitario_usd=item.preco_unitario_usd, loja=item.loja,
            ))

        self.session.add(StatusHistorico(pedido_id=pedido.id, status=StatusPedido.AGUARDANDO_COMPRA, observacao="Pedido criado"))
        self.session.commit()
        return ToolResult(sucesso=True, dados={"pedido_id": pedido.id})

    def atualizar_status(self, pedido_id: int, novo_status: str, observacao: Optional[str] = None,
                          notificar_email: bool = True) -> ToolResult:
        pedido = self.session.query(Pedido).get(pedido_id)
        if not pedido:
            return ToolResult(sucesso=False, erro="Pedido nao encontrado")
        try:
            status_enum = StatusPedido(novo_status)
        except ValueError:
            return ToolResult(sucesso=False, erro="Status invalido")

        pedido.status = status_enum
        pedido.atualizado_em = datetime.utcnow()
        self.session.add(StatusHistorico(pedido_id=pedido.id, status=status_enum, observacao=observacao))
        self.session.commit()

        if notificar_email and pedido.cliente:
            try:
                from services.email_service import EmailService
                EmailService().notificar_mudanca_status(
                    destinatario=pedido.cliente.email,
                    nome_cliente=pedido.cliente.nome,
                    pedido_id=pedido.id,
                    novo_status_label=status_enum.value.replace("_", " ").capitalize(),
                )
            except Exception:
                pass  # Falha de notificacao nao deve bloquear a atualizacao de status

        return ToolResult(sucesso=True, dados={"pedido_id": pedido.id, "status": status_enum.value})

    def registrar_chegada_warehouse(self, pedido_id: int, peso_kg: float, altura_cm: float,
                                     largura_cm: float, comprimento_cm: float,
                                     foto_url: Optional[str] = None,
                                     codigo_rastreio_eua: Optional[str] = None) -> ToolResult:
        pedido = self.session.query(Pedido).get(pedido_id)
        if not pedido:
            return ToolResult(sucesso=False, erro="Pedido nao encontrado")

        pacote = Pacote(
            pedido_id=pedido_id, peso_kg=peso_kg, altura_cm=altura_cm, largura_cm=largura_cm,
            comprimento_cm=comprimento_cm, foto_url=foto_url, codigo_rastreio_eua=codigo_rastreio_eua,
            recebido_em=datetime.utcnow(),
        )
        self.session.add(pacote)
        pedido.status = StatusPedido.RECEBIDO_WAREHOUSE
        self.session.add(StatusHistorico(pedido_id=pedido_id, status=StatusPedido.RECEBIDO_WAREHOUSE,
                                          observacao="Pacote recebido no warehouse EUA"))
        self.session.commit()
        return ToolResult(sucesso=True, dados={"pacote_id": pacote.id})


class OrcamentoService:
    TAXA_SERVICO_BASE_USD = 15.0
    COTACAO_DOLAR_PADRAO = 5.4

    def __init__(self, session: Session):
        self.session = session

    def calcular_orcamento(self, pedido_id: int, cotacao_dolar: Optional[float] = None) -> ToolResult:
        pedido = self.session.query(Pedido).get(pedido_id)
        if not pedido:
            return ToolResult(sucesso=False, erro="Pedido nao encontrado")

        valor_produtos = sum((item.preco_unitario_usd or 0) * item.quantidade for item in pedido.itens)
        frete_estimado = self._estimar_frete(pedido)
        taxa_servico = self.TAXA_SERVICO_BASE_USD
        dolar = cotacao_dolar or self.COTACAO_DOLAR_PADRAO

        subtotal_usd = valor_produtos + frete_estimado + taxa_servico
        imposto_estimado_brl = max(0.0, (valor_produtos * dolar) - 1000.0) * 0.6
        total_brl = subtotal_usd * dolar + imposto_estimado_brl

        orcamento = pedido.orcamento or Orcamento(pedido_id=pedido_id)
        orcamento.valor_produtos_usd = valor_produtos
        orcamento.taxa_servico_usd = taxa_servico
        orcamento.frete_estimado_usd = frete_estimado
        orcamento.imposto_estimado_brl = imposto_estimado_brl
        orcamento.cotacao_dolar = dolar
        orcamento.total_estimado_brl = total_brl

        self.session.add(orcamento)
        self.session.commit()

        return ToolResult(sucesso=True, dados={
            "pedido_id": pedido_id, "valor_produtos_usd": valor_produtos, "taxa_servico_usd": taxa_servico,
            "frete_estimado_usd": frete_estimado, "imposto_estimado_brl": imposto_estimado_brl,
            "cotacao_dolar": dolar, "total_estimado_brl": total_brl,
        })

    def _estimar_frete(self, pedido: Pedido) -> float:
        fatores = {"economico": 8.0, "padrao": 15.0, "expresso": 30.0}
        return fatores.get(pedido.tipo_servico.value, 15.0)


class DivisaoPacoteService:
    LIMITE_KG_ECONOMICO = 2.0

    def __init__(self, session: Session):
        self.session = session

    def sugerir_divisao(self, pedido_id: int) -> ToolResult:
        pedido = self.session.query(Pedido).get(pedido_id)
        if not pedido:
            return ToolResult(sucesso=False, erro="Pedido nao encontrado")

        itens_ids = [item.id for item in pedido.itens]
        if not itens_ids:
            return ToolResult(sucesso=False, erro="Pedido sem itens para dividir")

        grupos = [itens_ids[i:i + 3] for i in range(0, len(itens_ids), 3)]
        return ToolResult(sucesso=True, dados={
            "pedido_id": pedido_id, "pacotes_sugeridos": grupos,
            "justificativa": "Agrupamento provisorio por lote de 3 itens; ajustar quando houver peso/dimensao reais por item.",
        })


class FreteService:
    def __init__(self, session: Session):
        self.session = session

    def cotar_frete(self, pacote_id: int) -> ToolResult:
        pacote = self.session.query(Pacote).get(pacote_id)
        if not pacote:
            return ToolResult(sucesso=False, erro="Pacote nao encontrado")

        peso = pacote.peso_kg or 1.0
        cotacoes_simuladas = [
            {"transportadora": "FedEx", "valor_usd": round(12 + peso * 6.5, 2), "prazo_dias": 5},
            {"transportadora": "UPS", "valor_usd": round(10 + peso * 7.0, 2), "prazo_dias": 6},
            {"transportadora": "DHL", "valor_usd": round(14 + peso * 6.0, 2), "prazo_dias": 4},
        ]
        for c in cotacoes_simuladas:
            self.session.add(CotacaoFrete(pacote_id=pacote_id, transportadora=c["transportadora"],
                                           valor_usd=c["valor_usd"], prazo_dias=c["prazo_dias"]))
        self.session.commit()
        return ToolResult(sucesso=True, dados={"pacote_id": pacote_id, "cotacoes": cotacoes_simuladas})


class ConsultaPedidoService:
    def __init__(self, session: Session):
        self.session = session

    def listar_pedidos_por_cliente(self, cliente_id: int) -> ToolResult:
        pedidos = self.session.query(Pedido).filter_by(cliente_id=cliente_id).order_by(Pedido.criado_em.desc()).all()
        lista = [{
            "pedido_id": p.id, "status": p.status.value, "tipo_servico": p.tipo_servico.value,
            "criado_em": p.criado_em.strftime("%d/%m/%Y %H:%M") if p.criado_em else None,
            "qtd_itens": len(p.itens), "qtd_pacotes": len(p.pacotes),
        } for p in pedidos]
        return ToolResult(sucesso=True, dados={"pedidos": lista})

    def detalhar_pedido(self, pedido_id: int) -> ToolResult:
        pedido = self.session.query(Pedido).get(pedido_id)
        if not pedido:
            return ToolResult(sucesso=False, erro="Pedido nao encontrado")

        itens = [{
            "id": i.id, "url_produto": i.url_produto, "descricao": i.descricao,
            "quantidade": i.quantidade, "preco_unitario_usd": i.preco_unitario_usd, "loja": i.loja,
        } for i in pedido.itens]

        pacotes = [{
            "id": pk.id, "codigo_rastreio_eua": pk.codigo_rastreio_eua, "peso_kg": pk.peso_kg,
            "foto_url": pk.foto_url,
            "recebido_em": pk.recebido_em.strftime("%d/%m/%Y %H:%M") if pk.recebido_em else None,
            "cotacoes": [{
                "id": c.id, "transportadora": c.transportadora, "valor_usd": c.valor_usd,
                "prazo_dias": c.prazo_dias, "selecionada": c.selecionada,
            } for c in pk.cotacoes],
            "remessa": ({
                "transportadora": pk.remessa.transportadora,
                "codigo_rastreio_internacional": pk.remessa.codigo_rastreio_internacional,
                "status_transportadora": pk.remessa.status_transportadora,
                "enviado_em": pk.remessa.enviado_em.strftime("%d/%m/%Y %H:%M") if pk.remessa.enviado_em else None,
                "entregue_em": pk.remessa.entregue_em.strftime("%d/%m/%Y %H:%M") if pk.remessa.entregue_em else None,
            } if pk.remessa else None),
        } for pk in pedido.pacotes]

        historico = [{
            "status": h.status.value, "observacao": h.observacao,
            "criado_em": h.criado_em.strftime("%d/%m/%Y %H:%M") if h.criado_em else None,
        } for h in sorted(pedido.historico_status, key=lambda x: x.criado_em)]

        orcamento = None
        if pedido.orcamento:
            o = pedido.orcamento
            orcamento = {
                "valor_produtos_usd": o.valor_produtos_usd, "taxa_servico_usd": o.taxa_servico_usd,
                "frete_estimado_usd": o.frete_estimado_usd, "imposto_estimado_brl": o.imposto_estimado_brl,
                "cotacao_dolar": o.cotacao_dolar, "total_estimado_brl": o.total_estimado_brl,
            }

        return ToolResult(sucesso=True, dados={
            "pedido_id": pedido.id, "status": pedido.status.value, "tipo_servico": pedido.tipo_servico.value,
            "observacoes": pedido.observacoes,
            "criado_em": pedido.criado_em.strftime("%d/%m/%Y %H:%M") if pedido.criado_em else None,
            "itens": itens, "pacotes": pacotes, "historico": historico, "orcamento": orcamento,
        })


class AdminService:
    def __init__(self, session: Session):
        self.session = session

    def listar_todos_pedidos(self, status_filtro: Optional[str] = None) -> ToolResult:
        query = self.session.query(Pedido).join(Cliente)
        if status_filtro:
            try:
                query = query.filter(Pedido.status == StatusPedido(status_filtro))
            except ValueError:
                return ToolResult(sucesso=False, erro="Status invalido")

        pedidos = query.order_by(Pedido.criado_em.desc()).all()
        lista = [{
            "pedido_id": p.id, "cliente_nome": p.cliente.nome, "cliente_email": p.cliente.email,
            "status": p.status.value, "tipo_servico": p.tipo_servico.value,
            "criado_em": p.criado_em.strftime("%d/%m/%Y %H:%M") if p.criado_em else None,
            "qtd_itens": len(p.itens), "qtd_pacotes": len(p.pacotes),
        } for p in pedidos]
        return ToolResult(sucesso=True, dados={"pedidos": lista})

    def listar_pacotes_sem_cotacao(self) -> ToolResult:
        pacotes = self.session.query(Pacote).filter(~Pacote.cotacoes.any()).all()
        lista = [{"pacote_id": pk.id, "pedido_id": pk.pedido_id, "peso_kg": pk.peso_kg} for pk in pacotes]
        return ToolResult(sucesso=True, dados={"pacotes": lista})

    def selecionar_cotacao_frete(self, pacote_id: int, cotacao_id: int) -> ToolResult:
        pacote = self.session.query(Pacote).get(pacote_id)
        if not pacote:
            return ToolResult(sucesso=False, erro="Pacote nao encontrado")

        cotacao_escolhida = None
        for c in pacote.cotacoes:
            c.selecionada = (c.id == cotacao_id)
            if c.id == cotacao_id:
                cotacao_escolhida = c

        if not cotacao_escolhida:
            return ToolResult(sucesso=False, erro="Cotacao nao encontrada para este pacote")

        remessa = pacote.remessa or Remessa(pacote_id=pacote_id)
        remessa.transportadora = cotacao_escolhida.transportadora
        self.session.add(remessa)

        pedido = self.session.query(Pedido).get(pacote.pedido_id)
        pedido.status = StatusPedido.FRETE_COTADO
        self.session.add(StatusHistorico(pedido_id=pedido.id, status=StatusPedido.FRETE_COTADO,
                                          observacao=f"Frete selecionado: {cotacao_escolhida.transportadora}"))
        self.session.commit()
        return ToolResult(sucesso=True, dados={"pacote_id": pacote_id, "transportadora": cotacao_escolhida.transportadora})

    def registrar_envio(self, pacote_id: int, codigo_rastreio_internacional: str) -> ToolResult:
        pacote = self.session.query(Pacote).get(pacote_id)
        if not pacote or not pacote.remessa:
            return ToolResult(sucesso=False, erro="Remessa nao encontrada para este pacote. Selecione o frete primeiro.")

        pacote.remessa.codigo_rastreio_internacional = codigo_rastreio_internacional
        pacote.remessa.enviado_em = datetime.utcnow()
        pacote.remessa.status_transportadora = "Enviado"

        pedido = self.session.query(Pedido).get(pacote.pedido_id)
        pedido.status = StatusPedido.ENVIADO
        self.session.add(StatusHistorico(pedido_id=pedido.id, status=StatusPedido.ENVIADO,
                                          observacao=f"Codigo de rastreio: {codigo_rastreio_internacional}"))
        self.session.commit()
        return ToolResult(sucesso=True, dados={"pacote_id": pacote_id})


class RastreamentoService:
    ETAPAS_PADRAO = [
        "aguardando_compra", "aguardando_chegada_eua", "recebido_warehouse", "em_consolidacao",
        "frete_cotado", "enviado", "em_transito", "entregue",
    ]

    def __init__(self, session: Session):
        self.session = session

    def rastrear_pedido(self, pedido_id: int, cliente_id: int) -> ToolResult:
        pedido = self.session.query(Pedido).get(pedido_id)
        if not pedido:
            return ToolResult(sucesso=False, erro="Pedido nao encontrado")
        if pedido.cliente_id != cliente_id:
            return ToolResult(sucesso=False, erro="Este pedido nao pertence ao cliente logado")

        status_atual = pedido.status.value
        try:
            indice_atual = self.ETAPAS_PADRAO.index(status_atual)
        except ValueError:
            indice_atual = -1

        remessas = []
        for pacote in pedido.pacotes:
            if pacote.remessa:
                r = pacote.remessa
                remessas.append({
                    "pacote_id": pacote.id, "transportadora": r.transportadora,
                    "codigo_rastreio_internacional": r.codigo_rastreio_internacional,
                    "status_transportadora": r.status_transportadora,
                    "enviado_em": r.enviado_em.strftime("%d/%m/%Y %H:%M") if r.enviado_em else None,
                    "entregue_em": r.entregue_em.strftime("%d/%m/%Y %H:%M") if r.entregue_em else None,
                })

        historico = [{
            "status": h.status.value, "observacao": h.observacao,
            "criado_em": h.criado_em.strftime("%d/%m/%Y %H:%M") if h.criado_em else None,
        } for h in sorted(pedido.historico_status, key=lambda x: x.criado_em)]

        return ToolResult(sucesso=True, dados={
            "pedido_id": pedido.id, "status_atual": status_atual, "indice_etapa_atual": indice_atual,
            "etapas": self.ETAPAS_PADRAO, "remessas": remessas, "historico": historico,
        })
