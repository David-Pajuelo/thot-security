# Análisis Completo del Flujo de `indice_fila`

## Resumen Ejecutivo

Este documento analiza el flujo completo de `indice_fila` desde el OCR hasta el frontend, identificando todos los fallbacks y puntos donde se puede perder información.

---

## 1. Flujo Actual de `indice_fila`

### 1.1. OCR - Extracción
**Archivo:** `cryptotrace-ocr/app/ocr/processors/ac21_processor.py`

**Proceso:**
1. El prompt instruye al OCR a extraer `indice_fila` de la primera columna del documento
2. El OCR devuelve JSON con `indice_fila` para cada artículo
3. La sanitización (`sanitize_article_data`) procesa el `indice_fila`:
   - Intenta extraer de `article.get("indice_fila")` o `article.get("indice")` o `article.get("fila")`
   - **FALLBACK ACTUAL**: Si no encuentra, asigna `index` (posición en el array)

**Problema identificado:**
- Línea 473-474: `if indice_fila is None: indice_fila = index`
- Esto oculta errores del OCR: si el OCR no extrae `indice_fila`, se asigna automáticamente un valor

---

### 1.2. Frontend - Recepción y Visualización
**Archivo:** `cryptotrace-frontend/src/app/albaranes/upload-ac21/page.tsx`

**Proceso:**
1. El frontend recibe `processedData.articulos[]` con `indice_fila` del OCR
2. En la visualización (línea 3137-3139):
   ```typescript
   const rowNumber = (typeof articulo?.indice_fila === 'number' && !Number.isNaN(articulo.indice_fila))
     ? articulo.indice_fila
     : index + 1;  // FALLBACK
   ```
3. En el cálculo de filas faltantes (línea 1941-1946):
   ```typescript
   const filaIndices: number[] = (processedData?.articulos || []).map(
     (art: any, idx: number) =>
       (typeof art?.indice_fila === 'number' && !Number.isNaN(art.indice_fila))
         ? art.indice_fila
         : idx + 1  // FALLBACK
   );
   ```
4. Al insertar línea manualmente (línea 1151-1159):
   - Asigna `indice_fila` basándose en contexto, pero tiene fallbacks a `insertIndex + 1`

**Problemas identificados:**
- Múltiples fallbacks que ocultan errores
- Si el OCR no proporciona `indice_fila`, el sistema "funciona" pero con datos incorrectos

---

### 1.3. Backend - Procesamiento
**Archivo:** `cryptotrace-backend/src/productos/views.py`

**Proceso:**
- El backend NO procesa `indice_fila` directamente
- `indice_fila` se guarda en `datos_adicionales` de `LineaTemporalProducto` (si se usa el flujo temporal)
- En `procesar_directo`, `indice_fila` NO se usa para crear `MovimientoProducto`

**Estado:**
- ✅ El backend no tiene fallbacks para `indice_fila` porque no lo procesa directamente

---

## 2. Problemas Identificados

### 2.1. Fallbacks que Ocultan Errores

| Ubicación | Fallback | Problema |
|-----------|----------|----------|
| OCR - `sanitize_article_data` | `indice_fila = index` si no hay valor | Oculta que el OCR no extrajo el índice |
| Frontend - Visualización | `index + 1` si no hay `indice_fila` | Muestra número incorrecto |
| Frontend - Cálculo filas faltantes | `idx + 1` si no hay `indice_fila` | Cálculo incorrecto de filas faltantes |
| Frontend - Inserción línea | `insertIndex + 1` si no hay contexto | Asigna índice incorrecto |

### 2.2. Falta de Validación

- No hay validación que verifique que TODOS los artículos tienen `indice_fila`
- No hay alertas cuando el OCR no proporciona `indice_fila`
- No hay verificación de que los `indice_fila` son consistentes con el documento

---

## 3. Solución Propuesta

### 3.1. OCR - Eliminar Fallback

**Cambio:**
- Si el OCR no proporciona `indice_fila`, dejar como `None` o `null`
- NO asignar `index` automáticamente
- Agregar logging para alertar cuando falta `indice_fila`

### 3.2. OCR - Mejorar Prompt

**Cambio:**
- Hacer el prompt más estricto: `indice_fila` es OBLIGATORIO
- Si la primera columna no tiene número, el OCR debe reportar esto explícitamente
- NO permitir que el OCR invente valores

### 3.3. Frontend - Eliminar Fallbacks

**Cambio:**
- Si `indice_fila` no existe o es inválido, mostrar error o indicador visual
- NO usar `index + 1` como fallback
- Validar que todos los artículos tienen `indice_fila` válido antes de procesar

### 3.4. Frontend - Validación Pre-Procesamiento

**Cambio:**
- Antes de procesar, validar que TODOS los artículos tienen `indice_fila` válido
- Si falta alguno, mostrar error y no permitir procesar
- Alertar al usuario sobre artículos sin `indice_fila`

---

## 4. Implementación

### 4.1. OCR - Sanitización

```python
# ANTES (con fallback):
if indice_fila is None:
    indice_fila = index

# DESPUÉS (sin fallback):
if indice_fila is None:
    print(f"⚠️ [OCR] ADVERTENCIA: Artículo sin indice_fila: {codigo_producto}")
    # Dejar como None - el frontend debe manejar esto
```

### 4.2. Frontend - Visualización

```typescript
// ANTES (con fallback):
const rowNumber = articulo?.indice_fila || index + 1;

// DESPUÉS (sin fallback):
const rowNumber = articulo?.indice_fila;
if (!rowNumber || isNaN(rowNumber)) {
  // Mostrar error o indicador visual
  return <td className="error">⚠️ Sin índice</td>;
}
```

### 4.3. Frontend - Validación Pre-Procesamiento

```typescript
// Validar antes de procesar
const articulosSinIndice = processedData.articulos.filter(
  (art: any) => !art.indice_fila || isNaN(art.indice_fila)
);

if (articulosSinIndice.length > 0) {
  toast.error(
    `Error: ${articulosSinIndice.length} artículo(s) sin índice de fila. El OCR debe extraer el número de la primera columna.`,
    { duration: 10000 }
  );
  return; // No procesar
}
```

---

## 5. Validaciones Necesarias

1. **OCR debe SIEMPRE extraer `indice_fila`**
2. **Frontend debe validar que TODOS los artículos tienen `indice_fila`**
3. **Si falta `indice_fila`, mostrar error claro al usuario**
4. **NO procesar si hay artículos sin `indice_fila`**

---

## 6. Casos de Error Esperados

1. **OCR no extrae `indice_fila`**: Mostrar error, no procesar
2. **OCR extrae `indice_fila` inválido**: Mostrar error, no procesar
3. **Documento sin números en primera columna**: El OCR debe reportar esto explícitamente

---

## 7. Mejoras al Prompt del OCR

- Hacer `indice_fila` OBLIGATORIO en el prompt
- Instruir explícitamente: "SI la primera columna no tiene número visible, reporta esto explícitamente en el campo `indice_fila` como null o 0"
- NO permitir que el OCR invente valores secuenciales
