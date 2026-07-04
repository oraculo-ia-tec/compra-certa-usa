"""Configuração de conta — Compra Certa USA."""
import base64
import streamlit as st
from components.ui import page_header, inject_css
from components.session import require_auth, get_current_user, get_user_id
from services.auth import update_profile, AuthError

require_auth()
inject_css()
page_header("Configuração da Conta", "Gerencie seu perfil, foto e senha.", "⚙️")

user    = get_current_user()
user_id = get_user_id()

# ── Avatar atual ──────────────────────────────────────────────────────────────
avatar_url = user.get("avatar_url") or st.session_state.get("user", {}).get("avatar_url")

col_av, col_info = st.columns([1, 2])
with col_av:
    if avatar_url:
        st.html(f"""
        <div style="text-align:center;">
          <img src="data:image/jpeg;base64,{avatar_url}"
               style="width:120px;height:120px;border-radius:50%;object-fit:cover;
                      border:3px solid #1E3A8A;box-shadow:0 2px 12px rgba(30,58,138,.2);">
        </div>
        """)
    else:
        initials = "".join(w[0].upper() for w in user.get("full_name", "U").split()[:2])
        st.html(f"""
        <div style="text-align:center;">
          <div style="display:inline-flex;align-items:center;justify-content:center;
                      width:120px;height:120px;border-radius:50%;background:#1E3A8A;
                      font-size:2.5rem;font-weight:700;color:#FFFFFF;
                      border:3px solid #3B82F6;box-shadow:0 2px 12px rgba(30,58,138,.2);">
            {initials}
          </div>
        </div>
        """)
    st.caption("Foto de perfil atual")

with col_info:
    st.markdown(f"**Nome:** {user.get('full_name', '')}")
    st.markdown(f"**Role:** {user.get('role', '').capitalize()}")
    st.markdown(f"**Status:** {user.get('status', '').capitalize()}")

st.divider()

# ── Seção 1: Foto de perfil ───────────────────────────────────────────────────
st.html('<p class="ccu-section-title">📷 Foto de perfil</p>')

uploaded = st.file_uploader(
    "Enviar nova foto",
    type=["jpg", "jpeg", "png", "webp"],
    help="Tamanho máximo: 2 MB. Formatos: JPG, PNG, WEBP.",
)

col_b1, col_b2 = st.columns(2)

with col_b1:
    if uploaded:
        if uploaded.size > 2 * 1024 * 1024:
            st.error("⚠️ A foto deve ter no máximo 2 MB.")
        else:
            preview_b64 = base64.b64encode(uploaded.read()).decode()
            st.html(f"""
            <div style="text-align:center;margin:8px 0;">
              <img src="data:image/jpeg;base64,{preview_b64}"
                   style="width:80px;height:80px;border-radius:50%;object-fit:cover;
                          border:2px solid #3B82F6;">
              <p style="margin:4px 0 0;font-size:.75rem;color:#64748B;">Pré-visualização</p>
            </div>
            """)
            if st.button("💾 Salvar foto", type="primary", use_container_width=True):
                try:
                    result = update_profile(user_id, avatar_b64=preview_b64)
                    st.session_state["user"]["avatar_url"] = preview_b64
                    st.success("✅ Foto de perfil atualizada!")
                    st.rerun()
                except AuthError as e:
                    st.error(f"❌ {e.message}")

with col_b2:
    if avatar_url:
        if st.button("🗑️ Remover foto", use_container_width=True):
            try:
                update_profile(user_id, avatar_b64="")
                st.session_state["user"]["avatar_url"] = None
                st.success("✅ Foto removida.")
                st.rerun()
            except AuthError as e:
                st.error(f"❌ {e.message}")

st.divider()

# ── Seção 2: Dados do perfil ──────────────────────────────────────────────────
st.html('<p class="ccu-section-title">👤 Dados do perfil</p>')

with st.form("form_perfil"):
    novo_nome = st.text_input("Nome completo", value=user.get("full_name", ""))
    salvar_nome = st.form_submit_button("💾 Atualizar nome", use_container_width=True, type="primary")

if salvar_nome:
    if len(novo_nome.strip()) < 3:
        st.error("⚠️ O nome deve ter ao menos 3 caracteres.")
    else:
        try:
            result = update_profile(user_id, full_name=novo_nome)
            st.session_state["user"]["full_name"] = result["full_name"]
            st.success(f"✅ Nome atualizado para **{result['full_name']}**.")
            st.rerun()
        except AuthError as e:
            st.error(f"❌ {e.message}")

st.divider()

# ── Seção 3: Alterar senha ────────────────────────────────────────────────────
st.html('<p class="ccu-section-title">🔑 Alterar senha</p>')

with st.form("form_senha"):
    senha_atual  = st.text_input("Senha atual", type="password")
    nova_senha   = st.text_input("Nova senha",  type="password", placeholder="Mínimo 8 caracteres")
    nova_senha2  = st.text_input("Confirmar nova senha", type="password")
    alterar_senha = st.form_submit_button("🔒 Alterar senha", use_container_width=True)

if alterar_senha:
    erros = []
    if not senha_atual:
        erros.append("Informe a senha atual.")
    if len(nova_senha) < 8:
        erros.append("A nova senha deve ter ao menos 8 caracteres.")
    if nova_senha != nova_senha2:
        erros.append("As senhas não coincidem.")
    if erros:
        for e in erros:
            st.error(f"⚠️ {e}")
    else:
        try:
            update_profile(user_id, new_password=nova_senha, current_password=senha_atual)
            st.success("✅ Senha alterada com sucesso!")
        except AuthError as e:
            st.error(f"❌ {e.message}")
