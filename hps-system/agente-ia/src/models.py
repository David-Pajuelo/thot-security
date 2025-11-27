"""
Modelos Pydantic para el Sistema HPS
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# =============================================================================
# ENUMS
# =============================================================================

class UserRole(str, Enum):
    """Roles de usuario disponibles"""
    ADMIN = "admin"
    TEAM_LEAD = "team_lead"
    MEMBER = "member"

class HPSStatus(str, Enum):
    """Estados de solicitud HPS"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class HPSRequestType(str, Enum):
    """Tipos de solicitud HPS"""
    NEW = "new"
    RENEWAL = "renewal"
    TRANSFER = "transfer"

# =============================================================================
# MODELOS DE AUTENTICACIÓN
# =============================================================================

class UserLogin(BaseModel):
    """Modelo para login de usuario"""
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=6, description="Contraseña del usuario")

class UserLoginResponse(BaseModel):
    """Respuesta del login"""
    access_token: str = Field(..., description="Token JWT de acceso")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Tiempo de expiración en minutos")
    user: dict = Field(..., description="Datos del usuario")

class TokenData(BaseModel):
    """Datos del token JWT"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None

# =============================================================================
# MODELOS DE USUARIO
# =============================================================================

class UserBase(BaseModel):
    """Modelo base para usuarios"""
    email: EmailStr = Field(..., description="Email del usuario")
    first_name: str = Field(..., min_length=2, max_length=100, description="Nombre del usuario")
    last_name: str = Field(..., min_length=2, max_length=100, description="Apellido del usuario")
    role_id: int = Field(..., description="ID del rol del usuario")
    team_id: Optional[str] = Field(None, description="ID del equipo del usuario")

class UserCreate(UserBase):
    """Modelo para crear usuario"""
    password: str = Field(..., min_length=6, description="Contraseña del usuario")

class UserUpdate(BaseModel):
    """Modelo para actualizar usuario"""
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role_id: Optional[int] = None
    team_id: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    """Modelo de respuesta para usuarios"""
    id: str = Field(..., description="ID único del usuario")
    email: str = Field(..., description="Email del usuario")
    first_name: str = Field(..., description="Nombre del usuario")
    last_name: str = Field(..., description="Apellido del usuario")
    role_name: str = Field(..., description="Nombre del rol")
    permissions: dict = Field(..., description="Permisos del rol")
    team_id: Optional[str] = Field(None, description="ID del equipo")
    is_active: bool = Field(..., description="Estado activo del usuario")
    email_verified: bool = Field(..., description="Email verificado")
    last_login: Optional[datetime] = Field(None, description="Último login")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de última actualización")

    class Config:
        from_attributes = True

# =============================================================================
# MODELOS DE EQUIPO
# =============================================================================

class TeamBase(BaseModel):
    """Modelo base para equipos"""
    name: str = Field(..., min_length=2, max_length=100, description="Nombre del equipo")
    description: Optional[str] = Field(None, description="Descripción del equipo")

class TeamCreate(TeamBase):
    """Modelo para crear equipo"""
    team_lead_id: Optional[str] = Field(None, description="ID del jefe del equipo")

class TeamUpdate(BaseModel):
    """Modelo para actualizar equipo"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    team_lead_id: Optional[str] = None
    is_active: Optional[bool] = None

class TeamResponse(TeamBase):
    """Modelo de respuesta para equipos"""
    id: str = Field(..., description="ID único del equipo")
    team_lead_id: Optional[str] = Field(None, description="ID del jefe del equipo")
    is_active: bool = Field(..., description="Estado activo del equipo")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de última actualización")

    class Config:
        from_attributes = True

# =============================================================================
# MODELOS DE HPS
# =============================================================================

class HPSRequestBase(BaseModel):
    """Modelo base para solicitudes HPS"""
    user_id: str = Field(..., description="ID del usuario solicitante")
    request_type: HPSRequestType = Field(..., description="Tipo de solicitud")
    
    # Datos personales del formulario
    document_type: str = Field(..., description="Tipo de documento")
    document_number: str = Field(..., description="Número de documento")
    birth_date: datetime = Field(..., description="Fecha de nacimiento")
    first_name: str = Field(..., min_length=2, max_length=100, description="Nombre")
    first_last_name: str = Field(..., min_length=2, max_length=100, description="Primer apellido")
    second_last_name: Optional[str] = Field(None, max_length=100, description="Segundo apellido")
    nationality: str = Field(..., description="Nacionalidad")
    birth_place: str = Field(..., description="Lugar de nacimiento")
    email: EmailStr = Field(..., description="Email de contacto")
    phone: str = Field(..., description="Teléfono de contacto")

class HPSRequestCreate(HPSRequestBase):
    """Modelo para crear solicitud HPS"""
    submitted_by: str = Field(..., description="ID del usuario que envía la solicitud")
    notes: Optional[str] = Field(None, description="Notas adicionales")

class HPSRequestUpdate(BaseModel):
    """Modelo para actualizar solicitud HPS"""
    status: Optional[HPSStatus] = None
    approved_by: Optional[str] = Field(None, description="ID del usuario que aprueba")
    approved_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None

class HPSRequestResponse(HPSRequestBase):
    """Modelo de respuesta para solicitudes HPS"""
    id: str = Field(..., description="ID único de la solicitud")
    status: HPSStatus = Field(..., description="Estado de la solicitud")
    submitted_by: str = Field(..., description="ID del usuario que envía")
    submitted_at: datetime = Field(..., description="Fecha de envío")
    approved_by: Optional[str] = Field(None, description="ID del usuario que aprueba")
    approved_at: Optional[datetime] = Field(None, description="Fecha de aprobación")
    expires_at: Optional[datetime] = Field(None, description="Fecha de expiración")
    notes: Optional[str] = Field(None, description="Notas adicionales")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de última actualización")

    class Config:
        from_attributes = True

# =============================================================================
# MODELOS DE AUDITORÍA
# =============================================================================

class AuditLogBase(BaseModel):
    """Modelo base para logs de auditoría"""
    user_id: Optional[str] = Field(None, description="ID del usuario que realiza la acción")
    action: str = Field(..., description="Acción realizada")
    table_name: Optional[str] = Field(None, description="Nombre de la tabla afectada")
    record_id: Optional[str] = Field(None, description="ID del registro afectado")
    old_values: Optional[dict] = Field(None, description="Valores anteriores")
    new_values: Optional[dict] = Field(None, description="Valores nuevos")
    ip_address: Optional[str] = Field(None, description="Dirección IP del usuario")
    user_agent: Optional[str] = Field(None, description="User agent del navegador")

class AuditLogResponse(AuditLogBase):
    """Modelo de respuesta para logs de auditoría"""
    id: str = Field(..., description="ID único del log")
    created_at: datetime = Field(..., description="Fecha de creación")

    class Config:
        from_attributes = True

# =============================================================================
# MODELOS DE RESPUESTA GENERAL
# =============================================================================

class SuccessResponse(BaseModel):
    """Respuesta de éxito genérica"""
    success: bool = Field(default=True, description="Indicador de éxito")
    message: str = Field(..., description="Mensaje de respuesta")
    data: Optional[dict] = Field(None, description="Datos adicionales")

class ErrorResponse(BaseModel):
    """Respuesta de error genérica"""
    success: bool = Field(default=False, description="Indicador de éxito")
    error: str = Field(..., description="Descripción del error")
    details: Optional[dict] = Field(None, description="Detalles adicionales del error")

class PaginatedResponse(BaseModel):
    """Respuesta paginada genérica"""
    success: bool = Field(default=True, description="Indicador de éxito")
    data: List[dict] = Field(..., description="Lista de elementos")
    total: int = Field(..., description="Total de elementos")
    page: int = Field(..., description="Página actual")
    size: int = Field(..., description="Tamaño de página")
    pages: int = Field(..., description="Total de páginas")
