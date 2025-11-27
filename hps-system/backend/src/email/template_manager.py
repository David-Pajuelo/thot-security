"""
Gestor centralizado de templates de email
Sistema optimizado para manejar todos los templates de forma eficiente
"""

import logging
from typing import Dict, Any, Optional
from .schemas import EmailTemplateData, EmailTemplate

# Importar todos los templates
from .templates.reminder import ReminderTemplate
from .templates.new_user_notification import NewUserNotificationTemplate
from .templates.hps_form import HPSFormTemplate
from .templates.user_credentials import UserCredentialsTemplate
from .templates.hps_approved import HPSApprovedTemplate
from .templates.hps_rejected import HPSRejectedTemplate
from .templates.hps_expiration_reminder import HPSExpirationReminderTemplate
from .templates.status_update import StatusUpdateTemplate

logger = logging.getLogger(__name__)


class TemplateManager:
    """
    Gestor centralizado de templates de email
    Maneja todos los templates de forma eficiente sin necesidad de services individuales
    """
    
    # Registro de templates disponibles
    _templates = {
        EmailTemplate.REMINDER: ReminderTemplate,
        EmailTemplate.NEW_USER_NOTIFICATION: NewUserNotificationTemplate,
        EmailTemplate.HPS_FORM: HPSFormTemplate,
        EmailTemplate.USER_CREDENTIALS: UserCredentialsTemplate,
        EmailTemplate.HPS_APPROVED: HPSApprovedTemplate,
        EmailTemplate.HPS_REJECTED: HPSRejectedTemplate,
        EmailTemplate.HPS_EXPIRATION_REMINDER: HPSExpirationReminderTemplate,
        EmailTemplate.STATUS_UPDATE: StatusUpdateTemplate,
    }
    
    @classmethod
    def get_template(cls, template_name: str, data: EmailTemplateData) -> Dict[str, str]:
        """
        Obtiene un template renderizado de forma centralizada
        
        Args:
            template_name: Nombre del template
            data: Datos para renderizar
            
        Returns:
            Dict con subject, body y html_body
            
        Raises:
            ValueError: Si el template no existe
        """
        try:
            # Convertir string a enum si es necesario
            if isinstance(template_name, str):
                template_enum = EmailTemplate(template_name)
            else:
                template_enum = template_name
            
            # Obtener la clase del template
            template_class = cls._templates.get(template_enum)
            
            if not template_class:
                raise ValueError(f"Template '{template_enum.value}' no encontrado")
            
            # Renderizar el template
            result = template_class.get_template(data)
            
            logger.debug(f"Template '{template_enum.value}' renderizado exitosamente")
            return result
            
        except Exception as e:
            logger.error(f"Error renderizando template '{template_name}': {str(e)}")
            raise ValueError(f"Error renderizando template: {str(e)}")
    
    @classmethod
    def get_available_templates(cls) -> list:
        """
        Obtiene la lista de templates disponibles
        
        Returns:
            Lista de nombres de templates disponibles
        """
        return [template.value for template in cls._templates.keys()]
    
    @classmethod
    def register_template(cls, template_name: EmailTemplate, template_class):
        """
        Registra un nuevo template (para extensibilidad)
        
        Args:
            template_name: Nombre del template
            template_class: Clase del template
        """
        cls._templates[template_name] = template_class
        logger.info(f"Template '{template_name.value}' registrado")
    
    @classmethod
    def validate_template_data(cls, template_name: str, data: EmailTemplateData) -> bool:
        """
        Valida que los datos del template sean correctos
        
        Args:
            template_name: Nombre del template
            data: Datos a validar
            
        Returns:
            True si los datos son válidos
        """
        try:
            # Verificar que el template existe
            if template_name not in cls.get_available_templates():
                return False
            
            # Validaciones básicas
            if not data.user_name:
                logger.warning("user_name faltante en datos del template")
                return False
            
            if not data.user_email:
                logger.warning("user_email faltante en datos del template")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validando datos del template: {str(e)}")
            return False
    
    @classmethod
    def get_template_info(cls, template_name: str) -> Dict[str, Any]:
        """
        Obtiene información sobre un template
        
        Args:
            template_name: Nombre del template
            
        Returns:
            Dict con información del template
        """
        try:
            template_enum = EmailTemplate(template_name)
            template_class = cls._templates.get(template_enum)
            
            if not template_class:
                return {"exists": False, "error": f"Template '{template_name}' no encontrado"}
            
            return {
                "exists": True,
                "name": template_enum.value,
                "class": template_class.__name__,
                "module": template_class.__module__
            }
            
        except Exception as e:
            return {"exists": False, "error": str(e)}
    
    @classmethod
    def render_preview(cls, template_name: str, sample_data: Optional[EmailTemplateData] = None) -> Dict[str, str]:
        """
        Renderiza una vista previa del template con datos de muestra
        
        Args:
            template_name: Nombre del template
            sample_data: Datos de muestra (opcional)
            
        Returns:
            Dict con subject, body y html_body de la vista previa
        """
        try:
            # Crear datos de muestra si no se proporcionan
            if not sample_data:
                sample_data = EmailTemplateData(
                    user_name="Usuario de Prueba",
                    user_email="test@ejemplo.com",
                    document_number="12345678A",
                    request_type="nueva",
                    status="pending",
                    hps_request_id=1,
                    additional_data={
                        "team_name": "Equipo de Prueba",
                        "registration_date": "09/10/2025 14:30",
                        "created_by": "Admin Sistema"
                    }
                )
            
            return cls.get_template(template_name, sample_data)
            
        except Exception as e:
            logger.error(f"Error renderizando vista previa: {str(e)}")
            return {
                "subject": "Error en vista previa",
                "body": f"Error: {str(e)}",
                "html_body": f"<p>Error: {str(e)}</p>"
            }



