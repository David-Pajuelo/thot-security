"""
Esquemas Pydantic para gestión de equipos
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class TeamBase(BaseModel):
    """Esquema base para equipos"""
    name: str = Field(..., min_length=2, max_length=100, description="Nombre del equipo")
    description: Optional[str] = Field(None, max_length=500, description="Descripción del equipo")
    team_lead_id: Optional[UUID] = Field(None, description="ID del líder del equipo")
    
    @validator('team_lead_id', pre=True)
    def validate_team_lead_id(cls, v):
        if v == "" or v is None:
            return None
        return v


class TeamCreate(TeamBase):
    """Esquema para crear un equipo"""
    pass


class TeamUpdate(BaseModel):
    """Esquema para actualizar un equipo"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    team_lead_id: Optional[UUID] = None
    
    @validator('team_lead_id', pre=True)
    def validate_team_lead_id(cls, v):
        if v == "" or v is None:
            return None
        return v


class TeamMember(BaseModel):
    """Esquema para miembro del equipo"""
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login: Optional[datetime] = None


class TeamResponse(TeamBase):
    """Esquema de respuesta para equipo"""
    id: UUID
    is_active: bool
    member_count: int
    created_at: datetime
    updated_at: datetime
    team_lead_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class TeamDetailResponse(TeamResponse):
    """Esquema detallado para equipo con miembros"""
    members: List[TeamMember] = []


class TeamListResponse(BaseModel):
    """Esquema para lista de equipos"""
    teams: List[TeamResponse]
    total: int
    page: int
    size: int
    pages: int


class TeamStatsResponse(BaseModel):
    """Esquema para estadísticas de equipos"""
    total_teams: int
    active_teams: int
    total_members: int
    teams_with_leaders: int
    average_members_per_team: float
