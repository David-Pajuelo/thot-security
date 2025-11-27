# Router de autenticación para HPS Backend
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime
from src.database.database import get_db
from src.auth.schemas import UserLogin, Token, UserResponse, PasswordChange
from src.auth.service import AuthService
from src.auth.dependencies import get_current_user
from src.models.user import User
from src.models.chat_conversation import ChatConversation
from typing import Dict

router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
    responses={404: {"description": "No encontrado"}}
)

@router.post("/login", response_model=Token, summary="Iniciar sesión")
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Iniciar sesión con username y password.
    
    Retorna un token JWT que debe ser usado en el header Authorization:
    `Authorization: Bearer <token>`
    """
    auth_service = AuthService(db)
    return auth_service.login(login_data)

@router.post("/logout", summary="Cerrar sesión")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cerrar sesión del usuario actual.
    
    Nota: En JWT no hay logout real del lado del servidor.
    El cliente debe descartar el token.
    Además, se cierra automáticamente la conversación activa del chat.
    """
    try:
        # Cerrar conversación activa del usuario
        from src.chat.logging_service import ChatLoggingService
        
        # Buscar conversación activa del usuario
        active_conversation = db.query(ChatConversation).filter(
            ChatConversation.user_id == str(current_user.id),
            ChatConversation.status == "active"
        ).first()
        
        if active_conversation:
            # Archivar conversación (se suma al histórico)
            active_conversation.status = "archived"
            active_conversation.closed_at = datetime.now()
            active_conversation.updated_at = datetime.now()
            db.commit()
            
            print(f"✅ Conversación {active_conversation.id} archivada en histórico - usuario {current_user.email}")
        else:
            print(f"ℹ️ No hay conversación activa para usuario {current_user.email}")
            
    except Exception as e:
        print(f"⚠️ Error cerrando conversación para usuario {current_user.email}: {e}")
        # No fallar el logout por error en el chat
    
    # En una implementación real, podrías agregar el token a una blacklist
    # Por ahora, simplemente retornamos un mensaje
    return {
        "message": "Sesión cerrada exitosamente",
        "detail": "El token debe ser descartado del cliente. Conversación de chat cerrada."
    }

@router.get("/me", response_model=UserResponse, summary="Obtener usuario actual")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Obtener información del usuario autenticado actualmente.
    """
    return UserResponse.from_user(current_user)

@router.post("/change-password", summary="Cambiar contraseña")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cambiar la contraseña del usuario actual.
    """
    auth_service = AuthService(db)
    auth_service.change_password(current_user, password_data)
    
    return {
        "message": "Contraseña cambiada exitosamente",
        "detail": "La nueva contraseña ya está activa"
    }

@router.post("/verify-token", summary="Verificar token")
async def verify_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verificar si el token actual es válido.
    
    Este endpoint es útil para validar tokens en el frontend.
    También actualiza el last_login si han pasado más de 5 minutos.
    """
    from datetime import datetime, timedelta
    
    # Actualizar last_login solo si han pasado más de 5 minutos
    # para evitar actualizaciones excesivas
    if (not current_user.last_login or 
        datetime.now() - current_user.last_login.replace(tzinfo=None) > timedelta(minutes=5)):
        current_user.last_login = datetime.now()
        db.commit()
    
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.name,
        "message": "Token válido"
    }

@router.get("/health", summary="Health check de autenticación")
async def auth_health():
    """
    Health check específico para el sistema de autenticación.
    """
    return {
        "status": "healthy",
        "service": "Authentication System",
        "version": "1.0.0",
        "features": [
            "JWT Authentication",
            "Role-based Access Control",
            "Password Hashing",
            "Token Verification"
        ]
    }
