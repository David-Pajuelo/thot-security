#!/usr/bin/env python3
"""
Script para testing del procesamiento de PDFs del gobierno
"""

import os
import sys
import tempfile
from datetime import datetime

# Agregar el directorio del backend al path
sys.path.append('/app')

from src.database.database import SessionLocal
from src.email.service import EmailService
from src.email.pdf_monitor import PDFEmailMonitor
from src.config.settings import settings

def test_pdf_processing():
    """Probar el procesamiento de PDFs del gobierno"""
    
    print("🧪 Iniciando test de procesamiento de PDFs...")
    
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

    # Crear monitor con soporte para PDFs
    monitor = PDFEmailMonitor(email_service)

    # AGREGAR TU EMAIL A LOS REMITENTES DEL GOBIERNO PARA TESTING
    monitor.government_senders.append('aicoxidi@gmail.com')
    print(f"🔧 Remitentes del gobierno configurados: {monitor.government_senders}")

    # Obtener sesión de base de datos
    db = SessionLocal()
    try:
        print("📧 Procesando correos con PDFs...")
        result = monitor.monitor_emails_with_pdfs(db, since_days=1)
        print(f"✅ Resultado: {result}")
        
        # Verificar si se procesaron correos
        if result.get('emails_processed', 0) > 0:
            print(f"🎉 ¡Se procesaron {result['emails_processed']} correos!")
            if result.get('pdfs_processed', 0) > 0:
                print(f"📄 ¡Se procesaron {result['pdfs_processed']} PDFs!")
            if result.get('status_updates', 0) > 0:
                print(f"📊 ¡Se actualizaron {result['status_updates']} estados!")
        else:
            print("ℹ️ No se procesaron correos nuevos")
            
        # Verificar si hay errores
        if result.get('errors'):
            print("⚠️ Errores encontrados:")
            for error in result['errors']:
                print(f"  - {error}")
                
    finally:
        db.close()

if __name__ == "__main__":
    test_pdf_processing()
