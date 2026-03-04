from dataclasses import dataclass
from typing import Iterable, List, Optional, Set

from rest_framework import permissions


# -----------------------------------------------------------------------------
# RBAC: helpers y clases basadas en permisos (HpsPermission / granted_permissions)
# -----------------------------------------------------------------------------


def user_has_perm(user, codename: str, use_superuser_bypass: bool = True) -> bool:
    """
    Comprueba si el usuario tiene el permiso indicado (vía rol HPS).
    Si use_superuser_bypass es True, is_superuser tiene todos los permisos.
    """
    if not user or not user.is_authenticated:
        return False
    if use_superuser_bypass and getattr(user, "is_superuser", False):
        return True
    profile = getattr(user, "hps_profile", None)
    if not profile or not getattr(profile, "role_id", None):
        return False
    role = getattr(profile, "role", None)
    if not role:
        return False
    # Soporte para rol sin M2M (migraciones no aplicadas o roles legacy)
    granted = getattr(role, "granted_permissions", None)
    if granted is None:
        return False
    return granted.filter(codename=codename).exists()


def get_user_permissions(user) -> Set[str]:
    """Devuelve el conjunto de codenames de permisos del usuario (vía rol HPS)."""
    if not user or not user.is_authenticated:
        return set()
    if getattr(user, "is_superuser", False):
        # Opción: devolver todos los permisos conocidos; aquí devolvemos set sin cargar BD
        from .models import HpsPermission
        return set(HpsPermission.objects.values_list("codename", flat=True))
    profile = getattr(user, "hps_profile", None)
    if not profile or not getattr(profile, "role", None):
        return set()
    role = profile.role
    granted = getattr(role, "granted_permissions", None)
    if granted is None:
        return set()
    return set(granted.values_list("codename", flat=True))


class HasHpsPerm(permissions.BasePermission):
    """
    Permite acceso si el usuario tiene el permiso (codename) indicado.
    Uso: permission_classes = [IsAuthenticated, HasHpsPerm('hps.gestionar_roles')]
    """

    def __init__(self, codename: str, use_superuser_bypass: bool = True):
        self.codename = codename
        self.use_superuser_bypass = use_superuser_bypass

    def has_permission(self, request, view):
        return user_has_perm(request.user, self.codename, self.use_superuser_bypass)

    def __repr__(self):
        return f"HasHpsPerm({self.codename!r})"


class HasHpsPermAny(permissions.BasePermission):
    """
    Permite acceso si el usuario tiene al menos uno de los permisos indicados.
    Uso: permission_classes = [IsAuthenticated, HasHpsPermAny(['hps.ver_solicitudes_todas', 'hps.ver_solicitudes_equipos'])]
    """

    def __init__(self, codenames: Iterable[str], use_superuser_bypass: bool = True):
        self.codenames = list(codenames)
        self.use_superuser_bypass = use_superuser_bypass

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if self.use_superuser_bypass and getattr(request.user, "is_superuser", False):
            return True
        perms = get_user_permissions(request.user)
        return any(c in perms for c in self.codenames)

    def __repr__(self):
        return f"HasHpsPermAny({self.codenames!r})"


# -----------------------------------------------------------------------------
# Contexto de perfil (usado por HasHpsProfile y por lógica que necesite role/team_ids)
# -----------------------------------------------------------------------------


@dataclass
class HpsProfileContext:
    has_profile: bool
    role_name: Optional[str]
    team_id: Optional[str]  # Primer equipo (compatibilidad)
    team_ids: List[str]  # Lista de UUIDs de equipos del usuario (vía memberships)


def _extract_profile_context(user) -> HpsProfileContext:
    """
    Extraer contexto del perfil HPS del usuario.
    team_ids se obtiene de HpsTeamMembership (N:N).
    """
    if not user or not user.is_authenticated:
        return HpsProfileContext(False, None, None, [])
    profile = getattr(user, "hps_profile", None)
    if not profile:
        return HpsProfileContext(False, None, None, [])
    role_name = profile.role.name if profile.role else None

    from .models import HpsTeam, HpsTeamMembership
    is_team_lead = HpsTeam.objects.filter(team_lead=user, is_active=True).exists()
    if is_team_lead and role_name != "team_lead":
        pass  # role_name se mantiene; is_team_lead se usa en permisos

    team_ids = list(
        HpsTeamMembership.objects.filter(
            user=user,
            is_active=True,
        ).values_list('team_id', flat=True)
    )
    team_ids_str = [str(tid) for tid in team_ids]
    team_id = team_ids_str[0] if team_ids_str else (str(profile.team_id) if profile.team_id else None)
    return HpsProfileContext(True, role_name, team_id, team_ids_str)


class HasHpsProfile(permissions.BasePermission):
    """
    Exige que el usuario autenticado tenga un perfil HPS asociado.
    """

    message = "Tu usuario no tiene un perfil HPS asociado."

    def has_permission(self, request, view):
        ctx = _extract_profile_context(request.user)
        return ctx.has_profile


# -----------------------------------------------------------------------------
# Clases RBAC con object-level (audit log, editar perfil)
# -----------------------------------------------------------------------------


class CanViewAuditLog(permissions.BasePermission):
    """
    RBAC: ver audit logs. Acceso a la vista si tiene ver_audit_logs_todos o ver_audit_logs_propios.
    A nivel objeto: puede ver si tiene ver_audit_logs_todos o si el log es suyo.
    """

    message = "No tienes permiso para ver este registro de auditoría."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            user_has_perm(request.user, "hps.ver_audit_logs_todos")
            or user_has_perm(request.user, "hps.ver_audit_logs_propios")
        )

    def has_object_permission(self, request, view, obj):
        if user_has_perm(request.user, "hps.ver_audit_logs_todos"):
            return True
        return getattr(obj, "user_id", None) == getattr(request.user, "id", None)


class CanEditHpsProfileLedMember(permissions.BasePermission):
    """
    RBAC: editar/activar/desactivar perfiles. Quien tiene ver_perfiles_todos (admin) puede todo;
    quien tiene editar_perfil_equipo solo puede sobre usuarios de equipos que lidera.
    """

    message = "Solo puedes modificar usuarios de equipos que lideras."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        from .models import HpsTeam, HpsTeamMembership

        if not getattr(request.user, "hps_profile", None):
            return False
        if user_has_perm(request.user, "hps.ver_perfiles_todos"):
            return True
        if not user_has_perm(request.user, "hps.editar_perfil_equipo"):
            return False
        led_team_ids = set(
            HpsTeam.objects.filter(
                team_lead=request.user,
                is_active=True,
            ).values_list("id", flat=True)
        )
        if not led_team_ids:
            return False
        target_user_id = getattr(obj, "user_id", None) or (obj.user.id if getattr(obj, "user", None) else None)
        if not target_user_id:
            return False
        target_team_ids = set(
            HpsTeamMembership.objects.filter(
                user_id=target_user_id,
                is_active=True,
            ).values_list("team_id", flat=True)
        )
        return bool(led_team_ids & target_team_ids)

