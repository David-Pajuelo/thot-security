"""
Servicio de métricas en tiempo real para el chat con el agente IA
"""
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from ..models.chat_conversation import ChatConversation
from ..models.chat_message import ChatMessage
from ..models.chat_metrics import ChatMetrics
# UserSatisfaction eliminado


class ChatMetricsService:
    """Servicio para calcular y gestionar métricas del chat en tiempo real"""
    
    @staticmethod
    def get_realtime_metrics(db: Session) -> Dict[str, Any]:
        """Obtener métricas en tiempo real del chat"""
        now = datetime.utcnow()
        today = now.date()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Conversaciones activas hoy
        active_conversations_today = db.query(ChatConversation).filter(
            and_(
                func.date(ChatConversation.created_at) == today,
                ChatConversation.status == "active"
            )
        ).count()
        
        # Total de conversaciones hoy
        total_conversations_today = db.query(ChatConversation).filter(
            func.date(ChatConversation.created_at) == today
        ).count()
        
        # Total de mensajes hoy
        total_messages_today = db.query(ChatMessage).join(ChatConversation).filter(
            func.date(ChatMessage.created_at) == today
        ).count()
        
        # Total de tokens usados hoy
        total_tokens_today = db.query(func.sum(ChatMessage.tokens_used)).join(ChatConversation).filter(
            func.date(ChatMessage.created_at) == today
        ).scalar() or 0
        
        # Tiempo promedio de respuesta hoy (excluyendo mensajes de bienvenida)
        # Primero obtener todos los mensajes del agente de hoy
        agent_messages_today = db.query(ChatMessage).join(ChatConversation).filter(
            and_(
                func.date(ChatMessage.created_at) == today,
                ChatMessage.message_type == "assistant",
                ChatMessage.response_time_ms.isnot(None)
            )
        ).all()
        
        # Filtrar mensajes de bienvenida
        valid_agent_messages = [
            msg for msg in agent_messages_today 
            if not ChatMetricsService._is_welcome_message(msg)
        ]
        
        # Calcular tiempo promedio solo de mensajes válidos
        if valid_agent_messages:
            avg_response_time = sum(msg.response_time_ms for msg in valid_agent_messages) / len(valid_agent_messages)
        else:
            avg_response_time = 0
        
        # Tasa de error hoy
        error_messages_today = db.query(ChatMessage).join(ChatConversation).filter(
            and_(
                func.date(ChatMessage.created_at) == today,
                ChatMessage.is_error == True
            )
        ).count()
        
        error_rate = 0
        if total_messages_today > 0:
            error_rate = (error_messages_today / total_messages_today) * 100
        
        # Usuarios activos en las últimas 24h
        active_users_24h = db.query(func.count(func.distinct(ChatConversation.user_id))).filter(
            ChatConversation.created_at >= last_24h
        ).scalar() or 0
        
        # Conversaciones completadas hoy
        completed_conversations_today = db.query(ChatConversation).filter(
            and_(
                func.date(ChatConversation.created_at) == today,
                ChatConversation.status == "completed"
            )
        ).count()
        
        # Satisfacción eliminada - usar valor por defecto
        avg_satisfaction = 0
        
        # Conversaciones por hora (últimas 24h)
        conversations_by_hour = db.query(
            func.extract('hour', ChatConversation.created_at).label('hour'),
            func.count(ChatConversation.id).label('count')
        ).filter(
            ChatConversation.created_at >= last_24h
        ).group_by(
            func.extract('hour', ChatConversation.created_at)
        ).all()
        
        hourly_data = {str(int(hour)): count for hour, count in conversations_by_hour}
        
        return {
            "timestamp": now.isoformat(),
            "active_conversations": active_conversations_today,
            "total_conversations_today": total_conversations_today,
            "total_messages_today": total_messages_today,
            "total_tokens_today": int(total_tokens_today),
            "avg_response_time_ms": round(avg_response_time, 2),
            "error_rate_percent": round(error_rate, 2),
            "active_users_24h": active_users_24h,
            "completed_conversations_today": completed_conversations_today,
            # Campo de satisfacción eliminado
            "conversations_by_hour": hourly_data,
            "system_health_score": ChatMetricsService._calculate_health_score(
                error_rate, avg_response_time
            )
        }
    
    @staticmethod
    def get_historical_metrics(
        db: Session,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Obtener métricas históricas de los últimos N días"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days-1)
        
        # Obtener métricas diarias
        daily_metrics = db.query(
            func.date(ChatConversation.created_at).label('date'),
            func.count(ChatConversation.id).label('conversations'),
            func.count(ChatMessage.id).label('messages'),
            func.sum(ChatMessage.tokens_used).label('tokens'),
            func.avg(ChatMessage.response_time_ms).label('avg_response_time'),
            # Satisfacción eliminada
        ).outerjoin(ChatMessage).filter(
            and_(
                func.date(ChatConversation.created_at) >= start_date,
                func.date(ChatConversation.created_at) <= end_date
            )
        ).group_by(
            func.date(ChatConversation.created_at)
        ).order_by(
            func.date(ChatConversation.created_at)
        ).all()
        
        result = []
        for metric in daily_metrics:
            result.append({
                "date": metric.date.isoformat(),
                "conversations": metric.conversations or 0,
                "messages": metric.messages or 0,
                "tokens": int(metric.tokens or 0),
                "avg_response_time_ms": round(metric.avg_response_time or 0, 2),
                # Satisfacción eliminada
            })
        
        return result
    
    @staticmethod
    def get_top_topics(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener temas más frecuentes en las conversaciones"""
        # Obtener mensajes de usuario recientes
        user_messages = db.query(ChatMessage).join(ChatConversation).filter(
            ChatMessage.message_type == "user"
        ).order_by(desc(ChatMessage.created_at)).limit(1000).all()
        
        # Análisis de preguntas completas en lugar de palabras individuales
        question_patterns = {}
        
        for message in user_messages:
            content = message.content.lower().strip()
            
            # Patrones de preguntas comunes
            if any(keyword in content for keyword in ['comandos', 'comando']):
                question_patterns['¿Qué comandos tienes disponibles?'] = question_patterns.get('¿Qué comandos tienes disponibles?', 0) + 1
            elif any(keyword in content for keyword in ['alta', 'crear', 'nuevo']) and any(keyword in content for keyword in ['jefe', 'equipo', 'usuario']):
                question_patterns['¿Cómo dar de alta un jefe de equipo?'] = question_patterns.get('¿Cómo dar de alta un jefe de equipo?', 0) + 1
            elif any(keyword in content for keyword in ['hps', 'solicitud', 'habilitación']):
                question_patterns['¿Cómo crear una solicitud HPS?'] = question_patterns.get('¿Cómo crear una solicitud HPS?', 0) + 1
            elif any(keyword in content for keyword in ['estado', 'status', 'progreso']):
                question_patterns['¿Cuál es el estado de mi HPS?'] = question_patterns.get('¿Cuál es el estado de mi HPS?', 0) + 1
            elif any(keyword in content for keyword in ['renovar', 'renovación']):
                question_patterns['¿Cómo renovar una HPS?'] = question_patterns.get('¿Cómo renovar una HPS?', 0) + 1
            elif any(keyword in content for keyword in ['trasladar', 'traslado']):
                question_patterns['¿Cómo trasladar una HPS?'] = question_patterns.get('¿Cómo trasladar una HPS?', 0) + 1
            elif any(keyword in content for keyword in ['ayuda', 'help', 'soporte']):
                question_patterns['¿Necesito ayuda con el sistema?'] = question_patterns.get('¿Necesito ayuda con el sistema?', 0) + 1
            elif len(content) > 10:  # Preguntas generales
                # Usar el contenido completo como pregunta si es suficientemente largo
                question = content.capitalize()
                if not question.endswith('?'):
                    question += '?'
                question_patterns[question] = question_patterns.get(question, 0) + 1
        
        # Ordenar y devolver los más frecuentes
        sorted_questions = sorted(question_patterns.items(), key=lambda x: x[1], reverse=True)
        return [{"topic": question, "count": count} for question, count in sorted_questions[:limit]]
    
    @staticmethod
    def get_agent_performance(db: Session) -> Dict[str, Any]:
        """Obtener métricas de rendimiento del agente IA excluyendo mensajes de bienvenida"""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        
        # Respuestas del agente en las últimas 24h
        agent_messages = db.query(ChatMessage).join(ChatConversation).filter(
            and_(
                ChatMessage.message_type == "assistant",
                ChatMessage.created_at >= last_24h
            )
        ).all()
        
        # Filtrar mensajes de bienvenida
        valid_agent_messages = [
            msg for msg in agent_messages 
            if not ChatMetricsService._is_welcome_message(msg)
        ]
        
        if not valid_agent_messages:
            return {
                "total_responses": 0,
                "avg_response_time_ms": 0,
                "error_rate_percent": 0,
                "success_rate_percent": 100
            }
        
        total_responses = len(valid_agent_messages)
        error_responses = len([m for m in valid_agent_messages if m.is_error])
        
        response_times = [m.response_time_ms for m in valid_agent_messages if m.response_time_ms]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        error_rate = (error_responses / total_responses) * 100
        success_rate = 100 - error_rate
        
        return {
            "total_responses": total_responses,
            "avg_response_time_ms": round(avg_response_time, 2),
            "error_rate_percent": round(error_rate, 2),
            "success_rate_percent": round(success_rate, 2)
        }
    
    @staticmethod
    def save_daily_metrics(db: Session, date: datetime.date) -> ChatMetrics:
        """Guardar métricas diarias en la base de datos"""
        # Calcular métricas para el día específico
        start_datetime = datetime.combine(date, datetime.min.time())
        end_datetime = datetime.combine(date, datetime.max.time())
        
        conversations = db.query(ChatConversation).filter(
            and_(
                ChatConversation.created_at >= start_datetime,
                ChatConversation.created_at <= end_datetime
            )
        ).all()
        
        messages = db.query(ChatMessage).join(ChatConversation).filter(
            and_(
                ChatMessage.created_at >= start_datetime,
                ChatMessage.created_at <= end_datetime
            )
        ).all()
        
        total_conversations = len(conversations)
        total_messages = len(messages)
        total_tokens = sum(m.tokens_used for m in messages)
        
        response_times = [m.response_time_ms for m in messages if m.response_time_ms and m.message_type == "assistant"]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        error_messages = [m for m in messages if m.is_error]
        error_rate = (len(error_messages) / total_messages * 100) if total_messages > 0 else 0
        
        # Satisfacción eliminada
        avg_satisfaction = 0
        
        # Usuarios activos
        active_users = len(set(c.user_id for c in conversations))
        
        # Crear registro de métricas
        metrics = ChatMetrics(
            date=start_datetime,
            total_conversations=total_conversations,
            total_messages=total_messages,
            total_tokens_used=total_tokens,
            avg_response_time_ms=avg_response_time,
            # Campo de satisfacción eliminado
            error_rate=error_rate,
            active_users=active_users,
            peak_concurrent_users=active_users,  # Simplificado
            system_health_score=ChatMetricsService._calculate_health_score(error_rate, avg_response_time)
        )
        
        db.add(metrics)
        db.commit()
        db.refresh(metrics)
        return metrics
    
    @staticmethod
    def _calculate_health_score(error_rate: float, avg_response_time: float) -> float:
        """Calcular puntuación de salud del sistema (0-100)"""
        # Factores de salud (sin satisfacción)
        error_factor = max(0, 100 - error_rate)  # Menos errores = mejor
        response_factor = max(0, 100 - (avg_response_time / 1000))  # Respuesta más rápida = mejor
        
        # Promedio ponderado (sin factor de satisfacción)
        health_score = (float(error_factor) * 0.6 + float(response_factor) * 0.4)
        return min(100, max(0, health_score))
    
    @staticmethod
    def _is_welcome_message(message: ChatMessage) -> bool:
        """Detecta si un mensaje es de bienvenida basado en patrones específicos"""
        content = message.content.lower()
        
        welcome_patterns = [
            'soy tu asistente de hps',
            'como administrador',
            'puedes gestionar usuarios',
            '¿en qué puedo ayudarte hoy?',
            'asistente de hps',
            'gestionar usuarios, equipos y hps'
        ]
        
        # Contar cuántos patrones coinciden
        pattern_matches = sum(1 for pattern in welcome_patterns if pattern in content)
        
        # Si coincide con al menos 2 patrones, es bienvenida
        return pattern_matches >= 2
