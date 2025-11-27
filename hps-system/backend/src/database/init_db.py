"""
Script de inicialización automática de la base de datos
Se ejecuta al iniciar el backend para asegurar que todas las migraciones estén aplicadas
"""
import logging
import asyncio
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import time

logger = logging.getLogger(__name__)

def wait_for_database(db_url: str, max_retries: int = 30, delay: int = 2):
    """Esperar a que la base de datos esté disponible"""
    logger.info("🔄 Esperando a que la base de datos esté disponible...")
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ Base de datos disponible")
            return True
        except OperationalError as e:
            if attempt < max_retries - 1:
                logger.info(f"⏳ Intento {attempt + 1}/{max_retries}: Base de datos no disponible, reintentando en {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"❌ No se pudo conectar a la base de datos después de {max_retries} intentos")
                return False
    
    return False

def run_migrations():
    """Ejecutar todas las migraciones pendientes"""
    try:
        # Obtener la ruta del directorio de migraciones
        migrations_dir = Path(__file__).parent / "migrations"
        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", str(migrations_dir))
        
        # Obtener la URL de la base de datos desde variables de entorno
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            # Construir la URL desde variables individuales
            db_url = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        
        logger.info("🚀 Iniciando migraciones de base de datos...")
        
        # Ejecutar migraciones
        command.upgrade(alembic_cfg, "head")
        
        logger.info("✅ Todas las migraciones aplicadas correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando migraciones: {e}")
        return False

def init_database():
    """Función principal de inicialización"""
    logger.info("🔧 Inicializando base de datos del sistema HPS...")
    
    # Construir URL de la base de datos
    db_url = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    
    # Esperar a que la base de datos esté disponible
    if not wait_for_database(db_url):
        logger.error("❌ No se pudo conectar a la base de datos")
        return False
    
    # Ejecutar migraciones
    if not run_migrations():
        logger.error("❌ Error ejecutando migraciones")
        return False
    
    logger.info("🎉 Base de datos inicializada correctamente")
    return True

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejecutar inicialización
    success = init_database()
    if not success:
        sys.exit(1)









