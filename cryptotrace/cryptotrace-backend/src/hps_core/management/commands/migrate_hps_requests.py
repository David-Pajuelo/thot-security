"""
Script de migración de solicitudes HPS desde hps-system a Django.

Migra solicitudes de la tabla 'hps_requests' de HPS-System a 'hps_core_hpsrequest' de Django.
NOTA: Los PDFs (filled_pdf, response_pdf) se migran en un script separado (migrate_hps_pdfs.py).
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from django.core.management.base import BaseCommand
from django.db import transaction
from hps_core.models import HpsRequest, HpsTemplate, HpsUserMapping

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migra solicitudes HPS de hps-system a Django (sin PDFs)'

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
            default=100,
            help='Tamaño de lote para procesamiento (default: 100)'
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
            hps_cursor.execute("SELECT COUNT(*) as count FROM hps_requests")
            total = hps_cursor.fetchone()['count']
            self.stdout.write(f'Encontradas {total} solicitudes HPS en HPS-System')

            if not dry_run:
                migrated = 0
                skipped = 0
                errors = 0
                offset = 0

                while offset < total:
                    # Obtener lote
                    hps_cursor.execute("""
                        SELECT 
                            id, user_id, request_type, status, type as form_type,
                            template_id, document_type, document_number, birth_date,
                            first_name, first_last_name, second_last_name,
                            nationality, birth_place, email, phone,
                            submitted_by, submitted_at, approved_by, approved_at,
                            expires_at, notes,
                            security_clearance_level, government_expediente,
                            company_name, company_nif, internal_code, job_position,
                            auto_processed, source_pdf_filename, auto_processed_at,
                            government_document_type, data_source, original_status_text,
                            created_at, updated_at
                        FROM hps_requests
                        ORDER BY created_at
                        LIMIT %s OFFSET %s
                    """, (batch_size, offset))

                    batch = hps_cursor.fetchall()

                    with transaction.atomic():
                        for request_data in batch:
                            try:
                                # Verificar si ya existe (por UUID)
                                existing_request = HpsRequest.objects.filter(id=request_data['id']).first()

                                if existing_request:
                                    skipped += 1
                                    if skipped % 100 == 0:
                                        self.stdout.write(f'  ... {skipped} saltadas hasta ahora')
                                    continue

                                # Mapear user_id
                                user_mapping = HpsUserMapping.objects.filter(
                                    hps_user_uuid=request_data['user_id']
                                ).first()

                                if not user_mapping:
                                    self.stdout.write(
                                        self.style.ERROR(
                                            f'  ✗ Usuario no migrado: user_id={request_data["user_id"]} para solicitud {request_data["id"]}'
                                        )
                                    )
                                    errors += 1
                                    continue

                                # Mapear submitted_by
                                submitted_mapping = HpsUserMapping.objects.filter(
                                    hps_user_uuid=request_data['submitted_by']
                                ).first()

                                if not submitted_mapping:
                                    self.stdout.write(
                                        self.style.ERROR(
                                            f'  ✗ Usuario submitted_by no migrado: {request_data["submitted_by"]} para solicitud {request_data["id"]}'
                                        )
                                    )
                                    errors += 1
                                    continue

                                # Mapear approved_by (opcional)
                                approved_mapping = None
                                if request_data.get('approved_by'):
                                    approved_mapping = HpsUserMapping.objects.filter(
                                        hps_user_uuid=request_data['approved_by']
                                    ).first()

                                    if not approved_mapping:
                                        self.stdout.write(
                                            self.style.WARNING(
                                                f'  ⚠ Usuario approved_by no migrado: {request_data["approved_by"]} para solicitud {request_data["id"]} (continuando sin approved_by)'
                                            )
                                        )

                                # Mapear template_id (opcional)
                                django_template = None
                                if request_data.get('template_id'):
                                    try:
                                        django_template = HpsTemplate.objects.get(id=request_data['template_id'])
                                    except HpsTemplate.DoesNotExist:
                                        self.stdout.write(
                                            self.style.WARNING(
                                                f'  ⚠ Plantilla no encontrada: template_id={request_data["template_id"]} para solicitud {request_data["id"]}'
                                            )
                                        )

                                # Crear solicitud en Django (sin PDFs)
                                django_request = HpsRequest.objects.create(
                                    id=request_data['id'],  # Preservar UUID
                                    user=user_mapping.django_user,
                                    request_type=request_data['request_type'],
                                    status=request_data['status'],
                                    form_type=request_data.get('form_type', 'solicitud'),
                                    template=django_template,
                                    # PDFs se migran después
                                    filled_pdf=None,
                                    response_pdf=None,
                                    # Datos personales
                                    document_type=request_data['document_type'],
                                    document_number=request_data['document_number'],
                                    birth_date=request_data['birth_date'],
                                    first_name=request_data['first_name'],
                                    first_last_name=request_data['first_last_name'],
                                    second_last_name=request_data.get('second_last_name') or '',
                                    nationality=request_data['nationality'],
                                    birth_place=request_data['birth_place'],
                                    email=request_data['email'],
                                    phone=request_data['phone'],
                                    # Metadatos
                                    submitted_by=submitted_mapping.django_user,
                                    submitted_at=request_data.get('submitted_at'),
                                    approved_by=approved_mapping.django_user if approved_mapping else None,
                                    approved_at=request_data.get('approved_at'),
                                    expires_at=request_data.get('expires_at'),
                                    notes=request_data.get('notes') or '',
                                    # Campos adicionales
                                    security_clearance_level=request_data.get('security_clearance_level') or '',
                                    government_expediente=request_data.get('government_expediente') or '',
                                    company_name=request_data.get('company_name') or '',
                                    company_nif=request_data.get('company_nif') or '',
                                    internal_code=request_data.get('internal_code') or '',
                                    job_position=request_data.get('job_position') or '',
                                    auto_processed=request_data.get('auto_processed', False),
                                    source_pdf_filename=request_data.get('source_pdf_filename') or '',
                                    auto_processed_at=request_data.get('auto_processed_at'),
                                    government_document_type=request_data.get('government_document_type') or '',
                                    data_source=request_data.get('data_source', 'manual'),
                                    original_status_text=request_data.get('original_status_text') or '',
                                )

                                migrated += 1
                                if migrated % 100 == 0:
                                    self.stdout.write(f'  ... {migrated} migradas hasta ahora')

                            except Exception as e:
                                errors += 1
                                self.stdout.write(
                                    self.style.ERROR(f'  ✗ Error con solicitud {request_data.get("id", "unknown")}: {str(e)}')
                                )
                                logger.exception(f"Error migrando solicitud {request_data.get('id', 'unknown')}")

                    offset += batch_size
                    self.stdout.write(f'Procesado lote: {min(offset, total)}/{total}')

                self.stdout.write(self.style.SUCCESS(
                    f'\nMigración completada: {migrated} migradas, {skipped} saltadas, {errors} errores'
                ))
                self.stdout.write(self.style.WARNING(
                    '⚠ NOTA: Los PDFs se migrarán con el comando migrate_hps_pdfs'
                ))
            else:
                # Dry run: solo mostrar qué se haría
                hps_cursor.execute("SELECT COUNT(*) as count FROM hps_requests")
                total = hps_cursor.fetchone()['count']
                self.stdout.write(f'Total de solicitudes: {total}')
                self.stdout.write('(En dry-run no se muestran detalles individuales)')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error en migración: {str(e)}'))
            logger.exception("Error en migración de solicitudes HPS")
            raise
        finally:
            hps_cursor.close()
            hps_conn.close()
            self.stdout.write('Conexión cerrada')

