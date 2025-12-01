"""
Comando de gestión para corregir form_type de solicitudes HPS
"""
from django.core.management.base import BaseCommand
from hps_core.models import HpsRequest


class Command(BaseCommand):
    help = 'Corregir form_type de una solicitud HPS específica'

    def add_arguments(self, parser):
        parser.add_argument(
            '--request-id',
            type=str,
            help='ID de la solicitud HPS a corregir',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email del usuario para buscar la solicitud',
        )
        parser.add_argument(
            '--form-type',
            type=str,
            default='solicitud',
            choices=['solicitud', 'traslado'],
            help='Nuevo form_type (solicitud o traslado)',
        )

    def handle(self, *args, **options):
        request_id = options.get('request_id')
        email = options.get('email')
        form_type = options.get('form_type', 'solicitud')

        if request_id:
            try:
                request = HpsRequest.objects.get(id=request_id)
            except HpsRequest.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'No se encontró solicitud con ID: {request_id}'))
                return
        elif email:
            request = HpsRequest.objects.filter(email=email).order_by('-created_at').first()
            if not request:
                self.stdout.write(self.style.ERROR(f'No se encontró solicitud para email: {email}'))
                return
        else:
            self.stdout.write(self.style.ERROR('Debe proporcionar --request-id o --email'))
            return

        old_form_type = request.form_type
        request.form_type = HpsRequest.FormType.SOLICITUD if form_type == 'solicitud' else HpsRequest.FormType.TRASLADO
        request.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Solicitud actualizada:\n'
                f'  ID: {request.id}\n'
                f'  Email: {request.email}\n'
                f'  Nombre: {request.first_name} {request.first_last_name}\n'
                f'  form_type: {old_form_type} → {request.form_type}'
            )
        )

