"""
Esquemas Pydantic para tokens HPS
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class HPSTokenCreate(BaseModel):
    """Esquema para crear un token HPS"""
    email: EmailStr = Field(..., description="Email del destinatario")
    purpose: Optional[str] = Field(None, max_length=500, description="Motivo de la solicitud")
    hours_valid: Optional[int] = Field(72, ge=1, le=168, description="Horas de validez (1-168h)")


class HPSTokenResponse(BaseModel):
    """Esquema de respuesta para tokens HPS"""
    token: str = Field(..., description="Token seguro")
    email: str = Field(..., description="Email del destinatario")
    url: str = Field(..., description="URL completa del formulario")
    expires_at: datetime = Field(..., description="Fecha de expiración")
    
    class Config:
        from_attributes = True


class HPSTokenValidation(BaseModel):
    """Esquema para validar un token"""
    token: str = Field(..., description="Token a validar")
    email: Optional[str] = Field(None, description="Email asociado (verificación adicional)")


class HPSTokenInfo(BaseModel):
    """Información básica de un token"""
    is_valid: bool = Field(..., description="Si el token es válido")
    email: Optional[str] = Field(None, description="Email asociado")
    requested_by_name: Optional[str] = Field(None, description="Nombre de quien solicitó")
    purpose: Optional[str] = Field(None, description="Motivo de la solicitud")
    expires_at: Optional[datetime] = Field(None, description="Fecha de expiración")
    
    class Config:
        from_attributes = True

