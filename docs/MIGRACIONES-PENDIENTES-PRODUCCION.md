# Migraciones Pendientes para Producción

## Resumen

Este documento lista las migraciones que se han creado en desarrollo local y que deben aplicarse en producción (VPS) cuando se despliegue.

**Última actualización:** 2026-01-26

---

## Migraciones Pendientes

### 1. `0033_remove_catalogoproducto_tipo_cryptocustodio`

**Fecha:** 2026-01-26  
**Archivo:** `cryptotrace/cryptotrace-backend/src/productos/migrations/0033_remove_catalogoproducto_tipo_cryptocustodio.py`

**Descripción:**
- Elimina el campo `tipo_cryptocustodio` de la tabla `productos_catalogoproducto`
- Este campo era obsoleto y causaba errores en el admin de Django

**Operaciones:**
```python
migrations.RemoveField(
    model_name='catalogoproducto',
    name='tipo_cryptocustodio',
)
```

**Impacto:**
- ⚠️ **DESTRUCTIVA**: Elimina una columna de la base de datos
- No afecta datos existentes si el campo no se estaba usando
- Resuelve errores de `ProgrammingError` en el admin

---

### 2. `0034_replace_cc_with_tipo_producto`

**Fecha:** 2026-01-26  
**Archivo:** `cryptotrace/cryptotrace-backend/src/productos/migrations/0034_replace_cc_with_tipo_producto.py`

**Descripción:**
- Elimina el campo `cc` de `LineaTemporalProducto`
- Añade el campo `tipo_producto` (ForeignKey a `TipoProducto`) en `LineaTemporalProducto`
- Actualiza el `help_text` de `datos_adicionales` para clarificar que el CC del OCR se guarda ahí

**Operaciones:**
```python
migrations.RemoveField(
    model_name='lineatemporalproducto',
    name='cc',
),
migrations.AddField(
    model_name='lineatemporalproducto',
    name='tipo_producto',
    field=models.ForeignKey(
        blank=True,
        help_text='Tipo de cryptocustodio para tipificación de la línea temporal',
        null=True,
        on_delete=django.db.models.deletion.SET_NULL,
        to='productos.tipoproducto'
    ),
),
migrations.AlterField(
    model_name='lineatemporalproducto',
    name='datos_adicionales',
    field=models.JSONField(
        blank=True,
        default=dict,
        help_text='Información adicional del AC21 (cabecera, empresas, firmas, cc del OCR, etc.)',
        null=True
    ),
),
```

**Impacto:**
- ⚠️ **DESTRUCTIVA**: Elimina la columna `cc` de `productos_lineatemporalproducto`
- ✅ **ADITIVA**: Añade columna `tipo_producto_id` (ForeignKey)
- Cambia la estructura de datos para separar CC del OCR (informativo) de TipoProducto (clasificación)

**Nota importante:**
- El CC del OCR ahora se guarda en `datos_adicionales['cc']` (JSONField)
- El `tipo_producto` se usa para tipificación/clasificación de productos

---

### 3. `0035_allow_null_cc_in_movimiento`

**Fecha:** 2026-01-26  
**Archivo:** `cryptotrace/cryptotrace-backend/src/productos/migrations/0035_allow_null_cc_in_movimiento.py`

**Descripción:**
- Permite valores `NULL` en el campo `cc` de `MovimientoProducto`
- Actualiza el `help_text` para clarificar que es un campo informativo del AC21 que puede estar vacío

**Operaciones:**
```python
migrations.AlterField(
    model_name='movimientoproducto',
    name='cc',
    field=models.IntegerField(
        blank=True,
        help_text='Campo CC del AC-21 (Accounting Legend Code) - Informativo del documento, puede estar vacío',
        null=True
    ),
),
```

**Impacto:**
- ✅ **NO DESTRUCTIVA**: Solo modifica la definición del campo
- Permite que `cc` sea `NULL` cuando el OCR no proporciona valor
- Los valores existentes (1, 2, 3) se mantienen
- Resuelve el problema de que el sistema asignaba "1" automáticamente cuando el OCR devolvía CC vacío

**Nota importante:**
- Este cambio respeta el vacío del CC del OCR
- El campo `cc` en `MovimientoProducto` es **informativo** (diferente de `TipoProducto`)

---

## Orden de Aplicación

Las migraciones deben aplicarse en este orden:

1. `0033_remove_catalogoproducto_tipo_cryptocustodio`
2. `0034_replace_cc_with_tipo_producto`
3. `0035_allow_null_cc_in_movimiento`

**Dependencias:**
- `0034` depende de `0033`
- `0035` depende de `0034`

---

## Comandos para Aplicar en Producción

### Opción 1: Aplicar todas las migraciones pendientes

```bash
# Conectarse a la VPS
ssh usuario@vps-ip

# Navegar al directorio del proyecto
cd /ruta/al/proyecto/cryptotrace

# Aplicar migraciones
docker-compose exec backend python manage.py migrate productos
```

### Opción 2: Aplicar migración específica

```bash
# Aplicar hasta una migración específica
docker-compose exec backend python manage.py migrate productos 0035_allow_null_cc_in_movimiento
```

### Opción 3: Verificar estado de migraciones

```bash
# Ver qué migraciones están aplicadas y cuáles pendientes
docker-compose exec backend python manage.py showmigrations productos
```

---

## Verificación Post-Migración

Después de aplicar las migraciones, verificar:

1. **Migración 0033:**
   ```sql
   -- Verificar que la columna fue eliminada
   \d productos_catalogoproducto
   -- No debe aparecer 'tipo_cryptocustodio'
   ```

2. **Migración 0034:**
   ```sql
   -- Verificar que la columna cc fue eliminada
   \d productos_lineatemporalproducto
   -- No debe aparecer 'cc'
   
   -- Verificar que tipo_producto_id fue añadida
   \d productos_lineatemporalproducto
   -- Debe aparecer 'tipo_producto_id'
   ```

3. **Migración 0035:**
   ```sql
   -- Verificar que cc permite NULL
   \d productos_movimientoproducto
   -- El campo 'cc' debe tener 'nullable: true'
   ```

---

## Rollback (Si es Necesario)

Si necesitas revertir una migración:

```bash
# Revertir hasta una migración específica
docker-compose exec backend python manage.py migrate productos 0032_add_imagen_documento_field

# O revertir todas las migraciones pendientes
docker-compose exec backend python manage.py migrate productos zero
```

**⚠️ ADVERTENCIA:** El rollback puede causar pérdida de datos si hay dependencias.

---

## Notas Adicionales

1. **Backup antes de migrar:**
   ```bash
   # Hacer backup de la base de datos antes de aplicar migraciones
   docker-compose exec db pg_dump -U postgres cryptotrace_db > backup_pre_migraciones_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Horario recomendado:**
   - Aplicar migraciones durante ventana de mantenimiento
   - Las migraciones 0033 y 0034 son destructivas (eliminan columnas)

3. **Testing:**
   - Probar en staging antes de producción
   - Verificar que el flujo de AC21 funciona correctamente después de las migraciones

---

## Cambios Relacionados en el Código

Además de las migraciones, estos cambios requieren actualización del código:

1. **Backend (`views.py`):**
   - Lógica actualizada para manejar `cc` como `NULL`
   - Lógica actualizada para usar `tipo_producto` en lugar de `cc` en `LineaTemporalProducto`

2. **Frontend:**
   - Componentes actualizados para manejar CC vacío
   - Modal de líneas temporales actualizado para usar `TipoProducto`

3. **OCR:**
   - Prompt mejorado para no inventar valores de CC
   - Validación mejorada para respetar CC vacío

---

## Contacto

Si hay dudas sobre estas migraciones, consultar:
- Documentación: `docs/DISTINCION-CC-OCR-VS-TIPOPRODUCTO.md`
- Historial de cambios en Git
