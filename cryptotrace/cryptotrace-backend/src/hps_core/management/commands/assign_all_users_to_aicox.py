"""
Comando de gestión para asignar todos los usuarios al equipo AICOX.
"""
import uuid
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hps_core.models import HpsTeam, HpsUserProfile

User = get_user_model()
logger = logging.getLogger(__name__)

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
            # Si existe con otro UUID, actualizar el UUID (aunque esto es raro)
            # Por ahora, simplemente retornarlo
            return team
        
        # Crear el equipo AICOX
        team = HpsTeam.objects.create(
            id=AICOX_TEAM_UUID,
            name='AICOX',
            description='Equipo genérico AICOX',
            is_active=True
        )
        logger.info(f"Equipo AICOX creado con UUID {AICOX_TEAM_UUID}")
        return team


class Command(BaseCommand):
    help = 'Asigna todos los usuarios existentes al equipo AICOX'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula los cambios sin aplicarlos a la base de datos.',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        self.stdout.write(self.style.SUCCESS("Iniciando asignación de usuarios al equipo AICOX..."))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Modo DRY-RUN activado: No se realizarán cambios en la base de datos."))

        # Obtener o crear el equipo AICOX
        aicox_team = get_or_create_aicox_team()
        self.stdout.write(self.style.SUCCESS(f"✓ Equipo AICOX: {aicox_team.name} (ID: {aicox_team.id})"))

        # Obtener todos los perfiles de usuario
        profiles = HpsUserProfile.objects.select_related('user', 'team').all()
        total_profiles = profiles.count()
        
        self.stdout.write(f"\nTotal de perfiles a revisar: {total_profiles}")

        updated_count = 0
        already_assigned_count = 0
        error_count = 0

        for profile in profiles:
            try:
                # Verificar si ya está asignado al equipo AICOX
                if profile.team and profile.team.id == aicox_team.id:
                    already_assigned_count += 1
                    continue
                
                if not dry_run:
                    # Asignar al equipo AICOX
                    profile.team = aicox_team
                    profile.save(update_fields=['team'])
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Usuario asignado: {profile.user.email} → AICOX"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"DRY-RUN: Se asignaría {profile.user.email} → AICOX"
                        )
                    )
                    updated_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Error procesando usuario {profile.user.email}: {e}"
                    )
                )

        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Proceso de asignación finalizado."))
        self.stdout.write(self.style.SUCCESS(f"Perfiles revisados: {total_profiles}"))
        self.stdout.write(self.style.SUCCESS(f"Perfiles actualizados: {updated_count}"))
        self.stdout.write(self.style.WARNING(f"Perfiles ya asignados a AICOX: {already_assigned_count}"))
        self.stdout.write(self.style.ERROR(f"Errores encontrados: {error_count}"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

