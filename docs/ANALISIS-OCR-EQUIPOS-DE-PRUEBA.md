# Análisis: OCR y equipos de prueba (AC21)

## Qué intenta hacer el sistema

El OCR del AC21 funciona en **dos pasadas** con OpenAI Vision:

1. **Paso 1 (cabecera)**  
   - Usa la **imagen completa**.  
   - Extrae: cabecera, empresas, estado del material, firmas, observaciones.  
   - **No** extrae artículos, accesorios ni equipos de prueba (deja esas listas vacías).

2. **Paso 2 (ítems)**  
   - Usa una **imagen recortada** (solo la zona de “tabla”).  
   - Extrae: **artículos** (tabla principal), **accesorios** y **equipos_prueba**.  
   - El prompt pide un único JSON con `articulos`, `accesorios` y `equipos_prueba`.

Los equipos de prueba se intentan extraer **solo en el Paso 2**, a partir de esa imagen recortada.

---

## Cómo está definido hoy el prompt (equipos de prueba)

En `cryptotrace-ocr/app/ocr/processors/ac21_processor.py`, método `_create_openai_prompt_items`:

- El prompt está centrado en la **tabla de artículos** (columnas, índices, CC, etc.).
- Para accesorios y equipos de prueba solo dice (aprox. líneas 1278–1281):

  - **ACCESORIOS y EQUIPOS DE PRUEBA:**
  - `accesorios`: lista de objetos con `"descripcion"` y `"cantidad"` (solo si existen en el documento).
  - `equipos_prueba`: lista de objetos con `"codigo"` (solo si existen en el documento).

No se indica:

- **Dónde** están en el documento (debajo de la tabla de artículos).
- **Qué título** buscar (p. ej. “EQUIPOS PRUEBAS AICOX”, “EQUIPOS DE PRUEBA”, “TEST EQUIPMENT”).
- **Formato** de la sección (tabla de una columna, una fila por equipo con su código).

Por tanto, el modelo puede no identificar la sección correcta o no priorizar su extracción.

---

## Recorte de imagen (Paso 2)

Para el Paso 2 se usa `_crop_image_for_items`:

- Si el frontend **no** envía recorte, se llama a `detect_table_bounds()`:
  - Calcula densidad de contenido por filas.
  - Considera “tabla” la zona con más densidad.
  - Puede fijar el **final** de la tabla donde termina la tabla de artículos y **excluir** la zona de accesorios y equipos de prueba, que en el PDF están **debajo**.

- Si se envían **crop_params** con `bottom` alto (p. ej. 0.98), la imagen recortada sí suele incluir accesorios y equipos. El problema es más probable cuando se usa **solo detección automática** y el `bottom` queda demasiado arriba.

Conclusión: si la imagen que recibe el Paso 2 **no incluye** la sección de equipos de prueba, el OCR no puede extraerlos aunque el prompt fuera perfecto.

---

## Resumen de causas probables

1. **Prompt muy vago**  
   No se dice dónde están los equipos ni qué etiquetas buscar, ni se describe la estructura (tabla, columna “código”, una fila por equipo).

2. **Recorte que corta la sección**  
   La detección automática de límites puede dejar fuera la zona “ACCESORIOS / EQUIPOS PRUEBAS AICOX” (debajo de la tabla principal).

3. **Poca prioridad en el texto**  
   El prompt dedica casi todo el espacio a artículos; accesorios y equipos son una línea cada uno, por lo que el modelo puede “olvidarlos” o no buscarlos de forma sistemática.

---

## Cambios recomendados (implementados en el código)

1. **Ampliar el prompt de ítems**  
   - Indicar explícitamente que **debajo** de la tabla de artículos puede haber dos bloques:
     - “ACCESORIOS ENTREGADOS CON CADA EQUIPO” (descripción + cantidad).
     - “EQUIPOS PRUEBAS AICOX” / “EQUIPOS DE PRUEBA” / “TEST EQUIPMENT” (códigos).
   - Describir la estructura de equipos: tabla de una columna, cada fila = un `{ "codigo": "..." }`.
   - Pedir que se busquen esos títulos y se extraigan **todos** los códigos listados.

2. **Revisar el recorte**  
   - Si usas recorte automático, comprobar en logs los `crop_params` (sobre todo `bottom`).  
   - Asegurar que el recorte usado en el Paso 2 incluya hasta **debajo** de la tabla de artículos (incluyendo accesorios y equipos).  
   - Si hace falta, ampliar el `bottom` por defecto o el margen inferior en `detect_table_bounds` para que no corte la sección de equipos de prueba.

Con esto, el OCR debería “saber” qué buscar y en qué parte del documento, y la imagen enviada debería contener esa parte.
