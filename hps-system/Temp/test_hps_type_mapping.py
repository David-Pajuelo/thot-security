#!/usr/bin/env python3
"""
Script de prueba para verificar el mapeo de tipos HPS
"""

import re

def test_hps_type_mapping():
    """Verificar que el mapeo de request_type a type esté implementado"""
    print("🔍 Verificando mapeo de tipos HPS...")
    
    try:
        with open('../backend/src/hps/service.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ No se encontró service.py")
        return False
    
    # Buscar el mapeo en create_hps_request
    pattern = r'# Mapear request_type a type.*?hps_type = hps_type'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("❌ No se encontró el mapeo de request_type a type")
        return False
    
    mapping_code = match.group(0)
    print("✅ Mapeo encontrado:")
    print(f"   {mapping_code}")
    
    # Verificar que incluya los casos correctos
    if 'transfer' in mapping_code and 'traslado' in mapping_code:
        print("✅ Mapeo incluye transfer -> traslado")
    else:
        print("❌ Mapeo no incluye transfer -> traslado")
        return False
    
    if 'new' in mapping_code and 'renewal' in mapping_code and 'solicitud' in mapping_code:
        print("✅ Mapeo incluye new/renewal -> solicitud")
    else:
        print("❌ Mapeo no incluye new/renewal -> solicitud")
        return False
    
    return True

def show_expected_mapping():
    """Mostrar el mapeo esperado"""
    print("\n📋 MAPEO ESPERADO DE TIPOS HPS:")
    print("=" * 50)
    print("🔄 FRONTEND → BACKEND:")
    print("  request_type: 'new'      → type: 'solicitud'")
    print("  request_type: 'renewal'  → type: 'solicitud'")
    print("  request_type: 'transfer' → type: 'traslado'")
    print("")
    print("📊 CAMPOS EN LA BASE DE DATOS:")
    print("  request_type: 'new', 'renewal', 'transfer'")
    print("  type: 'solicitud', 'traslado'")
    print("")
    print("🎯 RESULTADO ESPERADO:")
    print("  ✅ Las HPS creadas tendrán el campo 'type' correcto")
    print("  ✅ No habrá HPS sin tipo definido")
    print("  ✅ Los filtros por tipo funcionarán correctamente")

def show_problem_explanation():
    """Explicar el problema encontrado"""
    print("\n🐛 PROBLEMA IDENTIFICADO:")
    print("=" * 50)
    print("1. FLUJO ANTERIOR (INCORRECTO):")
    print("   Frontend envía: request_type = 'transfer'")
    print("   Backend crea HPS con:")
    print("   - request_type = 'transfer' ✅")
    print("   - type = 'solicitud' (valor por defecto) ❌")
    print("")
    print("2. FLUJO CORREGIDO:")
    print("   Frontend envía: request_type = 'transfer'")
    print("   Backend mapea: transfer → traslado")
    print("   Backend crea HPS con:")
    print("   - request_type = 'transfer' ✅")
    print("   - type = 'traslado' ✅")
    print("")
    print("3. CAUSA DEL PROBLEMA:")
    print("   - La función create_hps_request no mapeaba request_type a type")
    print("   - Solo se asignaba request_type, type quedaba con valor por defecto")
    print("   - create_hps_request_with_token SÍ tenía el mapeo correcto")

def main():
    """Función principal de verificación"""
    print("🔧 VERIFICACIÓN DE MAPEO DE TIPOS HPS")
    print("=" * 70)
    
    # Verificar mapeo
    mapping_ok = test_hps_type_mapping()
    
    # Mostrar mapeo esperado
    show_expected_mapping()
    
    # Explicar problema
    show_problem_explanation()
    
    # Resumen
    print("\n" + "=" * 70)
    print("📊 RESUMEN:")
    if mapping_ok:
        print("✅ El mapeo de tipos HPS está implementado correctamente")
        print("   Las nuevas HPS creadas tendrán el campo 'type' correcto")
        print("   Las HPS existentes con tipo incorrecto necesitan migración")
    else:
        print("❌ El mapeo de tipos HPS no está implementado correctamente")
    
    return mapping_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
