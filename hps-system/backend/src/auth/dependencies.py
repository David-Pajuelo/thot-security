# Dependencias de FastAPI para autenticación
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from src.database.database import get_db
from src.auth.jwt import get_user_from_token, credentials_exception, permissions_exception
from src.auth.schemas import UserRole, TokenData
from src.models.user import User

# Configuración del esquema de seguridad Bearer
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Obtener usuario actual desde token JWT"""
    token = credentials.credentials
    
    # Verificar token y extraer datos
    user_data = get_user_from_token(token)
    if user_data is None:
        raise credentials_exception
    
    # Buscar usuario en base de datos por UUID con relaciones cargadas
    import uuid
    from sqlalchemy.orm import joinedload
    try:
        user_uuid = uuid.UUID(user_data["user_id"])
        user = db.query(User).options(
            joinedload(User.role),
            joinedload(User.team)
        ).filter(User.id == user_uuid).first()
    except (ValueError, TypeError):
        raise credentials_exception
    
    if user is None:
        raise credentials_exception
    
    # Verificar que el usuario esté activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Obtener usuario activo (alias para claridad)"""
    return current_user

def require_role(required_role: UserRole):
    """Dependencia para requerir un rol específico"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name != required_role.value:
            raise permissions_exception
        return current_user
    return role_checker

def require_admin():
    """Dependencia para requerir rol de administrador"""
    return require_role(UserRole.ADMIN)

def require_team_leader():
    """Dependencia para requerir rol de líder de equipo"""
    async def team_leader_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in [UserRole.ADMIN.value, UserRole.TEAM_LEADER.value]:
            raise permissions_exception
        return current_user
    return team_leader_checker

def require_any_role(*roles: UserRole):
    """Dependencia para requerir cualquiera de los roles especificados"""
    async def any_role_checker(current_user: User = Depends(get_current_user)) -> User:
        allowed_roles = [role.value for role in roles]
        if current_user.role.name not in allowed_roles:
            raise permissions_exception
        return current_user
    return any_role_checker

# Funciones de utilidad
def is_admin(user: User) -> bool:
    """Verificar si el usuario es administrador"""
    return user.role.name == UserRole.ADMIN.value

def is_team_leader(user: User) -> bool:
    """Verificar si el usuario es líder de equipo"""
    return user.role.name == UserRole.TEAM_LEADER.value

def can_manage_users(user: User) -> bool:
    """Verificar si el usuario puede gestionar otros usuarios"""
    return user.role.name in [UserRole.ADMIN.value, UserRole.TEAM_LEADER.value, "jefe_seguridad", "security_chief"]

def can_access_team_data(user: User, team_id: Optional[str] = None) -> bool:
    """Verificar si el usuario puede acceder a datos de equipo"""
    if user.role.name == UserRole.ADMIN.value:
        return True
    if user.role.name == UserRole.TEAM_LEADER.value:
        return team_id is None or str(user.team_id) == team_id
    return str(user.team_id) == team_id

async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """Obtener usuario actual desde token JWT como diccionario"""
    user = await get_current_user(credentials, db)
    
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role_name": user.role.name if user.role else "member",
        "is_active": user.is_active,
        "team_id": str(user.team_id) if user.team_id else None
    }
