"""
Procesador de comandos para el Agente IA (Django)
Versión simplificada para pruebas - se expandirá según necesidad
"""
import logging
import os
import re
from typing import Dict, Any, Optional
from datetime import datetime
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from hps_core.models import HpsUserProfile, HpsTeam, HpsRequest, HpsRole

logger = logging.getLogger(__name__)
User = get_user_model()


def is_email_only(message: str) -> Optional[str]:
    """Detecta si el mensaje es solo un email válido"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    clean_message = message.strip()
    if re.match(email_pattern, clean_message):
        return clean_message
    return None


class CommandProcessor:
    """Procesador que ejecuta comandos específicos del sistema HPS usando Django ORM"""
    
    def __init__(self):
        """Inicializar procesador de comandos"""
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
        self.backend_url = os.getenv("BACKEND_URL", "http://cryptotrace-backend:8080")
        logger.info(f"CommandProcessor inicializado - Backend: {self.backend_url}")
        
        # Flujos conversacionales activos por usuario
        self.conversation_flows = {}
    
    async def execute_command(self, ai_response: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar comando basado en la respuesta del AI"""
        
        user_id = user_context.get("id")
        user_message = ai_response.get("user_message", "")
        
        # Detectar si el mensaje es solo un email
        if user_message:
            email = is_email_only(user_message)
            if email:
                logger.info(f"Email detectado: {email} - Interpretando como consulta de estado HPS")
                return await self._consultar_estado_hps({"email": email}, user_context)
        
        if ai_response.get("tipo") != "comando":
            return ai_response
        
        accion = ai_response.get("accion")
        parametros = ai_response.get("parametros", {})
        parametros["user_message"] = user_message
        
        try:
            # Enrutar comando a la función correspondiente
            if accion == "consultar_estado_hps":
                return await self._consultar_estado_hps(parametros, user_context)
            elif accion == "consultar_hps_equipo":
                return await self._consultar_hps_equipo(user_context)
            elif accion == "consultar_todas_hps":
                return await self._consultar_todas_hps(user_context)
            elif accion == "listar_usuarios":
                return await self._listar_usuarios(user_context)
            elif accion == "listar_equipos":
                return await self._listar_equipos(user_context)
            elif accion == "solicitar_hps":
                # Detectar si es traspaso del mensaje
                user_message_lower = user_message.lower()
                is_transfer = any(word in user_message_lower for word in ["traslado", "traspaso", "trasladar", "traspasar", "transfer"])
                return await self._solicitar_hps(parametros, user_context, is_transfer=is_transfer)
            elif accion in ["trasladar_hps", "traspasar_hps"]:
                return await self._solicitar_hps(parametros, user_context, is_transfer=True)
            elif accion == "comandos_disponibles":
                return await self._mostrar_comandos_disponibles(user_context)
            elif accion == "ayuda_hps":
                return await self._mostrar_ayuda_hps(user_context)
            else:
                # Comando no reconocido
                user_role = user_context.get("role", "").lower()
                return {
                    "tipo": "conversacion",
                    "mensaje": f"Entiendo que quieres '{accion}', pero no reconozco ese comando específico. 😊\n\nPuedes preguntar '¿Qué comandos puedes ejecutar?' para ver los comandos disponibles según tu rol."
                }
                
        except Exception as e:
            logger.error(f"Error ejecutando comando {accion}: {e}")
            return {
                "tipo": "conversacion",
                "mensaje": "¡Ups! 😅 Parece que hubo un pequeño problema procesando tu solicitud. Por favor, intenta de nuevo."
            }
    
    @database_sync_to_async
    def _get_user_by_email(self, email: str):
        """Obtener usuario por email"""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
    
    async def _consultar_estado_hps(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Consultar estado de HPS de un usuario"""
        email = parametros.get("email")
        user_role = user_context.get("role", "").lower()
        current_user_email = user_context.get("email", "")
        
        # Si no hay email, usar el email del usuario actual
        if not email:
            email = current_user_email
        
        if not email:
            return {
                "tipo": "conversacion",
                "mensaje": "📧 Necesito el email del usuario para consultar su estado de HPS.\n\n**Por favor, proporciona el email:**\n• Ejemplo: 'estado hps de usuario@empresa.com'\n• O simplemente escribe: 'usuario@empresa.com'"
            }
        
        try:
            user = await self._get_user_by_email(email)
            if not user:
                return {
                    "tipo": "conversacion",
                    "mensaje": f"❌ No se encontró ningún usuario con el email {email}."
                }
            
            # Obtener HPS del usuario
            hps_request = await self._get_user_hps(user.id)
            
            if not hps_request:
                return {
                    "tipo": "conversacion",
                    "mensaje": f"ℹ️ El usuario {email} no tiene ninguna solicitud HPS registrada."
                }
            
            status = hps_request.get('status', 'unknown')
            status_emoji = {
                'pending': '⏳',
                'approved': '✅',
                'rejected': '❌',
                'expired': '⏰'
            }.get(status, '❓')
            
            return {
                "tipo": "exito",
                "mensaje": f"{status_emoji} **Estado HPS de {email}:**\n\n• **Estado:** {status}\n• **Fecha de solicitud:** {hps_request.get('created_at', 'N/A')}\n• **Última actualización:** {hps_request.get('updated_at', 'N/A')}",
                "data": hps_request
            }
            
        except Exception as e:
            logger.error(f"Error consultando estado HPS: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Hubo un error consultando el estado de HPS. Por favor, intenta de nuevo."
            }
    
    @database_sync_to_async
    def _get_user_hps(self, user_id):
        """Obtener HPS del usuario"""
        try:
            hps = HpsRequest.objects.filter(user_id=user_id).order_by('-created_at').first()
            if hps:
                return {
                    'id': str(hps.id),
                    'status': hps.status,
                    'created_at': hps.created_at.isoformat() if hps.created_at else None,
                    'updated_at': hps.updated_at.isoformat() if hps.updated_at else None,
                }
            return None
        except Exception as e:
            logger.error(f"Error obteniendo HPS: {e}")
            return None
    
    async def _consultar_hps_equipo(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Consultar HPS del equipo del usuario"""
        user_id = user_context.get("id")
        
        try:
            hps_list = await self._get_team_hps(user_id)
            
            if not hps_list:
                return {
                    "tipo": "conversacion",
                    "mensaje": "ℹ️ No hay solicitudes HPS en tu equipo."
                }
            
            message = f"📋 **HPS de tu equipo:**\n\n"
            for hps in hps_list[:10]:  # Limitar a 10
                status_emoji = {
                    'pending': '⏳',
                    'approved': '✅',
                    'rejected': '❌'
                }.get(hps.get('status', ''), '❓')
                message += f"{status_emoji} {hps.get('email', 'N/A')} - {hps.get('status', 'N/A')}\n"
            
            if len(hps_list) > 10:
                message += f"\n... y {len(hps_list) - 10} más."
            
            return {
                "tipo": "exito",
                "mensaje": message,
                "data": {"hps_list": hps_list}
            }
            
        except Exception as e:
            logger.error(f"Error consultando HPS del equipo: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Hubo un error consultando las HPS de tu equipo."
            }
    
    @database_sync_to_async
    def _get_team_hps(self, user_id):
        """Obtener HPS del equipo del usuario"""
        try:
            user = User.objects.get(id=user_id)
            if not hasattr(user, 'hps_profile') or not user.hps_profile.team:
                return []
            
            team = user.hps_profile.team
            team_users = HpsUserProfile.objects.filter(team=team).values_list('user_id', flat=True)
            hps_requests = HpsRequest.objects.filter(user_id__in=team_users).order_by('-created_at')[:50]
            
            return [
                {
                    'email': hps.user.email if hps.user else 'N/A',
                    'status': hps.status,
                    'created_at': hps.created_at.isoformat() if hps.created_at else None,
                }
                for hps in hps_requests
            ]
        except Exception as e:
            logger.error(f"Error obteniendo HPS del equipo: {e}")
            return []
    
    async def _consultar_todas_hps(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Consultar todas las HPS del sistema (solo admin)"""
        user_role = user_context.get("role", "").lower()
        
        if user_role != "admin":
            return {
                "tipo": "conversacion",
                "mensaje": "❌ Solo los administradores pueden ver todas las HPS del sistema."
            }
        
        try:
            stats = await self._get_all_hps_stats()
            
            return {
                "tipo": "exito",
                "mensaje": f"📊 **Resumen de todas las HPS del sistema:**\n\n• **Total:** {stats.get('total', 0)}\n• **Pendientes:** {stats.get('pending', 0)}\n• **Aprobadas:** {stats.get('approved', 0)}\n• **Rechazadas:** {stats.get('rejected', 0)}",
                "data": stats
            }
            
        except Exception as e:
            logger.error(f"Error consultando todas las HPS: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Hubo un error consultando las estadísticas."
            }
    
    @database_sync_to_async
    def _get_all_hps_stats(self):
        """Obtener estadísticas de todas las HPS"""
        try:
            total = HpsRequest.objects.count()
            pending = HpsRequest.objects.filter(status='pending').count()
            approved = HpsRequest.objects.filter(status='approved').count()
            rejected = HpsRequest.objects.filter(status='rejected').count()
            
            return {
                'total': total,
                'pending': pending,
                'approved': approved,
                'rejected': rejected
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {'total': 0, 'pending': 0, 'approved': 0, 'rejected': 0}
    
    async def _listar_usuarios(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Listar usuarios del sistema"""
        user_role = user_context.get("role", "").lower()
        
        if user_role not in ["admin", "team_lead", "team_leader"]:
            return {
                "tipo": "conversacion",
                "mensaje": "❌ No tienes permisos para listar usuarios."
            }
        
        try:
            users = await self._get_users_list(user_context)
            
            if not users:
                return {
                    "tipo": "conversacion",
                    "mensaje": "ℹ️ No se encontraron usuarios."
                }
            
            message = f"👥 **Usuarios del sistema:**\n\n"
            for user in users[:20]:  # Limitar a 20
                message += f"• {user.get('email', 'N/A')} - {user.get('role', 'N/A')}\n"
            
            if len(users) > 20:
                message += f"\n... y {len(users) - 20} más."
            
            return {
                "tipo": "exito",
                "mensaje": message,
                "data": {"users": users}
            }
            
        except Exception as e:
            logger.error(f"Error listando usuarios: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Hubo un error listando los usuarios."
            }
    
    @database_sync_to_async
    def _get_users_list(self, user_context: Dict[str, Any]):
        """Obtener lista de usuarios"""
        try:
            user_role = user_context.get("role", "").lower()
            user_id = user_context.get("id")
            
            if user_role == "admin":
                # Admin ve todos los usuarios
                profiles = HpsUserProfile.objects.select_related('user', 'role', 'team').all()[:100]
            else:
                # Team lead ve solo usuarios de su equipo
                user = User.objects.get(id=user_id)
                if hasattr(user, 'hps_profile') and user.hps_profile.team:
                    team = user.hps_profile.team
                    profiles = HpsUserProfile.objects.filter(team=team).select_related('user', 'role')[:100]
                else:
                    return []
            
            return [
                {
                    'email': profile.user.email if profile.user else 'N/A',
                    'role': profile.role.name if profile.role else 'N/A',
                    'team': profile.team.name if profile.team else 'N/A',
                }
                for profile in profiles
            ]
        except Exception as e:
            logger.error(f"Error obteniendo lista de usuarios: {e}")
            return []
    
    async def _listar_equipos(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Listar equipos del sistema"""
        try:
            teams = await self._get_teams_list()
            
            if not teams:
                return {
                    "tipo": "conversacion",
                    "mensaje": "ℹ️ No se encontraron equipos."
                }
            
            message = f"👥 **Equipos del sistema:**\n\n"
            for team in teams:
                message += f"• {team.get('name', 'N/A')} - {team.get('member_count', 0)} miembros\n"
            
            return {
                "tipo": "exito",
                "mensaje": message,
                "data": {"teams": teams}
            }
            
        except Exception as e:
            logger.error(f"Error listando equipos: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Hubo un error listando los equipos."
            }
    
    @database_sync_to_async
    def _get_teams_list(self):
        """Obtener lista de equipos"""
        try:
            teams = HpsTeam.objects.filter(is_active=True).all()
            
            return [
                {
                    'name': team.name,
                    'member_count': team.member_count,
                }
                for team in teams
            ]
        except Exception as e:
            logger.error(f"Error obteniendo lista de equipos: {e}")
            return []
    
    async def _solicitar_hps(self, parametros: Dict[str, Any], user_context: Dict[str, Any], is_transfer: bool = False) -> Dict[str, Any]:
        """
        Solicitar HPS para un usuario.
        
        Hay dos tipos de solicitudes:
        1. Solicitud de NUEVA HPS: "solicitar hps", "envío hps", "enviar hps"
        2. Solicitud de TRASPASO HPS: "trasladar hps", "traspasar hps", "envío traspaso hps", "enviar traspaso hps"
        """
        user_role = user_context.get("role", "").lower()
        email = parametros.get("email")
        user_message = parametros.get("user_message", "").lower()
        
        # Detectar tipo de solicitud del mensaje si no se especifica explícitamente
        # Buscar palabras clave de traspaso
        if not is_transfer:
            is_transfer = any(word in user_message for word in [
                "traslado", "traspaso", "trasladar", "traspasar", "transfer",
                "envío traspaso", "enviar traspaso", "envia traspaso", "envio traspaso",
                "envío traslado", "enviar traslado", "envia traslado", "envio traslado"
            ])
        
        # Detectar renovación (por ahora no implementada, pero detectamos para futuro)
        is_renewal = any(word in user_message for word in ["renovacion", "renovación", "renovar", "renovar hps", "renovación hps"])
        is_new = not (is_transfer or is_renewal)
        
        # Verificar permisos: traspasos solo para admin y jefes de seguridad
        if is_transfer:
            user_role_normalized = user_role.strip().lower() if user_role else ""
            allowed_roles = ["admin", "jefe_seguridad", "jefe_seguridad_suplente"]
            
            if user_role_normalized not in allowed_roles:
                return {
                    "tipo": "error",
                    "mensaje": f"❌ No tienes permisos para solicitar traspasos HPS. Tu rol actual es: '{user_role}'. Solo los administradores y jefes de seguridad pueden realizar esta acción."
                }
        else:
            # Para nuevas HPS y renovaciones
            if user_role not in ["admin", "team_lead", "team_leader", "jefe_seguridad", "jefe_seguridad_suplente", "crypto"]:
                return {
                    "tipo": "error",
                    "mensaje": "❌ No tienes permisos para solicitar HPS para otros usuarios."
                }
        
        if not email:
            if is_transfer:
                return {
                    "tipo": "conversacion",
                    "mensaje": "📧 Para solicitar un **traspaso de HPS**, necesito el email del usuario.\n\n**Por favor, proporciona el email:**\n• Ejemplo: 'envío traspaso hps a usuario@empresa.com'\n• O: 'trasladar hps de usuario@empresa.com'\n• O simplemente escribe: 'usuario@empresa.com'"
                }
            else:
                return {
                    "tipo": "conversacion",
                    "mensaje": "📧 Para solicitar una **nueva HPS**, necesito el email del usuario.\n\n**Por favor, proporciona el email:**\n• Ejemplo: 'envío hps a usuario@empresa.com'\n• O: 'solicitar hps para usuario@empresa.com'\n• O simplemente escribe: 'usuario@empresa.com'"
                }
        
        try:
            # Obtener usuario que solicita
            requesting_user = await self._get_user_by_id(user_context.get("id"))
            if not requesting_user:
                return {
                    "tipo": "error",
                    "mensaje": "❌ Error: Usuario no encontrado."
                }
            
            # Determinar propósito según el tipo
            if is_transfer:
                purpose = "Traspaso HPS"
                form_type = "traslado"
            elif is_renewal:
                purpose = "Renovación HPS"
                form_type = "renovacion"
            else:
                purpose = "Nueva HPS"
                form_type = "nueva"
            
            # Crear token HPS
            token = await self._create_hps_token(email, requesting_user, purpose)
            
            if not token:
                return {
                    "tipo": "error",
                    "mensaje": "❌ Error generando token HPS. Por favor, intenta de nuevo."
                }
            
            # Generar URL del formulario
            url = f"{self.frontend_url}/hps-form?token={token.token}&email={email}&type={form_type}"
            
            # Verificar si el usuario existe
            user_exists = await self._check_user_exists(email)
            
            # Enviar email con formulario
            user_name = email.split("@")[0].replace(".", " ").title()
            email_sent = await self._send_hps_form_email(email, url, user_name)
            
            if not email_sent:
                logger.warning(f"Email no enviado para {email}, pero token creado")
            
            # Mensaje según el tipo de solicitud
            if is_transfer:
                message = f"✅ Se ha enviado la **solicitud de traspaso HPS** a {email}.\n\n📧 El correo contiene el formulario de traspaso que el usuario debe completar.\n\nEl enlace es válido por 72 horas."
            elif is_renewal:
                message = f"✅ Se ha enviado la **solicitud de renovación HPS** a {email}.\n\n📧 El correo contiene el formulario de renovación que el usuario debe completar.\n\nEl enlace es válido por 72 horas."
            else:
                # Solicitud de nueva HPS
                if user_role in ["team_lead", "team_leader"]:
                    message = f"✅ Se ha enviado la **solicitud de nueva HPS** a {email}.\n\n📧 El correo contiene el formulario de nueva HPS que el usuario debe completar.\n\n📋 **El usuario se registrará automáticamente en tu equipo** cuando complete el formulario.\n\nEl enlace es válido por 72 horas."
                else:
                    message = f"✅ Se ha enviado la **solicitud de nueva HPS** a {email}.\n\n📧 El correo contiene el formulario de nueva HPS que el usuario debe completar.\n\nEl enlace es válido por 72 horas."
            
            if not user_exists:
                message += "\n\n🔑 Si el usuario no existe, se creará automáticamente y se le enviarán las credenciales de acceso."
            
            return {
                "tipo": "exito",
                "mensaje": message,
                "data": {
                    "url": url,
                    "token": token.token,
                    "email": email,
                    "expires_at": token.expires_at.isoformat() if token.expires_at else None,
                    "email_sent": email_sent,
                    "user_exists": user_exists,
                    "form_type": form_type
                }
            }
            
        except Exception as e:
            logger.error(f"Error solicitando HPS: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "tipo": "error",
                "mensaje": "❌ Hubo un error procesando la solicitud. Por favor, intenta de nuevo."
            }
    
    @database_sync_to_async
    def _get_user_by_id(self, user_id: str):
        """Obtener usuario por ID"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    @database_sync_to_async
    def _create_hps_token(self, email: str, requested_by_user, purpose: str = None, hours_valid: int = 72):
        """Crear token HPS"""
        try:
            from hps_core.models import HpsToken
            token = HpsToken.create_token(
                email=email,
                requested_by_user=requested_by_user,
                purpose=purpose or "",
                hours_valid=hours_valid
            )
            logger.info(f"✅ Token HPS creado para {email}: {token.token[:20]}...")
            return token
        except Exception as e:
            logger.error(f"Error creando token HPS: {e}")
            return None
    
    @database_sync_to_async
    def _check_user_exists(self, email: str) -> bool:
        """Verificar si un usuario existe"""
        try:
            return User.objects.filter(email=email).exists()
        except Exception as e:
            logger.error(f"Error verificando usuario: {e}")
            return False
    
    @database_sync_to_async
    def _send_hps_form_email(self, email: str, form_url: str, user_name: str) -> bool:
        """Enviar email con formulario HPS"""
        try:
            from hps_core.email_service import HpsEmailService
            email_service = HpsEmailService()
            success = email_service.send_hps_form_email(email, form_url, user_name)
            if success:
                logger.info(f"✅ Email con formulario HPS enviado a {email}")
            else:
                logger.warning(f"⚠️ Email no enviado a {email}")
            return success
        except Exception as e:
            logger.error(f"Error enviando email HPS: {e}")
            return False
    
    async def _mostrar_comandos_disponibles(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Mostrar comandos disponibles según el rol"""
        user_role = user_context.get("role", "").lower()
        
        if user_role == "admin":
            message = """🔹 **Comandos disponibles (ADMINISTRADOR):**

**📋 Consultas:**
• `estado hps de [email]` - Consultar estado de HPS
• `hps de mi equipo` - Ver HPS del equipo
• `todas las hps` - Estadísticas globales
• `listar usuarios` - Listar todos los usuarios
• `listar equipos` - Listar todos los equipos

**📧 Solicitudes HPS:**
• `envío hps a [email]` o `solicitar hps para [email]` - Solicitar **nueva HPS** (envía formulario)
• `envío traspaso hps a [email]` o `trasladar hps de [email]` - Solicitar **traspaso HPS** (envía formulario)

¿Qué comando quieres ejecutar? 🤔"""
        elif user_role in ["jefe_seguridad", "jefe_seguridad_suplente"]:
            message = """🔹 **Comandos disponibles (JEFE DE SEGURIDAD):**

**📋 Consultas:**
• `estado hps de [email]` - Consultar estado de HPS
• `todas las hps` - Estadísticas globales
• `listar equipos` - Ver todos los equipos

**📧 Solicitudes HPS:**
• `envío hps a [email]` o `solicitar hps para [email]` - Solicitar **nueva HPS** (envía formulario)
• `envío traspaso hps a [email]` o `trasladar hps de [email]` - Solicitar **traspaso HPS** (envía formulario)

¿Qué comando quieres ejecutar? 🤔"""
        elif user_role in ["team_lead", "team_leader"]:
            message = """🔹 **Comandos disponibles (JEFE DE EQUIPO):**

**📋 Consultas:**
• `estado hps de [email]` - Consultar estado de HPS
• `hps de mi equipo` - Ver HPS de tu equipo
• `listar usuarios` - Ver usuarios de tu equipo
• `listar equipos` - Ver todos los equipos

**📧 Solicitudes HPS:**
• `envío hps a [email]` o `solicitar hps para [email]` - Solicitar **nueva HPS** (envía formulario)

⚠️ **Nota:** Solo los jefes de seguridad pueden solicitar traspasos HPS.

¿Qué comando quieres ejecutar? 🤔"""
        else:
            message = """🔹 **Comandos disponibles (MIEMBRO):**

• `estado de mi hps` - Ver estado de tu HPS
• `estado hps de [email]` - Consultar estado de HPS (si tienes permisos)

¿Qué comando quieres ejecutar? 🤔"""
        
        return {
            "tipo": "conversacion",
            "mensaje": message
        }
    
    async def _mostrar_ayuda_hps(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Mostrar ayuda sobre HPS"""
        message = """📚 **Información sobre HPS (Habilitación Personal de Seguridad):**

HPS es un sistema de certificación de seguridad que permite gestionar las habilitaciones de personal.

**Componentes principales:**
• **Solicitud HPS:** Proceso para obtener una habilitación
• **Estado:** Puede ser pendiente, aprobada, rechazada o expirada
• **Equipos:** Organización de usuarios en equipos
• **Roles:** Diferentes niveles de acceso (admin, team_lead, member)

**¿Necesitas más información?** Pregunta '¿Qué comandos puedes ejecutar?' para ver los comandos disponibles según tu rol."""
        
        return {
            "tipo": "conversacion",
            "mensaje": message
        }

