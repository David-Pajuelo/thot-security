"""
Script de migración de plantillas desde hps-system a Django.

Migra plantillas de la tabla 'hps_templates' de HPS-System a 'hps_core_hpstemplate' de Django.
Incluye conversión de PDFs de LargeBinary a FileField.
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.files.base import ContentFile
from django.conf import settings
from pathlib import Path
from hps_core.models import HpsTemplate

logger = logging.getLogger(__name__)


def convert_largebinary_to_filefield(hps_binary_data, upload_to_path, filename):
    """
    Convierte un LargeBinary de HPS a FileField de Django.
    
    Args:
        hps_binary_data: bytes - Datos binarios del PDF desde HPS
        upload_to_path: str - Ruta relativa donde guardar (ej: "hps/templates/")
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
    
    # Crear directorio si no existe
    media_root = Path(settings.MEDIA_ROOT)
    target_dir = media_root / upload_to_path
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Retornar ContentFile (Django lo guardará automáticamente)
    return ContentFile(hps_binary_data, name=filename)


class Command(BaseCommand):
    help = 'Migra plantillas de hps-system a Django'

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
            # Obtener plantillas de HPS
            hps_cursor.execute("""
                SELECT id, name, description, template_pdf, template_type, version, active, created_at, updated_at
                FROM hps_templates
                ORDER BY id
            """)
            hps_templates = hps_cursor.fetchall()

            self.stdout.write(f'Encontradas {len(hps_templates)} plantillas en HPS-System')

            if not dry_run:
                migrated = 0
                skipped = 0
                errors = 0

                with transaction.atomic():
                    for template in hps_templates:
                        try:
                            # Verificar si ya existe (por ID)
                            existing_template = HpsTemplate.objects.filter(id=template['id']).first()

                            if existing_template:
                                skipped += 1
                                self.stdout.write(
                                    self.style.WARNING(f'  ⊙ Plantilla ya existe: {template["name"]} (ID: {template["id"]})')
                                )
                                continue

                            # Convertir PDF de LargeBinary a FileField
                            pdf_file = None
                            if template.get('template_pdf'):
                                try:
                                    filename = f"template_{template['id']}_{template['name'].replace(' ', '_')}.pdf"
                                    pdf_file = convert_largebinary_to_filefield(
                                        hps_binary_data=template['template_pdf'],
                                        upload_to_path="hps/templates/",
                                        filename=filename
                                    )
                                except Exception as e:
                                    self.stdout.write(
                                        self.style.ERROR(f'  ✗ Error convirtiendo PDF para plantilla {template["name"]}: {str(e)}')
                                    )
                                    errors += 1
                                    continue

                            # Crear plantilla en Django
                            django_template = HpsTemplate.objects.create(
                                id=template['id'],  # Preservar ID
                                name=template['name'],
                                description=template['description'] or '',
                                template_pdf=pdf_file,
                                template_type=template['template_type'],
                                version=template.get('version', '1.0'),
                                active=template.get('active', True),
                            )

                            migrated += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Migrada plantilla: {template["name"]} v{template.get("version", "1.0")} (ID: {template["id"]})'
                                )
                            )

                        except Exception as e:
                            errors += 1
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ Error con plantilla {template["name"]}: {str(e)}')
                            )
                            logger.exception(f"Error migrando plantilla {template['name']}")

                self.stdout.write(self.style.SUCCESS(
                    f'\nMigración completada: {migrated} migradas, {skipped} ya existían, {errors} errores'
                ))
            else:
                # Dry run: solo mostrar qué se haría
                for template in hps_templates:
                    exists = HpsTemplate.objects.filter(id=template['id']).exists()
                    has_pdf = bool(template.get('template_pdf'))

                    if exists:
                        self.stdout.write(f'  ⊙ Ya existe: {template["name"]} (ID: {template["id"]})')
                    else:
                        pdf_status = "con PDF" if has_pdf else "sin PDF"
                        self.stdout.write(f'  ✓ Se crearía: {template["name"]} v{template.get("version", "1.0")} ({pdf_status})')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error en migración: {str(e)}'))
            logger.exception("Error en migración de plantillas")
            raise
        finally:
            hps_cursor.close()
            hps_conn.close()
            self.stdout.write('Conexión cerrada')

