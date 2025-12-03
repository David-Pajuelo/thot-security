"""
Templates de email para HPS en Django
Adaptados desde hps-system/backend/src/email/templates/
"""
from typing import Dict, Any
from django.conf import settings


class UserCredentialsTemplate:
    """Template para credenciales de usuario"""
    
    @staticmethod
    def get_template(data: Dict[str, Any]) -> Dict[str, str]:
        """
        Renderiza el template de credenciales de usuario
        
        Args:
            data: Diccionario con user_name, user_email, temp_password, login_url
            
        Returns:
            Dict con subject, body y html_body
        """
        user_name = data.get("user_name", "")
        user_email = data.get("user_email", "")
        temp_password = data.get("temp_password", "")
        # Para emails HPS, usar HPS_SYSTEM_URL si está disponible, sino FRONTEND_URL
        hps_system_url = getattr(settings, 'HPS_SYSTEM_URL', None)
        default_url = hps_system_url if hps_system_url else getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        login_url = data.get("login_url", f"{default_url}/login")
        
        subject = f"Bienvenido al Sistema HPS - Tus credenciales de acceso"
        
        body = f"""
Hola {user_name},

¡Bienvenido al Sistema HPS!

Se ha creado tu cuenta en la plataforma con las siguientes credenciales:

📧 Email: {user_email}
🔑 Contraseña temporal: {temp_password}

IMPORTANTE: Esta es una contraseña temporal. Te recomendamos cambiarla en tu primer acceso.

Para acceder al sistema:
1. Ve a: {login_url}
2. Inicia sesión con las credenciales proporcionadas
3. Cambia tu contraseña por una más segura

Si tienes alguna pregunta, no dudes en contactarnos.

¡Gracias!

Equipo HPS
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Credenciales de Acceso - Sistema HPS</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #007bff;
            margin: 0;
            font-size: 28px;
        }}
        .credentials {{
            background-color: #f8f9fa;
            border: 2px solid #007bff;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }}
        .credential-item {{
            margin: 15px 0;
            font-size: 16px;
        }}
        .credential-label {{
            font-weight: bold;
            color: #007bff;
            display: block;
            margin-bottom: 5px;
        }}
        .credential-value {{
            font-family: 'Courier New', monospace;
            background-color: white;
            padding: 8px 12px;
            border-radius: 4px;
            border: 1px solid #ddd;
            display: inline-block;
            min-width: 200px;
        }}
        .warning {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
            color: #856404;
        }}
        .warning strong {{
            color: #d63031;
        }}
        .steps {{
            background-color: #e8f4fd;
            border-left: 4px solid #007bff;
            padding: 20px;
            margin: 20px 0;
        }}
        .steps h3 {{
            color: #007bff;
            margin-top: 0;
        }}
        .steps ol {{
            margin: 0;
            padding-left: 20px;
        }}
        .steps li {{
            margin: 10px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 14px;
        }}
        .button {{
            display: inline-block;
            background-color: #007bff;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
            font-weight: bold;
        }}
        .button:hover {{
            background-color: #0056b3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 ¡Bienvenido al Sistema HPS!</h1>
        </div>
        
        <p>Hola <strong>{user_name}</strong>,</p>
        
        <p>Se ha creado tu cuenta en la plataforma con las siguientes credenciales:</p>
        
        <div class="credentials">
            <div class="credential-item">
                <span class="credential-label">📧 Email:</span>
                <div class="credential-value">{user_email}</div>
            </div>
            <div class="credential-item">
                <span class="credential-label">🔑 Contraseña temporal:</span>
                <div class="credential-value" style="font-size: 18px; letter-spacing: 2px; font-weight: bold;">{temp_password}</div>
            </div>
        </div>
        
        <div class="warning">
            <strong>⚠️ IMPORTANTE:</strong> Esta es una contraseña temporal. Te recomendamos cambiarla en tu primer acceso por una más segura.
        </div>
        
        <div class="steps">
            <h3>📋 Para acceder al sistema:</h3>
            <ol>
                <li>Haz clic en el botón de abajo o ve a: <a href="{login_url}">{login_url}</a></li>
                <li>Inicia sesión con las credenciales proporcionadas</li>
                <li>Cambia tu contraseña por una más segura</li>
            </ol>
        </div>
        
        <div style="text-align: center;">
            <a href="{login_url}" class="button">🚀 Acceder al Sistema</a>
        </div>
        
        <p>Si tienes alguna pregunta, no dudes en contactarnos.</p>
        
        <p>¡Gracias!</p>
        
        <p><strong>Equipo HPS</strong></p>
    </div>
    
    <div class="footer">
        <p>Este es un correo automático, por favor no responda directamente.</p>
    </div>
</body>
</html>
        """.strip()
        
        return {
            "subject": subject,
            "body": body,
            "html_body": html_body
        }


class StatusUpdateTemplate:
    """Template para notificación de cambio de estado HPS"""
    
    @staticmethod
    def _get_status_message(status: str) -> str:
        """Obtener mensaje según el estado"""
        status_messages = {
            "pending": "Su solicitud está pendiente de revisión.",
            "waiting_dps": "Se le ha enviado un formulario DPS para completar.",
            "submitted": "Su solicitud ha sido enviada a la entidad competente y está en trámite.",
            "approved": "¡Felicidades! Su solicitud HPS ha sido aprobada.",
            "rejected": "Lamentamos informarle que su solicitud ha sido rechazada.",
            "expired": "Su solicitud HPS ha expirado."
        }
        return status_messages.get(status, "Su solicitud ha sido actualizada.")
    
    @staticmethod
    def get_template(data: Dict[str, Any]) -> Dict[str, str]:
        """
        Obtiene el template renderizado para notificación de cambio de estado
        
        Args:
            data: Diccionario con user_name, user_email, document_number, request_type, 
                  status, old_status, additional_data (opcional con info del correo original)
            
        Returns:
            Dict con subject, body y html_body
        """
        old_status = data.get("old_status", "N/A")
        new_status = data.get("status", "N/A")
        additional_data = data.get("additional_data", {})
        
        # Información del correo original del gobierno (si existe)
        original_email_from = additional_data.get("original_email_from", "")
        original_email_subject = additional_data.get("original_email_subject", "")
        original_email_body = additional_data.get("original_email_body", "")
        original_email_date = additional_data.get("original_email_date", "")
        
        subject = f"Actualización de solicitud HPS - {data.get('document_number', 'N/A')}"
        
        body = f"""
Estimado/a {data.get('user_name', 'Usuario')},

Su solicitud HPS ha sido actualizada automáticamente.

Detalles de la solicitud:
- Número de documento: {data.get('document_number', 'N/A')}
- Tipo de solicitud: {data.get('request_type', 'N/A')}
- Estado anterior: {old_status}
- Nuevo estado: {new_status}

{StatusUpdateTemplate._get_status_message(new_status)}

---
CORREO ORIGINAL DEL GOBIERNO QUE DESENCADENÓ ESTE CAMBIO:
---
De: {original_email_from or 'N/A'}
Asunto: {original_email_subject or 'N/A'}
Fecha: {original_email_date or 'N/A'}

{original_email_body or 'No disponible'}
---

Este cambio de estado fue detectado automáticamente por el sistema al procesar el correo del gobierno mostrado arriba.

Si tiene alguna pregunta, no dude en contactarnos.

Atentamente,
Equipo HPS System
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Actualización de solicitud HPS</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }}
        .container {{ max-width: 700px; margin: 0 auto; padding: 20px; background-color: #ffffff; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .content {{ padding: 30px; }}
        .status-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
            margin: 10px 0;
        }}
        .status-pending {{ background-color: #ffc107; color: #000; }}
        .status-waiting_dps {{ background-color: #17a2b8; color: #fff; }}
        .status-submitted {{ background-color: #007bff; color: #fff; }}
        .status-approved {{ background-color: #28a745; color: #fff; }}
        .status-rejected {{ background-color: #dc3545; color: #fff; }}
        .status-expired {{ background-color: #6c757d; color: #fff; }}
        .details-box {{
            background-color: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .details-box h3 {{ margin-top: 0; color: #667eea; }}
        .details-box ul {{ margin: 10px 0; padding-left: 20px; }}
        .details-box li {{ margin: 8px 0; }}
        .status-message {{
            background-color: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #4caf50;
        }}
        .original-email {{
            background-color: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 8px;
            padding: 20px;
            margin: 30px 0;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }}
        .original-email-header {{
            background-color: #ffc107;
            color: #000;
            padding: 10px 15px;
            margin: -20px -20px 15px -20px;
            border-radius: 6px 6px 0 0;
            font-weight: bold;
        }}
        .original-email-meta {{
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #ddd;
        }}
        .original-email-meta p {{
            margin: 5px 0;
        }}
        .original-email-body {{
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.5;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
            border-top: 1px solid #ddd;
            margin-top: 30px;
        }}
        .info-note {{
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 12px;
            margin: 20px 0;
            border-radius: 4px;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Actualización de Solicitud HPS</h1>
        </div>
        
        <div class="content">
            <p>Estimado/a <strong>{data.get('user_name', 'Usuario')}</strong>,</p>
            
            <p>Su solicitud HPS ha sido actualizada automáticamente por el sistema.</p>
            
            <div class="details-box">
                <h3>📝 Detalles de la solicitud:</h3>
                <ul>
                    <li><strong>Número de documento:</strong> {data.get('document_number', 'N/A')}</li>
                    <li><strong>Tipo de solicitud:</strong> {data.get('request_type', 'N/A')}</li>
                    <li><strong>Estado anterior:</strong> <span class="status-badge status-{old_status}">{old_status}</span></li>
                    <li><strong>Nuevo estado:</strong> <span class="status-badge status-{new_status}">{new_status}</span></li>
                </ul>
            </div>
            
            <div class="status-message">
                <strong>ℹ️ Información:</strong><br>
                {StatusUpdateTemplate._get_status_message(new_status)}
            </div>
            
            <div class="original-email">
                <div class="original-email-header">
                    📧 CORREO ORIGINAL DEL GOBIERNO QUE DESENCADENÓ ESTE CAMBIO
                </div>
                <div class="original-email-meta">
                    <p><strong>De:</strong> {original_email_from or 'N/A'}</p>
                    <p><strong>Asunto:</strong> {original_email_subject or 'N/A'}</p>
                    <p><strong>Fecha:</strong> {original_email_date or 'N/A'}</p>
                </div>
                <div class="original-email-body">{original_email_body or 'No disponible'}</div>
            </div>
            
            <div class="info-note">
                <strong>ℹ️ Nota:</strong> Este cambio de estado fue detectado automáticamente por el sistema al procesar el correo del gobierno mostrado arriba. Puede verificar el contenido del correo original para confirmar que el cambio se ha efectuado correctamente.
            </div>
            
            <p>Si tiene alguna pregunta, no dude en contactarnos.</p>
            
            <p>Atentamente,<br>
            <strong>Equipo HPS System</strong></p>
        </div>
        
        <div class="footer">
            <p>Este es un correo automático, por favor no responda directamente.</p>
            <p>Sistema HPS - Gestión de Habilitaciones Personales de Seguridad</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return {
            "subject": subject,
            "body": body,
            "html_body": html_body
        }


class HpsApprovedTemplate:
    """Template para HPS aprobadas"""
    
    @staticmethod
    def get_template(data: Dict[str, Any]) -> Dict[str, str]:
        """
        Renderiza el template de HPS aprobada
        
        Args:
            data: Diccionario con user_name, user_email, document_number, request_type, 
                  expires_at (opcional), notes (opcional)
            
        Returns:
            Dict con subject, body y html_body
        """
        subject = f"¡Su solicitud HPS ha sido APROBADA! - {data.get('document_number', 'N/A')}"
        
        body = f"""
Estimado/a {data.get('user_name', 'Usuario')},

¡Nos complace informarle que su solicitud HPS ha sido APROBADA!

Detalles de la solicitud:
- Número de documento: {data.get('document_number', 'N/A')}
- Tipo de solicitud: {data.get('request_type', 'N/A')}
- Estado: APROBADA
- Fecha de expiración: {data.get('expires_at', 'N/A')}

{data.get('notes', '')}

Puede acceder al sistema para ver los detalles de su HPS.

Si tiene alguna pregunta, no dude en contactarnos.

Atentamente,
Equipo HPS System
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Solicitud HPS APROBADA</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .details {{ background-color: white; padding: 15px; border-left: 4px solid #28a745; margin: 15px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Solicitud HPS APROBADA</h1>
        </div>
        
        <div class="content">
            <p>Estimado/a <strong>{data.get('user_name', 'Usuario')}</strong>,</p>
            
            <p>¡Nos complace informarle que su solicitud HPS ha sido <strong>APROBADA</strong>!</p>
            
            <div class="details">
                <h3>Detalles de la solicitud:</h3>
                <ul>
                    <li><strong>Número de documento:</strong> {data.get('document_number', 'N/A')}</li>
                    <li><strong>Tipo de solicitud:</strong> {data.get('request_type', 'N/A')}</li>
                    <li><strong>Estado:</strong> APROBADA</li>
                    <li><strong>Fecha de expiración:</strong> {data.get('expires_at', 'N/A')}</li>
                </ul>
            </div>
            
            {f'<p>{data.get("notes", "")}</p>' if data.get('notes') else ''}
            
            <p>Puede acceder al sistema para ver los detalles de su HPS.</p>
            
            <p>Si tiene alguna pregunta, no dude en contactarnos.</p>
            
            <p>Atentamente,<br>
            <strong>Equipo HPS System</strong></p>
        </div>
        
        <div class="footer">
            <p>Este es un correo automático, por favor no responda directamente.</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return {
            "subject": subject,
            "body": body,
            "html_body": html_body
        }


class HpsRejectedTemplate:
    """Template para HPS rechazadas"""
    
    @staticmethod
    def get_template(data: Dict[str, Any]) -> Dict[str, str]:
        """
        Renderiza el template de HPS rechazada
        
        Args:
            data: Diccionario con user_name, user_email, document_number, request_type, 
                  rejection_reason (opcional), notes (opcional)
            
        Returns:
            Dict con subject, body y html_body
        """
        subject = f"Su solicitud HPS ha sido RECHAZADA - {data.get('document_number', 'N/A')}"
        
        body = f"""
Estimado/a {data.get('user_name', 'Usuario')},

Lamentamos informarle que su solicitud HPS ha sido RECHAZADA.

Detalles de la solicitud:
- Número de documento: {data.get('document_number', 'N/A')}
- Tipo de solicitud: {data.get('request_type', 'N/A')}
- Estado: RECHAZADA
- Motivo del rechazo: {data.get('rejection_reason', 'No especificado')}

{data.get('notes', '')}

Si tiene alguna pregunta o desea más información, no dude en contactarnos.

Atentamente,
Equipo HPS System
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Solicitud HPS RECHAZADA</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .details {{ background-color: white; padding: 15px; border-left: 4px solid #dc3545; margin: 15px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>❌ Solicitud HPS RECHAZADA</h1>
        </div>
        
        <div class="content">
            <p>Estimado/a <strong>{data.get('user_name', 'Usuario')}</strong>,</p>
            
            <p>Lamentamos informarle que su solicitud HPS ha sido <strong>RECHAZADA</strong>.</p>
            
            <div class="details">
                <h3>Detalles de la solicitud:</h3>
                <ul>
                    <li><strong>Número de documento:</strong> {data.get('document_number', 'N/A')}</li>
                    <li><strong>Tipo de solicitud:</strong> {data.get('request_type', 'N/A')}</li>
                    <li><strong>Estado:</strong> RECHAZADA</li>
                    <li><strong>Motivo del rechazo:</strong> {data.get('rejection_reason', 'No especificado')}</li>
                </ul>
            </div>
            
            {f'<p>{data.get("notes", "")}</p>' if data.get('notes') else ''}
            
            <p>Si tiene alguna pregunta o desea más información, no dude en contactarnos.</p>
            
            <p>Atentamente,<br>
            <strong>Equipo HPS System</strong></p>
        </div>
        
        <div class="footer">
            <p>Este es un correo automático, por favor no responda directamente.</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return {
            "subject": subject,
            "body": body,
            "html_body": html_body
        }


class ConfirmationTemplate:
    """Template para confirmación de solicitud HPS"""
    
    @staticmethod
    def get_template(data: Dict[str, Any]) -> Dict[str, str]:
        """
        Renderiza el template de confirmación de solicitud HPS
        
        Args:
            data: Diccionario con user_name, user_email, document_number, request_type, status
            
        Returns:
            Dict con subject, body y html_body
        """
        subject = f"Confirmación de Solicitud HPS - {data.get('request_type', 'N/A')}"
        
        body = f"""
Hola {data.get('user_name', 'Usuario')},

Tu solicitud HPS ha sido recibida correctamente.

Tipo: {data.get('request_type', 'N/A')}
Estado: {data.get('status', 'N/A')}
Número de documento: {data.get('document_number', 'N/A')}

Gracias por usar CryptoTrace HPS.
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Confirmación HPS</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Confirmación de Solicitud HPS</h1>
        <p>Hola <strong>{data.get('user_name', 'Usuario')}</strong>,</p>
        <p>Tu solicitud HPS ha sido recibida correctamente.</p>
        <p><strong>Tipo:</strong> {data.get('request_type', 'N/A')}</p>
        <p><strong>Estado:</strong> {data.get('status', 'N/A')}</p>
        <p><strong>Número de documento:</strong> {data.get('document_number', 'N/A')}</p>
        <p>Gracias por usar CryptoTrace HPS.</p>
    </div>
</body>
</html>
        """.strip()
        
        return {
            "subject": subject,
            "body": body,
            "html_body": html_body
        }


class HpsExpirationReminderTemplate:
    """Template para recordatorios de caducidad de HPS"""
    
    @staticmethod
    def get_template(data: Dict[str, Any]) -> Dict[str, str]:
        """
        Renderiza el template de recordatorio de caducidad
        Adaptado desde hps-system/backend/src/email/templates/hps_expiration_reminder.py
        
        Args:
            data: Diccionario con user_name, user_email, document_number, 
                  y additional_data con: expires_at, days_remaining, months_remaining,
                  security_clearance_level, company_name, renewal_url
        
        Returns:
            Dict con subject, body y html_body
        """
        # Extraer datos adicionales
        additional_data = data.get("additional_data", {})
        expires_at = additional_data.get('expires_at', 'No especificada')
        days_remaining = additional_data.get('days_remaining', 0)
        months_remaining = additional_data.get('months_remaining', 0)
        security_level = additional_data.get('security_clearance_level', 'No especificado')
        company_name = additional_data.get('company_name', 'No especificada')
        renewal_url = additional_data.get('renewal_url', '#')
        
        # Determinar el nivel de urgencia
        if days_remaining <= 30:
            urgency_level = "URGENTE"
            urgency_color = "#dc3545"
            urgency_icon = "🚨"
        elif days_remaining <= 90:
            urgency_level = "IMPORTANTE"
            urgency_color = "#fd7e14"
            urgency_icon = "⚠️"
        else:
            urgency_level = "INFORMATIVO"
            urgency_color = "#17a2b8"
            urgency_icon = "ℹ️"
        
        subject = f"Recordatorio: Su HPS caduca en {months_remaining} meses - {data.get('document_number', 'N/A')}"
        
        body = f"""
Estimado/a {data.get('user_name', 'Usuario')},

Le informamos que su HPS está próxima a caducar y necesita renovación.

Detalles de su HPS:
- Número de documento: {data.get('document_number', 'N/A')}
- Fecha de caducidad: {expires_at}
- Días restantes: {days_remaining} días (~{months_remaining} meses)
- Nivel de seguridad: {security_level}
- Empresa: {company_name}

{urgency_icon} NIVEL DE URGENCIA: {urgency_level}

Es importante que inicie el proceso de renovación con suficiente antelación para evitar interrupciones en su acceso a información clasificada.

Recomendamos iniciar el proceso de renovación al menos 3 meses antes de la fecha de caducidad.

🔗 ENLACE DE RENOVACIÓN:
{renewal_url}

Este enlace es válido por 72 horas y le permitirá iniciar el proceso de renovación de su HPS.

Si tiene alguna pregunta o necesita asistencia con el proceso de renovación, no dude en contactarnos.

Atentamente,
Equipo HPS System
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recordatorio de Caducidad HPS</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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
            background: linear-gradient(135deg, {urgency_color} 0%, #6c757d 100%);
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
        .urgency-banner {{
            background-color: {urgency_color};
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
            font-weight: bold;
            font-size: 16px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 20px 0;
        }}
        .info-item {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid {urgency_color};
        }}
        .info-label {{
            font-weight: bold;
            color: #495057;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}
        .info-value {{
            color: #212529;
            font-size: 14px;
        }}
        .countdown {{
            background: linear-gradient(135deg, {urgency_color}, #6c757d);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 20px 0;
        }}
        .countdown h3 {{
            margin: 0 0 10px 0;
            font-size: 18px;
        }}
        .countdown .days {{
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .recommendation {{
            background-color: #e8f4fd;
            border-left: 4px solid #007bff;
            padding: 20px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }}
        .recommendation h3 {{
            color: #007bff;
            margin-top: 0;
        }}
        .renewal-section {{
            background-color: #f8f9fa;
            border: 2px solid #007bff;
            border-radius: 10px;
            padding: 25px;
            margin: 25px 0;
            text-align: center;
        }}
        .renewal-section h3 {{
            color: #007bff;
            margin-top: 0;
            margin-bottom: 15px;
        }}
        .renewal-link {{
            margin: 20px 0;
        }}
        .renewal-button {{
            display: inline-block;
            background: linear-gradient(135deg, #007bff, #0056b3);
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
            font-size: 16px;
            box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
            transition: all 0.3s ease;
        }}
        .renewal-button:hover {{
            background: linear-gradient(135deg, #0056b3, #004085);
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 123, 255, 0.4);
        }}
        .renewal-info {{
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin-top: 15px;
            border-radius: 0 8px 8px 0;
        }}
        .renewal-info p {{
            margin: 5px 0;
            color: #1565c0;
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
            <h1>{urgency_icon} Recordatorio de Caducidad HPS</h1>
        </div>
        
        <p>Estimado/a <strong>{data.get('user_name', 'Usuario')}</strong>,</p>
        
        <p>Le informamos que su HPS está próxima a caducar y necesita renovación.</p>
        
        <div class="urgency-banner">
            {urgency_icon} NIVEL DE URGENCIA: {urgency_level}
        </div>
        
        <div class="countdown">
            <h3>⏰ Tiempo Restante</h3>
            <div class="days">{days_remaining}</div>
            <div>días restantes</div>
            <div>(~{months_remaining} meses)</div>
        </div>
        
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Número de Documento</div>
                <div class="info-value">{data.get('document_number', 'N/A')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Fecha de Caducidad</div>
                <div class="info-value">{expires_at}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Nivel de Seguridad</div>
                <div class="info-value">{security_level}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Empresa</div>
                <div class="info-value">{company_name}</div>
            </div>
        </div>
        
        <div class="recommendation">
            <h3>📋 Recomendaciones Importantes</h3>
            <ul>
                <li><strong>Inicie el proceso de renovación con al menos 3 meses de antelación</strong></li>
                <li>Evite interrupciones en su acceso a información clasificada</li>
                <li>Mantenga actualizada su documentación personal</li>
                <li>Contacte con su administrador si necesita asistencia</li>
            </ul>
        </div>
        
        <div class="renewal-section">
            <h3>🔄 Proceso de Renovación</h3>
            <p>Para iniciar el proceso de renovación de su HPS, utilice el siguiente enlace:</p>
            
            <div class="renewal-link">
                <a href="{renewal_url}" class="renewal-button">
                    📋 INICIAR RENOVACIÓN HPS
                </a>
            </div>
            
            <div class="renewal-info">
                <p><strong>⏰ Este enlace es válido por 72 horas</strong></p>
                <p>El enlace le llevará directamente al formulario de renovación donde podrá completar todos los datos necesarios.</p>
            </div>
        </div>
        
        <p>Si tiene alguna pregunta o necesita asistencia con el proceso de renovación, no dude en contactarnos.</p>
        
        <p>Atentamente,<br>
        <strong>Equipo HPS System</strong></p>
        
        <div class="footer">
            <p>Este es un correo automático de recordatorio. Por favor, no responda directamente.</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return {
            "subject": subject,
            "body": body,
            "html_body": html_body
        }


class HpsFormTemplate:
    """Template para formularios HPS"""
    
    @staticmethod
    def get_template(data: Dict[str, Any]) -> Dict[str, str]:
        """
        Renderiza el template de formulario HPS
        Adaptado desde hps-system/backend/src/email/templates/hps_form.py
        
        Args:
            data: Diccionario con user_name, user_email, 
                  y additional_data con: form_url
        
        Returns:
            Dict con subject, body y html_body
        """
        additional_data = data.get("additional_data", {})
        form_url = additional_data.get('form_url', 'ENLACE_NO_DISPONIBLE')
        
        subject = "Formulario HPS - Acción Requerida"
        
        body = f"""
Hola {data.get('user_name', 'Usuario')},

Se ha generado un formulario HPS que necesita completar.

Por favor, acceda al siguiente enlace y rellene el formulario:

{form_url}

Este enlace es válido por 72 horas.

Gracias.

Equipo HPS
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Formulario HPS - Acción Requerida</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .form-link {{ background-color: #3498db; color: white; padding: 15px; text-align: center; margin: 20px 0; border-radius: 5px; }}
        .form-link a {{ color: white; text-decoration: none; font-weight: bold; font-size: 16px; }}
        .warning {{ background-color: #f39c12; color: white; padding: 10px; text-align: center; margin: 15px 0; border-radius: 5px; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Formulario HPS</h1>
        </div>
        
        <div class="content">
            <p>Hola <strong>{data.get('user_name', 'Usuario')}</strong>,</p>
            
            <p>Se ha generado un formulario HPS que necesita completar.</p>
            
            <div class="form-link">
                <a href="{form_url}">📋 ACCEDER AL FORMULARIO</a>
            </div>
            
            <div class="warning">
                ⏰ Este enlace es válido por 72 horas
            </div>
            
            <p>Gracias.</p>
            
            <p><strong>Equipo HPS</strong></p>
        </div>
        
        <div class="footer">
            <p>Este es un correo automático, por favor no responda directamente.</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return {
            "subject": subject,
            "body": body,
            "html_body": html_body
        }

