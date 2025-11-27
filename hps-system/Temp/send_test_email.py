#!/usr/bin/env python3
"""
Script simple para enviar un email de prueba
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from email.service import EmailService
from email.schemas import EmailTemplateData, SendEmailRequest, EmailTemplate
from database.database import SessionLocal

# Email de prueba
TEST_EMAIL = "pajuelodev@gmail.com"

def main():
    print("🚀 Enviando email de prueba...")
    print(f"📧 Destinatario: {TEST_EMAIL}")
    
    try:
        # Crear servicio de email
        print("🔧 Configurando servicio de email...")
        email_service = EmailService(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_username="aicoxidi@gmail.com",
            smtp_password="",  # TEMPORAL - usar variables de entorno
            imap_host="imap.gmail.com",
            imap_port=993,
            imap_username="aicoxidi@gmail.com",
            imap_password="",  # TEMPORAL - usar variables de entorno
            from_name="HPS System",
            reply_to="aicoxidi@gmail.com"
        )
        
        # Probar conexión
        print("🔗 Probando conexión...")
        connection_result = email_service.test_connections()
        
        if not connection_result["overall_success"]:
            print("❌ Error en conexión de email")
            print(f"SMTP: {connection_result['smtp']}")
            print(f"IMAP: {connection_result['imap']}")
            return False
        
        print("✅ Conexión exitosa")
        
        # Datos de prueba para email de confirmación
        print("📝 Preparando datos de prueba...")
        template_data = EmailTemplateData(
            user_name="Juan Pérez García",
            user_email=TEST_EMAIL,
            document_number="12345678A",
            request_type="nueva",
            status="pending",
            hps_request_id=1,
            additional_data={
                "request_date": "09/10/2025 15:30"
            }
        )
        
        # Crear request
        send_request = SendEmailRequest(
            to=TEST_EMAIL,
            template=EmailTemplate.CONFIRMATION,
            template_data=template_data
        )
        
        # Obtener sesión de base de datos
        print("🗄️ Conectando a base de datos...")
        db = SessionLocal()
        
        try:
            # Enviar correo
            print("📧 Enviando email de confirmación...")
            response = email_service.send_email_with_template(send_request, db)
            
            if response.success:
                print("✅ EMAIL ENVIADO EXITOSAMENTE")
                print(f"   Asunto: Confirmación de solicitud HPS - 12345678A")
                print(f"   Destinatario: {TEST_EMAIL}")
                print(f"   Email ID: {response.email_id}")
                print("\n📬 Revisa tu bandeja de entrada en pajuelodev@gmail.com")
                return True
            else:
                print(f"❌ Error enviando email: {response.error}")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 PRIMER EMAIL ENVIADO - Esperando confirmación...")
    else:
        print("\n❌ Error enviando email")



