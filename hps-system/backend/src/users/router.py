# Router de gestión de usuarios para HPS Backend
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from math import ceil

from src.database.database import get_db
from src.auth.dependencies import (
    get_current_user, 
    require_admin, 
    require_team_leader,
    require_any_role,
    can_manage_users
)
from src.auth.schemas import UserRole, UserResponse
from src.models.user import User
from src.users.service import UserService
from src.users.schemas import (
    UserListResponse,
    UserCreateRequest,
    UserUpdateRequest,
    UserDetailResponse,
    UserStatsResponse,
    UserSearchResponse,
    TeamMembersResponse,
    PasswordResetRequest,
    UserRoleChangeRequest,
    UserTeamChangeRequest,
    BulkUserOperation
)

router = APIRouter(
    prefix="/users",
    tags=["Gestión de Usuarios"],
    responses={404: {"description": "No encontrado"}}
)

@router.get("/team/{team_id}/members", response_model=List[UserResponse], summary="Obtener miembros del equipo")
async def get_team_members(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener lista de miembros de un equipo específico.
    Solo líderes de equipo pueden acceder a su propio equipo.
    """
    try:
        service = UserService(db)
        members = service.get_team_members(team_id, current_user)
        return [UserResponse.from_user(member) for member in members]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo miembros del equipo: {str(e)}"
        )

@router.get("/", response_model=UserListResponse, summary="Listar usuarios")
async def list_users(
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Elementos por página"),
    role: Optional[UserRole] = Query(None, description="Filtrar por rol"),
    team_id: Optional[int] = Query(None, description="Filtrar por equipo"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado"),
    search: Optional[str] = Query(None, description="Búsqueda por texto"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener lista paginada de usuarios con filtros opcionales.
    
    - **Admins**: Ven todos los usuarios
    - **Team Leaders**: Solo ven usuarios de su equipo
    - **Members**: Acceso denegado
    """
    if not can_manage_users(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver la lista de usuarios"
        )
    
    user_service = UserService(db)
    
    skip = (page - 1) * size
    role_str = role.value if role else None
    
    users = user_service.get_users(
        skip=skip,
        limit=size,
        role=role_str,
        team_id=team_id,
        is_active=is_active,
        search=search,
        current_user=current_user
    )
    
    total = user_service.count_users(
        role=role_str,
        team_id=team_id,
        is_active=is_active,
        search=search,
        current_user=current_user
    )
    
    # Convertir usuarios al formato de respuesta con información del equipo
    user_responses = [UserDetailResponse.from_user(user) for user in users]
    
    return UserListResponse(
        users=user_responses,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 0
    )

@router.post("/", response_model=UserResponse, summary="Crear usuario")
async def create_user(
    user_data: UserCreateRequest,
    current_user: User = Depends(require_any_role(UserRole.ADMIN, UserRole.TEAM_LEADER)),
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo usuario.
    
    - **Admins**: Pueden crear usuarios con cualquier rol
    - **Team Leaders**: Solo pueden crear usuarios en su equipo con rol Member
    """
    user_service = UserService(db)
    
    # Usar directamente UserCreateRequest que ya tiene el método get_role_enum()
    created_user = user_service.create_user(user_data, current_user)
    return UserResponse.from_user(created_user)

@router.get("/{user_id}", response_model=UserDetailResponse, summary="Obtener usuario")
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener información detallada de un usuario por ID.
    
    - **Admins**: Pueden ver cualquier usuario
    - **Team Leaders**: Solo usuarios de su equipo
    - **Members**: Solo pueden ver su propio perfil
    """
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar permisos de acceso
    if (current_user.role.name == UserRole.MEMBER.value and 
        current_user.id != user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver este usuario"
        )
    
    if (current_user.role.name == UserRole.TEAM_LEADER.value and 
        current_user.team_id != user.team_id and 
        current_user.id != user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes ver usuarios de tu equipo"
        )
    
    return UserDetailResponse.from_user(user)

@router.put("/{user_id}", response_model=UserResponse, summary="Actualizar usuario")
async def update_user(
    user_id: str,
    user_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualizar información de un usuario.
    
    - **Admins**: Pueden actualizar cualquier usuario
    - **Team Leaders**: Solo usuarios de su equipo (sin cambiar roles)
    - **Members**: Solo pueden actualizar su propio perfil (datos básicos)
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Actualizando usuario {user_id} con datos: {user_data.dict()}")
        
        user_service = UserService(db)
        
        # Convertir a esquema de auth
        from src.auth.schemas import UserUpdate
        
        # Asegurar que role sea un string (ya viene validado del schema)
        role_str = None
        if user_data.role is not None:
            if isinstance(user_data.role, str):
                role_str = user_data.role
            elif hasattr(user_data.role, 'value'):
                role_str = user_data.role.value
            else:
                role_str = str(user_data.role)
        
        auth_user_data = UserUpdate(
            email=user_data.email,
            full_name=user_data.full_name,
            role=role_str,
            team_id=user_data.team_id,
            is_active=user_data.is_active
        )
        
        logger.info(f"Datos convertidos: {auth_user_data.dict()}")
        
        result = user_service.update_user(user_id, auth_user_data, current_user)
        return UserResponse.from_user(result)
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error actualizando usuario {user_id}: {error_message}")
        # Asegurar que el error sea un string, no un objeto
        if not isinstance(error_message, str):
            error_message = f"Error al actualizar usuario: {type(e).__name__}"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

@router.delete("/{user_id}", summary="Eliminar usuario")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_any_role(UserRole.ADMIN, UserRole.TEAM_LEADER)),
    db: Session = Depends(get_db)
):
    """
    Eliminar un usuario (soft delete - desactivar).
    
    - **Admins**: Pueden eliminar cualquier usuario
    - **Team Leaders**: Solo usuarios de su equipo
    """
    user_service = UserService(db)
    result = user_service.delete_user(user_id, current_user)
    
    if isinstance(result, dict):
        # Si devuelve un diccionario con detalles de la eliminación
        return {
            "message": "Usuario eliminado exitosamente",
            "user_id": user_id,
            "deleted_by": current_user.email,
            "hps_deleted": result.get("hps_deleted", 0),
            "tokens_deleted": result.get("tokens_deleted", 0)
        }
    else:
        # Si devuelve solo True/False
        return {
            "message": "Usuario eliminado exitosamente",
            "user_id": user_id,
            "deleted_by": current_user.email
        }

@router.post("/{user_id}/activate", response_model=UserResponse, summary="Activar usuario")
async def activate_user(
    user_id: str,
    current_user: User = Depends(require_any_role(UserRole.ADMIN, UserRole.TEAM_LEADER)),
    db: Session = Depends(get_db)
):
    """
    Activar un usuario desactivado.
    """
    user_service = UserService(db)
    user = user_service.activate_user(user_id, current_user)
    
    return UserResponse.from_user(user)

@router.delete("/{user_id}/permanent", summary="Eliminar usuario definitivamente")
async def permanently_delete_user(
    user_id: str,
    current_user: User = Depends(require_any_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Eliminar un usuario definitivamente de la base de datos (hard delete).
    
    - **Solo Admins**: Pueden realizar eliminación definitiva
    - **No se puede eliminar a sí mismo**
    - **Eliminación en cascada**: Se eliminan también todas las solicitudes HPS y tokens asociados
    """
    user_service = UserService(db)
    result = user_service.permanently_delete_user(user_id, current_user)
    
    return {
        "message": "Usuario eliminado definitivamente de la base de datos",
        "user_id": user_id,
        "deleted_by": current_user.email,
        "hps_deleted": result.get("hps_deleted", 0),
        "tokens_deleted": result.get("tokens_deleted", 0)
    }

@router.get("/team/{team_id}", response_model=List[UserResponse], summary="Usuarios por equipo")
async def get_users_by_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener todos los usuarios de un equipo específico.
    """
    user_service = UserService(db)
    return user_service.get_users_by_team(team_id, current_user)

@router.get("/role/{role}", response_model=List[UserResponse], summary="Usuarios por rol")
async def get_users_by_role(
    role: UserRole,
    current_user: User = Depends(require_any_role(UserRole.ADMIN, UserRole.TEAM_LEADER)),
    db: Session = Depends(get_db)
):
    """
    Obtener todos los usuarios con un rol específico.
    """
    user_service = UserService(db)
    return user_service.get_users_by_role(role, current_user)

@router.get("/stats/summary", response_model=UserStatsResponse, summary="Estadísticas de usuarios")
async def get_user_stats(
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas generales de usuarios.
    Solo para administradores.
    """
    user_service = UserService(db)
    
    # Solo contar usuarios activos para estadísticas del dashboard
    total_users = user_service.count_users(is_active=True, current_user=current_user)
    active_users = user_service.count_users(is_active=True, current_user=current_user)
    inactive_users = user_service.count_users(is_active=False, current_user=current_user)
    
    # Solo contar usuarios activos por rol
    # Nota: admin y jefe_seguridad/jefe_seguridad_suplente se excluyen de las estadísticas mostradas
    # (siempre habrá 2 jefes de seguridad: normal y suplente)
    admins = 0  # No mostrar en estadísticas
    jefe_seguridad = 0  # No mostrar en estadísticas
    crypto = user_service.count_users(role=UserRole.CRYPTO.value, is_active=True, current_user=current_user)
    team_leaders = user_service.count_users(role=UserRole.TEAM_LEADER.value, is_active=True, current_user=current_user)
    members = user_service.count_users(role=UserRole.MEMBER.value, is_active=True, current_user=current_user)
    
    return UserStatsResponse(
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
        admins=admins,
        jefe_seguridad=jefe_seguridad,
        crypto=crypto,
        team_leaders=team_leaders,
        members=members,
        users_by_team={}  # TODO: Implementar estadísticas por equipo
    )

@router.get("/stats", response_model=dict, summary="Estadísticas detalladas para reportes")
async def get_detailed_user_stats(
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas detalladas de usuarios para reportes.
    Solo para administradores.
    """
    user_service = UserService(db)
    
    # Estadísticas básicas - solo usuarios activos para dashboard
    total_users = user_service.count_users(is_active=True, current_user=current_user)
    active_users = user_service.count_users(is_active=True, current_user=current_user)
    inactive_users = user_service.count_users(is_active=False, current_user=current_user)
    
    # Estadísticas por rol - solo usuarios activos
    # Nota: admin y jefe_seguridad/jefe_seguridad_suplente se excluyen de las estadísticas mostradas
    # (siempre habrá 2 jefes de seguridad: normal y suplente)
    admins = 0  # No mostrar en estadísticas
    jefe_seguridad = 0  # No mostrar en estadísticas
    crypto = user_service.count_users(role=UserRole.CRYPTO.value, is_active=True, current_user=current_user)
    team_leaders = user_service.count_users(role=UserRole.TEAM_LEADER.value, is_active=True, current_user=current_user)
    members = user_service.count_users(role=UserRole.MEMBER.value, is_active=True, current_user=current_user)
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "admins": admins,
        "jefe_seguridad": jefe_seguridad,
        "crypto": crypto,
        "team_leaders": team_leaders,
        "members": members,
        "users_by_team": {},  # TODO: Implementar estadísticas por equipo
        "period": "30_days",  # TODO: Hacer configurable
        "generated_at": datetime.utcnow().isoformat()
    }

@router.post("/{user_id}/reset-password", summary="Resetear contraseña")
async def reset_user_password(
    user_id: str,
    password_data: PasswordResetRequest,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    Resetear la contraseña de un usuario.
    Solo para administradores.
    """
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las contraseñas no coinciden"
        )
    
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Actualizar contraseña
    from src.auth.jwt import get_password_hash
    user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    return {
        "message": "Contraseña restablecida exitosamente",
        "user_id": user_id,
        "reset_by": current_user.username
    }

@router.get("/search/query", response_model=UserSearchResponse, summary="Buscar usuarios")
async def search_users(
    q: str = Query(..., min_length=2, description="Término de búsqueda"),
    limit: int = Query(10, ge=1, le=50, description="Límite de resultados"),
    current_user: User = Depends(require_any_role(UserRole.ADMIN, UserRole.TEAM_LEADER)),
    db: Session = Depends(get_db)
):
    """
    Buscar usuarios por nombre, username o email.
    """
    import time
    start_time = time.time()
    
    user_service = UserService(db)
    users = user_service.get_users(
        limit=limit,
        search=q,
        current_user=current_user
    )
    
    search_time = (time.time() - start_time) * 1000
    
    # Convertir usuarios al formato de respuesta
    user_responses = [UserResponse.from_user(user) for user in users]
    
    return UserSearchResponse(
        users=user_responses,
        query=q,
        total_found=len(users),
        search_time_ms=round(search_time, 2)
    )

@router.get("/check/{email}")
async def check_user_exists(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verificar si un usuario existe en el sistema
    """
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            return {"exists": True, "user_id": str(user.id)}
        else:
            return {"exists": False}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verificando usuario: {str(e)}"
        )

@router.get("/temp-password/{email}")
async def get_user_temp_password(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener la contraseña temporal de un usuario (solo para usuarios recién creados)
    """
    try:
        # Solo permitir a admins y team leaders
        if current_user.role.name not in ["admin", "team_leader"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a esta información"
            )
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar si el usuario fue creado recientemente (últimas 24 horas)
        from datetime import datetime, timedelta
        if user.created_at and user.created_at > datetime.utcnow() - timedelta(hours=24):
            # En un sistema real, aquí deberías tener un campo para almacenar la contraseña temporal
            # Por ahora, retornamos un mensaje indicando que se debe contactar al admin
            return {
                "temp_password": None,
                "message": "Usuario creado recientemente. Contacta al administrador para obtener las credenciales."
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este usuario no fue creado recientemente"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo contraseña temporal: {str(e)}"
        )

@router.get("/health", summary="Health check de usuarios")
async def users_health():
    """
    Health check específico para la gestión de usuarios.
    Este endpoint es público para monitoring.
    """
    return {
        "status": "healthy",
        "service": "User Management System",
        "version": "1.0.0",
        "endpoints": 15,
        "features": [
            "User CRUD Operations",
            "Role-based Access Control", 
            "Team Management",
            "User Search",
            "Bulk Operations",
            "User Statistics",
            "Password Management",
            "User Existence Check",
            "Temporary Password Management"
        ]
    }
