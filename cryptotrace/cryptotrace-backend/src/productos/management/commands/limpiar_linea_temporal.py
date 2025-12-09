"""
Comando para eliminar todas las entradas de la línea temporal de productos.

Elimina todos los registros de LineaTemporalProducto de la base de datos.
Útil para limpiar datos de prueba o resetear la línea temporal.
"""
from django.core.management.base import BaseCommand
from productos.models import LineaTemporalProducto


class Command(BaseCommand):
    help = 'Elimina todas las entradas de la línea temporal de productos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirmar eliminación sin pedir confirmación interactiva'
        )
        parser.add_argument(
            '--procesados',
            action='store_true',
            help='Eliminar solo los productos procesados'
        )
        parser.add_argument(
            '--no-procesados',
            action='store_true',
            help='Eliminar solo los productos no procesados'
        )

    def handle(self, *args, **options):
        confirm = options['confirm']
        solo_procesados = options['procesados']
        solo_no_procesados = options['no_procesados']

        # Determinar qué productos eliminar
        if solo_procesados and solo_no_procesados:
            self.stdout.write(
                self.style.ERROR('❌ No puedes usar --procesados y --no-procesados al mismo tiempo')
            )
            return

        if solo_procesados:
            queryset = LineaTemporalProducto.objects.filter(procesado=True)
            tipo_eliminacion = "procesados"
        elif solo_no_procesados:
            queryset = LineaTemporalProducto.objects.filter(procesado=False)
            tipo_eliminacion = "no procesados"
        else:
            queryset = LineaTemporalProducto.objects.all()
            tipo_eliminacion = "todos"

        # Contar registros
        total = queryset.count()
        
        if total == 0:
            self.stdout.write(
                self.style.SUCCESS('✓ No hay registros en la línea temporal para eliminar')
            )
            return

        # Mostrar información
        self.stdout.write(
            self.style.WARNING(f'\n⚠️  Se eliminarán {total} registro(s) {tipo_eliminacion} de la línea temporal')
        )

        # Pedir confirmación si no se usa --confirm
        if not confirm:
            respuesta = input('¿Estás seguro de que deseas continuar? (escribe "SI" para confirmar): ')
            if respuesta != 'SI':
                self.stdout.write(
                    self.style.ERROR('❌ Operación cancelada')
                )
                return

        # Eliminar registros
        try:
            eliminados = queryset.delete()
            # delete() devuelve una tupla (número_eliminado, {modelo: número})
            numero_eliminados = eliminados[0]
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Se eliminaron {numero_eliminados} registro(s) de la línea temporal')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al eliminar registros: {str(e)}')
            )

