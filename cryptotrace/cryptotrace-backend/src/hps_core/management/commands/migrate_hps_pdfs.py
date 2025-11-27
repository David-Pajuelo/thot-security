"""
Script de migración de PDFs desde hps-system a Django.

Migra los PDFs (filled_pdf y response_pdf) de solicitudes HPS desde LargeBinary
a FileField. Este script debe ejecutarse DESPUÉS de migrate_hps_requests.
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.files.base import ContentFile
from django.conf import settings
from pathlib import Path
import hashlib
from hps_core.models import HpsRequest

logger = logging.getLogger(__name__)


def convert_largebinary_to_filefield(hps_binary_data, upload_to_path, filename):
    """
    Convierte un LargeBinary de HPS a FileField de Django.
    
    Args:
        hps_binary_data: bytes - Datos binarios del PDF desde HPS
        upload_to_path: str - Ruta relativa donde guardar (ej: "hps/filled/")
        filename: str - Nombre del archivo
    
    Returns:
        ContentFile - Archivo listo para asignar a FileField
    """
    if not hps_binary_data:
        return None
    
    # Validar que sean datos binarios válidos
    if not isinstance(hps_binary_data, bytes):
        raise ValueError(f"Expected bytes, got {type(hps_binary_data)}")
    
    # Validar que sea un PDF (magic bytes: %PDF)
    if not hps_binary_data.startswith(b'%PDF'):
        raise ValueError("Invalid PDF file: missing PDF header")
    
    # Retornar ContentFile (Django lo guardará automáticamente en MEDIA_ROOT)
    return ContentFile(hps_binary_data, name=f"{upload_to_path}{filename}")


def validate_pdf_integrity(original_binary, saved_file_path):
    """Valida que el PDF migrado sea idéntico al original"""
    if not Path(saved_file_path).exists():
        return False
    
    with open(saved_file_path, 'rb') as f:
        saved_binary = f.read()
    
    # Comparar tamaños
    if len(original_binary) != len(saved_binary):
        return False
    
    # Comparar contenido (hash)
    original_hash = hashlib.md5(original_binary).hexdigest()
    saved_hash = hashlib.md5(saved_binary).hexdigest()
    
    return original_hash == saved_hash


class Command(BaseCommand):
    help = 'Migra PDFs de solicitudes HPS desde LargeBinary a FileField'

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
            default=50,
            help='Tamaño de lote para procesamiento (default: 50, más pequeño por tamaño de PDFs)'
        )
        parser.add_argument(
            '--validate',
            action='store_true',
            help='Validar integridad de PDFs después de migrar'
        )

    def handle(self, *args, **options):
        hps_db_url = options['hps_db_url']
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        validate = options['validate']

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se guardarán cambios'))

        # Verificar espacio en disco
        media_root = Path(settings.MEDIA_ROOT)
        media_root.mkdir(parents=True, exist_ok=True)
        
        # Conectar a base HPS
        try:
            hps_conn = psycopg2.connect(hps_db_url)
            hps_cursor = hps_conn.cursor(cursor_factory=RealDictCursor)
            self.stdout.write(self.style.SUCCESS('✓ Conectado a base HPS'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error conectando a base HPS: {str(e)}'))
            return

        try:
            # Contar solicitudes con PDFs
            hps_cursor.execute("""
                SELECT COUNT(*) as count 
                FROM hps_requests 
                WHERE filled_pdf IS NOT NULL OR response_pdf IS NOT NULL
            """)
            total = hps_cursor.fetchone()['count']
            self.stdout.write(f'Encontradas {total} solicitudes HPS con PDFs en HPS-System')

            if not dry_run:
                migrated_filled = 0
                migrated_response = 0
                skipped = 0
                errors = 0
                offset = 0

                while offset < total:
                    # Obtener lote
                    hps_cursor.execute("""
                        SELECT id, filled_pdf, response_pdf
                        FROM hps_requests
                        WHERE filled_pdf IS NOT NULL OR response_pdf IS NOT NULL
                        ORDER BY created_at
                        LIMIT %s OFFSET %s
                    """, (batch_size, offset))

                    batch = hps_cursor.fetchall()

                    for request_data in batch:
                        try:
                            # Buscar solicitud en Django
                            django_request = HpsRequest.objects.filter(id=request_data['id']).first()
                            
                            if not django_request:
                                skipped += 1
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'  ⊙ Solicitud no encontrada en Django: {request_data["id"]}'
                                    )
                                )
                                continue

                            # Migrar filled_pdf
                            if request_data.get('filled_pdf') and not django_request.filled_pdf:
                                try:
                                    hps_id = str(request_data['id'])
                                    filename_filled = f"hps_request_{hps_id}_filled.pdf"
                                    
                                    pdf_file = convert_largebinary_to_filefield(
                                        hps_binary_data=request_data['filled_pdf'],
                                        upload_to_path="hps/filled/",
                                        filename=filename_filled
                                    )
                                    
                                    django_request.filled_pdf = pdf_file
                                    django_request.save(update_fields=['filled_pdf'])
                                    
                                    # Validar si se solicita
                                    if validate:
                                        file_path = media_root / django_request.filled_pdf.name
                                        if validate_pdf_integrity(request_data['filled_pdf'], file_path):
                                            migrated_filled += 1
                                            self.stdout.write(
                                                self.style.SUCCESS(f'  ✓ Migrado filled_pdf para HPS {hps_id}')
                                            )
                                        else:
                                            errors += 1
                                            self.stdout.write(
                                                self.style.ERROR(f'  ✗ Error de integridad en filled_pdf para HPS {hps_id}')
                                            )
                                    else:
                                        migrated_filled += 1
                                        if migrated_filled % 10 == 0:
                                            self.stdout.write(f'  ... {migrated_filled} filled_pdf migrados')
                                
                                except Exception as e:
                                    errors += 1
                                    self.stdout.write(
                                        self.style.ERROR(f'  ✗ Error migrando filled_pdf para HPS {request_data["id"]}: {str(e)}')
                                    )
                                    logger.exception(f"Error migrando filled_pdf para HPS {request_data['id']}")

                            # Migrar response_pdf
                            if request_data.get('response_pdf') and not django_request.response_pdf:
                                try:
                                    hps_id = str(request_data['id'])
                                    filename_response = f"hps_request_{hps_id}_response.pdf"
                                    
                                    pdf_file = convert_largebinary_to_filefield(
                                        hps_binary_data=request_data['response_pdf'],
                                        upload_to_path="hps/responses/",
                                        filename=filename_response
                                    )
                                    
                                    django_request.response_pdf = pdf_file
                                    django_request.save(update_fields=['response_pdf'])
                                    
                                    # Validar si se solicita
                                    if validate:
                                        file_path = media_root / django_request.response_pdf.name
                                        if validate_pdf_integrity(request_data['response_pdf'], file_path):
                                            migrated_response += 1
                                            self.stdout.write(
                                                self.style.SUCCESS(f'  ✓ Migrado response_pdf para HPS {hps_id}')
                                            )
                                        else:
                                            errors += 1
                                            self.stdout.write(
                                                self.style.ERROR(f'  ✗ Error de integridad en response_pdf para HPS {hps_id}')
                                            )
                                    else:
                                        migrated_response += 1
                                        if migrated_response % 10 == 0:
                                            self.stdout.write(f'  ... {migrated_response} response_pdf migrados')
                                
                                except Exception as e:
                                    errors += 1
                                    self.stdout.write(
                                        self.style.ERROR(f'  ✗ Error migrando response_pdf para HPS {request_data["id"]}: {str(e)}')
                                    )
                                    logger.exception(f"Error migrando response_pdf para HPS {request_data['id']}")

                        except Exception as e:
                            errors += 1
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ Error procesando solicitud {request_data.get("id", "unknown")}: {str(e)}')
                            )
                            logger.exception(f"Error procesando solicitud {request_data.get('id', 'unknown')}")

                    offset += batch_size
                    self.stdout.write(f'Procesado lote: {min(offset, total)}/{total}')

                self.stdout.write(self.style.SUCCESS(
                    f'\nMigración completada:'
                ))
                self.stdout.write(f'  - filled_pdf: {migrated_filled} migrados')
                self.stdout.write(f'  - response_pdf: {migrated_response} migrados')
                self.stdout.write(f'  - Saltados: {skipped}')
                self.stdout.write(f'  - Errores: {errors}')
            else:
                # Dry run: solo mostrar qué se haría
                self.stdout.write(f'Total de solicitudes con PDFs: {total}')
                self.stdout.write('(En dry-run no se muestran detalles individuales)')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error en migración: {str(e)}'))
            logger.exception("Error en migración de PDFs")
            raise
        finally:
            hps_cursor.close()
            hps_conn.close()
            self.stdout.write('Conexión cerrada')

