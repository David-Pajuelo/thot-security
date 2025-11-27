"""
Cliente SMTP para envío de correos electrónicos
Maneja la conexión y envío via Gmail SMTP
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from .schemas import EmailMessage, EmailStatus

logger = logging.getLogger(__name__)


class SMTPClient:
    """Cliente SMTP para envío de correos"""
    
    def __init__(
        self,
        host: str = "smtp.gmail.com",
        port: int = 587,
        username: str = "",
        password: str = "",
        from_name: str = "HPS System",
        reply_to: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_name = from_name
        self.reply_to = reply_to or username or "noreply@hps-system.com"
        
    def _create_connection(self) -> smtplib.SMTP:
        """Crea una conexión SMTP segura"""
        try:
            # Crear contexto SSL
            context = ssl.create_default_context()
            
            # Conectar al servidor SMTP
            server = smtplib.SMTP(self.host, self.port)
            server.starttls(context=context)
            
            # Autenticar
            server.login(self.username, self.password)
            
            logger.info(f"Conectado exitosamente a SMTP {self.host}:{self.port}")
            return server
            
        except Exception as e:
            logger.error(f"Error conectando a SMTP: {str(e)}")
            raise
    
    def _create_message(self, email: EmailMessage) -> MIMEMultipart:
        """Crea un mensaje MIME multipart"""
        msg = MIMEMultipart('alternative')
        
        # Headers del mensaje
        msg['From'] = f"{self.from_name} <{self.username}>"
        msg['To'] = email.to
        msg['Subject'] = email.subject
        
        if email.reply_to:
            msg['Reply-To'] = email.reply_to
        
        # Cuerpo del mensaje
        if email.html_body:
            # Crear partes de texto y HTML
            text_part = MIMEText(email.body, 'plain', 'utf-8')
            html_part = MIMEText(email.html_body, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
        else:
            # Solo texto plano
            text_part = MIMEText(email.body, 'plain', 'utf-8')
            msg.attach(text_part)
        
        # Adjuntos
        if email.attachments:
            for attachment in email.attachments:
                self._add_attachment(msg, attachment)
        
        return msg
    
    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """Añade un adjunto al mensaje"""
        try:
            filename = attachment.get('filename', 'attachment')
            content = attachment.get('content', b'')
            content_type = attachment.get('content_type', 'application/octet-stream')
            
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Error añadiendo adjunto: {str(e)}")
    
    def send_email(self, email: EmailMessage) -> Dict[str, Any]:
        """
        Envía un correo electrónico
        
        Args:
            email: Objeto EmailMessage con los datos del correo
            
        Returns:
            Dict con el resultado del envío
        """
        try:
            # Crear conexión
            server = self._create_connection()
            
            # Crear mensaje
            msg = self._create_message(email)
            
            # Enviar correo
            text = msg.as_string()
            server.sendmail(self.username, email.to, text)
            server.quit()
            
            logger.info(f"Correo enviado exitosamente a {email.to}")
            
            return {
                "success": True,
                "message": "Correo enviado exitosamente",
                "message_id": msg['Message-ID'] if 'Message-ID' in msg else None,
                "sent_at": datetime.utcnow().isoformat()
            }
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"Error de autenticación SMTP: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": "Error de autenticación",
                "error": error_msg
            }
            
        except smtplib.SMTPRecipientsRefused as e:
            error_msg = f"Destinatario rechazado: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": "Destinatario inválido",
                "error": error_msg
            }
            
        except smtplib.SMTPServerDisconnected as e:
            error_msg = f"Servidor SMTP desconectado: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": "Error de conexión con el servidor",
                "error": error_msg
            }
            
        except Exception as e:
            error_msg = f"Error inesperado enviando correo: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": "Error inesperado",
                "error": error_msg
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Prueba la conexión SMTP
        
        Returns:
            Dict con el resultado de la prueba
        """
        try:
            server = self._create_connection()
            server.quit()
            
            return {
                "success": True,
                "message": "Conexión SMTP exitosa",
                "host": self.host,
                "port": self.port,
                "username": self.username
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error de conexión: {str(e)}",
                "host": self.host,
                "port": self.port,
                "username": self.username
            }
