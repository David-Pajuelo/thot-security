# Distinción entre CC del OCR y TipoProducto

## Resumen Ejecutivo

Existen **DOS campos completamente diferentes** que NO deben confundirse:

1. **CC del OCR (AC21)** - Campo informativo del documento
2. **TipoProducto** - Campo de clasificación/tipificación del sistema

---

## 1. CC del OCR (AC21) - Campo Informativo

### Propósito
- **Campo informativo** que viene del documento AC21 original
- Representa el "Accounting Legend Code" (ALC) o "Código de Contabilidad" del documento
- **Solo se usa para trasladar información** del OCR al albarán generado
- **NO se usa para clasificar productos** en el sistema

### Ubicación en el Código

#### Modelo: `MovimientoProducto.cc`
```python
# cryptotrace/cryptotrace-backend/src/productos/models.py
class MovimientoProducto(models.Model):
    # ...
    cc = models.IntegerField(default=1, help_text='Campo CC del AC-21')
    # ...
```

**Características:**
- Tipo: `IntegerField` (actualmente con `default=1`)
- Valores posibles: `1`, `2`, `3`, u otro número (según el documento AC21)
- **Puede estar vacío** en el OCR (el documento puede no tener CC)
- Se guarda en `MovimientoProducto` cuando se crea el movimiento desde el AC21

#### Almacenamiento Temporal: `LineaTemporalProducto.datos_adicionales['cc']`
```python
# cryptotrace/cryptotrace-backend/src/productos/models.py
class LineaTemporalProducto(models.Model):
    # ...
    datos_adicionales = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        help_text='Información adicional del AC21 (cabecera, empresas, firmas, cc del OCR, etc.)'
    )
    # ...
```

**Características:**
- El CC del OCR se guarda temporalmente en `datos_adicionales['cc']` durante el procesamiento
- Se extrae de ahí cuando se crea el `MovimientoProducto`
- **NO se usa para tipificación**

### Flujo de Datos

```
OCR del AC21
    ↓
articulos[].cc (string: "1", "2", "3", o "")
    ↓
LineaTemporalProducto.datos_adicionales['cc'] (temporal)
    ↓
MovimientoProducto.cc (IntegerField) - INFORMATIVO
```

### Ejemplo de Uso
```python
# En procesar_directo o procesar:
cc_del_ocr_raw = articulo.get('cc', '')  # Del OCR
# ... validación ...
movimiento = MovimientoProducto.objects.create(
    # ...
    cc=cc_del_ocr,  # Se guarda como información del documento
    # ...
)
```

---

## 2. TipoProducto - Campo de Clasificación

### Propósito
- **Campo de clasificación/tipificación** de productos en el sistema
- Se usa para categorizar productos (C, CC, Ninguno, etc.)
- Se asigna manualmente en el modal de líneas temporales
- Se guarda en el catálogo para **asignación automática** en futuros documentos

### Ubicación en el Código

#### Modelo: `TipoProducto`
```python
# cryptotrace/cryptotrace-backend/src/productos/models.py
class TipoProducto(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    # Ejemplos: "C", "CC", "NINGUNO", etc.
```

#### Modelo: `LineaTemporalProducto.tipo_producto`
```python
# cryptotrace/cryptotrace-backend/src/productos/models.py
class LineaTemporalProducto(models.Model):
    # ...
    tipo_producto = models.ForeignKey(
        TipoProducto, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        help_text='Tipo de cryptocustodio para tipificación de la línea temporal'
    )
    # ...
```

**Características:**
- Tipo: `ForeignKey` a `TipoProducto`
- Puede ser `NULL` (inicialmente no tipificado)
- Se asigna en el modal de líneas temporales
- Se guarda en `CatalogoProducto.tipo` para futuras asignaciones automáticas

#### Modelo: `CatalogoProducto.tipo`
```python
# cryptotrace/cryptotrace-backend/src/productos/models.py
class CatalogoProducto(models.Model):
    # ...
    tipo = models.ForeignKey(
        TipoProducto, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    # ...
```

**Características:**
- Se actualiza cuando se procesa un AC21
- Se usa para **asignación automática** en futuros documentos
- Si un producto ya tiene `tipo` asignado, se pre-selecciona en el modal

### Flujo de Datos

```
Usuario selecciona TipoProducto en modal
    ↓
LineaTemporalProducto.tipo_producto (ForeignKey)
    ↓
CatalogoProducto.tipo (ForeignKey) - Para futuras asignaciones automáticas
```

### Ejemplo de Uso
```python
# En el modal de líneas temporales:
producto.tipo_producto = TipoProducto.objects.get(nombre="CC")
producto.save()

# Al procesar:
catalogo_producto.tipo = linea_temporal.tipo_producto
catalogo_producto.save()
```

---

## 3. Comparación Directa

| Aspecto | CC del OCR (AC21) | TipoProducto |
|---------|-------------------|--------------|
| **Propósito** | Informativo (del documento) | Clasificación (del sistema) |
| **Origen** | OCR del AC21 | Asignación manual del usuario |
| **Modelo Principal** | `MovimientoProducto.cc` | `LineaTemporalProducto.tipo_producto` |
| **Tipo de Campo** | `IntegerField` | `ForeignKey` a `TipoProducto` |
| **Puede estar vacío** | ✅ Sí (puede no venir en el OCR) | ✅ Sí (inicialmente NULL) |
| **Se guarda en** | `MovimientoProducto` | `CatalogoProducto.tipo` |
| **Se usa para** | Trasladar info del documento | Clasificar productos |
| **Asignación automática** | ❌ No | ✅ Sí (en futuros documentos) |
| **Valores** | `1`, `2`, `3`, u otro número | `"C"`, `"CC"`, `"NINGUNO"`, etc. |

---

## 4. Puntos Críticos

### ⚠️ NO Confundir

1. **CC del OCR ≠ TipoProducto**
   - Son campos completamente diferentes
   - Tienen propósitos diferentes
   - Se guardan en lugares diferentes

2. **CC del OCR es informativo**
   - Solo se traslada del documento al albarán
   - NO se usa para clasificar productos
   - Puede estar vacío

3. **TipoProducto es de clasificación**
   - Se asigna manualmente por el usuario
   - Se guarda en el catálogo para futuras asignaciones
   - Es independiente del CC del OCR

### ✅ Flujo Correcto

```
1. OCR extrae CC del AC21 → articulos[].cc
2. CC se guarda temporalmente en datos_adicionales['cc']
3. Usuario asigna TipoProducto en modal → tipo_producto
4. Al procesar:
   - CC del OCR → MovimientoProducto.cc (informativo)
   - TipoProducto → CatalogoProducto.tipo (clasificación)
```

---

## 5. Problema Actual

### MovimientoProducto.cc

**Estado actual:**
```python
cc = models.IntegerField(default=1, help_text='Campo CC del AC-21')
```

**Problema:**
- El campo tiene `default=1`, lo que significa que siempre tiene un valor
- Si el OCR devuelve CC vacío (`""` o `None`), el backend usa `1` por defecto
- Esto **no respeta** el vacío del OCR

**Solución propuesta:**
- Cambiar a `null=True, blank=True` para permitir valores vacíos
- O cambiar a `CharField` para permitir cadenas vacías
- O usar un valor especial (ej: `0` o `-1`) para representar "vacío"

---

## 6. Recomendación

Para respetar completamente el vacío del CC del OCR:

1. **Opción 1: Permitir NULL**
   ```python
   cc = models.IntegerField(null=True, blank=True, help_text='Campo CC del AC-21 (puede estar vacío)')
   ```

2. **Opción 2: Cambiar a CharField**
   ```python
   cc = models.CharField(max_length=10, blank=True, null=True, help_text='Campo CC del AC-21 (puede estar vacío)')
   ```

3. **Opción 3: Valor especial para "vacío"**
   ```python
   cc = models.IntegerField(default=0, help_text='Campo CC del AC-21 (0 = vacío)')
   ```

**Recomendación:** Opción 1 (permitir NULL) es la más clara y respeta mejor el vacío del OCR.
