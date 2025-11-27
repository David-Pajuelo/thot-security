#!/usr/bin/env python3
"""
Script de prueba para el sistema de notificaciones de nuevo usuario
Prueba la funcionalidad de envío de correos cuando se crea un usuario
"""

import sys
import os
import logging
from datetime import datetime

# Agregar el directorio del backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from email.service import EmailService
from email.user_notification_service import UserNotificationService
from email.templates.new_user_notification import NewUserNotificationTemplate
from email.schemas import EmailTemplateData
from database.database import SessionLocal
from models.user import User
from models.team import Team

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_new_user_notification_template():
    """Prueba el template de notificación de nuevo usuario"""
    
    print("🧪 Probando template de notificación de nuevo usuario...")
    
    # Datos de prueba
    template_data = EmailTemplateData(
        user_name="Juan Pérez García",
        user_email="juan.perez@empresa.com",
        recipient_name="Ángel Bonacasa",
        recipient_email="abonacasa@aicox.com",
        additional_data={
            "user_role": "member",
            "team_name": "Equipo AICOX",
            "registration_date": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "created_by": "Carlos Alonso",
            "recipient_role": "jefe_seguridad"
        }
    )
    
    # Obtener template
    template = NewUserNotificationTemplate.get_template(template_data)
    
    print("✅ Template generado exitosamente")
    print(f"   Asunto: {template['subject']}")
    print(f"   Destinatario: {template_data.recipient_name}")
    print(f"   Usuario: {template_data.user_name}")
    print(f"   Rol: {template_data.additional_data['user_role']}")
    print(f"   Equipo: {template_data.additional_data['team_name']}")
    
    return True


def test_notification_service():
    """Prueba el servicio de notificaciones"""
    
    print("\n🔔 Probando servicio de notificaciones...")
    
    try:
        # Crear servicio de email (TEMPORAL - credenciales compartidas)
        print("📧 Configurando servicio de email...")
        email_service = EmailService(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_username="aicoxidi@gmail.com",  # TEMPORAL
            smtp_password="",  # TEMPORAL - usar variables de entorno
            imap_host="imap.gmail.com",
            imap_port=993,
            imap_username="aicoxidi@gmail.com",  # TEMPORAL
            imap_password="",  # TEMPORAL - usar variables de entorno
            from_name="HPS System",
            reply_to="aicoxidi@gmail.com"
        )
        
        # Crear servicio de notificaciones
        print("🔔 Creando servicio de notificaciones...")
        notification_service = UserNotificationService(email_service)
        
        # Obtener sesión de base de datos
        print("🗄️ Conectando a base de datos...")
        db = SessionLocal()
        
        try:
            # Buscar un usuario existente para simular
            test_user = db.query(User).filter(User.is_active == True).first()
            
            if not test_user:
                print("❌ No se encontraron usuarios en la base de datos")
                return False
            
            print(f"👤 Usando usuario de prueba: {test_user.email}")
            
            # Simular notificación (sin enviar correos reales)
            print("📬 Simulando notificación de nuevo usuario...")
            
            # Preparar datos del template
            template_data = notification_service._prepare_template_data(test_user, test_user, db)
            
            print("📋 Datos del template preparados:")
            print(f"   Usuario: {template_data['user_name']}")
            print(f"   Email: {template_data['user_email']}")
            print(f"   Rol: {template_data['additional_data']['user_role']}")
            print(f"   Equipo: {template_data['additional_data']['team_name']}")
            
            # Obtener destinatarios
            recipients = notification_service._get_notification_recipients(test_user, db)
            
            print(f"📧 Destinatarios encontrados: {len(recipients)}")
            for recipient in recipients:
                print(f"   - {recipient.email} ({recipient.role.name})")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error en la prueba: {str(e)}")
        logger.error(f"Error en prueba de notificaciones: {str(e)}")
        return False


def test_email_connection():
    """Prueba la conexión de email"""
    
    print("\n🔗 Probando conexión de email...")
    
    try:
        # Crear servicio de email
        email_service = EmailService(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_username="aicoxidi@gmail.com",  # TEMPORAL
            smtp_password="",  # TEMPORAL
            imap_host="imap.gmail.com",
            imap_port=993,
            imap_username="aicoxidi@gmail.com",  # TEMPORAL
            imap_password="",  # TEMPORAL
            from_name="HPS System",
            reply_to="aicoxidi@gmail.com"
        )
        
        # Probar conexiones
        connection_result = email_service.test_connections()
        
        if connection_result["overall_success"]:
            print("✅ Conexiones exitosas")
            print(f"   SMTP: {'✅' if connection_result['smtp']['success'] else '❌'}")
            print(f"   IMAP: {'✅' if connection_result['imap']['success'] else '❌'}")
            return True
        else:
            print("❌ Error en conexiones")
            print(f"   SMTP: {connection_result['smtp']}")
            print(f"   IMAP: {connection_result['imap']}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando conexión: {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 Sistema de Notificaciones de Usuario - Pruebas")
    print("=" * 60)
    
    # Prueba 1: Template de notificación
    print("\n1️⃣ Prueba de template de notificación")
    template_success = test_new_user_notification_template()
    
    # Prueba 2: Conexión de email
    print("\n2️⃣ Prueba de conexión de email")
    connection_success = test_email_connection()
    
    # Prueba 3: Servicio de notificaciones
    print("\n3️⃣ Prueba de servicio de notificaciones")
    service_success = test_notification_service()
    
    print("\n" + "=" * 60)
    if template_success and connection_success and service_success:
        print("🎉 Todas las pruebas completadas exitosamente")
        print("\n📝 Notas:")
        print("- Sistema de notificaciones implementado")
        print("- Templates modulares creados")
        print("- Credenciales temporales configuradas")
        print("- Listo para integrar en creación de usuarios")
    else:
        print("❌ Algunas pruebas fallaron")
        print("\n🔧 Verificar:")
        print("- Configuración de email")
        print("- Conexión a base de datos")
        print("- Permisos de usuario")



