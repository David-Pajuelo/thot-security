"""
Router para gestión de equipos
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from math import ceil

from src.database.database import get_db
from src.auth.dependencies import (
    get_current_user, 
    require_admin, 
    require_team_leader,
    require_any_role
)
from src.auth.schemas import UserRole
from src.models.user import User
from src.teams.service import TeamService
from src.teams.schemas import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamDetailResponse,
    TeamListResponse,
    TeamStatsResponse,
    TeamMember
)

router = APIRouter(
    prefix="/teams",
    tags=["Gestión de Equipos"],
    responses={404: {"description": "No encontrado"}}
)

@router.get("/", response_model=TeamListResponse, summary="Listar equipos")
async def list_teams(
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Elementos por página"),
    search: Optional[str] = Query(None, description="Búsqueda por texto"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener lista paginada de equipos con filtros opcionales.
    
    - **Admins**: Ven todos los equipos
    - **Team Leaders**: Solo ven su equipo
    - **Members**: Acceso denegado
    """
    if current_user.role.name not in ['admin', 'team_leader']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver la lista de equipos"
        )
    
    team_service = TeamService(db)
    
    skip = (page - 1) * size
    
    teams = team_service.get_teams(
        skip=skip,
        limit=size,
        search=search,
        is_active=is_active,
        current_user=current_user
    )
    
    total = team_service.count_teams(search=search, is_active=is_active)
    
    return TeamListResponse(
        teams=teams,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 0
    )

@router.post("/", response_model=TeamResponse, summary="Crear equipo")
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(require_any_role(UserRole.ADMIN, UserRole.TEAM_LEADER)),
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo equipo.
    
    - **Admins**: Pueden crear cualquier equipo
    - **Team Leaders**: Solo pueden crear equipos si tienen permisos especiales
    """
    team_service = TeamService(db)
    return team_service.create_team(team_data, current_user)

@router.get("/{team_id}", response_model=TeamDetailResponse, summary="Obtener equipo")
async def get_team(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener detalles de un equipo específico con sus miembros.
    """
    team_service = TeamService(db)
    
    # Verificar permisos
    if current_user.role.name == 'team_leader':
        # Los team leaders solo pueden ver su propio equipo
        if current_user.team_id != team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes ver tu propio equipo"
            )
    elif current_user.role.name == 'member':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver equipos"
        )
    
    team = team_service.get_team_detail(team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipo no encontrado"
        )
    
    return team

@router.put("/{team_id}", response_model=TeamResponse, summary="Actualizar equipo")
async def update_team(
    team_id: UUID,
    team_data: TeamUpdate,
    current_user: User = Depends(require_any_role(UserRole.ADMIN, UserRole.TEAM_LEADER)),
    db: Session = Depends(get_db)
):
    """
    Actualizar un equipo existente.
    
    - **Admins**: Pueden actualizar cualquier equipo
    - **Team Leaders**: Solo pueden actualizar su propio equipo
    """
    team_service = TeamService(db)
    
    # Verificar que el equipo existe
    existing_team = team_service.get_team_by_id(team_id)
    if not existing_team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipo no encontrado"
        )
    
    # Verificar permisos para team leaders
    if current_user.role.name == 'team_leader':
        if current_user.team_id != team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes actualizar tu propio equipo"
            )
    
    updated_team = team_service.update_team(team_id, team_data, current_user)
    if not updated_team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipo no encontrado"
        )
    
    return updated_team

@router.delete("/{team_id}", summary="Eliminar equipo")
async def delete_team(
    team_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Eliminar un equipo (soft delete).
    
    - **Solo Admins**: Pueden eliminar equipos
    - **Restricción**: No se puede eliminar un equipo con miembros activos
    """
    team_service = TeamService(db)
    
    success = team_service.delete_team(team_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipo no encontrado o no se puede eliminar"
        )
    
    return {"message": "Equipo eliminado exitosamente"}

@router.get("/stats/overview", response_model=TeamStatsResponse, summary="Estadísticas de equipos")
async def get_team_stats(
    current_user: User = Depends(require_any_role(UserRole.ADMIN, UserRole.TEAM_LEADER)),
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas generales de equipos.
    """
    team_service = TeamService(db)
    return team_service.get_team_stats()

@router.get("/leaders/available", response_model=List[TeamMember], summary="Líderes disponibles")
async def get_available_team_leaders(
    team_id: Optional[UUID] = Query(None, description="ID del equipo para el cual se buscan líderes (opcional)"),
    current_user: User = Depends(require_any_role(UserRole.ADMIN, UserRole.TEAM_LEADER)),
    db: Session = Depends(get_db)
):
    """
    Obtener lista de usuarios disponibles para ser líderes de equipo.
    
    - Si se especifica team_id: Incluye el líder actual del equipo en la lista
    - Si no se especifica: Solo muestra usuarios que no son líderes de ningún equipo
    """
    team_service = TeamService(db)
    return team_service.get_available_team_leaders(team_id)

@router.get("/{team_id}/members", response_model=List[TeamMember], summary="Miembros del equipo")
async def get_team_members(
    team_id: UUID,
    current_user: User = Depends(require_any_role(UserRole.ADMIN, UserRole.TEAM_LEADER)),
    db: Session = Depends(get_db)
):
    """
    Obtener lista de miembros de un equipo específico para asignar como líder.
    """
    team_service = TeamService(db)
    return team_service.get_team_members_for_leadership(team_id)





