from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import os
import logging
from datetime import datetime, timedelta

# Importar módulos locales
from .auth import AuthManager, get_current_user, get_current_admin_user, get_current_team_lead_user
from .models import (
    UserLogin, UserLoginResponse, UserCreate, UserResponse, 
    SuccessResponse, ErrorResponse, TokenData
)
from .agent.router import router as agent_router
from .websocket.router import router as websocket_router

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HPS AI Agent", 
    version="1.0.0",
    description="Agente conversacional para el Sistema HPS"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(agent_router, prefix="/api/v1")
app.include_router(websocket_router)

# =============================================================================
# ENDPOINTS DE AUTENTICACIÓN
# =============================================================================

@app.post("/auth/login", response_model=UserLoginResponse)
async def login(user_credentials: UserLogin):
    """Endpoint para autenticación de usuarios"""
    try:
        # Autenticar usuario
        user = AuthManager.authenticate_user(user_credentials.email, user_credentials.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        
        # Crear token JWT
        access_token_expires = timedelta(minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "480")))
        access_token = AuthManager.create_access_token(
            data={"sub": str(user["id"]), "email": user["email"], "role": user["role_name"]},
            expires_delta=access_token_expires
        )
        
        # Crear sesión en base de datos
        AuthManager.create_user_session(
            user_id=str(user["id"]),
            token_hash=access_token[-20:],  # Hash simplificado para demo
            ip_address=None,  # Se puede obtener del request
            user_agent=None   # Se puede obtener del request
        )
        
        # Actualizar último login
        # TODO: Implementar actualización de last_login
        
        return UserLoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "480")),
            user={
                "id": user["id"],
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "role_name": user["role_name"],
                "permissions": user.get("permissions", {})
            }
        )
        
    except Exception as e:
        logger.error(f"Error en login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@app.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Endpoint para cerrar sesión"""
    try:
        # TODO: Implementar invalidación de token
        # Por ahora solo retornamos éxito
        return SuccessResponse(
            message="Sesión cerrada exitosamente"
        )
    except Exception as e:
        logger.error(f"Error en logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Obtener información del usuario actual"""
    return current_user

# =============================================================================
# ENDPOINTS DE GESTIÓN DE USUARIOS (Solo Admin)
# =============================================================================

@app.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate, 
    current_admin: dict = Depends(get_current_admin_user)
):
    """Crear nuevo usuario (solo administradores)"""
    try:
        # TODO: Implementar creación de usuario
        # Por ahora retornamos mock
        return UserResponse(
            id="mock-id",
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role_name="member",
            permissions={},
            team_id=None,
            is_active=True,
            email_verified=False,
            last_login=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error creando usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

# =============================================================================
# ENDPOINTS DE SALUD Y ESTADO
# =============================================================================

@app.get("/")
async def root():
    return {
        "message": "🤖 HPS AI Agent is running!",
        "version": "1.0.0",
        "features": [
            "OpenAI GPT-4o-mini Integration",
            "Command Processing",
            "Role-based Permissions",
            "HPS System Integration",
            "Conversational AI"
        ],
        "endpoints": {
            "chat": "/api/v1/agent/chat",
            "health": "/api/v1/agent/health",
            "capabilities": "/api/v1/agent/capabilities/{role}"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "hps-ai-agent"}

@app.get("/health/db")
async def health_check_db():
    """Verificar salud de la base de datos"""
    try:
        # TODO: Implementar verificación real de BD
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Error verificando BD: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

# =============================================================================
# ENDPOINTS DE LIMPIEZA (Solo Admin)
# =============================================================================

@app.post("/admin/cleanup-sessions")
async def cleanup_expired_sessions(current_admin: dict = Depends(get_current_admin_user)):
    """Limpiar sesiones expiradas (solo administradores)"""
    try:
        deleted_count = AuthManager.cleanup_expired_sessions()
        return SuccessResponse(
            message=f"Sesiones expiradas limpiadas exitosamente",
            data={"deleted_sessions": deleted_count}
        )
    except Exception as e:
        logger.error(f"Error limpiando sesiones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
