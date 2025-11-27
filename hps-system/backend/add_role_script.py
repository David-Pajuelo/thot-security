#!/usr/bin/env python3
"""Script para agregar el rol jefe_seguridad_suplente a la base de datos"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.database import engine
from sqlalchemy import text

def add_role():
    """Agregar el rol jefe_seguridad_suplente"""
    sql = """
    INSERT INTO roles (name, description, created_at, updated_at) 
    VALUES 
    ('jefe_seguridad_suplente', 'Jefe de Seguridad Suplente', NOW(), NOW())
    ON CONFLICT (name) DO NOTHING;
    """
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            conn.commit()
            print("✅ Rol 'jefe_seguridad_suplente' agregado correctamente")
            
            # Verificar que se agregó
            check_sql = "SELECT name, description FROM roles WHERE name = 'jefe_seguridad_suplente';"
            result = conn.execute(text(check_sql))
            row = result.fetchone()
            if row:
                print(f"✅ Verificación: Rol encontrado - {row[0]}: {row[1]}")
            else:
                print("⚠️ Advertencia: El rol no se encontró después de insertarlo")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    add_role()

