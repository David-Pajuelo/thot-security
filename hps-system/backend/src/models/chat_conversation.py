from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..database.database import Base


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), nullable=False, index=True)
    title = Column(String(500), nullable=True)
    status = Column(String(50), default="active")  # active, closed, archived
    total_messages = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    # Campos de satisfacción eliminados
    conversation_data = Column(JSON, nullable=True)  # Almacena la conversación completa en JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)  # Fecha de cierre de la conversación
    
    # Relaciones
    user = relationship("User", back_populates="chat_conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatConversation(id={self.id}, user_id={self.user_id}, session_id={self.session_id})>"
