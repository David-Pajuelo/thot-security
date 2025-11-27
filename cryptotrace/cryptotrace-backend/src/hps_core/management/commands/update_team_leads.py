"""
Script para actualizar team_lead de equipos después de migrar usuarios.

Este script debe ejecutarse después de migrate_hps_users para mapear
los team_lead_id (UUIDs) a los usuarios Django migrados.
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from django.core.management.base import BaseCommand
from django.db import transaction
from hps_core.models import HpsTeam, HpsUserMapping

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Actualiza team_lead de equipos usando el mapeo de usuarios'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hps-db-url',
            type=str,
            required=True,
            help='URL de conexión a base HPS: postgresql://user:pass@host:port/dbname'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin guardar cambios'
        )

    def handle(self, *args, **options):
        hps_db_url = options['hps_db_url']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se guardarán cambios'))

        # Conectar a base HPS
        try:
            hps_conn = psycopg2.connect(hps_db_url)
            hps_cursor = hps_conn.cursor(cursor_factory=RealDictCursor)
            self.stdout.write(self.style.SUCCESS('✓ Conectado a base HPS'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error conectando a base HPS: {str(e)}'))
            return

        try:
            # Obtener equipos con team_lead_id
            hps_cursor.execute("""
                SELECT id, name, team_lead_id
                FROM teams
                WHERE team_lead_id IS NOT NULL
            """)
            teams_with_leads = hps_cursor.fetchall()

            self.stdout.write(f'Encontrados {len(teams_with_leads)} equipos con team_lead en HPS-System')

            if not dry_run:
                updated = 0
                not_found = 0
                errors = 0

                with transaction.atomic():
                    for team in teams_with_leads:
                        try:
                            # Buscar equipo en Django
                            django_team = HpsTeam.objects.filter(id=team['id']).first()
                            if not django_team:
                                self.stdout.write(
                                    self.style.WARNING(f'  ⊙ Equipo no encontrado: {team["name"]} (UUID: {team["id"]})')
                                )
                                not_found += 1
                                continue

                            # Buscar mapeo de usuario
                            user_mapping = HpsUserMapping.objects.filter(
                                hps_user_uuid=team['team_lead_id']
                            ).first()

                            if not user_mapping:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'  ⊙ Team lead no migrado: {team["team_lead_id"]} para equipo {team["name"]}'
                                    )
                                )
                                not_found += 1
                                continue

                            # Actualizar team_lead
                            django_team.team_lead = user_mapping.django_user
                            django_team.save(update_fields=['team_lead'])

                            updated += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Actualizado team_lead de {team["name"]}: {user_mapping.django_user.email}'
                                )
                            )

                        except Exception as e:
                            errors += 1
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ Error actualizando equipo {team["name"]}: {str(e)}')
                            )
                            logger.exception(f"Error actualizando team_lead para equipo {team['name']}")

                self.stdout.write(self.style.SUCCESS(
                    f'\nActualización completada: {updated} actualizados, {not_found} no encontrados, {errors} errores'
                ))
            else:
                # Dry run: solo mostrar qué se haría
                for team in teams_with_leads:
                    django_team = HpsTeam.objects.filter(id=team['id']).first()
                    user_mapping = HpsUserMapping.objects.filter(
                        hps_user_uuid=team['team_lead_id']
                    ).first()

                    if not django_team:
                        self.stdout.write(f'  ⊙ Equipo no encontrado: {team["name"]}')
                    elif not user_mapping:
                        self.stdout.write(f'  ⊙ Team lead no migrado: {team["team_lead_id"]}')
                    else:
                        self.stdout.write(
                            f'  ✓ Se actualizaría: {team["name"]} → {user_mapping.django_user.email}'
                        )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error en actualización: {str(e)}'))
            logger.exception("Error actualizando team leads")
            raise
        finally:
            hps_cursor.close()
            hps_conn.close()
            self.stdout.write('Conexión cerrada')

