"""
Script de migración de tokens desde hps-system a Django.

Migra tokens de la tabla 'hps_tokens' de HPS-System a 'hps_core_hpstoken' de Django.
Requiere que los usuarios ya estén migrados para mapear requested_by.
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from django.core.management.base import BaseCommand
from django.db import transaction
from hps_core.models import HpsToken, HpsUserMapping

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migra tokens de hps-system a Django'

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
            # Obtener tokens de HPS
            hps_cursor.execute("""
                SELECT 
                    id, token, email, requested_by, purpose,
                    is_used, used_at, expires_at, created_at, updated_at
                FROM hps_tokens
                ORDER BY created_at
            """)
            hps_tokens = hps_cursor.fetchall()

            self.stdout.write(f'Encontrados {len(hps_tokens)} tokens en HPS-System')

            if not dry_run:
                migrated = 0
                skipped = 0
                errors = 0

                with transaction.atomic():
                    for token_data in hps_tokens:
                        try:
                            # Verificar si ya existe (por UUID o token)
                            existing_token = HpsToken.objects.filter(
                                id=token_data['id']
                            ).first()

                            if existing_token:
                                skipped += 1
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'  ⊙ Token ya existe: {token_data["email"]} (UUID: {token_data["id"]})'
                                    )
                                )
                                continue

                            # Verificar que el token no esté duplicado por valor
                            existing_by_token = HpsToken.objects.filter(
                                token=token_data['token']
                            ).first()

                            if existing_by_token:
                                skipped += 1
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'  ⊙ Token duplicado (valor): {token_data["token"][:20]}... (saltado)'
                                    )
                                )
                                continue

                            # Buscar mapeo de usuario (requested_by)
                            user_mapping = HpsUserMapping.objects.filter(
                                hps_user_uuid=token_data['requested_by']
                            ).first()

                            if not user_mapping:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f'  ✗ Usuario no migrado: requested_by={token_data["requested_by"]} para token {token_data["email"]}'
                                    )
                                )
                                errors += 1
                                continue

                            # Crear token en Django
                            django_token = HpsToken.objects.create(
                                id=token_data['id'],  # Preservar UUID
                                token=token_data['token'],  # Preservar token exacto
                                email=token_data['email'],
                                requested_by=user_mapping.django_user,
                                purpose=token_data.get('purpose') or '',
                                is_used=token_data.get('is_used', False),
                                used_at=token_data.get('used_at'),
                                expires_at=token_data['expires_at'],
                            )

                            migrated += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Migrado token: {token_data["email"]} (UUID: {token_data["id"]})'
                                )
                            )

                        except Exception as e:
                            errors += 1
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ Error con token {token_data.get("email", "unknown")}: {str(e)}')
                            )
                            logger.exception(f"Error migrando token {token_data.get('email', 'unknown')}")

                self.stdout.write(self.style.SUCCESS(
                    f'\nMigración completada: {migrated} migrados, {skipped} saltados, {errors} errores'
                ))
            else:
                # Dry run: solo mostrar qué se haría
                for token_data in hps_tokens:
                    exists = HpsToken.objects.filter(id=token_data['id']).exists()
                    user_mapping = HpsUserMapping.objects.filter(
                        hps_user_uuid=token_data['requested_by']
                    ).first()

                    if exists:
                        self.stdout.write(f'  ⊙ Ya existe: {token_data["email"]} (UUID: {token_data["id"]})')
                    elif not user_mapping:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Usuario no migrado: {token_data["requested_by"]} para {token_data["email"]}')
                        )
                    else:
                        self.stdout.write(f'  ✓ Se crearía: {token_data["email"]}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error en migración: {str(e)}'))
            logger.exception("Error en migración de tokens")
            raise
        finally:
            hps_cursor.close()
            hps_conn.close()
            self.stdout.write('Conexión cerrada')

