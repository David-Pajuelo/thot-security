#!/usr/bin/env python3
"""Script para verificar y corregir los tipos de plantillas"""
from src.database.database import engine
from sqlalchemy import text

def check_and_fix_templates():
    """Verificar y mostrar todas las plantillas"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, name, template_type, active, created_at 
            FROM hps_templates 
            ORDER BY created_at DESC
        """))
        rows = result.fetchall()
        
        print("📋 Plantillas existentes:")
        print("-" * 80)
        for row in rows:
            template_id, name, template_type, active, created_at = row
            template_type = template_type or "NULL"
            print(f"ID: {template_id}")
            print(f"  Nombre: {name}")
            print(f"  Tipo: {template_type}")
            print(f"  Activa: {active}")
            print(f"  Creada: {created_at}")
            print()
        
        # Verificar si hay plantillas sin tipo o con tipo incorrecto
        result = conn.execute(text("""
            SELECT id, name, template_type 
            FROM hps_templates 
            WHERE template_type IS NULL OR template_type = ''
        """))
        rows_without_type = result.fetchall()
        
        if rows_without_type:
            print("⚠️  Plantillas sin tipo asignado:")
            for row in rows_without_type:
                print(f"  - ID {row[0]}: {row[1]}")
            print("\n💡 Estas plantillas se asignarán automáticamente como 'jefe_seguridad'")
        else:
            print("✅ Todas las plantillas tienen tipo asignado")

if __name__ == "__main__":
    check_and_fix_templates()

