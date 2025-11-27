#!/usr/bin/env python3
"""
Script de prueba para verificar que canManageUsers incluya jefes de seguridad
"""

import re

def test_can_manage_users_function():
    """Verificar que canManageUsers incluya jefe_seguridad"""
    print("🔍 Verificando función canManageUsers...")
    
    try:
        with open('../frontend/src/store/authStore.js', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ No se encontró authStore.js")
        return False
    
    # Buscar la función canManageUsers
    pattern = r'canManageUsers:\s*\(\)\s*=>\s*\{[^}]*\}'
    match = re.search(pattern, content)
    
    if not match:
        print("❌ No se encontró la función canManageUsers")
        return False
    
    function_code = match.group(0)
    print("✅ Función canManageUsers encontrada:")
    print(f"   {function_code}")
    
    # Verificar que incluya jefe_seguridad y security_chief
    if 'jefe_seguridad' in function_code and 'security_chief' in function_code:
        print("✅ La función incluye jefe_seguridad y security_chief")
        return True
    else:
        print("❌ La función no incluye jefe_seguridad o security_chief")
        return False

def show_expected_behavior():
    """Mostrar el comportamiento esperado"""
    print("\n📋 COMPORTAMIENTO ESPERADO:")
    print("=" * 50)
    print("🔧 ADMIN:")
    print("  ✅ canManageUsers(): true")
    print("  ✅ isSecurityChief(): false")
    print("  ✅ isAdmin(): true")
    print("")
    print("🛡️  JEFE DE SEGURIDAD:")
    print("  ✅ canManageUsers(): true  ← CORREGIDO")
    print("  ✅ isSecurityChief(): true")
    print("  ❌ isAdmin(): false")
    print("")
    print("👥 LÍDER DE EQUIPO:")
    print("  ✅ canManageUsers(): true")
    print("  ❌ isSecurityChief(): false")
    print("  ❌ isAdmin(): false")
    print("")
    print("👤 MIEMBRO:")
    print("  ❌ canManageUsers(): false")
    print("  ❌ isSecurityChief(): false")
    print("  ❌ isAdmin(): false")

def main():
    """Función principal de verificación"""
    print("🔧 VERIFICACIÓN DE CORRECCIÓN: canManageUsers")
    print("=" * 60)
    
    # Verificar función canManageUsers
    function_ok = test_can_manage_users_function()
    
    # Mostrar comportamiento esperado
    show_expected_behavior()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN:")
    if function_ok:
        print("✅ canManageUsers ahora incluye jefes de seguridad")
        print("   Los jefes de seguridad deberían poder acceder a:")
        print("   - Gestión de Usuarios")
        print("   - Estadísticas de usuarios en el dashboard")
    else:
        print("❌ La función canManageUsers no está corregida")
    
    return function_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
