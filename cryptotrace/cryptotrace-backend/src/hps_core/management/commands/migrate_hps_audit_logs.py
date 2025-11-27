"""
Script de migración de logs de auditoría desde hps-system a Django.

Migra logs de la tabla 'audit_logs' de HPS-System a 'hps_core_hpsauditlog' de Django.
Requiere que los usuarios ya estén migrados para mapear user_id.
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from django.core.management.base import BaseCommand
from django.db import transaction
from hps_core.models import HpsAuditLog, HpsUserMapping

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migra logs de auditoría de hps-system a Django'

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
            '--batch-size',
            type=int,
            default=500,
            help='Tamaño de lote para procesamiento (default: 500)'
        )

    def handle(self, *args, **options):
        hps_db_url = options['hps_db_url']
        dry_run = options['dry_run']
        batch_size = options['batch_size']

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
            # Contar total
            hps_cursor.execute("SELECT COUNT(*) as count FROM audit_logs")
            total = hps_cursor.fetchone()['count']
            self.stdout.write(f'Encontrados {total} logs de auditoría en HPS-System')

            if not dry_run:
                migrated = 0
                skipped = 0
                errors = 0
                offset = 0

                while offset < total:
                    # Obtener lote
                    hps_cursor.execute("""
                        SELECT 
                            id, user_id, action, table_name, record_id,
                            old_values, new_values, ip_address, user_agent, created_at
                        FROM audit_logs
                        ORDER BY created_at
                        LIMIT %s OFFSET %s
                    """, (batch_size, offset))

                    batch = hps_cursor.fetchall()

                    with transaction.atomic():
                        for log_data in batch:
                            try:
                                # Verificar si ya existe (por UUID)
                                existing_log = HpsAuditLog.objects.filter(id=log_data['id']).first()

                                if existing_log:
                                    skipped += 1
                                    if skipped % 100 == 0:
                                        self.stdout.write(f'  ... {skipped} saltados hasta ahora')
                                    continue

                                # Mapear user_id (opcional, puede ser NULL)
                                django_user = None
                                if log_data.get('user_id'):
                                    user_mapping = HpsUserMapping.objects.filter(
                                        hps_user_uuid=log_data['user_id']
                                    ).first()

                                    if user_mapping:
                                        django_user = user_mapping.django_user
                                    else:
                                        # Si el usuario no está migrado, continuar sin user
                                        pass

                                # Crear log en Django
                                django_log = HpsAuditLog.objects.create(
                                    id=log_data['id'],  # Preservar UUID
                                    user=django_user,
                                    action=log_data['action'],
                                    table_name=log_data.get('table_name') or '',
                                    record_id=log_data.get('record_id'),
                                    old_values=log_data.get('old_values'),
                                    new_values=log_data.get('new_values'),
                                    ip_address=log_data.get('ip_address'),
                                    user_agent=log_data.get('user_agent') or '',
                                )

                                migrated += 1
                                if migrated % 100 == 0:
                                    self.stdout.write(f'  ... {migrated} migrados hasta ahora')

                            except Exception as e:
                                errors += 1
                                self.stdout.write(
                                    self.style.ERROR(f'  ✗ Error con log {log_data.get("id", "unknown")}: {str(e)}')
                                )
                                logger.exception(f"Error migrando log {log_data.get('id', 'unknown')}")

                    offset += batch_size
                    self.stdout.write(f'Procesado lote: {min(offset, total)}/{total}')

                self.stdout.write(self.style.SUCCESS(
                    f'\nMigración completada: {migrated} migrados, {skipped} saltados, {errors} errores'
                ))
            else:
                # Dry run: solo mostrar qué se haría
                self.stdout.write(f'Total de logs: {total}')
                self.stdout.write('(En dry-run no se muestran detalles individuales)')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error en migración: {str(e)}'))
            logger.exception("Error en migración de logs de auditoría")
            raise
        finally:
            hps_cursor.close()
            hps_conn.close()
            self.stdout.write('Conexión cerrada')

