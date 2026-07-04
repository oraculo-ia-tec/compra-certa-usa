"""
AGENTE 2 - CORE-LOGIC
Servico de notificacoes por email (SMTP Hostinger).
Usado para notificar clientes sobre mudancas de status do pedido
e para envios do fluxo de autenticação (verificação, reset de senha, pagamento).
"""
import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger

from core.config import settings
from services.schemas import ToolResult


# ---------------------------------------------------------------------------
# Helpers para funções de autenticação (lêem st.secrets)
# ---------------------------------------------------------------------------

def _cfg():
    try:
        return st.secrets["email"]
    except Exception:
        return {}


def _get_base_url() -> str:
    for getter in [
        lambda: st.secrets["email"]["APP_BASE_URL"],
        lambda: st.secrets["default"]["APP_BASE_URL"],
        lambda: st.secrets["APP_BASE_URL"],
    ]:
        try:
            url = getter()
            if url:
                return url.rstrip("/")
        except Exception:
            pass
    return "http://localhost:8501"


def _send(to_email: str, subject: str, html_body: str) -> bool:
    cfg = _cfg()
    if not cfg:
        logger.error("[email] Secrets não configuradas")
        return False

    host      = cfg.get("EMAIL_HOST",     "smtp.hostinger.com")
    port      = int(cfg.get("EMAIL_PORT", 587))
    username  = cfg.get("EMAIL_USERNAME", "")
    password  = cfg.get("EMAIL_PASSWORD", "")
    remetente = cfg.get("EMAIL_REMETENTE", username)

    if not username or not password:
        logger.error("[email] EMAIL_USERNAME ou EMAIL_PASSWORD vazios")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"Compra Certa USA <{remetente}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls()
            server.login(username, password)
            server.sendmail(username, to_email, msg.as_string())

        logger.info(f"[email] Enviado para {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"[email] Erro ao enviar para {to_email}: {e}")
        return False


def send_verification_code_email(to_email: str, full_name: str, code: str) -> bool:
    """Envia e-mail com código numérico de 8 dígitos para verificação de conta."""
    base_url = _get_base_url()
    confirm_url = f"{base_url}/Confirmar_Conta"
    code_display = f"{code[:4]}&nbsp;&nbsp;{code[4:]}"
    first_name = full_name.split()[0] if full_name else "cliente"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F1F5F9;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(30,58,138,.10);">
        <tr>
          <td style="background:#1E3A8A;padding:32px 40px;text-align:center;">
            <p style="margin:0;font-size:28px;font-weight:700;color:#FFFFFF;letter-spacing:1px;">📦 COMPRA CERTA USA</p>
            <p style="margin:8px 0 0;font-size:13px;color:#93C5FD;">Redirecionamento de compras dos EUA para o Brasil</p>
          </td>
        </tr>
        <tr>
          <td style="padding:40px 40px 32px;">
            <p style="margin:0 0 8px;font-size:22px;font-weight:600;color:#0F172A;">Olá, {first_name}! 👋</p>
            <p style="margin:0 0 24px;font-size:15px;color:#475569;line-height:1.6;">
              Obrigado por se cadastrar na <strong>Compra Certa USA</strong>.<br>
              Use o código abaixo para ativar sua conta. Ele é válido por <strong>15 minutos</strong>.
            </p>
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr><td align="center" style="padding:24px 0;">
                <div style="display:inline-block;background:#EFF6FF;border:2px dashed #1E3A8A;border-radius:12px;padding:20px 48px;">
                  <p style="margin:0;font-size:11px;font-weight:600;color:#64748B;letter-spacing:3px;text-transform:uppercase;">Código de verificação</p>
                  <p style="margin:8px 0 0;font-size:40px;font-weight:800;color:#1E3A8A;letter-spacing:8px;font-family:'Courier New',monospace;">{code_display}</p>
                </div>
              </td></tr>
            </table>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin:8px 0 24px;">
              <tr><td align="center">
                <a href="{confirm_url}" style="display:inline-block;background:#1E3A8A;color:#FFFFFF;font-size:15px;font-weight:600;text-decoration:none;padding:14px 40px;border-radius:8px;">
                  Confirmar minha conta →
                </a>
              </td></tr>
            </table>
            <p style="margin:0;font-size:13px;color:#94A3B8;line-height:1.6;">
              Se você não se cadastrou na Compra Certa USA, ignore este e-mail com segurança.<br>
              Nunca compartilhe este código com ninguém.
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;text-align:center;">
            <p style="margin:0;font-size:12px;color:#94A3B8;">© 2026 Compra Certa USA · contato@oraculosia.site</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    return _send(to_email, "🔐 Seu código de verificação — Compra Certa USA", html)


def send_password_reset_email(to_email: str, full_name: str, reset_token: str) -> bool:
    """Envia e-mail com link de redefinição de senha."""
    base_url = _get_base_url()
    reset_url = f"{base_url}/Redefinir_Senha?token={reset_token}"
    first_name = full_name.split()[0] if full_name else "cliente"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F1F5F9;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(30,58,138,.10);">
        <tr>
          <td style="background:#1E3A8A;padding:32px 40px;text-align:center;">
            <p style="margin:0;font-size:28px;font-weight:700;color:#FFFFFF;letter-spacing:1px;">📦 COMPRA CERTA USA</p>
            <p style="margin:8px 0 0;font-size:13px;color:#93C5FD;">Redirecionamento de compras dos EUA para o Brasil</p>
          </td>
        </tr>
        <tr>
          <td style="padding:40px 40px 32px;">
            <p style="margin:0 0 8px;font-size:22px;font-weight:600;color:#0F172A;">Olá, {first_name}!</p>
            <p style="margin:0 0 24px;font-size:15px;color:#475569;line-height:1.6;">
              Recebemos uma solicitação para redefinir a senha da sua conta.<br>
              Clique no botão abaixo — o link é válido por <strong>1 hora</strong>.
            </p>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin:8px 0 32px;">
              <tr><td align="center">
                <a href="{reset_url}" style="display:inline-block;background:#1E3A8A;color:#FFFFFF;font-size:15px;font-weight:600;text-decoration:none;padding:14px 40px;border-radius:8px;">
                  Redefinir minha senha →
                </a>
              </td></tr>
            </table>
            <p style="margin:0 0 8px;font-size:13px;color:#64748B;">Se o botão não funcionar, copie e cole o link abaixo no navegador:</p>
            <p style="margin:0 0 24px;font-size:12px;color:#1E3A8A;word-break:break-all;">{reset_url}</p>
            <p style="margin:0;font-size:13px;color:#94A3B8;line-height:1.6;">
              Se você não solicitou a redefinição, ignore este e-mail — sua senha permanece a mesma.
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;text-align:center;">
            <p style="margin:0;font-size:12px;color:#94A3B8;">© 2026 Compra Certa USA · contato@oraculosia.site</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    return _send(to_email, "🔑 Redefinição de senha — Compra Certa USA", html)


def send_payment_success_email(to_email: str, full_name: str, plan_name: str) -> bool:
    """Envia e-mail de confirmação de pagamento/assinatura."""
    base_url = _get_base_url()
    dashboard_url = f"{base_url}/Meus_Pedidos"
    first_name = full_name.split()[0] if full_name else "cliente"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F1F5F9;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(30,58,138,.10);">
        <tr>
          <td style="background:#1E3A8A;padding:32px 40px;text-align:center;">
            <p style="margin:0;font-size:28px;font-weight:700;color:#FFFFFF;letter-spacing:1px;">📦 COMPRA CERTA USA</p>
            <p style="margin:8px 0 0;font-size:13px;color:#93C5FD;">Redirecionamento de compras dos EUA para o Brasil</p>
          </td>
        </tr>
        <tr>
          <td style="padding:40px 40px 32px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr><td align="center" style="padding-bottom:24px;">
                <div style="display:inline-block;background:#DCFCE7;border-radius:50%;width:64px;height:64px;line-height:64px;text-align:center;font-size:32px;">✅</div>
              </td></tr>
            </table>
            <p style="margin:0 0 8px;font-size:22px;font-weight:600;color:#0F172A;text-align:center;">Pagamento confirmado!</p>
            <p style="margin:0 0 24px;font-size:15px;color:#475569;line-height:1.6;text-align:center;">
              Parabéns, <strong>{first_name}</strong>! Seu plano <strong>{plan_name}</strong> está ativo.<br>
              Agora você pode criar pedidos e acompanhar suas encomendas.
            </p>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
              <tr>
                <td style="background:#EFF6FF;border-left:4px solid #1E3A8A;border-radius:0 8px 8px 0;padding:16px 24px;">
                  <p style="margin:0;font-size:13px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:1px;">Plano ativo</p>
                  <p style="margin:4px 0 0;font-size:20px;font-weight:700;color:#1E3A8A;">{plan_name}</p>
                </td>
              </tr>
            </table>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
              <tr><td align="center">
                <a href="{dashboard_url}" style="display:inline-block;background:#1E3A8A;color:#FFFFFF;font-size:15px;font-weight:600;text-decoration:none;padding:14px 40px;border-radius:8px;">
                  Acessar meus pedidos →
                </a>
              </td></tr>
            </table>
            <p style="margin:0;font-size:13px;color:#94A3B8;line-height:1.6;text-align:center;">
              Em caso de dúvidas: contato@oraculosia.site
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;text-align:center;">
            <p style="margin:0;font-size:12px;color:#94A3B8;">© 2026 Compra Certa USA · contato@oraculosia.site</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    return _send(to_email, f"✅ Pagamento confirmado — Plano {plan_name} ativo!", html)


class EmailService:
    """
    Hipotese declarada: envio sincrono e bloqueante. Em fase futura,
    considerar fila assincrona (ex: background task) para nao travar a UI.
    """

    def enviar_email(self, destinatario: str, assunto: str, corpo_html: str) -> ToolResult:
        if not settings.email_configurado():
            return ToolResult(sucesso=False, erro="Configuracao de email ausente (EMAIL_HOST/USERNAME/PASSWORD).")

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = assunto
            msg["From"] = settings.EMAIL_REMETENTE or settings.EMAIL_USERNAME
            msg["To"] = destinatario
            msg.attach(MIMEText(corpo_html, "html"))

            if settings.EMAIL_USE_SSL:
                servidor = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
            else:
                servidor = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
                if settings.EMAIL_USE_TLS:
                    servidor.starttls()

            servidor.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            servidor.sendmail(msg["From"], [destinatario], msg.as_string())
            servidor.quit()

            return ToolResult(sucesso=True, dados={"destinatario": destinatario, "assunto": assunto})
        except Exception as e:
            return ToolResult(sucesso=False, erro=f"Falha ao enviar email: {str(e)}")

    def notificar_mudanca_status(self, destinatario: str, nome_cliente: str, pedido_id: int, novo_status_label: str) -> ToolResult:
        assunto = f"COMPRA CERTA USA - Atualizacao do pedido #{pedido_id}"
        corpo_html = f"""
        <div style="font-family: Arial, sans-serif;">
            <h2 style="color:#1E3A8A;">COMPRA CERTA USA</h2>
            <p>Ola, {nome_cliente}!</p>
            <p>Seu pedido <strong>#{pedido_id}</strong> teve o status atualizado para:</p>
            <p style="font-size:18px; color:#1E3A8A;"><strong>{novo_status_label}</strong></p>
            <p>Acompanhe todos os detalhes na plataforma.</p>
        </div>
        """
        return self.enviar_email(destinatario, assunto, corpo_html)
