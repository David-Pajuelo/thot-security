#!/usr/bin/env python3
"""Script para agregar la columna template_type a hps_templates"""
from src.database.database import engine
from sqlalchemy import text

def add_template_type_column():
    """Agregar columna template_type si no existe"""
    with engine.connect() as conn:
        try:
            # Agregar columna si no existe
            conn.execute(text("""
                ALTER TABLE hps_templates 
                ADD COLUMN IF NOT EXISTS template_type VARCHAR(50) NOT NULL DEFAULT 'jefe_seguridad'
            """))
            
            # Crear índice si no existe
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_hps_templates_template_type 
                ON hps_templates(template_type)
            """))
            
            # Actualizar plantillas existentes
            conn.execute(text("""
                UPDATE hps_templates 
                SET template_type = 'jefe_seguridad' 
                WHERE template_type IS NULL OR template_type = ''
            """))
            
            conn.commit()
            print("✅ Columna template_type agregada exitosamente")
            
            # Verificar que se agregó
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'hps_templates' 
                AND column_name = 'template_type'
            """))
            if result.rowcount > 0:
                print("✅ Verificación: La columna template_type existe")
            else:
                print("❌ Error: La columna no se creó correctamente")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    add_template_type_column()

