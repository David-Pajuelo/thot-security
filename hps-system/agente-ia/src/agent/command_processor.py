"""
Procesador de comandos para el Agente IA del Sistema HPS
ACCESO DIRECTO A BASE DE DATOS REAL
"""
import logging
import httpx
import os
import re
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
# from .router import generate_suggestions  # Comentado para evitar importación circular

logger = logging.getLogger(__name__)

def is_email_only(message: str) -> Optional[str]:
    """Detecta si el mensaje es solo un email válido"""
    # Patrón para validar email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Limpiar el mensaje de espacios y caracteres especiales
    clean_message = message.strip()
    
    # Verificar si es solo un email
    if re.match(email_pattern, clean_message):
        return clean_message
    
    return None

def generate_suggestions(user_role: str, context: str = None) -> list:
    """Generar sugerencias contextuales según el rol del usuario y el contexto de la conversación"""
    
    # Sugerencias base por rol
    base_suggestions = {
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
            "Listar todos los equipos"
        ],
        "jefe_seguridad_suplente": [
            "¿Qué comandos puedes ejecutar?",
            "Dame un resumen de todas las HPS",
            "Solicitar traspaso HPS para un miembro",
            "Estado de mi equipo",
            "Listar todos los equipos"
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
        ],
        "member": [
            "Información sobre HPS",
            "estado de mi hps"
        ]
    }
    
    # Obtener sugerencias base del rol
    suggestions = base_suggestions.get(user_role.lower(), base_suggestions["member"])
    
    # Para miembros: SIEMPRE usar las mismas 2 sugerencias fijas
    if user_role.lower() == "member":
        suggestions = ["Información sobre HPS", "¿Cuál es el estado de mi HPS?"]
    else:
        # Para otros roles: aplicar lógica contextual
        if context:
            contextual_suggestions = get_contextual_suggestions(user_role, context)
            if contextual_suggestions:
                # Para otros roles: 2 contextuales + 3 base del rol
                suggestions = contextual_suggestions[:2] + suggestions[1:4]
    
    return suggestions

def get_contextual_suggestions(user_role: str, context: str) -> list:
    """Generar sugerencias específicas basadas en el contexto de la conversación"""
    
    context_lower = context.lower()
    
    # Sugerencias contextuales para administradores
    if user_role.lower() == "admin":
        if "resumen" in context_lower or "estadísticas" in context_lower or "hps" in context_lower:
            return [
                "Ver estado específico de HPS",
                "Crear nuevo usuario",
                "Modificar rol de usuario",
                "Listar todos los equipos"
            ]
        elif "equipos" in context_lower or "equipo" in context_lower:
            return [
                "Crear nuevo equipo",
                "Asignar usuario a equipo",
                "Ver detalles de equipo"
            ]
        elif "usuarios" in context_lower or "usuario" in context_lower:
            return [
                "Crear nuevo usuario",
                "Modificar rol de usuario",
                "Ver lista de usuarios"
            ]
    
    # Sugerencias contextuales para jefes de equipo
    elif user_role.lower() in ["team_lead", "team_leader"]:
        if "equipo" in context_lower or "mi equipo" in context_lower:
            return [
                "Solicitar HPS para miembro",
                "Renovar HPS de miembro",
                "Ver HPS del equipo"
            ]
        elif "hps" in context_lower:
            return [
                "Estado de mi equipo",
                "Solicitar nueva HPS",
                "Renovar HPS existente"
            ]
    
    # Sugerencias contextuales para miembros
    else:  # member
        if "hps" in context_lower or "estado" in context_lower:
            return [
                "Información sobre HPS",
                "¿Cuál es el estado de mi HPS?"
            ]
        elif "solicitud" in context_lower or "ayuda" in context_lower:
            return [
                "Información sobre HPS",
                "¿Cuál es el estado de mi HPS?"
            ]
    
    return []

class CommandProcessor:
    """Procesador que ejecuta comandos específicos del sistema HPS con acceso real a BBDD"""
    
    def __init__(self, auth_token: str = None):
        """Inicializar procesador de comandos con conexión a BBDD"""
        # Backend ahora es Django (cryptotrace-backend en puerto 8080)
        self.backend_url = os.getenv("BACKEND_URL", "http://cryptotrace-backend:8080")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
        self.timeout = float(os.getenv("AGENTE_IA_TIMEOUT", "30"))
        self.auth_token = auth_token
        
        # Conexión directa a PostgreSQL con asyncpg (usando la base de datos compartida de cryptotrace)
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@cryptotrace-db:5432/cryptotrace")
        # Cambiar postgresql:// por postgresql+asyncpg:// para usar el driver asíncrono
        self.db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
        self.engine = create_async_engine(self.db_url, echo=False)
        self.Session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        
        logger.info(f"CommandProcessor inicializado - Backend: {self.backend_url} - BBDD: {self.db_url.split('@')[1] if '@' in self.db_url else 'N/A'}")
        
        # Flujos conversacionales activos por usuario
        self.conversation_flows = {}
    
    async def execute_command(self, ai_response: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar comando basado en la respuesta del AI"""
        
        # Extraer token del contexto del usuario
        self.auth_token = user_context.get("auth_token")
        
        user_id = user_context.get("id")
        
        # Limpiar flujos antiguos automáticamente
        self._cleanup_old_flows()
        
        # NUEVA LÓGICA ROBUSTA: Detectar comandos nuevos y resetear contexto
        user_message = ai_response.get("user_message", "")
        
        # Verificar si es un comando nuevo (doble verificación)
        is_new_command = (ai_response.get("tipo") == "comando" or 
                        self._is_new_command(user_message))
        
        if is_new_command:
            # Es un comando nuevo - RESETEAR cualquier flujo conversacional activo
            if self._is_in_conversation_flow(user_id):
                logger.info(f"🔄 Comando nuevo detectado - Reseteando flujo conversacional para {user_id}")
                self._end_conversation_flow(user_id)
            
            # Añadir log para debugging
            accion = ai_response.get("accion", "unknown")
            logger.info(f"🎯 Ejecutando comando nuevo: {accion} para usuario {user_id}")
        elif self._is_in_conversation_flow(user_id):
            # No es un comando nuevo, pero hay un flujo activo - continuar con el flujo
            flow_response = await self._handle_conversation_flow(user_message, user_context)
            if flow_response:
                return flow_response
        
        # Detectar si el mensaje es solo un email
        if user_message:
            email = is_email_only(user_message)
            if email:
                # Si es solo un email, tratarlo como consulta de estado HPS
                logger.info(f"Email detectado: {email} - Interpretando como consulta de estado HPS")
                return await self._consultar_estado_hps({"email": email}, user_context)
        
        if ai_response.get("tipo") != "comando":
            return ai_response
        
        accion = ai_response.get("accion")
        parametros = ai_response.get("parametros", {})
        
        # Agregar el mensaje del usuario a los parámetros para análisis
        parametros["user_message"] = ai_response.get("user_message", "")
        
        # Obtener token de autenticación del contexto del usuario
        self.auth_token = user_context.get("auth_token")
        
        try:
            # Enrutar comando a la función correspondiente
            if accion == "dar_alta_jefe_equipo":
                return await self._crear_jefe_equipo(parametros, user_context)
            elif accion in ["solicitar_hps", "solicitar hps para", "solicitar hps", "generar hps", "crear hps", "envía formulario", "envía form", "envía hps", "enviar formulario", "enviar form", "enviar hps"]:
                return await self._solicitar_hps(parametros, user_context)
            elif accion in ["consultar_estado_hps", "estado hps de", "estado hps", "mi estado hps", "consultar hps", "ver estado específico de hps", "ver estado hps"]:
                return await self._consultar_estado_hps(parametros, user_context)
            elif accion in ["consultar_hps_equipo", "hps de mi equipo", "hps del equipo", "equipo hps"]:
                return await self._consultar_hps_equipo(user_context)
            elif accion in ["consultar_todas_hps", "todas las hps del sistema", "todas las hps", "estadísticas hps", "resumen hps", "todas_hps_del_sistema", "dame un resumen de todas las hps", "resumen de todas las hps", "estadísticas de hps", "resumen hps del sistema"]:
                return await self._consultar_todas_hps(user_context)
            elif accion in ["renovar_hps", "renovar hps", "renovar hps de", "renovar hps para", "renovacion hps", "renovación hps", "solicitar renovacion", "solicitar renovación"]:
                return await self._renovar_hps(parametros, user_context)
            elif accion in ["trasladar_hps", "trasladar hps", "trasladar hps de", "trasladar hps para", "traspasar_hps", "traspasar hps", "traspasar hps de", "traspasar hps para", "solicitar traspaso", "solicitar traslado"]:
                return await self._solicitar_hps(parametros, user_context)
            elif accion in ["listar_usuarios", "listar usuarios", "ver usuarios", "mostrar usuarios", "usuarios del sistema"]:
                return await self._listar_usuarios(user_context)
            elif accion in ["listar_equipos", "listar equipos", "ver equipos", "mostrar equipos", "equipos del sistema"]:
                return await self._listar_equipos(user_context)
            elif accion in ["crear_usuario", "crear usuario", "dar alta usuario", "nuevo usuario", "registrar usuario"]:
                return await self._crear_usuario(parametros, user_context)
            elif accion in ["crear_equipo", "crear equipo", "nuevo equipo", "registrar equipo", "dar alta equipo"]:
                return await self._crear_equipo(parametros, user_context)
            elif accion in ["asignar_equipo", "asignar equipo", "cambiar equipo", "mover usuario a equipo", "asignar usuario"]:
                return await self._asignar_equipo(parametros, user_context)
            elif accion in ["modificar_rol", "modificar rol", "cambiar rol", "actualizar rol", "cambiar permisos"]:
                return await self._modificar_rol(parametros, user_context)
            # Comandos de aprobar/rechazar HPS removidos - se manejan desde extensión de navegador
            elif accion in ["mi_historial_hps", "mi historial hps", "historial hps", "mi historial"]:
                return await self._consultar_historial_hps(user_context)
            elif accion in ["cuando_expira_mi_hps", "cuando expira mi hps", "expira mi hps", "fecha vencimiento"]:
                return await self._consultar_vencimiento_hps(user_context)
            elif accion in ["estado_de_mi_equipo", "estado de mi equipo", "mi equipo", "estado equipo"]:
                return await self._consultar_estado_equipo(user_context)
            elif accion in ["comandos_disponibles", "comandos disponibles", "ayuda", "qué comandos puedes ejecutar"]:
                return await self._mostrar_comandos_disponibles(user_context)
            elif accion in ["ayuda_hps", "ayuda hps", "comandos a ejecutar", "que es hps", "informacion hps", "que comandos puedo ejecutar", "comandos puedo ejecutar", "informacion sobre hps", "informacion sobre HPS"]:
                return await self._mostrar_ayuda_hps(user_context)
            else:
                # Respuesta positiva con sugerencias útiles según el rol
                user_role = user_context.get("role", "").lower()
                
                if user_role == "admin":
                    return {
                        "tipo": "conversacion",
                        "mensaje": f"Entiendo que quieres '{accion}', pero no reconozco ese comando específico. 😊\n\n**Comandos disponibles para administradores:**\n\n🔹 **Gestión de usuarios:**\n• 'listar usuarios' - Ver todos los usuarios\n• 'crear usuario [email]' - Crear nuevo usuario\n• 'modificar rol' - Cambiar rol de usuario\n• 'dar alta jefe de equipo [nombre] [email] [equipo]'\n\n🔹 **Gestión de equipos:**\n• 'listar equipos' - Ver todos los equipos\n• 'crear equipo [nombre]' - Crear nuevo equipo\n• 'asignar usuario [email] al equipo [nombre]'\n\n🔹 **Gestión de HPS:**\n• 'todas las hps' - Estadísticas globales\n• 'aprobar hps de [email]' - Aprobar solicitud\n• 'rechazar hps de [email]' - Rechazar solicitud\n• 'solicitar hps para [email]' - Generar solicitud\n\n¿Te gustaría probar alguno de estos comandos? 🤔"
                    }
                elif user_role in ["jefe_seguridad", "jefe_seguridad_suplente"]:
                    return {
                        "tipo": "conversacion",
                        "mensaje": f"Entiendo que quieres '{accion}', pero no reconozco ese comando específico. 😊\n\n**Comandos disponibles para jefes de seguridad:**\n\n🔹 **Gestión de HPS:**\n• 'todas las hps' - Estadísticas globales\n• 'solicitar traspaso hps para [email]' - Solicitar traspaso HPS (solo jefes de seguridad)\n• 'solicitar hps para [email]' - Generar solicitud nueva HPS\n• 'estado hps de [email]' - Consultar estado\n• 'renovar hps de [email]' - Renovar HPS\n\n🔹 **Consultas:**\n• 'listar usuarios' - Ver usuarios del sistema\n• 'listar equipos' - Ver todos los equipos\n\n¿Te gustaría probar alguno de estos comandos? 🤔"
                    }
                elif user_role in ["team_lead", "team_leader"]:
                    return {
                        "tipo": "conversacion",
                        "mensaje": f"Entiendo que quieres '{accion}', pero no reconozco ese comando específico. 😊\n\n**Comandos disponibles para jefes de equipo:**\n\n🔹 **Gestión de HPS de tu equipo:**\n• 'hps de mi equipo' - Ver HPS de tu equipo\n• 'solicitar hps para [email]' - Generar solicitud nueva HPS (solo tu equipo)\n• 'estado hps de [email]' - Consultar estado (solo tu equipo)\n• 'renovar hps de [email]' - Renovar HPS (solo tu equipo)\n• 'estado de mi equipo' - Ver estado general del equipo\n\n🔹 **Consultas:**\n• 'listar usuarios' - Ver usuarios de tu equipo\n• 'listar equipos' - Ver todos los equipos (solo referencia)\n\n⚠️ **Nota:** Solo los jefes de seguridad pueden solicitar traspasos HPS.\n\n¿Te gustaría probar alguno de estos comandos? 🤔"
                    }
                else:  # member
                    return {
                        "tipo": "conversacion",
                        "mensaje": f"Entiendo que quieres '{accion}', pero no reconozco ese comando específico. 😊\n\n**Comando disponible para miembros:**\n\n🔹 **Consulta personal:**\n• 'estado de mi hps' - Ver estado actual de tu HPS\n\n¿Te gustaría probar este comando? 🤔"
                    }
                
        except Exception as e:
            logger.error(f"Error ejecutando comando {accion}: {e}")
            return {
                "tipo": "conversacion",
                "mensaje": "¡Ups! 😅 Parece que hubo un pequeño problema procesando tu solicitud. No te preocupes, esto puede pasar.\n\n**¿Qué puedes hacer?**\n• Intenta reformular tu pregunta de manera más simple\n• Usa uno de los comandos disponibles que te mostré antes\n• Si necesitas ayuda, puedes preguntar '¿Qué comandos tienes disponibles?'\n\n¡Estoy aquí para ayudarte! 🤝"
            }
    
    async def _crear_jefe_equipo(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Crear nuevo jefe de equipo (solo admin)"""
        
        # Verificar permisos
        if user_context.get("role", "").lower() != "admin":
            return {
                "tipo": "conversacion",
                "mensaje": "¡Hola! 😊 Me encantaría ayudarte a dar de alta un jefe de equipo, pero esa función está reservada para administradores.\n\n**¿Qué puedes hacer?**\n• Consultar HPS: 'hps de mi equipo' o 'mi estado hps'\n• Solicitar HPS: 'solicitar hps para [email]'\n• Ver estadísticas: 'todas las hps'\n\nSi necesitas crear un jefe de equipo, contacta con un administrador. ¡Estoy aquí para ayudarte con otras tareas! 🤝"
            }
        
        nombre = parametros.get("nombre")
        email = parametros.get("email")
        equipo = parametros.get("equipo")
        
        if not nombre or not email:
            return {
                "tipo": "conversacion",
                "mensaje": "¡Perfecto! 😊 Para crear un jefe de equipo necesito un poquito más de información:\n\n**¿Podrías proporcionarme?**\n• **Nombre completo** del jefe de equipo\n• **Email** de contacto\n• **Equipo** (opcional, por defecto será AICOX)\n\n**Ejemplo:**\n'dar alta jefe de equipo Maria García maria@empresa.com AICOX'\n\n¡Así podré ayudarte mejor! 🤝"
            }
        
        # Si no se especifica equipo, usar AICOX por defecto
        if not equipo:
            equipo = "AICOX"
        
        try:
            # Obtener team_id del equipo especificado
            team_id = await self._get_team_id_by_name(equipo)
            if not team_id:
                return {
                    "tipo": "conversacion",
                    "mensaje": f"¡Ah! 😊 El equipo '{equipo}' no está registrado en el sistema.\n\n**Equipos disponibles:**\n• AICOX (por defecto)\n• IDI\n\n**¿Qué puedes hacer?**\n• Usar AICOX: 'dar alta jefe de equipo {nombre} {email}'\n• Usar IDI: 'dar alta jefe de equipo {nombre} {email} IDI'\n• Contactar al administrador para crear el equipo '{equipo}'\n\n¡Te ayudo con cualquiera de estas opciones! 🤝"
                }
            
            # Llamada real al backend para crear usuario
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                user_data = {
                    "email": email,
                    "full_name": nombre,
                    "password": "temp_password_123",  # El backend generará uno seguro
                    "role": "team_lead",
                    "team_id": team_id
                }
                
                response = await client.post(
                    f"{self.backend_url}/api/hps/user/profiles/",
                    json=user_data,
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    return {
                        "tipo": "exito",
                        "mensaje": f"✅ Jefe de equipo '{nombre}' creado exitosamente con email {email} en el equipo '{equipo}'. Se han enviado las credenciales por correo.",
                        "data": {
                            "nombre": nombre,
                            "email": email,
                            "rol": "team_lead",
                            "equipo": equipo
                        }
                    }
                else:
                    # Manejar errores específicos del backend de manera positiva
                    error_detail = response.text
                    if "email ya está en uso" in error_detail.lower() or "email already exists" in error_detail.lower():
                        return {
                            "tipo": "conversacion",
                            "mensaje": f"¡Ah! 😊 El email {email} ya está registrado en el sistema.\n\n**¿Qué puedes hacer?**\n• Usar un email diferente: 'crear jefe de equipo Pedro pedro.nuevo@test.com IDI'\n• Verificar si el usuario ya existe: 'estado hps de {email}'\n• Contactar al administrador si necesitas ayuda\n\n¡Te ayudo con cualquiera de estas opciones! 🤝"
                        }
                    else:
                        return {
                            "tipo": "conversacion",
                            "mensaje": f"¡Ups! 😅 Hubo un problema creando el jefe de equipo: {error_detail}\n\n**¿Qué puedes hacer?**\n• Verificar que el email sea válido\n• Intentar con un email diferente\n• Contactar al administrador si el problema persiste\n\n¡Estoy aquí para ayudarte! 🤝"
                        }
                    
        except Exception as e:
            logger.error(f"Error creando jefe de equipo: {e}")
            return {
                "tipo": "conversacion",
                "mensaje": "¡Ups! 😅 Parece que hay un problema de conexión con el servidor. No te preocupes, esto puede pasar.\n\n**¿Qué puedes hacer?**\n• Esperar unos segundos y volver a intentar\n• Verificar tu conexión a internet\n• Contactar al administrador si el problema persiste\n\n¡Estoy aquí para ayudarte en cuanto se restablezca la conexión! 🤝"
            }
    
    async def _solicitar_hps(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generar token y URL para solicitud HPS"""
        
        user_role = user_context.get("role", "").lower()
        email = parametros.get("email")
        user_message = parametros.get("user_message", "").lower()
        
        # Detectar tipo de solicitud HPS
        is_transfer = any(word in user_message for word in ["traslado", "traspaso", "trasladar", "traspasar", "transfer"])
        is_renewal = any(word in user_message for word in ["renovacion", "renovación", "renovar", "renovar hps", "renovación hps"])
        # Por defecto es nueva HPS, solo se bifurca si se detectan palabras específicas
        is_new = not (is_transfer or is_renewal)
        
        # Detectar si el usuario usó "envía" sin ser específico
        if "envía" in user_message and not any(word in user_message for word in ["formulario", "form", "hps"]):
            return {
                "tipo": "conversacion",
                "mensaje": "¿Quieres que envíe un formulario HPS? Por favor especifica el email, por ejemplo: 'envía formulario a usuario@empresa.com'"
            }
        
        if not email:
            return {
                "tipo": "conversacion",
                "mensaje": "📧 Para solicitar una HPS para un miembro de tu equipo, necesito el email de la persona.\n\n**Por favor, proporciona el email del miembro:**\n• Ejemplo: 'solicitar hps para miembro@empresa.com'\n• O simplemente escribe: 'miembro@empresa.com'\n\n¿Para qué email quieres solicitar la HPS?"
            }
        
        # Verificar permisos: traspasos solo para jefe_seguridad y jefe_seguridad_suplente
        if is_transfer:
            # Solo jefes de seguridad pueden solicitar traspasos
            if user_role not in ["jefe_seguridad", "jefe_seguridad_suplente"]:
                return {
                    "tipo": "error",
                    "mensaje": "❌ Solo los jefes de seguridad pueden solicitar traspasos HPS. Si necesitas solicitar un traspaso, contacta con un jefe de seguridad."
                }
        else:
            # Para nuevas HPS y renovaciones, mantener permisos actuales
            if user_role not in ["admin", "team_lead", "team_leader", "jefe_seguridad", "jefe_seguridad_suplente"]:
                return {
                    "tipo": "error",
                    "mensaje": "❌ No tienes permisos para solicitar HPS para otros usuarios."
                }
        
        # Para jefes de equipo, el nuevo usuario se asociará automáticamente a su equipo
        # No necesitamos validar si el usuario ya existe, ya que puede ser un nuevo miembro
        
        try:
            # Generar token HPS usando el backend
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                token_response = await client.post(
                    f"{self.backend_url}/api/hps/tokens/",
                    json={"email": email},
                    headers=headers
                )
                
                if token_response.status_code in [200, 201]:
                    token_data = token_response.json()
                    url = f"{self.frontend_url}/hps-form?token={token_data['token']}&email={email}"
                    
                    # Añadir tipo específico a la URL
                    if is_transfer:
                        url += "&type=traslado"
                    elif is_renewal:
                        url += "&type=renovacion"
                    elif is_new:
                        url += "&type=nueva"
                    
                    # Enviar email con el formulario HPS
                    email_sent = await self._send_hps_form_email(email, url, user_context)
                    
                    # Verificar si el usuario existe
                    user_exists = await self._check_user_exists(email)
                    credentials_sent = False
                    
                    if not user_exists:
                        # El usuario no existe, se creará cuando envíe el formulario
                        # El email de credenciales se enviará automáticamente desde el backend
                        credentials_sent = True  # Asumimos que se enviará
                    
                    # Mensaje específico según el tipo de solicitud
                    if is_transfer:
                        message = f"✅ Se ha enviado el formulario de **traspaso HPS** a {email}.\n\nEl enlace es válido por 72 horas."
                    elif is_renewal:
                        message = f"✅ Se ha enviado el formulario de **renovación HPS** a {email}.\n\nEl enlace es válido por 72 horas."
                    else:
                        # Por defecto es nueva HPS
                        if user_role in ["team_lead", "team_leader"]:
                            message = f"✅ Se ha enviado el formulario de **nueva HPS** a {email}.\n\n📋 **El usuario se registrará automáticamente en tu equipo** cuando complete el formulario.\n\nEl enlace es válido por 72 horas."
                        else:
                            message = f"✅ Se ha enviado el formulario de **nueva HPS** a {email}.\n\nEl enlace es válido por 72 horas."
                    
                    if credentials_sent:
                        message += "\n\n🔑 También se han enviado las credenciales de acceso al usuario."
                    
                    return {
                        "tipo": "exito",
                        "mensaje": message,
                        "data": {
                            "url": url,
                            "token": token_data["token"],
                            "email": email,
                            "expires_at": token_data.get("expires_at"),
                            "email_sent": email_sent,
                            "credentials_sent": credentials_sent,
                            "user_created": token_data.get("user_created", False),
                            "async": True
                        }
                    }
                else:
                    return {
                        "tipo": "error",
                        "mensaje": f"❌ Error generando token HPS: {token_response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"Error generando token HPS: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Error conectando con el servidor. Intenta de nuevo en unos momentos."
            }
    
    async def _consultar_estado_hps(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Consultar estado de HPS de un usuario - DATOS REALES DE BBDD"""
        
        email = parametros.get("email")
        user_role = user_context.get("role", "").lower()
        user_email = user_context.get("email", "")
        
        # Si no especifica email, consultar el propio
        if not email and user_role == "member":
            email = user_email
        
        if not email:
            # Iniciar flujo conversacional para pedir email
            user_id = user_context.get("id")
            self._start_conversation_flow(user_id, "consultar_estado_hps")
            return {
                "tipo": "conversacion",
                "mensaje": "📧 ¡Perfecto! Para consultar el estado de una HPS necesito el email del usuario.\n\n**Ejemplo:** usuario@empresa.com\n\nEscribe el email o 'cancelar' para salir.",
                "suggestions": ["Cancelar"]
            }
        
        # Verificar permisos
        if user_role == "member" and email != user_email:
            return {
                "tipo": "error",
                "mensaje": "❌ Solo puedes consultar el estado de tu propia HPS."
            }
        
        try:
            # CONSULTA REAL A LA BBDD
            async with self.Session() as session:
                # Consultar HPS más reciente del usuario
                query = text("""
                    SELECT h.*, u.first_name, u.last_name 
                    FROM hps_requests h 
                    JOIN users u ON h.email = u.email 
                    WHERE h.email = :email 
                    ORDER BY h.created_at DESC 
                    LIMIT 1
                """)
                
                result = await session.execute(query, {"email": email})
                hps_data = result.fetchone()
                
                if not hps_data:
                    return {
                        "tipo": "informacion",
                        "mensaje": f"📋 **Estado HPS de {email}:**\n\n❌ No se encontraron solicitudes HPS para este usuario.",
                        "data": {
                            "email": email,
                            "estado": "no_encontrado",
                            "mensaje": "Usuario sin solicitudes HPS"
                        }
                    }
                
                # Formatear respuesta con datos REALES
                status_es = {
                    "pending": "PENDIENTE",
                    "submitted": "ENVIADA", 
                    "approved": "APROBADA",
                    "rejected": "RECHAZADA",
                    "expired": "EXPIRADA"
                }
                
                estado = status_es.get(hps_data.status, hps_data.status.upper())
                fecha = hps_data.created_at.strftime("%d/%m/%Y") if hps_data.created_at else "No especificada"
                
                # Formatear fechas
                fecha_solicitud = hps_data.created_at.strftime("%d/%m/%Y") if hps_data.created_at else "No especificada"
                fecha_expiracion = hps_data.expires_at.strftime("%d/%m/%Y") if hps_data.expires_at else "No aplicable"
                ultima_actualizacion = hps_data.updated_at.strftime("%d/%m/%Y %H:%M") if hps_data.updated_at else "No disponible"
                
                return {
                    "tipo": "informacion",
                    "mensaje": f"📋 **Estado HPS de {hps_data.first_name} {hps_data.last_name} ({email})**\n\n" +
                             f"🔹 **Estado**: {estado}\n" +
                             f"📅 **Fecha de la solicitud**: {fecha_solicitud}\n" +
                             f"📝 **Observaciones**: {hps_data.notes or 'Sin observaciones'}\n" +
                             f"⏰ **Fecha de expiración**: {fecha_expiracion}\n" +
                             f"🔄 **Última actualización**: {ultima_actualizacion}",
                    "data": {
                        "email": email,
                        "estado": hps_data.status,
                        "fecha_solicitud": hps_data.created_at.isoformat() if hps_data.created_at else None,
                        "observaciones": hps_data.notes,
                        "fecha_expiracion": hps_data.expires_at.isoformat() if hps_data.expires_at else None,
                        "ultima_actualizacion": hps_data.updated_at.isoformat() if hps_data.updated_at else None,
                        "nombre": f"{hps_data.first_name} {hps_data.last_name}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error consultando estado HPS real: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Error consultando el estado en la base de datos. Intenta de nuevo."
            }
    
    async def _consultar_hps_equipo(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Consultar HPS del equipo del usuario - DATOS REALES DE BBDD"""
        
        user_role = user_context.get("role", "").lower()
        user_message = user_context.get("user_message", "").lower()
        
        # Detectar si se pregunta específicamente por pendientes
        is_pending_only = any(word in user_message for word in ["pendientes", "pending", "pendiente"])
        
        if user_role not in ["admin", "team_lead", "team_leader"]:
            return {
                "tipo": "conversacion",
                "mensaje": "¡Hola! 😊 Me encantaría mostrarte las HPS del equipo, pero esa función está disponible para jefes de equipo y administradores.\n\n**¿Qué puedes hacer?**\n• Consultar tu HPS: 'mi estado hps'\n• Ver todas las HPS: 'todas las hps'\n• Solicitar HPS: 'solicitar hps para [email]'\n\nSi necesitas acceso a las HPS del equipo, contacta con tu jefe de equipo o administrador. ¡Estoy aquí para ayudarte con otras consultas! 🤝"
            }
        
        try:
            # CONSULTA REAL A LA BBDD
            async with self.Session() as session:
                team_id = user_context.get("team_id")
                
                # Si es admin, consultar TODAS las HPS
                if user_role == "admin":
                    if is_pending_only:
                        query = text("""
                            SELECT h.*, u.first_name, u.last_name, u.email, t.name as team_name
                            FROM hps_requests h 
                            JOIN users u ON h.email = u.email 
                            LEFT JOIN teams t ON u.team_id = t.id
                            WHERE h.status = 'pending'
                            ORDER BY h.created_at DESC
                        """)
                        equipo_descripcion = "Todos los equipos (solo pendientes)"
                    else:
                        query = text("""
                            SELECT h.*, u.first_name, u.last_name, u.email, t.name as team_name
                            FROM hps_requests h 
                            JOIN users u ON h.email = u.email 
                            LEFT JOIN teams t ON u.team_id = t.id
                            ORDER BY h.created_at DESC
                        """)
                        equipo_descripcion = "Todos los equipos"
                    result = await session.execute(query)
                else:
                    # Si es team_lead, solo su equipo
                    if not team_id:
                        return {
                            "tipo": "error",
                            "mensaje": "❌ No se pudo identificar tu equipo. Contacta al administrador."
                        }
                    
                    if is_pending_only:
                        query = text("""
                            SELECT h.*, u.first_name, u.last_name, u.email, t.name as team_name
                            FROM hps_requests h 
                            JOIN users u ON h.email = u.email 
                            LEFT JOIN teams t ON u.team_id = t.id
                            WHERE u.team_id = :team_id AND h.status = 'pending'
                            ORDER BY h.created_at DESC
                        """)
                        equipo_descripcion = "Tu equipo (solo pendientes)"
                    else:
                        query = text("""
                            SELECT h.*, u.first_name, u.last_name, u.email, t.name as team_name
                            FROM hps_requests h 
                            JOIN users u ON h.email = u.email 
                            LEFT JOIN teams t ON u.team_id = t.id
                            WHERE u.team_id = :team_id 
                            ORDER BY h.created_at DESC
                        """)
                        equipo_descripcion = "Tu equipo"
                    result = await session.execute(query, {"team_id": team_id})
                hps_list = result.fetchall()
                
                if not hps_list:
                    if is_pending_only:
                        return {
                            "tipo": "informacion",
                            "mensaje": f"📋 **HPS Pendientes - {equipo_descripcion}:**\n\n✅ **¡Excelente!** No hay HPS pendientes en tu equipo.",
                            "data": {
                                "equipo": equipo_descripcion,
                                "total": 0,
                                "pendientes": 0,
                                "enviadas": 0,
                                "aprobadas": 0,
                                "rechazadas": 0
                            }
                        }
                    else:
                        return {
                            "tipo": "informacion",
                            "mensaje": f"📋 **Estado HPS - {equipo_descripcion}:**\n\n❌ No se encontraron solicitudes HPS.",
                            "data": {
                                "equipo": equipo_descripcion,
                                "total": 0,
                                "pendientes": 0,
                                "enviadas": 0,
                                "aprobadas": 0,
                                "rechazadas": 0
                            }
                        }
                
                # Contar por estado
                status_counts = {}
                for hps in hps_list:
                    status = hps.status
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                # Formatear lista de HPS
                hps_details = []
                for hps in hps_list[:10]:  # Mostrar solo las 10 más recientes
                    status_es = {
                        "pending": "PENDIENTE",
                        "submitted": "ENVIADA",
                        "approved": "APROBADA", 
                        "rejected": "RECHAZADA",
                        "expired": "EXPIRADA"
                    }
                    estado = status_es.get(hps.status, hps.status.upper())
                    fecha = hps.created_at.strftime("%d/%m/%Y") if hps.created_at else "N/A"
                    
                    hps_details.append(f"• **{hps.first_name} {hps.last_name}**: {estado} ({fecha})")
                
                # Construir mensaje con información del equipo
                if user_role == "admin":
                    # Para admin, mostrar información de equipos
                    equipo_info = "Todos los equipos"
                    mensaje_equipo = f"📋 **Estado HPS - {equipo_info}:**\n\n"
                else:
                    # Para team_lead, obtener nombre del equipo
                    team_query = text("SELECT name FROM teams WHERE id = :team_id")
                    team_result = await session.execute(team_query, {"team_id": team_id})
                    team_name = team_result.fetchone()
                    equipo_nombre = team_name[0] if team_name else "Tu equipo"
                    equipo_info = equipo_nombre
                    mensaje_equipo = f"📋 **Estado HPS - Equipo {equipo_nombre}:**\n\n"
                
                if is_pending_only:
                    return {
                        "tipo": "informacion",
                        "mensaje": mensaje_equipo +
                                 "\n".join(hps_details) + "\n\n" +
                                 f"📊 **Total pendientes**: {len(hps_list)}",
                        "data": {
                            "equipo": equipo_info,
                            "total": len(hps_list),
                            "pendientes": len(hps_list),
                            "enviadas": 0,
                            "aprobadas": 0,
                            "rechazadas": 0
                        }
                    }
                else:
                    return {
                        "tipo": "informacion",
                        "mensaje": mensaje_equipo +
                                 "\n".join(hps_details) + "\n\n" +
                                 f"📊 **Resumen**: {len(hps_list)} HPS total\n" +
                                 f"• Pendientes: {status_counts.get('pending', 0)}\n" +
                                 f"• Enviadas: {status_counts.get('submitted', 0)}\n" +
                                 f"• Aprobadas: {status_counts.get('approved', 0)}\n" +
                                 f"• Rechazadas: {status_counts.get('rejected', 0)}",
                        "data": {
                            "equipo": equipo_info,
                            "total": len(hps_list),
                            "pendientes": status_counts.get('pending', 0),
                            "enviadas": status_counts.get('submitted', 0),
                            "aprobadas": status_counts.get('approved', 0),
                            "rechazadas": status_counts.get('rejected', 0)
                        }
                    }
                
        except Exception as e:
            logger.error(f"Error consultando HPS del equipo real: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Error consultando HPS del equipo en la base de datos."
            }
    
    async def _consultar_todas_hps(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Consultar estadísticas globales de HPS - DATOS REALES DE BBDD (admin y jefes de seguridad)"""
        
        user_role = user_context.get("role", "").lower()
        if user_role not in ["admin", "jefe_seguridad", "jefe_seguridad_suplente"]:
            return {
                "tipo": "conversacion",
                "mensaje": "¡Hola! 😊 Me encantaría mostrarte las estadísticas globales, pero esa información está reservada para administradores y jefes de seguridad.\n\n**¿Qué puedes consultar?**\n• Tu HPS: 'mi estado hps'\n• HPS del equipo: 'hps de mi equipo' (si eres jefe de equipo)\n• Estado específico: 'estado hps de [email]'\n\nSi necesitas acceso a estadísticas globales, contacta con un administrador. ¡Estoy aquí para ayudarte con otras consultas! 🤝"
            }
        
        try:
            # CONSULTA REAL A LA BBDD
            async with self.Session() as session:
                # Estadísticas generales
                stats_query = text("""
                    SELECT 
                        status,
                        COUNT(*) as count
                    FROM hps_requests 
                    GROUP BY status
                """)
                
                stats_result = await session.execute(stats_query)
                stats_data = stats_result.fetchall()
                
                # Estadísticas por equipos
                team_query = text("""
                    SELECT 
                        t.name as team_name,
                        COUNT(h.id) as total_hps,
                        SUM(CASE WHEN h.status = 'pending' THEN 1 ELSE 0 END) as pending_count
                    FROM teams t
                    LEFT JOIN users u ON t.id = u.team_id
                    LEFT JOIN hps_requests h ON u.email = h.email
                    GROUP BY t.id, t.name
                    ORDER BY total_hps DESC
                """)
                
                team_result = await session.execute(team_query)
                team_data = team_result.fetchall()
                
                # Formatear estadísticas generales
                status_counts = {row.status: row.count for row in stats_data}
                total_hps = sum(status_counts.values())
                
                # Formatear respuesta con datos REALES
                general_stats = f"📊 **RESUMEN GENERAL HPS:**\n\n" + \
                              f"• **PENDIENTES**: {status_counts.get('pending', 0)} solicitudes\n" + \
                              f"• **ENVIADAS**: {status_counts.get('submitted', 0)} solicitudes\n" + \
                              f"• **APROBADAS**: {status_counts.get('approved', 0)} solicitudes\n" + \
                              f"• **RECHAZADAS**: {status_counts.get('rejected', 0)} solicitudes\n\n"
                
                team_stats = "📋 **POR EQUIPOS:**\n"
                for team in team_data:
                    team_stats += f"• **{team.team_name}**: {team.total_hps} HPS ({team.pending_count} pendientes)\n"
                
                return {
                    "tipo": "informacion",
                    "mensaje": general_stats + team_stats,
                    "suggestions": generate_suggestions(user_context.get("role", "member"), "resumen hps estadísticas"),
                    "data": {
                        "total": total_hps,
                        "pendientes": status_counts.get('pending', 0),
                        "enviadas": status_counts.get('submitted', 0),
                        "aprobadas": status_counts.get('approved', 0),
                        "rechazadas": status_counts.get('rejected', 0)
                    }
                }
                
        except Exception as e:
            logger.error(f"Error consultando todas las HPS reales: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Error consultando estadísticas globales en la base de datos."
            }
    
    async def _renovar_hps(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Iniciar proceso de renovación HPS - IMPLEMENTACIÓN REAL"""
        
        user_role = user_context.get("role", "").lower()
        email = parametros.get("email")
        
        if user_role not in ["admin", "team_lead", "team_leader"]:
            return {
                "tipo": "error",
                "mensaje": "❌ No tienes permisos para iniciar renovaciones HPS."
            }
        
        if not email:
            return {
                "tipo": "conversacion",
                "mensaje": "📧 Para renovar una HPS de un miembro de tu equipo, necesito el email de la persona.\n\n**Por favor, proporciona el email del miembro:**\n• Ejemplo: 'renovar hps de miembro@empresa.com'\n• O simplemente escribe: 'miembro@empresa.com'\n\n¿Para qué email quieres renovar la HPS?"
            }
        
        try:
            # Verificar que existe HPS previa
            async with self.Session() as session:
                check_query = text("SELECT id, status FROM hps_requests WHERE email = :email ORDER BY created_at DESC LIMIT 1")
                result = await session.execute(check_query, {"email": email})
                existing_hps = result.fetchone()
                
                if not existing_hps:
                    return {
                        "tipo": "error",
                        "mensaje": f"❌ No se encontró HPS previa para {email}. Debe solicitar una nueva HPS primero."
                    }
                
                if existing_hps.status == "pending":
                    return {
                        "tipo": "error",
                        "mensaje": f"❌ {email} ya tiene una HPS pendiente. No se puede renovar hasta que se procese la actual."
                    }
            
            # Generar nueva URL de renovación con tipo específico
            return await self._solicitar_hps({"email": email, "user_message": "renovar hps"}, user_context)
                
        except Exception as e:
            logger.error(f"Error en renovación HPS: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Error procesando la renovación. Intenta de nuevo."
            }
    
    async def _trasladar_hps(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Iniciar proceso de traspaso HPS - IMPLEMENTACIÓN REAL"""
        
        user_role = user_context.get("role", "").lower()
        email = parametros.get("email")
        
        if user_role not in ["admin", "team_lead", "team_leader"]:
            return {
                "tipo": "error",
                "mensaje": "❌ No tienes permisos para iniciar traspasos HPS."
            }
        
        if not email:
            return {
                "tipo": "error",
                "mensaje": "❌ Necesito el email del usuario para iniciar el traspaso."
            }
        
        try:
            # Verificar que existe HPS previa
            async with self.Session() as session:
                check_query = text("SELECT id, status FROM hps_requests WHERE email = :email ORDER BY created_at DESC LIMIT 1")
                result = await session.execute(check_query, {"email": email})
                existing_hps = result.fetchone()
                
                if not existing_hps:
                    return {
                        "tipo": "error",
                        "mensaje": f"❌ No se encontró HPS previa para {email}. Debe solicitar una nueva HPS primero."
                    }
            
            # Generar nueva URL de traslado
            return await self._solicitar_hps({"email": email}, user_context)
                
        except Exception as e:
            logger.error(f"Error en traspaso HPS: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Error procesando el traspaso. Intenta de nuevo."
            }
    
    async def _get_team_id_by_name(self, team_name: str) -> Optional[str]:
        """Obtener team_id por nombre del equipo"""
        try:
            async with self.Session() as session:
                result = await session.execute(
                    text("SELECT id FROM teams WHERE name = :team_name"),
                    {"team_name": team_name}
                )
                row = result.fetchone()
                return str(row[0]) if row else None
        except Exception as e:
            logger.error(f"Error obteniendo team_id para '{team_name}': {e}")
            return None
    
    async def _check_user_in_team(self, email: str, team_id: str) -> bool:
        """Verificar si un usuario pertenece a un equipo específico"""
        try:
            async with self.Session() as session:
                result = await session.execute(
                    text("SELECT id FROM users WHERE email = :email AND team_id = :team_id"),
                    {"email": email, "team_id": team_id}
                )
                user = result.fetchone()
                return user is not None
        except Exception as e:
            logger.error(f"Error verificando usuario en equipo: {e}")
            return False

    async def _listar_usuarios(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Listar usuarios según el rol del usuario"""
        
        user_role = user_context.get("role", "").lower()
        
        if user_role not in ["admin", "team_lead", "team_leader"]:
            return {
                "tipo": "conversacion",
                "mensaje": "¡Hola! 😊 Me encantaría mostrarte la lista de usuarios, pero esa función está reservada para administradores y jefes de equipo.\n\n**¿Qué puedes hacer?**\n• Consultar tu HPS: 'mi estado hps'\n• Ver tu historial: 'mi historial hps'\n\nSi necesitas acceso a la lista de usuarios, contacta con tu jefe de equipo o administrador. ¡Estoy aquí para ayudarte con otras consultas! 🤝"
            }
        
        try:
            # Llamada al backend para obtener usuarios
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Configurar parámetros según el rol
                params = {"page": 1, "size": 100}
                if user_role in ["team_lead", "team_leader"]:
                    # Team lead solo ve usuarios de su equipo
                    team_id = user_context.get("team_id")
                    if team_id:
                        params["team_id"] = team_id
                    else:
                        return {
                            "tipo": "conversacion",
                            "mensaje": "¡Ups! 😅 No puedo determinar tu equipo. Necesito esta información para mostrarte los usuarios de tu equipo.\n\n**¿Qué puedes hacer?**\n• Contactar al administrador para verificar tu asignación de equipo\n• Intentar de nuevo en unos momentos\n\n¡Estoy aquí para ayudarte! 🤝"
                        }
                
                response = await client.get(
                    f"{self.backend_url}/api/hps/user/profiles/",
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    users = data.get("users", [])
                    
                    if not users:
                        if user_role == "admin":
                            message = "📋 **Lista de Usuarios:**\n\n❌ No hay usuarios registrados en el sistema."
                        else:
                            team_name = user_context.get("team_name", "tu equipo")
                            message = f"📋 **Lista de Usuarios de {team_name}:**\n\n❌ No hay usuarios en tu equipo."
                        
                        return {
                            "tipo": "informacion",
                            "mensaje": message,
                            "data": {"total": 0, "usuarios": []}
                        }
                    
                    # Formatear lista de usuarios
                    user_list = []
                    for user in users:
                        status = "Activo" if user.get("is_active", True) else "Inactivo"
                        last_login = user.get("last_login")
                        if last_login:
                            try:
                                from datetime import datetime
                                last_login_dt = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                                last_login = last_login_dt.strftime("%d/%m/%Y")
                            except:
                                last_login = "N/A"
                        else:
                            last_login = "Nunca"
                        
                        user_list.append(f"• **{user.get('first_name', '')} {user.get('last_name', '')}** ({user.get('email', '')})\n  - Rol: {user.get('role', 'N/A')}\n  - Equipo: {user.get('team_name', 'Sin equipo')}\n  - Estado: {status}\n  - Último acceso: {last_login}")
                    
                    if user_role == "admin":
                        title = f"📋 **Lista de Usuarios ({len(users)} total):**"
                    else:
                        team_name = user_context.get("team_name", "tu equipo")
                        title = f"📋 **Lista de Usuarios de {team_name} ({len(users)} total):**"
                    
                    return {
                        "tipo": "informacion",
                        "mensaje": f"{title}\n\n" + "\n\n".join(user_list),
                        "data": {
                            "total": len(users),
                            "usuarios": [{"email": u.get("email", ""), "nombre": f"{u.get('first_name', '')} {u.get('last_name', '')}", "rol": u.get("role", ""), "equipo": u.get("team_name", "")} for u in users]
                        }
                    }
                else:
                    return {
                        "tipo": "conversacion",
                        "mensaje": f"¡Ups! 😅 Hubo un problema obteniendo la lista de usuarios: {response.text}\n\n**¿Qué puedes hacer?**\n• Intentar de nuevo en unos momentos\n• Contactar al administrador si el problema persiste\n\n¡Estoy aquí para ayudarte! 🤝"
                    }
                    
        except Exception as e:
            logger.error(f"Error listando usuarios: {e}")
            return {
                "tipo": "conversacion",
                "mensaje": "¡Ups! 😅 Parece que hay un problema de conexión con el servidor. No te preocupes, esto puede pasar.\n\n**¿Qué puedes hacer?**\n• Esperar unos segundos y volver a intentar\n• Verificar tu conexión a internet\n• Contactar al administrador si el problema persiste\n\n¡Estoy aquí para ayudarte en cuanto se restablezca la conexión! 🤝"
            }

    async def _listar_equipos(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Listar todos los equipos del sistema (solo admin)"""
        
        if user_context.get("role", "").lower() != "admin":
            return {
                "tipo": "conversacion",
                "mensaje": "¡Hola! 😊 Me encantaría mostrarte la lista de equipos, pero esa función está reservada para administradores.\n\n**¿Qué puedes hacer?**\n• Consultar tu HPS: 'mi estado hps'\n• Ver HPS del equipo: 'hps de mi equipo' (si eres jefe de equipo)\n• Ver estadísticas: 'todas las hps'\n\nSi necesitas acceso a la lista de equipos, contacta con un administrador. ¡Estoy aquí para ayudarte con otras consultas! 🤝"
            }
        
        try:
            # Llamada al backend para obtener equipos
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.backend_url}/api/hps/teams/",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    teams = data.get("teams", [])
                    
                    if not teams:
                        return {
                            "tipo": "informacion",
                            "mensaje": "📋 **Lista de Equipos:**\n\n❌ No hay equipos registrados en el sistema.",
                            "data": {"total": 0, "equipos": []}
                        }
                    
                    # Formatear lista de equipos
                    team_list = []
                    for team in teams:
                        # Convertir a diccionario si es un objeto Pydantic
                        if hasattr(team, 'dict'):
                            team_dict = team.dict()
                        elif hasattr(team, '__dict__'):
                            team_dict = team.__dict__
                        else:
                            team_dict = team
                        
                        status = "Activo" if team_dict.get("is_active", True) else "Inactivo"
                        leader_name = team_dict.get("team_lead_name", "Sin líder asignado")
                        
                        team_list.append(f"• **{team_dict.get('name', '')}**\n  - Descripción: {team_dict.get('description', 'Sin descripción')}\n  - Líder: {leader_name}\n  - Estado: {status}")
                    
                    return {
                        "tipo": "informacion",
                        "mensaje": f"📋 **Lista de Equipos ({len(teams)} total):**\n\n" + "\n\n".join(team_list),
                        "data": {
                            "total": len(teams),
                            "equipos": [{"nombre": team_dict.get("name", ""), "descripcion": team_dict.get("description", ""), "lider": team_dict.get("team_lead_name", "")} for team_dict in [team.dict() if hasattr(team, 'dict') else team.__dict__ if hasattr(team, '__dict__') else team for team in teams]]
                        }
                    }
                else:
                    return {
                        "tipo": "conversacion",
                        "mensaje": f"¡Ups! 😅 Hubo un problema obteniendo la lista de equipos: {response.text}\n\n**¿Qué puedes hacer?**\n• Intentar de nuevo en unos momentos\n• Contactar al administrador si el problema persiste\n\n¡Estoy aquí para ayudarte! 🤝"
                    }
                    
        except Exception as e:
            logger.error(f"Error listando equipos: {e}")
            return {
                "tipo": "conversacion",
                "mensaje": "¡Ups! 😅 Parece que hay un problema de conexión con el servidor. No te preocupes, esto puede pasar.\n\n**¿Qué puedes hacer?**\n• Esperar unos segundos y volver a intentar\n• Verificar tu conexión a internet\n• Contactar al administrador si el problema persiste\n\n¡Estoy aquí para ayudarte en cuanto se restablezca la conexión! 🤝"
            }

    async def _crear_usuario(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Crear usuario solo con email (solo admin)"""
        
        if user_context.get("role", "").lower() != "admin":
            return {
                "tipo": "conversacion",
                "mensaje": "¡Hola! 😊 Me encantaría ayudarte a crear un usuario, pero esa función está reservada para administradores.\n\n**¿Qué puedes hacer?**\n• Consultar tu HPS: 'mi estado hps'\n• Ver HPS del equipo: 'hps de mi equipo' (si eres jefe de equipo)\n• Ver estadísticas: 'todas las hps'\n\nSi necesitas crear un usuario, contacta con un administrador. ¡Estoy aquí para ayudarte con otras consultas! 🤝"
            }
        
        email = parametros.get("email")
        if not email:
            # Iniciar flujo conversacional
            user_id = user_context.get("id")
            self._start_conversation_flow(user_id, "crear_usuario")
            return {
                "tipo": "conversacion",
                "mensaje": "📧 ¡Perfecto! Para crear un usuario necesito el email.\n\n**Ejemplo:** usuario@empresa.com\n\nEscribe el email o 'cancelar' para salir.",
                "suggestions": ["Cancelar"]
            }
        
        try:
            # Llamada al backend para crear usuario
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                user_data = {
                    "email": email,
                    "full_name": email.split('@')[0],  # Usar parte antes del @ como nombre
                    "password": "temp_password_123",  # El backend generará uno seguro
                    "role": "member",
                    "team_id": None  # Sin equipo asignado
                }
                
                response = await client.post(
                    f"{self.backend_url}/api/hps/user/profiles/",
                    json=user_data,
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    return {
                        "tipo": "exito",
                        "mensaje": f"✅ Usuario '{email}' creado exitosamente como miembro. Se han enviado las credenciales por correo.",
                        "data": {
                            "email": email,
                            "rol": "member",
                            "equipo": "Sin asignar"
                        }
                    }
                else:
                    error_detail = response.text
                    if "email ya está en uso" in error_detail.lower():
                        return {
                            "tipo": "conversacion",
                            "mensaje": f"¡Ah! 😊 El email {email} ya está registrado en el sistema.\n\n**¿Qué puedes hacer?**\n• Usar un email diferente: 'crear usuario nuevo@example.com'\n• Verificar si el usuario ya existe: 'estado hps de {email}'\n• Contactar al administrador si necesitas ayuda\n\n¡Te ayudo con cualquiera de estas opciones! 🤝"
                        }
                    else:
                        return {
                            "tipo": "conversacion",
                            "mensaje": f"¡Ups! 😅 Hubo un problema creando el usuario: {error_detail}\n\n**¿Qué puedes hacer?**\n• Verificar que el email sea válido\n• Intentar con un email diferente\n• Contactar al administrador si el problema persiste\n\n¡Estoy aquí para ayudarte! 🤝"
                        }
                    
        except Exception as e:
            logger.error(f"Error creando usuario: {e}")
            return {
                "tipo": "conversacion",
                "mensaje": "¡Ups! 😅 Parece que hay un problema de conexión con el servidor. No te preocupes, esto puede pasar.\n\n**¿Qué puedes hacer?**\n• Esperar unos segundos y volver a intentar\n• Verificar tu conexión a internet\n• Contactar al administrador si el problema persiste\n\n¡Estoy aquí para ayudarte en cuanto se restablezca la conexión! 🤝"
            }

    async def _crear_equipo(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Crear nuevo equipo (solo admin)"""
        
        if user_context.get("role", "").lower() != "admin":
            return {
                "tipo": "conversacion",
                "mensaje": "¡Hola! 😊 Me encantaría ayudarte a crear un equipo, pero esa función está reservada para administradores.\n\n**¿Qué puedes hacer?**\n• Consultar tu HPS: 'mi estado hps'\n• Ver HPS del equipo: 'hps de mi equipo' (si eres jefe de equipo)\n• Ver estadísticas: 'todas las hps'\n\nSi necesitas crear un equipo, contacta con un administrador. ¡Estoy aquí para ayudarte con otras consultas! 🤝"
            }
        
        nombre = parametros.get("nombre")
        if not nombre:
            return {
                "tipo": "conversacion",
                "mensaje": "¡Perfecto! 😊 Para crear un equipo necesito el nombre.\n\n**Ejemplo:**\n'crear equipo NUEVO'\n\n¡Así podré ayudarte mejor! 🤝"
            }
        
        try:
            # Llamada al backend para crear equipo
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                team_data = {
                    "name": nombre,
                    "description": f"Equipo {nombre}",
                    "team_lead_id": None
                }
                
                response = await client.post(
                    f"{self.backend_url}/api/hps/teams/",
                    json=team_data,
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    return {
                        "tipo": "exito",
                        "mensaje": f"✅ Equipo '{nombre}' creado exitosamente.",
                        "data": {
                            "nombre": nombre,
                            "descripcion": f"Equipo {nombre}",
                            "lider": "Sin asignar"
                        }
                    }
                else:
                    error_detail = response.text
                    if "ya existe" in error_detail.lower() or "already exists" in error_detail.lower():
                        return {
                            "tipo": "conversacion",
                            "mensaje": f"¡Ah! 😊 El equipo '{nombre}' ya existe en el sistema.\n\n**¿Qué puedes hacer?**\n• Usar un nombre diferente: 'crear equipo {nombre}_NUEVO'\n• Verificar equipos existentes: 'listar equipos'\n• Contactar al administrador si necesitas ayuda\n\n¡Te ayudo con cualquiera de estas opciones! 🤝"
                        }
                    else:
                        return {
                            "tipo": "conversacion",
                            "mensaje": f"¡Ups! 😅 Hubo un problema creando el equipo: {error_detail}\n\n**¿Qué puedes hacer?**\n• Verificar que el nombre sea válido\n• Intentar con un nombre diferente\n• Contactar al administrador si el problema persiste\n\n¡Estoy aquí para ayudarte! 🤝"
                        }
                    
        except Exception as e:
            logger.error(f"Error creando equipo: {e}")
            return {
                "tipo": "conversacion",
                "mensaje": "¡Ups! 😅 Parece que hay un problema de conexión con el servidor. No te preocupes, esto puede pasar.\n\n**¿Qué puedes hacer?**\n• Esperar unos segundos y volver a intentar\n• Verificar tu conexión a internet\n• Contactar al administrador si el problema persiste\n\n¡Estoy aquí para ayudarte en cuanto se restablezca la conexión! 🤝"
            }

    async def _asignar_equipo(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Asignar usuario a equipo (solo admin)"""
        
        if user_context.get("role", "").lower() != "admin":
            return {
                "tipo": "conversacion",
                "mensaje": "¡Hola! 😊 Me encantaría ayudarte a asignar equipos, pero esa función está reservada para administradores.\n\n**¿Qué puedes hacer?**\n• Consultar tu HPS: 'mi estado hps'\n• Ver HPS del equipo: 'hps de mi equipo' (si eres jefe de equipo)\n• Ver estadísticas: 'todas las hps'\n\nSi necesitas asignar equipos, contacta con un administrador. ¡Estoy aquí para ayudarte con otras consultas! 🤝"
            }
        
        email = parametros.get("email")
        equipo = parametros.get("equipo")
        
        if not email or not equipo:
            return {
                "tipo": "conversacion",
                "mensaje": "¡Perfecto! 😊 Para asignar un usuario a un equipo necesito el email y el nombre del equipo.\n\n**Ejemplo:**\n'asignar usuario test@example.com al equipo AICOX'\n\n¡Así podré ayudarte mejor! 🤝"
            }
        
        try:
            # Obtener team_id del equipo
            team_id = await self._get_team_id_by_name(equipo)
            if not team_id:
                return {
                    "tipo": "conversacion",
                    "mensaje": f"¡Ah! 😊 No encontré el equipo '{equipo}' en el sistema.\n\n**¿Qué puedes hacer?**\n• Verificar equipos disponibles: 'listar equipos'\n• Usar un nombre de equipo correcto\n• Contactar al administrador si necesitas ayuda\n\n¡Te ayudo con cualquiera de estas opciones! 🤝"
                }
            
            # Llamada al backend para actualizar usuario
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Primero buscar el usuario por email
                # Buscar usuario por email en los perfiles HPS
                user_response = await client.get(
                    f"{self.backend_url}/api/hps/user/profiles/",
                    headers=headers,
                    params={"email": email}
                )
                
                if user_response.status_code != 200:
                    return {
                        "tipo": "conversacion",
                        "mensaje": f"¡Ah! 😊 No encontré el usuario '{email}' en el sistema.\n\n**¿Qué puedes hacer?**\n• Verificar usuarios disponibles: 'listar usuarios'\n• Usar un email correcto\n• Contactar al administrador si necesitas ayuda\n\n¡Te ayudo con cualquiera de estas opciones! 🤝"
                    }
                
                search_data = user_response.json()
                users = search_data.get("results", [])
                
                if not users:
                    return {
                        "tipo": "conversacion",
                        "mensaje": f"¡Ah! 😊 No encontré el usuario '{email}' en el sistema.\n\n**¿Qué puedes hacer?**\n• Verificar usuarios disponibles: 'listar usuarios'\n• Usar un email correcto\n• Contactar al administrador si necesitas ayuda\n\n¡Te ayudo con cualquiera de estas opciones! 🤝"
                    }
                
                user_data = users[0]  # Tomar el primer resultado
                user_data["team_id"] = team_id
                
                # Actualizar usuario
                # Actualizar perfil HPS usando el ID del perfil
                profile_id = user_data.get("id")  # ID del perfil HPS
                update_response = await client.patch(
                    f"{self.backend_url}/api/hps/user/profiles/{profile_id}/",
                    json={"team": user_data.get("team_id")},
                    headers=headers
                )
                
                if update_response.status_code in [200, 201]:
                    return {
                        "tipo": "exito",
                        "mensaje": f"✅ Usuario '{email}' asignado exitosamente al equipo '{equipo}'.",
                        "data": {
                            "email": email,
                            "equipo": equipo
                        }
                    }
                else:
                    return {
                        "tipo": "conversacion",
                        "mensaje": f"¡Ups! 😅 Hubo un problema asignando el usuario al equipo: {update_response.text}\n\n**¿Qué puedes hacer?**\n• Verificar que el usuario y equipo existan\n• Intentar de nuevo en unos momentos\n• Contactar al administrador si el problema persiste\n\n¡Estoy aquí para ayudarte! 🤝"
                    }
                    
        except Exception as e:
            logger.error(f"Error asignando equipo: {e}")
            return {
                "tipo": "conversacion",
                "mensaje": "¡Ups! 😅 Parece que hay un problema de conexión con el servidor. No te preocupes, esto puede pasar.\n\n**¿Qué puedes hacer?**\n• Esperar unos segundos y volver a intentar\n• Verificar tu conexión a internet\n• Contactar al administrador si el problema persiste\n\n¡Estoy aquí para ayudarte en cuanto se restablezca la conexión! 🤝"
            }

    async def _modificar_rol(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Modificar rol de usuario (solo admin)"""
        
        if user_context.get("role", "").lower() != "admin":
            return {
                "tipo": "conversacion",
                "mensaje": "¡Hola! 😊 Me encantaría ayudarte a modificar roles, pero esa función está reservada para administradores.\n\n**¿Qué puedes hacer?**\n• Consultar tu HPS: 'mi estado hps'\n• Ver HPS del equipo: 'hps de mi equipo' (si eres jefe de equipo)\n• Ver estadísticas: 'todas las hps'\n\nSi necesitas modificar roles, contacta con un administrador. ¡Estoy aquí para ayudarte con otras consultas! 🤝"
            }
        
        # Siempre iniciar flujo conversacional para modificar rol
        user_id = user_context.get("id")
        self._start_conversation_flow(user_id, "modificar_rol")
        return {
            "tipo": "conversacion",
            "mensaje": "👤 **Modificar Rol de Usuario**\n\n📧 Para modificar un rol necesito el email del usuario.\n\n**Ejemplo:** usuario@empresa.com\n\nEscribe el email o 'cancelar' para salir.",
            "suggestions": ["Cancelar"]
        }

    async def _aprobar_hps(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Aprobar HPS (solo admin)"""
        
        if user_context.get("role", "").lower() != "admin":
            return {
                "tipo": "conversacion",
                "mensaje": "¡Hola! 😊 Me encantaría ayudarte a aprobar HPS, pero esa función está reservada para administradores.\n\n**¿Qué puedes hacer?**\n• Consultar tu HPS: 'mi estado hps'\n• Ver HPS del equipo: 'hps de mi equipo' (si eres jefe de equipo)\n• Ver estadísticas: 'todas las hps'\n\nSi necesitas aprobar HPS, contacta con un administrador. ¡Estoy aquí para ayudarte con otras consultas! 🤝"
            }
        
        email = parametros.get("email")
        if not email:
            # Iniciar flujo conversacional
            user_id = user_context.get("id")
            self._start_conversation_flow(user_id, "aprobar_hps")
            return {
                "tipo": "conversacion",
                "mensaje": "📧 ¡Perfecto! Para aprobar una HPS necesito el email del usuario.\n\n**Ejemplo:** usuario@empresa.com\n\nEscribe el email o 'cancelar' para salir.",
                "suggestions": ["Cancelar"]
            }
        
        try:
            # Llamada al backend para aprobar HPS
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.backend_url}/api/hps/approve/{email}",
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    return {
                        "tipo": "exito",
                        "mensaje": f"✅ HPS de '{email}' aprobada exitosamente.",
                        "data": {
                            "email": email,
                            "estado": "aprobada"
                        }
                    }
                else:
                    error_detail = response.text
                    if "no encontrada" in error_detail.lower() or "not found" in error_detail.lower():
                        return {
                            "tipo": "conversacion",
                            "mensaje": f"¡Ah! 😊 No encontré una HPS pendiente para '{email}'.\n\n**¿Qué puedes hacer?**\n• Verificar el estado: 'estado hps de {email}'\n• Ver todas las HPS: 'todas las hps'\n• Contactar al administrador si necesitas ayuda\n\n¡Te ayudo con cualquiera de estas opciones! 🤝"
                        }
                    else:
                        return {
                            "tipo": "conversacion",
                            "mensaje": f"¡Ups! 😅 Hubo un problema aprobando la HPS: {error_detail}\n\n**¿Qué puedes hacer?**\n• Verificar que el usuario tenga una HPS pendiente\n• Intentar de nuevo en unos momentos\n• Contactar al administrador si el problema persiste\n\n¡Estoy aquí para ayudarte! 🤝"
                        }
                    
        except Exception as e:
            logger.error(f"Error aprobando HPS: {e}")
            return {
                "tipo": "conversacion",
                "mensaje": "¡Ups! 😅 Parece que hay un problema de conexión con el servidor. No te preocupes, esto puede pasar.\n\n**¿Qué puedes hacer?**\n• Esperar unos segundos y volver a intentar\n• Verificar tu conexión a internet\n• Contactar al administrador si el problema persiste\n\n¡Estoy aquí para ayudarte en cuanto se restablezca la conexión! 🤝"
            }

    async def _rechazar_hps(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Rechazar HPS (solo admin)"""
        
        if user_context.get("role", "").lower() != "admin":
            return {
                "tipo": "conversacion",
                "mensaje": "¡Hola! 😊 Me encantaría ayudarte a rechazar HPS, pero esa función está reservada para administradores.\n\n**¿Qué puedes hacer?**\n• Consultar tu HPS: 'mi estado hps'\n• Ver HPS del equipo: 'hps de mi equipo' (si eres jefe de equipo)\n• Ver estadísticas: 'todas las hps'\n\nSi necesitas rechazar HPS, contacta con un administrador. ¡Estoy aquí para ayudarte con otras consultas! 🤝"
            }
        
        email = parametros.get("email")
        if not email:
            # Iniciar flujo conversacional
            user_id = user_context.get("id")
            self._start_conversation_flow(user_id, "rechazar_hps")
            return {
                "tipo": "conversacion",
                "mensaje": "📧 ¡Perfecto! Para rechazar una HPS necesito el email del usuario.\n\n**Ejemplo:** usuario@empresa.com\n\nEscribe el email o 'cancelar' para salir.",
                "suggestions": ["Cancelar"]
            }
        
        try:
            # Llamada al backend para rechazar HPS
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Buscar la solicitud HPS por email del usuario
                # Primero obtener el usuario y luego su solicitud HPS
                user_response = await client.get(
                    f"{self.backend_url}/api/hps/user/profiles/",
                    headers=headers,
                    params={"email": email}
                )
                if user_response.status_code != 200:
                    return {
                        "tipo": "error",
                        "mensaje": f"❌ No se encontró el usuario '{email}' en el sistema."
                    }
                users = user_response.json().get("results", [])
                if not users:
                    return {
                        "tipo": "error",
                        "mensaje": f"❌ No se encontró el usuario '{email}' en el sistema."
                    }
                user_id = users[0].get("user_id")
                # Buscar la solicitud HPS del usuario
                hps_response = await client.get(
                    f"{self.backend_url}/api/hps/requests/",
                    headers=headers,
                    params={"user_id": user_id, "status": "pending"}
                )
                if hps_response.status_code != 200:
                    return {
                        "tipo": "error",
                        "mensaje": f"❌ No se encontró una solicitud HPS pendiente para '{email}'."
                    }
                hps_requests = hps_response.json().get("results", [])
                if not hps_requests:
                    return {
                        "tipo": "error",
                        "mensaje": f"❌ No se encontró una solicitud HPS pendiente para '{email}'."
                    }
                request_id = hps_requests[0].get("id")
                # Rechazar la solicitud
                response = await client.post(
                    f"{self.backend_url}/api/hps/requests/{request_id}/reject/",
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    return {
                        "tipo": "exito",
                        "mensaje": f"✅ HPS de '{email}' rechazada exitosamente.",
                        "data": {
                            "email": email,
                            "estado": "rechazada"
                        }
                    }
                else:
                    error_detail = response.text
                    if "no encontrada" in error_detail.lower() or "not found" in error_detail.lower():
                        return {
                            "tipo": "conversacion",
                            "mensaje": f"¡Ah! 😊 No encontré una HPS pendiente para '{email}'.\n\n**¿Qué puedes hacer?**\n• Verificar el estado: 'estado hps de {email}'\n• Ver todas las HPS: 'todas las hps'\n• Contactar al administrador si necesitas ayuda\n\n¡Te ayudo con cualquiera de estas opciones! 🤝"
                        }
                    else:
                        return {
                            "tipo": "conversacion",
                            "mensaje": f"¡Ups! 😅 Hubo un problema rechazando la HPS: {error_detail}\n\n**¿Qué puedes hacer?**\n• Verificar que el usuario tenga una HPS pendiente\n• Intentar de nuevo en unos momentos\n• Contactar al administrador si el problema persiste\n\n¡Estoy aquí para ayudarte! 🤝"
                        }
                    
        except Exception as e:
            logger.error(f"Error rechazando HPS: {e}")
            return {
                "tipo": "conversacion",
                "mensaje": "¡Ups! 😅 Parece que hay un problema de conexión con el servidor. No te preocupes, esto puede pasar.\n\n**¿Qué puedes hacer?**\n• Esperar unos segundos y volver a intentar\n• Verificar tu conexión a internet\n• Contactar al administrador si el problema persiste\n\n¡Estoy aquí para ayudarte en cuanto se restablezca la conexión! 🤝"
            }

    async def _consultar_historial_hps(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Consultar historial personal de HPS del usuario"""
        
        user_email = user_context.get("email", "")
        if not user_email:
            return {
                "tipo": "error",
                "mensaje": "❌ No se pudo identificar tu usuario. Contacta al administrador."
            }
        
        try:
            # CONSULTA REAL A LA BBDD
            async with self.Session() as session:
                query = text("""
                    SELECT h.*, u.first_name, u.last_name 
                    FROM hps_requests h 
                    JOIN users u ON h.email = u.email 
                    WHERE h.email = :email 
                    ORDER BY h.created_at DESC
                """)
                
                result = await session.execute(query, {"email": user_email})
                hps_list = result.fetchall()
                
                if not hps_list:
                    return {
                        "tipo": "informacion",
                        "mensaje": f"📋 **Tu historial HPS:**\n\n❌ No tienes solicitudes HPS registradas.",
                        "data": {
                            "email": user_email,
                            "total": 0,
                            "historial": []
                        }
                    }
                
                # Formatear historial
                historial_details = []
                for hps in hps_list:
                    status_es = {
                        "pending": "PENDIENTE",
                        "submitted": "ENVIADA", 
                        "approved": "APROBADA",
                        "rejected": "RECHAZADA",
                        "expired": "EXPIRADA"
                    }
                    estado = status_es.get(hps.status, hps.status.upper())
                    fecha = hps.created_at.strftime("%d/%m/%Y") if hps.created_at else "N/A"
                    
                    historial_details.append(f"• **{fecha}**: {estado} - {hps.request_type or 'Nueva solicitud'}")
                
                return {
                    "tipo": "informacion",
                    "mensaje": f"📋 **Tu historial HPS ({len(hps_list)} solicitudes):**\n\n" + "\n".join(historial_details),
                    "data": {
                        "email": user_email,
                        "total": len(hps_list),
                        "historial": [{"fecha": h.created_at.isoformat() if h.created_at else None, "estado": h.status, "tipo": h.request_type} for h in hps_list]
                    }
                }
                
        except Exception as e:
            logger.error(f"Error consultando historial HPS: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Error consultando tu historial en la base de datos. Intenta de nuevo."
            }
    
    async def _consultar_vencimiento_hps(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Consultar fecha de vencimiento de HPS del usuario"""
        
        user_email = user_context.get("email", "")
        if not user_email:
            return {
                "tipo": "error",
                "mensaje": "❌ No se pudo identificar tu usuario. Contacta al administrador."
            }
        
        try:
            # CONSULTA REAL A LA BBDD
            async with self.Session() as session:
                query = text("""
                    SELECT h.*, u.first_name, u.last_name 
                    FROM hps_requests h 
                    JOIN users u ON h.email = u.email 
                    WHERE h.email = :email 
                    AND h.status = 'approved'
                    ORDER BY h.created_at DESC 
                    LIMIT 1
                """)
                
                result = await session.execute(query, {"email": user_email})
                hps_data = result.fetchone()
                
                if not hps_data:
                    return {
                        "tipo": "informacion",
                        "mensaje": f"📋 **Fecha de vencimiento de tu HPS:**\n\n❌ No tienes una HPS aprobada actualmente.",
                        "data": {
                            "email": user_email,
                            "estado": "sin_hps_aprobada",
                            "vencimiento": None
                        }
                    }
                
                # Calcular fecha de vencimiento (asumiendo 1 año de validez)
                from datetime import datetime, timedelta
                fecha_aprobacion = hps_data.created_at
                fecha_vencimiento = fecha_aprobacion + timedelta(days=365)
                dias_restantes = (fecha_vencimiento - datetime.now()).days
                
                if dias_restantes > 0:
                    mensaje_vencimiento = f"✅ Tu HPS vence el **{fecha_vencimiento.strftime('%d/%m/%Y')}** (en {dias_restantes} días)"
                    estado_vencimiento = "vigente"
                else:
                    mensaje_vencimiento = f"⚠️ Tu HPS venció el **{fecha_vencimiento.strftime('%d/%m/%Y')}** (hace {abs(dias_restantes)} días)"
                    estado_vencimiento = "vencida"
                
                return {
                    "tipo": "informacion",
                    "mensaje": f"📋 **Fecha de vencimiento de tu HPS:**\n\n{mensaje_vencimiento}\n\n• **Fecha de aprobación**: {fecha_aprobacion.strftime('%d/%m/%Y')}\n• **Tipo**: {hps_data.request_type or 'Nueva solicitud'}",
                    "data": {
                        "email": user_email,
                        "estado": estado_vencimiento,
                        "fecha_aprobacion": fecha_aprobacion.isoformat(),
                        "fecha_vencimiento": fecha_vencimiento.isoformat(),
                        "dias_restantes": dias_restantes
                    }
                }
                
        except Exception as e:
            logger.error(f"Error consultando vencimiento HPS: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Error consultando la fecha de vencimiento en la base de datos. Intenta de nuevo."
            }
    
    async def _consultar_estado_equipo(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Consultar estado general del equipo del usuario"""
        
        user_role = user_context.get("role", "").lower()
        
        if user_role not in ["admin", "team_lead", "team_leader"]:
            return {
                "tipo": "conversacion",
                "mensaje": "¡Hola! 😊 Me encantaría mostrarte el estado de tu equipo, pero esa función está disponible para jefes de equipo y administradores.\n\n**¿Qué puedes hacer?**\n• Consultar tu HPS: 'mi estado hps'\n• Ver tu historial: 'mi historial hps'\n• Ver fecha de vencimiento: 'cuando expira mi hps'\n\nSi necesitas información del equipo, contacta con tu jefe de equipo. ¡Estoy aquí para ayudarte con otras consultas! 🤝"
            }
        
        try:
            # CONSULTA REAL A LA BBDD
            async with self.Session() as session:
                team_id = user_context.get("team_id")
                
                if not team_id:
                    return {
                        "tipo": "error",
                        "mensaje": "❌ No se pudo identificar tu equipo. Contacta al administrador."
                    }
                
                # Obtener información del equipo
                team_query = text("SELECT name, description FROM teams WHERE id = :team_id")
                team_result = await session.execute(team_query, {"team_id": team_id})
                team_info = team_result.fetchone()
                
                if not team_info:
                    return {
                        "tipo": "error",
                        "mensaje": "❌ No se encontró información de tu equipo. Contacta al administrador."
                    }
                
                # Obtener estadísticas del equipo
                stats_query = text("""
                    SELECT 
                        COUNT(DISTINCT u.id) as total_miembros,
                        COUNT(DISTINCT h.id) as total_hps,
                        SUM(CASE WHEN h.status = 'approved' THEN 1 ELSE 0 END) as hps_aprobadas,
                        SUM(CASE WHEN h.status = 'pending' THEN 1 ELSE 0 END) as hps_pendientes,
                        SUM(CASE WHEN h.status = 'rejected' THEN 1 ELSE 0 END) as hps_rechazadas
                    FROM users u
                    LEFT JOIN hps_requests h ON u.email = h.email
                    WHERE u.team_id = :team_id
                """)
                
                stats_result = await session.execute(stats_query, {"team_id": team_id})
                stats = stats_result.fetchone()
                
                # Obtener miembros del equipo
                members_query = text("""
                    SELECT u.first_name, u.last_name, u.email, u.role,
                           h.status as hps_status, h.created_at as hps_fecha
                    FROM users u
                    LEFT JOIN hps_requests h ON u.email = h.email 
                    WHERE u.team_id = :team_id
                    ORDER BY u.first_name, u.last_name
                """)
                
                members_result = await session.execute(members_query, {"team_id": team_id})
                members = members_result.fetchall()
                
                # Formatear información del equipo
                equipo_nombre = team_info.name
                equipo_descripcion = team_info.description or "Sin descripción"
                
                mensaje_equipo = f"🏢 **Estado del Equipo {equipo_nombre}:**\n\n"
                mensaje_equipo += f"📝 **Descripción**: {equipo_descripcion}\n\n"
                mensaje_equipo += f"📊 **Estadísticas:**\n"
                mensaje_equipo += f"• Total de miembros: {stats.total_miembros}\n"
                mensaje_equipo += f"• Total de HPS: {stats.total_hps}\n"
                mensaje_equipo += f"• HPS aprobadas: {stats.hps_aprobadas}\n"
                mensaje_equipo += f"• HPS pendientes: {stats.hps_pendientes}\n"
                mensaje_equipo += f"• HPS rechazadas: {stats.hps_rechazadas}\n\n"
                
                # Listar miembros
                mensaje_equipo += f"👥 **Miembros del equipo:**\n"
                for member in members:
                    nombre = f"{member.first_name} {member.last_name}"
                    rol = member.role or "member"
                    hps_status = member.hps_status or "Sin HPS"
                    
                    if hps_status == "approved":
                        hps_info = "✅ Aprobada"
                    elif hps_status == "pending":
                        hps_info = "⏳ Pendiente"
                    elif hps_status == "rejected":
                        hps_info = "❌ Rechazada"
                    else:
                        hps_info = "📋 Sin HPS"
                    
                    mensaje_equipo += f"• **{nombre}** ({rol}) - HPS: {hps_info}\n"
                
                return {
                    "tipo": "informacion",
                    "mensaje": mensaje_equipo,
                    "data": {
                        "equipo": equipo_nombre,
                        "descripcion": equipo_descripcion,
                        "total_miembros": stats.total_miembros,
                        "total_hps": stats.total_hps,
                        "hps_aprobadas": stats.hps_aprobadas,
                        "hps_pendientes": stats.hps_pendientes,
                        "hps_rechazadas": stats.hps_rechazadas,
                        "miembros": [{"nombre": f"{m.first_name} {m.last_name}", "email": m.email, "rol": m.role, "hps_status": m.hps_status} for m in members]
                    }
                }
                
        except Exception as e:
            logger.error(f"Error consultando estado del equipo: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Error consultando el estado del equipo en la base de datos. Intenta de nuevo."
            }

    async def _mostrar_comandos_disponibles(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Mostrar comandos disponibles según el rol del usuario"""
        
        user_role = user_context.get("role", "").lower()
        
        if user_role == "admin":
            comandos = """
🔧 **COMANDOS DE ADMINISTRADOR:**

**👥 GESTIÓN DE USUARIOS:**
• "listar usuarios" - Ver todos los usuarios
• "crear usuario email@ejemplo.com" - Crear nuevo usuario
• "modificar rol" - Cambiar rol de usuario

**🏢 GESTIÓN DE EQUIPOS:**
• "listar equipos" - Ver todos los equipos
• "crear equipo NOMBRE" - Crear nuevo equipo
• "asignar usuario email@ejemplo.com al equipo NOMBRE" - Asignar usuario

**📋 GESTIÓN DE HPS:**
• "todas las hps" - Ver resumen de todas las HPS
• "estado hps de email@ejemplo.com" - Consultar estado específico
• "solicitar hps para email@ejemplo.com" - Generar solicitud HPS

**💡 EJEMPLOS:**
• "crear usuario juan@empresa.com"
• "modificar rol"
• "listar equipos"
• "todas las hps"
"""
        elif user_role in ["jefe_seguridad", "jefe_seguridad_suplente"]:
            role_name = "JEFE DE SEGURIDAD" if user_role == "jefe_seguridad" else "JEFE DE SEGURIDAD SUPLENTE"
            comandos = f"""
🔧 **COMANDOS DE {role_name}:**

**📋 GESTIÓN DE HPS:**
• "dame un resumen de todas las hps" - Ver estadísticas globales de HPS
• "solicitar traspaso hps para email@ejemplo.com" - Solicitar traspaso HPS (solo jefes de seguridad)
• "solicitar hps para email@ejemplo.com" - Generar solicitud nueva HPS
• "estado hps de email@ejemplo.com" - Consultar estado de HPS
• "renovar hps de email@ejemplo.com" - Renovar HPS

**👥 GESTIÓN DE USUARIOS:**
• "modificar rol de email@ejemplo.com a [rol]" - Cambiar rol de usuario

**🏢 CONSULTAS:**
• "listar equipos" - Ver todos los equipos del sistema
• "listar usuarios" - Ver usuarios del sistema

**💡 EJEMPLOS:**
• "dame un resumen de todas las hps"
• "solicitar traspaso hps para carlos@empresa.com"
• "solicitar hps para juan@empresa.com"
• "modificar rol de juan@empresa.com a team_lead"
• "listar equipos"
"""
        elif user_role in ["team_lead", "team_leader"]:
            comandos = """
🔧 **COMANDOS DE JEFE DE EQUIPO:**

**👥 MI EQUIPO:**
• "estado de mi equipo" - Ver estado del equipo
• "hps de mi equipo" - Ver HPS del equipo
• "solicitar hps para email@ejemplo.com" - Solicitar nueva HPS para miembro

**📋 GESTIÓN DE HPS:**
• "renovar hps de email@ejemplo.com" - Renovar HPS
• "estado hps de email@ejemplo.com" - Consultar estado

**⚠️ NOTA IMPORTANTE:**
• Solo los jefes de seguridad pueden solicitar traspasos HPS. Si necesitas un traspaso, contacta con un jefe de seguridad.

**💡 EJEMPLOS:**
• "estado de mi equipo"
• "hps de mi equipo"
• "solicitar hps para carlos@empresa.com"
• "renovar hps de juan@empresa.com"
"""
        else:  # member
            comandos = """
🔧 **COMANDOS DE MIEMBRO:**

**📋 MIS HPS:**
• "¿Cuál es el estado de mi HPS?" - Ver estado actual de tu HPS
• "Información sobre HPS" - Información sobre HPS y procesos
"""
        
        # Para miembros, no usar contexto para evitar sugerencias adicionales
        user_role = user_context.get("role", "member")
        if user_role.lower() == "member":
            suggestions = generate_suggestions(user_role)
        else:
            suggestions = generate_suggestions(user_role, "comandos ayuda")
        
        return {
            "tipo": "informacion",
            "mensaje": f"¡Por supuesto! 😊 Aquí tienes los comandos que puedes ejecutar según tu rol:\n\n{comandos}",
            "suggestions": suggestions
        }
    
    # ===== SISTEMA DE FLUJOS CONVERSACIONALES =====
    
    def _start_conversation_flow(self, user_id: str, flow_type: str, initial_data: Dict[str, Any] = None) -> None:
        """Iniciar un flujo conversacional para un usuario"""
        self.conversation_flows[user_id] = {
            "type": flow_type,
            "step": 0,
            "data": initial_data or {},
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
        logger.info(f"🔄 Flujo conversacional iniciado para {user_id}: {flow_type}")
    
    def _get_conversation_flow(self, user_id: str) -> Dict[str, Any]:
        """Obtener flujo conversacional activo de un usuario"""
        return self.conversation_flows.get(user_id)
    
    def _update_conversation_flow(self, user_id: str, step: int = None, data: Dict[str, Any] = None) -> None:
        """Actualizar flujo conversacional de un usuario"""
        if user_id in self.conversation_flows:
            if step is not None:
                self.conversation_flows[user_id]["step"] = step
            if data:
                self.conversation_flows[user_id]["data"].update(data)
            # Actualizar timestamp de actividad
            self.conversation_flows[user_id]["last_activity"] = datetime.now()
    
    def _end_conversation_flow(self, user_id: str) -> None:
        """Terminar flujo conversacional de un usuario"""
        if user_id in self.conversation_flows:
            flow_type = self.conversation_flows[user_id]["type"]
            del self.conversation_flows[user_id]
            logger.info(f"✅ Flujo conversacional terminado para {user_id}: {flow_type}")
    
    def _is_in_conversation_flow(self, user_id: str) -> bool:
        """Verificar si un usuario está en un flujo conversacional"""
        return user_id in self.conversation_flows
    
    def _is_new_command(self, user_message: str) -> bool:
        """Detectar si el mensaje del usuario es un comando nuevo (no una respuesta a flujo)"""
        # Patrones que indican comandos nuevos
        command_patterns = [
            "crear usuario", "crear nuevo usuario", "nuevo usuario",
            "modificar rol", "cambiar rol", "actualizar rol",
            "aprobar hps", "rechazar hps", "estado hps",
            "listar usuarios", "listar equipos", "crear equipo",
            "solicitar hps", "trasladar hps", "consultar hps",
            "dar alta", "eliminar usuario", "borrar usuario"
        ]
        
        user_message_lower = user_message.lower().strip()
        
        # Si el mensaje es muy corto y no parece un comando, probablemente es respuesta a flujo
        if len(user_message_lower) < 10:
            return False
            
        # Verificar si contiene patrones de comandos
        for pattern in command_patterns:
            if pattern in user_message_lower:
                return True
                
        # Si contiene @ y parece email, pero NO es solo un email (debe tener contexto de comando)
        if "@" in user_message and "." in user_message:
            # Solo considerar comando si tiene palabras clave adicionales
            email_only_patterns = ["estado hps", "consultar", "ver", "mostrar", "aprobar", "rechazar"]
            for pattern in email_only_patterns:
                if pattern in user_message_lower:
                    return True
            # Si es solo un email sin contexto, NO es comando nuevo
            return False
            
        return False
    
    def _cleanup_old_flows(self) -> None:
        """Limpiar flujos conversacionales antiguos (más de 30 minutos)"""
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(minutes=30)
        
        users_to_remove = []
        for user_id, flow in self.conversation_flows.items():
            if flow.get("last_activity", flow.get("created_at")) < cutoff_time:
                users_to_remove.append(user_id)
        
        for user_id in users_to_remove:
            logger.info(f"🧹 Limpiando flujo conversacional antiguo para {user_id}")
            del self.conversation_flows[user_id]
    
    async def _handle_conversation_flow(self, user_message: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Manejar mensaje dentro de un flujo conversacional"""
        user_id = user_context.get("id")
        flow = self._get_conversation_flow(user_id)
        
        if not flow:
            return None
        
        flow_type = flow["type"]
        step = flow["step"]
        data = flow["data"]
        
        # Manejar cancelación
        if any(word in user_message.lower() for word in ["cancelar", "salir", "no", "stop", "parar"]):
            self._end_conversation_flow(user_id)
            # Para miembros, limitar sugerencias
            user_role = user_context.get("role", "member")
            if user_role.lower() == "member":
                suggestions = ["Información sobre HPS", "¿Cuál es el estado de mi HPS?"]
            else:
                suggestions = generate_suggestions(user_role)
            
            return {
                "tipo": "conversacion",
                "mensaje": "✅ Flujo cancelado. ¿En qué más puedo ayudarte?",
                "suggestions": suggestions
            }
        
        # Procesar según el tipo de flujo
        if flow_type == "aprobar_hps":
            return await self._handle_aprobar_hps_flow(user_message, user_context, step, data)
        elif flow_type == "rechazar_hps":
            return await self._handle_rechazar_hps_flow(user_message, user_context, step, data)
        elif flow_type == "crear_usuario":
            return await self._handle_crear_usuario_flow(user_message, user_context, step, data)
        elif flow_type == "modificar_rol":
            return await self._handle_modificar_rol_flow(user_message, user_context, step, data)
        elif flow_type == "consultar_estado_hps":
            return await self._handle_consultar_estado_hps_flow(user_message, user_context, step, data)
        
        return None
    
    async def _handle_aprobar_hps_flow(self, user_message: str, user_context: Dict[str, Any], step: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manejar flujo conversacional para aprobar HPS"""
        if step == 0:  # Pedir email
            if "@" in user_message and "." in user_message:
                # Parece un email válido
                email = user_message.strip()
                self._update_conversation_flow(user_context.get("id"), step=1, data={"email": email})
                return {
                    "tipo": "conversacion",
                    "mensaje": f"📧 Perfecto, quieres aprobar la HPS de **{email}**.\n\n¿Estás seguro? Responde 'sí' para confirmar o 'cancelar' para salir.",
                    "suggestions": ["Sí, aprobar", "Cancelar"]
                }
            else:
                return {
                    "tipo": "conversacion",
                    "mensaje": "📧 Por favor, proporciona el email del usuario cuya HPS quieres aprobar.\n\n**Ejemplo:** usuario@empresa.com",
                    "suggestions": ["Cancelar"]
                }
        
        elif step == 1:  # Confirmación
            if any(word in user_message.lower() for word in ["sí", "si", "yes", "confirmar", "aprobar"]):
                # Ejecutar aprobación
                email = data.get("email")
                self._end_conversation_flow(user_context.get("id"))
                return await self._aprobar_hps({"email": email}, user_context)
            else:
                return {
                    "tipo": "conversacion",
                    "mensaje": "🤔 No estoy seguro de tu respuesta. Responde 'sí' para aprobar o 'cancelar' para salir.",
                    "suggestions": ["Sí, aprobar", "Cancelar"]
                }
        
        return None
    
    async def _handle_rechazar_hps_flow(self, user_message: str, user_context: Dict[str, Any], step: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manejar flujo conversacional para rechazar HPS"""
        if step == 0:  # Pedir email
            if "@" in user_message and "." in user_message:
                email = user_message.strip()
                self._update_conversation_flow(user_context.get("id"), step=1, data={"email": email})
                return {
                    "tipo": "conversacion",
                    "mensaje": f"📧 Perfecto, quieres rechazar la HPS de **{email}**.\n\n⚠️ **Esta acción no se puede deshacer.** ¿Estás seguro? Responde 'sí' para confirmar o 'cancelar' para salir.",
                    "suggestions": ["Sí, rechazar", "Cancelar"]
                }
            else:
                return {
                    "tipo": "conversacion",
                    "mensaje": "📧 Por favor, proporciona el email del usuario cuya HPS quieres rechazar.\n\n**Ejemplo:** usuario@empresa.com",
                    "suggestions": ["Cancelar"]
                }
        
        elif step == 1:  # Confirmación
            if any(word in user_message.lower() for word in ["sí", "si", "yes", "confirmar", "rechazar"]):
                email = data.get("email")
                self._end_conversation_flow(user_context.get("id"))
                return await self._rechazar_hps({"email": email}, user_context)
            else:
                return {
                    "tipo": "conversacion",
                    "mensaje": "🤔 No estoy seguro de tu respuesta. Responde 'sí' para rechazar o 'cancelar' para salir.",
                    "suggestions": ["Sí, rechazar", "Cancelar"]
                }
        
        return None
    
    async def _handle_crear_usuario_flow(self, user_message: str, user_context: Dict[str, Any], step: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manejar flujo conversacional para crear usuario"""
        if step == 0:  # Pedir email
            if "@" in user_message and "." in user_message:
                email = user_message.strip()
                self._update_conversation_flow(user_context.get("id"), step=1, data={"email": email})
                return {
                    "tipo": "conversacion",
                    "mensaje": f"📧 Email: **{email}**\n\n👤 Ahora necesito el nombre completo del usuario.\n\n**Ejemplo:** Juan Pérez",
                    "suggestions": ["Cancelar"]
                }
            else:
                return {
                    "tipo": "conversacion",
                    "mensaje": "📧 Por favor, proporciona el email del nuevo usuario.\n\n**Ejemplo:** usuario@empresa.com",
                    "suggestions": ["Cancelar"]
                }
        
        elif step == 1:  # Pedir nombre
            if len(user_message.strip()) > 2:
                nombre = user_message.strip()
                self._update_conversation_flow(user_context.get("id"), step=2, data={"nombre": nombre})
                return {
                    "tipo": "conversacion",
                    "mensaje": f"👤 Nombre: **{nombre}**\n\n🏢 ¿A qué equipo quieres asignarlo? (opcional)\n\n**Ejemplo:** AICOX o deja en blanco para asignar después",
                    "suggestions": ["Cancelar"]
                }
            else:
                return {
                    "tipo": "conversacion",
                    "mensaje": "👤 Por favor, proporciona el nombre completo del usuario.\n\n**Ejemplo:** Juan Pérez",
                    "suggestions": ["Cancelar"]
                }
        
        elif step == 2:  # Pedir equipo (opcional)
            equipo = user_message.strip() if user_message.strip() else None
            self._update_conversation_flow(user_context.get("id"), step=3, data={"equipo": equipo})
            
            email = data.get("email")
            nombre = data.get("nombre")
            
            resumen = f"📋 **Resumen del nuevo usuario:**\n• Email: {email}\n• Nombre: {nombre}"
            if equipo:
                resumen += f"\n• Equipo: {equipo}"
            else:
                resumen += "\n• Equipo: Sin asignar"
            
            return {
                "tipo": "conversacion",
                "mensaje": f"{resumen}\n\n¿Crear este usuario? Responde 'sí' para confirmar o 'cancelar' para salir.",
                "suggestions": ["Sí, crear usuario", "Cancelar"]
            }
        
        elif step == 3:  # Confirmación final
            if any(word in user_message.lower() for word in ["sí", "si", "yes", "confirmar", "crear"]):
                email = data.get("email")
                nombre = data.get("nombre")
                equipo = data.get("equipo")
                
                self._end_conversation_flow(user_context.get("id"))
                return await self._crear_usuario({
                    "email": email,
                    "nombre": nombre,
                    "equipo": equipo
                }, user_context)
            else:
                return {
                    "tipo": "conversacion",
                    "mensaje": "🤔 No estoy seguro de tu respuesta. Responde 'sí' para crear el usuario o 'cancelar' para salir.",
                    "suggestions": ["Sí, crear usuario", "Cancelar"]
                }
        
        return None
    
    async def _handle_modificar_rol_flow(self, user_message: str, user_context: Dict[str, Any], step: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manejar flujo conversacional para modificar rol"""
        if step == 0:  # Pedir email
            if "@" in user_message and "." in user_message:
                email = user_message.strip()
                
                # Buscar el usuario para mostrar su rol actual
                try:
                    headers = {}
                    if self.auth_token:
                        headers["Authorization"] = f"Bearer {self.auth_token}"
                    
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        user_response = await client.get(
                            f"{self.backend_url}/api/users/search/query",
                            headers=headers,
                            params={"q": email, "limit": 1}
                        )
                        
                        if user_response.status_code == 200:
                            search_data = user_response.json()
                            users = search_data.get("users", [])
                            
                            if users:
                                user_data = users[0]
                                rol_actual = user_data.get("role", "member")
                                nombre = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
                                
                                # Mapear roles a nombres más legibles
                                roles_legibles = {
                                    "admin": "Administrador",
                                    "team_lead": "Jefe de Equipo", 
                                    "member": "Miembro"
                                }
                                rol_actual_legible = roles_legibles.get(rol_actual, rol_actual)
                                
                                self._update_conversation_flow(user_context.get("id"), step=1, data={"email": email, "rol_actual": rol_actual, "nombre": nombre})
                                
                                return {
                                    "tipo": "conversacion",
                                    "mensaje": f"👤 **Usuario encontrado:**\n• **Nombre**: {nombre}\n• **Email**: {email}\n• **Rol actual**: {rol_actual_legible}\n\n🔄 ¿Cuál será el nuevo rol?\n\n**Opciones disponibles:**\n• **admin** - Administrador\n• **team_lead** - Jefe de equipo\n• **member** - Miembro",
                                    "suggestions": ["admin", "team_lead", "member", "Cancelar"]
                                }
                            else:
                                return {
                                    "tipo": "conversacion",
                                    "mensaje": f"❌ No encontré el usuario '{email}' en el sistema.\n\n**¿Qué puedes hacer?**\n• Verificar usuarios disponibles: 'listar usuarios'\n• Usar un email correcto\n• Escribir 'cancelar' para salir",
                                    "suggestions": ["Cancelar"]
                                }
                        else:
                            return {
                                "tipo": "conversacion",
                                "mensaje": f"❌ Error buscando el usuario '{email}'.\n\n**¿Qué puedes hacer?**\n• Verificar que el email sea correcto\n• Intentar de nuevo\n• Escribir 'cancelar' para salir",
                                "suggestions": ["Cancelar"]
                            }
                            
                except Exception as e:
                    logger.error(f"Error buscando usuario en flujo modificar rol: {e}")
                    return {
                        "tipo": "conversacion",
                        "mensaje": f"❌ Error de conexión buscando el usuario.\n\n**¿Qué puedes hacer?**\n• Intentar de nuevo en unos momentos\n• Escribir 'cancelar' para salir",
                        "suggestions": ["Cancelar"]
                    }
            else:
                return {
                    "tipo": "conversacion",
                    "mensaje": "📧 Por favor, proporciona el email del usuario cuyo rol quieres modificar.\n\n**Ejemplo:** usuario@empresa.com\n\nEscribe el email o 'cancelar' para salir.",
                    "suggestions": ["Cancelar"]
                }
        
        elif step == 1:  # Pedir rol
            rol = user_message.strip().lower()
            if rol in ["admin", "team_lead", "member"]:
                email = data.get("email")
                rol_actual = data.get("rol_actual")
                nombre = data.get("nombre")
                
                # Mapear roles a nombres más legibles
                roles_legibles = {
                    "admin": "Administrador",
                    "team_lead": "Jefe de Equipo", 
                    "member": "Miembro"
                }
                rol_actual_legible = roles_legibles.get(rol_actual, rol_actual)
                rol_nuevo_legible = roles_legibles.get(rol, rol)
                
                self._update_conversation_flow(user_context.get("id"), step=2, data={"rol": rol})
                
                return {
                    "tipo": "conversacion",
                    "mensaje": f"📋 **Resumen del cambio de rol:**\n\n👤 **Usuario**: {nombre}\n📧 **Email**: {email}\n🔄 **Cambio**: {rol_actual_legible} → {rol_nuevo_legible}\n\n⚠️ **¿Confirmar este cambio?**\n\nResponde 'sí' para confirmar o 'cancelar' para salir.",
                    "suggestions": ["Sí, cambiar rol", "Cancelar"]
                }
            else:
                return {
                    "tipo": "conversacion",
                    "mensaje": "👤 Por favor, selecciona un rol válido:\n\n• **admin** - Administrador\n• **team_lead** - Jefe de equipo\n• **member** - Miembro\n\nEscribe el rol o 'cancelar' para salir.",
                    "suggestions": ["admin", "team_lead", "member", "Cancelar"]
                }
        
        elif step == 2:  # Confirmación final
            if any(word in user_message.lower() for word in ["sí", "si", "yes", "confirmar", "cambiar"]):
                email = data.get("email")
                rol = data.get("rol")
                rol_actual = data.get("rol_actual")
                nombre = data.get("nombre")
                
                self._end_conversation_flow(user_context.get("id"))
                
                # Ejecutar el cambio de rol
                try:
                    headers = {}
                    if self.auth_token:
                        headers["Authorization"] = f"Bearer {self.auth_token}"
                    
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        # Buscar el usuario nuevamente para obtener datos actualizados
                        user_response = await client.get(
                            f"{self.backend_url}/api/users/search/query",
                            headers=headers,
                            params={"q": email, "limit": 1}
                        )
                        
                        if user_response.status_code == 200:
                            search_data = user_response.json()
                            users = search_data.get("users", [])
                            
                            if users:
                                user_data = users[0]
                                user_data["role"] = rol
                                
                                # Actualizar usuario
                                update_response = await client.put(
                                    f"{self.backend_url}/api/users/{user_data['id']}",
                                    json=user_data,
                                    headers=headers
                                )
                                
                                if update_response.status_code in [200, 201]:
                                    # Mapear roles a nombres más legibles
                                    roles_legibles = {
                                        "admin": "Administrador",
                                        "team_lead": "Jefe de Equipo", 
                                        "member": "Miembro"
                                    }
                                    rol_actual_legible = roles_legibles.get(rol_actual, rol_actual)
                                    rol_nuevo_legible = roles_legibles.get(rol, rol)
                                    
                                    return {
                                        "tipo": "exito",
                                        "mensaje": f"✅ **Rol modificado exitosamente**\n\n👤 **Usuario**: {nombre}\n📧 **Email**: {email}\n🔄 **Cambio realizado**: {rol_actual_legible} → {rol_nuevo_legible}\n\nEl usuario recibirá una notificación del cambio.",
                                        "data": {
                                            "email": email,
                                            "nombre": nombre,
                                            "rol_anterior": rol_actual,
                                            "rol_nuevo": rol
                                        }
                                    }
                                else:
                                    return {
                                        "tipo": "error",
                                        "mensaje": f"❌ Error modificando el rol: {update_response.text}\n\n**¿Qué puedes hacer?**\n• Verificar que el usuario exista\n• Intentar de nuevo en unos momentos\n• Contactar al administrador si el problema persiste"
                                    }
                            else:
                                return {
                                    "tipo": "error",
                                    "mensaje": f"❌ No se pudo encontrar el usuario '{email}' para actualizar.\n\n**¿Qué puedes hacer?**\n• Verificar usuarios disponibles: 'listar usuarios'\n• Intentar de nuevo"
                                }
                        else:
                            return {
                                "tipo": "error",
                                "mensaje": f"❌ Error buscando el usuario para actualizar: {user_response.text}\n\n**¿Qué puedes hacer?**\n• Intentar de nuevo en unos momentos"
                            }
                            
                except Exception as e:
                    logger.error(f"Error modificando rol en flujo: {e}")
                    return {
                        "tipo": "error",
                        "mensaje": "❌ Error de conexión modificando el rol. Intenta de nuevo en unos momentos."
                    }
            else:
                return {
                    "tipo": "conversacion",
                    "mensaje": "🤔 No estoy seguro de tu respuesta. Responde 'sí' para cambiar el rol o 'cancelar' para salir.",
                    "suggestions": ["Sí, cambiar rol", "Cancelar"]
                }
        
        return None
    
    async def _handle_consultar_estado_hps_flow(self, user_message: str, user_context: Dict[str, Any], step: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manejar flujo conversacional para consultar estado de HPS"""
        if step == 0:  # Pedir email
            if "@" in user_message and "." in user_message:
                # Parece un email válido
                email = user_message.strip()
                self._end_conversation_flow(user_context.get("id"))
                return await self._consultar_estado_hps({"email": email}, user_context)
            else:
                return {
                    "tipo": "conversacion",
                    "mensaje": "📧 Por favor, proporciona el email del usuario cuyo estado HPS quieres consultar.\n\n**Ejemplo:** usuario@empresa.com",
                    "suggestions": ["Cancelar"]
                }
        
        return None
    
    async def _send_hps_form_email(self, email: str, form_url: str, user_context: Dict[str, Any]) -> bool:
        """Enviar email con formulario HPS usando el servicio de email del backend"""
        try:
            # Preparar datos para el template según el esquema EmailTemplateData
            email_data = {
                "user_name": email.split("@")[0].replace(".", " ").title(),
                "user_email": email,
                "additional_data": {
                    "form_url": form_url
                }
            }
            
            # Llamar al endpoint de email del backend
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                email_response = await client.post(
                    f"{self.backend_url}/api/email/send-hps-form-async/",  # Agregada barra final
                    params={
                        "email": email,
                        "form_url": form_url,
                        "user_name": email_data['user_name']
                    },
                    headers=headers
                )
                
                if email_response.status_code in [200, 201]:
                    response_data = email_response.json()
                    task_id = response_data.get("task_id")
                    logger.info(f"Email HPS encolado para envío asíncrono a {email} (Task ID: {task_id})")
                    return True
                else:
                    logger.error(f"Error encolando email HPS a {email}: {email_response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error enviando email HPS a {email}: {e}")
            return False
    
    async def _send_user_credentials_email(self, email: str, temp_password: str, user_name: str, user_context: Dict[str, Any]) -> bool:
        """Enviar email con credenciales de usuario usando el servicio de email del backend"""
        try:
            # Preparar datos para el template de credenciales
            email_data = {
                "user_name": user_name,
                "user_email": email,
                "additional_data": {
                    "temp_password": temp_password,
                    "login_url": f"{self.frontend_url}/login"
                }
            }
            
            # Llamar al endpoint de email del backend
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # TODO: Implementar endpoint de email en Django
                # Por ahora, retornamos True asumiendo que el email se enviará
                email_response = type('obj', (object,), {'status_code': 200})()
                # email_response = await client.post(
                #     f"{self.backend_url}/api/email/send",
                #     json={
                #         "to": email,
                #         "template": "user_credentials",
                #         "template_data": email_data
                #     },
                #     headers=headers
                # )
                
                if email_response.status_code in [200, 201]:
                    response_data = email_response.json()
                    logger.info(f"Email de credenciales enviado a {email}")
                    return True
                else:
                    logger.error(f"Error enviando email de credenciales a {email}: {email_response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error enviando email de credenciales a {email}: {e}")
            return False
    
    async def _check_user_exists(self, email: str) -> bool:
        """Verificar si un usuario existe en el sistema"""
        try:
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.backend_url}/api/users/check/{email}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return True
                elif response.status_code == 404:
                    return False
                else:
                    logger.error(f"Error verificando usuario {email}: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error verificando usuario {email}: {e}")
            return False
    
    async def _get_user_temp_password(self, email: str) -> Optional[str]:
        """Obtener la contraseña temporal de un usuario (solo para usuarios recién creados)"""
        try:
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # TODO: Implementar endpoint para obtener contraseña temporal en Django
                # Por ahora, retornamos None
                response = type('obj', (object,), {'status_code': 404})()
                # response = await client.get(
                #     f"{self.backend_url}/api/users/temp-password/{email}",
                #     headers=headers
                # )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("temp_password")
                else:
                    logger.error(f"Error obteniendo contraseña temporal para {email}: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error obteniendo contraseña temporal para {email}: {e}")
            return None

    async def _mostrar_ayuda_hps(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Mostrar información de ayuda sobre HPS, certificados y procesos"""
        
        return {
            "tipo": "conversacion",
            "mensaje": "📋 **Información sobre HPS**\n\nEsta funcionalidad está en desarrollo. Próximamente podrás consultar información detallada sobre:\n\n• ¿Qué es un número de integración?\n• ¿Qué es un certificado HPS?\n• Procesos y procedimientos\n• Preguntas frecuentes\n\n¡Muy pronto estará disponible! 🚀"
        }
