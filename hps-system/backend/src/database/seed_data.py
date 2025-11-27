"""
Script para poblar la base de datos con datos iniciales
Se ejecuta después de las migraciones para asegurar que haya datos básicos para funcionar
"""
import logging
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

def get_database_connection():
    """Obtener conexión a la base de datos"""
    try:
        # Construir URL de la base de datos
        db_url = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        return None

def check_data_exists(engine):
    """Verificar si ya existen datos en la base de datos"""
    try:
        with engine.connect() as conn:
            # Verificar si hay usuarios
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            
            # Verificar si hay roles
            result = conn.execute(text("SELECT COUNT(*) FROM roles"))
            role_count = result.scalar()
            
            # Verificar si hay equipos
            result = conn.execute(text("SELECT COUNT(*) FROM teams"))
            team_count = result.scalar()
            
            logger.info(f"Datos existentes - Usuarios: {user_count}, Roles: {role_count}, Equipos: {team_count}")
            
            return user_count > 0 and role_count > 0 and team_count > 0
            
    except Exception as e:
        logger.error(f"Error verificando datos existentes: {e}")
        return False

def seed_initial_data(engine):
    """Poblar la base de datos con datos iniciales"""
    try:
        with engine.connect() as conn:
            logger.info("🌱 Poblando base de datos con datos iniciales...")
            
            # Insertar roles básicos si no existen
            conn.execute(text("""
                INSERT INTO roles (name, description, permissions) VALUES
                ('admin', 'Administrador del sistema con acceso completo', '{"all": true, "view_chat_metrics": true}'),
                ('team_lead', 'Jefe de equipo con permisos de gestión de equipo', '{"team_management": true, "hps_requests": true, "user_view": true, "view_chat_metrics": true}'),
                ('member', 'Miembro del equipo con acceso básico', '{"hps_view": true, "profile_edit": true}')
                ON CONFLICT (name) DO NOTHING
            """))
            
            # Insertar equipo AICOX por defecto si no existe
            conn.execute(text("""
                INSERT INTO teams (id, name, description, is_active, created_at, updated_at) VALUES
                ('d8574c01-851f-4716-9ac9-bbda45469bdf', 'AICOX', 'Equipo genérico para usuarios sin equipo específico', true, now(), now())
                ON CONFLICT (id) DO NOTHING
            """))
            
            # Insertar usuario administrador por defecto si no existe
            conn.execute(text("""
                INSERT INTO users (id, email, password_hash, first_name, last_name, role_id, team_id, is_active, email_verified, created_at, updated_at) VALUES
                (gen_random_uuid(), 'admin@hps-system.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK8i', 'Admin', 'Sistema', 
                 (SELECT id FROM roles WHERE name = 'admin'), 
                 (SELECT id FROM teams WHERE name = 'AICOX'), 
                 true, true, now(), now())
                ON CONFLICT (email) DO NOTHING
            """))
            
            # Commit de los cambios
            conn.commit()
            
            logger.info("✅ Datos iniciales insertados correctamente")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error poblando datos iniciales: {e}")
        return False

def main():
    """Función principal"""
    logger.info("🌱 Iniciando población de datos iniciales...")
    
    # Obtener conexión a la base de datos
    engine = get_database_connection()
    if not engine:
        logger.error("❌ No se pudo conectar a la base de datos")
        return False
    
    # Verificar si ya existen datos
    if check_data_exists(engine):
        logger.info("✅ La base de datos ya contiene datos, no es necesario poblar")
        return True
    
    # Poblar datos iniciales
    if seed_initial_data(engine):
        logger.info("🎉 Base de datos poblada correctamente")
        return True
    else:
        logger.error("❌ Error poblando la base de datos")
        return False

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejecutar población de datos
    success = main()
    if not success:
        sys.exit(1)




