"""
Template de recordatorio para solicitudes HPS pendientes
"""

from typing import Dict, Any
from ..schemas import EmailTemplateData


class ReminderTemplate:
    """Template para recordatorios de solicitudes HPS"""
    
    @staticmethod
    def get_template(data: EmailTemplateData) -> Dict[str, str]:
        """
        Obtiene el template renderizado para recordatorio
        
        Args:
            data: Datos del template
            
        Returns:
            Dict con subject, body y html_body
        """
        subject = f"Recordatorio: Solicitud HPS pendiente - {data.document_number or 'N/A'}"
        
        body = f"""
Estimado/a {data.user_name},

Le recordamos que tiene una solicitud HPS pendiente de procesamiento.

Detalles de la solicitud:
- Número de documento: {data.document_number or 'N/A'}
- Tipo de solicitud: {data.request_type or 'N/A'}
- Estado: {data.status or 'Pendiente'}
- Fecha de solicitud: {data.additional_data.get('request_date', 'N/A')}

Por favor, revise el estado de su solicitud en el sistema.

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
            background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
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
        .reminder-box {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #ffc107;
        }}
        .reminder-box h3 {{
            margin-top: 0;
            color: #856404;
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
            color: #ffc107;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⏰ Recordatorio HPS</h1>
        </div>
        
        <p>Estimado/a <strong>{data.user_name}</strong>,</p>
        
        <div class="reminder-box">
            <h3>🔔 Solicitud Pendiente</h3>
            <p>Le recordamos que tiene una solicitud HPS pendiente de procesamiento. Por favor, revise el estado de su solicitud en el sistema.</p>
        </div>
        
        <div class="info-box">
            <h3>📋 Detalles de la Solicitud</h3>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Número de Documento</div>
                    <div class="info-value">{data.document_number or 'N/A'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Tipo de Solicitud</div>
                    <div class="info-value">{data.request_type or 'N/A'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Estado Actual</div>
                    <div class="info-value">{data.status or 'Pendiente'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Fecha de Solicitud</div>
                    <div class="info-value">{data.additional_data.get('request_date', 'N/A')}</div>
                </div>
            </div>
        </div>
        
        <p>Si tiene alguna pregunta sobre su solicitud, no dude en contactarnos.</p>
        
        <p>Atentamente,<br>
        <strong>Equipo HPS System</strong></p>
        
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



