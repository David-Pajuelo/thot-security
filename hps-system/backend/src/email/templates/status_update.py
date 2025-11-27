"""
Template para notificación de cambio de estado HPS
Incluye el correo original del gobierno que desencadenó el cambio
"""

from typing import Dict, Any
from ..schemas import EmailTemplateData


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
    def get_template(data: EmailTemplateData) -> Dict[str, str]:
        """
        Obtiene el template renderizado para notificación de cambio de estado
        
        Args:
            data: Datos del template con información de la HPS y el correo original
            
        Returns:
            Dict con subject, body y html_body
        """
        old_status = data.additional_data.get("old_status", "N/A") if data.additional_data else "N/A"
        new_status = data.status or "N/A"
        
        # Información del correo original del gobierno
        original_email_from = data.additional_data.get("original_email_from", "") if data.additional_data else ""
        original_email_subject = data.additional_data.get("original_email_subject", "") if data.additional_data else ""
        original_email_body = data.additional_data.get("original_email_body", "") if data.additional_data else ""
        original_email_date = data.additional_data.get("original_email_date", "") if data.additional_data else ""
        
        subject = f"Actualización de solicitud HPS - {data.document_number or 'N/A'}"
        
        # Cuerpo del correo en texto plano
        body = f"""
Estimado/a {data.user_name},

Su solicitud HPS ha sido actualizada automáticamente.

Detalles de la solicitud:
- Número de documento: {data.document_number or 'N/A'}
- Tipo de solicitud: {data.request_type or 'N/A'}
- Estado anterior: {old_status}
- Nuevo estado: {new_status}

{StatusUpdateTemplate._get_status_message(new_status)}

---
CORREO ORIGINAL DEL GOBIERNO QUE DESENCADENÓ ESTE CAMBIO:
---
De: {original_email_from}
Asunto: {original_email_subject}
Fecha: {original_email_date}

{original_email_body}
---

Este cambio de estado fue detectado automáticamente por el sistema al procesar el correo del gobierno mostrado arriba.

Si tiene alguna pregunta, no dude en contactarnos.

Atentamente,
Equipo HPS System
        """.strip()
        
        # Cuerpo del correo en HTML
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
            <p>Estimado/a <strong>{data.user_name}</strong>,</p>
            
            <p>Su solicitud HPS ha sido actualizada automáticamente por el sistema.</p>
            
            <div class="details-box">
                <h3>📝 Detalles de la solicitud:</h3>
                <ul>
                    <li><strong>Número de documento:</strong> {data.document_number or 'N/A'}</li>
                    <li><strong>Tipo de solicitud:</strong> {data.request_type or 'N/A'}</li>
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

