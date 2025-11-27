"""
Script de migración de equipos desde hps-system a Django.

Migra equipos de la tabla 'teams' de HPS-System a 'hps_core_hpsteam' de Django.
Nota: Los team_lead se actualizarán después de migrar usuarios.
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from django.core.management.base import BaseCommand
from django.db import transaction
from hps_core.models import HpsTeam

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migra equipos de hps-system a Django'

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
            # Obtener equipos de HPS
            hps_cursor.execute("""
                SELECT id, name, description, team_lead_id, is_active, created_at, updated_at
                FROM teams
                ORDER BY created_at
            """)
            hps_teams = hps_cursor.fetchall()

            self.stdout.write(f'Encontrados {len(hps_teams)} equipos en HPS-System')

            if not dry_run:
                migrated = 0
                skipped = 0
                errors = 0

                with transaction.atomic():
                    for team in hps_teams:
                        try:
                            # Verificar si ya existe (por UUID)
                            existing_team = HpsTeam.objects.filter(id=team['id']).first()

                            if existing_team:
                                skipped += 1
                                self.stdout.write(
                                    self.style.WARNING(f'  ⊙ Equipo ya existe: {team["name"]} (UUID: {team["id"]})')
                                )
                                continue

                            # Crear equipo (team_lead se actualizará después)
                            django_team = HpsTeam.objects.create(
                                id=team['id'],  # Preservar UUID
                                name=team['name'],
                                description=team['description'] or '',
                                team_lead=None,  # Se actualizará después de migrar usuarios
                                is_active=team.get('is_active', True),
                            )

                            migrated += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'  ✓ Creado equipo: {team["name"]} (UUID: {team["id"]})')
                            )

                        except Exception as e:
                            errors += 1
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ Error con equipo {team["name"]}: {str(e)}')
                            )
                            logger.exception(f"Error migrando equipo {team['name']}")

                self.stdout.write(self.style.SUCCESS(
                    f'\nMigración completada: {migrated} creados, {skipped} ya existían, {errors} errores'
                ))
                self.stdout.write(self.style.WARNING(
                    '⚠ NOTA: Los team_lead se actualizarán después de migrar usuarios con el comando update_team_leads'
                ))
            else:
                # Dry run: solo mostrar qué se haría
                for team in hps_teams:
                    exists = HpsTeam.objects.filter(id=team['id']).exists()
                    if exists:
                        self.stdout.write(f'  ⊙ Ya existe: {team["name"]} (UUID: {team["id"]})')
                    else:
                        self.stdout.write(f'  ✓ Se crearía: {team["name"]} (UUID: {team["id"]})')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error en migración: {str(e)}'))
            logger.exception("Error en migración de equipos")
            raise
        finally:
            hps_cursor.close()
            hps_conn.close()
            self.stdout.write('Conexión cerrada')

