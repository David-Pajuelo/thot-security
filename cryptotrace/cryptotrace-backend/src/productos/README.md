# Recalculo de Inventario al Borrar Albaranes y AC21

## Comportamiento implementado

Cuando se borra un albarán (tradicional o AC21), la plataforma recalcula automáticamente el estado del inventario para todos los productos afectados, siguiendo estas reglas:

### 1. Albarán tradicional (tipo INVENTARIO)
- Si el producto/número de serie **no tiene movimientos anteriores**, se elimina del inventario.
- Si **hay movimientos anteriores**, el inventario se restaura al estado y último movimiento anterior.

### 2. AC21 de ENTRADA (tipo_documento='TRANSFERENCIA', direccion_transferencia='ENTRADA')
- Si **hay movimientos anteriores**, el inventario se restaura al estado anterior.
- Si **no hay movimientos anteriores**, el producto queda en estado "inactivo" (fuera de custodia).

### 3. AC21 de SALIDA (tipo_documento='TRANSFERENCIA', direccion_transferencia='SALIDA')
- Si **hay movimientos anteriores**, el inventario se restaura al estado anterior.
- Si **no hay movimientos anteriores**, el producto queda en estado "activo" (en custodia).

## Trazabilidad
- El sistema siempre restaura el estado del inventario según el último movimiento anterior al albarán borrado, garantizando la integridad histórica.

## Tests automáticos
Se han implementado tests automáticos en `productos/tests.py` que cubren:
- Borrado de albarán de inventario (elimina el producto del inventario si no hay movimientos posteriores).
- Borrado de AC21 de entrada y salida (restaura el estado correcto según el historial).
- Borrado intermedio (con varios movimientos): el estado del inventario se restaura correctamente según el último movimiento anterior.

Para ejecutar los tests:

```bash
python manage.py test productos
```

## Notas
- El recálculo se realiza mediante una señal `pre_delete` de Django, por lo que funciona tanto al borrar desde la API como desde el código o en tests.
- Si necesitas añadir más reglas de negocio, modifica la señal en `productos/signals.py`. 