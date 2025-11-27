# Esquemas Pydantic para autenticación
from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    """Roles de usuario en el sistema HPS"""
    ADMIN = "admin"
    JEFE_SEGURIDAD = "jefe_seguridad"
    CRYPTO = "crypto"
    TEAM_LEADER = "team_lead"
    MEMBER = "member"

class Token(BaseModel):
    """Respuesta de token JWT"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str  # UUID como string
    email: str
    role: str

class TokenData(BaseModel):
    """Datos extraídos del token"""
    email: Optional[str] = None
    user_id: Optional[str] = None  # UUID como string
    role: Optional[str] = None

class UserLogin(BaseModel):
    """Esquema para login de usuario"""
    email: str  # Usamos email como login
    password: str

class UserCreate(BaseModel):
    """Esquema para crear usuario"""
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.MEMBER  # Enum del rol
    team_id: Optional[str] = None  # UUID como string
    
    # Campos internos para mapeo con BD
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role_id: Optional[int] = None
    
    @classmethod
    def from_form_data(cls, email: str, full_name: str, password: str, role: str, team_id: Optional[str] = None):
        """Crear desde datos del formulario frontend"""
        # Dividir full_name en first_name y last_name
        name_parts = full_name.strip().split()
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        # Convertir role string a UserRole enum
        role_enum = UserRole(role) if role in [r.value for r in UserRole] else UserRole.MEMBER
        
        return cls(
            email=email,
            full_name=full_name,
            password=password,
            role=role_enum,
            team_id=team_id,
            first_name=first_name,
            last_name=last_name
        )

class UserUpdate(BaseModel):
    """Esquema para actualizar usuario"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    team_id: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    """Respuesta de usuario (sin password)"""
    id: str  # UUID como string
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: str
    role: str  # Del relationship role.name
    is_active: bool
    is_temp_password: bool
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    created_at: str
    updated_at: str

    @classmethod
    def from_user(cls, user):
        """Crear UserResponse desde modelo User"""
        return cls(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name if user.first_name else None,
            last_name=user.last_name if user.last_name else None,
            full_name=f"{user.first_name} {user.last_name}".strip(),
            role=user.role.name if user.role else "member",
            is_active=user.is_active,
            is_temp_password=user.is_temp_password,
            team_id=str(user.team_id) if user.team_id else None,
            team_name=user.team.name if user.team else None,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat()
        )

    class Config:
        from_attributes = True

class PasswordChange(BaseModel):
    """Esquema para cambio de contraseña"""
    current_password: str
    new_password: str
    confirm_password: str
