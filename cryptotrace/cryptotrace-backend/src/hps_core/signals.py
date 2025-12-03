import uuid
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import HpsRole, HpsUserProfile, HpsTeam

# UUID del equipo AICOX (el mismo que se usa en el frontend)
AICOX_TEAM_UUID = uuid.UUID('d8574c01-851f-4716-9ac9-bbda45469bdf')


def get_or_create_aicox_team():
    """
    Obtener o crear el equipo AICOX.
    Retorna el equipo AICOX, creándolo si no existe.
    """
    try:
        # Intentar obtener el equipo por UUID
        team = HpsTeam.objects.get(id=AICOX_TEAM_UUID)
        return team
    except HpsTeam.DoesNotExist:
        # Si no existe, intentar obtenerlo por nombre
        team = HpsTeam.objects.filter(name__iexact='AICOX').first()
        if team:
            return team
        
        # Crear el equipo AICOX
        team = HpsTeam.objects.create(
            id=AICOX_TEAM_UUID,
            name='AICOX',
            description='Equipo genérico AICOX',
            is_active=True
        )
        return team


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_hps_profile(sender, instance, created, **kwargs):
    """
    Cada usuario de CryptoTrace debe tener un perfil HPS asociado.

    Si no existe, se crea automáticamente usando el rol "member" por defecto
    y asignándolo al equipo AICOX.
    """

    try:
        profile = instance.hps_profile
        # Si el perfil existe pero no tiene equipo, asignarlo a AICOX
        if not profile.team:
            aicox_team = get_or_create_aicox_team()
            profile.team = aicox_team
            profile.save(update_fields=['team'])
        return
    except HpsUserProfile.DoesNotExist:
        pass

    # Determinar el rol por defecto según el tipo de usuario
    if instance.is_superuser:
        # Si es superusuario de Django, asignar rol "admin" de HPS
        default_role = HpsRole.objects.filter(name="admin").first()
        if not default_role:
            default_role, _ = HpsRole.objects.get_or_create(
                name="admin",
                defaults={
                    "description": "Administrador del sistema HPS",
                    "permissions": {},
                },
            )
    else:
        # Para usuarios normales, usar rol "member" por defecto
        default_role = HpsRole.objects.filter(name="member").first()
        if not default_role:
            default_role, _ = HpsRole.objects.get_or_create(
                name="crypto",
                defaults={
                    "description": "Perfil base para usuarios de CryptoTrace",
                    "permissions": {},
                },
            )

    # Obtener o crear el equipo AICOX
    aicox_team = get_or_create_aicox_team()

    HpsUserProfile.objects.get_or_create(
        user=instance,
        defaults={
            "role": default_role,
            "team": aicox_team,  # Asignar automáticamente al equipo AICOX
        },
    )

