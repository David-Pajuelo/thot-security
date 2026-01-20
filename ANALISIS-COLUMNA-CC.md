# Análisis de la Columna CC (Código de Contabilidad)

## Resumen

La columna CC (Código de Contabilidad) en la tabla de inventario tiene lógica inconsistente entre el OCR, frontend y backend.

---

## 1. Definición del Campo CC

Según el documento AC-21, los **Códigos de Contabilidad (CC)** son:
- **1**: Contabilizable por número de serie
- **2**: Contabilizable por cantidad
- **3**: Acuse de recibo inicial. Puede ser controlado según instrucciones particulares del órgano correspondiente.

---

## 2. Estado Actual del Código

### 2.1 OCR (`ac21_processor.py`)

**Prompt (línea 723):**
```
* `cc`: El valor de la columna "CC" (código de contabilidad)
```

**Problema:**
- ❌ No especifica que los valores válidos son 1, 2 o 3
- ❌ No explica qué significa cada código
- ❌ No valida que el valor extraído sea uno de estos tres

**Sanitización (líneas 378-381):**
```python
try:
    sanitized_article["cc"] = int(article.get("cc") or 0)
except (ValueError, TypeError):
    sanitized_article["cc"] = 0
```

**Problema:**
- ❌ Si el OCR devuelve un string no numérico, se convierte a 0
- ❌ 0 no es un valor válido (debería ser 1, 2 o 3)
- ❌ No valida que el valor esté en el rango 1-3

### 2.2 Frontend - Upload AC21 (`page.tsx`)

**Input (líneas 3166-3176):**
```typescript
<input
  type="text"
  value={articulo.cc || articulosTipos[index] || ''}
  onChange={e => {
    nuevos[index].cc = e.target.value;
  }}
/>
```

**Problemas:**
1. ❌ **Input de texto libre**: Permite cualquier valor, no solo 1, 2 o 3
2. ❌ **Confusión con `articulosTipos`**: `articulosTipos[index]` es para tipos de artículo ('C', 'CC'), NO para códigos de contabilidad. Esto es un error lógico.
3. ❌ **No hay validación**: No valida que el valor sea 1, 2 o 3
4. ❌ **No hay ayuda visual**: No muestra las opciones disponibles

**Comparación con AC21Detail.tsx (líneas 1102-1110):**
```typescript
<select
  value={movimiento.cc || 1}
  onChange={e => actualizarMovimiento(index, 'cc', parseInt(e.target.value))}
>
  <option value={1}>1</option>
  <option value={2}>2</option>
  <option value={3}>3</option>
</select>
```

✅ **Este componente SÍ tiene la lógica correcta**: Usa un select con opciones 1, 2, 3.

### 2.3 Backend (`views.py`)

**Procesamiento (líneas 1408-1417):**
```python
cc_raw = articulo.get('cc')
try:
    if cc_raw is None or cc_raw == '':
        cc = 1  # Por defecto 1
    else:
        cc = int(float(str(cc_raw)))
        cc = max(1, cc)  # Mínimo 1
except (ValueError, TypeError):
    cc = 1
```

**Problemas:**
- ❌ No valida que el valor esté en el rango 1-3
- ❌ Si el valor es mayor a 3, lo acepta (solo fuerza mínimo 1)
- ✅ Establece 1 como valor por defecto (correcto)

---

## 3. Problemas Identificados

### 3.1 Inconsistencia en el Frontend

**Upload AC21 (`page.tsx`):**
- Usa input de texto libre
- Permite cualquier valor
- Confusión con `articulosTipos`

**AC21Detail (`AC21Detail.tsx`):**
- Usa select con opciones 1, 2, 3
- Valida valores correctamente
- UX mejor

### 3.2 Prompt del OCR Insuficiente

El prompt no especifica:
- Valores válidos (1, 2, 3)
- Significado de cada código
- Validación de rango

### 3.3 Falta de Validación

- OCR: No valida rango 1-3
- Frontend (upload): No valida rango 1-3
- Backend: No valida rango 1-3 (solo fuerza mínimo 1)

### 3.4 Confusión con `articulosTipos`

**Línea 3169:**
```typescript
value={articulo.cc || articulosTipos[index] || ''}
```

`articulosTipos` es para tipos de artículo ('C', 'CC'), no para códigos de contabilidad. Esto es un error lógico que puede causar confusión.

---

## 4. Soluciones Propuestas

### 4.1 Mejorar el Prompt del OCR

**Añadir instrucciones específicas:**
```
* `cc`: El valor de la columna "CC" (código de contabilidad). **VALORES VÁLIDOS: Solo 1, 2 o 3**.
  - **1**: Contabilizable por número de serie
  - **2**: Contabilizable por cantidad
  - **3**: Acuse de recibo inicial
  Si la celda está vacía o no puedes determinar el valor, usa "1" como valor por defecto.
  Si encuentras un valor que no sea 1, 2 o 3, usa "1" como valor por defecto.
```

### 4.2 Cambiar Frontend a Select

**Reemplazar input de texto por select:**
```typescript
<select
  className="w-10 border-none bg-transparent focus:ring-0 text-xs text-center"
  value={articulo.cc || '1'}
  onChange={e => {
    const nuevos = [...processedData.articulos];
    nuevos[index].cc = e.target.value;
    setProcessedData((prev: any) => ({ ...prev, articulos: nuevos }));
  }}
  disabled={yaExiste}
>
  <option value="1">1</option>
  <option value="2">2</option>
  <option value="3">3</option>
</select>
```

### 4.3 Eliminar Confusión con `articulosTipos`

**Eliminar el fallback incorrecto:**
```typescript
// ANTES (incorrecto):
value={articulo.cc || articulosTipos[index] || ''}

// DESPUÉS (correcto):
value={articulo.cc || '1'}
```

### 4.4 Añadir Validación en Backend

**Validar rango 1-3:**
```python
cc_raw = articulo.get('cc')
try:
    if cc_raw is None or cc_raw == '':
        cc = 1
    else:
        cc = int(float(str(cc_raw)))
        # Validar que esté en el rango 1-3
        if cc not in [1, 2, 3]:
            print(f"⚠️ [BACKEND] CC inválido ({cc}), usando 1 por defecto")
            cc = 1
except (ValueError, TypeError):
    cc = 1
```

### 4.5 Añadir Validación en OCR

**Validar en sanitización:**
```python
try:
    cc_value = int(article.get("cc") or 1)
    # Validar rango 1-3
    if cc_value not in [1, 2, 3]:
        print(f"⚠️ [OCR] CC inválido ({cc_value}), usando 1 por defecto")
        sanitized_article["cc"] = 1
    else:
        sanitized_article["cc"] = cc_value
except (ValueError, TypeError):
    sanitized_article["cc"] = 1
```

---

## 5. Recomendación Final

**Implementar todas las soluciones en este orden:**

1. ✅ **Mejorar prompt del OCR** - Especificar valores válidos y significado
2. ✅ **Cambiar frontend a select** - Mejor UX y validación
3. ✅ **Eliminar confusión con `articulosTipos`** - Corregir el fallback incorrecto
4. ✅ **Añadir validación en backend** - Asegurar que solo se acepten 1, 2 o 3
5. ✅ **Añadir validación en OCR** - Sanitizar valores inválidos

---

## 6. Checklist de Verificación

Después de implementar:
- [ ] El OCR solo devuelve valores 1, 2 o 3 para CC
- [ ] El frontend muestra un select con opciones 1, 2, 3
- [ ] No hay confusión con `articulosTipos`
- [ ] El backend valida que CC esté en rango 1-3
- [ ] Si el OCR devuelve un valor inválido, se usa 1 por defecto
- [ ] La UX es consistente entre upload-ac21 y AC21Detail
