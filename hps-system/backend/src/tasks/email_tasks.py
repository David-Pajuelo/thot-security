"""
Tareas asíncronas para envío de emails
"""
import logging
from typing import Dict, Any, Optional
from celery import current_task
from src.celery_app import celery_app
from src.email.service import EmailService
from src.email.schemas import SendEmailRequest, EmailTemplateData
from src.database.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="send_email_task")
def send_email_task(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tarea asíncrona para envío de emails
    
    Args:
        email_data: Datos del email a enviar
        
    Returns:
        Resultado del envío
    """
    try:
        # Actualizar estado de la tarea
        current_task.update_state(
            state="PROGRESS",
            meta={"status": "Iniciando envío de email", "progress": 10}
        )
        
        # Crear servicio de email
        email_service = EmailService(
            smtp_host=email_data.get("smtp_host", "smtp.gmail.com"),
            smtp_port=email_data.get("smtp_port", 587),
            smtp_username=email_data.get("smtp_username"),
            smtp_password=email_data.get("smtp_password"),
            imap_host=email_data.get("imap_host", "imap.gmail.com"),
            imap_port=email_data.get("imap_port", 993),
            imap_username=email_data.get("imap_username"),
            imap_password=email_data.get("imap_password"),
            from_name=email_data.get("from_name", "HPS System"),
            reply_to=email_data.get("reply_to")
        )
        
        current_task.update_state(
            state="PROGRESS",
            meta={"status": "Servicio de email creado", "progress": 30}
        )
        
        # Crear request de email
        template_data = EmailTemplateData(**email_data["template_data"])
        email_request = SendEmailRequest(
            to=email_data["to"],
            template=email_data["template"],
            template_data=template_data,
            custom_subject=email_data.get("custom_subject"),
            custom_body=email_data.get("custom_body")
        )
        
        current_task.update_state(
            state="PROGRESS",
            meta={"status": "Enviando email", "progress": 50}
        )
        
        # Obtener sesión de base de datos
        db = next(get_db())
        
        # Enviar email
        result = email_service.send_email_with_template(email_request, db)
        
        current_task.update_state(
            state="PROGRESS",
            meta={"status": "Email enviado", "progress": 90}
        )
        
        # Cerrar sesión de base de datos
        db.close()
        
        if result.success:
            logger.info(f"Email enviado exitosamente a {email_data['to']}")
            return {
                "success": True,
                "message": "Email enviado exitosamente",
                "email_id": result.email_id,
                "to": email_data["to"],
                "task_id": self.request.id
            }
        else:
            logger.error(f"Error enviando email a {email_data['to']}: {result.message}")
            return {
                "success": False,
                "message": result.message,
                "error": result.error,
                "to": email_data["to"],
                "task_id": self.request.id
            }
            
    except Exception as e:
        logger.error(f"Error en tarea de envío de email: {str(e)}")
        current_task.update_state(
            state="FAILURE",
            meta={"error": str(e), "to": email_data.get("to", "unknown")}
        )
        return {
            "success": False,
            "message": "Error interno en envío de email",
            "error": str(e),
            "to": email_data.get("to", "unknown"),
            "task_id": self.request.id
        }

@celery_app.task(bind=True, name="send_hps_form_email_task")
def send_hps_form_email_task(self, email: str, form_url: str, user_name: str, 
                            smtp_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tarea específica para envío de formularios HPS
    
    Args:
        email: Email del destinatario
        form_url: URL del formulario HPS
        user_name: Nombre del usuario
        smtp_config: Configuración SMTP
        
    Returns:
        Resultado del envío
    """
    try:
        current_task.update_state(
            state="PROGRESS",
            meta={"status": "Preparando email HPS", "progress": 20}
        )
        
        # Preparar datos del email
        email_data = {
            "to": email,
            "template": "hps_form",
            "template_data": {
                "user_name": user_name,
                "user_email": email,
                "additional_data": {
                    "form_url": form_url
                }
            },
            **smtp_config
        }
        
        # Llamar a la tarea de envío de email
        result = send_email_task.delay(email_data)
        
        return {
            "success": True,
            "message": "Tarea de envío HPS encolada",
            "task_id": result.id,
            "email": email,
            "form_url": form_url
        }
        
    except Exception as e:
        logger.error(f"Error en tarea de envío HPS: {str(e)}")
        return {
            "success": False,
            "message": "Error encolando tarea de envío HPS",
            "error": str(e),
            "email": email
        }

@celery_app.task(bind=True, name="send_bulk_emails_task")
def send_bulk_emails_task(self, emails_data: list, smtp_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tarea para envío masivo de emails
    
    Args:
        emails_data: Lista de datos de emails
        smtp_config: Configuración SMTP
        
    Returns:
        Resultado del envío masivo
    """
    try:
        results = []
        total_emails = len(emails_data)
        
        for i, email_data in enumerate(emails_data):
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "status": f"Enviando email {i+1}/{total_emails}",
                    "progress": int((i / total_emails) * 100)
                }
            )
            
            # Agregar configuración SMTP
            email_data.update(smtp_config)
            
            # Enviar email
            result = send_email_task.delay(email_data)
            results.append({
                "email": email_data["to"],
                "task_id": result.id,
                "status": "enqueued"
            })
        
        return {
            "success": True,
            "message": f"Encolados {total_emails} emails",
            "total_emails": total_emails,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error en tarea de envío masivo: {str(e)}")
        return {
            "success": False,
            "message": "Error en envío masivo de emails",
            "error": str(e)
        }
