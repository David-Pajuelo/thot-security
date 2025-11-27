"""
Comando para verificar HPS próximas a caducar
Ejecuta la tarea de verificación de HPS que están próximas a caducar (9 meses)
"""

import asyncio
import sys
import os
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from src.database.database import get_db
from src.models.hps import HPSRequest
from src.models.user import User
from src.tasks.hps_expiration_tasks import check_hps_expiration_task
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_hps_expiration_command():
    """
    Comando para verificar HPS próximas a caducar
    """
    try:
        logger.info("🔍 Iniciando verificación de HPS próximas a caducar...")
        
        # Ejecutar la tarea de verificación
        result = check_hps_expiration_task()
        
        if result.get("success"):
            logger.info("✅ Verificación completada exitosamente")
            logger.info(f"📊 HPS encontradas: {result.get('hps_found', 0)}")
            logger.info(f"📧 Emails enviados: {result.get('emails_sent', 0)}")
            
            if result.get('expiration_date_limit'):
                logger.info(f"📅 Fecha límite de búsqueda: {result.get('expiration_date_limit')}")
        else:
            logger.error(f"❌ Error en la verificación: {result.get('error')}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando comando: {str(e)}")
        return False

def check_hps_expiration_manual():
    """
    Verificación manual sin usar Celery (para testing)
    """
    try:
        logger.info("🔍 Iniciando verificación manual de HPS próximas a caducar...")
        
        # Calcular fecha límite (9 meses desde hoy)
        today = date.today()
        nine_months_from_now = today + timedelta(days=9 * 30)  # Aproximadamente 9 meses
        
        logger.info(f"📅 Buscando HPS que caduquen antes del {nine_months_from_now}")
        
        # Obtener sesión de base de datos
        db = next(get_db())
        
        try:
            # Buscar HPS aprobadas que caduquen en los próximos 9 meses
            hps_near_expiration = db.query(HPSRequest).join(User).filter(
                HPSRequest.status == 'approved',
                HPSRequest.expires_at.isnot(None),
                HPSRequest.expires_at <= nine_months_from_now,
                HPSRequest.expires_at > today  # No incluir las ya caducadas
            ).all()
            
            logger.info(f"📊 Encontradas {len(hps_near_expiration)} HPS próximas a caducar")
            
            if not hps_near_expiration:
                logger.info("✅ No hay HPS próximas a caducar en los próximos 9 meses")
                return True
            
            # Mostrar información de cada HPS
            for hps in hps_near_expiration:
                days_remaining = (hps.expires_at - today).days
                months_remaining = days_remaining // 30
                
                logger.info(f"📋 HPS {hps.id}:")
                logger.info(f"   👤 Usuario: {hps.first_name} {hps.first_last_name}")
                logger.info(f"   📧 Email: {hps.email}")
                logger.info(f"   📅 Caduca: {hps.expires_at} ({days_remaining} días, ~{months_remaining} meses)")
                logger.info(f"   🏢 Empresa: {hps.company_name or 'No especificada'}")
                logger.info(f"   🔒 Nivel: {hps.security_clearance_level or 'No especificado'}")
                logger.info("")
            
            logger.info(f"📧 Se enviarían {len(hps_near_expiration)} emails de recordatorio")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Error en verificación manual: {str(e)}")
        return False

if __name__ == "__main__":
    # Verificar argumentos
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        # Ejecutar verificación manual
        success = check_hps_expiration_manual()
    else:
        # Ejecutar verificación con Celery
        success = check_hps_expiration_command()
    
    if success:
        logger.info("✅ Comando ejecutado exitosamente")
        sys.exit(0)
    else:
        logger.error("❌ Comando falló")
        sys.exit(1)
