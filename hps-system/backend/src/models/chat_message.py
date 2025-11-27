from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..database.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("chat_conversations.id"), nullable=False)
    message_type = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0)
    response_time_ms = Column(Integer, nullable=True)  # Tiempo de respuesta en milisegundos
    is_error = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    message_metadata = Column(Text, nullable=True)  # JSON string con metadatos adicionales
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    conversation = relationship("ChatConversation", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, conversation_id={self.conversation_id}, type={self.message_type})>"
