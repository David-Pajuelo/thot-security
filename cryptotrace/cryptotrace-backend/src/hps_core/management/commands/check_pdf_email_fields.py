"""
Comando para verificar qué campos del PDF se están rellenando con el email
"""
from django.core.management.base import BaseCommand
from hps_core.models import HpsRequest
import fitz  # PyMuPDF
import os


class Command(BaseCommand):
    help = 'Verificar qué campos del PDF se están rellenando con el email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--request-id',
            type=str,
            help='ID de la solicitud HPS a verificar',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Verificar todas las solicitudes con PDF rellenado',
        )

    def handle(self, *args, **options):
        if options['request_id']:
            requests = HpsRequest.objects.filter(id=options['request_id'])
        elif options['all']:
            requests = HpsRequest.objects.exclude(filled_pdf='').filter(form_type='traslado')[:10]
        else:
            # Por defecto, la última solicitud de traspaso con PDF rellenado
            requests = HpsRequest.objects.exclude(filled_pdf='').filter(form_type='traslado').order_by('-created_at')[:1]
        
        for hps_request in requests:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Solicitud HPS ID: {hps_request.id}")
            self.stdout.write(f"Email: {hps_request.email}")
            self.stdout.write(f"Tipo: {hps_request.form_type}")
            self.stdout.write(f"{'='*60}\n")
            
            if not hps_request.filled_pdf:
                self.stdout.write(self.style.WARNING("No hay PDF rellenado para esta solicitud"))
                continue
            
            try:
                pdf_path = hps_request.filled_pdf.path
                if not os.path.exists(pdf_path):
                    self.stdout.write(self.style.ERROR(f"Archivo PDF no encontrado: {pdf_path}"))
                    continue
                
                pdf_document = fitz.open(pdf_path)
                page = pdf_document[0]
                widgets = page.widgets()
                
                self.stdout.write(f"\nCampos del PDF rellenados con el email '{hps_request.email}':\n")
                
                email_fields = []
                for widget in widgets:
                    if widget.field_name and widget.field_value:
                        widget_value = str(widget.field_value).strip()
                        # Verificar si el valor del campo contiene el email
                        if hps_request.email.lower() in widget_value.lower() or widget_value.lower() in hps_request.email.lower():
                            email_fields.append({
                                'field_name': widget.field_name,
                                'field_value': widget_value,
                                'field_type': widget.field_type_string
                            })
                            self.stdout.write(f"  - Campo: '{widget.field_name}'")
                            self.stdout.write(f"    Valor: '{widget_value}'")
                            self.stdout.write(f"    Tipo: {widget.field_type_string}")
                            self.stdout.write("")
                
                if not email_fields:
                    self.stdout.write(self.style.WARNING("  No se encontraron campos con el email"))
                else:
                    self.stdout.write(f"\nTotal de campos con email: {len(email_fields)}")
                    self.stdout.write(f"\nNombres de campos:")
                    for field in email_fields:
                        self.stdout.write(f"  - {field['field_name']}")
                
                pdf_document.close()
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error procesando PDF: {e}"))
                import traceback
                self.stdout.write(traceback.format_exc())

