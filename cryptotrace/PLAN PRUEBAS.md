Pruebas manuales de coherencia y robustez
1. Prepara el entorno
Asegúrate de que la base de datos está vacía o reseteada.
Inicia el backend y el frontend.
Accede a la interfaz de administración o al frontend para crear y consultar datos.
2. Alta de productos por inventario
Crea un producto en el catálogo (si tu flujo lo requiere).
Crea un albarán de tipo INVENTARIO con un producto y un número de serie (ejemplo: P001, S001).
Verifica:
El producto aparece en el inventario con estado activo.
Hay un movimiento de tipo INVENTARIO asociado al albarán y al producto/serie.
3. Alta de AC21 de entrada
Crea un albarán de tipo TRANSFERENCIA, dirección ENTRADA para el mismo producto/serie.
Verifica:
El inventario sigue mostrando el producto como activo.
Hay un nuevo movimiento de tipo TRANSFERENCIA (entrada) para ese producto/serie.
4. Alta de AC21 de salida
Crea un albarán de tipo TRANSFERENCIA, dirección SALIDA para el mismo producto/serie.
Verifica:
El inventario muestra el producto como inactivo.
Hay un nuevo movimiento de tipo TRANSFERENCIA (salida) para ese producto/serie.
5. Borrado de albarán de inventario
Borra el albarán de inventario (el primero que creaste).
Verifica:
Si hay movimientos posteriores (AC21), el inventario no se elimina y el estado se ajusta al último movimiento anterior.
Si no hay movimientos posteriores, el producto desaparece del inventario.
6. Borrado de AC21 de salida
Borra el albarán de AC21 de salida.
Verifica:
El producto vuelve a estado activo en inventario (por el movimiento anterior).
El historial de movimientos refleja correctamente la ausencia del movimiento de salida.
7. Borrado de AC21 de entrada
Borra el albarán de AC21 de entrada.
Verifica:
El producto vuelve a estado activo si hay un movimiento anterior de inventario.
Si no hay movimientos anteriores, el producto queda inactivo o desaparece del inventario.
8. Borrado en cascada y consistencia
Borra todos los albaranes relacionados con el producto/serie.
Verifica:
El producto ya no aparece en el inventario.
No quedan movimientos huérfanos en la base de datos.
9. Prueba con varios productos y series
Repite los pasos anteriores con varios productos y números de serie para comprobar que la lógica es robusta y no hay interferencias entre productos.
10. Auditoría y trazabilidad
Consulta el historial de movimientos de un producto/serie tras varias operaciones.
Verifica que el historial es coherente y refleja todos los cambios realizados.
Consejos
Haz cada operación desde la interfaz de usuario y/o la administración de Django.
Tras cada operación, consulta el inventario y los movimientos para comprobar el estado.
Si tienes endpoints de API, puedes usar herramientas como Postman para hacer las pruebas de forma más controlada.
