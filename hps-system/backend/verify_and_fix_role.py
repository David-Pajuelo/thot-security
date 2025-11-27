#!/usr/bin/env python3
"""
Script para verificar y corregir el rol 'jefe_seguridad_suplente' en la base de datos
Ejecutar desde el directorio backend: python verify_and_fix_role.py
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.database import SessionLocal, engine
from sqlalchemy import text
from datetime import datetime

def verify_and_fix_role():
    """Verificar si el rol existe y crearlo si no existe"""
    db = SessionLocal()
    try:
        print("🔍 Verificando si el rol 'jefe_seguridad_suplente' existe...")
        
        # Verificar si el rol existe
        result = db.execute(text("""
            SELECT id, name, description 
            FROM roles 
            WHERE name = 'jefe_seguridad_suplente'
        """))
        role = result.fetchone()
        
        if role:
            print(f"✅ El rol 'jefe_seguridad_suplente' ya existe:")
            print(f"   ID: {role[0]}")
            print(f"   Nombre: {role[1]}")
            print(f"   Descripción: {role[2]}")
            return True
        else:
            print("⚠️ El rol 'jefe_seguridad_suplente' NO existe. Creándolo...")
            
            # Crear el rol
            db.execute(text("""
                INSERT INTO roles (name, description, created_at, updated_at) 
                VALUES 
                ('jefe_seguridad_suplente', 'Jefe de Seguridad Suplente', NOW(), NOW())
                ON CONFLICT (name) DO NOTHING
            """))
            db.commit()
            
            # Verificar que se creó
            result = db.execute(text("""
                SELECT id, name, description 
                FROM roles 
                WHERE name = 'jefe_seguridad_suplente'
            """))
            role = result.fetchone()
            
            if role:
                print(f"✅ Rol creado exitosamente:")
                print(f"   ID: {role[0]}")
                print(f"   Nombre: {role[1]}")
                print(f"   Descripción: {role[2]}")
                return True
            else:
                print("❌ Error: El rol no se pudo crear")
                return False
                
    except Exception as e:
        db.rollback()
        print(f"❌ Error al verificar/crear el rol: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def list_all_roles():
    """Listar todos los roles existentes"""
    db = SessionLocal()
    try:
        print("\n📋 Listando todos los roles existentes:")
        result = db.execute(text("""
            SELECT id, name, description, created_at 
            FROM roles 
            ORDER BY name
        """))
        roles = result.fetchall()
        
        if roles:
            for role in roles:
                print(f"   - {role[1]} (ID: {role[0]}, Desc: {role[2]})")
        else:
            print("   No hay roles en la base de datos")
            
    except Exception as e:
        print(f"❌ Error al listar roles: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Verificación y corrección del rol 'jefe_seguridad_suplente'")
    print("=" * 60)
    
    # Listar todos los roles primero
    list_all_roles()
    
    # Verificar y corregir
    success = verify_and_fix_role()
    
    # Listar todos los roles después
    if success:
        list_all_roles()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Proceso completado exitosamente")
        sys.exit(0)
    else:
        print("❌ Proceso completado con errores")
        sys.exit(1)

