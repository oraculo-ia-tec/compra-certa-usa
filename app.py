"""
COMPRA CERTA USA — Ponto de entrada Streamlit.
Usa st.navigation() para controlar quais páginas aparecem no menu
conforme o estado de autenticação do usuário.
"""
import streamlit as st
from models.seed import init_db_and_seed
from components.session import is_logged_in, get_current_user, clear_session

st.set_page_config(
    page_title="COMPRA CERTA USA",
    page_icon="📦",
    layout="wide",
)

# Init DB + migrações + seed (idempotente, seguro a cada cold start)
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


# ── Helper: avatar HTML ────────────────────────────────────────────────────────
def _avatar_html(avatar_url: str | None, name: str, size: int = 52) -> str:
    if avatar_url:
        return (
            f'<img src="data:image/jpeg;base64,{avatar_url}" '
            f'style="width:{size}px;height:{size}px;border-radius:50%;'
            f'object-fit:cover;border:2px solid #3B82F6;flex-shrink:0;">'
        )
    initials = "".join(w[0].upper() for w in (name or "U").split()[:2])
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:50%;'
        f'background:#1E3A8A;color:#fff;font-size:{size//3}px;font-weight:700;'
        f'display:flex;align-items:center;justify-content:center;flex-shrink:0;'
        f'border:2px solid #3B82F6;">{initials}</div>'
    )


if is_logged_in():
    user      = get_current_user()
    role      = user.get("role", "client")
    name      = user.get("full_name", "")
    email_val = user.get("email", "")
    avatar    = user.get("avatar_url") or st.session_state.get("user", {}).get("avatar_url")
    role_label = {"admin": "👑 Admin", "operator": "🔧 Operador",
                  "client": "👤 Cliente", "ai_developer": "🤖 Dev IA"}.get(role, role)

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        # 1. Logomarca com borda redonda
        st.html("""
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
        """)

        # 2. Card do usuário: avatar | dados (borda retangular)
        st.html(f"""
        <div style="border:1.5px solid #CBD5E1;border-radius:10px;padding:10px 12px;
                    display:flex;gap:10px;align-items:center;
                    background:#F8FAFC;margin-bottom:6px;">
          {_avatar_html(avatar, name, 52)}
          <div style="min-width:0;flex:1;">
            <p style="margin:0;font-weight:700;font-size:.85rem;color:#0F172A;
                      white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</p>
            <p style="margin:2px 0 0;font-size:.70rem;color:#64748B;
                      white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{email_val}</p>
            <p style="margin:3px 0 0;font-size:.72rem;color:#1E3A8A;font-weight:600;">{role_label}</p>
          </div>
        </div>
        """)

    # ── Páginas por role ───────────────────────────────────────────────────────
    menu = [assistente_page, home_page, pedido_page, orcamento_page,
            meus_page, detalhe_page, rastreio_page]
    pages = {"📦 Menu": menu, "👤 Conta": [config_page]}
    if role in ("admin", "operator", "ai_developer"):
        pages["🔧 Gestão"] = [admin_page]

    pg = st.navigation(pages)

    # ── Sidebar: Divider + botões abaixo do menu ───────────────────────────────
    with st.sidebar:
        st.divider()
        col_sair, col_limpar = st.columns(2)
        with col_sair:
            if st.button("🚪 Sair", use_container_width=True, key="_btn_sair"):
                clear_session()
                st.rerun()
        with col_limpar:
            if st.button("🗑️ Limpar chat", use_container_width=True, key="_btn_limpar"):
                st.session_state["assistant_messages"] = []
                st.toast("Conversa limpa!", icon="🗑️")

else:
    # ── Sidebar público: apenas logomarca ─────────────────────────────────────
    with st.sidebar:
        st.html("""
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
        """)

    pages = {"🤖 Assistente": [assistente_pub],
             "🔐 Acesso": [login_page, cadastro_page, confirm_page, reset_page]}
    pg = st.navigation(pages)

pg.run()
