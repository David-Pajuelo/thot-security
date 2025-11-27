"""
Servicio para gestión de tokens HPS seguros
"""
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.models.hps_token import HPSToken
from src.models.user import User
from src.hps.token_schemas import HPSTokenCreate, HPSTokenResponse, HPSTokenInfo


class HPSTokenService:
    """Servicio para gestión de tokens HPS seguros"""

    @staticmethod
    def create_token(
        db: Session,
        token_data: HPSTokenCreate,
        requested_by_id: str,
        base_url: str = "http://localhost:3000"
    ) -> HPSTokenResponse:
        """
        Crear un token seguro para formulario HPS
        
        Args:
            db: Sesión de base de datos
            token_data: Datos del token a crear
            requested_by_id: ID del usuario que solicita el token
            base_url: URL base del frontend
            
        Returns:
            HPSTokenResponse con el token y URL generada
        """
        try:
            # Generar token único y seguro
            token_value = secrets.token_urlsafe(32)
            
            # Calcular fecha de expiración
            expires_at = datetime.utcnow() + timedelta(hours=token_data.hours_valid)
            
            # Crear registro del token
            hps_token = HPSToken(
                token=token_value,
                email=token_data.email,
                purpose=token_data.purpose,
                requested_by=uuid.UUID(requested_by_id),
                expires_at=expires_at,
                is_used=False
            )
            
            db.add(hps_token)
            db.commit()
            db.refresh(hps_token)
            
            # Construir URL del formulario
            form_url = f"{base_url}/hps-form?token={token_value}&email={token_data.email}"
            
            return HPSTokenResponse(
                token=token_value,
                email=token_data.email,
                url=form_url,
                expires_at=expires_at
            )
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_token_info(db: Session, token: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información de un token sin marcarlo como usado
        
        Args:
            db: Sesión de base de datos
            token: Token a validar
            
        Returns:
            Diccionario con información del token o None si no existe
        """
        try:
            # Buscar token en la base de datos
            hps_token = db.query(HPSToken).filter(
                and_(
                    HPSToken.token == token,
                    HPSToken.expires_at > datetime.utcnow(),
                    HPSToken.is_used == False
                )
            ).first()
            
            if not hps_token:
                return None
            
            # Obtener información del usuario que solicitó el token
            requested_by_user = db.query(User).filter(User.id == hps_token.requested_by).first()
            requested_by_name = f"{requested_by_user.first_name} {requested_by_user.last_name}".strip() if requested_by_user else "Usuario desconocido"
            
            return {
                "is_valid": True,
                "email": hps_token.email,
                "requested_by": hps_token.requested_by,  # ID del usuario que creó el token
                "requested_by_name": requested_by_name,
                "purpose": hps_token.purpose,
                "expires_at": hps_token.expires_at
            }
            
        except Exception as e:
            return None

    @staticmethod
    def validate_and_use_token(db: Session, token: str, email: str) -> Optional[Dict[str, Any]]:
        """
        Validar un token y marcarlo como usado
        
        Args:
            db: Sesión de base de datos
            token: Token a validar
            email: Email asociado al token
            
        Returns:
            Diccionario con información del token o None si no es válido
        """
        try:
            # Buscar token válido
            hps_token = db.query(HPSToken).filter(
                and_(
                    HPSToken.token == token,
                    HPSToken.email == email,
                    HPSToken.expires_at > datetime.utcnow(),
                    HPSToken.is_used == False
                )
            ).first()
            
            if not hps_token:
                return None
            
            # Marcar token como usado
            hps_token.is_used = True
            hps_token.used_at = datetime.utcnow()
            db.commit()
            
            # Obtener información del usuario que solicitó el token
            requested_by_user = db.query(User).filter(User.id == hps_token.requested_by).first()
            requested_by_name = f"{requested_by_user.first_name} {requested_by_user.last_name}".strip() if requested_by_user else "Usuario desconocido"
            
            return {
                "is_valid": True,
                "email": hps_token.email,
                "requested_by_name": requested_by_name,
                "purpose": hps_token.purpose,
                "expires_at": hps_token.expires_at
            }
            
        except Exception as e:
            db.rollback()
            return None

    @staticmethod
    def cleanup_expired_tokens(db: Session) -> int:
        """
        Limpiar tokens expirados de la base de datos
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            Número de tokens eliminados
        """
        try:
            # Eliminar tokens expirados
            expired_tokens = db.query(HPSToken).filter(
                HPSToken.expires_at <= datetime.utcnow()
            ).all()
            
            count = len(expired_tokens)
            
            for token in expired_tokens:
                db.delete(token)
            
            db.commit()
            return count
            
        except Exception as e:
            db.rollback()
            return 0

    @staticmethod
    def get_user_tokens(db: Session, user_id: str) -> list:
        """
        Obtener todos los tokens generados por un usuario
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            
        Returns:
            Lista de tokens generados por el usuario
        """
        try:
            tokens = db.query(HPSToken).filter(
                HPSToken.requested_by == uuid.UUID(user_id)
            ).order_by(HPSToken.created_at.desc()).all()
            
            return tokens
            
        except Exception as e:
            return []

    @staticmethod
    def delete_tokens_by_user_id(
        db: Session,
        user_id: uuid.UUID
    ) -> int:
        """
        Eliminar todos los tokens HPS generados por un usuario específico
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario cuyos tokens se van a eliminar
            
        Returns:
            Número de tokens eliminados
        """
        try:
            # Buscar todos los tokens del usuario
            tokens = db.query(HPSToken).filter(
                HPSToken.requested_by == user_id
            ).all()
            
            count = len(tokens)
            
            # Eliminar todos los tokens
            for token in tokens:
                db.delete(token)
            
            db.commit()
            return count
            
        except Exception as e:
            db.rollback()
            raise e



