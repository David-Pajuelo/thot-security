"""
Comando para vaciar inventario y catálogo (y opcionalmente albaranes y línea temporal).
Útil en VPS o local para dejar la base de datos a cero y hacer pruebas.

Orden de borrado por dependencias FK:
  MovimientoProducto → InventarioProducto → CatalogoProducto
Opcional: Albaran, LineaTemporalProducto (con flags).
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from productos.models import (
    MovimientoProducto,
    InventarioProducto,
    CatalogoProducto,
    Albaran,
    LineaTemporalProducto,
)


class Command(BaseCommand):
    help = 'Vacía inventario y catálogo (y opcionalmente albaranes y línea temporal) para pruebas desde cero'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirmar sin pedir confirmación interactiva',
        )
        parser.add_argument(
            '--albaranes',
            action='store_true',
            help='Borrar también todos los albaranes',
        )
        parser.add_argument(
            '--linea-temporal',
            action='store_true',
            help='Borrar también la línea temporal de productos',
        )

    def handle(self, *args, **options):
        confirm = options['confirm']
        borrar_albaranes = options['albaranes']
        borrar_linea_temporal = options['linea_temporal']

        with transaction.atomic():
            counts = {}
            # Orden por FKs: movimientos → inventario → catálogo
            counts['MovimientoProducto'] = MovimientoProducto.objects.count()
            counts['InventarioProducto'] = InventarioProducto.objects.count()
            counts['CatalogoProducto'] = CatalogoProducto.objects.count()
            if borrar_albaranes:
                counts['Albaran'] = Albaran.objects.count()
            if borrar_linea_temporal:
                counts['LineaTemporalProducto'] = LineaTemporalProducto.objects.count()

            total = sum(counts.values())
            if total == 0:
                self.stdout.write(self.style.SUCCESS('No hay datos que borrar.'))
                return

            self.stdout.write(self.style.WARNING('\nSe borrará:'))
            for model_name, n in counts.items():
                if n:
                    self.stdout.write(f'  - {model_name}: {n} registro(s)')
            if borrar_albaranes:
                self.stdout.write('  (incluye albaranes)')
            if borrar_linea_temporal:
                self.stdout.write('  (incluye línea temporal)')

            if not confirm:
                r = input('\n¿Continuar? Escribe "SI" para confirmar: ')
                if r != 'SI':
                    self.stdout.write(self.style.ERROR('Cancelado.'))
                    return

            # Borrar en orden (por FKs: movimientos → inventario → catálogo → albaranes)
            MovimientoProducto.objects.all().delete()
            InventarioProducto.objects.all().delete()
            CatalogoProducto.objects.all().delete()
            if borrar_albaranes:
                deleted_alb, _ = Albaran.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'Albaranes borrados: {deleted_alb}'))
            if borrar_linea_temporal:
                deleted_lt, _ = LineaTemporalProducto.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'Línea temporal borrada: {deleted_lt} registros'))

            self.stdout.write(self.style.SUCCESS('Inventario y catálogo vaciados correctamente.'))
