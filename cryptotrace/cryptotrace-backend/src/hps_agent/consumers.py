"""
WebSocket Consumer para el Agente IA (Django Channels)
"""
import json
import logging
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from django.conf import settings

from .services.openai_service import OpenAIService
from .services.command_processor import CommandProcessor
from .services.chat_service import ChatService
from .services.role_config import RoleConfig

logger = logging.getLogger(__name__)
User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket para el chat del agente IA.
    Maneja conexiones, mensajes y respuestas del agente.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.user_context = {}
        self.conversation_id = None
        self.openai_service = None
        self.command_processor = None
        self.chat_service = ChatService()
    
    async def connect(self):
        """Manejar conexión WebSocket"""
        logger.info(f"🔌 Intento de conexión WebSocket recibido")
        logger.info(f"📋 Scope path: {self.scope.get('path')}")
        logger.info(f"📋 Scope query_string: {self.scope.get('query_string')}")
        
        # Obtener token de query params o headers
        token = None
        
        # Intentar obtener de query params
        query_string = self.scope.get('query_string', b'').decode()
        logger.info(f"📋 Query string decodificado: {query_string}")
        if 'token=' in query_string:
            token = query_string.split('token=')[1].split('&')[0]
            logger.info(f"✅ Token encontrado en query params")
        
        # Si no está en query, intentar de headers
        if not token:
            headers = dict(self.scope.get('headers', []))
            logger.info(f"📋 Headers disponibles: {list(headers.keys())}")
            auth_header = headers.get(b'authorization', b'').decode()
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                logger.info(f"✅ Token encontrado en headers")
        
        if not token:
            logger.warning("❌ Token no proporcionado")
            await self.close(code=4001)
            return
        
        # Validar token JWT
        try:
            user_data = await self._validate_token(token)
            if not user_data:
                logger.warning("❌ Token inválido")
                await self.close(code=4003)
                return
            
            # Obtener usuario
            self.user = await ChatService.get_user_by_id(user_data['user_id'])
            if not self.user:
                logger.warning(f"❌ Usuario no encontrado: {user_data['user_id']}")
                await self.close(code=4003)
                return
            
            # Construir contexto del usuario (team_ids para N:N)
            team_ids = user_data.get('team_ids')
            if team_ids is None and user_data.get('team_id') is not None:
                team_ids = [user_data.get('team_id')]
            if not team_ids:
                team_ids = []
            self.user_context = {
                'id': str(self.user.id),
                'email': self.user.email,
                'first_name': self.user.first_name or '',
                'last_name': self.user.last_name or '',
                'role': user_data.get('role', 'member'),
                'team_id': user_data.get('team_id') or (team_ids[0] if team_ids else None),
                'team_ids': team_ids,
                'auth_token': token
            }
            
            # Inicializar servicios
            self.openai_service = OpenAIService()
            self.command_processor = CommandProcessor()
            
            # Aceptar conexión PRIMERO
            await self.accept()
            logger.info(f"✅ WebSocket aceptado para usuario {self.user.email}")
            
            # Pequeño delay para asegurar que el cliente esté listo para recibir mensajes
            import asyncio
            await asyncio.sleep(0.2)  # 200ms de delay
            
            # Buscar o crear conversación (no bloquear si falla)
            try:
                await self._initialize_conversation()
            except Exception as conv_error:
                logger.error(f"❌ Error inicializando conversación: {conv_error}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Continuar de todas formas - la conexión está establecida
                # Enviar mensaje de bienvenida de emergencia
                try:
                    await self._send_welcome_message()
                except Exception as welcome_error:
                    logger.error(f"❌ Error enviando mensaje de bienvenida de emergencia: {welcome_error}")
            
        except Exception as e:
            logger.error(f"❌ Error en connect: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            try:
                await self.close(code=4000)
            except:
                pass
    
    async def disconnect(self, close_code):
        """Manejar desconexión WebSocket"""
        logger.info(f"WebSocket desconectado: {close_code}")
    
    async def receive(self, text_data):
        """Manejar mensajes recibidos del cliente"""
        try:
            data = json.loads(text_data)
            
            # Manejar mensajes de ping (keepalive)
            if data.get('type') == 'ping':
                # Responder con pong para mantener la conexión viva
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
                return
            
            message = data.get('message', '').strip()
            
            if not message:
                return
            
            logger.info(f"📨 Mensaje recibido de {self.user.email}: {message[:100]}")
            
            # Inicializar start_time para calcular tiempo de respuesta
            start_time = datetime.now()
            
            # Guardar mensaje del usuario SIEMPRE (antes de procesar)
            if self.conversation_id:
                await self.chat_service.log_user_message(
                    self.conversation_id,
                    message
                )
                logger.info(f"✅ Mensaje del usuario guardado en conversación {self.conversation_id}")
            else:
                logger.warning("⚠️ No hay conversation_id, mensaje del usuario no guardado")
            
            # PRIMERO: Verificar si hay un flujo activo
            user_id = self.user_context.get("id")
            flow_key = f"{user_id}_flow"
            has_active_flow = flow_key in self.command_processor.conversation_flows
            
            logger.info(f"🔍 Verificando flujo activo para usuario {user_id}: {has_active_flow}")
            if has_active_flow:
                flow_info = self.command_processor.conversation_flows.get(flow_key, {})
                logger.info(f"🔄 Flujo activo detectado: tipo={flow_info.get('type')}, email={flow_info.get('email', 'N/A')}")
            
            # Si hay un flujo activo de solicitar_hps y el mensaje parece ser un email, forzar continuación del flujo
            flow_type = self.command_processor.conversation_flows.get(flow_key, {}).get('type', '') if has_active_flow else ''
            if has_active_flow and flow_type == "solicitar_hps":
                # Verificar si el mensaje parece ser un email (aunque no sea válido)
                import re
                email_like_pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+'
                if re.search(email_like_pattern, message):
                    logger.info(f"🔄 Flujo solicitar_hps activo y mensaje parece email, forzando continuación del flujo")
                    ai_response = {
                        "tipo": "comando",
                        "accion": "continuar_flujo",
                        "parametros": {},
                        "user_message": message,
                        "requiere_api": True
                    }
                else:
                    # No parece email, procesar con OpenAI para ver si es un comando
                    logger.info(f"🤖 Enviando mensaje a OpenAI para procesamiento")
                    ai_response = await self.openai_service.process_message(
                        message,
                        self.user_context
                    )
                    logger.info(f"🤖 Respuesta de OpenAI: tipo={ai_response.get('tipo')}, accion={ai_response.get('accion')}")
            else:
                # SIEMPRE procesar con OpenAI primero para detectar si es un nuevo comando
                # Esto permite que el usuario pueda cancelar un flujo escribiendo un nuevo comando
                logger.info(f"🤖 Enviando mensaje a OpenAI para procesamiento")
                ai_response = await self.openai_service.process_message(
                    message,
                    self.user_context
                )
                logger.info(f"🤖 Respuesta de OpenAI: tipo={ai_response.get('tipo')}, accion={ai_response.get('accion')}")
            
            # Comandos que inician flujos conversacionales (deben cancelar cualquier flujo anterior)
            comandos_que_inician_flujo = ['crear_usuario', 'modificar_rol']
            new_action = ai_response.get('accion', '')
            
            # Si el usuario intenta iniciar un nuevo flujo, cancelar el flujo anterior
            if new_action in comandos_que_inician_flujo and has_active_flow:
                logger.info(f"🔄 Comando que inicia flujo detectado ({new_action}), cancelando flujo anterior")
                if flow_key in self.command_processor.conversation_flows:
                    del self.command_processor.conversation_flows[flow_key]
                    logger.info(f"✅ Flujo anterior cancelado: {flow_key}")
            
            # Si hay un flujo activo PERO el usuario escribió un comando válido diferente, cancelar el flujo
            if has_active_flow and ai_response.get('tipo') == 'comando' and flow_type != "solicitar_hps":
                flow_type = self.command_processor.conversation_flows.get(flow_key, {}).get('type', '')
                
                # Lista de comandos que NO son parte de ningún flujo conversacional
                comandos_que_cancelan_flujo = [
                    'consultar_todas_hps', 'consultar_estado_hps', 'consultar_hps_equipo',
                    'listar_usuarios', 'listar_equipos', 'comandos_disponibles',
                    'solicitar_hps', 'trasladar_hps', 'renovar_hps',
                    'crear_equipo', 'asignar_usuario_equipo', 'dar_alta_jefe_equipo'
                ]
                
                # Si el nuevo comando es diferente del flujo activo, cancelar el flujo
                if new_action in comandos_que_cancelan_flujo or (new_action != 'continuar_flujo' and new_action != flow_type and new_action not in comandos_que_inician_flujo):
                    logger.info(f"🔄 Nuevo comando detectado ({new_action}) mientras hay flujo activo ({flow_type}), cancelando flujo")
                    if flow_key in self.command_processor.conversation_flows:
                        del self.command_processor.conversation_flows[flow_key]
                        logger.info(f"✅ Flujo cancelado: {flow_key}")
                elif new_action == flow_type or new_action == 'continuar_flujo':
                    # Es el mismo comando o continuación del flujo, procesar como flujo
                    logger.info(f"🔄 Continuando con flujo activo: {flow_type}")
                    ai_response = {
                        "tipo": "comando",
                        "accion": "continuar_flujo",
                        "parametros": {},
                        "user_message": message,
                        "requiere_api": True
                    }
            elif has_active_flow and flow_type != "solicitar_hps":
                # Hay flujo activo pero no es un comando, continuar con el flujo
                logger.info(f"🔄 Flujo activo detectado, procesando como continuación del flujo")
                ai_response = {
                    "tipo": "comando",
                    "accion": "continuar_flujo",
                    "parametros": {},
                    "user_message": message,
                    "requiere_api": True
                }
            
            # Agregar user_message al contexto para el command processor
            ai_response['user_message'] = message
            
            # Manejar caso especial: OpenAI puede devolver tipo="comandos_disponibles" directamente
            if ai_response.get('tipo') == 'comandos_disponibles' and not ai_response.get('accion'):
                ai_response['tipo'] = 'comando'
                ai_response['accion'] = 'comandos_disponibles'
                logger.info(f"🔄 Corrigiendo respuesta OpenAI: tipo=comandos_disponibles -> tipo=comando, accion=comandos_disponibles")
            
            # Si es un comando, ejecutarlo
            if ai_response.get('tipo') == 'comando':
                accion = ai_response.get('accion', '')
                # CRÍTICO: Algunos comandos siempre deben ejecutarse para iniciar flujos conversacionales
                # incluso si requiere_api es false (como crear_usuario o modificar_rol sin parámetros)
                # También comandos que muestran información (como comandos_disponibles)
                # Y comandos de solicitud HPS que necesitan iniciar flujos conversacionales
                comandos_que_siempre_ejecutar = ['crear_usuario', 'modificar_rol', 'comandos_disponibles', 'ayuda_hps', 'solicitar_hps', 'trasladar_hps', 'renovar_hps', 'consultar_hps_por_estado', 'consultar_todas_hps', 'consultar_estado_hps', 'consultar_hps_equipo', 'listar_usuarios', 'listar_equipos']
                
                if ai_response.get('requiere_api', False) or accion in comandos_que_siempre_ejecutar:
                    logger.info(f"🔧 Ejecutando comando: {accion} (requiere_api={ai_response.get('requiere_api', False)})")
                    final_response = await self.command_processor.execute_command(
                        ai_response,
                        self.user_context
                    )
                else:
                    # Si no requiere API pero es un comando, puede ser que falte información
                    # En este caso, usar la respuesta del AI directamente
                    final_response = ai_response
            else:
                final_response = ai_response
            
            # Calcular tiempo de respuesta
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Extraer mensaje final
            response_message = final_response.get('mensaje', 'Lo siento, no pude procesar tu solicitud.')
            
            # Generar sugerencias
            user_role = self.user_context.get('role', 'member')
            suggestions = RoleConfig.get_suggestions_by_role(user_role)
            
            # Enviar respuesta
            await self.send(text_data=json.dumps({
                'type': 'assistant',
                'message': response_message,
                'timestamp': datetime.now().isoformat(),
                'suggestions': suggestions,
                'data': final_response.get('data', {})
            }))
            
            # Guardar mensaje del asistente
            if self.conversation_id:
                await self.chat_service.log_assistant_message(
                    self.conversation_id,
                    response_message,
                    tokens_used=0,  # TODO: Extraer de respuesta OpenAI
                    response_time_ms=response_time,
                    metadata=final_response.get('data', {})
                )
            
        except json.JSONDecodeError:
            logger.error("❌ Error parseando JSON")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Error procesando el mensaje. Por favor, intenta de nuevo.'
            }))
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Hubo un error procesando tu solicitud. Por favor, intenta de nuevo.'
            }))
    
    async def _validate_token(self, token: str):
        """Validar token JWT y extraer datos del usuario"""
        try:
            # Validar token
            UntypedToken(token)
            
            # Decodificar token
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = AccessToken(token)
            
            # Extraer datos del usuario (team_ids para múltiples equipos)
            team_ids = access_token.get('team_ids')
            if team_ids is None and access_token.get('team_id') is not None:
                team_ids = [access_token.get('team_id')]
            if not team_ids:
                team_ids = []
            user_data = {
                'user_id': access_token['user_id'],
                'email': access_token.get('email', ''),
                'first_name': access_token.get('first_name', ''),
                'last_name': access_token.get('last_name', ''),
                'role': access_token.get('role', 'member'),
                'team_id': access_token.get('team_id') or (team_ids[0] if team_ids else None),
                'team_ids': team_ids,
            }
            
            return user_data
            
        except (InvalidToken, TokenError) as e:
            logger.error(f"❌ Error validando token: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado validando token: {e}")
            return None
    
    async def _initialize_conversation(self):
        """Inicializar o recuperar conversación"""
        try:
            user_id = str(self.user.id)
            session_id = f"ws_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"🔍 Buscando conversación activa para usuario {user_id}")
            
            # Buscar conversación activa
            conversation_id = await self.chat_service.find_active_conversation(user_id)
            logger.info(f"🔍 Resultado búsqueda conversación: {conversation_id}")
            
            if not conversation_id:
                logger.info(f"📝 Creando nueva conversación para usuario {user_id}")
                # Crear nueva conversación
                conversation_id = await self.chat_service.create_conversation(
                    user_id,
                    session_id,
                    "Nueva conversación iniciada"
                )
                logger.info(f"✅ Nueva conversación creada: {conversation_id}")
                
                if conversation_id:
                    # Establecer conversation_id ANTES de enviar mensaje de bienvenida
                    self.conversation_id = conversation_id
                    
                    # Enviar conversation_id
                    await self.send(text_data=json.dumps({
                        'type': 'conversation_id',
                        'conversation_id': conversation_id,
                        'timestamp': datetime.now().isoformat()
                    }))
                    logger.info(f"✅ conversation_id enviado: {conversation_id}")
                    
                    # Enviar mensaje de bienvenida (ahora conversation_id está establecido)
                    await self._send_welcome_message()
                else:
                    logger.warning("⚠️ No se pudo crear conversación, continuando sin ella")
                    await self._send_welcome_message()
            else:
                logger.info(f"✅ Reutilizando conversación activa: {conversation_id}")
                # Establecer conversation_id antes de cargar historial
                self.conversation_id = conversation_id
                
                # Enviar conversation_id
                await self.send(text_data=json.dumps({
                    'type': 'conversation_id',
                    'conversation_id': conversation_id,
                    'timestamp': datetime.now().isoformat()
                }))
                logger.info(f"✅ conversation_id enviado: {conversation_id}")
                
                # Cargar historial de mensajes (si no hay mensajes, enviará bienvenida)
                await self._load_conversation_history()
            
            if conversation_id and not self.conversation_id:
                # Fallback: asegurar que conversation_id esté establecido
                self.conversation_id = conversation_id
                logger.info(f"✅ Conversación inicializada: {conversation_id}")
            else:
                logger.warning("⚠️ Continuando sin conversation_id")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando conversación: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Continuar sin conversación si hay error - enviar bienvenida de todas formas
            try:
                await self._send_welcome_message()
            except Exception as welcome_error:
                logger.error(f"❌ Error enviando mensaje de bienvenida de emergencia: {welcome_error}")
    
    async def _send_welcome_message(self):
        """Enviar mensaje de bienvenida - SIEMPRE se envía al frontend, incluso si falla al guardar"""
        try:
            user_role = self.user_context.get('role', 'member')
            user_name = self.user_context.get('first_name', 'Usuario') or 'Usuario'
            
            welcome_text = RoleConfig.get_welcome_message(user_role, user_name)
            suggestions = RoleConfig.get_suggestions_by_role(user_role)
            
            welcome_message = f"{welcome_text}\n\n**¿En qué puedo ayudarte hoy?** 😊"
            
            # CRÍTICO: Enviar mensaje al frontend PRIMERO (siempre debe llegar al usuario)
            await self.send(text_data=json.dumps({
                'type': 'assistant',
                'message': welcome_message,
                'timestamp': datetime.now().isoformat(),
                'suggestions': suggestions,
                'conversation_id': self.conversation_id
            }))
            logger.info(f"✅ Mensaje de bienvenida enviado al frontend (conversation_id: {self.conversation_id})")
            
            # Intentar guardar mensaje de bienvenida en la base de datos (no crítico si falla)
            if self.conversation_id:
                try:
                    await self.chat_service.log_assistant_message(
                        self.conversation_id,
                        welcome_message,
                        tokens_used=0,
                        response_time_ms=0,
                        metadata={'type': 'welcome', 'suggestions': suggestions}
                    )
                    logger.info(f"✅ Mensaje de bienvenida guardado en conversación {self.conversation_id}")
                except Exception as save_error:
                    # No crítico: el mensaje ya se envió al frontend
                    logger.warning(f"⚠️ No se pudo guardar mensaje de bienvenida en BD: {save_error}")
            else:
                logger.warning("⚠️ No hay conversation_id, mensaje de bienvenida no guardado (pero enviado al frontend)")
            
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje de bienvenida: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Intentar enviar un mensaje de bienvenida básico como fallback
            try:
                await self.send(text_data=json.dumps({
                    'type': 'assistant',
                    'message': '¡Hola! 👋 Soy tu asistente de HPS. ¿En qué puedo ayudarte hoy?',
                    'timestamp': datetime.now().isoformat(),
                    'suggestions': [],
                    'conversation_id': self.conversation_id
                }))
                logger.info("✅ Mensaje de bienvenida de emergencia enviado")
            except Exception as fallback_error:
                logger.error(f"❌ Error crítico: no se pudo enviar mensaje de bienvenida de emergencia: {fallback_error}")
    
    async def _load_conversation_history(self):
        """Cargar historial de conversación"""
        try:
            if not self.conversation_id:
                # Si no hay conversation_id, enviar bienvenida (primera vez)
                await self._send_welcome_message()
                return
            
            messages = await self.chat_service.get_conversation_messages(
                self.conversation_id,
                limit=50
            )
            
            if messages and len(messages) > 0:
                logger.info(f"📜 Cargando {len(messages)} mensajes del historial")
                last_message_has_suggestions = False
                
                for msg in messages:
                    # Incluir sugerencias si existen en el mensaje
                    suggestions = msg.get('suggestions', [])
                    if suggestions and len(suggestions) > 0:
                        last_message_has_suggestions = True
                    
                    await self.send(text_data=json.dumps({
                        'type': msg.get('type', 'assistant'),
                        'message': msg.get('message', ''),
                        'timestamp': msg.get('timestamp', datetime.now().isoformat()),
                        'conversation_id': self.conversation_id,
                        'suggestions': suggestions if suggestions else []
                    }))
                
                # Si el último mensaje no tiene sugerencias, enviar un mensaje con sugerencias actuales
                if not last_message_has_suggestions:
                    user_role = self.user_context.get('role', 'member')
                    suggestions = RoleConfig.get_suggestions_by_role(user_role)
                    if suggestions and len(suggestions) > 0:
                        logger.info(f"📋 Último mensaje sin sugerencias, enviando sugerencias actuales para rol {user_role}")
                        await self.send(text_data=json.dumps({
                            'type': 'system',
                            'message': '',
                            'timestamp': datetime.now().isoformat(),
                            'conversation_id': self.conversation_id,
                            'suggestions': suggestions
                        }))
                # No enviar bienvenida si hay historial - solo se muestra en primera vez o después de reset
            else:
                # Si no hay historial, enviar bienvenida (primera vez o después de reset)
                logger.info("📜 No hay mensajes en el historial, enviando bienvenida")
                await self._send_welcome_message()
                
        except Exception as e:
            logger.error(f"❌ Error cargando historial: {e}")
            # Enviar bienvenida si hay error (por seguridad)
            await self._send_welcome_message()
