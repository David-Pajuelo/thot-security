#!/usr/bin/env python3
"""
Script para configurar la automatización de recordatorios de HPS próximas a caducar
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta

def setup_cron_job():
    """Configura el cron job para verificación automática en horario laboral"""
    print("Configurando automatizacion de recordatorios HPS...")
    
    # Directorio del proyecto
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(project_dir, "src", "commands", "check_hps_expiration.py")
    
    # Verificar que el script existe
    if not os.path.exists(script_path):
        print(f"ERROR: No se encontro el script {script_path}")
        return False
    
    # Crear entrada de cron (L-V a las 9:00 AM)
    cron_entry = f"0 9 * * 1-5 cd {project_dir} && python {script_path} >> /var/log/hps_expiration_check.log 2>&1"
    
    try:
        # Obtener crontab actual
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_crontab = result.stdout if result.returncode == 0 else ""
        
        # Verificar si ya existe la entrada
        if "check_hps_expiration.py" in current_crontab:
            print("OK - La automatizacion ya esta configurada")
            return True
        
        # Agregar nueva entrada
        new_crontab = current_crontab + f"\n{cron_entry}\n"
        
        # Aplicar nuevo crontab
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_crontab)
        
        if process.returncode == 0:
            print("OK - Cron job configurado exitosamente")
            print("Frecuencia: L-V a las 9:00 AM")
            print("Log: /var/log/hps_expiration_check.log")
            print(f"Comando: {cron_entry}")
            return True
        else:
            print("ERROR - Error configurando cron job")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_manual_check():
    """Prueba la verificación manual"""
    print("🧪 Probando verificación manual...")
    
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(project_dir, "src", "commands", "check_hps_expiration.py")
    
    try:
        result = subprocess.run([
            sys.executable, script_path, "--manual"
        ], capture_output=True, text=True, cwd=project_dir)
        
        if result.returncode == 0:
            print("✅ Verificación manual exitosa")
            print("📋 Salida:")
            print(result.stdout)
            return True
        else:
            print("❌ Error en verificación manual")
            print("📋 Error:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando verificación: {e}")
        return False

def show_status():
    """Muestra el estado actual de la configuración"""
    print("📊 Estado de la automatización:")
    
    try:
        # Mostrar crontab actual
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            crontab_lines = result.stdout.strip().split('\n')
            hps_entries = [line for line in crontab_lines if "check_hps_expiration.py" in line]
            
            if hps_entries:
                print("✅ Automatización configurada:")
                for entry in hps_entries:
                    print(f"   {entry}")
            else:
                print("❌ No hay automatización configurada")
        else:
            print("❌ No se pudo obtener crontab")
            
    except Exception as e:
        print(f"❌ Error obteniendo estado: {e}")

def main():
    """Función principal"""
    print("🚀 Configuración de Automatización de Recordatorios HPS")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            success = setup_cron_job()
            sys.exit(0 if success else 1)
            
        elif command == "test":
            success = test_manual_check()
            sys.exit(0 if success else 1)
            
        elif command == "status":
            show_status()
            sys.exit(0)
            
        elif command == "help":
            print("Uso: python setup_hps_expiration_automation.py [comando]")
            print("")
            print("Comandos disponibles:")
            print("  setup  - Configurar automatización (cron job)")
            print("  test   - Probar verificación manual")
            print("  status - Mostrar estado actual")
            print("  help   - Mostrar esta ayuda")
            sys.exit(0)
            
        else:
            print(f"❌ Comando desconocido: {command}")
            print("Usa 'help' para ver comandos disponibles")
            sys.exit(1)
    else:
        # Sin argumentos, mostrar menú interactivo
        print("Selecciona una opción:")
        print("1. Configurar automatización")
        print("2. Probar verificación manual")
        print("3. Mostrar estado")
        print("4. Salir")
        
        choice = input("\nOpción (1-4): ").strip()
        
        if choice == "1":
            setup_cron_job()
        elif choice == "2":
            test_manual_check()
        elif choice == "3":
            show_status()
        elif choice == "4":
            print("👋 ¡Hasta luego!")
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main()
