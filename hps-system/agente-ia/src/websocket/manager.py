"""
Gestor de conexiones WebSocket para el Agente IA
"""
import json
import logging
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Gestor de conexiones WebSocket para chat en tiempo real"""
    
    def __init__(self):
        # Diccionario de conexiones activas {user_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # Historial de mensajes por usuario {user_id: [messages]}
        self.message_history: Dict[str, List[dict]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Conectar un nuevo WebSocket"""
        await websocket.accept()
        
        # Si ya hay una conexión para este usuario, cerrarla
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].close()
            except:
                pass
        
        # Agregar nueva conexión
        self.active_connections[user_id] = websocket
        
        # Inicializar historial si no existe
        if user_id not in self.message_history:
            self.message_history[user_id] = []
        
        logger.info(f"Usuario {user_id} conectado al WebSocket")
        
        # Enviar mensaje de bienvenida
        try:
            await self.send_welcome_message(user_id, websocket)
            # Enviar ping inicial para mantener conexión activa
            await self.send_ping(user_id)
        except Exception as e:
            logger.error(f"Error enviando mensajes iniciales: {e}")
            # No desconectar por errores en mensajes iniciales
    
    async def disconnect(self, user_id: str):
        """Desconectar un WebSocket"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].close()
            except:
                pass
            del self.active_connections[user_id]
            logger.info(f"Usuario {user_id} desconectado del WebSocket")
    
    async def send_personal_message(self, message: str, user_id: str):
        """Enviar mensaje personal a un usuario específico"""
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_text(message)
                
                # Guardar en historial
                self.message_history[user_id].append({
                    "type": "system",
                    "content": message,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error enviando mensaje a usuario {user_id}: {e}")
                await self.disconnect(user_id)
    
    async def send_welcome_message(self, user_id: str, websocket: WebSocket):
        """Enviar mensaje de bienvenida al conectar"""
        welcome_data = {
            "type": "system",
            "message": "¡Bienvenido al chat IA del Sistema HPS! Estoy aquí para ayudarte.",
            "timestamp": datetime.now().isoformat(),
            "suggestions": [
                "¿Cuál es el estado de mi HPS?",
                "Necesito ayuda con una solicitud",
                "¿Cómo puedo crear una nueva solicitud?"
            ]
        }
        
        try:
            await websocket.send_text(json.dumps(welcome_data))
            
            # Guardar en historial
            self.message_history[user_id].append(welcome_data)
            
        except Exception as e:
            logger.error(f"Error enviando mensaje de bienvenida: {e}")
    
    async def process_user_message(self, user_id: str, message_data: dict, user_context: dict):
        """Procesar mensaje del usuario directamente con el agente IA"""
        try:
            # Extraer mensaje del usuario
            user_message = message_data.get("message", "")
            
            if not user_message.strip():
                await self.send_error_message(user_id, "Mensaje vacío recibido")
                return
            
            # Enviar indicador de "escribiendo..."
            await self.send_typing_indicator(user_id, True)
            
            # TODO: Aquí procesarías el mensaje con OpenAI y el procesador de comandos
            # Por ahora, simulamos una respuesta básica
            
            # Simular procesamiento del agente IA
            ai_response = await self.process_with_agent_ia(user_message, user_context)
            
            # Quitar indicador de "escribiendo..."
            await self.send_typing_indicator(user_id, False)
            
            # Enviar respuesta del agente al usuario
            response_data = {
                "type": "assistant",
                "message": ai_response.get("message", "Lo siento, hubo un error procesando tu solicitud."),
                "timestamp": datetime.now().isoformat(),
                "data": ai_response.get("data", {}),
                "suggestions": ai_response.get("suggestions", [])
            }
            
            await self.send_personal_message(json.dumps(response_data), user_id)
            
        except Exception as e:
            logger.error(f"Error procesando mensaje de usuario {user_id}: {e}")
            await self.send_typing_indicator(user_id, False)
            await self.send_error_message(user_id, "Error interno procesando tu mensaje")
    
    async def process_with_agent_ia(self, message: str, user_context: dict) -> dict:
        """Procesar mensaje con el agente IA (OpenAI + CommandProcessor)"""
        try:
            # Importar aquí para evitar circular imports
            from ..agent.openai_client import OpenAIClient
            from ..agent.command_processor import CommandProcessor
            
            # Crear instancias si no existen
            if not hasattr(self, 'openai_client'):
                self.openai_client = OpenAIClient()
                self.command_processor = CommandProcessor()
            
            # 1. Procesar mensaje con OpenAI
            ai_response = await self.openai_client.process_message(
                message=message,
                user_context=user_context
            )
            
            logger.info(f"Respuesta de OpenAI: {ai_response.get('tipo', 'unknown')}")
            
            # 2. Si es un comando, ejecutarlo
            if ai_response.get("tipo") == "comando" and ai_response.get("requiere_api", False):
                final_response = await self.command_processor.execute_command(ai_response, user_context)
            else:
                final_response = ai_response
            
            # 3. Generar sugerencias basadas en el rol del usuario
            suggestions = self.generate_suggestions(user_context.get("role", "member"))
            
            # 4. Formatear respuesta final
            response_message = final_response.get("mensaje", "Lo siento, no pude procesar tu solicitud.")
            
            return {
                "message": response_message,
                "data": final_response.get("data", {}),
                "suggestions": suggestions
            }
                
        except Exception as e:
            logger.error(f"Error procesando con agente IA: {e}")
            # Fallback a respuesta básica
            return {
                "message": f"He recibido tu mensaje: '{message}'. El agente IA está temporalmente no disponible, pero he registrado tu consulta.",
                "data": {},
                "suggestions": ["¿Cuál es el estado de mi HPS?", "Necesito ayuda", "Crear solicitud"]
            }
    
    def generate_suggestions(self, user_role: str) -> list:
        """Generar sugerencias basadas en el rol del usuario"""
        base_suggestions = [
            "¿Cuál es el estado de mi HPS?",
            "Necesito ayuda con una solicitud"
        ]
        
        if user_role in ["admin", "team_lead"]:
            base_suggestions.extend([
                "¿Cómo puedo crear una nueva solicitud?",
                "Revisar estadísticas del sistema",
                "Gestionar usuarios del equipo"
            ])
        else:
            base_suggestions.extend([
                "¿Cómo puedo crear una nueva solicitud?",
                "¿Qué documentos necesito?",
                "¿Cuándo tendré respuesta?"
            ])
        
        return base_suggestions
    
    async def send_ping(self, user_id: str):
        """Enviar ping para mantener conexión activa"""
        if user_id in self.active_connections:
            try:
                ping_data = {
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                }
                await self.active_connections[user_id].send_text(json.dumps(ping_data))
            except Exception as e:
                logger.error(f"Error enviando ping a usuario {user_id}: {e}")
                await self.disconnect(user_id)
    
    async def send_typing_indicator(self, user_id: str, is_typing: bool):
        """Enviar indicador de que el agente está escribiendo"""
        typing_data = {
            "type": "typing",
            "is_typing": is_typing,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_personal_message(json.dumps(typing_data), user_id)
    
    async def send_error_message(self, user_id: str, error_message: str):
        """Enviar mensaje de error al usuario"""
        error_data = {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_personal_message(json.dumps(error_data), user_id)
    
    async def broadcast(self, message: str):
        """Enviar mensaje a todos los usuarios conectados"""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)
    
    def get_connected_users(self) -> List[str]:
        """Obtener lista de usuarios conectados"""
        return list(self.active_connections.keys())
    
    def is_connected(self, user_id: str) -> bool:
        """Verificar si un usuario está conectado"""
        return user_id in self.active_connections

# Instancia global del manager
manager = WebSocketManager()
