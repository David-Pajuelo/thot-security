#!/usr/bin/env python3
"""
Script de prueba para envío de emails del sistema HPS
Envía emails de prueba a pajuelodev@gmail.com para verificar funcionamiento
"""

import sys
import os
import logging
from datetime import datetime

# Agregar el directorio del backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from email.service import EmailService
from email.template_manager import TemplateManager
from email.schemas import EmailTemplateData, SendEmailRequest, EmailTemplate
from database.database import SessionLocal

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Email de prueba
TEST_EMAIL = "pajuelodev@gmail.com"


def test_email_connection():
    """Prueba la conexión de email"""
    
    print("🔗 Probando conexión de email...")
    
    try:
        # Crear servicio de email
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
        
        # Probar conexiones
        connection_result = email_service.test_connections()
        
        if connection_result["overall_success"]:
            print("✅ Conexiones exitosas")
            print(f"   SMTP: {'✅' if connection_result['smtp']['success'] else '❌'}")
            print(f"   IMAP: {'✅' if connection_result['imap']['success'] else '❌'}")
            return email_service, True
        else:
            print("❌ Error en conexiones")
            print(f"   SMTP: {connection_result['smtp']}")
            print(f"   IMAP: {connection_result['imap']}")
            return None, False
            
    except Exception as e:
        print(f"❌ Error probando conexión: {str(e)}")
        return None, False


def test_confirmation_email(email_service):
    """Prueba el template de confirmación"""
    
    print("\n📧 Probando email de confirmación...")
    
    try:
        # Datos de prueba
        template_data = EmailTemplateData(
            user_name="Juan Pérez García",
            user_email=TEST_EMAIL,
            document_number="12345678A",
            request_type="nueva",
            status="pending",
            hps_request_id=1,
            additional_data={
                "request_date": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
        )
        
        # Crear request
        send_request = SendEmailRequest(
            to=TEST_EMAIL,
            template=EmailTemplate.CONFIRMATION,
            template_data=template_data
        )
        
        # Obtener sesión de base de datos
        db = SessionLocal()
        
        try:
            # Enviar correo
            response = email_service.send_email_with_template(send_request, db)
            
            if response.success:
                print("✅ Email de confirmación enviado exitosamente")
                print(f"   Asunto: Confirmación de solicitud HPS - 12345678A")
                print(f"   Destinatario: {TEST_EMAIL}")
                print(f"   Email ID: {response.email_id}")
                return True
            else:
                print(f"❌ Error enviando email de confirmación: {response.error}")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error en prueba de confirmación: {str(e)}")
        return False


def test_status_update_email(email_service):
    """Prueba el template de actualización de estado"""
    
    print("\n📧 Probando email de actualización de estado...")
    
    try:
        # Datos de prueba
        template_data = EmailTemplateData(
            user_name="María García López",
            user_email=TEST_EMAIL,
            document_number="87654321B",
            request_type="renovación",
            status="approved",
            hps_request_id=2,
            additional_data={
                "old_status": "pending",
                "new_status": "approved"
            }
        )
        
        # Crear request
        send_request = SendEmailRequest(
            to=TEST_EMAIL,
            template=EmailTemplate.STATUS_UPDATE,
            template_data=template_data
        )
        
        # Obtener sesión de base de datos
        db = SessionLocal()
        
        try:
            # Enviar correo
            response = email_service.send_email_with_template(send_request, db)
            
            if response.success:
                print("✅ Email de actualización de estado enviado exitosamente")
                print(f"   Asunto: Actualización de estado HPS - 87654321B")
                print(f"   Destinatario: {TEST_EMAIL}")
                print(f"   Email ID: {response.email_id}")
                return True
            else:
                print(f"❌ Error enviando email de actualización: {response.error}")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error en prueba de actualización: {str(e)}")
        return False


def test_reminder_email(email_service):
    """Prueba el template de recordatorio"""
    
    print("\n📧 Probando email de recordatorio...")
    
    try:
        # Datos de prueba
        template_data = EmailTemplateData(
            user_name="Carlos Alonso Ruiz",
            user_email=TEST_EMAIL,
            document_number="11223344C",
            request_type="nueva",
            status="pending",
            hps_request_id=3,
            additional_data={
                "request_date": "05/10/2025 10:30",
                "days_pending": "4"
            }
        )
        
        # Crear request
        send_request = SendEmailRequest(
            to=TEST_EMAIL,
            template=EmailTemplate.REMINDER,
            template_data=template_data
        )
        
        # Obtener sesión de base de datos
        db = SessionLocal()
        
        try:
            # Enviar correo
            response = email_service.send_email_with_template(send_request, db)
            
            if response.success:
                print("✅ Email de recordatorio enviado exitosamente")
                print(f"   Asunto: Recordatorio: Solicitud HPS pendiente - 11223344C")
                print(f"   Destinatario: {TEST_EMAIL}")
                print(f"   Email ID: {response.email_id}")
                return True
            else:
                print(f"❌ Error enviando email de recordatorio: {response.error}")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error en prueba de recordatorio: {str(e)}")
        return False


def test_new_user_notification_email(email_service):
    """Prueba el template de notificación de nuevo usuario"""
    
    print("\n📧 Probando email de notificación de nuevo usuario...")
    
    try:
        # Datos de prueba
        template_data = EmailTemplateData(
            user_name="Ana Martínez Sánchez",
            user_email="ana.martinez@empresa.com",
            recipient_name="Ángel Bonacasa",
            recipient_email=TEST_EMAIL,
            additional_data={
                "user_role": "member",
                "team_name": "Equipo AICOX",
                "registration_date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "created_by": "Carlos Alonso",
                "recipient_role": "jefe_seguridad"
            }
        )
        
        # Crear request
        send_request = SendEmailRequest(
            to=TEST_EMAIL,
            template=EmailTemplate.NEW_USER_NOTIFICATION,
            template_data=template_data
        )
        
        # Obtener sesión de base de datos
        db = SessionLocal()
        
        try:
            # Enviar correo
            response = email_service.send_email_with_template(send_request, db)
            
            if response.success:
                print("✅ Email de notificación de nuevo usuario enviado exitosamente")
                print(f"   Asunto: Nuevo usuario registrado: Ana Martínez Sánchez")
                print(f"   Destinatario: {TEST_EMAIL}")
                print(f"   Email ID: {response.email_id}")
                return True
            else:
                print(f"❌ Error enviando email de notificación: {response.error}")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error en prueba de notificación: {str(e)}")
        return False


def test_user_credentials_email(email_service):
    """Prueba el template de credenciales de usuario"""
    
    print("\n📧 Probando email de credenciales de usuario...")
    
    try:
        # Datos de prueba
        template_data = EmailTemplateData(
            user_name="Pedro González López",
            user_email=TEST_EMAIL,
            document_number="99887766D",
            request_type="nueva",
            status="pending",
            hps_request_id=4,
            additional_data={
                "temp_password": "TempPass123!",
                "login_url": "http://localhost:3000/login",
                "expires_in": "7 días"
            }
        )
        
        # Crear request
        send_request = SendEmailRequest(
            to=TEST_EMAIL,
            template=EmailTemplate.USER_CREDENTIALS,
            template_data=template_data
        )
        
        # Obtener sesión de base de datos
        db = SessionLocal()
        
        try:
            # Enviar correo
            response = email_service.send_email_with_template(send_request, db)
            
            if response.success:
                print("✅ Email de credenciales enviado exitosamente")
                print(f"   Asunto: Credenciales de acceso - Pedro González López")
                print(f"   Destinatario: {TEST_EMAIL}")
                print(f"   Email ID: {response.email_id}")
                return True
            else:
                print(f"❌ Error enviando email de credenciales: {response.error}")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error en prueba de credenciales: {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 Sistema de Emails HPS - Pruebas de Envío")
    print("=" * 60)
    print(f"📧 Email de prueba: {TEST_EMAIL}")
    print("=" * 60)
    
    # Prueba 1: Conexión de email
    print("\n1️⃣ Probando conexión de email")
    email_service, connection_success = test_email_connection()
    
    if not connection_success:
        print("❌ No se puede continuar sin conexión de email")
        exit(1)
    
    # Prueba 2: Email de confirmación (empezar con uno)
    print("\n2️⃣ Probando email de confirmación")
    confirmation_success = test_confirmation_email(email_service)
    
    if confirmation_success:
        print("\n✅ PRIMER EMAIL ENVIADO EXITOSAMENTE")
        print("📧 Revisa tu bandeja de entrada en pajuelodev@gmail.com")
        print("🔍 Busca el email con asunto: 'Confirmación de solicitud HPS - 12345678A'")
        print("\n⏳ Esperando confirmación...")
        input("Presiona Enter cuando hayas confirmado que llegó el email...")
        
        # Continuar con el resto de emails
        print("\n🔄 Continuando con el resto de emails...")
        
        # Prueba 3: Email de actualización de estado
        print("\n3️⃣ Probando email de actualización de estado")
        status_success = test_status_update_email(email_service)
        
        # Prueba 4: Email de recordatorio
        print("\n4️⃣ Probando email de recordatorio")
        reminder_success = test_reminder_email(email_service)
        
        # Prueba 5: Email de notificación de nuevo usuario
        print("\n5️⃣ Probando email de notificación de nuevo usuario")
        notification_success = test_new_user_notification_email(email_service)
        
        # Prueba 6: Email de credenciales
        print("\n6️⃣ Probando email de credenciales")
        credentials_success = test_user_credentials_email(email_service)
        
        # Resumen final
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE PRUEBAS")
        print("=" * 60)
        print(f"✅ Conexión: {'✅' if connection_success else '❌'}")
        print(f"✅ Confirmación: {'✅' if confirmation_success else '❌'}")
        print(f"✅ Actualización: {'✅' if status_success else '❌'}")
        print(f"✅ Recordatorio: {'✅' if reminder_success else '❌'}")
        print(f"✅ Notificación: {'✅' if notification_success else '❌'}")
        print(f"✅ Credenciales: {'✅' if credentials_success else '❌'}")
        
        total_success = sum([connection_success, confirmation_success, status_success, 
                           reminder_success, notification_success, credentials_success])
        
        print(f"\n📈 Total exitosos: {total_success}/6")
        
        if total_success == 6:
            print("🎉 TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
            print("📧 Todos los emails enviados a pajuelodev@gmail.com")
        else:
            print("⚠️ Algunas pruebas fallaron")
            
    else:
        print("❌ No se pudo enviar el primer email")
        print("🔧 Verificar configuración de email")



