# Migración de datos RBAC: crear permisos y asignarlos a roles según AUDITORIA-Y-PLAN-RBAC-GLOBAL.md

from django.db import migrations


# Todos los permisos: (codename, name, category)
PERMISSIONS_DATA = [
    ("hps.ver_perfil", "Tener perfil HPS (acceso mínimo)", "hps"),
    ("hps.gestionar_roles", "Gestionar roles HPS", "hps"),
    ("hps.ver_equipos_todos", "Ver todos los equipos", "hps"),
    ("hps.ver_equipos_liderados", "Ver equipos que lidera", "hps"),
    ("hps.gestionar_equipos", "Crear/editar/eliminar equipos", "hps"),
    ("hps.ver_solicitudes_todas", "Ver todas las solicitudes HPS", "hps"),
    ("hps.ver_solicitudes_equipos", "Ver solicitudes de equipos que lidera", "hps"),
    ("hps.ver_solicitudes_propias", "Ver propias solicitudes", "hps"),
    ("hps.crear_tokens", "Crear tokens HPS", "hps"),
    ("hps.ver_todos_tokens", "Listar/ver todos los tokens", "hps"),
    ("hps.gestionar_plantillas", "Gestionar plantillas PDF", "hps"),
    ("hps.ver_audit_logs_todos", "Ver todos los audit logs", "hps"),
    ("hps.ver_audit_logs_propios", "Ver propios audit logs", "hps"),
    ("hps.ver_perfiles_todos", "Ver todos los perfiles", "hps"),
    ("hps.ver_perfiles_equipos", "Ver perfiles de equipos que lidera", "hps"),
    ("hps.crear_perfil", "Crear perfiles de usuario", "hps"),
    ("hps.editar_perfil_equipo", "Editar perfiles de miembros de equipos que lidera", "hps"),
    ("hps.asignar_rol", "Asignar roles a usuarios", "hps"),
    ("chat.ver_todas_conversaciones", "Ver listado global de conversaciones", "chat"),
    ("productos.ver_toda_linea_temporal", "Ver toda la línea temporal de productos", "productos"),
    ("productos.limpiar_toda_linea_temporal", "Limpiar registros de cualquier usuario en línea temporal", "productos"),
]

# Rol name -> list of codenames (según matriz del plan RBAC)
ROLE_PERMISSIONS = {
    "admin": [
        "hps.ver_perfil",
        "hps.gestionar_roles",
        "hps.ver_equipos_todos",
        "hps.ver_equipos_liderados",
        "hps.gestionar_equipos",
        "hps.ver_solicitudes_todas",
        "hps.ver_solicitudes_equipos",
        "hps.ver_solicitudes_propias",
        "hps.crear_tokens",
        "hps.ver_todos_tokens",
        "hps.gestionar_plantillas",
        "hps.ver_audit_logs_todos",
        "hps.ver_perfiles_todos",
        "hps.crear_perfil",
        "hps.editar_perfil_equipo",
        "hps.asignar_rol",
        "chat.ver_todas_conversaciones",
        "productos.ver_toda_linea_temporal",
        "productos.limpiar_toda_linea_temporal",
    ],
    "jefe_seguridad": [
        "hps.ver_perfil",
        "hps.ver_equipos_todos",
        "hps.ver_equipos_liderados",
        "hps.gestionar_equipos",
        "hps.ver_solicitudes_todas",
        "hps.ver_solicitudes_equipos",
        "hps.ver_solicitudes_propias",
        "hps.crear_tokens",
        "hps.ver_todos_tokens",
        "hps.gestionar_plantillas",
        "hps.ver_audit_logs_todos",
        "hps.ver_perfiles_todos",
        "hps.crear_perfil",
        "hps.editar_perfil_equipo",
        "hps.asignar_rol",
        "productos.ver_toda_linea_temporal",
        "productos.limpiar_toda_linea_temporal",
    ],
    "jefe_seguridad_suplente": [
        "hps.ver_perfil",
        "hps.ver_equipos_liderados",
        "hps.gestionar_equipos",
        "hps.ver_solicitudes_equipos",
        "hps.ver_solicitudes_propias",
        "hps.crear_tokens",
        "hps.gestionar_plantillas",
        "hps.ver_audit_logs_propios",
        "hps.ver_perfiles_todos",
        "hps.ver_perfiles_equipos",
        "hps.crear_perfil",
        "hps.editar_perfil_equipo",
        "hps.asignar_rol",
        "productos.ver_toda_linea_temporal",
        "productos.limpiar_toda_linea_temporal",
    ],
    "team_lead": [
        "hps.ver_perfil",
        "hps.ver_equipos_liderados",
        "hps.gestionar_equipos",
        "hps.ver_solicitudes_equipos",
        "hps.ver_solicitudes_propias",
        "hps.ver_audit_logs_propios",
        "hps.ver_perfiles_todos",
        "hps.ver_perfiles_equipos",
        "hps.crear_perfil",
        "hps.editar_perfil_equipo",
    ],
    "member": [
        "hps.ver_perfil",
        "hps.ver_solicitudes_propias",
        "hps.ver_audit_logs_propios",
        "hps.ver_perfiles_todos",
    ],
    "crypto": [
        "hps.ver_perfil",
        "hps.ver_solicitudes_propias",
        "hps.ver_audit_logs_propios",
        "hps.ver_perfiles_todos",
        "productos.ver_toda_linea_temporal",
        "productos.limpiar_toda_linea_temporal",
    ],
}


def populate_permissions(apps, schema_editor):
    HpsPermission = apps.get_model("hps_core", "HpsPermission")
    HpsRole = apps.get_model("hps_core", "HpsRole")

    for codename, name, category in PERMISSIONS_DATA:
        HpsPermission.objects.get_or_create(
            codename=codename,
            defaults={"name": name, "category": category},
        )

    codename_to_perm = {p.codename: p for p in HpsPermission.objects.all()}

    for role_name, codenames in ROLE_PERMISSIONS.items():
        try:
            role = HpsRole.objects.get(name=role_name)
        except HpsRole.DoesNotExist:
            continue
        to_add = [codename_to_perm[c] for c in codenames if c in codename_to_perm]
        role.granted_permissions.add(*to_add)


def reverse_populate(apps, schema_editor):
    HpsRole = apps.get_model("hps_core", "HpsRole")
    for role in HpsRole.objects.all():
        role.granted_permissions.clear()


class Migration(migrations.Migration):

    dependencies = [
        ("hps_core", "0007_add_hps_permission_and_role_m2m"),
    ]

    operations = [
        migrations.RunPython(populate_permissions, reverse_populate),
    ]
