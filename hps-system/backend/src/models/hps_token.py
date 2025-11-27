"""
Modelo para tokens seguros de formularios HPS
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta, timezone
import uuid
import secrets

from src.database.database import Base


class HPSToken(Base):
    """
    Modelo para tokens seguros de formularios HPS
    
    Permite que usuarios no autenticados accedan a formularios HPS específicos
    de forma segura y con trazabilidad completa.
    """
    __tablename__ = "hps_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Token seguro (UUID + secreto adicional)
    token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Email del usuario destinatario
    email = Column(String(255), nullable=False)
    
    # Usuario que solicitó el HPS (leader/admin)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Datos de contexto
    purpose = Column(String(500), nullable=True)  # Motivo de la solicitud
    
    # Control de acceso
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Control de expiración
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Metadatos
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    requested_by_user = relationship("User", back_populates="requested_hps_tokens")
    
    @classmethod
    def generate_secure_token(cls):
        """Generar token seguro único"""
        return f"{uuid.uuid4().hex}{secrets.token_urlsafe(32)}"
    
    @classmethod
    def create_token(cls, email: str, requested_by_id: str, purpose: str = None, hours_valid: int = 72):
        """
        Crear un nuevo token HPS
        
        Args:
            email: Email del destinatario
            requested_by_id: ID del usuario que solicita
            purpose: Motivo de la solicitud
            hours_valid: Horas de validez (por defecto 72h)
        """
        return cls(
            token=cls.generate_secure_token(),
            email=email,
            requested_by=requested_by_id,
            purpose=purpose,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=hours_valid)
        )
    
    @property
    def is_expired(self):
        """Verificar si el token ha expirado"""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self):
        """Verificar si el token es válido (no usado y no expirado)"""
        return not self.is_used and not self.is_expired
    
    def mark_as_used(self):
        """Marcar token como usado"""
        self.is_used = True
        self.used_at = datetime.now(timezone.utc)
