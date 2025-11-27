from django.core.management.base import BaseCommand
from productos.models import CatalogoProducto, MovimientoProducto

class Command(BaseCommand):
    help = 'Revisa y reporta productos en el catálogo que fueron creados sin tipo asignado'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mostrar-movimientos',
            action='store_true',
            help='Muestra también los movimientos asociados a cada producto sin tipo',
        )
        parser.add_argument(
            '--limite',
            type=int,
            default=50,
            help='Límite de productos a mostrar (default: 50)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🔍 Revisando productos sin tipo asignado...'))
        
        # Buscar productos sin tipo
        productos_sin_tipo = CatalogoProducto.objects.filter(tipo__isnull=True)
        total = productos_sin_tipo.count()
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ No hay productos sin tipo en el catálogo'))
            return
        
        self.stdout.write(
            self.style.WARNING(f'⚠️  Encontrados {total} productos sin tipo asignado')
        )
        
        # Mostrar productos limitados
        limite = options['limite']
        productos_a_mostrar = productos_sin_tipo[:limite]
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write('PRODUCTOS SIN TIPO:')
        self.stdout.write('='*80)
        
        for producto in productos_a_mostrar:
            self.stdout.write(f'\n📦 ID: {producto.id}')
            self.stdout.write(f'   Código: {producto.codigo_producto}')
            self.stdout.write(f'   Descripción: {producto.descripcion}')
            self.stdout.write(f'   Creado: {producto.ultima_actualizacion}')
            
            if options['mostrar_movimientos']:
                movimientos = MovimientoProducto.objects.filter(producto=producto)
                if movimientos.exists():
                    self.stdout.write('   Movimientos:')
                    for mov in movimientos[:3]:  # Solo mostrar los primeros 3
                        self.stdout.write(f'     - Albarán: {mov.albaran.numero} ({mov.fecha})')
                    if movimientos.count() > 3:
                        self.stdout.write(f'     ... y {movimientos.count() - 3} más')
                else:
                    self.stdout.write('   Sin movimientos asociados')
        
        if total > limite:
            self.stdout.write(f'\n... y {total - limite} productos más (usa --limite para ver más)')
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write(
            self.style.WARNING(
                f'💡 Tip: Puedes asignar tipos a estos productos desde el panel de administración '
                f'o mediante la gestión temporal de productos'
            )
        ) 