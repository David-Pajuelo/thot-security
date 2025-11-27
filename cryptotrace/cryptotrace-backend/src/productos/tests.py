from django.test import TestCase
from django.utils import timezone
from .models import CatalogoProducto, Albaran, MovimientoProducto, InventarioProducto, Empresa, User

class InventarioRecalculoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='tester')
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test', direccion='Calle Falsa 123', ciudad='Ciudad', codigo_postal='00000', provincia='Provincia')
        self.producto = CatalogoProducto.objects.create(codigo_producto='P001', descripcion='Producto Test')

    def crear_albaran_inventario(self):
        albaran = Albaran.objects.create(
            numero='A001',
            tipo_documento='INVENTARIO',
            fecha=timezone.now(),
            created_by=self.user,
            updated_by=self.user
        )
        MovimientoProducto.objects.create(
            albaran=albaran,
            producto=self.producto,
            numero_serie='S001',
            tipo_movimiento='INVENTARIO',
            estado_anterior='inactivo',
            estado_nuevo='activo'
        )
        return albaran

    def crear_ac21_entrada(self):
        albaran = Albaran.objects.create(
            numero='A002',
            tipo_documento='TRANSFERENCIA',
            direccion_transferencia='ENTRADA',
            fecha=timezone.now(),
            created_by=self.user,
            updated_by=self.user
        )
        MovimientoProducto.objects.create(
            albaran=albaran,
            producto=self.producto,
            numero_serie='S001',
            tipo_movimiento='TRANSFERENCIA',
            estado_anterior='inactivo',
            estado_nuevo='activo'
        )
        return albaran

    def crear_ac21_salida(self):
        albaran = Albaran.objects.create(
            numero='A003',
            tipo_documento='TRANSFERENCIA',
            direccion_transferencia='SALIDA',
            fecha=timezone.now(),
            created_by=self.user,
            updated_by=self.user
        )
        MovimientoProducto.objects.create(
            albaran=albaran,
            producto=self.producto,
            numero_serie='S001',
            tipo_movimiento='TRANSFERENCIA',
            estado_anterior='activo',
            estado_nuevo='inactivo'
        )
        return albaran

    def test_borrado_albaran_inventario_elimina_inventario(self):
        albaran = self.crear_albaran_inventario()
        self.assertTrue(InventarioProducto.objects.filter(producto=self.producto, numero_serie='S001').exists())
        albaran.delete()
        self.assertFalse(InventarioProducto.objects.filter(producto=self.producto, numero_serie='S001').exists())

    def test_borrado_ac21_entrada_pone_inactivo(self):
        self.crear_albaran_inventario()
        albaran = self.crear_ac21_entrada()
        inv = InventarioProducto.objects.get(producto=self.producto, numero_serie='S001')
        self.assertEqual(inv.estado, 'activo')
        albaran.delete()
        inv.refresh_from_db()
        self.assertEqual(inv.estado, 'activo')

    def test_borrado_ac21_salida_pone_activo(self):
        self.crear_albaran_inventario()
        self.crear_ac21_entrada()
        albaran = self.crear_ac21_salida()
        inv = InventarioProducto.objects.get(producto=self.producto, numero_serie='S001')
        self.assertEqual(inv.estado, 'inactivo')
        albaran.delete()
        inv.refresh_from_db()
        self.assertEqual(inv.estado, 'activo')

    def test_borrado_intermedio_restaurar_estado(self):
        albaran1 = self.crear_albaran_inventario()
        albaran2 = self.crear_ac21_entrada()
        albaran3 = self.crear_ac21_salida()
        inv = InventarioProducto.objects.get(producto=self.producto, numero_serie='S001')
        self.assertEqual(inv.estado, 'inactivo')
        albaran3.delete()  # Borro salida, debe volver a activo
        inv.refresh_from_db()
        self.assertEqual(inv.estado, 'activo')
        albaran2.delete()  # Borro entrada, debe volver a activo (por el inventario)
        inv.refresh_from_db()
        self.assertEqual(inv.estado, 'activo')
        albaran1.delete()  # Borro inventario, debe eliminar inventario
        self.assertFalse(InventarioProducto.objects.filter(producto=self.producto, numero_serie='S001').exists())
