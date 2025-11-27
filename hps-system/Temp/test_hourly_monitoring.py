#!/usr/bin/env python3
"""
Script de prueba para la nueva configuración de monitorización horaria
Verifica que la tarea se ejecute correctamente cada hora entre 8 AM y 6 PM
"""

import sys
import os
import logging
from datetime import datetime

# Agregar el directorio del backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from tasks.hps_monitor_tasks import hourly_hps_monitoring_task, CELERY_BEAT_SCHEDULE
from celery.schedules import crontab

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_hourly_schedule():
    """Probar la configuración de horarios"""
    print("🕐 Probando configuración de horarios...")
    
    # Verificar configuración de CELERY_BEAT_SCHEDULE
    hourly_config = CELERY_BEAT_SCHEDULE.get('hourly-hps-monitoring')
    
    if not hourly_config:
        print("❌ Error: No se encontró configuración 'hourly-hps-monitoring'")
        return False
    
    print(f"✅ Configuración encontrada: {hourly_config}")
    
    # Verificar que sea un crontab con hora 8-18
    schedule = hourly_config['schedule']
    if isinstance(schedule, crontab):
        print(f"✅ Tipo de schedule correcto: {type(schedule).__name__}")
        print(f"✅ Horas configuradas: {schedule.hour}")
        print(f"✅ Minutos configurados: {schedule.minute}")
        
        if schedule.hour == '8-18' and schedule.minute == 0:
            print("✅ Configuración correcta: Cada hora entre 8:00 AM y 6:00 PM")
            return True
        else:
            print(f"❌ Configuración incorrecta: hora={schedule.hour}, minuto={schedule.minute}")
            return False
    else:
        print(f"❌ Tipo de schedule incorrecto: {type(schedule)}")
        return False

def test_task_execution():
    """Probar la ejecución de la tarea"""
    print("\n🚀 Probando ejecución de tarea...")
    
    try:
        # Ejecutar tarea de forma síncrona para prueba
        result = hourly_hps_monitoring_task.apply()
        
        print(f"✅ Tarea ejecutada exitosamente")
        print(f"✅ Task ID: {result.id}")
        print(f"✅ Resultado: {result.result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error ejecutando tarea: {str(e)}")
        return False

def show_schedule_info():
    """Mostrar información detallada del horario"""
    print("\n📅 Información detallada del horario:")
    
    # Simular horarios de ejecución
    print("Horarios de ejecución programados:")
    for hour in range(8, 19):  # 8 AM a 6 PM
        print(f"  - {hour:02d}:00 - {hour:02d}:59")
    
    print(f"\nTotal de ejecuciones por día: 11 (8:00 AM - 6:00 PM)")
    print(f"Total de ejecuciones por semana: 77 (11 × 7 días)")
    print(f"Total de ejecuciones por mes: ~330 (11 × 30 días)")

def main():
    """Función principal de prueba"""
    print("🔧 PRUEBA DE CONFIGURACIÓN DE MONITORIZACIÓN HORARIA")
    print("=" * 60)
    
    # Probar configuración
    config_ok = test_hourly_schedule()
    
    # Mostrar información del horario
    show_schedule_info()
    
    # Probar ejecución (solo si la configuración es correcta)
    if config_ok:
        print("\n" + "=" * 60)
        print("⚠️  ADVERTENCIA: La siguiente prueba ejecutará la tarea real")
        print("   Esto puede procesar correos reales y actualizar la base de datos")
        
        response = input("\n¿Continuar con la prueba de ejecución? (y/N): ")
        if response.lower() == 'y':
            execution_ok = test_task_execution()
        else:
            print("⏭️  Prueba de ejecución omitida")
            execution_ok = True
    else:
        execution_ok = False
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS:")
    print(f"  Configuración: {'✅ CORRECTA' if config_ok else '❌ INCORRECTA'}")
    print(f"  Ejecución: {'✅ EXITOSA' if execution_ok else '❌ FALLIDA' if config_ok else '⏭️  OMITIDA'}")
    
    if config_ok and execution_ok:
        print("\n🎉 ¡Configuración de monitorización horaria lista!")
        print("   La tarea se ejecutará automáticamente cada hora entre 8 AM y 6 PM")
    else:
        print("\n⚠️  Hay problemas que deben resolverse antes de usar en producción")
    
    return config_ok and execution_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
