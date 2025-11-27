"""
Script de migración de roles desde hps-system a Django.

Migra roles de la tabla 'roles' de HPS-System a 'hps_core_hpsrole' de Django.
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from django.core.management.base import BaseCommand
from django.db import transaction
from hps_core.models import HpsRole

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migra roles de hps-system a Django'

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
            # Obtener roles de HPS
            hps_cursor.execute("""
                SELECT id, name, description, permissions, created_at, updated_at
                FROM roles
                ORDER BY id
            """)
            hps_roles = hps_cursor.fetchall()

            self.stdout.write(f'Encontrados {len(hps_roles)} roles en HPS-System')

            if not dry_run:
                migrated = 0
                skipped = 0
                errors = 0

                with transaction.atomic():
                    for role in hps_roles:
                        try:
                            # Intentar obtener o crear el rol
                            django_role, created = HpsRole.objects.get_or_create(
                                name=role['name'],
                                defaults={
                                    'description': role['description'] or '',
                                    'permissions': role['permissions'] or {},
                                }
                            )

                            if created:
                                migrated += 1
                                self.stdout.write(
                                    self.style.SUCCESS(f'  ✓ Creado rol: {role["name"]}')
                                )
                            else:
                                skipped += 1
                                self.stdout.write(
                                    self.style.WARNING(f'  ⊙ Rol ya existe: {role["name"]} (saltado)')
                                )

                        except Exception as e:
                            errors += 1
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ Error con rol {role["name"]}: {str(e)}')
                            )
                            logger.exception(f"Error migrando rol {role['name']}")

                self.stdout.write(self.style.SUCCESS(
                    f'\nMigración completada: {migrated} creados, {skipped} ya existían, {errors} errores'
                ))
            else:
                # Dry run: solo mostrar qué se haría
                for role in hps_roles:
                    exists = HpsRole.objects.filter(name=role['name']).exists()
                    if exists:
                        self.stdout.write(f'  ⊙ Ya existe: {role["name"]}')
                    else:
                        self.stdout.write(f'  ✓ Se crearía: {role["name"]}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error en migración: {str(e)}'))
            logger.exception("Error en migración de roles")
            raise
        finally:
            hps_cursor.close()
            hps_conn.close()
            self.stdout.write('Conexión cerrada')

