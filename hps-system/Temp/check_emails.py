#!/usr/bin/env python3
"""
Script para verificar correos en la bandeja de entrada
"""

from src.email.service import EmailService
from src.config.settings import settings

def check_emails():
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

    print('Verificando correos nuevos...')
    try:
        # Probar conexión IMAP
        connection_result = email_service.test_connections()
        print(f'Conexión IMAP: {connection_result["imap"]["success"]}')
        
        if connection_result['imap']['success']:
            # Obtener correos nuevos
            new_emails = email_service.check_new_emails(since_days=1)
            print(f'Correos nuevos encontrados: {len(new_emails)}')
            
            for i, email in enumerate(new_emails[:5]):  # Mostrar solo los primeros 5
                print(f'  Correo {i+1}:')
                print(f'    De: {email.from_email}')
                print(f'    Asunto: {email.subject}')
                print(f'    Fecha: {email.date}')
                print(f'    Contenido (primeros 200 chars): {email.body[:200]}...')
                print()
        else:
            print('Error en conexión IMAP:', connection_result.get('imap_error', 'Desconocido'))
            
    except Exception as e:
        print(f'Error: {str(e)}')

if __name__ == "__main__":
    check_emails()
