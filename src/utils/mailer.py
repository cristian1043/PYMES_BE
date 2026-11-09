import os
import smtplib
import threading
from email.message import EmailMessage


class Mailer:
    """
    Utilidad de despacho de correos electrónicos vía SMTP (Gmail / Outlook / SMTP corporativo).
    Ejecuta el despacho de red en un hilo en segundo plano (no bloqueante) para evitar
    timeouts HTTP (ej. en Render u otros entornos cloud cuando el puerto 587 tiene latencia o bloqueo).
    """

    @staticmethod
    def _despachar_smtp_sync(smtp_host: str, smtp_port: int, smtp_user: str, smtp_pass: str, msg: EmailMessage, destinatario: str):
        try:
            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=4) as server:
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=4) as server:
                    server.ehlo()
                    if smtp_port in (587, 25):
                        server.starttls()
                        server.ehlo()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
            print(f"[MAILER SMTP] Correo enviado exitosamente a {destinatario}")
        except Exception as e:
            print(f"[MAILER ERROR] No se pudo enviar correo SMTP a {destinatario}: {e}")

    @staticmethod
    def enviar_correo(destinatario: str, asunto: str, cuerpo_html: str, cuerpo_texto: str = "") -> bool:
        smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com").strip()
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = (
            os.environ.get("SMTP_USER")
            or os.environ.get("GMAIL_USER")
            or os.environ.get("MAIL_USERNAME")
            or ""
        ).strip()
        smtp_pass = (
            os.environ.get("SMTP_PASSWORD")
            or os.environ.get("GMAIL_APP_PASSWORD")
            or os.environ.get("MAIL_PASSWORD")
            or ""
        ).strip()
        smtp_from = os.environ.get("SMTP_FROM", smtp_user or "no-reply@pymesoft.co").strip()

        if not smtp_user or not smtp_pass:
            print(f"[MAILER LOCAL] Sin credenciales SMTP configuradas. Destinatario: {destinatario} | Asunto: {asunto}")
            return False

        try:
            msg = EmailMessage()
            msg["Subject"] = asunto
            msg["From"] = f"PYMESOFT Seguridad <{smtp_from}>"
            msg["To"] = destinatario
            msg.set_content(cuerpo_texto or "Código de verificación de seguridad PYMESOFT.")
            msg.add_alternative(cuerpo_html, subtype="html")

            hilo = threading.Thread(
                target=Mailer._despachar_smtp_sync,
                args=(smtp_host, smtp_port, smtp_user, smtp_pass, msg, destinatario),
                daemon=True,
            )
            hilo.start()
            return True
        except Exception as e:
            print(f"[MAILER ERROR] Fallo al programar envío de correo a {destinatario}: {e}")
            return False

    @staticmethod
    def enviar_codigo_recuperacion(destinatario: str, nombre: str, otp_codigo: str, link_recuperacion: str) -> bool:
        asunto = f"🔑 Código de recuperación PYMESOFT: {otp_codigo}"
        cuerpo_texto = (
            f"Hola {nombre},\n\n"
            f"Tu código de verificación para restablecer tu contraseña en PYMESOFT es: {otp_codigo}\n"
            f"También puedes usar este enlace directo: {link_recuperacion}\n\n"
            f"Este código expira en 30 minutos."
        )
        cuerpo_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
            <div style="background: #1e3c72; color: #ffffff; padding: 20px; text-align: center;">
                <h2 style="margin: 0;">PYMESOFT</h2>
                <p style="margin: 4px 0 0 0; opacity: 0.85; font-size: 13px;">Recuperación y Restablecimiento de Contraseña</p>
            </div>
            <div style="padding: 24px; color: #1e293b; background: #ffffff;">
                <p>Hola <strong>{nombre}</strong>,</p>
                <p>Recibimos una solicitud para restablecer tu contraseña. Utiliza el siguiente código de verificación de 6 dígitos:</p>
                <div style="background: #f1f5f9; border: 2px dashed #1e3c72; border-radius: 10px; padding: 16px; text-align: center; margin: 20px 0;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #1e3c72;">{otp_codigo}</span>
                </div>
                <p style="font-size: 13px; color: #64748b;">Este código es válido durante 30 minutos.</p>
            </div>
        </div>
        """
        return Mailer.enviar_correo(destinatario, asunto, cuerpo_html, cuerpo_texto)

    @staticmethod
    def enviar_codigo_eliminacion(destinatario: str, nombre: str, otp_codigo: str) -> bool:
        asunto = f"⚠️ Código de verificación para eliminar cuenta PYMESOFT: {otp_codigo}"
        cuerpo_texto = (
            f"Hola {nombre},\n\n"
            f"Has iniciado el proceso de eliminación de tu cuenta en PYMESOFT.\n"
            f"Tu código de verificación de segundo paso (2FA) es: {otp_codigo}\n\n"
            f"Este código expira en 10 minutos. Si no solicitaste esto, cambia tu contraseña inmediatamente."
        )
        cuerpo_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; border: 1px solid #fecaca; border-radius: 12px; overflow: hidden;">
            <div style="background: #dc2626; color: #ffffff; padding: 20px; text-align: center;">
                <h2 style="margin: 0;">⚠️ Verificación de 2 Pasos — PYMESOFT</h2>
                <p style="margin: 4px 0 0 0; opacity: 0.9; font-size: 13px;">Confirmación de Eliminación de Cuenta</p>
            </div>
            <div style="padding: 24px; color: #1e293b; background: #ffffff;">
                <p>Hola <strong>{nombre}</strong>,</p>
                <p>Para completar el segundo paso y confirmar la eliminación definitiva de tu cuenta, ingresa este código de 6 dígitos:</p>
                <div style="background: #fef2f2; border: 2px dashed #dc2626; border-radius: 10px; padding: 16px; text-align: center; margin: 20px 0;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #dc2626;">{otp_codigo}</span>
                </div>
                <p style="font-size: 13px; color: #64748b;">Este código expira en 10 minutos.</p>
            </div>
        </div>
        """
        return Mailer.enviar_correo(destinatario, asunto, cuerpo_html, cuerpo_texto)
