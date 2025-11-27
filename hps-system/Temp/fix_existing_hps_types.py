#!/usr/bin/env python3
"""
Script para corregir los tipos de HPS existentes que tienen el campo 'type' incorrecto
"""

def show_migration_script():
    """Mostrar el script de migración SQL"""
    print("🔧 SCRIPT DE MIGRACIÓN PARA CORREGIR TIPOS HPS")
    print("=" * 70)
    
    print("\n📋 PROBLEMA IDENTIFICADO:")
    print("Las HPS existentes tienen el campo 'type' incorrecto:")
    print("- request_type = 'transfer' pero type = 'solicitud' (debería ser 'traslado')")
    print("- request_type = 'new'/'renewal' pero type = 'solicitud' (correcto)")
    
    print("\n🔧 SCRIPT SQL PARA CORREGIR:")
    print("=" * 50)
    print("-- Corregir tipos de HPS basándose en request_type")
    print("UPDATE hps_requests")
    print("SET type = 'traslado'")
    print("WHERE request_type = 'transfer' AND type = 'solicitud';")
    print("")
    print("-- Verificar que no hay HPS con request_type = 'transfer' y type = 'solicitud'")
    print("SELECT id, request_type, type, first_name, last_name")
    print("FROM hps_requests")
    print("WHERE request_type = 'transfer' AND type = 'solicitud';")
    print("")
    print("-- Verificar el resultado después de la corrección")
    print("SELECT request_type, type, COUNT(*) as count")
    print("FROM hps_requests")
    print("GROUP BY request_type, type")
    print("ORDER BY request_type, type;")
    
    print("\n🎯 RESULTADO ESPERADO DESPUÉS DE LA MIGRACIÓN:")
    print("=" * 60)
    print("request_type | type      | count")
    print("-------------|-----------|------")
    print("new          | solicitud | X")
    print("renewal      | solicitud | X")
    print("transfer     | traslado  | X")
    print("")
    print("❌ NO debería haber:")
    print("transfer     | solicitud | 0")

def show_verification_queries():
    """Mostrar consultas de verificación"""
    print("\n🔍 CONSULTAS DE VERIFICACIÓN:")
    print("=" * 50)
    print("1. HPS problemáticas (antes de corregir):")
    print("   SELECT id, request_type, type, first_name, last_name")
    print("   FROM hps_requests")
    print("   WHERE request_type = 'transfer' AND type = 'solicitud';")
    print("")
    print("2. HPS en estado 'waiting_dps' sin tipo correcto:")
    print("   SELECT id, request_type, type, status, first_name, last_name")
    print("   FROM hps_requests")
    print("   WHERE status = 'waiting_dps' AND request_type = 'transfer' AND type = 'solicitud';")
    print("")
    print("3. Resumen de tipos después de corrección:")
    print("   SELECT request_type, type, status, COUNT(*) as count")
    print("   FROM hps_requests")
    print("   GROUP BY request_type, type, status")
    print("   ORDER BY request_type, type, status;")

def show_prevention_measures():
    """Mostrar medidas de prevención"""
    print("\n🛡️  MEDIDAS DE PREVENCIÓN IMPLEMENTADAS:")
    print("=" * 60)
    print("✅ Backend corregido:")
    print("   - create_hps_request() ahora mapea request_type → type")
    print("   - create_hps_request_with_token() ya tenía el mapeo correcto")
    print("")
    print("✅ Mapeo implementado:")
    print("   - 'new'/'renewal' → 'solicitud'")
    print("   - 'transfer' → 'traslado'")
    print("")
    print("✅ Validación en frontend:")
    print("   - HPSForm mapea correctamente hpsType → request_type")
    print("   - HPSList muestra correctamente los tipos")

def main():
    """Función principal"""
    print("🔧 CORRECCIÓN DE TIPOS HPS EXISTENTES")
    print("=" * 70)
    
    show_migration_script()
    show_verification_queries()
    show_prevention_measures()
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN:")
    print("1. ✅ Problema identificado: mapeo faltante en create_hps_request()")
    print("2. ✅ Solución implementada: mapeo agregado al backend")
    print("3. ⚠️  Migración necesaria: corregir HPS existentes con SQL")
    print("4. ✅ Prevención: nuevas HPS tendrán el tipo correcto")
    
    print("\n🚀 PRÓXIMOS PASOS:")
    print("1. Ejecutar el script SQL de migración")
    print("2. Verificar que no hay HPS problemáticas")
    print("3. Reiniciar el backend")
    print("4. Probar creación de nuevas HPS")

if __name__ == "__main__":
    main()
