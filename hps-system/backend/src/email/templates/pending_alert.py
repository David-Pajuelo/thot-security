"""
Template para alerta de HPS en estado pending que aparece en PDF del gobierno
"""

from typing import Dict
from ..schemas import EmailTemplateData


class PendingAlertTemplate:
    """Template para alerta de HPS en estado pending que aparece en PDF del gobierno"""
    
    @staticmethod
    def get_template(data: EmailTemplateData) -> Dict[str, str]:
    """Template para alerta de HPS en estado pending que aparece en PDF del gobierno"""
    subject = f"🚨 ALERTA: HPS en estado 'pending' aparece en PDF del gobierno - {data.document_number or 'N/A'}"
    
    body = f"""
ALERTA DEL SISTEMA HPS

Se ha detectado un caso anómalo que requiere su atención:

Una solicitud HPS que estaba en estado 'pending' ha aparecido en un PDF oficial del gobierno, lo que indica que se saltó algún paso del proceso normal.

DETALLES DEL CASO:
- Usuario: {data.user_name}
- Email: {data.user_email}
- DNI: {data.document_number}
- ID HPS: {data.hps_request_id}
- Estado anterior: {data.old_status}
- Nuevo estado: {data.new_status}
- Archivo PDF: {data.pdf_filename}
- Expediente gobierno: {data.government_expediente}
- Grado/Especialidad: {data.security_clearance_level}
- Fecha de caducidad: {data.expires_at}
- Fecha de aprobación: {data.approved_at}

ACCIÓN REQUERIDA:
Por favor, revise este caso para determinar:
1. ¿Por qué no se detectaron las actualizaciones intermedias?
2. ¿Es necesario ajustar el sistema de monitoreo?
3. ¿Hay otros casos similares que requieran revisión?

El sistema ha actualizado automáticamente el estado, pero se recomienda una revisión manual.

Atentamente,
Sistema HPS Automático
    """.strip()
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🚨 ALERTA: HPS Pending en PDF Gobierno</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #dc3545; color: white; padding: 25px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ padding: 25px; background-color: #f8f9fa; border: 1px solid #dee2e6; }}
        .alert-box {{ background-color: #fff3cd; border: 2px solid #ffc107; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .details {{ background-color: white; padding: 20px; border-left: 5px solid #dc3545; margin: 20px 0; border-radius: 0 8px 8px 0; }}
        .action-required {{ background-color: #e3f2fd; border: 2px solid #2196f3; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        .highlight {{ background-color: #ffeb3b; padding: 2px 4px; border-radius: 3px; font-weight: bold; }}
        .status-badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .status-pending {{ background-color: #ffc107; color: #000; }}
        .status-approved {{ background-color: #28a745; color: white; }}
        .status-rejected {{ background-color: #dc3545; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 ALERTA DEL SISTEMA HPS</h1>
            <h2>HPS en estado 'pending' aparece en PDF del gobierno</h2>
        </div>
        
        <div class="content">
            <div class="alert-box">
                <h3>⚠️ CASO ANÓMALO DETECTADO</h3>
                <p>Se ha detectado una solicitud HPS que estaba en estado <span class="highlight">'pending'</span> pero ha aparecido en un PDF oficial del gobierno.</p>
                <p><strong>Esto indica que se saltó algún paso del proceso normal de monitoreo.</strong></p>
            </div>
            
            <div class="details">
                <h3>📋 Detalles del Caso:</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Usuario:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.user_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Email:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.user_email}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>DNI:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.document_number}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>ID HPS:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.hps_request_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Estado anterior:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><span class="status-badge status-pending">{data.old_status}</span></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Nuevo estado:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><span class="status-badge status-{'approved' if data.new_status == 'approved' else 'rejected'}">{data.new_status}</span></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Archivo PDF:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.pdf_filename}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Expediente gobierno:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.government_expediente}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Grado/Especialidad:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.security_clearance_level}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Fecha de caducidad:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.expires_at}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;"><strong>Fecha de aprobación:</strong></td>
                        <td style="padding: 8px;">{data.approved_at}</td>
                    </tr>
                </table>
            </div>
            
            <div class="action-required">
                <h3>🔍 ACCIÓN REQUERIDA</h3>
                <p>Por favor, revise este caso para determinar:</p>
                <ol>
                    <li><strong>¿Por qué no se detectaron las actualizaciones intermedias?</strong></li>
                    <li><strong>¿Es necesario ajustar el sistema de monitoreo?</strong></li>
                    <li><strong>¿Hay otros casos similares que requieran revisión?</strong></li>
                </ol>
                <p><strong>Nota:</strong> El sistema ha actualizado automáticamente el estado, pero se recomienda una revisión manual.</p>
            </div>
            
            <p>Atentamente,<br>
            <strong>Sistema HPS Automático</strong></p>
        </div>
        
        <div class="footer">
            <p>Este es un correo automático del sistema de monitoreo HPS.</p>
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
