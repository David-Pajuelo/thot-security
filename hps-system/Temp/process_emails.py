#!/usr/bin/env python3
"""
Script para procesar correos del sistema de monitorización
"""

from src.email.hps_monitor import HPSEmailMonitor
from src.email.service import EmailService
from src.database.database import SessionLocal
from src.config.settings import settings

def process_emails():
    print("📧 Procesando correos del sistema de monitorización...")
    
    # Crear servicio de email con credenciales del .env
    email_service = EmailService(
        smtp_host=settings.SMTP_HOST,
        smtp_port=settings.SMTP_PORT,
        smtp_username=settings.SMTP_USER,
        smtp_password=settings.SMTP_PASSWORD,
        imap_host=settings.IMAP_HOST,
        imap_port=settings.IMAP_PORT,
        imap_username=settings.IMAP_USER,
        imap_password=settings.IMAP_PASSWORD,
        from_name=settings.SMTP_FROM_NAME,
        reply_to=settings.SMTP_REPLY_TO
    )

    # Crear monitor
    monitor = HPSEmailMonitor(email_service)

    # MODIFICACIÓN TEMPORAL PARA TESTING: Agregar tu email a los remitentes del gobierno
    monitor.government_senders.append('aicoxidi@gmail.com')
    print("🔧 Remitentes del gobierno configurados:", monitor.government_senders)

    # Obtener sesión de base de datos
    db = SessionLocal()
    try:
        print("📧 Procesando correos nuevamente...")
        result = monitor.monitor_emails(db, since_days=1)
        print(f"✅ Resultado: {result}")
        
        # Verificar si se procesaron correos
        if result.get('emails_processed', 0) > 0:
            print(f"🎉 ¡Se procesaron {result['emails_processed']} correos!")
            if result.get('status_updates', 0) > 0:
                print(f"📊 ¡Se actualizaron {result['status_updates']} estados!")
        else:
            print("ℹ️ No se procesaron correos nuevos")
            
    finally:
        db.close()

if __name__ == "__main__":
    process_emails()
