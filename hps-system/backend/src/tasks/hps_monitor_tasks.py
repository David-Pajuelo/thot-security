"""
Tareas automáticas para monitorización de correos HPS
Sistema de ejecución periódica para automatización de estados
"""

import logging
from typing import Dict, Any
from celery import Celery
from sqlalchemy.orm import Session

from ..email.hps_monitor import HPSEmailMonitor
from ..email.service import EmailService
from ..database.database import SessionLocal

logger = logging.getLogger(__name__)

# Instancia de Celery (usar la misma del sistema)
from ..celery_app import celery_app


@celery_app.task(bind=True, name="hps_monitor.monitor_emails")
def monitor_hps_emails_task(self, since_days: int = 1) -> Dict[str, Any]:
    """
    Tarea Celery para monitorización automática de correos HPS
    
    Args:
        since_days: Días hacia atrás para buscar correos
        
    Returns:
        Dict con resultados del procesamiento
    """
    try:
        logger.info(f"Iniciando tarea de monitorización HPS (últimos {since_days} días)")
        
        # Crear servicio de email (TEMPORAL - usar credenciales compartidas)
        email_service = EmailService(
            smtp_host="smtp.gmail.com",  # TEMPORAL - cambiar por credenciales definitivas
            smtp_port=587,
            smtp_username="aicoxidi@gmail.com",  # TEMPORAL
            smtp_password="",  # TEMPORAL - usar variables de entorno
            imap_host="imap.gmail.com",  # TEMPORAL
            imap_port=993,
            imap_username="aicoxidi@gmail.com",  # TEMPORAL
            imap_password="",  # TEMPORAL - usar variables de entorno
            from_name="HPS System",
            reply_to="aicoxidi@gmail.com"  # TEMPORAL
        )
        
        # Crear monitor
        monitor = HPSEmailMonitor(email_service)
        
        # Obtener sesión de base de datos
        db = SessionLocal()
        
        try:
            # Ejecutar monitorización
            result = monitor.monitor_emails(db, since_days)
            
            logger.info(f"Monitorización completada: {result}")
            
            return {
                "success": True,
                "task_id": self.request.id,
                "result": result,
                "message": "Monitorización completada exitosamente"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error en tarea de monitorización HPS: {str(e)}")
        return {
            "success": False,
            "task_id": self.request.id,
            "error": str(e),
            "message": "Error en monitorización"
        }


@celery_app.task(bind=True, name="hps_monitor.hourly_check")
def hourly_hps_monitoring_task(self) -> Dict[str, Any]:
    """
    Tarea horaria para monitorización de correos HPS y procesamiento de PDFs
    Se ejecuta cada hora entre las 8:00 AM y las 6:00 PM
    
    Returns:
        Dict con resultados del procesamiento
    """
    try:
        logger.info("Iniciando monitorización horaria de correos HPS y PDFs")
        
        # Crear servicio de email (TEMPORAL - usar credenciales compartidas)
        email_service = EmailService(
            smtp_host="smtp.gmail.com",  # TEMPORAL - cambiar por credenciales definitivas
            smtp_port=587,
            smtp_username="aicoxidi@gmail.com",  # TEMPORAL
            smtp_password="",  # TEMPORAL - usar variables de entorno
            imap_host="imap.gmail.com",  # TEMPORAL
            imap_port=993,
            imap_username="aicoxidi@gmail.com",  # TEMPORAL
            imap_password="",  # TEMPORAL - usar variables de entorno
            from_name="HPS System",
            reply_to="aicoxidi@gmail.com"  # TEMPORAL
        )
        
        # Obtener sesión de base de datos
        db = SessionLocal()
        
        try:
            # 1. Monitorización de correos HPS (cambio de estados: pending → waiting_dps)
            from ..email.hps_monitor import HPSEmailMonitor
            hps_monitor = HPSEmailMonitor(email_service)
            hps_result = hps_monitor.monitor_emails(db, since_days=1)
            
            # 2. Procesamiento de PDFs adjuntos (concesiones/rechazos del gobierno)
            from ..email.pdf_monitor import PDFEmailMonitor
            pdf_monitor = PDFEmailMonitor(email_service)
            pdf_result = pdf_monitor.monitor_emails_with_pdfs(db, since_days=1)
            
            logger.info(f"Monitorización horaria completada - HPS: {hps_result}, PDFs: {pdf_result}")
            
            return {
                "success": True,
                "task_id": self.request.id,
                "hps_monitoring": hps_result,
                "pdf_processing": pdf_result,
                "message": "Monitorización horaria completada exitosamente"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error en tarea horaria de monitorización: {str(e)}")
        return {
            "success": False,
            "task_id": self.request.id,
            "error": str(e),
            "message": "Error en monitorización horaria"
        }


@celery_app.task(bind=True, name="hps_monitor.weekly_stats")
def weekly_hps_stats_task(self) -> Dict[str, Any]:
    """
    Tarea semanal para generar estadísticas de monitorización
    
    Returns:
        Dict con estadísticas
    """
    try:
        logger.info("Generando estadísticas semanales de monitorización HPS")
        
        # Crear servicio de email
        email_service = EmailService(
            smtp_host="smtp.gmail.com",  # TEMPORAL
            smtp_port=587,
            smtp_username="aicoxidi@gmail.com",  # TEMPORAL
            smtp_password="",  # TEMPORAL
            imap_host="imap.gmail.com",  # TEMPORAL
            imap_port=993,
            imap_username="aicoxidi@gmail.com",  # TEMPORAL
            imap_password="",  # TEMPORAL
            from_name="HPS System",
            reply_to="aicoxidi@gmail.com"  # TEMPORAL
        )
        
        # Crear monitor
        monitor = HPSEmailMonitor(email_service)
        
        # Obtener sesión de base de datos
        db = SessionLocal()
        
        try:
            # Obtener estadísticas de la última semana
            stats = monitor.get_monitoring_stats(db, days=7)
            
            logger.info(f"Estadísticas semanales: {stats}")
            
            return {
                "success": True,
                "task_id": self.request.id,
                "stats": stats,
                "message": "Estadísticas semanales generadas"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error generando estadísticas semanales: {str(e)}")
        return {
            "success": False,
            "task_id": self.request.id,
            "error": str(e),
            "message": "Error generando estadísticas"
        }


def schedule_hps_monitoring():
    """
    Programa las tareas automáticas de monitorización HPS
    """
    try:
        # Programar tarea horaria (8:00 AM - 6:00 PM)
        hourly_hps_monitoring_task.apply_async(
            countdown=60,  # Ejecutar en 1 minuto para prueba
            # Para producción usar: eta=datetime.now() + timedelta(hours=1)
        )
        
        # Programar estadísticas semanales los lunes a las 8:00 AM
        weekly_hps_stats_task.apply_async(
            countdown=120,  # Ejecutar en 2 minutos para prueba
            # Para producción usar: eta=next_monday_8am
        )
        
        logger.info("Tareas de monitorización HPS programadas (cada hora 8AM-6PM)")
        
    except Exception as e:
        logger.error(f"Error programando tareas de monitorización: {str(e)}")


# Configuración de tareas periódicas (usando Celery Beat)
from celery.schedules import crontab

# Configuración de tareas periódicas
CELERY_BEAT_SCHEDULE = {
    'hourly-hps-monitoring': {
        'task': 'hps_monitor.hourly_check',
        'schedule': crontab(hour='8-18', minute=0),  # Cada hora entre 8:00 AM y 6:00 PM
    },
    'weekly-hps-stats': {
        'task': 'hps_monitor.weekly_stats',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),  # Lunes a las 8:00 AM
    },
}
