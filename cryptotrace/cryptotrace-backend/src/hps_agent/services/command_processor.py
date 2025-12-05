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
        accion = ai_response.get("accion", "")
        
        logger.info(f"🔧 execute_command: accion={accion}, user_message={user_message[:50]}")
        
        # PRIMERO: Verificar si hay un flujo activo para este usuario (esto tiene prioridad)
        flow_key = f"{user_id}_flow"
        logger.info(f"🔍 Verificando flujo activo: flow_key={flow_key}, existe={flow_key in self.conversation_flows}")
        if flow_key in self.conversation_flows:
            flow = self.conversation_flows[flow_key]
            flow_type = flow.get("type")
            
            # Si hay un flujo activo de crear_usuario
            if flow_type == "crear_usuario":
                logger.info(f"🔄 Procesando flujo crear_usuario, user_message={user_message}")
                email = is_email_only(user_message)
                if email:
                    logger.info(f"✅ Email detectado en flujo: {email}")
                    # Continuar con el flujo de crear usuario
                    parametros = {"email": email, "user_message": user_message}
                    del self.conversation_flows[flow_key]  # Limpiar flujo
                    return await self._crear_usuario(parametros, user_context)
                else:
                    # Seguir esperando el email
                    return {
                        "tipo": "conversacion",
                        "mensaje": "📧 Necesito el email del usuario para crearlo.\n\n**Por favor, proporciona el email:**\n• Ejemplo: usuario@empresa.com"
                    }
            
            # Si hay un flujo activo de modificar_rol
            elif flow_type == "modificar_rol":
                email = flow.get("email")
                
                if not email:
                    # Intentar extraer email del mensaje (puede venir solo email o email + rol)
                    email = is_email_only(user_message)
                    if not email:
                        # Intentar extraer email del inicio del mensaje (formato: "email rol")
                        words = user_message.strip().split()
                        for word in words:
                            if "@" in word and "." in word:
                                email = word
                                break
                    
                    if email:
                        # Verificar si hay un rol después del email
                        remaining_text = user_message.replace(email, "").strip()
                        if remaining_text:
                            # El usuario proporcionó email y rol en el mismo mensaje
                            new_role = remaining_text.split()[0]  # Tomar la primera palabra como rol
                            parametros = {"email": email, "rol": new_role, "user_message": user_message}
                            del self.conversation_flows[flow_key]  # Limpiar flujo
                            logger.info(f"🔄 Flujo modificar_rol: email y rol proporcionados juntos: {email} -> {new_role}")
                            return await self._modificar_rol(parametros, user_context)
                        else:
                            # Solo email, guardar y pedir rol
                            self.conversation_flows[flow_key]["email"] = email
                            logger.info(f"🔄 Flujo modificar_rol: email recibido: {email}, esperando rol")
                            return {
                                "tipo": "conversacion",
                                "mensaje": f"✅ Email recibido: {email}\n\n📋 Ahora necesito el nuevo rol para este usuario.\n\n**Por favor, proporciona el rol:**\n• Ejemplo: team_lead, member, admin, crypto, etc."
                            }
                    else:
                        return {
                            "tipo": "conversacion",
                            "mensaje": "📧 Necesito el email del usuario cuyo rol quieres modificar.\n\n**Por favor, proporciona el email:**\n• Ejemplo: usuario@empresa.com\n\nTambién puedes proporcionar email y rol juntos: 'usuario@empresa.com team_lead'"
                        }
                else:
                    # Ya tenemos email, esperar rol
                    new_role = user_message.strip()
                    if new_role and new_role.lower() not in ["cancelar", "cancel", "no", "n"]:
                        parametros = {"email": email, "rol": new_role, "user_message": user_message}
                        del self.conversation_flows[flow_key]  # Limpiar flujo
                        logger.info(f"🔄 Flujo modificar_rol: rol recibido: {new_role} para {email}")
                        return await self._modificar_rol(parametros, user_context)
                    else:
                        return {
                            "tipo": "conversacion",
                            "mensaje": f"📋 Necesito el nuevo rol para {email}.\n\n**Por favor, proporciona el rol:**\n• Ejemplo: team_lead, member, admin, crypto, etc.\n\n(Escribe 'cancelar' si quieres cancelar esta operación)"
                        }
        
        # Detectar si el mensaje es solo un email (solo si NO hay flujo activo)
        # IMPORTANTE: Esta verificación debe ir DESPUÉS de verificar flujos activos
        if user_message and flow_key not in self.conversation_flows:
            email = is_email_only(user_message)
            if email:
                logger.info(f"Email detectado (sin flujo activo): {email} - Interpretando como consulta de estado HPS")
                return await self._consultar_estado_hps({"email": email}, user_context)
        
        if ai_response.get("tipo") != "comando":
            return ai_response
        
        parametros = ai_response.get("parametros", {})
        parametros["user_message"] = user_message
        
        accion = ai_response.get("accion")
        
        # Si la acción es "continuar_flujo", el flujo ya se procesó arriba
        # Esto no debería llegar aquí, pero por si acaso retornamos
        if accion == "continuar_flujo":
            return {
                "tipo": "conversacion",
                "mensaje": "Lo siento, hubo un problema procesando tu solicitud. Por favor, intenta de nuevo."
            }
        
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
            elif accion == "crear_usuario":
                return await self._crear_usuario(parametros, user_context)
            elif accion == "crear_equipo":
                return await self._crear_equipo(parametros, user_context)
            elif accion == "asignar_usuario_equipo":
                return await self._asignar_usuario_equipo(parametros, user_context)
            elif accion == "modificar_rol":
                return await self._modificar_rol(parametros, user_context)
            elif accion == "aprobar_hps":
                return await self._aprobar_hps(parametros, user_context)
            elif accion == "rechazar_hps":
                return await self._rechazar_hps(parametros, user_context)
            elif accion == "renovar_hps":
                return await self._renovar_hps(parametros, user_context)
            elif accion == "dar_alta_jefe_equipo":
                return await self._dar_alta_jefe_equipo(parametros, user_context)
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
        """Consultar todas las HPS del sistema (admin, jefe_seguridad, jefe_seguridad_suplente)"""
        user_role = user_context.get("role", "").lower()
        user_id = user_context.get("id")
        
        # Obtener rol del perfil HPS si está disponible (más confiable que el token)
        hps_role = await self._get_user_hps_role(user_id)
        if hps_role:
            user_role = hps_role.lower()
        
        logger.info(f"🔍 _consultar_todas_hps: user_role={user_role}, user_id={user_id}, hps_role={hps_role}")
        
        # Permitir acceso a admin, jefe_seguridad y jefe_seguridad_suplente
        allowed_roles = ["admin", "jefe_seguridad", "jefe_seguridad_suplente", "security_chief"]
        
        if user_role not in allowed_roles:
            logger.warning(f"❌ Acceso denegado: user_role={user_role} no está en {allowed_roles}")
            return {
                "tipo": "conversacion",
                "mensaje": "❌ Solo los administradores y jefes de seguridad pueden ver todas las HPS del sistema."
            }
        
        try:
            stats = await self._get_all_hps_stats()
            
            mensaje = f"📊 **Resumen de todas las HPS del sistema:**\n\n"
            mensaje += f"• **Total:** {stats.get('total', 0)}\n"
            mensaje += f"• **Pendientes:** {stats.get('pending', 0)}\n"
            mensaje += f"• **Esperando DPS:** {stats.get('waiting_dps', 0)}\n"
            mensaje += f"• **Enviadas:** {stats.get('submitted', 0)}\n"
            mensaje += f"• **Aprobadas:** {stats.get('approved', 0)}\n"
            mensaje += f"• **Rechazadas:** {stats.get('rejected', 0)}\n"
            mensaje += f"• **Expiradas:** {stats.get('expired', 0)}"
            
            return {
                "tipo": "exito",
                "mensaje": mensaje,
                "data": stats
            }
            
        except Exception as e:
            logger.error(f"Error consultando todas las HPS: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Hubo un error consultando las estadísticas."
            }
    
    @database_sync_to_async
    def _get_user_hps_role(self, user_id: str):
        """Obtener rol del usuario desde su perfil HPS"""
        try:
            user = User.objects.get(id=user_id)
            logger.info(f"🔍 Obteniendo rol HPS para usuario {user.email} (ID: {user_id})")
            if hasattr(user, 'hps_profile'):
                profile = user.hps_profile
                if profile.role:
                    role_name = profile.role.name
                    logger.info(f"✅ Rol HPS encontrado: {role_name}")
                    return role_name
                else:
                    logger.warning(f"⚠️ Usuario {user.email} tiene perfil HPS pero sin rol asignado")
            else:
                logger.warning(f"⚠️ Usuario {user.email} no tiene perfil HPS")
            return None
        except User.DoesNotExist:
            logger.error(f"❌ Usuario con ID {user_id} no encontrado")
            return None
        except Exception as e:
            logger.error(f"Error obteniendo rol HPS del usuario: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    @database_sync_to_async
    def _get_all_hps_stats(self):
        """Obtener estadísticas de todas las HPS"""
        try:
            total = HpsRequest.objects.count()
            pending = HpsRequest.objects.filter(status='pending').count()
            submitted = HpsRequest.objects.filter(status='submitted').count()
            waiting_dps = HpsRequest.objects.filter(status='waiting_dps').count()
            approved = HpsRequest.objects.filter(status='approved').count()
            rejected = HpsRequest.objects.filter(status='rejected').count()
            expired = HpsRequest.objects.filter(status='expired').count()
            
            return {
                'total': total,
                'pending': pending,
                'submitted': submitted,
                'waiting_dps': waiting_dps,
                'approved': approved,
                'rejected': rejected,
                'expired': expired
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {
                'total': 0, 
                'pending': 0, 
                'submitted': 0,
                'waiting_dps': 0,
                'approved': 0, 
                'rejected': 0,
                'expired': 0
            }
    
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

**👥 Gestión de Usuarios:**
• `crear usuario [email]` - Crear nuevo usuario
• `modificar rol de [email] a [rol]` - Cambiar rol de usuario
• `asignar usuario [email] al equipo [nombre]` - Asignar usuario a equipo
• `dar alta jefe de equipo [nombre] [email] [equipo]` - Crear jefe de equipo completo

**🏢 Gestión de Equipos:**
• `crear equipo [nombre]` - Crear nuevo equipo

**📧 Solicitudes HPS:**
• `envío hps a [email]` o `solicitar hps para [email]` - Solicitar **nueva HPS** (envía formulario)
• `envío traspaso hps a [email]` o `trasladar hps de [email]` - Solicitar **traspaso HPS** (envía formulario)
• `renovar hps de [email]` - Solicitar **renovación HPS** (envía formulario)

**✅ Gestión de HPS:**
• `aprobar hps de [email]` - Aprobar solicitud HPS
• `rechazar hps de [email]` - Rechazar solicitud HPS

¿Qué comando quieres ejecutar? 🤔"""
        elif user_role in ["jefe_seguridad", "jefe_seguridad_suplente"]:
            message = """🔹 **Comandos disponibles (JEFE DE SEGURIDAD):**

**📋 Consultas:**
• `estado hps de [email]` - Consultar estado de HPS
• `todas las hps` - Estadísticas globales
• `listar equipos` - Ver todos los equipos

**👥 Gestión de Usuarios:**
• `modificar rol de [email] a [rol]` - Cambiar rol de usuario

**📧 Solicitudes HPS:**
• `envío hps a [email]` o `solicitar hps para [email]` - Solicitar **nueva HPS** (envía formulario)
• `envío traspaso hps a [email]` o `trasladar hps de [email]` - Solicitar **traspaso HPS** (envía formulario)
• `renovar hps de [email]` - Solicitar **renovación HPS** (envía formulario)

**✅ Gestión de HPS:**
• `aprobar hps de [email]` - Aprobar solicitud HPS
• `rechazar hps de [email]` - Rechazar solicitud HPS

¿Qué comando quieres ejecutar? 🤔"""
        elif user_role in ["team_lead", "team_leader"]:
            message = """🔹 **Comandos disponibles (JEFE DE EQUIPO):**

**📋 Consultas:**
• `estado hps de [email]` - Consultar estado de HPS
• `hps de mi equipo` - Ver HPS de tu equipo
• `listar usuarios` - Ver usuarios de tu equipo
• `listar equipos` - Ver todos los equipos

**👥 Gestión de Usuarios de tu Equipo:**
• `crear usuario [email]` - Crear usuario en tu equipo
• `asignar usuario [email] al equipo [nombre]` - Asignar usuario a tu equipo

**📧 Solicitudes HPS:**
• `envío hps a [email]` o `solicitar hps para [email]` - Solicitar **nueva HPS** (envía formulario, el usuario se asociará a tu equipo)
• `renovar hps de [email]` - Solicitar **renovación HPS** (envía formulario)

**✅ Gestión de HPS de tu Equipo:**
• `aprobar hps de [email]` - Aprobar HPS de tu equipo
• `rechazar hps de [email]` - Rechazar HPS de tu equipo

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
    
    async def _crear_usuario(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Crear nuevo usuario con flujo conversacional"""
        user_role = user_context.get("role", "").lower()
        email = parametros.get("email")
        user_message = parametros.get("user_message", "")
        
        logger.info(f"👤 _crear_usuario llamado: email={email}, user_message={user_message[:50]}")
        
        # Verificar permisos
        if user_role not in ["admin", "team_lead", "team_leader"]:
            return {
                "tipo": "error",
                "mensaje": "❌ No tienes permisos para crear usuarios. Solo administradores y jefes de equipo pueden realizar esta acción."
            }
        
        # IMPORTANTE: Si el email viene del contexto del usuario actual, ignorarlo
        current_user_email = user_context.get("email", "")
        if email == current_user_email:
            logger.warning(f"Email del usuario actual detectado en crear_usuario, ignorando: {email}")
            email = None
        
        # Si no hay email, iniciar flujo conversacional
        if not email or email.strip() == "":
            logger.info(f"📧 No hay email, intentando extraer de user_message o iniciar flujo")
            # Intentar extraer email del mensaje
            email = is_email_only(user_message)
            logger.info(f"🔍 Intentando extraer email de user_message: email={email}")
            if not email:
                # Iniciar flujo conversacional
                user_id = user_context.get("id")
                flow_key = f"{user_id}_flow"
                self.conversation_flows[flow_key] = {
                    "type": "crear_usuario",
                    "started_at": datetime.now().isoformat()
                }
                logger.info(f"🔄 Flujo crear_usuario iniciado para usuario {user_id}, flow_key={flow_key}")
                logger.info(f"📋 Flujos activos: {list(self.conversation_flows.keys())}")
                return {
                    "tipo": "conversacion",
                    "mensaje": "📧 Para crear un usuario, necesito el email.\n\n**Por favor, proporciona el email del nuevo usuario:**\n• Ejemplo: usuario@empresa.com"
                }
        
        # Si tenemos email, crear el usuario
        try:
            result = await self._create_user_in_db_with_email(email, user_context)
            if result.get("success"):
                user = result.get("user")
                temp_password = result.get("temp_password")
                user_was_new = result.get("user_was_new", True)
                
                # Solo enviar email con credenciales si es un usuario nuevo
                if user_was_new and temp_password:
                    email_sent = await self._send_user_credentials_email(email, temp_password, user)
                    
                    if email_sent:
                        return {
                            "tipo": "exito",
                            "mensaje": f"✅ Usuario creado exitosamente: {email}\n\n📧 Se ha enviado un correo electrónico con las credenciales de acceso al usuario.",
                            "data": {"email": email, "user_id": str(user.id), "email_sent": True}
                        }
                    else:
                        return {
                            "tipo": "exito",
                            "mensaje": f"✅ Usuario creado exitosamente: {email}\n\n⚠️ **Nota:** El usuario fue creado pero no se pudo enviar el correo con las credenciales. La contraseña temporal es: {temp_password}\n\n🔑 **IMPORTANTE:** Comparte estas credenciales con el usuario de forma segura.",
                            "data": {"email": email, "user_id": str(user.id), "email_sent": False, "temp_password": temp_password}
                        }
                else:
                    # Usuario existente, solo se actualizó el perfil
                    return {
                        "tipo": "exito",
                        "mensaje": f"✅ Perfil HPS creado/actualizado para el usuario existente: {email}\n\nℹ️ El usuario ya existía en el sistema, se ha creado o actualizado su perfil HPS.",
                        "data": {"email": email, "user_id": str(user.id), "user_was_new": False}
                    }
            else:
                return {
                    "tipo": "error",
                    "mensaje": result.get("message", f"❌ El usuario {email} ya existe en el sistema.")
                }
        except Exception as e:
            logger.error(f"Error creando usuario: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "tipo": "error",
                "mensaje": "❌ Hubo un error creando el usuario. Por favor, intenta de nuevo."
            }
    
    @database_sync_to_async
    def _create_user_in_db_with_email(self, email: str, user_context: Dict[str, Any]):
        """Crear usuario en la base de datos y retornar usuario y contraseña"""
        try:
            # Verificar si el usuario ya existe
            user = None
            user_exists = User.objects.filter(email=email).exists()
            
            # Generar contraseña temporal solo si es usuario nuevo
            temp_password = None
            if not user_exists:
                # Generar contraseña temporal
                import secrets
                import string
                alphabet = string.ascii_letters.replace('O', '').replace('o', '').replace('I', '').replace('l', '') + \
                          string.digits.replace('0', '').replace('1', '')
                temp_password = ''.join(secrets.choice(alphabet) for i in range(12))
                
                # Crear nuevo usuario con contraseña temporal
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=temp_password,
                    first_name=email.split("@")[0].split(".")[0].title(),
                    last_name="",
                    is_active=True
                )
                logger.info(f"Usuario nuevo creado: {email} con contraseña temporal")
            else:
                user = User.objects.get(email=email)
                # Verificar si ya tiene perfil HPS
                if hasattr(user, 'hps_profile'):
                    return {
                        "success": False,
                        "message": f"❌ El usuario {email} ya existe en el sistema y tiene un perfil HPS activo."
                    }
                # Si el usuario existe pero no tiene perfil, continuamos para crear el perfil
                logger.info(f"Usuario {email} existe pero no tiene perfil HPS, creando perfil...")
            
            # Obtener rol por defecto (member)
            member_role, _ = HpsRole.objects.get_or_create(
                name="member",
                defaults={"description": "Miembro del equipo", "permissions": {}}
            )
            
            # Obtener equipo del usuario actual si es team_lead
            team = None
            current_user_id = user_context.get("id")
            if user_context.get("role", "").lower() in ["team_lead", "team_leader"]:
                current_user = User.objects.get(id=current_user_id)
                if hasattr(current_user, 'hps_profile') and current_user.hps_profile.team:
                    team = current_user.hps_profile.team
            
            # Si no hay equipo, usar AICOX
            if not team:
                from hps_core.signals import get_or_create_aicox_team
                team = get_or_create_aicox_team()
            
            # Crear o actualizar perfil HPS (solo si no existe)
            if not hasattr(user, 'hps_profile'):
                # IMPORTANTE: Establecer TODOS los campos necesarios del perfil HPS
                # Si se envía correo con contraseña temporal, marcar como temporal
                profile = HpsUserProfile.objects.create(
                    user=user,
                    role=member_role,
                    team=team,
                    email_verified=False,  # Email no verificado inicialmente
                    is_temp_password=not user_exists,  # True si es usuario nuevo (se envía correo)
                    must_change_password=not user_exists,  # True si es usuario nuevo (debe cambiar contraseña)
                    last_login=None,  # Sin login inicial
                    extra_permissions={}  # Sin permisos extra inicialmente
                )
                logger.info(f"Perfil HPS creado completamente para usuario: {email} - is_temp_password={not user_exists}, must_change_password={not user_exists}")
            else:
                # Si ya tiene perfil, actualizar equipo si es necesario
                if user.hps_profile.team != team:
                    user.hps_profile.team = team
                    user.hps_profile.save()
                    logger.info(f"Equipo actualizado para usuario: {email}")
            
            return {
                "success": True,
                "user": user,
                "temp_password": temp_password,
                "user_was_new": not user_exists
            }
        except Exception as e:
            logger.error(f"Error creando usuario en DB: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    @database_sync_to_async
    def _send_user_credentials_email(self, email: str, temp_password: str, user) -> bool:
        """Enviar email con credenciales de usuario"""
        try:
            from hps_core.email_service import HpsEmailService
            email_service = HpsEmailService()
            
            user_name = f"{user.first_name} {user.last_name}".strip() or email.split("@")[0]
            success = email_service.send_user_credentials_email(
                email=email,
                username=email,
                password=temp_password,
                user_name=user_name
            )
            
            if success:
                logger.info(f"✅ Email con credenciales enviado a {email}")
            else:
                logger.warning(f"⚠️ Email no enviado a {email}")
            
            return success
        except Exception as e:
            logger.error(f"Error enviando email de credenciales: {e}")
            return False
    
    async def _crear_equipo(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Crear nuevo equipo"""
        user_role = user_context.get("role", "").lower()
        team_name = parametros.get("nombre") or parametros.get("name")
        
        # Verificar permisos
        if user_role != "admin":
            return {
                "tipo": "error",
                "mensaje": "❌ Solo los administradores pueden crear equipos."
            }
        
        if not team_name:
            return {
                "tipo": "conversacion",
                "mensaje": "📋 Para crear un equipo, necesito el nombre.\n\n**Por favor, proporciona el nombre:**\n• Ejemplo: 'crear equipo Desarrollo'"
            }
        
        try:
            team = await self._create_team_in_db(team_name)
            if team:
                return {
                    "tipo": "exito",
                    "mensaje": f"✅ Equipo '{team_name}' creado exitosamente.",
                    "data": {"team_id": str(team.id), "name": team.name}
                }
            else:
                return {
                    "tipo": "error",
                    "mensaje": f"❌ El equipo '{team_name}' ya existe."
                }
        except Exception as e:
            logger.error(f"Error creando equipo: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Hubo un error creando el equipo. Por favor, intenta de nuevo."
            }
    
    @database_sync_to_async
    def _create_team_in_db(self, team_name: str):
        """Crear equipo en la base de datos"""
        try:
            if HpsTeam.objects.filter(name=team_name, is_active=True).exists():
                return None
            
            team = HpsTeam.objects.create(
                name=team_name,
                description=f"Equipo {team_name}",
                is_active=True
            )
            return team
        except Exception as e:
            logger.error(f"Error creando equipo en DB: {e}")
            raise
    
    async def _asignar_usuario_equipo(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Asignar usuario a un equipo"""
        user_role = user_context.get("role", "").lower()
        email = parametros.get("email")
        team_name = parametros.get("equipo") or parametros.get("team")
        
        # Verificar permisos
        if user_role not in ["admin", "team_lead", "team_leader"]:
            return {
                "tipo": "error",
                "mensaje": "❌ No tienes permisos para asignar usuarios a equipos."
            }
        
        if not email or not team_name:
            return {
                "tipo": "conversacion",
                "mensaje": "📋 Para asignar un usuario a un equipo, necesito el email y el nombre del equipo.\n\n**Por favor, proporciona:**\n• Ejemplo: 'asignar usuario usuario@empresa.com al equipo Desarrollo'"
            }
        
        try:
            result = await self._assign_user_to_team_in_db(email, team_name, user_context)
            if result.get("success"):
                return {
                    "tipo": "exito",
                    "mensaje": f"✅ Usuario {email} asignado al equipo '{team_name}' exitosamente.",
                    "data": result
                }
            else:
                return {
                    "tipo": "error",
                    "mensaje": result.get("message", "❌ Error asignando usuario al equipo.")
                }
        except Exception as e:
            logger.error(f"Error asignando usuario a equipo: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Hubo un error asignando el usuario al equipo. Por favor, intenta de nuevo."
            }
    
    @database_sync_to_async
    def _assign_user_to_team_in_db(self, email: str, team_name: str, user_context: Dict[str, Any]):
        """Asignar usuario a equipo en la base de datos"""
        try:
            user = User.objects.get(email=email)
            team = HpsTeam.objects.get(name=team_name, is_active=True)
            
            # Verificar permisos: team_lead solo puede asignar a su equipo
            user_role = user_context.get("role", "").lower()
            if user_role in ["team_lead", "team_leader"]:
                current_user_id = user_context.get("id")
                current_user = User.objects.get(id=current_user_id)
                if hasattr(current_user, 'hps_profile') and current_user.hps_profile.team:
                    if current_user.hps_profile.team.id != team.id:
                        return {
                            "success": False,
                            "message": f"❌ Solo puedes asignar usuarios a tu propio equipo."
                        }
            
            # Actualizar perfil HPS
            if hasattr(user, 'hps_profile'):
                user.hps_profile.team = team
                user.hps_profile.save()
            else:
                # Crear perfil si no existe con todos los campos necesarios
                member_role, _ = HpsRole.objects.get_or_create(
                    name="member",
                    defaults={"description": "Miembro del equipo", "permissions": {}}
                )
                HpsUserProfile.objects.create(
                    user=user,
                    role=member_role,
                    team=team,
                    email_verified=False,
                    is_temp_password=False,  # No es nueva creación con temp password
                    must_change_password=False,
                    last_login=None,
                    extra_permissions={}
                )
            
            return {
                "success": True,
                "email": email,
                "team_name": team_name
            }
        except User.DoesNotExist:
            return {
                "success": False,
                "message": f"❌ Usuario {email} no encontrado."
            }
        except HpsTeam.DoesNotExist:
            return {
                "success": False,
                "message": f"❌ Equipo '{team_name}' no encontrado."
            }
        except Exception as e:
            logger.error(f"Error asignando usuario a equipo en DB: {e}")
            raise
    
    async def _modificar_rol(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Modificar rol de un usuario con flujo conversacional"""
        user_role = user_context.get("role", "").lower()
        email = parametros.get("email")
        new_role_name = parametros.get("rol") or parametros.get("role")
        user_message = parametros.get("user_message", "")
        
        # Verificar permisos
        if user_role not in ["admin", "jefe_seguridad"]:
            return {
                "tipo": "error",
                "mensaje": "❌ Solo administradores y jefes de seguridad pueden modificar roles."
            }
        
        # IMPORTANTE: Si el email viene del contexto del usuario actual, ignorarlo
        current_user_email = user_context.get("email", "")
        if email == current_user_email:
            logger.warning(f"Email del usuario actual detectado en modificar_rol, ignorando: {email}")
            email = None
        
        # Si falta información, iniciar o continuar flujo conversacional
        if not email or email.strip() == "":
            # Intentar extraer email del mensaje
            email = is_email_only(user_message)
            if not email:
                # Iniciar flujo conversacional
                user_id = user_context.get("id")
                flow_key = f"{user_id}_flow"
                self.conversation_flows[flow_key] = {
                    "type": "modificar_rol",
                    "started_at": datetime.now().isoformat()
                }
                return {
                    "tipo": "conversacion",
                    "mensaje": "📧 Para modificar el rol de un usuario, necesito el email.\n\n**Por favor, proporciona el email del usuario:**\n• Ejemplo: usuario@empresa.com"
                }
        
        if not new_role_name:
            # Ya tenemos email, pero falta el rol
            user_id = user_context.get("id")
            flow_key = f"{user_id}_flow"
            if flow_key not in self.conversation_flows:
                # Iniciar flujo con el email ya proporcionado
                self.conversation_flows[flow_key] = {
                    "type": "modificar_rol",
                    "email": email,
                    "started_at": datetime.now().isoformat()
                }
            else:
                # Actualizar flujo con el email
                self.conversation_flows[flow_key]["email"] = email
            
            return {
                "tipo": "conversacion",
                "mensaje": f"✅ Email recibido: {email}\n\n📋 Ahora necesito el nuevo rol para este usuario.\n\n**Por favor, proporciona el rol:**\n• Ejemplo: team_lead, member, admin, crypto, jefe_seguridad, etc."
            }
        
        # Si tenemos ambos, modificar el rol
        try:
            result = await self._modify_user_role_in_db(email, new_role_name, user_context)
            if result.get("success"):
                # Limpiar flujo si existe
                user_id = user_context.get("id")
                flow_key = f"{user_id}_flow"
                if flow_key in self.conversation_flows:
                    del self.conversation_flows[flow_key]
                
                return {
                    "tipo": "exito",
                    "mensaje": f"✅ Rol de {email} modificado a '{new_role_name}' exitosamente.",
                    "data": result
                }
            else:
                return {
                    "tipo": "error",
                    "mensaje": result.get("message", "❌ Error modificando el rol.")
                }
        except Exception as e:
            logger.error(f"Error modificando rol: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Hubo un error modificando el rol. Por favor, intenta de nuevo."
            }
    
    @database_sync_to_async
    def _modify_user_role_in_db(self, email: str, new_role_name: str, user_context: Dict[str, Any]):
        """Modificar rol de usuario en la base de datos"""
        try:
            user = User.objects.get(email=email)
            role, _ = HpsRole.objects.get_or_create(
                name=new_role_name.lower(),
                defaults={"description": f"Rol {new_role_name}", "permissions": {}}
            )
            
            if hasattr(user, 'hps_profile'):
                user.hps_profile.role = role
                user.hps_profile.save()
            else:
                # Crear perfil si no existe con todos los campos necesarios
                from hps_core.signals import get_or_create_aicox_team
                team = get_or_create_aicox_team()
                HpsUserProfile.objects.create(
                    user=user,
                    role=role,
                    team=team,
                    email_verified=False,
                    is_temp_password=False,  # No es nueva creación con temp password
                    must_change_password=False,
                    last_login=None,
                    extra_permissions={}
                )
            
            return {
                "success": True,
                "email": email,
                "new_role": new_role_name
            }
        except User.DoesNotExist:
            return {
                "success": False,
                "message": f"❌ Usuario {email} no encontrado."
            }
        except Exception as e:
            logger.error(f"Error modificando rol en DB: {e}")
            raise
    
    async def _aprobar_hps(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Aprobar solicitud HPS"""
        user_role = user_context.get("role", "").lower()
        email = parametros.get("email")
        
        # Verificar permisos
        allowed_roles = ["admin", "jefe_seguridad", "jefe_seguridad_suplente", "crypto", "team_lead", "team_leader"]
        if user_role not in allowed_roles:
            return {
                "tipo": "error",
                "mensaje": "❌ No tienes permisos para aprobar solicitudes HPS."
            }
        
        if not email:
            return {
                "tipo": "conversacion",
                "mensaje": "📋 Para aprobar una solicitud HPS, necesito el email del usuario.\n\n**Por favor, proporciona el email:**\n• Ejemplo: 'aprobar hps de usuario@empresa.com'"
            }
        
        try:
            result = await self._approve_hps_in_db(email, user_context)
            if result.get("success"):
                return {
                    "tipo": "exito",
                    "mensaje": f"✅ Solicitud HPS de {email} aprobada exitosamente.",
                    "data": result
                }
            else:
                return {
                    "tipo": "error",
                    "mensaje": result.get("message", "❌ Error aprobando la solicitud HPS.")
                }
        except Exception as e:
            logger.error(f"Error aprobando HPS: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Hubo un error aprobando la solicitud HPS. Por favor, intenta de nuevo."
            }
    
    @database_sync_to_async
    def _approve_hps_in_db(self, email: str, user_context: Dict[str, Any]):
        """Aprobar HPS en la base de datos"""
        try:
            user = User.objects.get(email=email)
            approver = User.objects.get(id=user_context.get("id"))
            
            # Buscar solicitud HPS pendiente o enviada
            hps_request = HpsRequest.objects.filter(
                user=user,
                status__in=["pending", "submitted"]
            ).order_by('-created_at').first()
            
            if not hps_request:
                return {
                    "success": False,
                    "message": f"❌ No se encontró una solicitud HPS pendiente para {email}."
                }
            
            # Verificar permisos según el rol
            user_role = user_context.get("role", "").lower()
            if user_role in ["team_lead", "team_leader"]:
                # Team leads solo pueden aprobar HPS de su equipo
                if hasattr(approver, 'hps_profile') and approver.hps_profile.team:
                    if not hasattr(user, 'hps_profile') or user.hps_profile.team != approver.hps_profile.team:
                        return {
                            "success": False,
                            "message": f"❌ Solo puedes aprobar HPS de usuarios de tu equipo."
                        }
            
            # Aprobar HPS
            from datetime import date, timedelta
            expires_at = date.today() + timedelta(days=365)  # 1 año de validez
            hps_request.approve(approver, expires_at=expires_at)
            hps_request.save()
            
            return {
                "success": True,
                "email": email,
                "hps_id": str(hps_request.id),
                "expires_at": expires_at.isoformat()
            }
        except User.DoesNotExist:
            return {
                "success": False,
                "message": f"❌ Usuario {email} no encontrado."
            }
        except Exception as e:
            logger.error(f"Error aprobando HPS en DB: {e}")
            raise
    
    async def _rechazar_hps(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Rechazar solicitud HPS"""
        user_role = user_context.get("role", "").lower()
        email = parametros.get("email")
        notes = parametros.get("notas") or parametros.get("notes", "")
        
        # Verificar permisos
        allowed_roles = ["admin", "jefe_seguridad", "jefe_seguridad_suplente", "crypto", "team_lead", "team_leader"]
        if user_role not in allowed_roles:
            return {
                "tipo": "error",
                "mensaje": "❌ No tienes permisos para rechazar solicitudes HPS."
            }
        
        if not email:
            return {
                "tipo": "conversacion",
                "mensaje": "📋 Para rechazar una solicitud HPS, necesito el email del usuario.\n\n**Por favor, proporciona el email:**\n• Ejemplo: 'rechazar hps de usuario@empresa.com'"
            }
        
        try:
            result = await self._reject_hps_in_db(email, notes, user_context)
            if result.get("success"):
                return {
                    "tipo": "exito",
                    "mensaje": f"✅ Solicitud HPS de {email} rechazada exitosamente.",
                    "data": result
                }
            else:
                return {
                    "tipo": "error",
                    "mensaje": result.get("message", "❌ Error rechazando la solicitud HPS.")
                }
        except Exception as e:
            logger.error(f"Error rechazando HPS: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Hubo un error rechazando la solicitud HPS. Por favor, intenta de nuevo."
            }
    
    @database_sync_to_async
    def _reject_hps_in_db(self, email: str, notes: str, user_context: Dict[str, Any]):
        """Rechazar HPS en la base de datos"""
        try:
            user = User.objects.get(email=email)
            approver = User.objects.get(id=user_context.get("id"))
            
            # Buscar solicitud HPS pendiente o enviada
            hps_request = HpsRequest.objects.filter(
                user=user,
                status__in=["pending", "submitted"]
            ).order_by('-created_at').first()
            
            if not hps_request:
                return {
                    "success": False,
                    "message": f"❌ No se encontró una solicitud HPS pendiente para {email}."
                }
            
            # Verificar permisos según el rol
            user_role = user_context.get("role", "").lower()
            if user_role in ["team_lead", "team_leader"]:
                # Team leads solo pueden rechazar HPS de su equipo
                if hasattr(approver, 'hps_profile') and approver.hps_profile.team:
                    if not hasattr(user, 'hps_profile') or user.hps_profile.team != approver.hps_profile.team:
                        return {
                            "success": False,
                            "message": f"❌ Solo puedes rechazar HPS de usuarios de tu equipo."
                        }
            
            # Rechazar HPS
            hps_request.reject(approver, notes=notes)
            hps_request.save()
            
            return {
                "success": True,
                "email": email,
                "hps_id": str(hps_request.id)
            }
        except User.DoesNotExist:
            return {
                "success": False,
                "message": f"❌ Usuario {email} no encontrado."
            }
        except Exception as e:
            logger.error(f"Error rechazando HPS en DB: {e}")
            raise
    
    async def _renovar_hps(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Renovar HPS de un usuario"""
        # Forzar is_renewal a True
        parametros["user_message"] = parametros.get("user_message", "") + " renovacion"
        return await self._solicitar_hps(parametros, user_context, is_transfer=False)
    
    async def _dar_alta_jefe_equipo(self, parametros: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Dar de alta un jefe de equipo completo"""
        user_role = user_context.get("role", "").lower()
        email = parametros.get("email")
        nombre = parametros.get("nombre") or parametros.get("name")
        team_name = parametros.get("equipo") or parametros.get("team")
        
        # Verificar permisos
        if user_role != "admin":
            return {
                "tipo": "error",
                "mensaje": "❌ Solo los administradores pueden dar de alta jefes de equipo."
            }
        
        if not email:
            return {
                "tipo": "conversacion",
                "mensaje": "📋 Para dar de alta un jefe de equipo, necesito el email, nombre y equipo.\n\n**Por favor, proporciona:**\n• Ejemplo: 'dar alta jefe de equipo Juan Pérez juan@empresa.com Desarrollo'"
            }
        
        try:
            result = await self._create_team_lead_in_db(email, nombre, team_name, user_context)
            if result.get("success"):
                return {
                    "tipo": "exito",
                    "mensaje": f"✅ Jefe de equipo creado exitosamente: {nombre} ({email}) en el equipo '{team_name}'.",
                    "data": result
                }
            else:
                return {
                    "tipo": "error",
                    "mensaje": result.get("message", "❌ Error creando el jefe de equipo.")
                }
        except Exception as e:
            logger.error(f"Error dando de alta jefe de equipo: {e}")
            return {
                "tipo": "error",
                "mensaje": "❌ Hubo un error creando el jefe de equipo. Por favor, intenta de nuevo."
            }
    
    @database_sync_to_async
    def _create_team_lead_in_db(self, email: str, nombre: str, team_name: str, user_context: Dict[str, Any]):
        """Crear jefe de equipo en la base de datos"""
        try:
            # Verificar si el usuario ya existe
            user_exists = User.objects.filter(email=email).exists()
            
            # Obtener o crear equipo
            team, team_created = HpsTeam.objects.get_or_create(
                name=team_name,
                defaults={"description": f"Equipo {team_name}", "is_active": True}
            )
            
            # Obtener o crear rol team_lead
            team_lead_role, _ = HpsRole.objects.get_or_create(
                name="team_lead",
                defaults={"description": "Jefe de equipo", "permissions": {}}
            )
            
            # Generar contraseña temporal
            import secrets
            import string
            alphabet = string.ascii_letters.replace('O', '').replace('o', '').replace('I', '').replace('l', '') + \
                      string.digits.replace('0', '').replace('1', '')
            temp_password = ''.join(secrets.choice(alphabet) for i in range(12))
            
            # Crear o actualizar usuario
            if user_exists:
                user = User.objects.get(email=email)
                user.set_password(temp_password)
                if nombre:
                    name_parts = nombre.split(" ", 1)
                    user.first_name = name_parts[0]
                    user.last_name = name_parts[1] if len(name_parts) > 1 else ""
                user.is_active = True
                user.save()
            else:
                name_parts = nombre.split(" ", 1) if nombre else [email.split("@")[0]]
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=temp_password,
                    first_name=name_parts[0],
                    last_name=name_parts[1] if len(name_parts) > 1 else "",
                    is_active=True
                )
            
            # Crear o actualizar perfil HPS
            profile, profile_created = HpsUserProfile.objects.get_or_create(
                user=user,
                defaults={
                    "role": team_lead_role,
                    "team": team,
                    "email_verified": False,
                    "is_temp_password": True,
                    "must_change_password": True
                }
            )
            
            if not profile_created:
                profile.role = team_lead_role
                profile.team = team
                profile.is_temp_password = True
                profile.must_change_password = True
                profile.save()
            
            # Asignar como team_lead del equipo
            team.team_lead = user
            team.save()
            
            logger.info(f"Jefe de equipo creado: {email} con contraseña temporal: {temp_password}")
            
            return {
                "success": True,
                "email": email,
                "team_name": team_name,
                "user_created": not user_exists
            }
        except Exception as e:
            logger.error(f"Error creando jefe de equipo en DB: {e}")
            raise
    
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

