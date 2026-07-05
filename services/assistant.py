"""
Assistente IA da Compra Certa USA — powered by Groq.
Implementa tool calling para consulta de pedidos, cálculo de impostos e FAQ.
"""
import json
import streamlit as st
from loguru import logger
from core.config import settings

# ── Definições das ferramentas (MCP tools) ────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_meus_pedidos",
            "description": "Lista todos os pedidos do usuário autenticado com status atual.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_detalhe_pedido",
            "description": "Retorna detalhes completos de um pedido específico pelo ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pedido_id": {
                        "type": "integer",
                        "description": "ID numérico do pedido a consultar.",
                    }
                },
                "required": ["pedido_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_estimativa_impostos",
            "description": (
                "Calcula a estimativa de impostos brasileiros para uma compra internacional."
                " Retorna imposto de importação, ICMS e total estimado em BRL."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "valor_usd": {
                        "type": "number",
                        "description": "Valor total da compra em dólares americanos (USD).",
                    },
                    "cotacao_dolar": {
                        "type": "number",
                        "description": "Cotação do dólar em reais. Se não informado, usa 5.80.",
                    },
                    "estado_destino": {
                        "type": "string",
                        "description": "Sigla do estado de destino (ex: SP, RJ, MG). Afeta o ICMS.",
                    },
                },
                "required": ["valor_usd"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "informacoes_servico",
            "description": "Retorna informações sobre os tipos de serviço de frete disponíveis (econômico, padrão, expresso).",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "enum": ["economico", "padrao", "expresso", "todos"],
                        "description": "Tipo de serviço a consultar.",
                    }
                },
                "required": ["tipo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mostrar_widget_planos",
            "description": (
                "Exibe os cards interativos de planos de assinatura da Compra Certa USA. "
                "Use quando o usuário demonstrar interesse em: contratar, assinar, ver preços, "
                "quanto custa, quero ser cliente, como me cadastro, planos disponíveis, "
                "ou qualquer intenção de compra/assinatura."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "plano_sugerido": {
                        "type": "string",
                        "enum": ["starter", "pro", "premium", "nenhum"],
                        "description": "Plano mais adequado ao perfil/contexto do usuário. Use 'pro' se incerto.",
                    },
                    "motivo": {
                        "type": "string",
                        "description": "Breve justificativa da sugestão de plano.",
                    },
                },
                "required": ["plano_sugerido"],
            },
        },
    },
]

# ── ICMS por estado (alíquota padrão para importação) ─────────────────────────
_ICMS = {
    "SP": 0.18, "RJ": 0.20, "MG": 0.18, "RS": 0.18, "PR": 0.18,
    "SC": 0.17, "BA": 0.19, "GO": 0.17, "DF": 0.18, "CE": 0.17,
    "PE": 0.185, "AM": 0.20, "PA": 0.17, "ES": 0.17, "MT": 0.17,
    "MS": 0.17, "RN": 0.18, "AL": 0.19, "SE": 0.19, "PB": 0.18,
    "PI": 0.185, "MA": 0.195, "TO": 0.17, "RO": 0.175, "AC": 0.17,
    "AP": 0.17, "RR": 0.17,
}

_SERVICOS = {
    "economico": {
        "prazo": "15 a 30 dias úteis",
        "ideal_para": "Produtos sem urgência, menor custo de frete",
        "descricao": "Opção mais econômica. Consolidação de pacotes para reduzir custo.",
    },
    "padrao": {
        "prazo": "10 a 20 dias úteis",
        "ideal_para": "Equilíbrio entre custo e velocidade",
        "descricao": "Serviço padrão com rastreamento completo.",
    },
    "expresso": {
        "prazo": "5 a 10 dias úteis",
        "ideal_para": "Produtos urgentes ou de alto valor",
        "descricao": "Envio prioritário com rastreamento em tempo real.",
    },
}


# ── Executores das ferramentas ────────────────────────────────────────────────

def _exec_consultar_meus_pedidos(user_id: int | None) -> str:
    if not user_id:
        return json.dumps({"erro": "Usuário não autenticado. Faça login para consultar pedidos."})
    try:
        from tools.tools import tool_listar_pedidos_por_cliente
        resultado = tool_listar_pedidos_por_cliente(user_id)
        if resultado.sucesso:
            return json.dumps(resultado.dados, ensure_ascii=False, default=str)
        return json.dumps({"erro": resultado.erro})
    except Exception as e:
        logger.error(f"[assistant] consultar_meus_pedidos: {e}")
        return json.dumps({"erro": str(e)})


def _exec_consultar_detalhe_pedido(pedido_id: int, user_id: int | None) -> str:
    try:
        from tools.tools import tool_detalhar_pedido
        resultado = tool_detalhar_pedido(pedido_id)
        if resultado.sucesso:
            return json.dumps(resultado.dados, ensure_ascii=False, default=str)
        return json.dumps({"erro": resultado.erro})
    except Exception as e:
        logger.error(f"[assistant] consultar_detalhe_pedido: {e}")
        return json.dumps({"erro": str(e)})


def _exec_calcular_impostos(valor_usd: float, cotacao: float = 5.80, estado: str = "SP") -> str:
    estado = (estado or "SP").upper()
    icms_rate = _ICMS.get(estado, 0.18)

    # Regra Remessa Conforme (2024): até USD 50 de PF para PF → isento
    isento_remessa_conforme = valor_usd <= 50.0

    # Base de cálculo em BRL
    valor_brl = valor_usd * cotacao

    if isento_remessa_conforme:
        resultado = {
            "valor_usd": valor_usd,
            "cotacao_dolar": cotacao,
            "valor_brl": round(valor_brl, 2),
            "isento_remessa_conforme": True,
            "imposto_importacao_brl": 0.0,
            "icms_brl": 0.0,
            "total_impostos_brl": 0.0,
            "total_com_impostos_brl": round(valor_brl, 2),
            "nota": "Isento pelo programa Remessa Conforme (compras até USD 50).",
        }
    else:
        # Imposto de importação: 20% sobre valor em BRL
        ii = valor_brl * 0.20
        # Base ICMS = (valor BRL + II) / (1 - alíquota ICMS)
        base_icms = (valor_brl + ii) / (1 - icms_rate)
        icms = base_icms * icms_rate
        total_impostos = ii + icms
        resultado = {
            "valor_usd": valor_usd,
            "cotacao_dolar": cotacao,
            "valor_brl": round(valor_brl, 2),
            "isento_remessa_conforme": False,
            "imposto_importacao_20pct_brl": round(ii, 2),
            "icms_estado": estado,
            "icms_aliquota": f"{icms_rate*100:.1f}%",
            "icms_brl": round(icms, 2),
            "total_impostos_brl": round(total_impostos, 2),
            "total_com_impostos_brl": round(valor_brl + total_impostos, 2),
            "nota": (
                "Estimativa baseada nas regras da Receita Federal (II 20%) e ICMS do estado. "
                "Valores finais dependem da classificação fiscal do produto."
            ),
        }
    return json.dumps(resultado, ensure_ascii=False)


def _exec_informacoes_servico(tipo: str) -> str:
    if tipo == "todos":
        return json.dumps(_SERVICOS, ensure_ascii=False)
    info = _SERVICOS.get(tipo)
    if not info:
        return json.dumps({"erro": f"Tipo '{tipo}' não encontrado."})
    return json.dumps({tipo: info}, ensure_ascii=False)


def _exec_mostrar_planos(plano_sugerido: str, motivo: str) -> str:
    """Sinaliza ao frontend que deve exibir o widget de planos."""
    try:
        st.session_state["flow_state"]     = "mostrar_planos"
        st.session_state["plano_sugerido"] = plano_sugerido if plano_sugerido != "nenhum" else "pro"
    except Exception:
        pass

    from services.stripe_service import PLANOS
    resumo = {
        slug: {
            "nome":      p["nome"],
            "preco_brl": p["preco_brl"],
            "pedidos":   p["pedidos"],
            "fretes":    p["fretes"],
        }
        for slug, p in PLANOS.items()
    }
    return json.dumps({
        "widget_exibido":  True,
        "plano_sugerido":  plano_sugerido,
        "motivo":          motivo,
        "planos_disponiveis": resumo,
    }, ensure_ascii=False)


def _run_tool(name: str, args: dict, user_id: int | None) -> str:
    if name == "consultar_meus_pedidos":
        return _exec_consultar_meus_pedidos(user_id)
    if name == "consultar_detalhe_pedido":
        return _exec_consultar_detalhe_pedido(args.get("pedido_id"), user_id)
    if name == "calcular_estimativa_impostos":
        return _exec_calcular_impostos(
            args.get("valor_usd", 0),
            args.get("cotacao_dolar", 5.80),
            args.get("estado_destino", "SP"),
        )
    if name == "informacoes_servico":
        return _exec_informacoes_servico(args.get("tipo", "todos"))
    if name == "mostrar_widget_planos":
        return _exec_mostrar_planos(
            args.get("plano_sugerido", "pro"),
            args.get("motivo", ""),
        )
    return json.dumps({"erro": f"Ferramenta '{name}' não reconhecida."})


# ── System prompt ──────────────────────────────────────────────────────────────

def _build_system_prompt(user_name: str | None) -> str:
    nome = f" Você está atendendo **{user_name}**." if user_name else ""
    return f"""Você é o **Assistente IA da Compra Certa USA**, um serviço especializado em redirecionamento de compras dos Estados Unidos para o Brasil.{nome}

## Sua missão
Ajudar clientes com dúvidas sobre:
- Como funciona o processo de compra e redirecionamento
- Taxas e impostos de importação no Brasil
- Status e rastreamento de pedidos
- Tipos de frete disponíveis e prazos
- Procedimentos de cadastro e uso da plataforma

## Sobre a Compra Certa USA
A Compra Certa USA oferece um endereço (suite) nos EUA para que clientes brasileiros possam comprar em lojas americanas. O processo é:
1. Cliente se cadastra e recebe um endereço exclusivo nos EUA (ex: CCU-XXXXX, Miami FL)
2. Cliente compra online em qualquer loja americana usando o endereço da suite
3. O produto é recebido no warehouse da Compra Certa USA em Miami
4. A equipe consolida os pacotes, tira fotos e informa o peso/dimensões
5. O cliente escolhe o tipo de frete e aprova o orçamento
6. O pacote é enviado ao Brasil com rastreamento completo

## Tipos de frete
- **Econômico**: 15-30 dias úteis — menor custo, ideal para produtos sem urgência
- **Padrão**: 10-20 dias úteis — equilíbrio entre custo e velocidade
- **Expresso**: 5-10 dias úteis — envio prioritário, produtos urgentes

## Impostos de importação no Brasil (regras 2024)
- **Programa Remessa Conforme**: compras até USD 50 de pessoa física para pessoa física são **isentas** de imposto de importação
- **Compras acima de USD 50**: incide **20% de Imposto de Importação** sobre o valor em BRL + ICMS do estado de destino
- **ICMS**: varia por estado (SP: 18%, RJ: 20%, MG: 18%, etc.), calculado sobre a base majorada
- **IOF**: 6,38% sobre o valor da compra no cartão internacional (cobrado pelo banco, não pela Receita)
- O desembaraço aduaneiro pode levar de 5 a 30 dias úteis após a chegada ao Brasil
- Produtos acima de USD 3.000 podem ter alíquotas progressivas e exigir DI (Declaração de Importação)

## Proibições e restrições
- Alimentos perecíveis, medicamentos controlados, armas e produtos counterfeit não são aceitos
- Eletrônicos com bateria de lítio têm restrições de transporte aéreo
- Produtos que precisam de certificação ANATEL devem ter o processo feito pelo importador

## Ferramentas disponíveis
Você tem acesso a ferramentas para:
- Consultar pedidos do cliente autenticado
- Calcular estimativas de impostos
- Informar sobre tipos de serviço
- **Exibir widget interativo de planos de assinatura**

## Análise de intenção — planos de assinatura
Use a ferramenta `mostrar_widget_planos` SEMPRE que o usuário expressar:
- Interesse em contratar, assinar, tornar-se cliente
- Perguntas sobre preço, valor, quanto custa, planos disponíveis
- Frases como "quero me cadastrar", "como funciona a assinatura", "vale a pena?"
- Comparação de planos ou pergunta sobre benefícios
- Qualquer sentimento positivo de compra ("adorei", "quero começar", "vou contratar")

### Sugestão de plano por perfil
- **Starter** (R$29,90): usuário com poucas compras ou quer testar o serviço
- **Pro** (R$59,90): usuário regular, até 10 pedidos/mês — **use como padrão se incerto**
- **Premium** (R$99,90): usuário frequente, quer expresso ou volume alto

## Regras de comportamento
- Seja objetivo, cordial e profissional
- Use formatação Markdown para clareza (negrito, listas, tabelas)
- Quando calcular impostos, sempre explique a memória de cálculo
- Para pedidos específicos, use a ferramenta — não invente dados
- Se não souber responder, indique o canal de suporte: contato@oraculosia.site
- Responda **sempre em português**
"""


# ── Cliente Groq ───────────────────────────────────────────────────────────────

def _get_groq_key() -> str | None:
    try:
        return st.secrets["default"]["GROQ_API_KEY"]
    except Exception:
        pass
    return settings.GROQ_API_KEY


def chat(messages: list, user_id: int | None, user_name: str | None) -> str:
    """
    Executa o ciclo completo de chat com tool calling.
    Retorna a resposta final como string.
    """
    api_key = _get_groq_key()
    if not api_key:
        return "⚠️ A chave GROQ_API_KEY não está configurada nos Secrets do Streamlit Cloud."

    try:
        from groq import Groq
    except ImportError:
        return "⚠️ Pacote `groq` não instalado. Adicione `groq>=0.9` ao requirements.txt."

    client = Groq(api_key=api_key)
    system = {"role": "system", "content": _build_system_prompt(user_name)}
    conversation = [system] + messages

    # ── Primeira chamada — o modelo pode pedir ferramentas ─────────────────────
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation,
        tools=TOOLS,
        tool_choice="auto",
        max_tokens=2048,
        temperature=0.3,
    )

    msg = response.choices[0].message

    # ── Se não há tool calls, retorna direto ───────────────────────────────────
    if not msg.tool_calls:
        return msg.content or ""

    # ── Executa cada ferramenta solicitada ────────────────────────────────────
    conversation.append(msg)  # adiciona a mensagem do assistente com tool_calls

    for tc in msg.tool_calls:
        try:
            args = json.loads(tc.function.arguments)
        except Exception:
            args = {}

        logger.info(f"[assistant] tool_call: {tc.function.name}({args})")
        result = _run_tool(tc.function.name, args, user_id)

        conversation.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": result,
        })

    # ── Segunda chamada — resposta final com os resultados das ferramentas ─────
    final = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation,
        max_tokens=2048,
        temperature=0.3,
    )
    return final.choices[0].message.content or ""
