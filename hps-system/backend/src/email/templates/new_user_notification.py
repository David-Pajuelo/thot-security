"""
Template para notificación de nuevo usuario a jefes de seguridad y líderes de equipo
"""

from typing import Dict, Any
from ..schemas import EmailTemplateData


class NewUserNotificationTemplate:
    """Template para notificación de nuevo usuario"""
    
    @staticmethod
    def get_template(data: EmailTemplateData) -> Dict[str, str]:
        """
        Obtiene el template renderizado para notificación de nuevo usuario
        
        Args:
            data: Datos del template con información del usuario y destinatario
            
        Returns:
            Dict con subject, body y html_body
        """
        subject = f"Nuevo usuario registrado: {data.user_name}"
        
        body = f"""
Estimado/a {data.recipient_name},

Se ha registrado un nuevo usuario en el sistema HPS:

Detalles del nuevo usuario:
- Nombre: {data.user_name}
- Email: {data.user_email}
- Rol: {data.additional_data.get('user_role', 'N/A')}
- Equipo: {data.additional_data.get('team_name', 'N/A')}
- Fecha de registro: {data.additional_data.get('registration_date', 'N/A')}

El usuario ha sido creado por: {data.additional_data.get('created_by', 'Sistema')}

Puede acceder al sistema para gestionar este usuario.

Atentamente,
Equipo HPS System
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nuevo Usuario Registrado</title>
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
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
            border-left: 4px solid #667eea;
        }}
        .user-info h3 {{
            margin-top: 0;
            color: #667eea;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 15px 0;
        }}
        .info-item {{
            padding: 10px;
            background-color: white;
            border-radius: 5px;
            border: 1px solid #e9ecef;
        }}
        .info-label {{
            font-weight: bold;
            color: #495057;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .info-value {{
            color: #212529;
            font-size: 14px;
            margin-top: 5px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            color: #6c757d;
            font-size: 12px;
        }}
        .button {{
            display: inline-block;
            background-color: #667eea;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .role-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .role-admin {{ background-color: #dc3545; color: white; }}
        .role-jefe_seguridad {{ background-color: #fd7e14; color: white; }}
        .role-crypto {{ background-color: #ffc107; color: black; }}
        .role-team_lead {{ background-color: #0d6efd; color: white; }}
        .role-member {{ background-color: #198754; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔔 Nuevo Usuario Registrado</h1>
        </div>
        
        <p>Estimado/a <strong>{data.recipient_name}</strong>,</p>
        
        <p>Se ha registrado un nuevo usuario en el sistema HPS que requiere su atención:</p>
        
        <div class="user-info">
            <h3>👤 Información del Nuevo Usuario</h3>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Nombre Completo</div>
                    <div class="info-value">{data.user_name}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Email</div>
                    <div class="info-value">{data.user_email}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Rol Asignado</div>
                    <div class="info-value">
                        <span class="role-badge role-{data.additional_data.get('user_role', 'member')}">
                            {data.additional_data.get('user_role', 'N/A')}
                        </span>
                    </div>
                </div>
                <div class="info-item">
                    <div class="info-label">Equipo</div>
                    <div class="info-value">{data.additional_data.get('team_name', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Fecha de Registro</div>
                    <div class="info-value">{data.additional_data.get('registration_date', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Creado por</div>
                    <div class="info-value">{data.additional_data.get('created_by', 'Sistema')}</div>
                </div>
            </div>
        </div>
        
        <p>Como <strong>{data.additional_data.get('recipient_role', 'supervisor')}</strong>, puede acceder al sistema para gestionar este usuario y asignar las responsabilidades correspondientes.</p>
        
        <p>Si tiene alguna pregunta sobre este nuevo usuario, no dude en contactarnos.</p>
        
        <p>Atentamente,<br>
        <strong>Equipo HPS System</strong></p>
        
        <div class="footer">
            <p>Este es un correo automático del sistema HPS. Por favor, no responda directamente a este correo.</p>
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



