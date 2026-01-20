"""
Configuración centralizada de roles y sugerencias para el Agente IA
"""
from typing import Dict, List


class RoleConfig:
    """Configuración centralizada para roles del sistema HPS"""
    
    # Configuración de sugerencias por rol
    SUGGESTIONS_BY_ROLE: Dict[str, List[str]] = {
        "member": [
            "Información sobre HPS",
            "¿Cuál es el estado de mi HPS?"
        ],
        "admin": [
            "¿Qué comandos puedes ejecutar?",
            "Dame un resumen de todas las HPS",
            "Crear nuevo usuario",
            "Modificar rol de usuario",
            "Listar todos los equipos"
        ],
        "jefe_seguridad": [
            "¿Qué comandos puedes ejecutar?",
            "Dame un resumen de todas las HPS",
            "Ver HPS pendientes",
            "Enviar solicitud HPS",
            "Enviar solicitud de traspaso HPS",
            "¿Hay HPS pendientes en mi equipo?"
        ],
        "jefe_seguridad_suplente": [
            "¿Qué comandos puedes ejecutar?",
            "Dame un resumen de todas las HPS",
            "Ver HPS pendientes",
            "Enviar solicitud HPS",
            "Enviar solicitud de traspaso HPS",
            "¿Hay HPS pendientes en mi equipo?"
        ],
        "crypto": [
            "¿Qué comandos puedes ejecutar?",
            "¿Cuál es el estado de mi HPS?"
        ],
        "team_lead": [
            "¿Qué comandos puedes ejecutar?",
            "Estado de mi equipo",
            "Solicitar HPS para un miembro",
            "¿Hay HPS pendientes en mi equipo?",
            "Renovar HPS de un miembro"
        ]
    }
    
    # Mensajes de bienvenida por rol
    WELCOME_MESSAGES: Dict[str, str] = {
        "admin": "¡Hola {user_name}! 👋 Soy tu asistente de HPS. Como administrador, puedes gestionar usuarios, equipos y HPS del sistema.",
        "jefe_seguridad": "¡Hola {user_name}! 👋 Soy tu asistente de HPS. Como jefe de seguridad, puedes gestionar HPS y supervisar la seguridad del sistema.",
        "jefe_seguridad_suplente": "¡Hola {user_name}! 👋 Soy tu asistente de HPS. Como jefe de seguridad suplente, puedes gestionar HPS y supervisar la seguridad del sistema.",
        "crypto": "¡Hola {user_name}! 👋 Soy tu asistente de HPS. Como especialista en crypto, puedes consultar información sobre tu propia HPS.",
        "team_lead": "¡Hola {user_name}! 👋 Soy tu asistente de HPS. Como jefe de equipo, puedes gestionar tu equipo y sus HPS.",
        "member": "¡Hola {user_name}! 👋 Soy tu asistente de HPS. Estoy aquí para ayudarte con todo lo relacionado con tu habilitación personal de seguridad."
    }
    
    @classmethod
    def get_suggestions_by_role(cls, user_role: str) -> List[str]:
        """
        Obtener sugerencias según el rol del usuario.
        
        Args:
            user_role: Rol del usuario (member, admin, team_lead)
            
        Returns:
            Lista de sugerencias para el rol o sugerencias por defecto (member)
        """
        role = user_role.lower() if user_role else "member"
        return cls.SUGGESTIONS_BY_ROLE.get(role, cls.SUGGESTIONS_BY_ROLE["member"])
    
    @classmethod
    def get_welcome_message(cls, user_role: str, user_name: str) -> str:
        """
        Obtener mensaje de bienvenida según el rol del usuario.
        
        Args:
            user_role: Rol del usuario
            user_name: Nombre del usuario
            
        Returns:
            Mensaje de bienvenida personalizado
        """
        role = user_role.lower() if user_role else "member"
        message_template = cls.WELCOME_MESSAGES.get(role, cls.WELCOME_MESSAGES["member"])
        return message_template.format(user_name=user_name or "Usuario")

