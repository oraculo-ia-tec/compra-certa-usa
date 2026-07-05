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
                "Use quando o usuário demonstrar interesse em contratar, ver preços ou fazer upgrade."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "modo": {
                        "type": "string",
                        "enum": ["todos", "upgrade_premium", "upgrade_pro"],
                        "description": (
                            "todos = mostra os 3 planos (público/sem assinatura ou assinante Starter); "
                            "upgrade_premium = mostra APENAS o card Premium (para assinante Pro querendo subir); "
                            "upgrade_pro = mostra APENAS o card Pro (para assinante Starter querendo subir)."
                        ),
                    },
                    "plano_sugerido": {
                        "type": "string",
                        "enum": ["starter", "pro", "premium", "nenhum"],
                        "description": "Plano mais adequado ao perfil. Use 'pro' se incerto.",
                    },
                    "motivo": {
                        "type": "string",
                        "description": "Justificativa da sugestão.",
                    },
                },
                "required": ["modo", "plano_sugerido"],
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


def _exec_mostrar_planos(modo: str, plano_sugerido: str, motivo: str) -> str:
    """Sinaliza ao frontend o modo de exibição de planos."""
    flow_map = {
        "todos":            "mostrar_planos",
        "upgrade_premium":  "upgrade_premium",
        "upgrade_pro":      "upgrade_pro",
    }
    try:
        st.session_state["flow_state"]     = flow_map.get(modo, "mostrar_planos")
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
        "widget_exibido":     True,
        "modo":               modo,
        "plano_sugerido":     plano_sugerido,
        "motivo":             motivo,
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
            args.get("modo", "todos"),
            args.get("plano_sugerido", "pro"),
            args.get("motivo", ""),
        )
    return json.dumps({"erro": f"Ferramenta '{name}' não reconhecida."})


# ── System prompt ──────────────────────────────────────────────────────────────

def _build_system_prompt(
    user_name: str | None,
    subscription_active: bool = False,
    subscription_plan: str | None = None,
) -> str:
    from services.stripe_service import PLANOS

    # ── Contexto A: PÚBLICO (visitante sem conta / redes sociais) ───────────────
    if not subscription_active:
        return f"""Você é o **Assistente IA da Compra Certa USA**, especializado em redirecionamento de compras dos EUA para o Brasil. Seu objetivo é **converter visitantes em assinantes**.

## Seu público agora
Visitante que chegou pelas redes sociais. **Não tem conta ainda.** Precisa entender o serviço e ser convertido.

## Estratégia de venda — funil AIDA
1. **Atenção**: desperte curiosidade com beneficios concretos (comprar Nike, Apple, Amazon com endereço americano)
2. **Interesse**: faça perguntas qualificadoras — "Que tipo de produto você costuma querer comprar nos EUA?"
3. **Desejo**: mostre o processo simples, o valor entregue, cases de uso
4. **Ação**: apresente os planos com `mostrar_widget_planos(modo='todos')`

## Rebate de objeções comuns
- "é complicado?" → "Não! Você compra normalmente, nós recebemos, você escolhe o frete."
- "e o imposto?" → Explique a regra Remessa Conforme e calcule se der valor
- "como confio?" → "Tiramos foto do seu produto ao chegar, você aprova antes de enviar"
- "caro?" → "A partir de R$ 29,90/mês. Numa compra de USD 100 você economiza muito mais."

## Regras do modo público
- **Primeira mensagem = saudação/cumprimento**: responda cordialmente, apresente-se brevemente e faça UMA pergunta qualificadora (ex: "Que tipo de produto você costuma querer comprar nos EUA?"). **NÃO mostre os planos ainda.**
- Use `mostrar_widget_planos(modo='todos')` **SOMENTE** quando o usuário expressar intenção clara e explícita de comprar/assinar — frases como "quero contratar", "como faço para assinar", "qual o preço", "quero começar", "me mostra os planos"
- **Não antecipe** a venda em saudações neutras ("oi", "boa tarde", "olá", "tudo bem")
- Seja entusiasmado, acolhedor, orientado a benefícios — mas respeite o ritmo do visitante
- Responda **sempre em português**

## Sobre o serviço
O cliente se cadastra, recebe um endereço nos EUA (ex: CCU-XXXXX, Miami FL), compra em qualquer loja americana, o produto chega ao warehouse, a equipe consolida e envia ao Brasil com rastreamento completo.

## Planos disponíveis
- **Starter** R$29,90/mês — 3 pedidos, frete Econômico
- **Pro** R$59,90/mês — 10 pedidos, Econômico + Padrão *(mais popular)*
- **Premium** R$99,90/mês — Ilimitado, todos os fretes incluindo Expresso
"""

    # ── Contexto B: ASSINANTE PRO → upsell Premium ───────────────────────
    if subscription_plan == "pro":
        nome_txt = f"**{user_name}**" if user_name else "você"
        return f"""Você é o **Assistente IA da Compra Certa USA**. Você está atendendo {nome_txt}, que já é assinante do **plano Pro**.

## Contexto do cliente
- Plano atual: **Pro** (10 pedidos/mês, frete Econômico e Padrão)
- Cliente existente, satisfeito o suficiente para manter o plano
- Objetivo: detectar interesse em **upgrade para o Premium**

## Quando acionar o upgrade
Acione `mostrar_widget_planos(modo='upgrade_premium', plano_sugerido='premium')` se o cliente mencionar:
- Frete expresso, urgente, rápido, precisa chegar logo
- Mais de 10 pedidos, volume alto, muitas compras
- "Vale o Premium?", "o que eu ganho subindo de plano?"
- Qualquer insatisfação com limite de pedidos

## Como argumentar o upgrade
- Reconheça que o cliente já é Pro: *"Você já está no plano certo para muitas situações..."
- Destaque o que ele GANHA: pedidos ilimitados + frete Expresso (5-10 dias vs 15-30)
- Diferença de custo: apenas +R$40,00/mês para recursos premium
- Não force — apresente como uma opção quando fizer sentido

## Regras
- Ajude com suporte, pedidos, rastreamento e dúvidas normais
- Só apresente o upgrade quando houver intenção real
- Nunca mostre Starter para esse cliente — seria um downgrade
- Responda **sempre em português**
"""

    # ── Contexto C: ASSINANTE STARTER → upsell Pro ──────────────────────
    if subscription_plan == "starter":
        nome_txt = f"**{user_name}**" if user_name else "você"
        return f"""Você é o **Assistente IA da Compra Certa USA**. Você está atendendo {nome_txt}, assinante do **plano Starter**.

## Contexto do cliente
- Plano atual: **Starter** (3 pedidos/mês, somente frete Econômico)
- Objetivo: detectar interesse em upgrade para **Pro**

## Quando acionar o upgrade
Use `mostrar_widget_planos(modo='upgrade_pro', plano_sugerido='pro')` se o cliente mencionar:
- Querer fazer mais de 3 pedidos no mês
- Interesse em frete Padrão (mais rápido que o atual)
- Perguntas sobre limites, planos maiores

## Argumento para upgrade
- Pro custa apenas +R$30,00/mês e dá acesso a 10 pedidos e frete Padrão
- Ajude com suporte e dúvidas normais normalmente
- Responda **sempre em português**
"""

    # ── Contexto D: ASSINANTE PREMIUM (suporte, retenção) ──────────────────
    nome_txt = f"**{user_name}**" if user_name else "você"
    return f"""Você é o **Assistente IA da Compra Certa USA**. Você está atendendo {nome_txt}, assinante **Premium** (plano máximo).

## Contexto
- Plano atual: **Premium** — pedidos ilimitados, todos os fretes incluindo Expresso
- Foque em suporte excepcional, resolução de problemas, rastreamento
- Não apresente planos — o cliente já tem o melhor
- Se o cliente mencionar algo positivo, reforce o valor do plano Premium
- Responda **sempre em português**

## Ferramentas disponíveis
Consultar pedidos, calcular impostos, informar sobre fretes.
"""


def _build_system_prompt_legacy(user_name: str | None) -> str:
    """Mantido para compatibilidade — usa contexto genérico."""
    return _build_system_prompt(user_name)


# ── Cliente Groq ───────────────────────────────────────────────────────────────

def _get_groq_key() -> str | None:
    try:
        return st.secrets["default"]["GROQ_API_KEY"]
    except Exception:
        pass
    return settings.GROQ_API_KEY


def chat(
    messages: list,
    user_id: int | None,
    user_name: str | None,
    subscription_active: bool = False,
    subscription_plan: str | None = None,
) -> str:
    """
    Executa o ciclo completo de chat com tool calling.
    subscription_active/subscription_plan definem o contexto (público vs assinante).
    """
    api_key = _get_groq_key()
    if not api_key:
        return "⚠️ A chave GROQ_API_KEY não está configurada nos Secrets do Streamlit Cloud."

    try:
        from groq import Groq
    except ImportError:
        return "⚠️ Pacote `groq` não instalado. Adicione `groq>=0.9` ao requirements.txt."

    client = Groq(api_key=api_key)
    system = {
        "role": "system",
        "content": _build_system_prompt(user_name, subscription_active, subscription_plan),
    }
    conversation = [system] + messages

    # ── Detecta saudação simples na 1ª mensagem → bloqueia tools ─────────────
    _PURCHASE_KEYWORDS = {
        "plano", "assinar", "assinatura", "preço", "preco", "quanto", "custa",
        "contratar", "cadastrar", "começar", "comecar", "starter", "pro", "premium",
        "valor", "mensalidade", "quero", "comprar", "importar", "frete",
    }
    _first_content = (messages[0]["content"] if messages else "").lower().strip()
    _is_greeting_only = (
        len(messages) == 1
        and len(_first_content) < 50
        and not any(kw in _first_content for kw in _PURCHASE_KEYWORDS)
    )
    _tool_choice = "none" if _is_greeting_only else "auto"

    # ── Primeira chamada — o modelo pode pedir ferramentas ─────────────────────
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation,
        tools=TOOLS,
        tool_choice=_tool_choice,
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
