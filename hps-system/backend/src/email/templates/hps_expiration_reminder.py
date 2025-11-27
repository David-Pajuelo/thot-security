"""
Template para recordatorios de caducidad de HPS
Envía notificaciones cuando una HPS está próxima a caducar
"""

from typing import Dict
from ..schemas import EmailTemplateData


class HPSExpirationReminderTemplate:
    """Template para recordatorios de caducidad de HPS"""
    
    @staticmethod
    def get_template(data: EmailTemplateData) -> Dict[str, str]:
        """
        Renderiza el template de recordatorio de caducidad
        
        Args:
            data: Datos del template
            
        Returns:
            Dict con subject, body y html_body
        """
        # Extraer datos adicionales
        expires_at = data.additional_data.get('expires_at', 'No especificada') if data.additional_data else 'No especificada'
        days_remaining = data.additional_data.get('days_remaining', 0) if data.additional_data else 0
        months_remaining = data.additional_data.get('months_remaining', 0) if data.additional_data else 0
        security_level = data.additional_data.get('security_clearance_level', 'No especificado') if data.additional_data else 'No especificado'
        company_name = data.additional_data.get('company_name', 'No especificada') if data.additional_data else 'No especificada'
        renewal_url = data.additional_data.get('renewal_url', '#') if data.additional_data else '#'
        
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
        
        subject = f"Recordatorio: Su HPS caduca en {months_remaining} meses - {data.document_number or 'N/A'}"
        
        body = f"""
Estimado/a {data.user_name},

Le informamos que su HPS está próxima a caducar y necesita renovación.

Detalles de su HPS:
- Número de documento: {data.document_number or 'N/A'}
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
        
        <p>Estimado/a <strong>{data.user_name}</strong>,</p>
        
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
                <div class="info-value">{data.document_number or 'N/A'}</div>
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
