"""
Template para credenciales de usuario
Envía credenciales de acceso a nuevos usuarios
"""

from typing import Dict
from ..schemas import EmailTemplateData
from ...config.settings import settings


class UserCredentialsTemplate:
    """Template para credenciales de usuario"""
    
    @staticmethod
    def get_template(data: EmailTemplateData) -> Dict[str, str]:
        """
        Renderiza el template de credenciales de usuario
        
        Args:
            data: Datos del template
            
        Returns:
            Dict con subject, body y html_body
        """
        user_name = data.user_name
        user_email = data.user_email
        temp_password = data.additional_data.get("temp_password", "") if data.additional_data else ""
        login_url = data.additional_data.get("login_url", f"{settings.FRONTEND_URL}/login") if data.additional_data else f"{settings.FRONTEND_URL}/login"
        
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
                <div class="credential-value">{temp_password}</div>
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
