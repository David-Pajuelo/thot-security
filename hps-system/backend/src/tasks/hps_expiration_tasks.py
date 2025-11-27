"""
Tareas de Celery para automatización de HPS próximas a caducar
"""

from celery import Celery
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from src.database.database import get_db
from src.models.hps import HPSRequest
from src.models.user import User
from src.email.service import EmailService
from src.email.schemas import EmailTemplateData, EmailTemplate
import logging

logger = logging.getLogger(__name__)

# Obtener instancia de Celery
from src.celery_app import celery_app

@celery_app.task(bind=True, name='check_hps_expiration_task')
def check_hps_expiration_task(self):
    """
    Tarea para verificar HPS que están próximas a caducar (9 meses)
    y enviar correos de notificación UNA SOLA VEZ
    """
    try:
        logger.info("Iniciando verificación de HPS próximas a caducar (9 meses)...")
        
        # Verificar que estamos en horario laboral (L-V 08:00-19:00)
        now = datetime.now()
        if now.weekday() >= 5:  # Sábado = 5, Domingo = 6
            logger.info("No es día laboral, saltando verificación")
            return {"success": True, "message": "No es día laboral", "emails_sent": 0}
        
        if not (8 <= now.hour < 19):
            logger.info("No es horario laboral, saltando verificación")
            return {"success": True, "message": "No es horario laboral", "emails_sent": 0}
        
        # Calcular fecha límite (exactamente 9 meses desde hoy)
        today = date.today()
        nine_months_from_now = today + timedelta(days=9 * 30)  # 9 meses
        
        logger.info(f"Buscando HPS que caduquen en {nine_months_from_now}")
        
        # Obtener sesión de base de datos
        db = next(get_db())
        
        try:
            # Buscar HPS aprobadas que caduquen exactamente en 9 meses
            hps_near_expiration = db.query(HPSRequest).join(User).filter(
                HPSRequest.status == 'approved',
                HPSRequest.expires_at.isnot(None),
                HPSRequest.expires_at <= nine_months_from_now,
                HPSRequest.expires_at > today  # No incluir las ya caducadas
            ).all()
            
            logger.info(f"Encontradas {len(hps_near_expiration)} HPS próximas a caducar")
            
            if not hps_near_expiration:
                logger.info("No hay HPS próximas a caducar en los próximos 9 meses")
                return {
                    "success": True,
                    "message": "No hay HPS próximas a caducar",
                    "hps_found": 0,
                    "emails_sent": 0
                }
            
            # Inicializar servicio de email
            email_service = EmailService()
            emails_sent = 0
            
            for hps in hps_near_expiration:
                try:
                    # Calcular días restantes
                    days_remaining = (hps.expires_at - today).days
                    months_remaining = days_remaining // 30
                    
                    logger.info(f"Enviando notificación para HPS {hps.id} - {hps.first_name} {hps.first_last_name}")
                    logger.info(f"Caduca: {hps.expires_at} ({days_remaining} días, ~{months_remaining} meses)")
                    
                    # Generar enlace de renovación HPS
                    from src.hps.token_service import HPSTokenService
                    from src.hps.schemas import HPSTokenCreate
                    
                    # Crear token para renovación
                    token_data = HPSTokenCreate(
                        email=hps.email,
                        purpose="renovacion",
                        hours_valid=72  # 3 días de validez
                    )
                    
                    # Crear el token en la base de datos
                    token_response = HPSTokenService.create_token(
                        db=db,
                        token_data=token_data,
                        requested_by_id=str(hps.user_id),
                        base_url="http://localhost:3000"
                    )
                    
                    # Generar URL del formulario de renovación
                    renewal_url = token_response.url + "&type=renovacion"
                    
                    # Preparar datos para el template
                    template_data = EmailTemplateData(
                        user_name=f"{hps.first_name} {hps.first_last_name}",
                        user_email=hps.email,
                        document_number=hps.document_number,
                        request_type=hps.request_type,
                        status=hps.status,
                        hps_request_id=str(hps.id),
                        additional_data={
                            "expires_at": hps.expires_at.strftime("%d/%m/%Y"),
                            "days_remaining": days_remaining,
                            "months_remaining": months_remaining,
                            "security_clearance_level": hps.security_clearance_level,
                            "company_name": hps.company_name,
                            "renewal_url": renewal_url
                        }
                    )
                    
                    # Enviar email de notificación
                    result = email_service.send_email(
                        to=hps.email,
                        template=EmailTemplate.HPS_EXPIRATION_REMINDER,
                        template_data=template_data,
                        custom_subject=f"Recordatorio: Su HPS caduca en {months_remaining} meses"
                    )
                    
                    if result.get("success"):
                        emails_sent += 1
                        logger.info(f"Email enviado exitosamente a {hps.email}")
                    else:
                        logger.error(f"Error enviando email a {hps.email}: {result.get('error')}")
                        
                except Exception as e:
                    logger.error(f"Error procesando HPS {hps.id}: {str(e)}")
                    continue
            
            logger.info(f"Proceso completado: {emails_sent} emails enviados de {len(hps_near_expiration)} HPS")
            
            return {
                "success": True,
                "message": f"Verificación completada: {emails_sent} emails enviados",
                "hps_found": len(hps_near_expiration),
                "emails_sent": emails_sent,
                "expiration_date_limit": nine_months_from_now.isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error en verificación de HPS próximas a caducar: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "hps_found": 0,
            "emails_sent": 0
        }

@celery_app.task(bind=True, name='send_hps_expiration_reminder_task')
def send_hps_expiration_reminder_task(self, hps_id: str, user_email: str, days_remaining: int):
    """
    Tarea específica para enviar recordatorio de caducidad de HPS
    """
    try:
        logger.info(f"📧 Enviando recordatorio de caducidad para HPS {hps_id}")
        
        # Obtener datos de la HPS
        db = next(get_db())
        try:
            hps = db.query(HPSRequest).filter(HPSRequest.id == hps_id).first()
            
            if not hps:
                logger.error(f"❌ HPS {hps_id} no encontrada")
                return {"success": False, "error": "HPS no encontrada"}
            
            # Preparar datos para el template
            months_remaining = days_remaining // 30
            
            template_data = EmailTemplateData(
                user_name=f"{hps.first_name} {hps.first_last_name}",
                user_email=hps.email,
                document_number=hps.document_number,
                request_type=hps.request_type,
                status=hps.status,
                hps_request_id=str(hps.id),
                additional_data={
                    "expires_at": hps.expires_at.strftime("%d/%m/%Y") if hps.expires_at else "No especificada",
                    "days_remaining": days_remaining,
                    "months_remaining": months_remaining,
                    "security_clearance_level": hps.security_clearance_level,
                    "company_name": hps.company_name
                }
            )
            
            # Enviar email
            email_service = EmailService()
            result = email_service.send_email(
                to=user_email,
                template=EmailTemplate.REMINDER,
                template_data=template_data,
                custom_subject=f"Recordatorio: Su HPS caduca en {months_remaining} meses"
            )
            
            if result.get("success"):
                logger.info(f"✅ Recordatorio enviado exitosamente a {user_email}")
                return {"success": True, "message": "Recordatorio enviado exitosamente"}
            else:
                logger.error(f"❌ Error enviando recordatorio: {result.get('error')}")
                return {"success": False, "error": result.get('error')}
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Error enviando recordatorio de caducidad: {str(e)}")
        return {"success": False, "error": str(e)}
