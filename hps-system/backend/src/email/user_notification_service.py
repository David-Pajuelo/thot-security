"""
Servicio de notificaciones para usuarios
Maneja el envío de correos cuando se crean nuevos usuarios
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from .service import EmailService
from .schemas import EmailTemplateData, SendEmailRequest, EmailTemplate
from ..models.user import User
from ..models.team import Team

logger = logging.getLogger(__name__)


class UserNotificationService:
    """
    Servicio para notificaciones relacionadas con usuarios
    """
    
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
    
    def notify_new_user(self, new_user: User, created_by: User, db: Session) -> Dict[str, Any]:
        """
        Notifica a jefes de seguridad y líderes de equipo sobre un nuevo usuario
        
        Args:
            new_user: Usuario recién creado
            created_by: Usuario que creó al nuevo usuario
            db: Sesión de base de datos
            
        Returns:
            Dict con resultados de las notificaciones
        """
        try:
            logger.info(f"Iniciando notificaciones para nuevo usuario: {new_user.email}")
            
            # Obtener destinatarios de notificación
            recipients = self._get_notification_recipients(new_user, db)
            
            if not recipients:
                logger.warning("No se encontraron destinatarios para notificación")
                return {
                    "success": False,
                    "message": "No se encontraron destinatarios para notificación",
                    "notifications_sent": 0
                }
            
            # Preparar datos del template
            template_data = self._prepare_template_data(new_user, created_by, db)
            
            # Enviar notificaciones
            notifications_sent = 0
            errors = []
            
            for recipient in recipients:
                try:
                    # Personalizar datos para cada destinatario
                    recipient_data = template_data.copy()
                    recipient_data["recipient_name"] = f"{recipient.first_name} {recipient.last_name}"
                    recipient_data["recipient_email"] = recipient.email
                    recipient_data["additional_data"]["recipient_role"] = recipient.role.name
                    
                    # Crear request de envío
                    send_request = SendEmailRequest(
                        to=recipient.email,
                        template=EmailTemplate.NEW_USER_NOTIFICATION,  # Usar template de notificación de nuevo usuario
                        template_data=EmailTemplateData(**recipient_data)
                    )
                    
                    # Enviar correo
                    response = self.email_service.send_email_with_template(send_request, db)
                    
                    if response.success:
                        notifications_sent += 1
                        logger.info(f"Notificación enviada a {recipient.email}")
                    else:
                        error_msg = f"Error enviando a {recipient.email}: {response.error}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        
                except Exception as e:
                    error_msg = f"Error procesando notificación para {recipient.email}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            logger.info(f"Notificaciones completadas: {notifications_sent} enviadas, {len(errors)} errores")
            
            return {
                "success": notifications_sent > 0,
                "message": f"Notificaciones enviadas: {notifications_sent}/{len(recipients)}",
                "notifications_sent": notifications_sent,
                "total_recipients": len(recipients),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error en notificación de nuevo usuario: {str(e)}")
            return {
                "success": False,
                "message": f"Error en notificación: {str(e)}",
                "notifications_sent": 0,
                "errors": [str(e)]
            }
    
    def _get_notification_recipients(self, new_user: User, db: Session) -> List[User]:
        """
        Obtiene la lista de destinatarios para notificación de nuevo usuario
        
        Args:
            new_user: Usuario recién creado
            db: Sesión de base de datos
            
        Returns:
            Lista de usuarios que deben recibir la notificación (puede incluir objetos User o dicts con email)
        """
        recipients = []
        
        try:
            # 1. Jefes de Seguridad - enviar a email fijo compartido
            # IMPORTANTE: NO se consulta la BD para jefes de seguridad
            # Se envía SIEMPRE un único correo a este email, sin importar cuántos
            # usuarios con rol jefe_seguridad o jefe_seguridad_suplente existan en la BD
            # REGLA: 1 evento = 1 correo a este email
            security_chiefs_email = "pajuelodev@gmail.com"
            
            # Crear un objeto simple para representar el email de jefes de seguridad
            # Esto permite mantener la compatibilidad con el código existente
            class SecurityChiefRecipient:
                def __init__(self, email):
                    self.email = email
                    self.first_name = "Jefes"
                    self.last_name = "de Seguridad"
                    self.role = type('Role', (), {'name': 'jefe_seguridad'})()
            
            # Agregar UN SOLO destinatario para jefes de seguridad (email fijo)
            security_chief_recipient = SecurityChiefRecipient(security_chiefs_email)
            recipients.append(security_chief_recipient)
            logger.info(f"Email de jefes de seguridad configurado: {security_chiefs_email} (1 evento = 1 correo)")
            
            # NOTA: Ya no se notifica a líderes de equipo, solo a jefes de seguridad
            
            # 2. Admin (si no hay otros destinatarios - fallback)
            if not recipients:
                admin_users = db.query(User).join(User.role).filter(
                    User.role.has(name="admin"),
                    User.is_active == True
                ).all()
                
                recipients.extend(admin_users)
                logger.info(f"Admins encontrados: {len(admin_users)}")
            
            # Eliminar duplicados por email (garantiza que cada email reciba solo 1 correo)
            # Esto es especialmente importante para asegurar que el email de jefes de seguridad
            # solo reciba un correo por evento, incluso si por algún error se agregara múltiples veces
            seen_emails = set()
            unique_recipients = []
            for recipient in recipients:
                recipient_email = recipient.email if hasattr(recipient, 'email') else str(recipient)
                if recipient_email not in seen_emails:
                    seen_emails.add(recipient_email)
                    unique_recipients.append(recipient)
                else:
                    logger.warning(f"Email duplicado detectado y eliminado: {recipient_email}")
            
            recipients = unique_recipients
            
            logger.info(f"Total destinatarios para notificación: {len(recipients)}")
            return recipients
            
        except Exception as e:
            logger.error(f"Error obteniendo destinatarios: {str(e)}")
            return []
    
    def _prepare_template_data(self, new_user: User, created_by: User, db: Session) -> Dict[str, Any]:
        """
        Prepara los datos para el template de notificación
        
        Args:
            new_user: Usuario recién creado
            created_by: Usuario que creó al nuevo usuario
            db: Sesión de base de datos
            
        Returns:
            Dict con datos para el template
        """
        try:
            # Obtener información del equipo
            team_name = "Sin equipo"
            if new_user.team_id:
                team = db.query(Team).filter(Team.id == new_user.team_id).first()
                if team:
                    team_name = team.name
            
            # Preparar datos del template
            template_data = {
                "user_name": f"{new_user.first_name} {new_user.last_name}",
                "user_email": new_user.email,
                "recipient_name": "",  # Se personalizará para cada destinatario
                "recipient_email": "",  # Se personalizará para cada destinatario
                "additional_data": {
                    "user_role": new_user.role.name,
                    "team_name": team_name,
                    "registration_date": datetime.utcnow().strftime("%d/%m/%Y %H:%M"),
                    "created_by": f"{created_by.first_name} {created_by.last_name}",
                    "recipient_role": ""  # Se personalizará para cada destinatario
                }
            }
            
            return template_data
            
        except Exception as e:
            logger.error(f"Error preparando datos del template: {str(e)}")
            return {
                "user_name": f"{new_user.first_name} {new_user.last_name}",
                "user_email": new_user.email,
                "recipient_name": "",
                "recipient_email": "",
                "additional_data": {
                    "user_role": new_user.role.name,
                    "team_name": "N/A",
                    "registration_date": datetime.utcnow().strftime("%d/%m/%Y %H:%M"),
                    "created_by": f"{created_by.first_name} {created_by.last_name}",
                    "recipient_role": ""
                }
            }



