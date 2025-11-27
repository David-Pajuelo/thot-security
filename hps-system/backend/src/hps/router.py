"""
Router para el módulo HPS (Habilitación Personal de Seguridad)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
import logging

from src.database.database import get_db
from src.auth.dependencies import get_current_user
from src.models.user import User
from src.models.hps import HPSRequest
from . import schemas
from .service import HPSService
from src.email.service import EmailService
try:
    from src.services.government_email_processor import GovernmentEmailProcessor, DEFAULT_EMAIL_CONFIG
except ImportError:
    # Si PyPDF2 no está instalado, usar None como fallback
    GovernmentEmailProcessor = None
    DEFAULT_EMAIL_CONFIG = None

logger = logging.getLogger(__name__)

def get_request_type_display(request_type: str) -> str:
    """Convierte el tipo de solicitud interno a nombre legible"""
    type_mapping = {
        "new": "Solicitud HPS",
        "renewal": "Renovación HPS", 
        "transfer": "Traspaso HPS"
    }
    return type_mapping.get(request_type, request_type)

def format_date_spanish(date_value) -> str:
    """Convierte fecha de ISO (YYYY-MM-DD) a formato español (DD/MM/YYYY)"""
    if not date_value:
        return "N/A"
    try:
        if isinstance(date_value, str):
            from datetime import datetime
            date_obj = datetime.strptime(date_value, "%Y-%m-%d").date()
        else:
            date_obj = date_value
        return date_obj.strftime("%d/%m/%Y")
    except (ValueError, AttributeError, TypeError):
        return str(date_value) if date_value else "N/A"

router = APIRouter(tags=["HPS"])

@router.get("/test")
async def test_endpoint():
    """Endpoint de prueba para verificar que el router se carga"""
    return {"message": "Router HPS cargado correctamente", "status": "ok"}

@router.get("/test-auth")
async def test_auth_endpoint(
    current_user: User = Depends(get_current_user)
):
    """Endpoint de prueba para verificar autenticación"""
    return {
        "message": "Autenticación funcionando",
        "user_id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role.name
    }

@router.get("/team/{team_id}", response_model=List[schemas.HPSRequestResponse], summary="Obtener HPS del equipo")
async def get_team_hps(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener todas las solicitudes HPS de un equipo específico.
    Solo líderes de equipo pueden acceder a su propio equipo.
    """
    try:
        # Verificar permisos
        if current_user.role.name not in ['admin', 'team_leader', 'team_lead', 'jefe_seguridad', 'security_chief']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a equipos"
            )
        
        # Si es team_leader o team_lead, solo puede acceder a su propio equipo
        if current_user.role.name in ['team_leader', 'team_lead'] and str(current_user.team_id) != str(team_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes acceder a tu propio equipo"
            )
        
        # Obtener HPS del equipo
        hps_requests = db.query(HPSRequest).join(User, HPSRequest.user_id == User.id).filter(
            User.team_id == team_id
        ).all()
        
        return [schemas.HPSRequestResponse.from_hps_request(hps) for hps in hps_requests]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo HPS del equipo: {str(e)}"
        )

@router.get("/", response_model=schemas.HPSRequestList)
async def get_hps_list(
    page: int = 1,
    per_page: int = 10,
    status: Optional[str] = None,
    request_type: Optional[str] = None,
    hps_type: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener lista de solicitudes HPS"""
    try:
        from .schemas import HPSStatus, HPSRequestType
        
        # Convertir parámetros de string a enum si es necesario
        status_enum = None
        if status:
            try:
                status_enum = HPSStatus(status)
                print(f"DEBUG: status='{status}' -> status_enum={status_enum}")
            except ValueError as e:
                print(f"DEBUG: Error converting status '{status}': {e}")
                pass
        
        request_type_filter = None
        if request_type:
            try:
                request_type_filter = HPSRequestType(request_type)
            except ValueError:
                pass
        
        hps_list = HPSService.get_hps_requests(
            db, 
            page=page, 
            per_page=per_page, 
            current_user=current_user,
            status=status_enum,
            request_type=request_type_filter,
            user_id=user_id,
            hps_type=hps_type
        )
        
        return hps_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo lista de HPS: {str(e)}"
        )

@router.get("/stats", response_model=schemas.HPSStatsResponse)
async def get_hps_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas resumidas de HPS"""
    try:
        print(f"DEBUG: Usuario autenticado: {current_user.email}, Role: {current_user.role.name}")
        stats = HPSService.get_hps_stats(db, current_user)
        print(f"DEBUG: Estadísticas obtenidas: {stats.total_requests} solicitudes")
        return stats
    except Exception as e:
        print(f"DEBUG: Error en get_hps_stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )

@router.get("/{hps_id}", response_model=schemas.HPSRequestResponse)
async def get_hps_by_id(
    hps_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener solicitud HPS por ID"""
    try:
        hps = HPSService.get_hps_request_by_id(db, hps_id, current_user)
        if not hps:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud HPS no encontrada"
            )
        return hps
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo HPS: {str(e)}"
        )

@router.post("/", response_model=schemas.HPSRequestResponse)
async def create_hps(
    hps_data: schemas.HPSRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear nueva solicitud HPS"""
    try:
        hps = HPSService.create_hps_request(db, hps_data, current_user.id)
        return hps
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando HPS: {str(e)}"
        )

@router.post("/public", response_model=schemas.HPSRequestResponse)
async def create_hps_public(
    hps_data: schemas.HPSRequestCreate,
    token: str = Query(..., description="Token de autenticación"),
    hps_type: str = Query("solicitud", description="Tipo de solicitud HPS"),
    db: Session = Depends(get_db)
):
    """Crear nueva solicitud HPS usando token (público)"""
    print(f"🔍 DEBUG ENDPOINT: hps_type recibido: '{hps_type}'")
    try:
        # Validar token
        from src.hps.token_service import HPSTokenService
        token_info = HPSTokenService.get_token_info(db, token)
        
        if not token_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado"
            )
        
        # Crear solicitud HPS usando el email del token
        hps = HPSService.create_hps_request_with_token(
            db, 
            hps_data, 
            token_info["email"], 
            token_info["requested_by"],
            hps_type
        )
        
        # Si se creó un nuevo usuario, enviar email con credenciales usando Celery
        if hps.user_created and hps.temp_password:
            try:
                from src.tasks.email_tasks import send_email_task
                
                # Preparar datos para el template
                template_data = {
                    "user_name": f"{hps_data.first_name} {hps_data.first_last_name}".strip(),
                    "user_email": token_info["email"],
                    "additional_data": {
                        "temp_password": hps.temp_password,
                        "login_url": "http://localhost:3000/login"
                    }
                }
                
                # Enviar email de credenciales de forma asíncrona
                from src.config.settings import settings
                
                email_data = {
                    "to": token_info["email"],
                    "template": "user_credentials",
                    "template_data": template_data,
                    # Usar configuración del sistema desde variables de entorno
                    "smtp_host": settings.SMTP_HOST,
                    "smtp_port": settings.SMTP_PORT,
                    "smtp_username": settings.SMTP_USER,
                    "smtp_password": settings.SMTP_PASSWORD,
                    "imap_host": settings.IMAP_HOST,
                    "imap_port": settings.IMAP_PORT,
                    "imap_username": settings.IMAP_USER,
                    "imap_password": settings.IMAP_PASSWORD,
                    "from_name": settings.SMTP_FROM_NAME,
                    "reply_to": settings.SMTP_REPLY_TO
                }
                task = send_email_task.delay(email_data)
                logger.info(f"Email de credenciales encolado para envío asíncrono a {token_info['email']} (Task ID: {task.id})")
                
            except Exception as e:
                logger.error(f"Error encolando email de credenciales a {token_info['email']}: {e}")
                # No fallar la creación del HPS por un error de email
        
        return hps
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando HPS: {str(e)}"
        )

@router.put("/{hps_id}", response_model=schemas.HPSRequestResponse)
async def update_hps(
    hps_id: str,
    hps_data: schemas.HPSRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar solicitud HPS"""
    try:
        hps = HPSService.update_hps_request(db, hps_id, hps_data, current_user)
        return hps
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando HPS: {str(e)}"
        )

@router.delete("/{hps_id}")
async def delete_hps(
    hps_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar solicitud HPS"""
    try:
        success = HPSService.delete_hps_request(db, hps_id, current_user)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud HPS no encontrada"
            )
        return {"message": "Solicitud HPS eliminada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando HPS: {str(e)}"
        )

@router.get("/pending/list", response_model=List[schemas.HPSRequestResponse])
async def get_pending_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener lista de solicitudes HPS pendientes"""
    try:
        pending_requests = HPSService.get_pending_requests(db, current_user)
        return pending_requests
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo solicitudes pendientes: {str(e)}"
        )

@router.get("/submitted/list", response_model=List[schemas.HPSRequestResponse])
async def get_submitted_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener lista de solicitudes HPS enviadas"""
    try:
        submitted_requests = HPSService.get_submitted_requests(db, current_user)
        return submitted_requests
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo solicitudes enviadas: {str(e)}"
        )

@router.post("/{hps_id}/approve", response_model=schemas.HPSRequestResponse)
async def approve_hps_request(
    hps_id: str,
    expires_at: Optional[date] = None,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aprobar una solicitud HPS"""
    try:
        hps = HPSService.approve_hps_request(db, hps_id, current_user, expires_at, notes)
        if not hps:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud HPS no encontrada"
            )
        
        # Enviar email de notificación
        try:
            from src.email.schemas import EmailTemplateData, SendEmailRequest, EmailTemplate
            from src.tasks.email_tasks import send_email_task
            import os
            
            # Obtener datos de la solicitud para el email
            from src.models.hps import HPSRequest
            hps_request = db.query(HPSRequest).filter(HPSRequest.id == hps_id).first()
            if hps_request:
                user_email = hps_request.user.email
                user_name = f"{hps_request.first_name} {hps_request.first_last_name}".strip()
                
                template_data = EmailTemplateData(
                    user_name=user_name,
                    user_email=user_email,
                    document_number=hps_request.document_number,
                    request_type=get_request_type_display(hps_request.request_type),
                    status="approved",
                    additional_data={
                        "expires_at": format_date_spanish(expires_at) if expires_at else None,
                        "notes": notes
                    }
                )
                
                email_request = SendEmailRequest(
                    to=user_email,
                    template=EmailTemplate.HPS_APPROVED,
                    template_data=template_data
                )
                
                # Preparar datos para la tarea de Celery
                email_task_data = {
                    "to": email_request.to,
                    "template": email_request.template,
                    "template_data": email_request.template_data.dict(),
                    "custom_subject": email_request.custom_subject,
                    "custom_body": email_request.custom_body,
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
                
                task = send_email_task.delay(email_task_data)
                logger.info(f"Email de aprobación para HPS {hps_id} encolado. Tarea ID: {task.id}")
        except Exception as email_error:
            # No fallar la operación si el email falla
            logger.warning(f"Error enviando email de aprobación: {str(email_error)}")
        
        return hps
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error aprobando HPS: {str(e)}"
        )

@router.post("/{hps_id}/reject", response_model=schemas.HPSRequestResponse)
async def reject_hps_request(
    hps_id: str,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rechazar una solicitud HPS"""
    try:
        hps = HPSService.reject_hps_request(db, hps_id, current_user, notes)
        if not hps:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud HPS no encontrada"
            )
        
        # Enviar email de notificación
        try:
            from src.email.schemas import EmailTemplateData, SendEmailRequest, EmailTemplate
            from src.tasks.email_tasks import send_email_task
            import os
            
            # Obtener datos de la solicitud para el email
            from src.models.hps import HPSRequest
            hps_request = db.query(HPSRequest).filter(HPSRequest.id == hps_id).first()
            if hps_request:
                user_email = hps_request.user.email
                user_name = f"{hps_request.first_name} {hps_request.first_last_name}".strip()
                
                template_data = EmailTemplateData(
                    user_name=user_name,
                    user_email=user_email,
                    document_number=hps_request.document_number,
                    request_type=get_request_type_display(hps_request.request_type),
                    status="rejected",
                    additional_data={
                        "rejection_reason": notes or "No especificado",
                        "notes": notes
                    }
                )
                
                email_request = SendEmailRequest(
                    to=user_email,
                    template=EmailTemplate.HPS_REJECTED,
                    template_data=template_data
                )
                
                # Preparar datos para la tarea de Celery
                email_task_data = {
                    "to": email_request.to,
                    "template": email_request.template,
                    "template_data": email_request.template_data.dict(),
                    "custom_subject": email_request.custom_subject,
                    "custom_body": email_request.custom_body,
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
                
                task = send_email_task.delay(email_task_data)
                logger.info(f"Email de rechazo para HPS {hps_id} encolado. Tarea ID: {task.id}")
        except Exception as email_error:
            # No fallar la operación si el email falla
            logger.warning(f"Error enviando email de rechazo: {str(email_error)}")
        
        return hps
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rechazando HPS: {str(e)}"
        )

@router.post("/{hps_id}/submit", response_model=schemas.HPSRequestResponse)
async def submit_hps_request(
    hps_id: str,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marcar una solicitud HPS como enviada"""
    try:
        hps = HPSService.submit_hps_request(db, hps_id, current_user, notes)
        if not hps:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud HPS no encontrada"
            )
        return hps
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enviando HPS: {str(e)}"
        )

# ===== ENDPOINTS PARA TRASLADOS HPS =====

@router.post("/transfers", response_model=schemas.HPSRequestResponse)
async def create_transfer_request(
    hps_data: schemas.HPSRequestCreate,
    template_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear una nueva solicitud de traslado HPS"""
    # Verificar permisos: solo admin y jefes de seguridad pueden crear traspasos
    if current_user.role.name not in ["admin", "jefe_seguridad", "jefe_seguridad_suplente"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores y jefes de seguridad pueden crear traspasos HPS"
        )
    
    try:
        hps = HPSService.create_transfer_request(db, hps_data, current_user.id, template_id, submitted_by_user=current_user)
        return hps
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando traslado: {str(e)}"
        )

@router.get("/transfers", response_model=schemas.HPSRequestList)
async def get_transfer_requests(
    page: int = 1,
    per_page: int = 10,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener lista de solicitudes de traslado"""
    try:
        from .schemas import HPSStatus
        status_filter = None
        if status:
            try:
                status_filter = HPSStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Estado inválido: {status}"
                )
        
        hps_list = HPSService.get_transfer_requests(
            db, 
            current_user, 
            page=page, 
            per_page=per_page, 
            status=status_filter
        )
        return hps_list
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo traslados: {str(e)}"
        )

@router.post("/{hps_id}/upload-filled-pdf", response_model=schemas.HPSRequestResponse)
async def upload_filled_pdf(
    hps_id: str,
    pdf_file: bytes,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Subir PDF rellenado por el empleado"""
    try:
        hps = HPSService.upload_filled_pdf(db, hps_id, pdf_file, current_user)
        if not hps:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud HPS no encontrada"
            )
        return hps
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error subiendo PDF: {str(e)}"
        )

@router.post("/{hps_id}/upload-response-pdf", response_model=schemas.HPSRequestResponse)
async def upload_response_pdf(
    hps_id: str,
    pdf_file: bytes,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Subir PDF de respuesta oficial (solo admin)"""
    try:
        hps = HPSService.upload_response_pdf(db, hps_id, pdf_file, current_user)
        if not hps:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud HPS no encontrada"
            )
        return hps
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error subiendo PDF de respuesta: {str(e)}"
        )


@router.get("/{hps_id}/filled-pdf")
async def get_filled_pdf(
    hps_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Descargar PDF rellenado de una solicitud HPS"""
    try:
        from src.models.hps import HPSRequest
        from fastapi.responses import StreamingResponse
        import io
        
        hps_request = db.query(HPSRequest).filter(HPSRequest.id == hps_id).first()
        if not hps_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud HPS no encontrada"
            )
        
        if not hps_request.filled_pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay PDF rellenado para esta solicitud"
            )
        
        # Generar nombre del archivo basado en los datos del usuario
        user_name = f"{hps_request.first_name} {hps_request.first_last_name}".strip()
        if hps_request.second_last_name:
            user_name += f" {hps_request.second_last_name}"
        
        # Limpiar caracteres no válidos para nombres de archivo
        import re
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', user_name)
        filename = f"{safe_name} - Traslado HPS.pdf"
        
        return StreamingResponse(
            io.BytesIO(hps_request.filled_pdf),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error descargando PDF: {str(e)}"
        )


@router.get("/{hps_id}/response-pdf")
async def get_response_pdf(
    hps_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Descargar PDF de respuesta de una solicitud HPS"""
    try:
        from src.models.hps import HPSRequest
        from fastapi.responses import StreamingResponse
        import io
        
        hps_request = db.query(HPSRequest).filter(HPSRequest.id == hps_id).first()
        if not hps_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud HPS no encontrada"
            )
        
        if not hps_request.response_pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay PDF de respuesta para esta solicitud"
            )
        
        return StreamingResponse(
            io.BytesIO(hps_request.response_pdf),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=hps_response_{hps_id}.pdf"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error descargando PDF: {str(e)}"
        )

@router.post("/{hps_id}/edit-filled-pdf")
async def edit_filled_pdf(
    hps_id: str,
    field_updates: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Editar campos específicos del PDF rellenado (solo para traslados pendientes)"""
    try:
        from src.models.hps import HPSRequest
        from src.hps.schemas import HPSStatus
        from src.hps.pdf_service import PDFService
        from sqlalchemy.orm import joinedload
        
        # Buscar la solicitud
        hps_request = db.query(HPSRequest).filter(HPSRequest.id == hps_id).first()
        if not hps_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud HPS no encontrada"
            )
        
        # Verificar que es un traslado
        if hps_request.type != 'traslado':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden editar PDFs de solicitudes de traslado"
            )
        
        # Verificar que está pendiente
        if hps_request.status != HPSStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden editar PDFs de solicitudes pendientes"
            )
        
        # Verificar que tiene PDF rellenado
        if not hps_request.filled_pdf:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay PDF rellenado para editar"
            )
        
        # Control de acceso
        if current_user.role.name == "admin":
            pass  # Admin puede editar cualquier PDF
        elif current_user.role.name == "team_leader":
            # Team leader puede editar PDFs de su equipo
            if hps_request.user.team_id != current_user.team_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para editar este PDF"
                )
        else:
            # Member solo puede editar su propio PDF
            if hps_request.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo puedes editar tu propio PDF"
                )
        
        # Editar el PDF con los campos actualizados
        updated_pdf = PDFService.edit_existing_pdf(hps_request.filled_pdf, field_updates)
        
        # Actualizar el PDF en la base de datos
        hps_request.filled_pdf = updated_pdf
        db.commit()
        db.refresh(hps_request)
        
        # Cargar relaciones para la respuesta
        hps_request = db.query(HPSRequest).options(
            joinedload(HPSRequest.user),
            joinedload(HPSRequest.submitted_by_user),
            joinedload(HPSRequest.approved_by_user),
            joinedload(HPSRequest.template)
        ).filter(HPSRequest.id == hps_request.id).first()
        
        return {"success": True, "message": "PDF actualizado correctamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error editando PDF: {str(e)}"
        )


@router.get("/{hps_id}/extract-pdf-fields")
async def extract_pdf_fields(
    hps_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Extraer campos del PDF rellenado usando PyMuPDF"""
    try:
        from src.models.hps import HPSRequest
        from src.hps.schemas import HPSStatus
        from src.hps.pdf_service import PDFService
        
        # Buscar la solicitud
        hps_request = db.query(HPSRequest).filter(HPSRequest.id == hps_id).first()
        if not hps_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud HPS no encontrada"
            )
        
        # Verificar que es un traslado
        if hps_request.type != 'traslado':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden extraer campos de PDFs de solicitudes de traslado"
            )
        
        # Verificar que tiene PDF rellenado
        if not hps_request.filled_pdf:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay PDF rellenado para extraer campos"
            )
        
        # Control de acceso
        if current_user.role.name == "admin":
            pass  # Admin puede extraer campos de cualquier PDF
        elif current_user.role.name == "team_leader":
            # Team leader puede extraer campos de PDFs de su equipo
            if hps_request.user.team_id != current_user.team_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para extraer campos de este PDF"
                )
        else:
            # Member solo puede extraer campos de su propio PDF
            if hps_request.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo puedes extraer campos de tu propio PDF"
                )
        
        # Extraer campos del PDF usando PyMuPDF
        extracted_fields = PDFService.extract_pdf_fields(hps_request.filled_pdf)
        
        return extracted_fields
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extrayendo campos del PDF: {str(e)}"
        )


@router.post("/government/process-emails", summary="Procesar emails del gobierno con PDFs de HPS")
async def process_government_emails(
    limit_emails: int = Query(10, ge=1, le=100, description="Número máximo de emails a procesar"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Procesar emails del gobierno buscando PDFs de HPS para actualización automática.
    
    Solo disponible para administradores.
    """
    try:
        # Verificar permisos de administrador
        if current_user.role.name != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los administradores pueden procesar emails del gobierno"
            )
        
        logger.info(f"Procesamiento de emails iniciado por admin: {current_user.email}")
        
        # Crear procesador de emails
        if GovernmentEmailProcessor is None or DEFAULT_EMAIL_CONFIG is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="El procesador de emails del gobierno no está disponible. PyPDF2 no está instalado."
            )
        processor = GovernmentEmailProcessor(DEFAULT_EMAIL_CONFIG)
        
        # Procesar emails
        results = processor.process_email_attachments(limit_emails=limit_emails)
        
        if 'error' in results:
            logger.error(f"Error procesando emails: {results['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error procesando emails: {results['error']}"
            )
        
        logger.info(f"Procesamiento completado: {results['pdfs_processed']} PDFs procesados")
        
        return {
            "success": True,
            "message": "Procesamiento de emails completado",
            "results": {
                "total_emails_checked": results['total_emails_checked'],
                "government_emails_found": results['government_emails_found'],
                "pdfs_processed": results['pdfs_processed'],
                "records_updated": results['records_updated'],
                "processed_files": [
                    {
                        "filename": file_info['filename'],
                        "type": file_info['type'],
                        "empresa": file_info['empresa'],
                        "total_personas": file_info['total_personas']
                    }
                    for file_info in results.get('processed_files', [])
                ],
                "errors": results.get('errors', [])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado procesando emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )
