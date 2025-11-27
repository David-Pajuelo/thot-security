# Esquemas específicos para API de usuarios
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Union
from src.auth.schemas import UserRole, UserResponse
from datetime import datetime, date

class UserDetailResponse(UserResponse):
    """Respuesta detallada de usuario con información adicional"""
    last_login: Optional[datetime] = None
    login_count: int = 0
    team_name: Optional[str] = None
    hps_status: Optional[str] = None  # "active", "pending", "expired", "none"
    hps_expires_at: Optional[date] = None
    pending_hps_requests: int = 0
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_user(cls, user):
        """Crear UserDetailResponse desde modelo User"""
        base_data = UserResponse.from_user(user)
        data = base_data.dict()
        
        # Obtener información de HPS
        hps_status = "none"
        hps_expires_at = None
        pending_requests = 0
        
        if user.hps_requests:
            # Buscar HPS activa más reciente
            active_hps = None
            for hps in user.hps_requests:
                if hps.status == "approved" and (not hps.expires_at or hps.expires_at > datetime.now().date()):
                    if not active_hps or hps.approved_at > active_hps.approved_at:
                        active_hps = hps
                elif hps.status == "pending":
                    pending_requests += 1
            
            if active_hps:
                hps_status = "active"
                hps_expires_at = active_hps.expires_at
            elif pending_requests > 0:
                hps_status = "pending"
            else:
                # Verificar si hay solicitudes enviadas (submitted) pero no aprobadas
                submitted_requests = 0
                for hps in user.hps_requests:
                    if hps.status == "submitted":
                        submitted_requests += 1
                
                if submitted_requests > 0:
                    hps_status = "submitted"  # Nuevo estado para solicitudes enviadas
                else:
                    # Verificar si hay HPS expirada
                    for hps in user.hps_requests:
                        if hps.status == "approved" and hps.expires_at and hps.expires_at <= datetime.now().date():
                            hps_status = "expired"
                            hps_expires_at = hps.expires_at
                            break
        
        # Agregar información adicional
        data.update({
            "last_login": user.last_login,
            "login_count": 0,  # Por ahora 0, se puede implementar después
            "team_name": user.team.name if user.team else None,
            "hps_status": hps_status,
            "hps_expires_at": hps_expires_at,
            "pending_hps_requests": pending_requests
        })
        
        return cls(**data)

class UserListResponse(BaseModel):
    """Respuesta de lista de usuarios con paginación"""
    users: List[UserDetailResponse]
    total: int
    page: int
    size: int
    pages: int

class UserFilter(BaseModel):
    """Filtros para búsqueda de usuarios"""
    role: Optional[UserRole] = None
    team_id: Optional[int] = None
    is_active: Optional[bool] = None
    search: Optional[str] = Field(None, description="Búsqueda por username, nombre o email")

class UserCreateRequest(BaseModel):
    """Request para crear usuario desde API"""
    email: EmailStr = Field(..., description="Dirección de email única (se usará como nombre de usuario)")
    full_name: str = Field(..., min_length=2, max_length=100, description="Nombre completo")
    password: str = Field(..., min_length=6, description="Contraseña (mínimo 6 caracteres)")
    role: str = Field(UserRole.MEMBER.value, description="Rol del usuario")
    team_id: Optional[str] = Field(None, description="ID del equipo asignado (UUID como string)")
    
    def get_role_enum(self) -> UserRole:
        """Convertir string a UserRole enum"""
        try:
            return UserRole(self.role)
        except ValueError:
            raise ValueError(f"Rol '{self.role}' no es válido. Roles disponibles: {[r.value for r in UserRole]}")

class UserUpdateRequest(BaseModel):
    """Request para actualizar usuario desde API"""
    email: Optional[EmailStr] = Field(None, description="Nueva dirección de email")
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Nuevo nombre completo")
    role: Optional[Union[UserRole, str]] = Field(None, description="Nuevo rol del usuario")
    team_id: Optional[str] = Field(None, description="Nuevo ID del equipo (UUID como string)")
    is_active: Optional[bool] = Field(None, description="Estado activo del usuario")
    
    @field_validator('role', mode='before')
    @classmethod
    def validate_role(cls, v):
        """Convertir role a string si viene como enum o mantener como string"""
        if v is None:
            return None
        if isinstance(v, UserRole):
            return v.value
        if isinstance(v, str):
            # Validar que el string sea un rol válido
            try:
                UserRole(v)  # Validar que existe
                return v
            except ValueError:
                # Si no es válido, devolver el string de todas formas para que el servicio maneje el error
                return v
        return str(v) if v else None

class UserStatsResponse(BaseModel):
    """Estadísticas de usuarios"""
    total_users: int
    active_users: int
    inactive_users: int
    admins: int
    jefe_seguridad: int
    crypto: int
    team_leaders: int
    members: int
    users_by_team: dict

class BulkUserOperation(BaseModel):
    """Operación en lote sobre usuarios"""
    user_ids: List[int] = Field(..., description="Lista de IDs de usuarios")
    operation: str = Field(..., description="Operación a realizar: activate, deactivate, delete")

class UserSearchResponse(BaseModel):
    """Respuesta de búsqueda de usuarios"""
    users: List[UserResponse]
    query: str
    total_found: int
    search_time_ms: float

class TeamMembersResponse(BaseModel):
    """Respuesta de miembros de equipo"""
    team_id: int
    team_name: Optional[str] = None
    members: List[UserResponse]
    total_members: int
    leaders: List[UserResponse]
    
class UserActivityResponse(BaseModel):
    """Respuesta de actividad de usuario"""
    user_id: int
    username: str
    last_login: Optional[datetime] = None
    login_count: int = 0
    hps_requests: int = 0
    last_activity: Optional[datetime] = None
    
class PasswordResetRequest(BaseModel):
    """Request para reset de contraseña"""
    user_id: int
    new_password: str = Field(..., min_length=6, description="Nueva contraseña")
    confirm_password: str = Field(..., description="Confirmación de nueva contraseña")

class UserRoleChangeRequest(BaseModel):
    """Request para cambio de rol"""
    user_id: int
    new_role: UserRole
    reason: Optional[str] = Field(None, description="Razón del cambio de rol")

class UserTeamChangeRequest(BaseModel):
    """Request para cambio de equipo"""
    user_id: int
    new_team_id: Optional[int]
    reason: Optional[str] = Field(None, description="Razón del cambio de equipo")

