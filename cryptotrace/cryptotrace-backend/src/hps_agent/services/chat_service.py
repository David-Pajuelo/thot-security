"""
Servicio de Chat para guardado directo en Django
"""
import logging
from typing import Optional, Dict, Any
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from hps_core.models import ChatConversation, ChatMessage

logger = logging.getLogger(__name__)
User = get_user_model()


class ChatService:
    """Servicio para gestionar conversaciones y mensajes de chat directamente en Django"""
    
    @staticmethod
    @database_sync_to_async
    def get_user_by_id(user_id: str):
        """Obtener usuario por ID"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    @database_sync_to_async
    def find_active_conversation(user_id: str) -> Optional[str]:
        """Buscar conversación activa del usuario"""
        try:
            user = User.objects.get(id=user_id)
            conversation = ChatConversation.objects.filter(
                user=user,
                status='active'
            ).order_by('-created_at').first()
            
            if conversation:
                return str(conversation.id)
            return None
        except Exception as e:
            logger.error(f"Error buscando conversación activa: {e}")
            return None
    
    @staticmethod
    @database_sync_to_async
    def create_conversation(user_id: str, session_id: str, title: Optional[str] = None) -> Optional[str]:
        """Crear nueva conversación"""
        try:
            user = User.objects.get(id=user_id)
            conversation = ChatConversation.objects.create(
                user=user,
                session_id=session_id,
                title=title or f"Conversación {session_id[:8]}",
                status='active'
            )
            logger.info(f"✅ Conversación creada: {conversation.id}")
            return str(conversation.id)
        except Exception as e:
            logger.error(f"Error creando conversación: {e}")
            return None

    @staticmethod
    @database_sync_to_async
    def conversation_belongs_to_user(conversation_id: str, user_id: str) -> bool:
        """Comprobar si la conversación existe y pertenece al usuario (p. ej. tras reset)."""
        try:
            return ChatConversation.objects.filter(
                id=conversation_id,
                user_id=user_id
            ).exists()
        except Exception as e:
            logger.warning(f"Error comprobando conversación: {e}")
            return False

    @staticmethod
    @database_sync_to_async
    def log_user_message(
        conversation_id: str,
        message: str,
        tokens_used: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Registrar mensaje del usuario"""
        try:
            conversation = ChatConversation.objects.get(id=conversation_id)
            
            # Serializar metadata a JSON string si es un diccionario
            metadata_str = ''
            if metadata:
                import json
                metadata_str = json.dumps(metadata)
            
            ChatMessage.objects.create(
                conversation=conversation,
                message_type='user',
                content=message,
                tokens_used=tokens_used,
                message_metadata=metadata_str
            )
            # Actualizar contador de mensajes
            conversation.total_messages = conversation.messages.count()
            conversation.save(update_fields=['total_messages'])
            logger.info(f"✅ Mensaje del usuario registrado en conversación {conversation_id} (total: {conversation.total_messages})")
            return True
        except Exception as e:
            logger.error(f"Error registrando mensaje del usuario: {e}")
            return False
    
    @staticmethod
    @database_sync_to_async
    def log_assistant_message(
        conversation_id: str,
        message: str,
        tokens_used: int = 0,
        response_time_ms: Optional[int] = None,
        is_error: bool = False,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Registrar mensaje del asistente"""
        try:
            conversation = ChatConversation.objects.get(id=conversation_id)
            # Preparar datos para crear el mensaje
            # error_message debe ser cadena vacía si es None (el modelo no acepta null)
            # Serializar metadata a JSON string si es un diccionario
            metadata_str = ''
            if metadata:
                import json
                metadata_str = json.dumps(metadata)
            
            message_data = {
                'conversation': conversation,
                'message_type': 'assistant',
                'content': message,
                'tokens_used': tokens_used,
                'response_time_ms': response_time_ms,
                'is_error': is_error,
                'error_message': error_message or '',  # Cadena vacía si es None
                'message_metadata': metadata_str
            }
            
            ChatMessage.objects.create(**message_data)
            # Actualizar contador de mensajes
            conversation.total_messages = conversation.messages.count()
            conversation.save(update_fields=['total_messages'])
            logger.info(f"✅ Mensaje del asistente registrado en conversación {conversation_id} (total: {conversation.total_messages})")
            return True
        except Exception as e:
            logger.error(f"Error registrando mensaje del asistente: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    @staticmethod
    @database_sync_to_async
    def complete_conversation(
        conversation_id: str,
        satisfaction_rating: Optional[int] = None,
        satisfaction_feedback: Optional[str] = None
    ) -> bool:
        """Completar conversación"""
        try:
            conversation = ChatConversation.objects.get(id=conversation_id)
            conversation.status = 'closed'
            if satisfaction_rating is not None:
                conversation.satisfaction_rating = satisfaction_rating
            if satisfaction_feedback:
                conversation.satisfaction_feedback = satisfaction_feedback
            conversation.save()
            logger.info(f"✅ Conversación completada: {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Error completando conversación: {e}")
            return False
    
    @staticmethod
    @database_sync_to_async
    def get_conversation_messages(conversation_id: str, limit: int = 50):
        """Obtener mensajes de una conversación"""
        try:
            conversation = ChatConversation.objects.get(id=conversation_id)
            messages = ChatMessage.objects.filter(
                conversation=conversation
            ).order_by('created_at')[:limit]
            
            result = []
            import json
            for msg in messages:
                # Parsear metadata si es un string JSON
                metadata = {}
                if msg.message_metadata:
                    try:
                        if isinstance(msg.message_metadata, str):
                            metadata = json.loads(msg.message_metadata) if msg.message_metadata.strip() else {}
                        elif isinstance(msg.message_metadata, dict):
                            metadata = msg.message_metadata
                    except (json.JSONDecodeError, TypeError):
                        metadata = {}
                
                # Extraer sugerencias del metadata si existen
                suggestions = metadata.get('suggestions', [])
                
                result.append({
                    'type': msg.message_type,
                    'message': msg.content,
                    'timestamp': msg.created_at.isoformat(),
                    'tokens_used': msg.tokens_used,
                    'metadata': metadata,
                    'suggestions': suggestions if suggestions else []
                })
            return result
        except Exception as e:
            logger.error(f"Error obteniendo mensajes: {e}")
            return []

    @staticmethod
    @database_sync_to_async
    def user_has_welcome_in_any_conversation(user_id: str) -> bool:
        """True si el usuario tiene ya un mensaje de bienvenida en alguna conversación (evitar duplicados al reconectar)."""
        try:
            from django.db.models import Q
            welcome_marker = "¿En qué puedo ayudarte hoy?"
            has_welcome = ChatMessage.objects.filter(
                conversation__user_id=user_id
            ).filter(
                Q(content__icontains=welcome_marker) | Q(message_metadata__icontains='"type":"welcome"')
            ).exists()
            return has_welcome
        except Exception as e:
            logger.warning(f"Error comprobando bienvenida por usuario: {e}")
            return False

