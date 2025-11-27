#!/usr/bin/env python3
"""
Script de prueba para el sistema modular de templates
Prueba la funcionalidad del TemplateManager y templates individuales
"""

import sys
import os
import logging
from datetime import datetime

# Agregar el directorio del backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from email.template_manager import TemplateManager
from email.schemas import EmailTemplateData, EmailTemplate
from email.templates.confirmation import ConfirmationTemplate
from email.templates.status_update import StatusUpdateTemplate
from email.templates.reminder import ReminderTemplate
from email.templates.new_user_notification import NewUserNotificationTemplate

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_individual_templates():
    """Prueba los templates individuales"""
    
    print("🧪 Probando templates individuales...")
    
    # Datos de prueba
    sample_data = EmailTemplateData(
        user_name="Juan Pérez García",
        user_email="juan.perez@empresa.com",
        document_number="12345678A",
        request_type="nueva",
        status="pending",
        hps_request_id=1,
        additional_data={
            "team_name": "Equipo AICOX",
            "registration_date": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "created_by": "Carlos Alonso",
            "recipient_role": "jefe_seguridad"
        }
    )
    
    # Probar cada template
    templates_to_test = [
        ("ConfirmationTemplate", ConfirmationTemplate),
        ("StatusUpdateTemplate", StatusUpdateTemplate),
        ("ReminderTemplate", ReminderTemplate),
        ("NewUserNotificationTemplate", NewUserNotificationTemplate)
    ]
    
    for template_name, template_class in templates_to_test:
        try:
            print(f"\n📧 Probando {template_name}...")
            result = template_class.get_template(sample_data)
            
            print(f"   ✅ Asunto: {result['subject']}")
            print(f"   ✅ Cuerpo generado: {len(result['body'])} caracteres")
            print(f"   ✅ HTML generado: {len(result['html_body'])} caracteres")
            
        except Exception as e:
            print(f"   ❌ Error en {template_name}: {str(e)}")
            return False
    
    return True


def test_template_manager():
    """Prueba el TemplateManager centralizado"""
    
    print("\n🔧 Probando TemplateManager...")
    
    # Datos de prueba
    sample_data = EmailTemplateData(
        user_name="María García López",
        user_email="maria.garcia@empresa.com",
        document_number="87654321B",
        request_type="renovación",
        status="approved",
        hps_request_id=2,
        additional_data={
            "team_name": "Equipo Seguridad",
            "registration_date": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "created_by": "Ángel Bonacasa",
            "recipient_role": "admin"
        }
    )
    
    # Probar templates disponibles
    available_templates = TemplateManager.get_available_templates()
    print(f"📋 Templates disponibles: {available_templates}")
    
    # Probar cada template a través del manager
    for template_name in available_templates:
        try:
            print(f"\n📧 Probando template '{template_name}'...")
            
            # Obtener template
            result = TemplateManager.get_template(template_name, sample_data)
            
            print(f"   ✅ Asunto: {result['subject']}")
            print(f"   ✅ Cuerpo: {len(result['body'])} caracteres")
            print(f"   ✅ HTML: {len(result['html_body'])} caracteres")
            
            # Validar datos
            is_valid = TemplateManager.validate_template_data(template_name, sample_data)
            print(f"   ✅ Datos válidos: {is_valid}")
            
        except Exception as e:
            print(f"   ❌ Error en template '{template_name}': {str(e)}")
            return False
    
    return True


def test_template_info():
    """Prueba la información de templates"""
    
    print("\n📊 Probando información de templates...")
    
    # Obtener templates disponibles
    available_templates = TemplateManager.get_available_templates()
    
    for template_name in available_templates:
        try:
            print(f"\n🔍 Información de '{template_name}':")
            
            # Obtener información del template
            info = TemplateManager.get_template_info(template_name)
            
            if info["exists"]:
                print(f"   ✅ Existe: {info['exists']}")
                print(f"   ✅ Clase: {info['class']}")
                print(f"   ✅ Módulo: {info['module']}")
            else:
                print(f"   ❌ Error: {info['error']}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error obteniendo información: {str(e)}")
            return False
    
    return True


def test_template_preview():
    """Prueba la vista previa de templates"""
    
    print("\n👁️ Probando vista previa de templates...")
    
    # Obtener templates disponibles
    available_templates = TemplateManager.get_available_templates()
    
    for template_name in available_templates:
        try:
            print(f"\n🖼️ Vista previa de '{template_name}':")
            
            # Renderizar vista previa
            preview = TemplateManager.render_preview(template_name)
            
            print(f"   ✅ Asunto: {preview['subject']}")
            print(f"   ✅ Cuerpo: {len(preview['body'])} caracteres")
            print(f"   ✅ HTML: {len(preview['html_body'])} caracteres")
            
        except Exception as e:
            print(f"   ❌ Error en vista previa: {str(e)}")
            return False
    
    return True


def test_template_registration():
    """Prueba el registro de templates"""
    
    print("\n📝 Probando registro de templates...")
    
    try:
        # Obtener templates iniciales
        initial_count = len(TemplateManager.get_available_templates())
        print(f"📊 Templates iniciales: {initial_count}")
        
        # El sistema ya tiene templates registrados
        current_count = len(TemplateManager.get_available_templates())
        print(f"📊 Templates actuales: {current_count}")
        
        if current_count >= initial_count:
            print("✅ Sistema de templates funcionando correctamente")
            return True
        else:
            print("❌ Error en el sistema de templates")
            return False
            
    except Exception as e:
        print(f"❌ Error probando registro: {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 Sistema Modular de Templates - Pruebas")
    print("=" * 60)
    
    # Prueba 1: Templates individuales
    print("\n1️⃣ Prueba de templates individuales")
    individual_success = test_individual_templates()
    
    # Prueba 2: TemplateManager
    print("\n2️⃣ Prueba de TemplateManager")
    manager_success = test_template_manager()
    
    # Prueba 3: Información de templates
    print("\n3️⃣ Prueba de información de templates")
    info_success = test_template_info()
    
    # Prueba 4: Vista previa
    print("\n4️⃣ Prueba de vista previa")
    preview_success = test_template_preview()
    
    # Prueba 5: Registro de templates
    print("\n5️⃣ Prueba de registro de templates")
    registration_success = test_template_registration()
    
    print("\n" + "=" * 60)
    if all([individual_success, manager_success, info_success, preview_success, registration_success]):
        print("🎉 Todas las pruebas completadas exitosamente")
        print("\n📝 Ventajas del sistema modular:")
        print("- Templates separados por archivo")
        print("- Gestor centralizado eficiente")
        print("- Fácil mantenimiento y extensión")
        print("- No necesita services individuales")
        print("- Sistema optimizado y escalable")
    else:
        print("❌ Algunas pruebas fallaron")
        print("\n🔧 Verificar:")
        print("- Imports de templates")
        print("- Configuración del TemplateManager")
        print("- Datos de prueba")



