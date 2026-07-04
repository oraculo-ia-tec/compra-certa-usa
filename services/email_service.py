"""
AGENTE 2 - CORE-LOGIC
Servico de notificacoes por email (SMTP Hostinger).
Usado para notificar clientes sobre mudancas de status do pedido.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from core.config import settings
from services.schemas import ToolResult


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
