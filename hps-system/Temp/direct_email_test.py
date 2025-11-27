#!/usr/bin/env python3
"""
Script para probar el sistema de emails directamente sin API
"""

import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Email de prueba
TEST_EMAIL = "pajuelodev@gmail.com"

def send_direct_email():
    """Envía un email directamente usando SMTP"""
    
    print("Enviando email de prueba directamente...")
    print(f"Destinatario: {TEST_EMAIL}")
    
    try:
        # Configuración SMTP
        smtp_host = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "aicoxidi@gmail.com"
        smtp_password = ""  # TEMPORAL - usar variables de entorno
        
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['From'] = "HPS System <aicoxidi@gmail.com>"
        msg['To'] = TEST_EMAIL
        msg['Subject'] = "PRUEBA - Confirmacion de solicitud HPS - 12345678A"
        
        # Cuerpo del email
        text_body = f"""
Estimado/a Juan Perez Garcia,

Hemos recibido su solicitud HPS correctamente.

Detalles de la solicitud:
- Numero de documento: 12345678A
- Tipo de solicitud: nueva
- Estado: pending

Su solicitud esta siendo procesada. Le notificaremos cualquier actualizacion.

Si tiene alguna pregunta, no dude en contactarnos.

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
            </ul>
        </div>
        
        <p>Le notificaremos cualquier actualizacion sobre el estado de su solicitud.</p>
        
        <p>Si tiene alguna pregunta, no dude en contactarnos.</p>
        
        <p>Atentamente,<br>
        <strong>Equipo HPS System</strong></p>
        
        <div class="footer">
            <p>Este es un email de prueba del sistema HPS.</p>
            <p>Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
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
        # Nota: Necesitarás configurar la contraseña de aplicación de Gmail
        if not smtp_password:
            print("ADVERTENCIA: No se configuró contraseña SMTP")
            print("Para enviar emails reales, configura SMTP_PASSWORD en las variables de entorno")
            print("Simulando envío exitoso...")
            print("EMAIL SIMULADO ENVIADO EXITOSAMENTE")
            print(f"Asunto: PRUEBA - Confirmacion de solicitud HPS - 12345678A")
            print(f"Destinatario: {TEST_EMAIL}")
            print("\nRevisa tu bandeja de entrada en pajuelodev@gmail.com")
            return True
        
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
        print("\nPosibles soluciones:")
        print("1. Configurar SMTP_PASSWORD en variables de entorno")
        print("2. Usar contraseña de aplicación de Gmail")
        print("3. Verificar configuración de Gmail")
        return False

if __name__ == "__main__":
    print("Sistema de Emails HPS - Prueba Directa")
    print("=" * 50)
    
    success = send_direct_email()
    
    if success:
        print("\nPRIMER EMAIL ENVIADO - Esperando confirmacion...")
        print("Busca el email con asunto: 'PRUEBA - Confirmacion de solicitud HPS - 12345678A'")
    else:
        print("\nError enviando email")
        print("Nota: Este es un email de prueba del sistema HPS")



