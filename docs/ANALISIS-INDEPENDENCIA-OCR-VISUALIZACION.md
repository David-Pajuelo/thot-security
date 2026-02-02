# Análisis: Independencia del OCR respecto a la Visualización

## Resumen Ejecutivo

El OCR **NO se ve afectado** por el zoom, pan o posición de la imagen en la visualización del frontend. El OCR siempre analiza la **imagen completa** generada del PDF a **máxima calidad**, independientemente de cómo el usuario visualice el documento.

---

## 1. Flujo de Generación de Imagen para OCR

### 1.1. Frontend - Generación de Imagen de Alta Calidad

**Archivo:** `cryptotrace-frontend/src/app/albaranes/upload-ac21/page.tsx` (líneas 360-417)

**Proceso:**
1. Cuando se carga un PDF, se genera una imagen de **alta resolución** para cada página
2. Se calcula la escala para que la dimensión más corta sea **~2200px** (objetivo: máxima legibilidad)
3. Se usa `page.render()` con viewport calculado para generar el canvas
4. La imagen se guarda en `previewImages[currentPage]` como data URL PNG (sin pérdidas)

**Código clave:**
```typescript
// Calcular escala para alta resolución
const shortestDimension = Math.min(originalViewport.width, originalViewport.height);
const targetShortestSize = 2200;
const scale = shortestDimension < targetShortestSize
  ? targetShortestSize / shortestDimension
  : 1;

// Generar imagen completa
const viewport = page.getViewport({ scale: scale, rotation: -page.rotate });
canvas.width = viewport.width;
canvas.height = viewport.height;
await page.render({ canvasContext: context, viewport }).promise;

// Guardar como PNG sin pérdidas
const imageDataUrl = finalCanvas.toDataURL('image/png');
images.push(imageDataUrl);
```

**Características:**
- ✅ Imagen completa de la página (sin recortes)
- ✅ Alta resolución (dimensión corta ~2200px)
- ✅ Formato PNG sin pérdidas
- ✅ Independiente de la visualización del usuario

---

## 2. Flujo de Envío al OCR

### 2.1. Frontend - Preparación de Imagen para OCR

**Archivo:** `cryptotrace-frontend/src/app/albaranes/upload-ac21/page.tsx` (líneas 456-536)

**Proceso:**
1. Se toma la imagen completa de `previewImages[currentPage]` (NO la vista del usuario)
2. Si hay rotación aplicada por el usuario, se crea un nuevo canvas con la rotación
3. Se convierte a Blob PNG (sin pérdidas)
4. Se envía al OCR como FormData

**Código clave:**
```typescript
// Usar imagen completa generada del PDF (NO la vista del usuario)
if (rotation === 0) {
  imageBlob = await fetch(previewImages[currentPage]).then(res => res.blob());
} else {
  // Aplicar rotación en nuevo canvas (mantiene calidad)
  // ... código de rotación ...
}

const formData = new FormData();
formData.append("file", imageBlob, fileName);
formData.append("document_type", "ac21");

// Crop opcional (solo si el usuario activa "usarRecorte")
if (usarRecorte) {
  formData.append("crop_top", String(cropTop));
  formData.append("crop_bottom", String(cropBottom));
  formData.append("crop_left", String(cropLeft));
  formData.append("crop_right", String(cropRight));
}
```

**Características:**
- ✅ Usa la imagen completa generada del PDF
- ✅ NO usa la vista del usuario (zoom/pan no afecta)
- ✅ Mantiene alta calidad (PNG sin pérdidas)
- ✅ Crop manual es opcional (solo si `usarRecorte` está activado)

---

### 2.2. Visualización del Usuario (Zoom/Pan)

**Archivo:** `cryptotrace-frontend/src/app/albaranes/upload-ac21/page.tsx` (líneas 2531-2611)

**Proceso:**
1. Se usa `TransformWrapper` y `TransformComponent` de `react-zoom-pan-pinch`
2. La imagen mostrada es `previewImages[currentPage]` con rotación CSS aplicada
3. El zoom/pan es **solo visual** - no afecta la imagen enviada al OCR

**Código clave:**
```typescript
<TransformWrapper
  initialScale={1.4}
  minScale={0.3}
  maxScale={8}
  centerOnInit={true}
  centerZoomedOut={true}
  limitToBounds={false}
>
  <TransformComponent>
    <img
      src={previewImages[currentPage]}
      alt={`Preview ${currentPage + 1}`}
      style={{ transform: `rotate(${rotations[currentPage] || 0}deg)` }}
    />
  </TransformComponent>
</TransformWrapper>
```

**Características:**
- ✅ Zoom/pan es solo visual (CSS transforms)
- ✅ NO modifica la imagen original
- ✅ NO afecta al OCR

---

## 3. Procesamiento en el OCR

### 3.1. OCR - Recepción y Procesamiento

**Archivo:** `cryptotrace-ocr/app/main.py` (líneas 54-99)

**Proceso:**
1. Recibe la imagen completa como bytes
2. Aplica preprocesamiento (mejora calidad, resolución, contraste)
3. Si hay `crop_params` del frontend (solo si `usarRecorte` está activado), los usa
4. Si NO hay `crop_params`, detecta automáticamente los límites de la tabla

**Código clave:**
```python
# Recibir imagen completa
file_content = await file.read()

# Procesar con crop opcional
crop_params = None
if any(v is not None for v in [crop_top, crop_bottom, crop_left, crop_right]):
    crop_params = {
        "top": crop_top if crop_top is not None else 0.25,
        "bottom": crop_bottom if crop_bottom is not None else 0.98,
        "left": crop_left if crop_left is not None else 0.0,
        "right": crop_right if crop_right is not None else 1.0,
    }

result = processor.process_image(file_content, crop_params=crop_params)
```

**Archivo:** `cryptotrace-ocr/app/ocr/processors/ac21_processor.py` (líneas 603-630)

**Proceso:**
1. Preprocesa la imagen (mejora calidad)
2. Usa imagen completa para cabecera/empresas/firmas
3. Si hay `crop_params`, recorta para la tabla de items
4. Si NO hay `crop_params`, detecta automáticamente los límites

**Código clave:**
```python
def process_image(self, image_bytes: bytes, crop_params: Optional[Dict[str, float]] = None):
    # Preprocesar imagen (mejorar calidad)
    processed_image_bytes = self.preprocess_image(image_bytes)
    
    # Imagen completa para cabecera/empresas/firmas
    base64_image_full = self.encode_image(processed_image_bytes)
    
    # Detectar límites automáticamente si no se proporcionan
    if crop_params is None:
        detected_bounds = self.detect_table_bounds(processed_image_bytes)
        crop_params = detected_bounds
    
    # Recortar para items (solo si hay crop_params)
    cropped_bytes = self._crop_image_for_items(processed_image_bytes, crop_params=crop_params)
    base64_image_items = self.encode_image(cropped_bytes)
```

**Características:**
- ✅ Recibe imagen completa de alta calidad
- ✅ Preprocesa para mejorar calidad
- ✅ Usa imagen completa para cabecera/empresas/firmas
- ✅ Crop es opcional (detecta automáticamente si no se proporciona)

---

## 4. Conclusión

### ✅ El OCR NO se ve afectado por:
- ❌ Zoom del usuario
- ❌ Pan/posición de la imagen
- ❌ Visualización en el navegador

### ✅ El OCR SIEMPRE analiza:
- ✅ Imagen completa generada del PDF
- ✅ Alta resolución (dimensión corta ~2200px)
- ✅ Formato PNG sin pérdidas
- ✅ Preprocesada para máxima calidad

### ✅ Crop Manual:
- Es **opcional** (solo si el usuario activa "usarRecorte")
- Si no se activa, el OCR detecta automáticamente los límites de la tabla
- La imagen completa siempre se usa para cabecera/empresas/firmas

---

## 5. Recomendaciones

### 5.1. Asegurar que el Crop Manual NO se Active por Defecto

**Estado actual:** El crop manual está desactivado por defecto (`usarRecorte = false`)

**Verificación:** ✅ Correcto - el crop solo se aplica si el usuario lo activa explícitamente

### 5.2. Mejorar Documentación Visual

**Sugerencia:** Agregar tooltip o mensaje que indique claramente:
- "El zoom y pan son solo para visualización"
- "El OCR siempre analiza la imagen completa a máxima calidad"
- "El recorte manual es opcional y solo afecta la tabla de items"

---

## 6. Verificación de Calidad

### 6.1. Resolución de Imagen

**Objetivo:** Dimensión corta ~2200px
**Estado:** ✅ Implementado correctamente

### 6.2. Formato de Imagen

**Objetivo:** PNG sin pérdidas
**Estado:** ✅ Implementado correctamente

### 6.3. Preprocesamiento

**Objetivo:** Mejorar calidad antes del OCR
**Estado:** ✅ Implementado en `preprocess_image()`

### 6.4. Detección Automática de Límites

**Objetivo:** Si no hay crop manual, detectar automáticamente
**Estado:** ✅ Implementado en `detect_table_bounds()`

---

## 7. Resumen Final

**El sistema está correctamente implementado:**

1. ✅ La imagen enviada al OCR es independiente de la visualización
2. ✅ Se genera a alta resolución (~2200px dimensión corta)
3. ✅ Se usa formato PNG sin pérdidas
4. ✅ El OCR preprocesa la imagen para mejorar calidad
5. ✅ El crop manual es opcional (detecta automáticamente si no se proporciona)
6. ✅ La imagen completa siempre se usa para cabecera/empresas/firmas

**No se requieren cambios** - el sistema ya garantiza que el OCR analice siempre la imagen completa a máxima calidad, independientemente de la visualización.
