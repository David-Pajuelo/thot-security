"""
Router WebSocket para el Agente IA del Sistema HPS
"""
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Optional
import os
from datetime import datetime
import httpx

from .manager import manager
from ..auth import AuthManager
from ..chat_integration import chat_integration
from ..agent.role_config import RoleConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

def get_default_suggestions_by_role(user_role: str) -> list:
    """
    Generar sugerencias por defecto según el rol del usuario.
    Usa la configuración centralizada para facilitar mantenimiento.
    """
    return RoleConfig.get_suggestions_by_role(user_role)

async def send_welcome_message(websocket: WebSocket, user: dict):
    """Enviar mensaje de bienvenida con sugerencias según el rol del usuario"""
    try:
        user_role = (user.get("role") or "member").lower()
        user_name = user.get("first_name", "Usuario")
        
        # Generar sugerencias y mensaje usando la configuración centralizada
        suggestions = get_default_suggestions_by_role(user_role)
        welcome_text = RoleConfig.get_welcome_message(user_role, user_name)
        
        welcome_message = {
            "type": "assistant",
            "message": f"{welcome_text}\n\n**¿En qué puedo ayudarte hoy?** 😊",
            "timestamp": datetime.now().isoformat(),
            "suggestions": suggestions
        }
        
        await websocket.send_text(json.dumps(welcome_message))
        logger.info(f"✅ Mensaje de bienvenida enviado a {user_name} (rol: {user_role})")
        
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje de bienvenida: {e}")

async def send_welcome_message_with_test(websocket: WebSocket, user: dict):
    """Enviar mensaje de bienvenida con 'test' para identificar error de carga"""
    try:
        user_role = (user.get("role") or "member").lower()
        user_name = user.get("first_name", "Usuario")
        
        # Generar sugerencias y mensaje usando la configuración centralizada
        suggestions = get_default_suggestions_by_role(user_role)
        welcome_text = RoleConfig.get_welcome_message(user_role, user_name)
        
        welcome_message = {
            "type": "assistant",
            "message": f"TEST - {welcome_text}\n\n**¿En qué puedo ayudarte hoy?** 😊",
            "timestamp": datetime.now().isoformat(),
            "suggestions": suggestions
        }
        
        await websocket.send_text(json.dumps(welcome_message))
        logger.info(f"✅ Mensaje de bienvenida TEST enviado a {user_name} (rol: {user_role})")
        
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje de bienvenida TEST: {e}")

async def send_conversation_history(websocket: WebSocket, conversation_id: str, user: dict, token: str):
    """Cargar y enviar historial de conversación existente"""
    try:
        # Obtener historial de mensajes de la conversación
        messages = await get_conversation_messages(conversation_id, token)
        
        # Enviar conversation_id al frontend siempre
        await websocket.send_text(json.dumps({
            "type": "conversation_id",
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        if messages and len(messages) > 0:
            logger.info(f"📜 Cargando {len(messages)} mensajes del historial")
            
            # Enviar cada mensaje del historial
            for message in messages:
                await websocket.send_text(json.dumps({
                    "type": message.get("message_type", "assistant"),
                    "message": message.get("content", ""),
                    "timestamp": message.get("created_at", datetime.now().isoformat()),
                    "suggestions": message.get("suggestions", []),
                    "conversation_id": conversation_id
                }))
            
            logger.info(f"✅ Historial cargado exitosamente")
        else:
            # Si no hay historial, enviar mensaje de bienvenida
            logger.info("📜 No hay historial disponible, enviando mensaje de bienvenida")
            await send_welcome_message(websocket, user)
            
    except Exception as e:
        logger.error(f"❌ Error cargando historial: {e}")
        # En caso de error, verificar si hay mensajes de otra forma
        # Si no se puede cargar el historial, asumir que no hay historial y enviar bienvenida
        logger.info("📜 Error cargando historial, enviando mensaje de bienvenida por seguridad")
        await send_welcome_message_with_test(websocket, user)

async def get_conversation_messages(conversation_id: str, token: str) -> list:
    """Obtener mensajes de una conversación desde el backend"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        # Backend ahora es Django (cryptotrace-backend en puerto 8080)
        backend_url = os.getenv("BACKEND_URL", "http://cryptotrace-backend:8080")
        url = f"{backend_url}/api/hps/chat/conversations/{conversation_id}/messages/"
        
        logger.info(f"🔍 Obteniendo mensajes de conversación: {conversation_id}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                logger.info(f"✅ Obtenidos {len(messages)} mensajes del historial")
                return messages
            else:
                logger.warning(f"⚠️ Error obteniendo mensajes: {response.status_code}")
                return []
                
    except Exception as e:
        logger.error(f"❌ Error obteniendo mensajes: {e}")
        return []

@router.websocket("/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None
):
    """
    Endpoint WebSocket para chat directo con el Agente IA
    """
    # Obtener token del query parameter
    if not token:
        # Intentar obtener token de los headers
        auth_header = websocket.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        
        if not token:
            await websocket.close(code=4001, reason="Token requerido")
            return
    
    try:
        # Validar token JWT
        user = await validate_websocket_token(token)
        if not user:
            await websocket.close(code=4003, reason="Token inválido")
            return
        
        user_id = str(user.get("id"))
        logger.info(f"Usuario {user_id} conectando al Agente IA")
        logger.info(f"User object: {user}")
        
        # Establecer conexión WebSocket
        await websocket.accept()
        logger.info(f"✅ WebSocket aceptado para usuario {user_id}")
        logger.info(f"🔍 Estado del WebSocket después de accept: {websocket.client_state.name if hasattr(websocket, 'client_state') else 'unknown'}")
        
        # Buscar conversación activa existente o crear una nueva
        session_id = f"ws_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        conversation_id = None
        
        try:
            # Primero intentar encontrar una conversación activa del usuario
            logger.info(f"🔍 Buscando conversación activa para usuario {user_id}...")
            conversation_id = await chat_integration.find_active_conversation(
                user_id=user_id,
                auth_token=token
            )
            logger.info(f"🔍 Resultado de búsqueda de conversación: {conversation_id}")
            
            # Si no hay conversación activa, crear una nueva
            if not conversation_id:
                logger.info(f"📝 Creando nueva conversación para usuario {user_id}...")
                conversation_id = await chat_integration.start_conversation(
                    user_id=user_id,  # user_id ya es el UUID del usuario
                    session_id=session_id,
                    title="Nueva conversación iniciada",  # Título inicial, se actualizará con el primer mensaje
                    auth_token=token
                )
                logger.info(f"✅ Nueva conversación creada: {conversation_id}")
                
                # Verificar que el WebSocket sigue conectado antes de enviar
                if websocket.client_state.name != "CONNECTED":
                    logger.error(f"❌ WebSocket desconectado antes de enviar mensaje de bienvenida")
                    return
                
                # Enviar conversation_id y mensaje de bienvenida para nueva conversación
                try:
                    await websocket.send_text(json.dumps({
                        "type": "conversation_id",
                        "conversation_id": conversation_id,
                        "timestamp": datetime.now().isoformat()
                    }))
                    await send_welcome_message(websocket, user)
                    logger.info(f"✅ Mensajes de bienvenida enviados")
                except Exception as send_error:
                    logger.error(f"❌ Error enviando mensajes de bienvenida: {send_error}")
                    # Continuar de todas formas
            else:
                logger.info(f"✅ Reutilizando conversación activa: {conversation_id}")
                
                # Verificar que el WebSocket sigue conectado antes de enviar
                if websocket.client_state.name != "CONNECTED":
                    logger.error(f"❌ WebSocket desconectado antes de cargar historial")
                    return
                
                # ✅ NUEVA FUNCIONALIDAD: Cargar historial de conversación existente
                try:
                    await send_conversation_history(websocket, conversation_id, user, token)
                    logger.info(f"✅ Historial cargado")
                except Exception as history_error:
                    logger.error(f"❌ Error cargando historial: {history_error}")
                    # Continuar de todas formas
            
            if conversation_id:
                logger.info(f"✅ Conversación de logging iniciada: {conversation_id}")
            else:
                logger.warning("⚠️ No se pudo iniciar conversación de logging, continuando sin logging")
        except Exception as init_error:
            logger.error(f"❌ Error durante inicialización de conversación: {init_error}")
            import traceback
            logger.error(f"📚 Traceback: {traceback.format_exc()}")
            # Continuar de todas formas, el WebSocket ya está aceptado
        
        # Verificar estado final del WebSocket antes de entrar al loop
        logger.info(f"🔍 Estado del WebSocket antes del loop: {websocket.client_state.name if hasattr(websocket, 'client_state') else 'unknown'}")
        if websocket.client_state.name != "CONNECTED":
            logger.error(f"❌ WebSocket no está conectado antes del loop, abortando")
            return
        
        # Mantener conexión activa y procesar mensajes
        try:
            while True:
                try:
                    # Verificar si la conexión sigue activa ANTES de intentar recibir
                    try:
                        client_state = websocket.client_state.name
                        logger.debug(f"Estado del WebSocket: {client_state}")
                        if client_state != "CONNECTED":
                            logger.info(f"WebSocket desconectado para usuario {user_id} (estado: {client_state})")
                            break
                    except Exception as state_error:
                        logger.error(f"Error verificando estado del WebSocket: {state_error}")
                        # Si no podemos verificar el estado, intentar recibir de todas formas
                    
                    # Recibir mensaje del cliente
                    logger.info(f"🔄 Esperando mensaje del usuario {user_id}...")
                    try:
                        data = await websocket.receive_text()
                    except RuntimeError as ws_error:
                        if "not connected" in str(ws_error).lower() or "accept" in str(ws_error).lower():
                            logger.error(f"❌ WebSocket no está conectado. Estado: {websocket.client_state if hasattr(websocket, 'client_state') else 'unknown'}")
                            logger.error(f"❌ Error: {ws_error}")
                            break
                        raise
                    logger.info(f"📨 Mensaje recibido del usuario {user_id}: {data[:100]}...")
                    
                    # Parsear mensaje JSON
                    try:
                        message_data = json.loads(data)
                        logger.info(f"✅ JSON parseado correctamente: {message_data}")
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Error parseando JSON del usuario {user_id}: {e}")
                        logger.error(f"📝 Datos recibidos: {data}")
                        continue
                    
                    # Validar estructura del mensaje
                    if not isinstance(message_data, dict):
                        logger.warning(f"⚠️ Mensaje no es un diccionario: {type(message_data)}")
                        continue
                    
                    if "message" not in message_data:
                        logger.warning(f"⚠️ Mensaje no tiene clave 'message': {message_data.keys()}")
                        continue
                    
                    user_message = message_data.get("message", "")
                    logger.info(f"💬 Mensaje del usuario {user_id}: '{user_message}'")
                    
                    # Registrar mensaje del usuario en el sistema de logging
                    await chat_integration.log_user_message(
                        message=user_message,
                        tokens_used=0,  # Se puede calcular si es necesario
                        metadata={"websocket_session": session_id},
                        auth_token=token
                    )
                    
                    # Actualizar título de la conversación con el primer mensaje del usuario
                    if conversation_id and len(user_message) > 10:  # Solo si el mensaje es suficientemente largo
                        await chat_integration.update_conversation_title(
                            conversation_id=conversation_id,
                            title=user_message[:50] + "..." if len(user_message) > 50 else user_message,
                            auth_token=token
                        )
                    
                    # Procesar mensaje con el agente IA REAL
                    logger.info(f"🤖 Iniciando procesamiento del mensaje del usuario {user_id}")
                    
                    # Importar y usar el procesador real de IA
                    from ..agent.openai_client import OpenAIClient
                    from ..agent.command_processor import CommandProcessor
                    
                    # Crear contexto del usuario
                    # Priorizar role del token/user, luego del contexto del mensaje
                    role_from_context = message_data.get("context", {}).get("role") if "context" in message_data else None
                    role_from_user = user.get("role")
                    
                    # Determinar el rol final (priorizar contexto del mensaje, luego user del token, luego default)
                    final_role = role_from_context or role_from_user or "member"
                    
                    # Normalizar el rol (eliminar espacios, convertir a minúsculas)
                    final_role = final_role.strip().lower() if final_role else "member"
                    
                    logger.info(f"🔍 [WebSocket] Construyendo user_context - role_from_context: '{role_from_context}', role_from_user: '{role_from_user}', final_role: '{final_role}'")
                    
                    user_context = {
                        "id": user_id,
                        "email": user.get("email", ""),
                        "role": final_role,  # Rol normalizado
                        "first_name": user.get("first_name", ""),
                        "last_name": user.get("last_name", ""),
                        "team_id": user.get("team_id"),
                        "auth_token": token  # Pasar el token JWT para autenticación
                    }
                    
                    # Si el team_id no está en user, intentar obtenerlo del contexto del mensaje
                    if not user_context.get("team_id") and "context" in message_data:
                        context = message_data.get("context", {})
                        user_context["team_id"] = context.get("team_id")
                        user_context["team_name"] = context.get("team_name")
                        logger.info(f"🔧 Team ID obtenido del contexto: {user_context.get('team_id')}")
                    
                    logger.info(f"🔧 User context final: {user_context}")
                    
                    # Marcar tiempo de inicio para calcular tiempo de respuesta (antes del try)
                    import time
                    start_time = time.time()
                    
                    try:
                        
                        # Usar instancia singleton del CommandProcessor para mantener flujos conversacionales
                        if not hasattr(websocket, 'command_processor'):
                            logger.info("🔧 Inicializando CommandProcessor...")
                            websocket.command_processor = CommandProcessor()
                            logger.info("✅ CommandProcessor inicializado")
                        
                        # Usar instancia singleton de OpenAIClient para evitar recrear en cada mensaje
                        if not hasattr(websocket, 'openai_client'):
                            logger.info("🔧 Inicializando OpenAIClient...")
                            try:
                                websocket.openai_client = OpenAIClient()
                                logger.info("✅ OpenAIClient inicializado correctamente")
                            except Exception as e:
                                logger.error(f"❌ Error inicializando OpenAIClient: {e}")
                                raise
                        
                        # NUEVA LÓGICA: Verificar si hay un flujo conversacional activo ANTES de procesar con OpenAI
                        user_id = user_context.get("id")
                        logger.info(f"🔍 Verificando flujo conversacional para user_id: {user_id}")
                        logger.info(f"🔍 Flujos activos: {list(websocket.command_processor.conversation_flows.keys())}")
                        
                        if websocket.command_processor._is_in_conversation_flow(user_id):
                            logger.info(f"🔄 Flujo conversacional activo detectado para {user_id}, procesando directamente")
                            # Procesar directamente con el flujo conversacional
                            ai_response = await websocket.command_processor._handle_conversation_flow(user_message, user_context)
                            if ai_response:
                                logger.info(f"✅ Respuesta del flujo conversacional: {ai_response}")
                                # Enviar respuesta del flujo conversacional
                                await websocket.send_text(json.dumps({
                                    "type": "assistant",
                                    "message": ai_response.get("mensaje", ""),
                                    "suggestions": ai_response.get("suggestions", []),
                                    "timestamp": datetime.now().isoformat()
                                }))
                                continue
                            else:
                                logger.warning(f"⚠️ No se obtuvo respuesta del flujo conversacional para {user_id}")
                        else:
                            logger.info(f"ℹ️ No hay flujo conversacional activo para {user_id}, usando OpenAI")
                        
                        # Si no hay flujo activo o no se procesó, usar OpenAI
                        logger.info(f"🤖 Procesando mensaje con OpenAI: '{user_message[:50]}...'")
                        ai_response = await websocket.openai_client.process_message(user_message, user_context)
                        logger.info(f"✅ Respuesta de OpenAI recibida: tipo={ai_response.get('tipo', 'unknown')}")
                        
                        # Agregar el mensaje del usuario al contexto para que los comandos puedan acceder a él
                        user_context["user_message"] = user_message
                        
                        # Si es un comando, ejecutarlo
                        if ai_response.get("tipo") == "comando":
                            # Pasar el mensaje del usuario para flujos conversacionales
                            ai_response["user_message"] = user_message
                            ai_response = await websocket.command_processor.execute_command(ai_response, user_context)
                        
                        # Generar sugerencias por defecto según el rol
                        default_suggestions = get_default_suggestions_by_role(user_context.get("role", "member"))
                        
                        # Convertir a formato del WebSocket
                        if ai_response.get("tipo") == "conversacion":
                            final_response = {
                                "type": "assistant",
                                "message": ai_response.get("mensaje", "No pude procesar tu solicitud."),
                                "timestamp": datetime.now().isoformat(),
                                "suggestions": ai_response.get("suggestions", default_suggestions)
                            }
                        elif ai_response.get("tipo") == "exito":
                            final_response = {
                                "type": "assistant",
                                "message": ai_response.get("mensaje", "Operación completada exitosamente."),
                                "timestamp": datetime.now().isoformat(),
                                "data": ai_response.get("data", {}),
                                "suggestions": ai_response.get("suggestions", default_suggestions)
                            }
                        elif ai_response.get("tipo") == "informacion":
                            final_response = {
                                "type": "assistant",
                                "message": ai_response.get("mensaje", "Aquí tienes la información solicitada."),
                                "timestamp": datetime.now().isoformat(),
                                "data": ai_response.get("data", {}),
                                "suggestions": ai_response.get("suggestions", default_suggestions)
                            }
                        elif ai_response.get("tipo") == "error":
                            final_response = {
                                "type": "error",
                                "message": ai_response.get("mensaje", "Hubo un error procesando tu solicitud."),
                                "timestamp": datetime.now().isoformat()
                            }
                        else:
                            # Respuesta genérica
                            final_response = {
                                "type": "assistant",
                                "message": ai_response.get("mensaje", "He procesado tu solicitud."),
                                "timestamp": datetime.now().isoformat(),
                                "suggestions": ai_response.get("suggestions", default_suggestions)
                            }
                        
                        ai_response = final_response
                        
                    except Exception as e:
                        logger.error(f"❌ Error procesando mensaje con IA: {e}")
                        import traceback
                        logger.error(f"📚 Traceback completo: {traceback.format_exc()}")
                        ai_response = {
                            "type": "error",
                            "message": f"Lo siento, hubo un problema procesando tu solicitud: {str(e)}. Por favor, intenta de nuevo.",
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    # Asegurar que siempre hay una respuesta
                    if not ai_response or not isinstance(ai_response, dict):
                        logger.warning(f"⚠️ ai_response no es válido: {ai_response}, creando respuesta por defecto")
                        ai_response = {
                            "type": "error",
                            "message": "No se pudo generar una respuesta. Por favor, intenta de nuevo.",
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    logger.info(f"📤 Enviando respuesta del agente IA al usuario {user_id}")
                    logger.info(f"📋 Contenido de la respuesta: {ai_response}")
                    
                    # Calcular tiempo de respuesta en milisegundos
                    try:
                        response_time_ms = int((time.time() - start_time) * 1000)
                        logger.info(f"⏱️ Tiempo de respuesta calculado: {response_time_ms}ms")
                    except NameError:
                        logger.warning("⚠️ start_time no definido, usando 0")
                        response_time_ms = 0
                    
                    # Registrar respuesta del asistente en el sistema de logging
                    await chat_integration.log_assistant_message(
                        message=ai_response.get("message", ""),
                        tokens_used=0,  # Se puede calcular si es necesario
                        response_time_ms=response_time_ms,
                        is_error=ai_response.get("type") == "error",
                        error_message=ai_response.get("message") if ai_response.get("type") == "error" else None,
                        metadata={
                            "response_type": ai_response.get("type", "assistant"),
                            "websocket_session": session_id,
                            "has_data": "data" in ai_response,
                            "has_suggestions": "suggestions" in ai_response
                        },
                        auth_token=token
                    )
                    
                    # Enviar respuesta al cliente
                    try:
                        await websocket.send_text(json.dumps(ai_response))
                        logger.info(f"✅ Respuesta enviada exitosamente al usuario {user_id}")
                    except Exception as send_error:
                        logger.error(f"❌ Error enviando respuesta al usuario {user_id}: {send_error}")
                        logger.error(f"🔍 Tipo de error: {type(send_error)}")
                        break
                    
                except WebSocketDisconnect:
                    logger.info(f"Usuario {user_id} desconectado del Agente IA")
                    # Marcar conversación como abandonada
                    await chat_integration.abandon_conversation()
                    break
                except Exception as e:
                    logger.error(f"❌ Error procesando mensaje de {user_id}: {e}")
                    logger.error(f"🔍 Tipo de error: {type(e)}")
                    logger.error(f"📚 Detalles del error: {str(e)}")
                    # Si es un error de conexión, salir del bucle
                    if "disconnect" in str(e).lower() or "connection" in str(e).lower():
                        # Marcar conversación como abandonada
                        await chat_integration.abandon_conversation()
                        break
                    continue
            
        except WebSocketDisconnect:
            logger.info(f"Usuario {user_id} desconectado del Agente IA")
            # Marcar conversación como abandonada
            await chat_integration.abandon_conversation()
            
    except Exception as e:
        logger.error(f"Error en WebSocket del Agente IA: {e}")
        try:
            await websocket.close(code=4000, reason="Error interno del servidor")
        except:
            pass

async def validate_websocket_token(token: str) -> Optional[dict]:
    """
    Validar token JWT directamente en el Agente IA
    """
    try:
        # Verificar token usando el AuthManager del agente
        payload = AuthManager.verify_token_websocket(token)
        if not payload:
            logger.error("Token no pudo ser decodificado")
            return None
        
        # Django SimpleJWT usa 'user_id' directamente, no 'sub'
        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            logger.error(f"No se encontró user_id en el payload: {payload.keys()}")
            return None
        
        # Obtener información del usuario desde el payload del token
        # Django SimpleJWT incluye username, first_name, last_name directamente
        # Si no hay role en el token, obtenerlo del perfil HPS haciendo una llamada al backend
        role = payload.get("role")
        team_id = payload.get("team_id")
        
        # Si no hay role en el token, intentar obtenerlo del backend
        if not role:
            try:
                import httpx
                backend_url = os.getenv("BACKEND_URL", "http://cryptotrace-backend:8080")
                headers = {"Authorization": f"Bearer {token}"}
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{backend_url}/api/hps/user/profile/",
                        headers=headers,
                        timeout=5.0
                    )
                    if response.status_code == 200:
                        profile_data = response.json()
                        role = profile_data.get("role") or profile_data.get("role_name")
                        if not team_id:
                            team_id = profile_data.get("team_id")
            except Exception as e:
                logger.warning(f"No se pudo obtener role del backend: {e}")
        
        user_info = {
            "id": str(user_id),  # Asegurar que sea string
            "email": payload.get("username") or payload.get("email", ""),  # Django usa 'username'
            "role": role or "member",  # Default a "member" si no hay role
            "first_name": payload.get("first_name", ""),
            "last_name": payload.get("last_name", ""),
            "team_id": team_id  # Puede ser None
        }
        
        logger.info(f"Payload del token: {payload}")
        logger.info(f"User info creado: {user_info}")
        
        return user_info
        
    except Exception as e:
        logger.error(f"Error validando token WebSocket: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

# Endpoint HTTP para verificar estado del agente
@router.get("/status")
async def get_agent_status():
    """Obtener estado del agente IA"""
    return {
        "status": "online",
        "active_connections": len(manager.active_connections),
        "connected_users": manager.get_connected_users(),
        "agent_version": "1.0.0"
    }
