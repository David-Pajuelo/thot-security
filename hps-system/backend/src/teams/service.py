"""
Servicio para gestión de equipos
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional, Dict, Any
from uuid import UUID
import math

from src.models.team import Team
from src.models.user import User
from src.teams.schemas import (
    TeamCreate, TeamUpdate, TeamResponse, TeamDetailResponse, 
    TeamListResponse, TeamStatsResponse, TeamMember
)


class TeamService:
    """Servicio para gestión de equipos"""

    def __init__(self, db: Session):
        self.db = db

    def create_team(self, team_data: TeamCreate, current_user: User) -> TeamResponse:
        """Crear un nuevo equipo"""
        try:
            # Verificar que el nombre no exista
            existing_team = self.db.query(Team).filter(Team.name == team_data.name).first()
            if existing_team:
                raise ValueError("Ya existe un equipo con ese nombre")

            # Verificar que el líder del equipo existe y es activo
            team_lead = None
            if team_data.team_lead_id:
                team_lead = self.db.query(User).filter(
                    and_(User.id == team_data.team_lead_id, User.is_active == True)
                ).first()
                if not team_lead:
                    raise ValueError("El usuario seleccionado como líder no existe o está inactivo")
                
                # Verificar que el usuario no sea ya líder de otro equipo
                existing_team_with_leader = self.db.query(Team).filter(
                    and_(Team.team_lead_id == team_data.team_lead_id, Team.is_active == True)
                ).first()
                if existing_team_with_leader:
                    raise ValueError(f"El usuario {team_lead.full_name} ya es líder del equipo '{existing_team_with_leader.name}'. Un usuario solo puede ser líder de un equipo.")

            # Crear el equipo
            team = Team(
                name=team_data.name,
                description=team_data.description,
                team_lead_id=team_data.team_lead_id,
                is_active=True
            )
            
            self.db.add(team)
            self.db.flush()  # Para obtener el ID del equipo
            
            # Si se asignó un líder, actualizar su rol y team_id (si no es admin)
            if team_data.team_lead_id:
                team_lead = self.db.query(User).filter(User.id == team_data.team_lead_id).first()
                if team_lead:
                    # Cambiar rol a team_lead solo si no es admin
                    if team_lead.role.name != "admin":
                        from src.models.user import Role
                        team_leader_role = self.db.query(Role).filter(Role.name == "team_lead").first()
                        if team_leader_role:
                            team_lead.role_id = team_leader_role.id
                    # Actualizar team_id (siempre, independientemente del rol)
                    team_lead.team_id = team.id
            
            self.db.commit()
            self.db.refresh(team)
            
            return self._team_to_response(team)
            
        except Exception as e:
            self.db.rollback()
            raise e

    def get_teams(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        current_user: User = None
    ) -> List[TeamResponse]:
        """Obtener lista de equipos con filtros"""
        from sqlalchemy.orm import joinedload
        
        query = self.db.query(Team).options(joinedload(Team.team_lead_user))
        
        # Aplicar filtros
        if search:
            query = query.filter(
                Team.name.ilike(f"%{search}%") | 
                Team.description.ilike(f"%{search}%")
            )
        
        if is_active is not None:
            query = query.filter(Team.is_active == is_active)
        
        # Ordenar por nombre
        query = query.order_by(Team.name)
        
        # Aplicar paginación
        teams = query.offset(skip).limit(limit).all()
        
        return [self._team_to_response(team) for team in teams]

    def count_teams(
        self, 
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """Contar equipos con filtros"""
        query = self.db.query(Team)
        
        if search:
            query = query.filter(
                Team.name.ilike(f"%{search}%") | 
                Team.description.ilike(f"%{search}%")
            )
        
        if is_active is not None:
            query = query.filter(Team.is_active == is_active)
        
        return query.count()

    def get_team_by_id(self, team_id: UUID) -> Optional[TeamResponse]:
        """Obtener equipo por ID"""
        from sqlalchemy.orm import joinedload
        
        team = self.db.query(Team).options(joinedload(Team.team_lead_user)).filter(Team.id == team_id).first()
        if not team:
            return None
        
        return self._team_to_response(team)

    def get_team_detail(self, team_id: UUID) -> Optional[TeamDetailResponse]:
        """Obtener detalles del equipo con miembros"""
        from sqlalchemy.orm import joinedload
        
        team = self.db.query(Team).options(joinedload(Team.team_lead_user)).filter(Team.id == team_id).first()
        if not team:
            return None
        
        # Obtener miembros del equipo
        members = self.db.query(User).filter(
            and_(User.team_id == team_id, User.is_active == True)
        ).all()
        
        team_response = self._team_to_response(team)
        team_detail = TeamDetailResponse(**team_response.dict())
        
        # Convertir miembros al formato de respuesta
        team_detail.members = [
            TeamMember(
                id=member.id,
                email=member.email,
                full_name=member.full_name,
                role=member.role.name if member.role else "Sin rol",
                is_active=member.is_active,
                last_login=member.last_login
            ) for member in members
        ]
        
        return team_detail

    def update_team(self, team_id: UUID, team_data: TeamUpdate, current_user: User) -> Optional[TeamResponse]:
        """Actualizar equipo"""
        try:
            team = self.db.query(Team).filter(Team.id == team_id).first()
            if not team:
                return None
            
            # Verificar que el nombre no exista (si se está cambiando)
            if team_data.name and team_data.name != team.name:
                existing_team = self.db.query(Team).filter(
                    and_(Team.name == team_data.name, Team.id != team_id)
                ).first()
                if existing_team:
                    raise ValueError("Ya existe un equipo con ese nombre")
            
            # Verificar que el líder del equipo existe y es activo (solo si se está cambiando)
            if team_data.team_lead_id is not None and team_data.team_lead_id != team.team_lead_id:
                team_lead = self.db.query(User).filter(
                    and_(User.id == team_data.team_lead_id, User.is_active == True)
                ).first()
                if not team_lead:
                    raise ValueError("El usuario seleccionado como líder no existe o está inactivo")
                
                # Verificar que el usuario no sea ya líder de otro equipo (excluyendo el equipo actual)
                existing_team_with_leader = self.db.query(Team).filter(
                    and_(
                        Team.team_lead_id == team_data.team_lead_id, 
                        Team.is_active == True,
                        Team.id != team_id
                    )
                ).first()
                if existing_team_with_leader:
                    raise ValueError(f"El usuario {team_lead.full_name} ya es líder del equipo '{existing_team_with_leader.name}'. Un usuario solo puede ser líder de un equipo.")
            
            # Actualizar campos
            if team_data.name is not None:
                team.name = team_data.name
            if team_data.description is not None:
                team.description = team_data.description
            # Manejar cambios en el líder del equipo
            # Procesar si team_lead_id está presente en los datos (incluso si es None)
            if hasattr(team_data, 'team_lead_id'):
                # Verificar si realmente se está cambiando el líder
                old_team_lead_id = team.team_lead_id
                new_team_lead_id = team_data.team_lead_id
                
                # Solo procesar si hay un cambio real
                if new_team_lead_id != old_team_lead_id:
                    # Quitar rol team_lead del líder anterior (si existe y no es admin)
                    if old_team_lead_id:
                        old_leader = self.db.query(User).filter(User.id == old_team_lead_id).first()
                        if old_leader and old_leader.role.name != "admin":
                            # Cambiar rol a member solo si no es admin
                            from src.models.user import Role
                            member_role = self.db.query(Role).filter(Role.name == "member").first()
                            if member_role:
                                old_leader.role_id = member_role.id
                    
                    # Actualizar el team_lead_id del equipo primero (puede ser None para quitar el líder)
                    team.team_lead_id = new_team_lead_id
                    
                    # Asignar nuevo líder y cambiar su rol (si se especifica uno y no es admin)
                    if new_team_lead_id:
                        new_leader = self.db.query(User).filter(User.id == new_team_lead_id).first()
                        if new_leader:
                            # Cambiar rol a team_lead solo si no es admin
                            if new_leader.role.name != "admin":
                                from src.models.user import Role
                                team_leader_role = self.db.query(Role).filter(Role.name == "team_lead").first()
                                if team_leader_role:
                                    new_leader.role_id = team_leader_role.id
                            # Actualizar team_id (siempre, independientemente del rol)
                            new_leader.team_id = team_id
            
            self.db.commit()
            self.db.refresh(team)
            
            return self._team_to_response(team)
            
        except Exception as e:
            self.db.rollback()
            raise e

    def delete_team(self, team_id: UUID, current_user: User) -> bool:
        """Eliminar equipo (soft delete)"""
        try:
            team = self.db.query(Team).filter(Team.id == team_id).first()
            if not team:
                return False
            
            # Verificar que no tenga miembros activos
            active_members = self.db.query(User).filter(
                and_(User.team_id == team_id, User.is_active == True)
            ).count()
            
            if active_members > 0:
                raise ValueError("No se puede eliminar un equipo que tiene miembros activos")
            
            # Soft delete
            team.is_active = False
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise e

    def get_team_stats(self) -> TeamStatsResponse:
        """Obtener estadísticas de equipos"""
        total_teams = self.db.query(Team).count()
        active_teams = self.db.query(Team).filter(Team.is_active == True).count()
        
        # Contar miembros activos
        total_members = self.db.query(User).filter(User.is_active == True).count()
        
        # Contar equipos con líderes
        teams_with_leaders = self.db.query(Team).filter(
            and_(Team.is_active == True, Team.team_lead_id.isnot(None))
        ).count()
        
        # Promedio de miembros por equipo
        average_members = total_members / active_teams if active_teams > 0 else 0
        
        return TeamStatsResponse(
            total_teams=total_teams,
            active_teams=active_teams,
            total_members=total_members,
            teams_with_leaders=teams_with_leaders,
            average_members_per_team=round(average_members, 2)
        )

    def get_team_members_for_leadership(self, team_id: UUID) -> List[TeamMember]:
        """Obtener miembros de un equipo específico para asignar como líder"""
        from sqlalchemy.orm import joinedload
        
        # Obtener todos los miembros activos del equipo
        members = self.db.query(User).options(
            joinedload(User.role)
        ).filter(
            and_(User.team_id == team_id, User.is_active == True)
        ).all()
        
        return [
            TeamMember(
                id=member.id,
                email=member.email,
                full_name=member.full_name,
                role=member.role.name if member.role else "Sin rol",
                is_active=member.is_active,
                last_login=member.last_login
            ) for member in members
        ]

    def get_available_team_leaders(self, current_team_id: Optional[UUID] = None) -> List[TeamMember]:
        """Obtener usuarios disponibles para ser líderes de equipo (DEPRECATED - usar get_team_members_for_leadership)"""
        # Buscar usuarios con rol team_leader o admin que no sean líderes de otro equipo
        from sqlalchemy import or_
        
        # Construir la consulta base
        query = self.db.query(User).join(User.role).filter(
            and_(
                User.is_active == True,
                or_(User.role.has(name='team_leader'), User.role.has(name='admin'))
            )
        )
        
        # Si se especifica un team_id, permitir cambiar el líder del mismo equipo
        if current_team_id:
            # Excluir solo líderes de otros equipos (no del equipo actual)
            query = query.filter(
                ~User.id.in_(
                    self.db.query(Team.team_lead_id).filter(
                        and_(
                            Team.team_lead_id.isnot(None),
                            Team.id != current_team_id
                        )
                    )
                )
            )
        else:
            # Si no se especifica team_id, excluir todos los líderes existentes
            query = query.filter(
                ~User.id.in_(
                    self.db.query(Team.team_lead_id).filter(Team.team_lead_id.isnot(None))
                )
            )
        
        leaders = query.all()
        
        return [
            TeamMember(
                id=leader.id,
                email=leader.email,
                full_name=leader.full_name,
                role=leader.role.name if leader.role else "Sin rol",
                is_active=leader.is_active,
                last_login=leader.last_login
            ) for leader in leaders
        ]

    def _team_to_response(self, team: Team) -> TeamResponse:
        """Convertir modelo Team a TeamResponse"""
        team_lead_name = None
        if team.team_lead_user:
            team_lead_name = team.team_lead_user.full_name
        
        return TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            team_lead_id=team.team_lead_id,
            is_active=team.is_active,
            member_count=team.member_count,
            created_at=team.created_at,
            updated_at=team.updated_at,
            team_lead_name=team_lead_name
        )
