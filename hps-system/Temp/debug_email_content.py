#!/usr/bin/env python3
"""
Script para debuggear el contenido del correo
"""

from src.email.service import EmailService
from src.config.settings import settings

def debug_email_content():
    print("🔍 Debuggeando contenido del correo...")
    
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

    try:
        # Obtener correos de los últimos 7 días
        new_emails = email_service.check_new_emails(since_days=7)
        print(f"Correos encontrados: {len(new_emails)}")
        
        for i, email in enumerate(new_emails):
            print(f"\n--- CORREO {i+1} ---")
            print(f"Asunto: '{email.subject}'")
            print(f"Cuerpo (primeros 200 chars): '{email.body[:200]}...'")
            print(f"Contenido combinado (asunto + cuerpo): '{email.subject} {email.body[:200]}...'")
            
            # Probar los patrones manualmente
            import re
            content = f"{email.subject} {email.body}"
            
            # Patrón específico para "de Laur Jiemnez, con fecha"
            pattern = r"de\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+),\s+con\s+fecha"
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                print(f"✅ Patrón 'de X, con fecha' encontró: '{match.group(1)}'")
            else:
                print("❌ Patrón 'de X, con fecha' NO encontró nada")
                
            # Patrón más específico con fecha
            pattern2 = r"([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+),\s+con\s+fecha\s+\d{2}/\d{2}/\d{4}"
            match2 = re.search(pattern2, content, re.IGNORECASE)
            if match2:
                print(f"✅ Patrón 'X, con fecha DD/MM/YYYY' encontró: '{match2.group(1)}'")
            else:
                print("❌ Patrón 'X, con fecha DD/MM/YYYY' NO encontró nada")
                
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    debug_email_content()
