"""
Servicio de integración para logging automático de conversaciones del chat
"""
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import httpx
import os

logger = logging.getLogger(__name__)

class ChatIntegrationService:
    """Servicio para integrar el agente IA con el sistema de logging del backend"""
    
    def __init__(self):
        # Backend ahora es Django (cryptotrace-backend en puerto 8080)
        self.backend_url = os.getenv("BACKEND_URL", "http://cryptotrace-backend:8080")
        self.api_base = f"{self.backend_url}/api/hps/chat"  # Django usa /api/hps/chat
        self.session_id = None
        self.conversation_id = None
        
    async def find_active_conversation(
        self,
        user_id: str,
        auth_token: str = None
    ) -> Optional[str]:
        """Buscar una conversación activa existente del usuario (solo status='active')"""
        try:
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            url = f"{self.api_base}/conversations/active/"
            params = {"user_id": user_id}
            
            logger.info(f"🔍 Buscando conversación activa para usuario {user_id}")
            logger.info(f"📡 Headers: {headers}")
            logger.info(f"🌐 URL: {url}")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    conversation_id = data.get("conversation_id") or data.get("id")
                    if conversation_id:
                        logger.info(f"✅ Conversación activa encontrada: {conversation_id}")
                        return conversation_id
                    else:
                        logger.info("ℹ️ No hay conversaciones activas")
                        return None
                else:
                    logger.warning(f"⚠️ Error buscando conversación activa: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error buscando conversación activa: {e}")
            return None

    async def start_conversation(
        self, 
        user_id: str, 
        session_id: str,
        title: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> Optional[str]:
        """Iniciar una nueva conversación en el backend"""
        try:
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            logger.info(f"🔍 Iniciando conversación - user_id: {user_id}, session_id: {session_id}, title: {title}")
            logger.info(f"🔍 Headers: {headers}")
            logger.info(f"🔍 URL: {self.api_base}/conversations/")
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/conversations/",
                    json={
                        "user_id": user_id,
                        "session_id": session_id,
                        "title": title
                    },
                    headers=headers,
                    timeout=10.0
                )
                
                logger.info(f"🔍 Respuesta del servidor: {response.status_code}")
                logger.info(f"🔍 Contenido de la respuesta: {response.text}")
                
                if response.status_code in [200, 201]:  # Django devuelve 201 para creación
                    data = response.json()
                    self.conversation_id = data.get("id")
                    self.session_id = session_id
                    logger.info(f"✅ Conversación iniciada: {self.conversation_id}")
                    return self.conversation_id
                else:
                    logger.error(f"❌ Error iniciando conversación: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error conectando con backend para iniciar conversación: {e}")
            return None
    
    async def log_user_message(
        self,
        message: str,
        tokens_used: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None
    ) -> bool:
        """Registrar mensaje del usuario"""
        if not self.conversation_id:
            logger.warning("⚠️ No hay conversación activa para registrar mensaje del usuario")
            return False
            
        try:
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/messages/",
                    json={
                        "conversation_id": self.conversation_id,
                        "message_type": "user",
                        "content": message,
                        "tokens_used": tokens_used,
                        "message_metadata": metadata
                    },
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"✅ Mensaje del usuario registrado")
                    return True
                else:
                    logger.error(f"❌ Error registrando mensaje del usuario: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error registrando mensaje del usuario: {e}")
            return False
    
    async def log_assistant_message(
        self,
        message: str,
        tokens_used: int = 0,
        response_time_ms: Optional[int] = None,
        is_error: bool = False,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None
    ) -> bool:
        """Registrar mensaje del asistente IA"""
        if not self.conversation_id:
            logger.warning("⚠️ No hay conversación activa para registrar mensaje del asistente")
            return False
            
        try:
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/messages/",
                    json={
                        "conversation_id": self.conversation_id,
                        "message_type": "assistant",
                        "content": message,
                        "tokens_used": tokens_used,
                        "response_time_ms": response_time_ms,
                        "is_error": is_error,
                        "error_message": error_message,
                        "message_metadata": metadata
                    },
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"✅ Mensaje del asistente registrado")
                    return True
                else:
                    logger.error(f"❌ Error registrando mensaje del asistente: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error registrando mensaje del asistente: {e}")
            return False
    
    async def complete_conversation(
        self,
        satisfaction_rating: Optional[int] = None,
        satisfaction_feedback: Optional[str] = None
    ) -> bool:
        """Completar la conversación actual"""
        if not self.conversation_id:
            logger.warning("⚠️ No hay conversación activa para completar")
            return False
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/conversations/{self.conversation_id}/complete/",
                    params={
                        "satisfaction_rating": satisfaction_rating,
                        "satisfaction_feedback": satisfaction_feedback
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Conversación completada: {self.conversation_id}")
                    self.conversation_id = None
                    self.session_id = None
                    return True
                else:
                    logger.error(f"❌ Error completando conversación: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error completando conversación: {e}")
            return False
    
    async def update_conversation_title(
        self,
        conversation_id: str,
        title: str,
        auth_token: Optional[str] = None
    ) -> bool:
        """Actualizar el título de una conversación"""
        try:
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
                
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.api_base}/conversations/{conversation_id}/",
                    json={"title": title},
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Título de conversación actualizado: {title}")
                    return True
                else:
                    logger.error(f"❌ Error actualizando título: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error conectando con backend para actualizar título: {e}")
            return False

    async def abandon_conversation(self) -> bool:
        """Marcar la conversación como abandonada"""
        if not self.conversation_id:
            logger.warning("⚠️ No hay conversación activa para abandonar")
            return False
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/conversations/{self.conversation_id}/abandon/",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Conversación abandonada: {self.conversation_id}")
                    self.conversation_id = None
                    self.session_id = None
                    return True
                else:
                    logger.error(f"❌ Error abandonando conversación: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error abandonando conversación: {e}")
            return False
    
    def get_conversation_id(self) -> Optional[str]:
        """Obtener ID de la conversación actual"""
        return self.conversation_id
    
    def is_conversation_active(self) -> bool:
        """Verificar si hay una conversación activa"""
        return self.conversation_id is not None


# Instancia global del servicio
chat_integration = ChatIntegrationService()
