"""
COMPRA CERTA USA — Ponto de entrada Streamlit.
Usa st.navigation(position="hidden") + st.page_link() para controle total
da ordem da sidebar: logo → card → menu → divider → botões.
"""
import streamlit as st
from models.seed import init_db_and_seed
from components.session import is_logged_in, get_current_user, clear_session

st.set_page_config(
    page_title="COMPRA CERTA USA",
    page_icon="📦",
    layout="wide",
)

# Init DB + migrações + seed
if "db_initialized" not in st.session_state:
    init_db_and_seed()
    st.session_state["db_initialized"] = True

# ── Definição de páginas ───────────────────────────────────────────────────────
assistente_pub  = st.Page("pages/0_Assistente.py",    title="Assistente IA",     icon="🤖", default=True)
login_page      = st.Page("pages/Login.py",            title="Login",             icon="🔐")
cadastro_page   = st.Page("pages/Cadastro.py",          title="Cadastro",          icon="📝")
confirm_page    = st.Page("pages/Confirmar_Conta.py",  title="Confirmar Conta",   icon="📧")
reset_page      = st.Page("pages/Redefinir_Senha.py",  title="Redefinir Senha",   icon="🔑")

assistente_page = st.Page("pages/0_Assistente.py",    title="Assistente IA",     icon="🤖", default=True)
home_page       = st.Page("pages/1_Onboarding.py",    title="Início",            icon="🏠")
pedido_page     = st.Page("pages/2_Novo_Pedido.py",    title="Novo Pedido",       icon="🛒")
orcamento_page  = st.Page("pages/3_Orcamento.py",      title="Orçamento",         icon="💰")
meus_page       = st.Page("pages/4_Meus_Pedidos.py",   title="Meus Pedidos",      icon="📋")
detalhe_page    = st.Page("pages/5_Detalhe_Pedido.py", title="Detalhe do Pedido", icon="📄")
rastreio_page   = st.Page("pages/7_Rastreamento.py",   title="Rastreamento",      icon="✈️")
config_page     = st.Page("pages/Configuracao.py",     title="Configuração",      icon="⚙️")
admin_page      = st.Page("pages/6_Administracao.py",  title="Administração",     icon="🔧")


def _avatar_html(avatar_url, name, size=52):
    if avatar_url:
        return (
            f'<img src="data:image/jpeg;base64,{avatar_url}" '
            f'style="width:{size}px;height:{size}px;border-radius:50%;'
            f'object-fit:cover;border:2px solid #3B82F6;flex-shrink:0;">'
        )
    initials = "".join(w[0].upper() for w in (name or "U").split()[:2]) or "U"
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:50%;'
        f'background:#1E3A8A;color:#fff;font-size:{size//3}px;font-weight:700;'
        f'display:flex;align-items:center;justify-content:center;flex-shrink:0;'
        f'border:2px solid #3B82F6;">{initials}</div>'
    )


_LOGO_HTML = """
<div style="text-align:center;padding:18px 0 14px;">
  <div style="display:inline-flex;align-items:center;justify-content:center;
              background:#1E3A8A;border-radius:50%;width:76px;height:76px;
              font-size:2.2rem;border:3px solid #3B82F6;
              box-shadow:0 4px 16px rgba(30,58,138,.30);">
    📦
  </div>
  <p style="margin:8px 0 2px;font-weight:800;font-size:.95rem;
            color:#1E3A8A;letter-spacing:.8px;">COMPRA CERTA USA</p>
  <p style="margin:0;font-size:.68rem;color:#94A3B8;">Importações dos EUA para o Brasil</p>
</div>
"""


def _section_label(text):
    st.html(
        f'<p style="font-size:.68rem;font-weight:700;color:#94A3B8;'
        f'text-transform:uppercase;letter-spacing:1.2px;'
        f'padding:10px 0 2px;margin:0;">{text}</p>'
    )


if is_logged_in():
    user      = get_current_user()
    role      = user.get("role") or "client"
    name      = user.get("full_name") or ""
    email_val = user.get("email") or ""
    avatar    = user.get("avatar_url") or st.session_state.get("user", {}).get("avatar_url")
    role_label = {"admin": "👑 Admin", "operator": "🔧 Operador",
                  "client": "👤 Cliente", "ai_developer": "🤖 Dev IA"}.get(role, role)

    pages_map = {
        "Menu":  [assistente_page, home_page, pedido_page, orcamento_page,
                  meus_page, detalhe_page, rastreio_page],
        "Conta": [config_page],
    }
    if role in ("admin", "operator", "ai_developer"):
        pages_map["Gestão"] = [admin_page]

    pg = st.navigation(pages_map, position="hidden")

    with st.sidebar:
        st.html(_LOGO_HTML)

        st.html(f"""
        <div style="border:1.5px solid #CBD5E1;border-radius:10px;padding:10px 12px;
                    display:flex;gap:10px;align-items:center;
                    background:#F8FAFC;margin-bottom:4px;">
          {_avatar_html(avatar, name, 52)}
          <div style="min-width:0;flex:1;">
            <p style="margin:0;font-weight:700;font-size:.85rem;color:#0F172A;
                      white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name or chr(8212)}</p>
            <p style="margin:2px 0 0;font-size:.70rem;color:#64748B;
                      white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{email_val}</p>
            <p style="margin:3px 0 0;font-size:.72rem;color:#1E3A8A;font-weight:600;">{role_label}</p>
          </div>
        </div>
        """)

        _section_label("Menu")
        st.page_link(assistente_page, label="Assistente IA",     icon="🤖")
        st.page_link(home_page,        label="Início",            icon="🏠")
        st.page_link(pedido_page,      label="Novo Pedido",       icon="🛒")
        st.page_link(orcamento_page,   label="Orçamento",         icon="💰")
        st.page_link(meus_page,        label="Meus Pedidos",      icon="📋")
        st.page_link(detalhe_page,     label="Detalhe do Pedido", icon="📄")
        st.page_link(rastreio_page,    label="Rastreamento",      icon="✈️")

        _section_label("Conta")
        st.page_link(config_page, label="Configuração", icon="⚙️")

        if role in ("admin", "operator", "ai_developer"):
            _section_label("Gestão")
            st.page_link(admin_page, label="Administração", icon="🔧")

        st.divider()
        col_sair, col_limpar = st.columns(2)
        with col_sair:
            if st.button("🚪 Sair", use_container_width=True, key="_btn_sair"):
                clear_session()
                st.rerun()
        with col_limpar:
            if st.button("🗑️ Limpar", use_container_width=True, key="_btn_limpar"):
                st.session_state["assistant_messages"] = []
                st.toast("Conversa limpa!", icon="🗑️")

else:
    pages_map = {
        "Assistente": [assistente_pub],
        "Acesso":     [login_page, cadastro_page, confirm_page, reset_page],
    }
    pg = st.navigation(pages_map, position="hidden")

    with st.sidebar:
        st.html(_LOGO_HTML)
        _section_label("Assistente")
        st.page_link(assistente_pub, label="Assistente IA", icon="🤖")
        _section_label("Acesso")
        st.page_link(login_page,    label="Login",           icon="🔐")
        st.page_link(cadastro_page, label="Cadastro",        icon="📝")
        st.page_link(confirm_page,  label="Confirmar Conta", icon="📧")
        st.page_link(reset_page,    label="Redefinir Senha", icon="🔑")

pg.run()
