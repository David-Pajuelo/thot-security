"""
Router para APIs de monitoreo del chat IA
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

logger = logging.getLogger(__name__)

from ..database.database import get_db
from ..auth.dependencies import get_current_user
from ..models.user import User
from ..models.chat_conversation import ChatConversation
from .schemas import (
    RealtimeMetricsResponse,
    HistoricalMetricsResponse,
    AgentPerformanceResponse,
    TopicAnalysisResponse,
    ChatAnalyticsResponse,
    ConversationStatsResponse,
    ChatConversationResponse,
    ChatConversationCreate,
    ChatMessageCreate,
    ChatMessageResponse,
# UserSatisfaction eliminado
)
from .metrics_service import ChatMetricsService
from .logging_service import ChatLoggingService

router = APIRouter(prefix="/api/v1/chat", tags=["Chat Monitoring"])


@router.get("/metrics/realtime", response_model=RealtimeMetricsResponse)
async def get_realtime_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener métricas en tiempo real del chat"""
    if not current_user.has_permission("view_chat_metrics"):
        raise HTTPException(status_code=403, detail="No tienes permisos para ver métricas del chat")
    
    metrics = ChatMetricsService.get_realtime_metrics(db)
    return RealtimeMetricsResponse(**metrics)


@router.get("/metrics/historical", response_model=List[HistoricalMetricsResponse])
async def get_historical_metrics(
    days: int = Query(7, ge=1, le=30, description="Número de días a consultar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener métricas históricas del chat"""
    if not current_user.has_permission("view_chat_metrics"):
        raise HTTPException(status_code=403, detail="No tienes permisos para ver métricas del chat")
    
    metrics = ChatMetricsService.get_historical_metrics(db, days)
    return [HistoricalMetricsResponse(**metric) for metric in metrics]


@router.get("/performance", response_model=AgentPerformanceResponse)
async def get_agent_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener métricas de rendimiento del agente IA"""
    if not current_user.has_permission("view_chat_metrics"):
        raise HTTPException(status_code=403, detail="No tienes permisos para ver métricas del chat")
    
    performance = ChatMetricsService.get_agent_performance(db)
    return AgentPerformanceResponse(**performance)


@router.get("/topics", response_model=List[TopicAnalysisResponse])
async def get_top_topics(
    limit: int = Query(10, ge=1, le=50, description="Número máximo de temas a devolver"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener temas más frecuentes en las conversaciones"""
    if not current_user.has_permission("view_chat_metrics"):
        raise HTTPException(status_code=403, detail="No tienes permisos para ver métricas del chat")
    
    topics = ChatMetricsService.get_top_topics(db, limit)
    return [TopicAnalysisResponse(**topic) for topic in topics]


@router.get("/analytics", response_model=ChatAnalyticsResponse)
async def get_chat_analytics(
    days: int = Query(7, ge=1, le=30, description="Número de días para análisis"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener análisis completo del chat"""
    if not current_user.has_permission("view_chat_metrics"):
        raise HTTPException(status_code=403, detail="No tienes permisos para ver métricas del chat")
    
    # Obtener todas las métricas
    realtime_metrics = ChatMetricsService.get_realtime_metrics(db)
    historical_metrics = ChatMetricsService.get_historical_metrics(db, days)
    agent_performance = ChatMetricsService.get_agent_performance(db)
    top_topics = ChatMetricsService.get_top_topics(db, 10)
    
    # Obtener conversaciones recientes
    recent_conversations = ChatLoggingService.get_recent_conversations(
        db, limit=10
    )
    
    return ChatAnalyticsResponse(
        realtime_metrics=RealtimeMetricsResponse(**realtime_metrics),
        historical_metrics=[HistoricalMetricsResponse(**metric) for metric in historical_metrics],
        agent_performance=AgentPerformanceResponse(**agent_performance),
        top_topics=[TopicAnalysisResponse(**topic) for topic in top_topics],
        recent_conversations=[
            ChatConversationResponse.from_orm(conv) for conv in recent_conversations
        ]
    )


@router.post("/conversations", response_model=ChatConversationResponse)
async def create_conversation(
    conversation_data: ChatConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crear una nueva conversación de chat"""
    conversation = ChatLoggingService.create_conversation(
        db=db,
        user_id=conversation_data.user_id,
        session_id=conversation_data.session_id,
        title=conversation_data.title
    )
    return ChatConversationResponse.from_orm(conversation)


@router.get("/conversations", response_model=List[ChatConversationResponse])
async def get_user_conversations(
    limit: int = Query(50, ge=1, le=100, description="Número máximo de conversaciones"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener conversaciones del usuario actual (activas + archivadas)"""
    conversations = ChatLoggingService.get_user_conversations(
        db, current_user.id, limit, offset
    )
    return [ChatConversationResponse.from_orm(conv) for conv in conversations]

@router.get("/conversations/all", response_model=List[ChatConversationResponse])
async def get_all_conversations(
    limit: int = Query(100, ge=1, le=500, description="Número máximo de conversaciones"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener todas las conversaciones de todos los usuarios (solo para admins)"""
    if not current_user.has_permission("view_chat_metrics"):
        raise HTTPException(status_code=403, detail="No tienes permisos para ver todas las conversaciones")
    
    try:
        # Obtener todas las conversaciones ordenadas por fecha de creación
        conversations = db.query(ChatConversation).order_by(
            desc(ChatConversation.created_at)
        ).offset(offset).limit(limit).all()
        
        return [ChatConversationResponse.from_orm(conv) for conv in conversations]
        
    except Exception as e:
        logger.error(f"Error obteniendo todas las conversaciones: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@router.get("/conversations/history", response_model=List[ChatConversationResponse])
async def get_user_conversation_history(
    limit: int = Query(100, ge=1, le=500, description="Número máximo de conversaciones"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
    include_active: bool = Query(True, description="Incluir conversaciones activas"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener histórico completo de conversaciones del usuario (activas + archivadas)"""
    try:
        # Obtener conversaciones archivadas
        archived_conversations = db.query(ChatConversation).filter(
            and_(
                ChatConversation.user_id == str(current_user.id),
                ChatConversation.status == "archived"
            )
        ).order_by(desc(ChatConversation.closed_at)).limit(limit).offset(offset).all()
        
        result = [ChatConversationResponse.from_orm(conv) for conv in archived_conversations]
        
        # Si se solicitan conversaciones activas, agregarlas al inicio
        if include_active:
            active_conversations = db.query(ChatConversation).filter(
                and_(
                    ChatConversation.user_id == str(current_user.id),
                    ChatConversation.status == "active"
                )
            ).order_by(desc(ChatConversation.created_at)).all()
            
            active_results = [ChatConversationResponse.from_orm(conv) for conv in active_conversations]
            result = active_results + result
        
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo histórico de conversaciones: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.get("/conversations/{conversation_id}/stats", response_model=ConversationStatsResponse)
async def get_conversation_stats(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener estadísticas de una conversación específica"""
    stats = ChatLoggingService.get_conversation_stats(db, conversation_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    return ConversationStatsResponse(**stats)


@router.post("/messages", response_model=ChatMessageResponse)
async def create_message(
    message_data: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crear un nuevo mensaje en una conversación"""
    message = ChatLoggingService.log_message(
        db=db,
        conversation_id=message_data.conversation_id,
        message_type=message_data.message_type,
        content=message_data.content,
        tokens_used=message_data.tokens_used,
        response_time_ms=message_data.response_time_ms,
        is_error=message_data.is_error,
        error_message=message_data.error_message,
        message_metadata=message_data.message_metadata
    )
    return ChatMessageResponse.from_orm(message)


# Endpoint de satisfacción eliminado


@router.put("/conversations/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: str,
    title_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualizar el título de una conversación"""
    conversation = ChatLoggingService.get_conversation_by_id(db, conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta conversación")
    
    new_title = title_data.get("title", "")
    if new_title:
        ChatLoggingService.update_conversation_title(db, conversation_id, new_title)
        return {"message": "Título actualizado", "title": new_title}
    
    return {"message": "Título no proporcionado"}


@router.post("/conversations/{conversation_id}/complete")
async def complete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marcar una conversación como completada"""
    conversation = ChatLoggingService.get_conversation_by_id(
        db, conversation_id
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    ChatLoggingService.complete_conversation(
        db, conversation_id
    )
    
    return {"message": "Conversación completada exitosamente"}


@router.post("/conversations/{conversation_id}/abandon")
async def abandon_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marcar una conversación como abandonada"""
    conversation = ChatLoggingService.get_conversation_by_id(
        db, conversation_id
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    ChatLoggingService.abandon_conversation(db, conversation_id)
    
    return {"message": "Conversación marcada como abandonada"}


@router.get("/conversations/active")
async def get_active_conversation(
    user_id: str = Query(..., description="ID del usuario"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener la conversación activa de un usuario"""
    try:
        # Verificar permisos (solo admin o el propio usuario)
        if current_user.role.name != "admin" and str(current_user.id) != user_id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para ver las conversaciones de este usuario"
            )
        
        # Buscar conversación activa del usuario
        conversation = db.query(ChatConversation).filter(
            and_(
                ChatConversation.user_id == user_id,
                ChatConversation.status == "active"
            )
        ).order_by(desc(ChatConversation.created_at)).first()
        
        if conversation:
            return {
                "success": True,
                "conversation_id": str(conversation.id),
                "conversation": ChatConversationResponse.from_orm(conversation)
            }
        else:
            return {
                "success": True,
                "conversation_id": None,
                "message": "No hay conversaciones activas"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo conversación activa: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100, description="Número máximo de mensajes"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener mensajes de una conversación específica"""
    try:
        # Verificar que la conversación existe
        conversation = ChatLoggingService.get_conversation_by_id(db, conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversación no encontrada"
            )
        
        # Verificar permisos (solo admin o el propio usuario)
        if current_user.role.name != "admin" and conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para ver esta conversación"
            )
        
        # Obtener mensajes de la conversación
        messages = ChatLoggingService.get_conversation_messages(db, conversation_id, limit)
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "messages": [
                {
                    "id": msg.id,
                    "message_type": msg.message_type,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "tokens_used": msg.tokens_used,
                    "suggestions": msg.message_metadata.get("suggestions", []) if isinstance(msg.message_metadata, dict) else []
                }
                for msg in messages
            ],
            "total": len(messages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo mensajes de conversación: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.post("/conversations/archive-active")
async def archive_active_conversation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Archivar conversación activa del usuario actual"""
    try:
        # Buscar conversación activa del usuario
        active_conversation = db.query(ChatConversation).filter(
            and_(
                ChatConversation.user_id == str(current_user.id),
                ChatConversation.status == "active"
            )
        ).first()
        
        if not active_conversation:
            return {
                "success": True,
                "message": "No hay conversación activa para archivar",
                "archived_conversation_id": None
            }
        
        # Cambiar estado a "archived" y agregar timestamp de cierre
        active_conversation.status = "archived"
        active_conversation.closed_at = datetime.now()
        
        db.commit()
        
        logger.info(f"Conversación {active_conversation.id} archivada para usuario {current_user.id}")
        
        return {
            "success": True,
            "message": "Conversación archivada exitosamente",
            "archived_conversation_id": str(active_conversation.id)
        }
        
    except Exception as e:
        logger.error(f"Error archivando conversación: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@router.post("/conversations/{conversation_id}/mark_inactive")
async def mark_conversation_inactive(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marcar una conversación como inactiva"""
    try:
        conversation = ChatLoggingService.get_conversation_by_id(db, conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversación no encontrada"
            )
        
        # Verificar permisos (solo admin o el propio usuario)
        if current_user.role.name != "admin" and conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para modificar esta conversación"
            )
        
        # Marcar como inactiva
        conversation.is_active = False
        conversation.updated_at = datetime.now()
        db.commit()
        
        return {
            "success": True,
            "message": "Conversación marcada como inactiva",
            "conversation_id": conversation_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marcando conversación como inactiva: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.get("/conversations/{conversation_id}/full")
async def get_full_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener la conversación completa en formato JSON"""
    try:
        conversation = ChatLoggingService.get_conversation_by_id(db, conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversación no encontrada"
            )
        
        # Verificar permisos (solo admin o el propio usuario)
        if current_user.role.name != "admin" and conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para ver esta conversación"
            )
        
        return {
            "success": True,
            "conversation": ChatConversationResponse.from_orm(conversation)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo conversación completa: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@router.post("/conversations/reset")
async def reset_active_conversation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resetear conversación activa del usuario (archivar actual y crear nueva)"""
    try:
        # Buscar conversación activa del usuario
        active_conversation = db.query(ChatConversation).filter(
            and_(
                ChatConversation.user_id == str(current_user.id),
                ChatConversation.status == "active"
            )
        ).first()
        
        if active_conversation:
            # Marcar conversación actual como cerrada (histórico)
            active_conversation.status = "closed"
            active_conversation.closed_at = datetime.now()
            active_conversation.updated_at = datetime.now()
            db.commit()
            
            logger.info(f"✅ Conversación {active_conversation.id} archivada para usuario {current_user.email}")
        
        # Crear nueva conversación activa
        new_conversation = ChatLoggingService.create_conversation(
            db=db,
            user_id=str(current_user.id),
            session_id=f"reset_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title="Nueva conversación iniciada"
        )
        
        logger.info(f"✅ Nueva conversación creada: {new_conversation.id} para usuario {current_user.email}")
        
        return {
            "success": True,
            "message": "Conversación reseteada exitosamente",
            "new_conversation_id": str(new_conversation.id),
            "archived_conversation_id": str(active_conversation.id) if active_conversation else None
        }
        
    except Exception as e:
        logger.error(f"Error reseteando conversación para usuario {current_user.email}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )
