"""
Esquemas Pydantic para el monitoreo del chat IA
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatConversationBase(BaseModel):
    session_id: str
    title: Optional[str] = None
    status: str = "active"


class ChatConversationCreate(ChatConversationBase):
    user_id: str


class UserInfo(BaseModel):
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None

class ChatConversationResponse(ChatConversationBase):
    id: str
    user_id: str
    user: Optional[UserInfo] = None
    total_messages: int
    total_tokens_used: int
    # Campos de satisfacción eliminados
    conversation_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Convertir UUID a string para compatibilidad con Pydantic"""
        # Obtener información del usuario si está disponible
        user_info = None
        if hasattr(obj, 'user') and obj.user:
            user_info = UserInfo(
                id=str(obj.user.id),
                email=obj.user.email,
                first_name=obj.user.first_name,
                last_name=obj.user.last_name,
                role=obj.user.role.name if hasattr(obj.user.role, 'name') else str(obj.user.role)
            )
        
        data = {
            "id": str(obj.id),
            "user_id": str(obj.user_id),
            "user": user_info,
            "session_id": obj.session_id,
            "title": obj.title,
            "status": obj.status,
            "total_messages": obj.total_messages,
            "total_tokens_used": obj.total_tokens_used,
            # Campos de satisfacción eliminados
            "conversation_data": obj.conversation_data,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "completed_at": obj.completed_at
        }
        return cls(**data)


class ChatMessageBase(BaseModel):
    message_type: str  # user, assistant, system
    content: str
    tokens_used: int = 0
    response_time_ms: Optional[int] = None
    is_error: bool = False
    error_message: Optional[str] = None
    message_metadata: Optional[Dict[str, Any]] = None


class ChatMessageCreate(ChatMessageBase):
    conversation_id: str


class ChatMessageResponse(ChatMessageBase):
    id: str
    conversation_id: str
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Convertir UUID a string para compatibilidad con Pydantic"""
        # Parsear message_metadata si es string JSON
        metadata = obj.message_metadata
        if isinstance(metadata, str):
            try:
                import json
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = None
        
        data = {
            "id": str(obj.id),
            "conversation_id": str(obj.conversation_id),
            "message_type": obj.message_type,
            "content": obj.content,
            "tokens_used": obj.tokens_used,
            "response_time_ms": obj.response_time_ms,
            "is_error": obj.is_error,
            "error_message": obj.error_message,
            "message_metadata": metadata,
            "created_at": obj.created_at
        }
        return cls(**data)


# UserSatisfaction eliminado


class RealtimeMetricsResponse(BaseModel):
    timestamp: str
    active_conversations: int
    total_conversations_today: int
    total_messages_today: int
    total_tokens_today: int
    avg_response_time_ms: float
    error_rate_percent: float
    active_users_24h: int
    completed_conversations_today: int
    # Campo de satisfacción eliminado
    conversations_by_hour: Dict[str, int]
    system_health_score: float


class HistoricalMetricsResponse(BaseModel):
    date: str
    conversations: int
    messages: int
    tokens: int
    avg_response_time_ms: float
    # Campo de satisfacción eliminado


class AgentPerformanceResponse(BaseModel):
    total_responses: int
    avg_response_time_ms: float
    error_rate_percent: float
    success_rate_percent: float


class TopicAnalysisResponse(BaseModel):
    topic: str
    count: int


class ConversationStatsResponse(BaseModel):
    conversation_id: str
    total_messages: int
    user_messages: int
    assistant_messages: int
    error_messages: int
    total_tokens: int
    avg_response_time_ms: float
    # Campo de satisfacción eliminado
    duration_minutes: Optional[float]
    status: str


class ChatAnalyticsResponse(BaseModel):
    realtime_metrics: RealtimeMetricsResponse
    historical_metrics: List[HistoricalMetricsResponse]
    agent_performance: AgentPerformanceResponse
    top_topics: List[TopicAnalysisResponse]
    recent_conversations: List[ChatConversationResponse]
