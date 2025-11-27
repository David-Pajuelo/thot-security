"""
Script de migración de usuarios desde hps-system a Django.

Migra usuarios de la tabla 'users' de HPS-System a 'auth_user' + 'hps_core_hpsuserprofile' de Django.
Este es el script más complejo ya que requiere:
- Crear User de Django
- Crear HpsUserProfile
- Mapear roles y equipos
- Crear entrada en HpsUserMapping
- Manejar password_hash
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from hps_core.models import HpsRole, HpsTeam, HpsUserProfile, HpsUserMapping

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migra usuarios de hps-system a Django'

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
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Saltar usuarios que ya existen (por email)'
        )

    def handle(self, *args, **options):
        hps_db_url = options['hps_db_url']
        dry_run = options['dry_run']
        skip_existing = options['skip_existing']

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
            # Obtener usuarios de HPS
            hps_cursor.execute("""
                SELECT 
                    id, email, password_hash, first_name, last_name,
                    role_id, team_id, is_active, email_verified,
                    is_temp_password, last_login, created_at, updated_at
                FROM users
                ORDER BY created_at
            """)
            hps_users = hps_cursor.fetchall()

            self.stdout.write(f'Encontrados {len(hps_users)} usuarios en HPS-System')

            if not dry_run:
                migrated = 0
                skipped = 0
                errors = 0

                with transaction.atomic():
                    for user_data in hps_users:
                        try:
                            # Verificar si usuario ya existe por email
                            existing_user = User.objects.filter(email=user_data['email']).first()
                            
                            if existing_user:
                                if skip_existing:
                                    skipped += 1
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f'  ⊙ Usuario ya existe: {user_data["email"]} (saltado)'
                                        )
                                    )
                                    continue
                                else:
                                    self.stdout.write(
                                        self.style.ERROR(
                                            f'  ✗ Usuario ya existe: {user_data["email"]} (use --skip-existing para saltar)'
                                        )
                                    )
                                    errors += 1
                                    continue

                            # Verificar que el rol existe
                            try:
                                django_role = HpsRole.objects.get(id=user_data['role_id'])
                            except HpsRole.DoesNotExist:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f'  ✗ Rol no encontrado: role_id={user_data["role_id"]} para usuario {user_data["email"]}'
                                    )
                                )
                                errors += 1
                                continue

                            # Verificar que el equipo existe (si tiene team_id)
                            django_team = None
                            if user_data.get('team_id'):
                                try:
                                    django_team = HpsTeam.objects.get(id=user_data['team_id'])
                                except HpsTeam.DoesNotExist:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f'  ⚠ Equipo no encontrado: team_id={user_data["team_id"]} para usuario {user_data["email"]} (continuando sin equipo)'
                                        )
                                    )

                            # Crear User de Django
                            # Usar email como username (Django requiere username único)
                            django_user = User.objects.create_user(
                                username=user_data['email'],  # Usar email como username
                                email=user_data['email'],
                                password=user_data['password_hash'],  # Django manejará el hash
                                first_name=user_data['first_name'],
                                last_name=user_data['last_name'],
                                is_active=user_data.get('is_active', True),
                                is_staff=False,  # Por defecto no es staff
                                is_superuser=False,  # Por defecto no es superuser
                            )

                            # IMPORTANTE: Actualizar password_hash directamente
                            # Django normalmente hashea la contraseña, pero aquí ya viene hasheada
                            django_user.password = user_data['password_hash']
                            django_user.save(update_fields=['password'])

                            # Actualizar last_login si existe
                            if user_data.get('last_login'):
                                django_user.last_login = user_data['last_login']
                                django_user.save(update_fields=['last_login'])

                            # Crear HpsUserProfile
                            hps_profile = HpsUserProfile.objects.create(
                                user=django_user,
                                role=django_role,
                                team=django_team,
                                email_verified=user_data.get('email_verified', False),
                                is_temp_password=user_data.get('is_temp_password', False),
                                must_change_password=user_data.get('is_temp_password', False),
                                last_login=user_data.get('last_login'),
                            )

                            # Crear entrada en HpsUserMapping
                            HpsUserMapping.objects.create(
                                hps_user_uuid=user_data['id'],
                                django_user=django_user,
                                notes=f'Migrado desde HPS-System el {user_data.get("created_at")}'
                            )

                            migrated += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Migrado usuario: {user_data["email"]} (UUID: {user_data["id"]}) → User ID: {django_user.id}'
                                )
                            )

                        except Exception as e:
                            errors += 1
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ Error con usuario {user_data.get("email", "unknown")}: {str(e)}')
                            )
                            logger.exception(f"Error migrando usuario {user_data.get('email', 'unknown')}")

                self.stdout.write(self.style.SUCCESS(
                    f'\nMigración completada: {migrated} migrados, {skipped} saltados, {errors} errores'
                ))
            else:
                # Dry run: solo mostrar qué se haría
                for user_data in hps_users:
                    exists = User.objects.filter(email=user_data['email']).exists()
                    role_exists = HpsRole.objects.filter(id=user_data['role_id']).exists()
                    team_exists = True
                    if user_data.get('team_id'):
                        team_exists = HpsTeam.objects.filter(id=user_data['team_id']).exists()

                    if exists:
                        self.stdout.write(f'  ⊙ Ya existe: {user_data["email"]}')
                    elif not role_exists:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Rol no existe: role_id={user_data["role_id"]} para {user_data["email"]}')
                        )
                    elif not team_exists:
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠ Equipo no existe: team_id={user_data["team_id"]} para {user_data["email"]}')
                        )
                    else:
                        self.stdout.write(f'  ✓ Se crearía: {user_data["email"]}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error en migración: {str(e)}'))
            logger.exception("Error en migración de usuarios")
            raise
        finally:
            hps_cursor.close()
            hps_conn.close()
            self.stdout.write('Conexión cerrada')

