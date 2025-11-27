"""
Servicio de Email para HPS System
Lógica de negocio para envío y recepción de correos
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .smtp_client import SMTPClient
from .imap_client import IMAPClient
from .template_manager import TemplateManager
from .schemas import (
    EmailMessage, EmailTemplate, EmailTemplateData, 
    SendEmailRequest, EmailResponse, ReceivedEmail,
    EmailStatus, EmailLog
)
from ..database.database import get_db
from ..models.hps import HPSRequest
from ..models.user import User

logger = logging.getLogger(__name__)


class EmailService:
    """Servicio principal de email"""
    
    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_username: str = "",
        smtp_password: str = "",
        imap_host: str = "imap.gmail.com",
        imap_port: int = 993,
        imap_username: str = "",
        imap_password: str = "",
        from_name: str = "HPS System",
        reply_to: Optional[str] = None
    ):
        # Clientes SMTP e IMAP
        self.smtp_client = SMTPClient(
            host=smtp_host,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            from_name=from_name,
            reply_to=reply_to or smtp_username
        )
        
        self.imap_client = IMAPClient(
            host=imap_host,
            port=imap_port,
            username=imap_username,
            password=imap_password
        )
    
    def send_email_with_template(
        self, 
        request: SendEmailRequest,
        db: Session
    ) -> EmailResponse:
        """
        Envía un correo usando un template
        
        Args:
            request: Datos del correo a enviar
            db: Sesión de base de datos
            
        Returns:
            Response con el resultado del envío
        """
        try:
            # Obtener template usando el gestor centralizado
            template_data = TemplateManager.get_template(
                request.template.value, 
                request.template_data
            )
            
            # Crear mensaje de correo
            email_message = EmailMessage(
                to=request.to,
                subject=request.custom_subject or template_data["subject"],
                body=request.custom_body or template_data["body"],
                html_body=template_data["html_body"],
                from_name=self.smtp_client.from_name,
                reply_to=self.smtp_client.reply_to
            )
            
            # Enviar correo
            result = self.smtp_client.send_email(email_message)
            
            # Log del correo
            self._log_email(
                db=db,
                message_id=result.get("message_id", ""),
                to=request.to,
                from_email=self.smtp_client.username,
                subject=email_message.subject,
                status=EmailStatus.SENT if result["success"] else EmailStatus.FAILED,
                template_used=request.template,
                hps_request_id=request.template_data.hps_request_id,
                error_message=result.get("error")
            )
            
            return EmailResponse(
                success=result["success"],
                message=result["message"],
                email_id=result.get("message_id"),
                error=result.get("error")
            )
            
        except Exception as e:
            logger.error(f"Error enviando correo con template: {str(e)}")
            return EmailResponse(
                success=False,
                message="Error inesperado enviando correo",
                error=str(e)
            )
    
    def send_confirmation_email(
        self, 
        hps_request_id: int,
        db: Session
    ) -> EmailResponse:
        """
        Envía correo de confirmación de solicitud HPS
        
        Args:
            hps_request_id: ID de la solicitud HPS
            db: Sesión de base de datos
            
        Returns:
            Response con el resultado del envío
        """
        try:
            # Obtener datos de la solicitud
            hps_request = db.query(HPSRequest).filter(
                HPSRequest.id == hps_request_id
            ).first()
            
            if not hps_request:
                return EmailResponse(
                    success=False,
                    message="Solicitud HPS no encontrada",
                    error="HPS request not found"
                )
            
            # Obtener datos del usuario
            user = db.query(User).filter(User.id == hps_request.user_id).first()
            
            if not user:
                return EmailResponse(
                    success=False,
                    message="Usuario no encontrado",
                    error="User not found"
                )
            
            # Crear datos del template
            template_data = EmailTemplateData(
                user_name=f"{hps_request.first_name} {hps_request.first_last_name}",
                user_email=user.email,
                hps_request_id=hps_request_id,
                document_number=hps_request.document_number,
                request_type=hps_request.request_type,
                status=hps_request.status
            )
            
            # Crear request
            send_request = SendEmailRequest(
                to=user.email,
                template=EmailTemplate.CONFIRMATION,
                template_data=template_data
            )
            
            return self.send_email_with_template(send_request, db)
            
        except Exception as e:
            logger.error(f"Error enviando correo de confirmación: {str(e)}")
            return EmailResponse(
                success=False,
                message="Error enviando correo de confirmación",
                error=str(e)
            )
    
    def send_status_update_email(
        self, 
        hps_request_id: int,
        new_status: str,
        old_status: str = None,
        original_email = None,
        db: Session = None
    ) -> EmailResponse:
        """
        Envía correo de actualización de estado incluyendo el correo original del gobierno
        
        Args:
            hps_request_id: ID de la solicitud HPS
            new_status: Nuevo estado de la solicitud
            old_status: Estado anterior (opcional)
            original_email: Correo original del gobierno que desencadenó el cambio (opcional)
            db: Sesión de base de datos
            
        Returns:
            Response con el resultado del envío
        """
        try:
            # Obtener datos de la solicitud
            hps_request = db.query(HPSRequest).filter(
                HPSRequest.id == hps_request_id
            ).first()
            
            if not hps_request:
                return EmailResponse(
                    success=False,
                    message="Solicitud HPS no encontrada",
                    error="HPS request not found"
                )
            
            # Obtener datos del usuario
            user = db.query(User).filter(User.id == hps_request.user_id).first()
            
            if not user:
                return EmailResponse(
                    success=False,
                    message="Usuario no encontrado",
                    error="User not found"
                )
            
            # Preparar datos adicionales con información del correo original
            additional_data = {
                "old_status": old_status or hps_request.status
            }
            
            # Si hay correo original, incluir su información
            if original_email:
                additional_data.update({
                    "original_email_from": getattr(original_email, 'from_email', 'N/A'),
                    "original_email_subject": getattr(original_email, 'subject', 'N/A'),
                    "original_email_body": getattr(original_email, 'body', 'N/A'),
                    "original_email_date": getattr(original_email, 'received_at', None)
                })
                # Formatear fecha si existe
                if additional_data.get("original_email_date"):
                    if hasattr(additional_data["original_email_date"], 'strftime'):
                        additional_data["original_email_date"] = additional_data["original_email_date"].strftime("%d/%m/%Y %H:%M")
                    else:
                        additional_data["original_email_date"] = str(additional_data["original_email_date"])
            
            # Crear datos del template
            template_data = EmailTemplateData(
                user_name=f"{hps_request.first_name} {hps_request.first_last_name}",
                user_email=user.email,
                hps_request_id=hps_request_id,
                document_number=hps_request.document_number,
                request_type=hps_request.request_type,
                status=new_status,
                additional_data=additional_data
            )
            
            # Crear request usando el template STATUS_UPDATE
            send_request = SendEmailRequest(
                to=user.email,
                template=EmailTemplate.STATUS_UPDATE,
                template_data=template_data
            )
            
            return self.send_email_with_template(send_request, db)
            
        except Exception as e:
            logger.error(f"Error enviando correo de actualización: {str(e)}")
            return EmailResponse(
                success=False,
                message="Error enviando correo de actualización",
                error=str(e)
            )
    
    def check_new_emails(self, since_days: int = 1) -> List[ReceivedEmail]:
        """
        Revisa correos nuevos recibidos
        
        Args:
            since_days: Días hacia atrás para buscar
            
        Returns:
            Lista de correos recibidos
        """
        try:
            emails = self.imap_client.get_unread_emails(since_days)
            logger.info(f"Obtenidos {len(emails)} correos nuevos")
            return emails
            
        except Exception as e:
            logger.error(f"Error obteniendo correos nuevos: {str(e)}")
            return []
    
    def mark_email_as_read(self, message_id: str) -> bool:
        """
        Marca un correo como leído
        
        Args:
            message_id: ID del mensaje
            
        Returns:
            True si se marcó exitosamente
        """
        try:
            return self.imap_client.mark_as_read(message_id)
        except Exception as e:
            logger.error(f"Error marcando correo como leído: {str(e)}")
            return False
    
    def test_connections(self) -> Dict[str, Any]:
        """
        Prueba las conexiones SMTP e IMAP
        
        Returns:
            Dict con resultados de las pruebas
        """
        smtp_result = self.smtp_client.test_connection()
        imap_result = self.imap_client.test_connection()
        
        return {
            "smtp": smtp_result,
            "imap": imap_result,
            "overall_success": smtp_result["success"] and imap_result["success"]
        }
    
    def _log_email(
        self,
        db: Session,
        message_id: str,
        to: str,
        from_email: str,
        subject: str,
        status: EmailStatus,
        template_used: Optional[EmailTemplate] = None,
        hps_request_id: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """
        Registra un correo en el log
        
        Args:
            db: Sesión de base de datos
            message_id: ID del mensaje
            to: Destinatario
            from_email: Remitente
            subject: Asunto
            status: Estado del correo
            template_used: Template utilizado
            hps_request_id: ID de solicitud HPS
            error_message: Mensaje de error
        """
        try:
            # TODO: Implementar tabla de logs de email en la base de datos
            # Por ahora solo log en archivo
            logger.info(f"Email logged: {message_id} - {to} - {status.value}")
            
        except Exception as e:
            logger.error(f"Error registrando email en log: {str(e)}")
    
    def get_email_logs(
        self, 
        db: Session,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Obtiene logs de correos
        
        Args:
            db: Sesión de base de datos
            limit: Límite de resultados
            offset: Offset para paginación
            
        Returns:
            Lista de logs de correos
        """
        try:
            # TODO: Implementar consulta a tabla de logs de email
            # Por ahora retornar lista vacía
            return []
            
        except Exception as e:
            logger.error(f"Error obteniendo logs de email: {str(e)}")
            return []
