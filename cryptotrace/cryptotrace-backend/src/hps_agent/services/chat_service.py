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
    def log_user_message(
        conversation_id: str,
        message: str,
        tokens_used: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Registrar mensaje del usuario"""
        try:
            conversation = ChatConversation.objects.get(id=conversation_id)
            ChatMessage.objects.create(
                conversation=conversation,
                message_type='user',
                content=message,
                tokens_used=tokens_used,
                message_metadata=metadata or {}
            )
            logger.info(f"✅ Mensaje del usuario registrado en conversación {conversation_id}")
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
            ChatMessage.objects.create(
                conversation=conversation,
                message_type='assistant',
                content=message,
                tokens_used=tokens_used,
                response_time_ms=response_time_ms,
                is_error=is_error,
                error_message=error_message,
                message_metadata=metadata or {}
            )
            logger.info(f"✅ Mensaje del asistente registrado en conversación {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Error registrando mensaje del asistente: {e}")
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
            
            return [
                {
                    'type': msg.message_type,
                    'message': msg.content,
                    'timestamp': msg.created_at.isoformat(),
                    'tokens_used': msg.tokens_used,
                    'metadata': msg.message_metadata
                }
                for msg in messages
            ]
        except Exception as e:
            logger.error(f"Error obteniendo mensajes: {e}")
            return []

