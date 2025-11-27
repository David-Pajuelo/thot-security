#!/usr/bin/env python3
"""
Script simplificado para verificar la configuración de monitorización horaria
Solo verifica la configuración sin ejecutar tareas reales
"""

import re

def verify_crontab_config():
    """Verificar que la configuración de crontab sea correcta"""
    print("🔍 Verificando configuración de crontab...")
    
    # Leer el archivo de configuración
    try:
        with open('../backend/src/tasks/hps_monitor_tasks.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ No se encontró el archivo de configuración")
        return False
    
    # Buscar la configuración de CELERY_BEAT_SCHEDULE
    schedule_match = re.search(r"CELERY_BEAT_SCHEDULE\s*=\s*\{[^}]*'hourly-hps-monitoring'[^}]*\}", content, re.DOTALL)
    
    if not schedule_match:
        print("❌ No se encontró la configuración 'hourly-hps-monitoring'")
        return False
    
    schedule_config = schedule_match.group(0)
    print("✅ Configuración encontrada:")
    print(schedule_config)
    
    # Verificar que contenga la configuración correcta
    if "crontab(hour='8-18', minute=0)" in schedule_config:
        print("✅ Configuración correcta: cada hora entre 8:00 AM y 6:00 PM")
        return True
    else:
        print("❌ Configuración incorrecta: no se encontró crontab(hour='8-18', minute=0)")
        return False

def verify_task_definition():
    """Verificar que la tarea esté definida correctamente"""
    print("\n🔍 Verificando definición de tarea...")
    
    try:
        with open('../backend/src/tasks/hps_monitor_tasks.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ No se encontró el archivo de configuración")
        return False
    
    # Buscar la definición de la tarea horaria
    task_match = re.search(r"@celery_app\.task\(bind=True, name=\"hps_monitor\.hourly_check\"\)\s*def hourly_hps_monitoring_task", content)
    
    if not task_match:
        print("❌ No se encontró la definición de 'hourly_hps_monitoring_task'")
        return False
    
    print("✅ Tarea 'hourly_hps_monitoring_task' encontrada")
    
    # Verificar que incluya procesamiento de PDFs
    if "PDFEmailMonitor" in content and "pdf_monitor.monitor_emails_with_pdfs" in content:
        print("✅ Procesamiento de PDFs incluido en la tarea")
        return True
    else:
        print("❌ Procesamiento de PDFs no encontrado en la tarea")
        return False

def show_schedule_details():
    """Mostrar detalles del horario de ejecución"""
    print("\n📅 DETALLES DEL HORARIO DE EJECUCIÓN:")
    print("=" * 50)
    
    print("🕐 Horarios de ejecución programados:")
    for hour in range(8, 19):  # 8 AM a 6 PM
        print(f"   {hour:02d}:00 - {hour:02d}:59")
    
    print(f"\n📊 Estadísticas:")
    print(f"   • Ejecuciones por día: 11")
    print(f"   • Ejecuciones por semana: 77 (11 × 7 días)")
    print(f"   • Ejecuciones por mes: ~330 (11 × 30 días)")
    
    print(f"\n🔧 Funcionalidades incluidas:")
    print(f"   • Monitorización de correos HPS (pending → waiting_dps)")
    print(f"   • Procesamiento de PDFs adjuntos (concesiones/rechazos)")
    print(f"   • Alertas de seguridad (HPS en pending en PDFs del gobierno)")

def main():
    """Función principal de verificación"""
    print("🔧 VERIFICACIÓN DE CONFIGURACIÓN DE MONITORIZACIÓN HORARIA")
    print("=" * 70)
    
    # Verificar configuración de crontab
    crontab_ok = verify_crontab_config()
    
    # Verificar definición de tarea
    task_ok = verify_task_definition()
    
    # Mostrar detalles del horario
    show_schedule_details()
    
    # Resumen final
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE VERIFICACIÓN:")
    print(f"  Configuración crontab: {'✅ CORRECTA' if crontab_ok else '❌ INCORRECTA'}")
    print(f"  Definición de tarea: {'✅ CORRECTA' if task_ok else '❌ INCORRECTA'}")
    
    if crontab_ok and task_ok:
        print("\n🎉 ¡Configuración de monitorización horaria verificada correctamente!")
        print("   La tarea se ejecutará automáticamente cada hora entre 8 AM y 6 PM")
        print("   Incluye procesamiento de correos HPS y PDFs adjuntos")
    else:
        print("\n⚠️  Hay problemas en la configuración que deben resolverse")
    
    return crontab_ok and task_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
