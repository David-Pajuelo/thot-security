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
    if not user or not user.is_authenticated:
        return HpsProfileContext(False, None, None)
    profile = getattr(user, "hps_profile", None)
    if not profile:
        return HpsProfileContext(False, None, None)
    role_name = profile.role.name if profile.role else None
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
    """

    message = "Solo administradores o líderes HPS pueden realizar esta acción."

    def has_permission(self, request, view):
        ctx = _extract_profile_context(request.user)
        if not ctx.has_profile:
            return False
        return ctx.role_name in ADMIN_ROLES.union(TEAM_LEADS)


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

