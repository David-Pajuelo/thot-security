"""
Router para el sistema de monitorización de correos HPS
Endpoints para automatización de estados basada en correos del gobierno
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from .hps_monitor import HPSEmailMonitor
from .pdf_monitor import PDFEmailMonitor
from .service import EmailService
from ..database.database import get_db
from ..auth.dependencies import get_current_user
from ..models.user import User
from ..tasks.hps_monitor_tasks import hourly_hps_monitoring_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/email/monitor", tags=["email-monitor"])

# Instancia global del monitor
hps_monitor: HPSEmailMonitor = None


def get_hps_monitor() -> HPSEmailMonitor:
    """Obtiene la instancia del monitor HPS"""
    global hps_monitor
    if hps_monitor is None:
        # Obtener servicio de email
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
        hps_monitor = HPSEmailMonitor(email_service)
    return hps_monitor


@router.post("/start")
async def start_monitoring(
    background_tasks: BackgroundTasks,
    since_days: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    monitor: HPSEmailMonitor = Depends(get_hps_monitor)
):
    """
    Inicia el proceso de monitorización de correos HPS
    
    Args:
        since_days: Días hacia atrás para buscar correos (default: 1)
        db: Sesión de base de datos
        current_user: Usuario actual
        monitor: Instancia del monitor HPS
    
    Returns:
        Resultado del proceso de monitorización
    """
    try:
        # Verificar permisos (solo admin y jefe_seguridad)
        if current_user.role not in ["admin", "jefe_seguridad"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para iniciar la monitorización"
            )
        
        logger.info(f"Iniciando monitorización para usuario {current_user.email}")
        
        # Ejecutar monitorización
        result = monitor.monitor_emails(db, since_days)
        
        return {
            "success": result["success"],
            "message": "Monitorización completada",
            "emails_processed": result["emails_processed"],
            "status_updates": result["status_updates"],
            "errors": result["errors"]
        }
        
    except Exception as e:
        logger.error(f"Error iniciando monitorización: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error iniciando monitorización: {str(e)}"
        )


@router.post("/start-background")
async def start_background_monitoring(
    background_tasks: BackgroundTasks,
    since_days: int = 1,
    current_user: User = Depends(get_current_user),
    monitor: HPSEmailMonitor = Depends(get_hps_monitor)
):
    """
    Inicia la monitorización en segundo plano
    
    Args:
        since_days: Días hacia atrás para buscar correos
        background_tasks: Tareas en segundo plano
        current_user: Usuario actual
        monitor: Instancia del monitor HPS
    
    Returns:
        Confirmación de inicio en segundo plano
    """
    try:
        # Verificar permisos
        if current_user.role not in ["admin", "jefe_seguridad"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para iniciar la monitorización"
            )
        
        # Agregar tarea en segundo plano
        background_tasks.add_task(
            _background_monitoring_task,
            monitor,
            since_days
        )
        
        return {
            "success": True,
            "message": "Monitorización iniciada en segundo plano",
            "since_days": since_days
        }
        
    except Exception as e:
        logger.error(f"Error iniciando monitorización en segundo plano: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error iniciando monitorización: {str(e)}"
        )


@router.get("/stats")
async def get_monitoring_stats(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    monitor: HPSEmailMonitor = Depends(get_hps_monitor),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas del sistema de monitorización
    
    Args:
        days: Días hacia atrás para las estadísticas
        current_user: Usuario actual
        monitor: Instancia del monitor HPS
        db: Sesión de base de datos
    
    Returns:
        Estadísticas de monitorización
    """
    try:
        # Verificar permisos
        if current_user.role not in ["admin", "jefe_seguridad"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para ver estadísticas de monitorización"
            )
        
        stats = monitor.get_monitoring_stats(db, days)
        
        return {
            "success": stats["success"],
            "stats": stats,
            "message": "Estadísticas obtenidas correctamente"
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )


@router.get("/test-connection")
async def test_monitoring_connection(
    current_user: User = Depends(get_current_user),
    monitor: HPSEmailMonitor = Depends(get_hps_monitor)
):
    """
    Prueba la conexión del sistema de monitorización
    
    Args:
        current_user: Usuario actual
        monitor: Instancia del monitor HPS
    
    Returns:
        Resultado de la prueba de conexión
    """
    try:
        # Verificar permisos
        if current_user.role not in ["admin", "jefe_seguridad"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para probar la conexión"
            )
        
        # Probar conexiones
        connection_result = monitor.email_service.test_connections()
        
        return {
            "success": connection_result["overall_success"],
            "connections": connection_result,
            "message": "Prueba de conexión completada"
        }
        
    except Exception as e:
        logger.error(f"Error probando conexión: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error probando conexión: {str(e)}"
        )


async def _background_monitoring_task(monitor: HPSEmailMonitor, since_days: int):
    """
    Tarea en segundo plano para monitorización
    
    Args:
        monitor: Instancia del monitor HPS
        since_days: Días hacia atrás para buscar
    """
    try:
        logger.info(f"Iniciando monitorización en segundo plano (últimos {since_days} días)")
        
        # Obtener sesión de base de datos
        from ..database.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Ejecutar monitorización
            result = monitor.monitor_emails(db, since_days)
            
            logger.info(f"Monitorización en segundo plano completada: {result}")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error en monitorización en segundo plano: {str(e)}")


@router.post("/test-hourly")
async def test_hourly_monitoring(
    current_user: User = Depends(get_current_user)
):
    """
    Probar la nueva tarea horaria de monitorización HPS y PDFs
    Solo para administradores y jefes de seguridad
    """
    # Verificar permisos
    if current_user.role not in ["admin", "security_chief"]:
        raise HTTPException(
            status_code=403,
            detail="Solo administradores y jefes de seguridad pueden probar la monitorización"
        )
    
    try:
        logger.info("Iniciando prueba de monitorización horaria")
        
        # Ejecutar tarea horaria de forma síncrona para prueba
        result = hourly_hps_monitoring_task.apply()
        
        return {
            "success": True,
            "message": "Prueba de monitorización horaria completada",
            "result": result.result if hasattr(result, 'result') else result,
            "task_id": result.id if hasattr(result, 'id') else None
        }
        
    except Exception as e:
        logger.error(f"Error en prueba de monitorización horaria: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en prueba de monitorización: {str(e)}"
        )
