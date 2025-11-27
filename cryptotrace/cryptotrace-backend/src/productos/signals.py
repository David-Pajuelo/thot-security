from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Albaran, MovimientoProducto, InventarioProducto, UserProfile

@receiver(pre_delete, sender=Albaran)
def recalcular_inventario_al_borrar_albaran(sender, instance, **kwargs):
    movimientos = list(MovimientoProducto.objects.filter(albaran=instance))
    for mov in movimientos:
        producto = mov.producto
        numero_serie = mov.numero_serie
        # Buscar movimientos anteriores a este albarán para este producto/serie
        movimientos_anteriores = MovimientoProducto.objects.filter(
            producto=producto,
            numero_serie=numero_serie
        ).exclude(albaran=instance).order_by('-fecha')
        inventario = InventarioProducto.objects.filter(producto=producto, numero_serie=numero_serie).first()
        if instance.tipo_documento == 'INVENTARIO':
            # Si no hay movimientos anteriores, eliminar del inventario
            if not movimientos_anteriores.exists():
                if inventario:
                    inventario.delete()
            else:
                mov_ant = movimientos_anteriores.first()
                if inventario:
                    inventario.estado = mov_ant.estado_nuevo
                    inventario.ultimo_movimiento = mov_ant
                    inventario.ultima_actualizacion = timezone.now()
                    inventario.save()
        elif instance.tipo_documento == 'TRANSFERENCIA':
            if instance.direccion_transferencia == 'ENTRADA':
                # AC21 de entrada: restaurar estado anterior o poner inactivo
                if movimientos_anteriores.exists():
                    mov_ant = movimientos_anteriores.first()
                    if inventario:
                        inventario.estado = mov_ant.estado_nuevo
                        inventario.ultimo_movimiento = mov_ant
                        inventario.ultima_actualizacion = timezone.now()
                        inventario.save()
                else:
                    if inventario:
                        inventario.estado = 'inactivo'
                        inventario.ultimo_movimiento = None
                        inventario.ultima_actualizacion = timezone.now()
                        inventario.save()
            elif instance.direccion_transferencia == 'SALIDA':
                # AC21 de salida: restaurar estado anterior o poner activo
                if movimientos_anteriores.exists():
                    mov_ant = movimientos_anteriores.first()
                    if inventario:
                        inventario.estado = mov_ant.estado_nuevo
                        inventario.ultimo_movimiento = mov_ant
                        inventario.ultima_actualizacion = timezone.now()
                        inventario.save()
                else:
                    if inventario:
                        inventario.estado = 'activo'
                        inventario.ultimo_movimiento = None
                        inventario.ultima_actualizacion = timezone.now()
                        inventario.save()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crear automáticamente un UserProfile cuando se crea un nuevo usuario
    """
    if created:
        UserProfile.objects.get_or_create(user=instance, defaults={'must_change_password': True}) 