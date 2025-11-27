"""
Template para formularios HPS
Envía enlaces a formularios de solicitud HPS
"""

from typing import Dict
from ..schemas import EmailTemplateData


class HPSFormTemplate:
    """Template para formularios HPS"""
    
    @staticmethod
    def get_template(data: EmailTemplateData) -> Dict[str, str]:
        """
        Renderiza el template de formulario HPS
        
        Args:
            data: Datos del template
            
        Returns:
            Dict con subject, body y html_body
        """
        subject = "Formulario HPS - Acción Requerida"
        
        body = f"""
Hola {data.user_name},

Se ha generado un formulario HPS que necesita completar.

Por favor, acceda al siguiente enlace y rellene el formulario:

{data.additional_data.get('form_url', 'ENLACE_NO_DISPONIBLE') if data.additional_data else 'ENLACE_NO_DISPONIBLE'}

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
            <p>Hola <strong>{data.user_name}</strong>,</p>
            
            <p>Se ha generado un formulario HPS que necesita completar.</p>
            
            <div class="form-link">
                <a href="{data.additional_data.get('form_url', '#') if data.additional_data else '#'}">📋 ACCEDER AL FORMULARIO</a>
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
