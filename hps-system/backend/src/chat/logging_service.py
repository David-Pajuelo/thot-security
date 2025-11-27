"""
Servicio de logging para conversaciones del chat con el agente IA
"""
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..models.chat_conversation import ChatConversation
from ..models.chat_message import ChatMessage
# UserSatisfaction eliminado


class ChatLoggingService:
    """Servicio para registrar y gestionar conversaciones del chat"""
    
    @staticmethod
    def create_conversation(
        db: Session,
        user_id: str,
        session_id: str,
        title: Optional[str] = None
    ) -> ChatConversation:
        """Crear una nueva conversación de chat"""
        conversation = ChatConversation(
            user_id=user_id,
            session_id=session_id,
            title=title or f"Conversación {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            status="active"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    
    @staticmethod
    def get_conversation_by_session(
        db: Session,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Optional[ChatConversation]:
        """Obtener conversación por session_id"""
        query = db.query(ChatConversation).filter(
            ChatConversation.session_id == session_id
        )
        if user_id:
            query = query.filter(ChatConversation.user_id == user_id)
        return query.first()
    
    @staticmethod
    def get_conversation_by_id(
        db: Session,
        conversation_id: str
    ) -> Optional[ChatConversation]:
        """Obtener conversación por ID"""
        return db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()
    
    @staticmethod
    def update_conversation_title(
        db: Session,
        conversation_id: str,
        new_title: str
    ) -> bool:
        """Actualizar el título de una conversación"""
        conversation = db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()
        
        if conversation:
            conversation.title = new_title
            db.commit()
            return True
        return False
    
    @staticmethod
    def log_message(
        db: Session,
        conversation_id: str,
        message_type: str,
        content: str,
        tokens_used: int = 0,
        response_time_ms: Optional[int] = None,
        is_error: bool = False,
        error_message: Optional[str] = None,
        message_metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """Registrar un mensaje en la conversación"""
        message = ChatMessage(
            conversation_id=conversation_id,
            message_type=message_type,
            content=content,
            tokens_used=tokens_used,
            response_time_ms=response_time_ms,
            is_error=is_error,
            error_message=error_message,
            message_metadata=json.dumps(message_metadata) if message_metadata else None
        )
        db.add(message)
        
        # Actualizar contadores de la conversación
        conversation = db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()
        if conversation:
            conversation.total_messages += 1
            conversation.total_tokens_used += tokens_used
            conversation.updated_at = datetime.utcnow()
            
            # Actualizar JSON de la conversación
            ChatLoggingService._update_conversation_json(db, conversation, message)
        
        db.commit()
        db.refresh(message)
        return message
    
    @staticmethod
    def complete_conversation(
        db: Session,
        conversation_id: str
    ) -> ChatConversation:
        """Marcar conversación como completada"""
        conversation = db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()
        
        if conversation:
            conversation.status = "completed"
            conversation.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(conversation)
        
        return conversation
    
    @staticmethod
    def abandon_conversation(
        db: Session,
        conversation_id: str
    ) -> ChatConversation:
        """Marcar conversación como abandonada"""
        conversation = db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()
        
        if conversation:
            conversation.status = "abandoned"
            conversation.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(conversation)
        
        return conversation
    
    @staticmethod
    def _update_conversation_json(db: Session, conversation: ChatConversation, new_message: ChatMessage):
        """Actualizar el JSON de la conversación con el nuevo mensaje"""
        # Obtener todos los mensajes de la conversación ordenados por fecha
        messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation.id
        ).order_by(ChatMessage.created_at).all()
        
        # Construir el JSON de la conversación
        conversation_data = {
            "conversation_id": str(conversation.id),
            "user_id": str(conversation.user_id),
            "session_id": conversation.session_id,
            "title": conversation.title,
            "status": conversation.status,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
            "total_messages": conversation.total_messages,
            "total_tokens_used": conversation.total_tokens_used,
            "messages": []
        }
        
        # Agregar todos los mensajes
        for msg in messages:
            message_data = {
                "id": str(msg.id),
                "type": msg.message_type,
                "content": msg.content,
                "tokens_used": msg.tokens_used,
                "response_time_ms": msg.response_time_ms,
                "is_error": msg.is_error,
                "error_message": msg.error_message,
                "created_at": msg.created_at.isoformat(),
                "metadata": json.loads(msg.message_metadata) if msg.message_metadata else None
            }
            conversation_data["messages"].append(message_data)
        
        # Actualizar el campo JSON
        conversation.conversation_data = conversation_data
    
    @staticmethod
    def get_user_conversations(
        db: Session,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> list[ChatConversation]:
        """Obtener conversaciones de un usuario"""
        return db.query(ChatConversation).filter(
            ChatConversation.user_id == user_id
        ).order_by(desc(ChatConversation.created_at)).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_recent_conversations(
        db: Session,
        limit: int = 10
    ) -> list[ChatConversation]:
        """Obtener conversaciones recientes con información del usuario"""
        from ..models.user import User
        
        # Obtener conversaciones recientes con JOIN opcional para evitar errores
        try:
            conversations = db.query(ChatConversation).join(
                User, ChatConversation.user_id == User.id
            ).order_by(desc(ChatConversation.created_at)).limit(limit).all()
        except Exception:
            # Si hay problema con el JOIN, obtener conversaciones sin JOIN
            conversations = db.query(ChatConversation).order_by(
                desc(ChatConversation.created_at)
            ).limit(limit).all()
            
            # Cargar información del usuario por separado
            for conversation in conversations:
                try:
                    user = db.query(User).filter(User.id == conversation.user_id).first()
                    if user:
                        conversation.user = user
                except Exception:
                    # Si no se puede cargar el usuario, continuar sin él
                    pass
        
        return conversations
    
    @staticmethod
    def get_conversation_messages(
        db: Session,
        conversation_id: str,
        limit: int = 100
    ) -> list[ChatMessage]:
        """Obtener mensajes de una conversación"""
        return db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id
        ).order_by(ChatMessage.created_at).limit(limit).all()
    
    # log_satisfaction eliminado
    
    @staticmethod
    def get_conversation_stats(
        db: Session,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Obtener estadísticas de una conversación"""
        conversation = db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()
        
        if not conversation:
            return {}
        
        messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id
        ).all()
        
        user_messages = [m for m in messages if m.message_type == "user"]
        assistant_messages = [m for m in messages if m.message_type == "assistant"]
        error_messages = [m for m in messages if m.is_error]
        
        avg_response_time = 0
        if assistant_messages:
            response_times = [m.response_time_ms for m in assistant_messages if m.response_time_ms]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
        
        return {
            "conversation_id": conversation_id,
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "error_messages": len(error_messages),
            "total_tokens": conversation.total_tokens_used,
            "avg_response_time_ms": avg_response_time,
            # Campo de satisfacción eliminado
            "duration_minutes": None,  # Se puede calcular si es necesario
            "status": conversation.status
        }
