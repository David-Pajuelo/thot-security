from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from ..database.database import Base


class ChatMetrics(Base):
    __tablename__ = "chat_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    total_conversations = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    avg_response_time_ms = Column(Float, default=0.0)
    avg_satisfaction_rating = Column(Float, default=0.0)
    error_rate = Column(Float, default=0.0)
    active_users = Column(Integer, default=0)
    peak_concurrent_users = Column(Integer, default=0)
    most_common_topics = Column(Text, nullable=True)  # JSON string
    system_health_score = Column(Float, default=100.0)  # 0-100
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ChatMetrics(id={self.id}, date={self.date}, conversations={self.total_conversations})>"





