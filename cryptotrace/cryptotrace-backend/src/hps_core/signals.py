from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import HpsRole, HpsUserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_hps_profile(sender, instance, created, **kwargs):
    """
    Cada usuario de CryptoTrace debe tener un perfil HPS asociado.

    Si no existe, se crea automáticamente usando el rol "member" por defecto.
    """

    try:
        instance.hps_profile
        return
    except HpsUserProfile.DoesNotExist:
        pass

    # Intentar obtener el rol "member", si no existe crear "crypto" como fallback
    default_role = HpsRole.objects.filter(name="member").first()
    if not default_role:
        default_role, _ = HpsRole.objects.get_or_create(
            name="crypto",
            defaults={
                "description": "Perfil base para usuarios de CryptoTrace",
                "permissions": {},
            },
        )

    HpsUserProfile.objects.get_or_create(
        user=instance,
        defaults={
            "role": default_role,
        },
    )

