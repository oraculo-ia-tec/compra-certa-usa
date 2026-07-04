"""
Design System centralizado — Compra Certa USA.
Todos os componentes visuais reutilizáveis ficam aqui.
"""
import streamlit as st

# ─────────────────────────────────────────────
# Paleta de cores
# ─────────────────────────────────────────────
COLORS = {
    "primary":    "#1E3A8A",
    "primary_lt": "#EFF6FF",
    "accent":     "#3B82F6",
    "bg":         "#FFFFFF",
    "bg_muted":   "#F1F5F9",
    "border":     "#E2E8F0",
    "text":       "#0F172A",
    "muted":      "#64748B",
    "success":    "#16A34A",
    "warning":    "#D97706",
    "error":      "#DC2626",
}

# ─────────────────────────────────────────────
# Status de pedido — fonte única de verdade
# ─────────────────────────────────────────────
STATUS_LABELS = {
    "aguardando_compra":      "Aguardando compra",
    "aguardando_chegada_eua": "Aguardando chegada nos EUA",
    "recebido_warehouse":     "Recebido no warehouse",
    "em_consolidacao":        "Em consolidação",
    "frete_cotado":           "Frete cotado",
    "enviado":                "Enviado",
    "em_transito":            "Em trânsito",
    "entregue":               "Entregue",
    "cancelado":              "Cancelado",
}

STATUS_COLORS = {
    "aguardando_compra":      "#94A3B8",
    "aguardando_chegada_eua": "#F59E0B",
    "recebido_warehouse":     "#3B82F6",
    "em_consolidacao":        "#8B5CF6",
    "frete_cotado":           "#06B6D4",
    "enviado":                "#10B981",
    "em_transito":            "#F97316",
    "entregue":               "#16A34A",
    "cancelado":              "#DC2626",
}

TIPO_SERVICO_LABELS = {
    "economico": "Econômico",
    "padrao":    "Padrão",
    "expresso":  "Expresso",
}

# ─────────────────────────────────────────────
# CSS Global
# ─────────────────────────────────────────────
_CSS = """
<style>
/* Cabeçalho de página */
.ccu-page-header        {margin-bottom: 1.5rem;}
.ccu-page-title         {font-size:1.9rem;font-weight:700;color:#1E3A8A;margin:0 0 .2rem;}
.ccu-page-subtitle      {color:#64748B;font-size:.95rem;margin:0 0 .5rem;}
.ccu-page-divider       {border:none;border-top:2px solid #E2E8F0;margin:.75rem 0 1.25rem;}

/* Badge de status */
.ccu-badge              {display:inline-block;padding:3px 10px;border-radius:999px;
                         font-size:.78rem;font-weight:600;letter-spacing:.3px;}

/* Card de pedido */
.ccu-card               {background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;
                         padding:1rem 1.25rem;margin-bottom:.75rem;}
.ccu-card-title         {font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 .15rem;}
.ccu-card-meta          {font-size:.8rem;color:#64748B;}

/* Métricas */
.ccu-metric-label       {font-size:.75rem;font-weight:600;color:#64748B;text-transform:uppercase;
                         letter-spacing:.5px;margin:0 0 .15rem;}
.ccu-metric-value       {font-size:1.4rem;font-weight:700;color:#0F172A;margin:0;}

/* Avisos de auth */
.ccu-auth-warn          {background:#FFF7ED;border-left:4px solid #F59E0B;
                         border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:1rem;}
.ccu-auth-warn p        {margin:0;color:#92400E;font-size:.9rem;}

/* Seção */
.ccu-section-title      {font-size:1.1rem;font-weight:600;color:#1E3A8A;margin:1.25rem 0 .5rem;}
</style>
"""


def inject_css():
    """Injeta o CSS global. Chamar uma vez no início de cada página."""
    st.html(_CSS)


# ─────────────────────────────────────────────
# Componentes
# ─────────────────────────────────────────────

def page_header(title: str, subtitle: str = "", icon: str = ""):
    """Cabeçalho padronizado de página."""
    inject_css()
    prefix = f"{icon} " if icon else ""
    st.html(f"""
    <div class="ccu-page-header">
      <p class="ccu-page-title">{prefix}{title}</p>
      {"<p class='ccu-page-subtitle'>" + subtitle + "</p>" if subtitle else ""}
      <hr class="ccu-page-divider">
    </div>
    """)


def status_badge(status_key: str) -> str:
    """Retorna HTML de badge colorido para um status de pedido."""
    label = STATUS_LABELS.get(status_key, status_key)
    color = STATUS_COLORS.get(status_key, "#94A3B8")
    bg    = color + "1A"  # 10% opacity
    return (
        f'<span class="ccu-badge" '
        f'style="background:{bg};color:{color};border:1px solid {color}33;">'
        f'{label}</span>'
    )


def auth_warning(message: str, button_label: str = "Ir para o login", page: str = "pages/Login.py"):
    """Bloco padronizado de aviso de autenticação com botão de redirecionamento."""
    inject_css()
    st.html(f'<div class="ccu-auth-warn"><p>⚠️ {message}</p></div>')
    if st.button(button_label, type="primary"):
        st.switch_page(page)
    st.stop()


def section_title(text: str):
    """Subtítulo de seção com estilo padrão."""
    st.html(f'<p class="ccu-section-title">{text}</p>')


def user_topbar():
    """Barra superior com nome do usuário e botão de logout."""
    from components.session import is_logged_in, get_current_user, clear_session
    if not is_logged_in():
        return
    user = get_current_user()
    name = user.get("full_name", "")
    role = user.get("role", "")
    role_label = {"admin": "👑 Admin", "operator": "🔧 Operador",
                  "client": "👤 Cliente", "ai_developer": "🤖 Dev IA"}.get(role, role)

    col1, col2, col3 = st.columns([5, 2, 1])
    with col2:
        st.caption(f"{role_label} · **{name}**")
    with col3:
        if st.button("Sair", key="_topbar_logout"):
            clear_session()
            st.switch_page("pages/Login.py")
