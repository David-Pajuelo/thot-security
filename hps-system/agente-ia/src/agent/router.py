"""
Router principal del Agente IA Conversacional
"""
import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional

from .openai_client import OpenAIClient
from .command_processor import CommandProcessor

logger = logging.getLogger(__name__)

# Esquemas para el API
class ChatRequest(BaseModel):
    message: str
    user_id: str
    user_context: Dict[str, Any]
    conversation_history: Optional[list] = []

class ChatResponse(BaseModel):
    response: str
    type: str
    data: Optional[Dict[str, Any]] = None
    suggestions: Optional[list] = []

# Router
router = APIRouter(prefix="/agent", tags=["agent"])

# Instancias globales
openai_client = None
command_processor = None

@router.on_event("startup")
async def startup_agent():
    """Inicializar el agente IA al startup"""
    global openai_client, command_processor
    
    try:
        logger.info("🤖 Inicializando Agente IA...")
        
        # Inicializar OpenAI
        openai_client = OpenAIClient()
        await openai_client.test_connection()
        
        # Inicializar procesador de comandos
        command_processor = CommandProcessor()
        
        logger.info("✅ Agente IA inicializado correctamente")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando Agente IA: {e}")
        raise e

@router.post("/chat", response_model=ChatResponse)
async def process_chat_message(request: ChatRequest):
    """Procesar mensaje de chat y generar respuesta del agente IA"""
    
    global openai_client, command_processor
    
    if not openai_client or not command_processor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agente IA no está disponible"
        )
    
    try:
        logger.info(f"Procesando mensaje de usuario {request.user_id}: {request.message}")
        
        # 1. Procesar mensaje con OpenAI
        ai_response = await openai_client.process_message(
            message=request.message,
            user_context=request.user_context
        )
        
        logger.info(f"Respuesta de OpenAI: {ai_response.get('tipo', 'unknown')}")
        
        # 2. Si es un comando, ejecutarlo
        if ai_response.get("tipo") == "comando" and ai_response.get("requiere_api", False):
            final_response = await command_processor.execute_command(ai_response, request.user_context)
        else:
            final_response = ai_response
        
        # 3. Generar sugerencias basadas en el rol del usuario
        suggestions = generate_suggestions(request.user_context.get("role", "member"))
        
        # 4. Formatear respuesta final
        response_message = final_response.get("mensaje", "Lo siento, no pude procesar tu solicitud.")
        response_type = final_response.get("tipo", "conversacion")
        response_data = final_response.get("data", {})
        
        return ChatResponse(
            response=response_message,
            type=response_type,
            data=response_data,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Error procesando chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno procesando el mensaje"
        )

@router.get("/health")
async def health_check():
    """Verificar estado del agente IA"""
    
    global openai_client, command_processor
    
    status_info = {
        "agent_status": "healthy" if openai_client and command_processor else "unhealthy",
        "openai_connection": False,
        "command_processor": bool(command_processor)
    }
    
    # Verificar conexión OpenAI
    if openai_client:
        try:
            status_info["openai_connection"] = await openai_client.test_connection()
        except:
            status_info["openai_connection"] = False
    
    return status_info

@router.get("/capabilities/{role}")
async def get_capabilities(role: str):
    """Obtener capacidades disponibles según el rol del usuario"""
    
    capabilities = {
        "admin": [
            "Dar de alta jefes de equipo",
            "Solicitar HPS para cualquier usuario",
            "Consultar estado de cualquier HPS",
            "Ver estadísticas globales del sistema",
            "Gestionar renovaciones y traspasos",
            "Acceso completo a todos los equipos"
        ],
        "team_lead": [
            "Solicitar HPS para miembros de su equipo",
            "Consultar estado HPS de su equipo",
            "Ver estadísticas de su equipo",
            "Gestionar renovaciones de su equipo",
            "Iniciar traspasos de su equipo"
        ],
        "team_leader": [
            "Solicitar HPS para miembros de su equipo",
            "Consultar estado HPS de su equipo",
            "Ver estadísticas de su equipo",
            "Gestionar renovaciones de su equipo",
            "Iniciar traspasos de su equipo"
        ],
        "member": [
            "Consultar estado de su propia HPS",
            "Ver fecha de vencimiento de su HPS",
            "Consultar historial personal",
            "Solicitar ayuda sobre el proceso HPS"
        ]
    }
    
    return {
        "role": role,
        "capabilities": capabilities.get(role.lower(), capabilities["member"])
    }

def generate_suggestions(user_role: str) -> list:
    """Generar sugerencias contextuales según el rol del usuario"""
    
    suggestions_map = {
        "admin": [
            "¿Qué comandos puedes ejecutar?",
            "Dame un resumen de todas las HPS",
            "Dar de alta un jefe de equipo",
            "Solicitar HPS para un usuario",
            "Listar todos los equipos"
        ],
        "team_lead": [
            "¿Qué comandos puedes ejecutar?",
            "Estado de mi equipo",
            "Solicitar HPS para un miembro",
            "¿Hay HPS pendientes en mi equipo?",
            "Renovar HPS de un miembro"
        ],
        "team_leader": [
            "¿Qué comandos puedes ejecutar?",
            "Estado de mi equipo", 
            "Solicitar HPS para un miembro",
            "¿Hay HPS pendientes en mi equipo?",
            "Renovar HPS de un miembro"
        ],
        "member": [
            "Información sobre HPS",
            "¿Cuál es el estado de mi HPS?"
        ]
    }
    
    return suggestions_map.get(user_role.lower(), suggestions_map["member"])








