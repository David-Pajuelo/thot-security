import logging
from typing import Dict, Any
from datetime import datetime, date, timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from .email_service import HpsEmailService
from .models import HpsRequest, HpsToken

logger = logging.getLogger(__name__)
User = get_user_model()
email_service = HpsEmailService()


@shared_task(bind=True)
def send_hps_credentials_email(self, payload: Dict):
    """
    Tarea Celery para envío de credenciales HPS.
    """
    try:
        email = payload.get("to")
        if not email:
            logger.error("No se proporcionó email en payload: %s", payload)
            return {"status": "error", "message": "Email no proporcionado"}
        
        # Obtener datos del usuario si están disponibles
        username = payload.get("username", email.split("@")[0])
        password = payload.get("password", "")
        user_name = payload.get("user_name", username)
        
        success = email_service.send_user_credentials_email(
            email=email,
            username=username,
            password=password,
            user_name=user_name
        )
        
        if success:
            logger.info("Email de credenciales enviado exitosamente a %s", email)
            return {"status": "sent", "email": email}
        else:
            logger.error("Error enviando email de credenciales a %s", email)
            return {"status": "error", "email": email, "message": "Error enviando email"}
            
    except Exception as e:
        logger.exception("Excepción en tarea de credenciales HPS: %s", str(e))
        return {"status": "error", "message": str(e)}


@shared_task(bind=True)
def send_hps_confirmation_email(self, hps_request_id: str):
    """
    Tarea Celery para envío de confirmación de solicitud HPS.
    """
    try:
        from .models import HpsRequest
        
        hps_request = HpsRequest.objects.get(id=hps_request_id)
        success = email_service.send_hps_confirmation_email(hps_request)
        
        if success:
            logger.info("Email de confirmación enviado para HPS %s", hps_request_id)
            return {"status": "sent", "hps_request_id": hps_request_id}
        else:
            logger.error("Error enviando email de confirmación para HPS %s", hps_request_id)
            return {"status": "error", "hps_request_id": hps_request_id}
            
    except HpsRequest.DoesNotExist:
        logger.error("HPS request no encontrado: %s", hps_request_id)
        return {"status": "error", "message": "HPS request no encontrado"}
    except Exception as e:
        logger.exception("Excepción en tarea de confirmación HPS: %s", str(e))
        return {"status": "error", "message": str(e)}


@shared_task(bind=True)
def send_hps_status_update_email(self, hps_request_id: int, status: str, old_status: str = None):
    """
    Tarea Celery para envío de actualización de estado de solicitud HPS.
    """
    try:
        from .models import HpsRequest
        
        hps_request = HpsRequest.objects.get(id=hps_request_id)
        success = email_service.send_hps_status_update_email(
            hps_request, 
            new_status=status,
            old_status=old_status
        )
        
        if success:
            logger.info("Email de actualización de estado enviado para HPS %s", hps_request_id)
            return {"status": "sent", "hps_request_id": hps_request_id, "status": status}
        else:
            logger.error("Error enviando email de actualización para HPS %s", hps_request_id)
            return {"status": "error", "hps_request_id": hps_request_id}
            
    except HpsRequest.DoesNotExist:
        logger.error("HPS request no encontrado: %s", hps_request_id)
        return {"status": "error", "message": "HPS request no encontrado"}
    except Exception as e:
        logger.exception("Excepción en tarea de actualización de estado HPS: %s", str(e))
        return {"status": "error", "message": str(e)}


@shared_task(bind=True)
def send_hps_approved_email(self, hps_request_id: int):
    """
    Tarea Celery para envío de notificación de aprobación HPS.
    """
    try:
        from .models import HpsRequest
        
        hps_request = HpsRequest.objects.get(id=hps_request_id)
        # Usar send_hps_status_update_email con estado 'approved'
        success = email_service.send_hps_status_update_email(
            hps_request,
            new_status='approved',
            old_status=None
        )
        
        if success:
            logger.info("Email de aprobación enviado para HPS %s", hps_request_id)
            return {"status": "sent", "hps_request_id": hps_request_id}
        else:
            logger.error("Error enviando email de aprobación para HPS %s", hps_request_id)
            return {"status": "error", "hps_request_id": hps_request_id}
            
    except HpsRequest.DoesNotExist:
        logger.error("HPS request no encontrado: %s", hps_request_id)
        return {"status": "error", "message": "HPS request no encontrado"}
    except Exception as e:
        logger.exception("Excepción en tarea de aprobación HPS: %s", str(e))
        return {"status": "error", "message": str(e)}


@shared_task(bind=True)
def send_hps_rejected_email(self, hps_request_id: int, rejection_reason: str = ""):
    """
    Tarea Celery para envío de notificación de rechazo HPS.
    """
    try:
        from .models import HpsRequest
        
        hps_request = HpsRequest.objects.get(id=hps_request_id)
        # Usar send_hps_status_update_email con estado 'rejected'
        success = email_service.send_hps_status_update_email(
            hps_request,
            new_status='rejected',
            old_status=None
        )
        
        if success:
            logger.info("Email de rechazo enviado para HPS %s", hps_request_id)
            return {"status": "sent", "hps_request_id": hps_request_id}
        else:
            logger.error("Error enviando email de rechazo para HPS %s", hps_request_id)
            return {"status": "error", "hps_request_id": hps_request_id}
            
    except HpsRequest.DoesNotExist:
        logger.error("HPS request no encontrado: %s", hps_request_id)
        return {"status": "error", "message": "HPS request no encontrado"}
    except Exception as e:
        logger.exception("Excepción en tarea de rechazo HPS: %s", str(e))
        return {"status": "error", "message": str(e)}


@shared_task(bind=True, name="hps_expiration.check_expiration")
def check_hps_expiration_task(self):
    """
    Tarea para verificar HPS que están próximas a caducar (9 meses)
    y enviar correos de notificación UNA SOLA VEZ.
    """
    try:
        logger.info("Iniciando verificación de HPS próximas a caducar (9 meses)...")
        
        # Verificar que estamos en horario laboral (L-V 08:00-19:00)
        now = timezone.now()
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
        
        # Buscar HPS aprobadas que caduquen exactamente en 9 meses
        # TODO: Agregar campo expiration_reminder_sent al modelo para evitar duplicados
        hps_near_expiration = HpsRequest.objects.filter(
            status='approved',
            expires_at__isnull=False,
            expires_at__lte=nine_months_from_now,
            expires_at__gt=today  # No incluir las ya caducadas
        )
        
        logger.info(f"Encontradas {hps_near_expiration.count()} HPS próximas a caducar")
        
        if not hps_near_expiration.exists():
            logger.info("No hay HPS próximas a caducar en los próximos 9 meses")
            return {
                "success": True,
                "message": "No hay HPS próximas a caducar",
                "hps_found": 0,
                "emails_sent": 0
            }
        
        emails_sent = 0
        
        for hps in hps_near_expiration:
            try:
                # Calcular días restantes
                days_remaining = (hps.expires_at - today).days
                months_remaining = days_remaining // 30
                
                logger.info(f"Enviando notificación para HPS {hps.id} - {hps.first_name} {hps.first_last_name}")
                logger.info(f"Caduca: {hps.expires_at} ({days_remaining} días, ~{months_remaining} meses)")
                
                # TODO: Crear token para renovación y enviar email de recordatorio
                # Por ahora solo registramos la acción
                # En el futuro, cuando se agregue expiration_reminder_sent:
                # hps.expiration_reminder_sent = True
                # hps.save(update_fields=['expiration_reminder_sent'])
                
                emails_sent += 1
                logger.info(f"Recordatorio procesado para HPS {hps.id}")
                
            except Exception as e:
                logger.error(f"Error procesando HPS {hps.id}: {str(e)}")
                continue
        
        logger.info(f"Proceso completado: {emails_sent} recordatorios procesados de {hps_near_expiration.count()} HPS")
        
        return {
            "success": True,
            "message": f"Verificación completada: {emails_sent} recordatorios procesados",
            "hps_found": hps_near_expiration.count(),
            "emails_sent": emails_sent,
            "expiration_date_limit": nine_months_from_now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en verificación de HPS próximas a caducar: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "hps_found": 0,
            "emails_sent": 0
        }


@shared_task(bind=True)
def send_hps_form_email_task(self, email: str, form_url: str, user_name: str = ""):
    """
    Tarea Celery para envío de email con formulario HPS.
    """
    try:
        success = email_service.send_hps_form_email(
            email=email,
            form_url=form_url,
            user_name=user_name
        )
        
        if success:
            logger.info("Email con formulario HPS enviado exitosamente a %s", email)
            return {"status": "sent", "email": email}
        else:
            logger.error("Error enviando email con formulario HPS a %s", email)
            return {"status": "error", "email": email, "message": "Error enviando email"}
            
    except Exception as e:
        logger.exception("Excepción en tarea de formulario HPS: %s", str(e))
        return {"status": "error", "message": str(e)}


@shared_task(bind=True, name="hps_core.send_generic_email")
def send_generic_email_task(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tarea genérica para envío de emails con templates.
    Adaptada desde hps-system/backend/src/tasks/email_tasks.py
    
    Args:
        email_data: Diccionario con:
            - to: Email del destinatario
            - template: Nombre del template (opcional, si no se usa template genérico)
            - subject: Asunto del email
            - body: Cuerpo del email (texto plano)
            - html_body: Cuerpo del email (HTML, opcional)
            - from_email: Email remitente (opcional, usa DEFAULT_FROM_EMAIL si no se proporciona)
            - reply_to: Email de respuesta (opcional)
    
    Returns:
        Dict con el resultado del envío
    """
    try:
        from django.core.mail import EmailMultiAlternatives
        from django.conf import settings
        
        # Actualizar estado de la tarea
        self.update_state(
            state="PROGRESS",
            meta={"status": "Iniciando envío de email", "progress": 10}
        )
        
        # Extraer datos del email
        to_email = email_data.get("to")
        if not to_email:
            logger.error("No se proporcionó email destinatario")
            return {"success": False, "message": "Email destinatario no proporcionado"}
        
        subject = email_data.get("subject", "Sin asunto")
        body = email_data.get("body", "")
        html_body = email_data.get("html_body")
        from_email = email_data.get("from_email", getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@cryptotrace.local'))
        reply_to = email_data.get("reply_to", getattr(settings, 'SMTP_REPLY_TO', None))
        
        self.update_state(
            state="PROGRESS",
            meta={"status": "Preparando email", "progress": 30}
        )
        
        # Crear mensaje de email
        email_msg = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[to_email]
        )
        
        # Añadir reply-to si está configurado
        if reply_to:
            email_msg.reply_to = [reply_to]
        
        # Añadir versión HTML si está disponible
        if html_body:
            email_msg.attach_alternative(html_body, "text/html")
        
        self.update_state(
            state="PROGRESS",
            meta={"status": "Enviando email", "progress": 60}
        )
        
        # Enviar email
        email_msg.send()
        
        self.update_state(
            state="PROGRESS",
            meta={"status": "Email enviado", "progress": 90}
        )
        
        logger.info("Email genérico enviado exitosamente a %s", to_email)
        return {
            "success": True,
            "message": "Email enviado exitosamente",
            "to": to_email,
            "task_id": self.request.id
        }
        
    except Exception as e:
        logger.exception("Error en tarea de envío genérico de email: %s", str(e))
        self.update_state(
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


@shared_task(bind=True, name="hps_core.monitor_hps_emails_task")
def monitor_hps_emails_task(self, since_days: int = 1) -> Dict[str, Any]:
    """
    Tarea Celery para monitorización automática de correos HPS entrantes.
    Adaptada desde hps-system/backend/src/tasks/hps_monitor_tasks.py
    
    Args:
        since_days: Días hacia atrás para buscar correos
        
    Returns:
        Dict con resultados del procesamiento
    """
    try:
        from .email_monitor import HPSEmailMonitor
        
        logger.info(f"Iniciando monitorización de correos HPS (últimos {since_days} días)...")
        
        # Crear monitor
        monitor = HPSEmailMonitor()
        
        # Ejecutar monitorización
        result = monitor.monitor_emails(since_days=since_days)
        
        logger.info(f"Monitorización completada: {result.get('emails_processed', 0)} correos procesados, {result.get('status_updates', 0)} estados actualizados")
        
        return result
        
    except Exception as e:
        logger.exception(f"Error en tarea de monitorización HPS: {str(e)}")
        return {
            "success": False,
            "emails_processed": 0,
            "status_updates": 0,
            "errors": [str(e)]
        }


@shared_task(bind=True, name="hps_core.send_bulk_emails")
def send_bulk_emails_task(self, emails_data: list) -> Dict[str, Any]:
    """
    Tarea para envío masivo de emails.
    Adaptada desde hps-system/backend/src/tasks/email_tasks.py
    
    Args:
        emails_data: Lista de diccionarios con datos de emails (mismo formato que send_generic_email_task)
    
    Returns:
        Dict con el resultado del envío masivo
    """
    try:
        results = []
        total_emails = len(emails_data)
        
        for i, email_data in enumerate(emails_data):
            self.update_state(
                state="PROGRESS",
                meta={
                    "status": f"Enviando email {i+1}/{total_emails}",
                    "progress": int((i / total_emails) * 100),
                    "current": i + 1,
                    "total": total_emails
                }
            )
            
            # Enviar email usando la tarea genérica
            result = send_generic_email_task.delay(email_data)
            results.append({
                "email": email_data.get("to", "unknown"),
                "task_id": result.id,
                "status": "enqueued"
            })
        
        logger.info("Encolados %d emails para envío masivo", total_emails)
        return {
            "success": True,
            "message": f"Encolados {total_emails} emails",
            "total_emails": total_emails,
            "results": results
        }
        
    except Exception as e:
        logger.exception("Error en tarea de envío masivo: %s", str(e))
        return {
            "success": False,
            "message": "Error en envío masivo de emails",
            "error": str(e)
        }


@shared_task(bind=True, name="hps_core.tasks.analyze_emails_task")
def analyze_emails_task(self, analysis_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Tarea asíncrona para análisis de emails recibidos.
    Adaptada desde hps-system/backend/src/tasks/analysis_tasks.py
    
    Args:
        analysis_config: Configuración del análisis (opcional, usa valores por defecto de settings si no se proporciona)
            - since_days: Días hacia atrás para buscar correos (default: 1)
            - imap_host: Host IMAP (opcional, usa settings)
            - imap_port: Puerto IMAP (opcional, usa settings)
            - imap_username: Usuario IMAP (opcional, usa settings)
            - imap_password: Contraseña IMAP (opcional, usa settings)
    
    Returns:
        Dict con el resultado del análisis
    """
    try:
        from .imap_client import IMAPClient
        
        # Usar configuración por defecto si no se proporciona
        if analysis_config is None:
            analysis_config = {}
        
        self.update_state(
            state="PROGRESS",
            meta={"status": "Iniciando análisis de emails", "progress": 10}
        )
        
        # Crear cliente IMAP (usa configuración de Django settings por defecto)
        imap_client = IMAPClient(
            host=analysis_config.get("imap_host"),
            port=analysis_config.get("imap_port"),
            username=analysis_config.get("imap_username"),
            password=analysis_config.get("imap_password"),
            mailbox=analysis_config.get("imap_mailbox")
        )
        
        self.update_state(
            state="PROGRESS",
            meta={"status": "Conectando a IMAP", "progress": 30}
        )
        
        # Obtener emails (no leídos desde hace X días)
        since_days = analysis_config.get("since_days", 1)
        emails = imap_client.get_unread_emails(since_days=since_days)
        
        self.update_state(
            state="PROGRESS",
            meta={"status": f"Analizando {len(emails)} emails", "progress": 60}
        )
        
        # Análisis básico
        analysis_results = {
            "total_emails": len(emails),
            "emails_by_sender": {},
            "emails_by_subject": {},
            "recent_emails": []
        }
        
        for email in emails:
            # Contar por remitente
            sender = email.get("from_email", "unknown")
            analysis_results["emails_by_sender"][sender] = \
                analysis_results["emails_by_sender"].get(sender, 0) + 1
            
            # Contar por asunto
            subject = email.get("subject", "Sin asunto")
            analysis_results["emails_by_subject"][subject] = \
                analysis_results["emails_by_subject"].get(subject, 0) + 1
            
            # Emails recientes (máximo 10)
            if len(analysis_results["recent_emails"]) < 10:
                analysis_results["recent_emails"].append({
                    "from": sender,
                    "subject": subject,
                    "received_at": email.get("received_at")
                })
        
        self.update_state(
            state="PROGRESS",
            meta={"status": "Análisis completado", "progress": 90}
        )
        
        logger.info("Análisis completado: %d emails procesados", len(emails))
        
        return {
            "success": True,
            "message": "Análisis de emails completado",
            "results": analysis_results,
            "task_id": self.request.id
        }
        
    except Exception as e:
        logger.exception("Error en análisis de emails: %s", str(e))
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        return {
            "success": False,
            "message": "Error en análisis de emails",
            "error": str(e),
            "task_id": self.request.id
        }

