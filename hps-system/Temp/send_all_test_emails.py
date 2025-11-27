#!/usr/bin/env python3
"""
Script para enviar todos los tipos de emails de prueba
"""

import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Email de prueba
TEST_EMAIL = "pajuelodev@gmail.com"

def send_email(subject, text_body, html_body):
    """Envía un email con el contenido especificado"""
    
    try:
        # Configuración SMTP
        smtp_host = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "aicoxidi@gmail.com"
        smtp_password = "wxnopfgcliyexyqf"
        
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['From'] = "HPS System <aicoxidi@gmail.com>"
        msg['To'] = TEST_EMAIL
        msg['Subject'] = subject
        
        # Agregar partes del mensaje
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        # Conectar y enviar
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"Error enviando email: {str(e)}")
        return False

def send_status_update_email():
    """Envía email de actualización de estado"""
    
    print("Enviando email de actualizacion de estado...")
    
    subject = "PRUEBA - Actualizacion de estado HPS - 87654321B"
    
    text_body = f"""
Estimado/a Maria Garcia Lopez,

Su solicitud HPS ha sido actualizada.

Detalles de la actualizacion:
- Numero de documento: 87654321B
- Tipo de solicitud: renovacion
- Estado anterior: pending
- Nuevo estado: approved
- ID de solicitud: 2

Su solicitud ha sido aprobada exitosamente.

Atentamente,
Equipo HPS System

---
Este es un email de prueba del sistema HPS.
Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}
    """.strip()
    
    html_body = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Actualizacion de Estado HPS</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
            padding: 20px;
            border-radius: 10px 10px 0 0;
            margin: -30px -30px 30px -30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            margin: 10px 5px;
        }}
        .status-approved {{
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        .status-pending {{
            background-color: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }}
        .info-box {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #007bff;
        }}
        .info-box h3 {{
            margin-top: 0;
            color: #007bff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>PRUEBA - Estado HPS Actualizado</h1>
        </div>
        
        <p>Estimado/a <strong>Maria Garcia Lopez</strong>,</p>
        
        <p>Su solicitud HPS ha sido actualizada con un nuevo estado.</p>
        
        <div class="info-box">
            <h3>Detalles de la Actualizacion</h3>
            <ul>
                <li><strong>Numero de documento:</strong> 87654321B</li>
                <li><strong>Tipo de solicitud:</strong> renovacion</li>
                <li><strong>Estado anterior:</strong> <span class="status-badge status-pending">pending</span></li>
                <li><strong>Nuevo estado:</strong> <span class="status-badge status-approved">approved</span></li>
                <li><strong>ID de solicitud:</strong> 2</li>
            </ul>
        </div>
        
        <p>Su solicitud ha sido <strong>aprobada exitosamente</strong>.</p>
        
        <p>Atentamente,<br>
        <strong>Equipo HPS System</strong></p>
    </div>
</body>
</html>
    """.strip()
    
    return send_email(subject, text_body, html_body)

def send_reminder_email():
    """Envía email de recordatorio"""
    
    print("Enviando email de recordatorio...")
    
    subject = "PRUEBA - Recordatorio: Solicitud HPS pendiente - 11223344C"
    
    text_body = f"""
Estimado/a Carlos Alonso Ruiz,

Le recordamos que tiene una solicitud HPS pendiente.

Detalles de la solicitud:
- Numero de documento: 11223344C
- Tipo de solicitud: nueva
- Estado: pending
- Fecha de solicitud: 05/10/2025 10:30
- Dias pendiente: 4
- ID de solicitud: 3

Por favor, complete los pasos necesarios para continuar con su solicitud.

Atentamente,
Equipo HPS System

---
Este es un email de prueba del sistema HPS.
Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}
    """.strip()
    
    html_body = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recordatorio HPS</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%);
            color: #212529;
            padding: 20px;
            border-radius: 10px 10px 0 0;
            margin: -30px -30px 30px -30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .alert-box {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .info-box {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #ffc107;
        }}
        .info-box h3 {{
            margin-top: 0;
            color: #856404;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>PRUEBA - Recordatorio HPS Pendiente</h1>
        </div>
        
        <div class="alert-box">
            <strong>Recordatorio:</strong> Tiene una solicitud HPS pendiente que requiere su atencion.
        </div>
        
        <p>Estimado/a <strong>Carlos Alonso Ruiz</strong>,</p>
        
        <p>Le recordamos que tiene una solicitud HPS pendiente desde hace varios dias.</p>
        
        <div class="info-box">
            <h3>Detalles de la Solicitud Pendiente</h3>
            <ul>
                <li><strong>Numero de documento:</strong> 11223344C</li>
                <li><strong>Tipo de solicitud:</strong> nueva</li>
                <li><strong>Estado:</strong> pending</li>
                <li><strong>Fecha de solicitud:</strong> 05/10/2025 10:30</li>
                <li><strong>Dias pendiente:</strong> 4</li>
                <li><strong>ID de solicitud:</strong> 3</li>
            </ul>
        </div>
        
        <p>Por favor, complete los pasos necesarios para continuar con su solicitud.</p>
        
        <p>Atentamente,<br>
        <strong>Equipo HPS System</strong></p>
    </div>
</body>
</html>
    """.strip()
    
    return send_email(subject, text_body, html_body)

def send_new_user_notification_email():
    """Envía email de notificación de nuevo usuario"""
    
    print("Enviando email de notificacion de nuevo usuario...")
    
    subject = "PRUEBA - Nuevo usuario registrado: Ana Martinez Sanchez"
    
    text_body = f"""
Estimado/a Angel Bonacasa,

Se ha registrado un nuevo usuario en el sistema.

Detalles del nuevo usuario:
- Nombre: Ana Martinez Sanchez
- Email: ana.martinez@empresa.com
- Rol: member
- Equipo: Equipo AICOX
- Fecha de registro: {datetime.now().strftime("%d/%m/%Y %H:%M")}
- Registrado por: Carlos Alonso

Como jefe de seguridad, puede revisar y gestionar este nuevo usuario.

Atentamente,
Equipo HPS System

---
Este es un email de prueba del sistema HPS.
    """.strip()
    
    html_body = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notificacion Nuevo Usuario</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #6f42c1 0%, #5a32a3 100%);
            color: white;
            padding: 20px;
            border-radius: 10px 10px 0 0;
            margin: -30px -30px 30px -30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .user-info {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #6f42c1;
        }}
        .user-info h3 {{
            margin-top: 0;
            color: #6f42c1;
        }}
        .user-details {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 15px;
        }}
        .user-details div {{
            padding: 8px;
            background-color: white;
            border-radius: 4px;
            border: 1px solid #e9ecef;
        }}
        .user-details strong {{
            color: #6f42c1;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>PRUEBA - Nuevo Usuario Registrado</h1>
        </div>
        
        <p>Estimado/a <strong>Angel Bonacasa</strong>,</p>
        
        <p>Se ha registrado un nuevo usuario en el sistema que requiere su atencion como jefe de seguridad.</p>
        
        <div class="user-info">
            <h3>Detalles del Nuevo Usuario</h3>
            <div class="user-details">
                <div><strong>Nombre:</strong> Ana Martinez Sanchez</div>
                <div><strong>Email:</strong> ana.martinez@empresa.com</div>
                <div><strong>Rol:</strong> member</div>
                <div><strong>Equipo:</strong> Equipo AICOX</div>
                <div><strong>Fecha de registro:</strong> {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>
                <div><strong>Registrado por:</strong> Carlos Alonso</div>
            </div>
        </div>
        
        <p>Como jefe de seguridad, puede revisar y gestionar este nuevo usuario desde el panel de administracion.</p>
        
        <p>Atentamente,<br>
        <strong>Equipo HPS System</strong></p>
    </div>
</body>
</html>
    """.strip()
    
    return send_email(subject, text_body, html_body)

if __name__ == "__main__":
    print("Sistema de Emails HPS - Enviando Todos los Emails de Prueba")
    print("=" * 70)
    print(f"Destinatario: {TEST_EMAIL}")
    print("=" * 70)
    
    # Lista de emails a enviar
    emails_to_send = [
        ("Actualizacion de Estado", send_status_update_email),
        ("Recordatorio", send_reminder_email),
        ("Notificacion de Nuevo Usuario", send_new_user_notification_email),
    ]
    
    results = []
    
    for i, (email_name, email_function) in enumerate(emails_to_send, 1):
        print(f"\n{i}. Enviando email de {email_name}...")
        success = email_function()
        results.append((email_name, success))
        
        if success:
            print(f"OK - Email de {email_name} enviado exitosamente")
        else:
            print(f"ERROR - Error enviando email de {email_name}")
    
    # Resumen final
    print("\n" + "=" * 70)
    print("RESUMEN FINAL DE ENVIOS")
    print("=" * 70)
    
    for email_name, success in results:
        status = "OK" if success else "ERROR"
        print(f"{email_name}: {status}")
    
    total_success = sum(1 for _, success in results if success)
    total_emails = len(results)
    
    print(f"\nTotal exitosos: {total_success}/{total_emails}")
    
    if total_success == total_emails:
        print("TODOS LOS EMAILS ENVIADOS EXITOSAMENTE")
        print("Sistema de emails funcionando correctamente")
    else:
        print("Algunos emails fallaron")
    
    print(f"\nRevisa tu bandeja de entrada en {TEST_EMAIL}")
    print("Busca los emails con asunto que contengan 'PRUEBA'")
