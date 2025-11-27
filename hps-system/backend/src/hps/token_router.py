"""
Router para gestión de tokens HPS seguros
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from src.database.database import get_db
from src.auth.dependencies import get_current_user
from src.models.user import User
from .token_schemas import HPSTokenCreate, HPSTokenResponse, HPSTokenInfo
from .token_service import HPSTokenService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tokens", tags=["HPS Tokens"])


@router.post("/", response_model=HPSTokenResponse, status_code=status.HTTP_201_CREATED)
async def create_hps_token(
    token_data: HPSTokenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crear un token seguro para formulario HPS
    
    Permite a leaders/admins generar URLs seguras para que usuarios
    no autenticados completen formularios HPS.
    """
    try:
        # Verificar permisos (admin, team_leader o team_lead)
        if current_user.role.name not in ["admin", "team_leader", "team_lead"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo administradores y líderes de equipo pueden crear tokens HPS"
            )
        
        logger.info(f"Creando token HPS por usuario {current_user.id} para {token_data.email}")
        
        # Crear token
        token_response = HPSTokenService.create_token(
            db=db,
            token_data=token_data,
            requested_by_id=str(current_user.id),
            base_url="http://localhost:3000"
        )
        
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear token HPS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al crear el token HPS"
        )


@router.get("/validate", response_model=HPSTokenInfo)
async def validate_hps_token(
    token: str = Query(..., description="Token a validar"),
    email: Optional[str] = Query(None, description="Email asociado (validación adicional)"),
    db: Session = Depends(get_db)
):
    """
    Validar un token HPS sin marcarlo como usado
    
    Endpoint público para verificar la validez de un token
    antes de mostrar el formulario.
    """
    try:
        logger.info(f"Validando token HPS: {token[:20]}...")
        
        # Obtener información del token
        token_info = HPSTokenService.get_token_info(db, token)
        
        if not token_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token no encontrado"
            )
        
        # Validación adicional de email si se proporciona
        if email and token_info["email"] != email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email no coincide con el token"
            )
        
        return HPSTokenInfo(**token_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al validar token HPS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al validar el token"
        )
