"""
Template para HPS aprobadas
Notifica cuando una HPS ha sido aprobada
"""

from typing import Dict
from ..schemas import EmailTemplateData


class HPSApprovedTemplate:
    """Template para HPS aprobadas"""
    
    @staticmethod
    def get_template(data: EmailTemplateData) -> Dict[str, str]:
        """
        Renderiza el template de HPS aprobada
        
        Args:
            data: Datos del template
            
        Returns:
            Dict con subject, body y html_body
        """
        subject = f"¡Su solicitud HPS ha sido APROBADA! - {data.document_number or 'N/A'}"
        
        body = f"""
Estimado/a {data.user_name},

¡Nos complace informarle que su solicitud HPS ha sido APROBADA!

Detalles de la solicitud:
- Número de documento: {data.document_number or 'N/A'}
- Tipo de solicitud: {data.request_type or 'N/A'}
- Estado: APROBADA
- Fecha de expiración: {data.additional_data.get('expires_at', 'N/A') if data.additional_data else 'N/A'}

{data.additional_data.get('notes', '') if data.additional_data else ''}

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
            <p>Estimado/a <strong>{data.user_name}</strong>,</p>
            
            <p>¡Nos complace informarle que su solicitud HPS ha sido <strong>APROBADA</strong>!</p>
            
            <div class="details">
                <h3>Detalles de la solicitud:</h3>
                <ul>
                    <li><strong>Número de documento:</strong> {data.document_number or 'N/A'}</li>
                    <li><strong>Tipo de solicitud:</strong> {data.request_type or 'N/A'}</li>
                    <li><strong>Estado:</strong> APROBADA</li>
                    <li><strong>Fecha de expiración:</strong> {data.additional_data.get('expires_at', 'N/A') if data.additional_data else 'N/A'}</li>
                </ul>
            </div>
            
            <p>{data.additional_data.get('notes', '') if data.additional_data else ''}</p>
            
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
