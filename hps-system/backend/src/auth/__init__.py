# Módulo de autenticación para HPS Backend
from .jwt import verify_password, get_password_hash, create_access_token, verify_token
from .schemas import UserRole, Token, TokenData, UserLogin, UserCreate, UserUpdate, UserResponse, PasswordChange
from .dependencies import (
    get_current_user, 
    get_current_active_user, 
    require_role, 
    require_admin, 
    require_team_leader,
    require_any_role,
    is_admin,
    is_team_leader,
    can_manage_users,
    can_access_team_data
)
from .service import AuthService

__all__ = [
    # JWT functions
    "verify_password", 
    "get_password_hash", 
    "create_access_token", 
    "verify_token",
    
    # Schemas
    "UserRole", 
    "Token", 
    "TokenData", 
    "UserLogin", 
    "UserCreate", 
    "UserUpdate", 
    "UserResponse", 
    "PasswordChange",
    
    # Dependencies
    "get_current_user", 
    "get_current_active_user", 
    "require_role", 
    "require_admin", 
    "require_team_leader",
    "require_any_role",
    "is_admin",
    "is_team_leader",
    "can_manage_users",
    "can_access_team_data",
    
    # Services
    "AuthService"
]