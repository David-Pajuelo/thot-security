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
            "Solicitar traspaso HPS para un miembro",
            "Estado de mi equipo",
            "¿Hay HPS pendientes en mi equipo?"
        ],
        "jefe_seguridad_suplente": [
            "¿Qué comandos puedes ejecutar?",
            "Dame un resumen de todas las HPS",
            "Solicitar traspaso HPS para un miembro",
            "Estado de mi equipo",
            "¿Hay HPS pendientes en mi equipo?"
        ],
        "crypto": [
            "¿Qué comandos puedes ejecutar?",
            "Estado de mi equipo",
            "Solicitar HPS para un miembro",
            "¿Hay HPS pendientes en mi equipo?",
            "Renovar HPS de un miembro"
        ],
        "team_lead": [
            "¿Qué comandos puedes ejecutar?",
            "Estado de mi equipo",
            "Solicitar HPS para un miembro",
            "¿Hay HPS pendientes en mi equipo?",
            "Renovar HPS de un miembro"
        ],
        "team_leader": [
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
        "crypto": "¡Hola {user_name}! 👋 Soy tu asistente de HPS. Como especialista en crypto, puedes gestionar HPS y operaciones criptográficas.",
        "team_lead": "¡Hola {user_name}! 👋 Soy tu asistente de HPS. Como jefe de equipo, puedes gestionar tu equipo y sus HPS.",
        "team_leader": "¡Hola {user_name}! 👋 Soy tu asistente de HPS. Como jefe de equipo, puedes gestionar tu equipo y sus HPS.",
        "member": "¡Hola {user_name}! 👋 Soy tu asistente de HPS. Estoy aquí para ayudarte con todo lo relacionado con tu habilitación personal de seguridad."
    }
    
    @classmethod
    def get_suggestions_by_role(cls, user_role: str) -> List[str]:
        """
        Obtener sugerencias según el rol del usuario.
        
        Args:
            user_role: Rol del usuario (member, admin, team_lead, team_leader)
            
        Returns:
            Lista de sugerencias para el rol o sugerencias por defecto (member)
        """
        role = user_role.lower()
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
        role = user_role.lower()
        message_template = cls.WELCOME_MESSAGES.get(role, cls.WELCOME_MESSAGES["member"])
        return message_template.format(user_name=user_name)
    
    @classmethod
    def add_role_config(cls, role: str, suggestions: List[str], welcome_message: str):
        """
        Agregar configuración para un nuevo rol.
        
        Args:
            role: Nombre del rol
            suggestions: Lista de sugerencias para el rol
            welcome_message: Mensaje de bienvenida para el rol
        """
        cls.SUGGESTIONS_BY_ROLE[role.lower()] = suggestions
        cls.WELCOME_MESSAGES[role.lower()] = welcome_message
    
    @classmethod
    def update_role_suggestions(cls, role: str, suggestions: List[str]):
        """
        Actualizar sugerencias para un rol existente.
        
        Args:
            role: Nombre del rol
            suggestions: Nueva lista de sugerencias
        """
        cls.SUGGESTIONS_BY_ROLE[role.lower()] = suggestions
    
    @classmethod
    def update_role_welcome_message(cls, role: str, welcome_message: str):
        """
        Actualizar mensaje de bienvenida para un rol existente.
        
        Args:
            role: Nombre del rol
            welcome_message: Nuevo mensaje de bienvenida
        """
        cls.WELCOME_MESSAGES[role.lower()] = welcome_message
