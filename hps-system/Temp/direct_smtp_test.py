#!/usr/bin/env python3
"""
Script para probar el envío directo de emails usando SMTP
"""

import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Email de prueba
TEST_EMAIL = "pajuelodev@gmail.com"

def send_confirmation_email():
    """Envía email de confirmación directamente"""
    
    print("Enviando email de confirmacion directamente...")
    print(f"Destinatario: {TEST_EMAIL}")
    
    try:
        # Configuración SMTP con las credenciales proporcionadas
        smtp_host = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "aicoxidi@gmail.com"
        smtp_password = "wxnopfgcliyexyqf"
        
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['From'] = "HPS System <aicoxidi@gmail.com>"
        msg['To'] = TEST_EMAIL
        msg['Subject'] = "PRUEBA - Confirmacion de solicitud HPS - 12345678A"
        
        # Cuerpo del email en texto plano
        text_body = f"""
Estimado/a Juan Perez Garcia,

Hemos recibido su solicitud HPS correctamente.

Detalles de la solicitud:
- Numero de documento: 12345678A
- Tipo de solicitud: nueva
- Estado: pending
- ID de solicitud: 1
- Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}

Su solicitud esta siendo procesada. Le notificaremos cualquier actualizacion.

Si tiene alguna pregunta, no dude en contactarnos.

Atentamente,
Equipo HPS System

---
Este es un email de prueba del sistema HPS.
        """.strip()
        
        # Cuerpo del email en HTML
        html_body = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Confirmacion de Solicitud HPS</title>
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
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
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
        .info-box {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #28a745;
        }}
        .info-box h3 {{
            margin-top: 0;
            color: #28a745;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            color: #6c757d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>PRUEBA - Solicitud HPS Confirmada</h1>
        </div>
        
        <p>Estimado/a <strong>Juan Perez Garcia</strong>,</p>
        
        <p>Hemos recibido su solicitud HPS correctamente y esta siendo procesada.</p>
        
        <div class="info-box">
            <h3>Detalles de la Solicitud</h3>
            <ul>
                <li><strong>Numero de documento:</strong> 12345678A</li>
                <li><strong>Tipo de solicitud:</strong> nueva</li>
                <li><strong>Estado actual:</strong> pending</li>
                <li><strong>ID de solicitud:</strong> 1</li>
                <li><strong>Fecha:</strong> {datetime.now().strftime("%d/%m/%Y %H:%M")}</li>
            </ul>
        </div>
        
        <p>Le notificaremos cualquier actualizacion sobre el estado de su solicitud.</p>
        
        <p>Si tiene alguna pregunta, no dude en contactarnos.</p>
        
        <p>Atentamente,<br>
        <strong>Equipo HPS System</strong></p>
        
        <div class="footer">
            <p>Este es un email de prueba del sistema HPS.</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        # Agregar partes del mensaje
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        # Conectar y enviar
        print("Conectando a SMTP...")
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        
        print("Autenticando...")
        server.login(smtp_username, smtp_password)
        
        print("Enviando email...")
        server.send_message(msg)
        server.quit()
        
        print("EMAIL ENVIADO EXITOSAMENTE")
        print(f"Asunto: PRUEBA - Confirmacion de solicitud HPS - 12345678A")
        print(f"Destinatario: {TEST_EMAIL}")
        print("\nRevisa tu bandeja de entrada en pajuelodev@gmail.com")
        return True
        
    except Exception as e:
        print(f"Error enviando email: {str(e)}")
        return False

if __name__ == "__main__":
    print("Sistema de Emails HPS - Prueba Directa SMTP")
    print("=" * 50)
    
    success = send_confirmation_email()
    
    if success:
        print("\nPRIMER EMAIL ENVIADO EXITOSAMENTE")
        print("Busca el email con asunto: 'PRUEBA - Confirmacion de solicitud HPS - 12345678A'")
        print("Revisa tu bandeja de entrada en pajuelodev@gmail.com")
    else:
        print("\nError enviando email")



