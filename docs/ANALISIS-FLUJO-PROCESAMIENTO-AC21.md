# Análisis del Flujo de Procesamiento de AC21

## Resumen Ejecutivo

Este documento analiza el flujo completo de procesamiento de documentos AC21 desde la carga del PDF hasta la creación del inventario, identificando todos los puntos de transformación de datos y posibles problemas.

---

## 1. Flujo General del Procesamiento

### 1.1. Fase 1: Carga y Procesamiento OCR (Frontend)

**Archivo:** `cryptotrace-frontend/src/app/albaranes/upload-ac21/page.tsx`

**Proceso:**
1. Usuario sube un archivo PDF/Imagen del AC21
2. El frontend extrae el PDF usando `pdfjs-dist`
3. Se envía la imagen al servicio OCR (`processAC21Image`)
4. El OCR devuelve datos estructurados:
   - **Cabecera:** número_registro_salida, número_registro_entrada, fechas, tipo_transaccion
   - **Empresas:** origen y destino (con datos completos)
   - **Artículos:** código_producto, número_serie, observaciones, cantidad, cc
   - **Firmas:** datos de firmantes A y B
   - **Otros:** accesorios, equipos_prueba, observaciones generales

**Datos clave extraídos del OCR:**
```typescript
{
  cabecera: {
    numero_registro_salida: string,
    numero_registro_entrada: string,
    fecha_informe: string,
    fecha_transaccion: string,
    tipo_transaccion: { transferencia, inventario, destruccion, recibo_en_mano, otro }
  },
  empresa_origen: { nombre, direccion, codigo_postal, ciudad, provincia, numero_odmc, id? },
  empresa_destino: { nombre, direccion, codigo_postal, ciudad, provincia, numero_odmc, id? },
  articulos: [{
    codigo_producto: string,  // "TÍTULO CORTO / EDICIÓN"
    numero_serie_inicio: string,
    numero_serie_fin: string,
    observaciones: string,    // "OBSERVACIONES/REMARKS"
    cantidad: number,
    cc: string | number       // Campo CC del OCR
  }],
  firmas: { firma_a: {...}, firma_b: {...} },
  accesorios: [],
  equipos_prueba: []
}
```

---

### 1.2. Fase 2: Validación y Guardado en Línea Temporal (Frontend → Backend)

**Archivo Frontend:** `cryptotrace-frontend/src/app/albaranes/upload-ac21/page.tsx` (función `handleConfirmContinuado`)

**Validaciones realizadas:**
1. ✅ Verificar que existe al menos un número de registro (salida o entrada)
2. ✅ Verificar si es AC21 de ENTRADA (requiere tipificación)
3. ✅ Verificar si existe documento con mismo número de registro

**Endpoint Backend:** `POST /api/lineas-temporales/bulk_create/`

**Archivo Backend:** `cryptotrace-backend/src/productos/views.py` (método `bulk_create`)

**Proceso en `bulk_create`:**
1. Recibe datos del AC21 (JSON o FormData con imagen)
2. Extrae número de albarán de la cabecera
3. **Elimina registros temporales previos** del mismo usuario (limpieza)
4. Para cada artículo del OCR:
   - Extrae `codigo_producto` (TÍTULO CORTO / EDICIÓN)
   - Extrae `numero_serie` (de inicio o fin)
   - Extrae `descripcion` (de observaciones del OCR)
   - Extrae `cantidad` (validada, mínimo 1)
   - Extrae `cc` (del OCR, validado, default 1)
   - **Crea registro en `LineaTemporalProducto`** con:
     - `codigo_producto`: código del producto
     - `descripcion`: observaciones del OCR
     - `numero_serie`: número de serie
     - `cantidad`: cantidad validada
     - `datos_adicionales`: JSON con toda la información del AC21 (cabecera, empresas, firmas, cc, etc.)
     - `tipo_producto`: **NULL** (se asignará después en el modal)
     - `procesado`: **False**
5. Si hay imagen, la guarda temporalmente y almacena la ruta en `datos_adicionales`

**⚠️ PUNTO CRÍTICO 1:** En `bulk_create` NO se crea el producto en `CatalogoProducto`. Solo se crean registros temporales.

**Estructura de `LineaTemporalProducto`:**
```python
{
  usuario: User,
  numero_albaran: string,           # Número del documento
  codigo_producto: string,          # Código del producto
  descripcion: string,              # Observaciones del OCR
  numero_serie: string,
  cantidad: int,
  tipo_producto: TipoProducto | None,  # NULL inicialmente
  datos_adicionales: {
    cabecera: {...},
    empresa_origen: {...},
    empresa_destino: {...},
    firmas: {...},
    accesorios: [],
    equipos_prueba: [],
    observaciones_generales: string,
    numero_serie_inicio: string,
    numero_serie_fin: string,
    cantidad: int,
    cc: int  # CC del OCR
  },
  procesado: False
}
```

---

### 1.3. Fase 3: Tipificación de Productos (Frontend)

**Archivo:** `cryptotrace-frontend/src/components/albaranes/LineaTemporalModal.tsx` y `GestionLineaTemporal.tsx`

**Proceso:**
1. Usuario ve modal con productos agrupados por `codigo_producto`
2. Para cada producto, puede seleccionar un `TipoProducto` (C, CC, Ninguno, etc.)
3. Al seleccionar tipo, se llama a `guardarTipoProducto` que actualiza `LineaTemporalProducto.tipo_producto`

**Endpoint:** `POST /api/lineas-temporales/asignar-tipo-producto/`

**Datos actualizados:**
- `LineaTemporalProducto.tipo_producto` → ForeignKey a `TipoProducto`

**⚠️ PUNTO CRÍTICO 2:** El tipo se asigna a nivel de `codigo_producto`, no por número de serie individual.

---

### 1.4. Fase 4: Procesamiento Final (Backend)

**Endpoint:** `POST /api/lineas-temporales/procesar/`

**Archivo Backend:** `cryptotrace-backend/src/productos/views.py` (método `procesar`)

**Proceso completo:**

#### 4.1. Preparación
1. Obtiene todos los `LineaTemporalProducto` no procesados del usuario
2. Filtra por `numero_albaran` (solo productos del mismo documento)
3. Extrae datos generales del primer producto temporal:
   - Cabecera, empresas, firmas, accesorios, equipos_prueba
   - Imagen temporal (si existe)

#### 4.2. Creación del Albarán
1. Verifica si existe documento con mismo número de registro
2. Si existe → crea página adicional
3. Si no existe → crea documento nuevo (página principal)
4. Normaliza `tipo_documento` desde `tipo_transaccion`
5. Crea `Albaran` con:
   - Datos de cabecera
   - Empresas (origen y destino)
   - Firmas
   - `direccion_transferencia`: **SIEMPRE 'ENTRADA'** para este flujo
   - Imagen del documento (si existe)

#### 4.3. Creación de Movimientos e Inventario
Para cada `LineaTemporalProducto`:

1. **Buscar/Crear Producto en Catálogo:**
   ```python
   producto = CatalogoProducto.objects.filter(codigo_producto=p.codigo_producto).first()
   if not producto:
       # ✅ CORREGIDO: Ahora se crea automáticamente
       producto, created = CatalogoProducto.objects.get_or_create(
           codigo_producto=p.codigo_producto,
           defaults={'descripcion': descripcion}
       )
   ```

2. **Actualizar Tipo del Producto:**
   ```python
   if p.tipo_producto:
       producto.tipo = p.tipo_producto  # Actualiza CatalogoProducto.tipo
       producto.save()
   ```

3. **Verificar Duplicados:**
   - Verifica si ya existe `MovimientoProducto` con mismo albarán, producto y número de serie

4. **Determinar Estados:**
   ```python
   inventario_existente = InventarioProducto.objects.filter(
       producto=producto,
       numero_serie=p.numero_serie
   ).first()
   estado_anterior = inventario_existente.estado if inventario_existente else 'inactivo'
   
   if albaran.direccion_transferencia == 'ENTRADA':
       estado_nuevo = 'activo'
   elif albaran.direccion_transferencia == 'SALIDA':
       estado_nuevo = 'inactivo'
   ```

5. **Crear MovimientoProducto:**
   ```python
   movimiento = MovimientoProducto.objects.create(
       albaran=albaran,
       producto=producto,
       numero_serie=p.numero_serie,
       descripcion=producto.descripcion,
       tipo_movimiento=tipo_documento_normalizado,
       cantidad=p.cantidad,
       cc=datos_adicionales.get('cc', 1),  # CC del OCR
       observaciones=p.observaciones,
       estado_anterior=estado_anterior,
       estado_nuevo=estado_nuevo
   )
   ```

6. **Actualización Automática del Inventario:**
   - El método `save()` de `MovimientoProducto` se ejecuta automáticamente
   - Busca `InventarioProducto` existente
   - Si existe → actualiza estado, último_movimiento, última_actualizacion
   - Si no existe → crea nuevo `InventarioProducto` con estado 'activo'

7. **Marcar como Procesado:**
   ```python
   productos_temporales.update(procesado=True)
   ```

8. **Limpieza:**
   - Elimina registros temporales no procesados restantes del usuario
   - Elimina páginas vacías del documento (sin movimientos)

---

## 2. Mapeo de Datos en el Flujo

### 2.1. Campos del OCR → LineaTemporalProducto

| Campo OCR | Campo LineaTemporalProducto | Notas |
|-----------|----------------------------|-------|
| `codigo_producto` (TÍTULO CORTO) | `codigo_producto` | Directo |
| `observaciones` (OBSERVACIONES/REMARKS) | `descripcion` | Mapeado |
| `numero_serie_inicio` o `numero_serie_fin` | `numero_serie` | Usa inicio si existe |
| `cantidad` | `cantidad` | Validado (mínimo 1) |
| `cc` | `datos_adicionales['cc']` | **NO se guarda en campo `cc`** |
| `cabecera` | `datos_adicionales['cabecera']` | JSON completo |
| `empresa_origen` | `datos_adicionales['empresa_origen']` | JSON completo |
| `empresa_destino` | `datos_adicionales['empresa_destino']` | JSON completo |
| `firmas` | `datos_adicionales['firmas']` | JSON completo |

### 2.2. LineaTemporalProducto → MovimientoProducto

| Campo LineaTemporalProducto | Campo MovimientoProducto | Notas |
|----------------------------|--------------------------|-------|
| `codigo_producto` | `producto` (FK) | Busca/crea en CatalogoProducto |
| `numero_serie` | `numero_serie` | Directo |
| `descripcion` | `descripcion` | Desde producto.descripcion |
| `cantidad` | `cantidad` | Directo |
| `datos_adicionales['cc']` | `cc` | **CC del OCR** |
| `tipo_producto` | - | Se actualiza en `CatalogoProducto.tipo` |
| - | `estado_anterior` | Calculado desde inventario existente |
| - | `estado_nuevo` | Calculado según dirección_transferencia |

### 2.3. MovimientoProducto → InventarioProducto

| Campo MovimientoProducto | Campo InventarioProducto | Notas |
|--------------------------|--------------------------|-------|
| `producto` | `producto` | Directo |
| `numero_serie` | `numero_serie` | Directo |
| `producto.descripcion` | `descripcion` | Directo |
| `estado_nuevo` | `estado` | Directo |
| `self` | `ultimo_movimiento` | FK al movimiento |
| `fecha` | `ultima_actualizacion` | Directo |

---

## 3. Problemas Identificados y Corregidos

### 3.1. ✅ CORREGIDO: Producto no se creaba en CatalogoProducto

**Problema:** En el método `procesar`, si el producto no existía en `CatalogoProducto`, no se creaba automáticamente, causando que no se crearan movimientos ni inventario.

**Solución:** Añadida creación automática con `get_or_create()` similar a `perform_create`.

**Ubicación:** `cryptotrace-backend/src/productos/views.py:2413-2424`

### 3.2. ✅ CORREGIDO: Estados no se establecían explícitamente

**Problema:** Al crear `MovimientoProducto`, no se establecían `estado_anterior` y `estado_nuevo` explícitamente, causando que el inventario no se actualizara correctamente.

**Solución:** Añadida lógica para determinar estados basándose en inventario existente y dirección de transferencia.

**Ubicación:** `cryptotrace-backend/src/productos/views.py:2454-2468`

---

## 4. Puntos de Atención

### 4.1. Distinción entre CC del OCR y TipoProducto

- **`cc` (del OCR):** Se almacena en `MovimientoProducto.cc` y `LineaTemporalProducto.datos_adicionales['cc']`. Es información del documento original.
- **`TipoProducto`:** Se almacena en `LineaTemporalProducto.tipo_producto` y `CatalogoProducto.tipo`. Es la clasificación del producto para tipificación.

### 4.2. Flujo de ENTRADA vs SALIDA

- **AC21 de ENTRADA:** Siempre usa el flujo de línea temporal (requiere tipificación)
- **AC21 de SALIDA:** Puede usar `perform_create` directamente (no requiere tipificación)

### 4.3. Limpieza de Registros Temporales

- Se eliminan registros temporales previos del usuario antes de crear nuevos
- Se eliminan registros temporales no procesados después del procesamiento
- Se eliminan páginas vacías del documento

### 4.4. Manejo de Imágenes

- Las imágenes se guardan temporalmente en `media/temp_documentos/`
- Se transfieren al albarán durante el procesamiento
- Se eliminan archivos temporales después de la transferencia

---

## 5. Flujo de Datos Completo (Diagrama)

```
[PDF/Imagen AC21]
       ↓
[OCR Processing]
       ↓
[Datos Estructurados]
       ↓
[Frontend: Validaciones]
       ↓
[POST /api/lineas-temporales/bulk_create/]
       ↓
[LineaTemporalProducto] (procesado=False, tipo_producto=NULL)
       ↓
[Modal de Tipificación]
       ↓
[POST /api/lineas-temporales/asignar-tipo-producto/]
       ↓
[LineaTemporalProducto] (tipo_producto asignado)
       ↓
[POST /api/lineas-temporales/procesar/]
       ↓
[Albaran] (creado)
       ↓
[Para cada LineaTemporalProducto:]
       ├─→ [CatalogoProducto] (buscar/crear)
       ├─→ [CatalogoProducto.tipo] (actualizar si hay tipo_producto)
       ├─→ [MovimientoProducto] (crear)
       │     └─→ [MovimientoProducto.save()]
       │           └─→ [InventarioProducto] (crear/actualizar)
       └─→ [LineaTemporalProducto.procesado] = True
```

---

## 6. Campos Clave por Modelo

### 6.1. LineaTemporalProducto
- `codigo_producto`: Código del producto (del OCR)
- `descripcion`: Observaciones del OCR
- `numero_serie`: Número de serie
- `cantidad`: Cantidad
- `tipo_producto`: TipoProducto asignado (NULL inicialmente)
- `datos_adicionales`: JSON con toda la información del AC21
- `procesado`: Boolean (False hasta procesar)

### 6.2. CatalogoProducto
- `codigo_producto`: Código único del producto
- `descripcion`: Descripción del producto
- `tipo`: TipoProducto asociado (se actualiza desde LineaTemporalProducto)

### 6.3. MovimientoProducto
- `producto`: FK a CatalogoProducto
- `numero_serie`: Número de serie
- `albaran`: FK a Albaran
- `cc`: CC del OCR (IntegerField)
- `estado_anterior`: Estado previo del inventario
- `estado_nuevo`: Nuevo estado (activo/inactivo)
- `tipo_movimiento`: Tipo de movimiento
- `cantidad`: Cantidad

### 6.4. InventarioProducto
- `producto`: FK a CatalogoProducto
- `numero_serie`: Número de serie
- `estado`: Estado actual (activo/inactivo)
- `ultimo_movimiento`: FK a MovimientoProducto
- `ultima_actualizacion`: Fecha de última actualización

---

## 7. Endpoints Clave

1. **POST /api/lineas-temporales/bulk_create/**
   - Crea registros temporales desde AC21
   - Acepta JSON o FormData con imagen

2. **GET /api/lineas-temporales/agrupados/**
   - Devuelve productos agrupados por código
   - Incluye tipos disponibles y tipos desde catálogo

3. **POST /api/lineas-temporales/asignar-tipo-producto/**
   - Asigna TipoProducto a productos temporales

4. **POST /api/lineas-temporales/procesar/**
   - Procesa productos temporales y crea albarán, movimientos e inventario

---

## 8. Conclusión

El flujo actual funciona correctamente después de las correcciones aplicadas. Los puntos críticos son:

1. ✅ Creación automática de productos en catálogo
2. ✅ Establecimiento explícito de estados en movimientos
3. ✅ Actualización automática de inventario mediante `save()` de MovimientoProducto

**Próximos pasos sugeridos:**
- Revisar si hay otros flujos que requieran correcciones similares
- Validar que el flujo de SALIDA también funciona correctamente
- Considerar añadir validaciones adicionales en el frontend
