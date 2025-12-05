"""
Servicio de Email para HPS en Django
Lógica de negocio para envío de correos relacionados con HPS
"""
import logging
from typing import Optional, Dict, Any
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from .models import HpsRequest
from .email_templates import (
    UserCredentialsTemplate, 
    StatusUpdateTemplate, 
    ConfirmationTemplate,
    HpsApprovedTemplate,
    HpsRejectedTemplate
)

logger = logging.getLogger(__name__)


class HpsEmailService:
    """Servicio principal de email para HPS"""
    
    def __init__(self):
        # Priorizar SMTP_FROM_EMAIL si está definido, sino usar DEFAULT_FROM_EMAIL
        self.from_email = getattr(settings, 'SMTP_FROM_EMAIL', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@cryptotrace.local')
        self.from_name = getattr(settings, 'SMTP_FROM_NAME', 'CryptoTrace HPS')
        self.reply_to = getattr(settings, 'SMTP_REPLY_TO', getattr(settings, 'EMAIL_HOST_USER', ''))
    
    def send_hps_confirmation_email(self, hps_request: HpsRequest) -> bool:
        """
        Envía correo de confirmación de solicitud HPS
        
        Args:
            hps_request: Solicitud HPS
            
        Returns:
            True si se envió correctamente
        """
        try:
            user = hps_request.user
            if not user or not user.email:
                logger.warning(f"No se puede enviar email: usuario sin email para HPS {hps_request.id}")
                return False
            
            subject = f"Confirmación de Solicitud HPS - {hps_request.get_request_type_display()}"
            
            # Usar template de confirmación
            template_data = {
                'user_name': f"{hps_request.first_name} {hps_request.first_last_name}",
                'user_email': user.email,
                'document_number': hps_request.document_number,
                'request_type': hps_request.get_request_type_display(),
                'status': hps_request.get_status_display(),
            }
            
            template = ConfirmationTemplate.get_template(template_data)
            subject = template['subject']
            text_message = template['body']
            html_message = template['html_body']
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=self.from_email,
                to=[user.email]
            )
            
            # Añadir reply-to si está configurado
            if self.reply_to:
                email.reply_to = [self.reply_to]
            
            if html_message:
                email.attach_alternative(html_message, "text/html")
            
            email.send()
            logger.info(f"Email de confirmación enviado para HPS {hps_request.id} a {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando correo de confirmación HPS {hps_request.id}: {str(e)}")
            return False
    
    def send_hps_status_update_email(
        self, 
        hps_request: HpsRequest, 
        new_status: str,
        old_status: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Envía correo de actualización de estado de solicitud HPS
        
        Args:
            hps_request: Solicitud HPS
            new_status: Nuevo estado
            old_status: Estado anterior (opcional)
            additional_data: Datos adicionales (ej: información del correo original del gobierno)
            
        Returns:
            True si se envió correctamente
        """
        try:
            user = hps_request.user
            if not user or not user.email:
                logger.warning(f"No se puede enviar email: usuario sin email para HPS {hps_request.id}")
                return False
            
            # Usar template específico según el estado
            # Asegurar que los estados sean strings
            new_status_str = str(new_status) if new_status else str(hps_request.status)
            old_status_str = str(old_status) if old_status else None
            
            template_data = {
                'user_name': f"{hps_request.first_name} {hps_request.first_last_name}",
                'user_email': user.email,
                'document_number': hps_request.document_number,
                'request_type': hps_request.get_request_type_display(),
                'status': new_status_str,
                'old_status': old_status_str,
            }
            
            # Usar template específico para aprobación/rechazo, o genérico para otros estados
            if new_status_str == 'approved':
                template_data['expires_at'] = hps_request.expires_at.strftime('%d/%m/%Y') if hps_request.expires_at else 'N/A'
                template_data['notes'] = hps_request.notes or ''
                template = HpsApprovedTemplate.get_template(template_data)
            elif new_status_str == 'rejected':
                template_data['rejection_reason'] = hps_request.notes or 'No especificado'
                template_data['notes'] = hps_request.notes or ''
                template = HpsRejectedTemplate.get_template(template_data)
            else:
                # Para otros estados, usar template genérico de actualización
                # Incluir información del correo original si está disponible
                template_data['additional_data'] = additional_data or {}
                template = StatusUpdateTemplate.get_template(template_data)
            
            subject = template['subject']
            text_message = template['body']
            html_message = template['html_body']
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=self.from_email,
                to=[user.email]
            )
            
            # Añadir reply-to si está configurado
            if self.reply_to:
                email.reply_to = [self.reply_to]
            
            if html_message:
                email.attach_alternative(html_message, "text/html")
            
            email.send()
            logger.info(f"Email de actualización enviado para HPS {hps_request.id} a {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando correo de actualización HPS {hps_request.id}: {str(e)}")
            return False
    
    def send_user_credentials_email(
        self,
        email: str,
        username: str,
        password: str,
        user_name: str
    ) -> bool:
        """
        Envía correo con credenciales de nuevo usuario
        
        Args:
            email: Email del destinatario
            username: Nombre de usuario
            password: Contraseña temporal
            user_name: Nombre completo del usuario
            
        Returns:
            True si se envió correctamente
        """
        try:
            # Usar template de credenciales
            # Para credenciales HPS, usar HPS_SYSTEM_URL en lugar de FRONTEND_URL
            # Sin fallback - debe estar definida en settings
            hps_system_url = getattr(settings, 'HPS_SYSTEM_URL', None)
            if not hps_system_url:
                logger.warning("HPS_SYSTEM_URL no está definida en settings")
            template_data = {
                'user_name': user_name,
                'user_email': email,
                'temp_password': password,
                'login_url': hps_system_url + '/login',
            }
            
            template = UserCredentialsTemplate.get_template(template_data)
            subject = template['subject']
            text_message = template['body']
            html_message = template['html_body']
            
            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=self.from_email,
                to=[email]
            )
            
            # Añadir reply-to si está configurado
            if self.reply_to:
                email_msg.reply_to = [self.reply_to]
            
            if html_message:
                email_msg.attach_alternative(html_message, "text/html")
            
            email_msg.send()
            logger.info(f"Email de credenciales enviado a {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando correo de credenciales a {email}: {str(e)}")
            return False
    
    def send_hps_form_email(self, email: str, form_url: str, user_name: str = "") -> bool:
        """
        Envía correo con enlace al formulario HPS
        
        Args:
            email: Email del destinatario
            form_url: URL del formulario HPS
            user_name: Nombre del usuario (opcional)
            
        Returns:
            True si se envió correctamente
        """
        try:
            subject = "Formulario HPS - Complete su solicitud"
            
            # Crear mensaje simple con el enlace
            text_message = f"""
Hola {user_name or 'Usuario'},

Se ha generado un formulario HPS para usted. Por favor, complete el formulario en el siguiente enlace:

{form_url}

Este enlace es válido por tiempo limitado. Si tiene alguna pregunta, por favor contacte con el administrador.

Saludos,
Equipo CryptoTrace HPS
"""
            
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .button:hover {{ background-color: #0056b3; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Formulario HPS</h2>
        <p>Hola {user_name or 'Usuario'},</p>
        <p>Se ha generado un formulario HPS para usted. Por favor, complete el formulario haciendo clic en el siguiente botón:</p>
        <a href="{form_url}" class="button">Completar Formulario HPS</a>
        <p>O copie y pegue este enlace en su navegador:</p>
        <p><a href="{form_url}">{form_url}</a></p>
        <p>Este enlace es válido por tiempo limitado. Si tiene alguna pregunta, por favor contacte con el administrador.</p>
        <p>Saludos,<br>Equipo CryptoTrace HPS</p>
    </div>
</body>
</html>
"""
            
            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=self.from_email,
                to=[email]
            )
            
            # Añadir reply-to si está configurado
            if self.reply_to:
                email_msg.reply_to = [self.reply_to]
            
            if html_message:
                email_msg.attach_alternative(html_message, "text/html")
            
            email_msg.send()
            logger.info(f"Email con formulario HPS enviado a {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando correo con formulario HPS a {email}: {str(e)}")
            return False

