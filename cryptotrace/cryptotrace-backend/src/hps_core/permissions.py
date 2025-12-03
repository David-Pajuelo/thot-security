from dataclasses import dataclass
from typing import Iterable, Optional

from rest_framework import permissions


ADMIN_ROLES = {
    "admin",
    "jefe_seguridad",
    "security_chief",
}

TEAM_LEADS = {
    "team_lead",
    "team_leader",
    "jefe_seguridad_suplente",
}


@dataclass
class HpsProfileContext:
    has_profile: bool
    role_name: Optional[str]
    team_id: Optional[int]


def _extract_profile_context(user) -> HpsProfileContext:
    """
    Extraer contexto del perfil HPS del usuario.
    También verifica si el usuario es líder de algún equipo, independientemente de su rol.
    """
    if not user or not user.is_authenticated:
        return HpsProfileContext(False, None, None)
    profile = getattr(user, "hps_profile", None)
    if not profile:
        return HpsProfileContext(False, None, None)
    role_name = profile.role.name if profile.role else None
    
    # Verificar si el usuario es líder de algún equipo activo
    # Si es líder pero su rol no es "team_lead", considerar que tiene permisos de líder
    from .models import HpsTeam
    is_team_lead = HpsTeam.objects.filter(team_lead=user, is_active=True).exists()
    if is_team_lead and role_name != "team_lead":
        # El usuario es líder de equipo pero tiene otro rol (crypto, admin, etc.)
        # Internamente tiene permisos de líder aunque su rol no lo refleje
        # Mantener el rol original pero el sistema de permisos lo tratará como líder
        pass  # role_name se mantiene como está, pero is_team_lead se usará en permisos
    
    team_id = str(profile.team_id) if profile.team_id else None
    return HpsProfileContext(True, role_name, team_id)


class HasHpsProfile(permissions.BasePermission):
    """
    Exige que el usuario autenticado tenga un perfil HPS asociado.
    """

    message = "Tu usuario no tiene un perfil HPS asociado."

    def has_permission(self, request, view):
        ctx = _extract_profile_context(request.user)
        return ctx.has_profile


class IsHpsAdmin(permissions.BasePermission):
    """
    Solo permite acceso completo a roles administradores de HPS.
    """

    message = "Se requieren privilegios de administrador HPS."

    def has_permission(self, request, view):
        ctx = _extract_profile_context(request.user)
        return ctx.has_profile and ctx.role_name in ADMIN_ROLES


class IsHpsAdminOrTeamLead(permissions.BasePermission):
    """
    Permite acceso a administradores y líderes de equipo.
    Un usuario es considerado líder si:
    - Tiene rol "team_lead", "team_leader" o "jefe_seguridad_suplente"
    - O es líder de algún equipo activo (independientemente de su rol)
    """

    message = "Solo administradores o líderes HPS pueden realizar esta acción."

    def has_permission(self, request, view):
        ctx = _extract_profile_context(request.user)
        if not ctx.has_profile:
            return False
        
        # Verificar si es admin
        if ctx.role_name in ADMIN_ROLES:
            return True
        
        # Verificar si tiene rol de líder
        if ctx.role_name in TEAM_LEADS:
            return True
        
        # Verificar si es líder de algún equipo activo (aunque su rol no sea team_lead)
        from .models import HpsTeam
        is_team_lead = HpsTeam.objects.filter(team_lead=request.user, is_active=True).exists()
        return is_team_lead


class IsHpsAdminOrSelf(permissions.BasePermission):
    """
    Permite a administradores ver todo y al resto solo sus propias entidades.
    ViewSets pueden usar este permiso en combinación con filtros.
    """

    message = "Solo puedes acceder a tus solicitudes HPS."

    def has_permission(self, request, view):
        ctx = _extract_profile_context(request.user)
        return ctx.has_profile

    def has_object_permission(self, request, view, obj):
        ctx = _extract_profile_context(request.user)
        if ctx.role_name in ADMIN_ROLES:
            return True
        return getattr(obj, "user_id", None) == getattr(request.user, "id", None)

