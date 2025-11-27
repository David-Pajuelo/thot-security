"""
Router de Email para HPS System
Endpoints REST para funcionalidades de email
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging
import os

from .service import EmailService
from .schemas import (
    SendEmailRequest, EmailResponse, EmailTemplateData,
    EmailTemplate, ReceivedEmail
)
from .monitor_router import router as monitor_router
from ..database.database import get_db
from ..auth.dependencies import get_current_user
from ..models.user import User
from ..tasks.email_tasks import send_email_task, send_hps_form_email_task
from ..celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/email", tags=["email"])

# Instancia global del servicio de email
email_service: EmailService = None


def get_email_service() -> EmailService:
    """Obtiene la instancia del servicio de email"""
    global email_service
    if email_service is None:
        # Cargar configuración desde variables de entorno
        email_service = EmailService(
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USER", "aicoxidi@gmail.com"),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            imap_host=os.getenv("IMAP_HOST", "imap.gmail.com"),
            imap_port=int(os.getenv("IMAP_PORT", "993")),
            imap_username=os.getenv("IMAP_USER", "aicoxidi@gmail.com"),
            imap_password=os.getenv("IMAP_PASSWORD", ""),
            from_name=os.getenv("SMTP_FROM_NAME", "HPS System"),
            reply_to=os.getenv("SMTP_REPLY_TO", "aicoxidi@gmail.com")
        )
    return email_service


@router.post("/send", response_model=EmailResponse)
async def send_email(
    request: SendEmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: EmailService = Depends(get_email_service)
):
    """
    Envía un correo electrónico usando un template
    
    Args:
        request: Datos del correo a enviar
        background_tasks: Tareas en segundo plano
        db: Sesión de base de datos
        current_user: Usuario actual autenticado
        service: Servicio de email
        
    Returns:
        Response con el resultado del envío
    """
    try:
        # Verificar permisos (solo admin puede enviar correos)
        if current_user.role.name not in ["admin", "team_leader", "team_lead"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para enviar correos"
            )
        
        # Enviar correo
        response = service.send_email_with_template(request, db)
        
        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=response.message
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint send_email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.post("/send-confirmation/{hps_request_id}", response_model=EmailResponse)
async def send_confirmation_email(
    hps_request_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: EmailService = Depends(get_email_service)
):
    """
    Envía correo de confirmación de solicitud HPS
    
    Args:
        hps_request_id: ID de la solicitud HPS
        background_tasks: Tareas en segundo plano
        db: Sesión de base de datos
        current_user: Usuario actual autenticado
        service: Servicio de email
        
    Returns:
        Response con el resultado del envío
    """
    try:
        # Verificar permisos
        if current_user.role.name not in ["admin", "team_leader", "team_lead"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para enviar correos"
            )
        
        # Enviar correo de confirmación
        response = service.send_confirmation_email(hps_request_id, db)
        
        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=response.message
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint send_confirmation_email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.post("/send-status-update/{hps_request_id}", response_model=EmailResponse)
async def send_status_update_email(
    hps_request_id: int,
    new_status: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: EmailService = Depends(get_email_service)
):
    """
    Envía correo de actualización de estado
    
    Args:
        hps_request_id: ID de la solicitud HPS
        new_status: Nuevo estado de la solicitud
        background_tasks: Tareas en segundo plano
        db: Sesión de base de datos
        current_user: Usuario actual autenticado
        service: Servicio de email
        
    Returns:
        Response con el resultado del envío
    """
    try:
        # Verificar permisos
        if current_user.role.name not in ["admin", "team_leader", "team_lead"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para enviar correos"
            )
        
        # Enviar correo de actualización
        response = service.send_status_update_email(hps_request_id, new_status, db)
        
        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=response.message
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint send_status_update_email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.get("/check-new-emails", response_model=List[ReceivedEmail])
async def check_new_emails(
    since_days: int = 1,
    current_user: User = Depends(get_current_user),
    service: EmailService = Depends(get_email_service)
):
    """
    Revisa correos nuevos recibidos
    
    Args:
        since_days: Días hacia atrás para buscar
        current_user: Usuario actual autenticado
        service: Servicio de email
        
    Returns:
        Lista de correos recibidos
    """
    try:
        # Verificar permisos
        if current_user.role.name not in ["admin", "team_leader", "team_lead"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para revisar correos"
            )
        
        # Obtener correos nuevos
        emails = service.check_new_emails(since_days)
        
        return emails
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint check_new_emails: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.post("/mark-as-read/{message_id}")
async def mark_email_as_read(
    message_id: str,
    current_user: User = Depends(get_current_user),
    service: EmailService = Depends(get_email_service)
):
    """
    Marca un correo como leído
    
    Args:
        message_id: ID del mensaje
        current_user: Usuario actual autenticado
        service: Servicio de email
        
    Returns:
        Resultado de la operación
    """
    try:
        # Verificar permisos
        if current_user.role.name not in ["admin", "team_leader", "team_lead"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para marcar correos"
            )
        
        # Marcar como leído
        success = service.mark_email_as_read(message_id)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Error marcando correo como leído"
            )
        
        return {"success": True, "message": "Correo marcado como leído"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint mark_email_as_read: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.get("/test-connections")
async def test_email_connections(
    current_user: User = Depends(get_current_user),
    service: EmailService = Depends(get_email_service)
):
    """
    Prueba las conexiones SMTP e IMAP
    
    Args:
        current_user: Usuario actual autenticado
        service: Servicio de email
        
    Returns:
        Resultado de las pruebas de conexión
    """
    try:
        # Verificar permisos
        if current_user.role.name not in ["admin", "team_leader", "team_lead"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para probar conexiones"
            )
        
        # Probar conexiones
        result = service.test_connections()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint test_email_connections: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.get("/logs")
async def get_email_logs(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: EmailService = Depends(get_email_service)
):
    """
    Obtiene logs de correos
    
    Args:
        limit: Límite de resultados
        offset: Offset para paginación
        db: Sesión de base de datos
        current_user: Usuario actual autenticado
        service: Servicio de email
        
    Returns:
        Lista de logs de correos
    """
    try:
        # Verificar permisos
        if current_user.role.name not in ["admin", "team_leader", "team_lead"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para ver logs de email"
            )
        
        # Obtener logs
        logs = service.get_email_logs(db, limit, offset)
        
        return logs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint get_email_logs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.get("/templates")
async def get_available_templates(
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene la lista de templates disponibles
    
    Args:
        current_user: Usuario actual autenticado
        
    Returns:
        Lista de templates disponibles
    """
    try:
        # Verificar permisos
        if current_user.role.name not in ["admin", "team_leader", "team_lead"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para ver templates"
            )
        
        # Obtener templates disponibles
        templates = [
            {
                "name": template.value,
                "description": EmailTemplate.__doc__ or f"Template {template.value}"
            }
            for template in EmailTemplate
        ]
        
        return templates
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint get_available_templates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


# ============================================================================
# ENDPOINTS ASÍNCRONOS CON CELERY
# ============================================================================

@router.post("/send-async", response_model=Dict[str, Any])
async def send_email_async(
    request: SendEmailRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Envía un correo electrónico de forma asíncrona usando Celery
    
    Args:
        request: Datos del correo a enviar
        current_user: Usuario actual autenticado
        
    Returns:
        ID de la tarea y estado
    """
    try:
        # Verificar permisos (solo admin puede enviar correos)
        if current_user.role.name not in ["admin", "team_leader", "team_lead"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para enviar correos"
            )
        
        # Preparar datos para la tarea
        email_data = {
            "to": request.to,
            "template": request.template,
            "template_data": request.template_data.dict(),
            "custom_subject": request.custom_subject,
            "custom_body": request.custom_body,
            "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "smtp_username": os.getenv("SMTP_USER"),
            "smtp_password": os.getenv("SMTP_PASSWORD"),
            "imap_host": os.getenv("IMAP_HOST", "imap.gmail.com"),
            "imap_port": int(os.getenv("IMAP_PORT", "993")),
            "imap_username": os.getenv("IMAP_USER"),
            "imap_password": os.getenv("IMAP_PASSWORD"),
            "from_name": os.getenv("SMTP_FROM_NAME", "HPS System"),
            "reply_to": os.getenv("SMTP_REPLY_TO")
        }
        
        # Encolar tarea
        task = send_email_task.delay(email_data)
        
        return {
            "success": True,
            "message": "Email encolado para envío asíncrono",
            "task_id": task.id,
            "status": "PENDING",
            "to": request.to
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint send_email_async: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.post("/send-hps-form-async", response_model=Dict[str, Any])
async def send_hps_form_email_async(
    email: str,
    form_url: str,
    user_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Envía un formulario HPS de forma asíncrona
    
    Args:
        email: Email del destinatario
        form_url: URL del formulario HPS
        user_name: Nombre del usuario
        current_user: Usuario actual autenticado
        
    Returns:
        ID de la tarea y estado
    """
    try:
        # Verificar permisos (solo admin puede enviar correos)
        if current_user.role.name not in ["admin", "team_leader", "team_lead"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para enviar correos"
            )
        
        # Preparar configuración SMTP
        smtp_config = {
            "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "smtp_username": os.getenv("SMTP_USER"),
            "smtp_password": os.getenv("SMTP_PASSWORD"),
            "imap_host": os.getenv("IMAP_HOST", "imap.gmail.com"),
            "imap_port": int(os.getenv("IMAP_PORT", "993")),
            "imap_username": os.getenv("IMAP_USER"),
            "imap_password": os.getenv("IMAP_PASSWORD"),
            "from_name": os.getenv("SMTP_FROM_NAME", "HPS System"),
            "reply_to": os.getenv("SMTP_REPLY_TO")
        }
        
        # Encolar tarea
        task = send_hps_form_email_task.delay(email, form_url, user_name, smtp_config)
        
        return {
            "success": True,
            "message": "Formulario HPS encolado para envío asíncrono",
            "task_id": task.id,
            "status": "PENDING",
            "email": email,
            "form_url": form_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint send_hps_form_email_async: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.get("/task-status/{task_id}", response_model=Dict[str, Any])
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el estado de una tarea asíncrona
    
    Args:
        task_id: ID de la tarea
        current_user: Usuario actual autenticado
        
    Returns:
        Estado de la tarea
    """
    try:
        # Verificar permisos
        if current_user.role.name not in ["admin", "team_leader", "team_lead"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para consultar tareas"
            )
        
        # Obtener estado de la tarea
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == "PENDING":
            response = {
                "task_id": task_id,
                "state": task_result.state,
                "status": "La tarea está esperando ser procesada"
            }
        elif task_result.state == "PROGRESS":
            response = {
                "task_id": task_id,
                "state": task_result.state,
                "current": task_result.info.get("current", 0),
                "total": task_result.info.get("total", 1),
                "status": task_result.info.get("status", ""),
                "progress": task_result.info.get("progress", 0)
            }
        elif task_result.state == "SUCCESS":
            response = {
                "task_id": task_id,
                "state": task_result.state,
                "result": task_result.result
            }
        else:  # FAILURE
            response = {
                "task_id": task_id,
                "state": task_result.state,
                "error": str(task_result.info)
            }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint get_task_status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


# Incluir router de monitorización
router.include_router(monitor_router)
