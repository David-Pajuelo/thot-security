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
            
            # Construir contexto del usuario
            self.user_context = {
                'id': str(self.user.id),
                'email': self.user.email,
                'first_name': self.user.first_name or '',
                'last_name': self.user.last_name or '',
                'role': user_data.get('role', 'member'),
                'team_id': user_data.get('team_id'),
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
            message = data.get('message', '').strip()
            
            if not message:
                return
            
            logger.info(f"📨 Mensaje recibido de {self.user.email}: {message[:100]}")
            
            # Inicializar start_time para calcular tiempo de respuesta
            start_time = datetime.now()
            
            # PRIMERO: Verificar si hay un flujo activo (esto tiene prioridad sobre OpenAI)
            user_id = self.user_context.get("id")
            flow_key = f"{user_id}_flow"
            has_active_flow = flow_key in self.command_processor.conversation_flows
            
            logger.info(f"🔍 Verificando flujo activo para usuario {user_id}: {has_active_flow}")
            if has_active_flow:
                flow_info = self.command_processor.conversation_flows.get(flow_key, {})
                logger.info(f"🔄 Flujo activo detectado: tipo={flow_info.get('type')}, email={flow_info.get('email', 'N/A')}")
            
            if has_active_flow:
                # Si hay flujo activo, procesar directamente sin OpenAI
                logger.info(f"🔄 Flujo activo detectado para usuario {user_id}, procesando directamente")
                # Crear una respuesta simulada para que execute_command la procese
                ai_response = {
                    "tipo": "comando",
                    "accion": "continuar_flujo",  # Acción especial para flujos
                    "parametros": {},
                    "user_message": message,
                    "requiere_api": True
                }
            else:
                # Guardar mensaje del usuario
                if self.conversation_id:
                    await self.chat_service.log_user_message(
                        self.conversation_id,
                        message
                    )
                
                # Procesar mensaje con OpenAI
                logger.info(f"🤖 Enviando mensaje a OpenAI para procesamiento")
                ai_response = await self.openai_service.process_message(
                    message,
                    self.user_context
                )
                logger.info(f"🤖 Respuesta de OpenAI: tipo={ai_response.get('tipo')}, accion={ai_response.get('accion')}")
            
            # Agregar user_message al contexto para el command processor
            ai_response['user_message'] = message
            
            # Si es un comando, ejecutarlo
            if ai_response.get('tipo') == 'comando':
                accion = ai_response.get('accion', '')
                # CRÍTICO: Algunos comandos siempre deben ejecutarse para iniciar flujos conversacionales
                # incluso si requiere_api es false (como crear_usuario o modificar_rol sin parámetros)
                comandos_que_siempre_ejecutar = ['crear_usuario', 'modificar_rol']
                
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
            
            # Extraer datos del usuario
            user_data = {
                'user_id': access_token['user_id'],
                'email': access_token.get('email', ''),
                'first_name': access_token.get('first_name', ''),
                'last_name': access_token.get('last_name', ''),
                'role': access_token.get('role', 'member'),
                'team_id': access_token.get('team_id'),
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
                    # Enviar conversation_id
                    await self.send(text_data=json.dumps({
                        'type': 'conversation_id',
                        'conversation_id': conversation_id,
                        'timestamp': datetime.now().isoformat()
                    }))
                    logger.info(f"✅ conversation_id enviado: {conversation_id}")
                    
                    # Enviar mensaje de bienvenida
                    await self._send_welcome_message()
                else:
                    logger.warning("⚠️ No se pudo crear conversación, continuando sin ella")
                    await self._send_welcome_message()
            else:
                logger.info(f"✅ Reutilizando conversación activa: {conversation_id}")
                # Cargar historial
                self.conversation_id = conversation_id
                await self.send(text_data=json.dumps({
                    'type': 'conversation_id',
                    'conversation_id': conversation_id,
                    'timestamp': datetime.now().isoformat()
                }))
                logger.info(f"✅ conversation_id enviado: {conversation_id}")
                
                # Cargar historial de mensajes
                await self._load_conversation_history()
            
            if conversation_id:
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
        """Enviar mensaje de bienvenida"""
        try:
            user_role = self.user_context.get('role', 'member')
            user_name = self.user_context.get('first_name', 'Usuario') or 'Usuario'
            
            welcome_text = RoleConfig.get_welcome_message(user_role, user_name)
            suggestions = RoleConfig.get_suggestions_by_role(user_role)
            
            await self.send(text_data=json.dumps({
                'type': 'assistant',
                'message': f"{welcome_text}\n\n**¿En qué puedo ayudarte hoy?** 😊",
                'timestamp': datetime.now().isoformat(),
                'suggestions': suggestions
            }))
            
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje de bienvenida: {e}")
    
    async def _load_conversation_history(self):
        """Cargar historial de conversación"""
        try:
            if not self.conversation_id:
                # Si no hay conversation_id, enviar bienvenida
                await self._send_welcome_message()
                return
            
            messages = await self.chat_service.get_conversation_messages(
                self.conversation_id,
                limit=50
            )
            
            if messages and len(messages) > 0:
                logger.info(f"📜 Cargando {len(messages)} mensajes del historial")
                for msg in messages:
                    await self.send(text_data=json.dumps({
                        'type': msg.get('type', 'assistant'),
                        'message': msg.get('message', ''),
                        'timestamp': msg.get('timestamp', datetime.now().isoformat()),
                        'conversation_id': self.conversation_id
                    }))
                # Después de cargar historial, verificar si el último mensaje es reciente
                # Si el último mensaje es muy antiguo (más de 5 minutos), enviar bienvenida
                if messages:
                    last_message = messages[-1]
                    last_timestamp = last_message.get('timestamp')
                    if last_timestamp:
                        try:
                            from datetime import datetime, timezone
                            last_msg_time = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
                            time_diff = (datetime.now(timezone.utc) - last_msg_time.replace(tzinfo=timezone.utc)).total_seconds()
                            # Si el último mensaje es de hace más de 5 minutos, enviar bienvenida
                            if time_diff > 300:  # 5 minutos
                                logger.info(f"📜 Último mensaje es antiguo ({int(time_diff)}s), enviando bienvenida")
                                await self._send_welcome_message()
                        except Exception as time_error:
                            logger.warning(f"⚠️ Error calculando tiempo del último mensaje: {time_error}")
                            # Si hay error, enviar bienvenida por seguridad
                            await self._send_welcome_message()
            else:
                # Si no hay historial, enviar bienvenida
                logger.info("📜 No hay mensajes en el historial, enviando bienvenida")
                await self._send_welcome_message()
                
        except Exception as e:
            logger.error(f"❌ Error cargando historial: {e}")
            # Enviar bienvenida si hay error
            await self._send_welcome_message()
