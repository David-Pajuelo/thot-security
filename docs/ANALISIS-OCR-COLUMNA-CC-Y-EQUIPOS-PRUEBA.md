# Análisis OCR: Columna CC y Equipos de Prueba

Todo lo que afecta a la **extracción de la columna CC** y a los **equipos de prueba** en el prompt del OCR (AC21) y en el post-procesado. Referencia: `cryptotrace-ocr/app/ocr/processors/ac21_processor.py`.

---

## 1. COLUMNA CC (Accounting Legend Code / Código de contabilidad)

### 1.1 Reglas en el prompt de ÍTEMS (Paso 2 – tabla de artículos)

El prompt usado para extraer la tabla (`_create_openai_prompt_items`) contiene lo siguiente referido a CC:

#### Reglas fundamentales (principio del prompt)

- **Regla 4 – CRÍTICO PARA CC:**  
  - El campo `cc` **puede estar vacío en TODAS las filas**.  
  - Si la columna CC está vacía o solo tiene símbolos → usar `""` en **todas** las filas.  
  - **NUNCA** asignar secuencias (1, 2, 3…) a CC.  
  - **NUNCA** usar el número de `indice_fila` para CC.

#### Validación de contenido por fila

- Para cada fila hay que comprobar que el contenido (incluido `cc`) coincide **exactamente** con lo que aparece en esa fila del documento.  
- `cc` debe corresponder a la **misma fila** que los demás campos (código_producto, observaciones, cantidad, numero_serie).

#### Instrucciones específicas del campo `cc`

- **Dónde buscar:**  
  Columna etiquetada **"12. CC"** (ES) o **"12. ALC"** (EN) en la **cabecera** de la tabla.

- **Qué extraer:**  
  - Si hay un **número visible y claro** (ej. "1", "2", "3", "4") → extraer ese número como **string**.  
  - Si hay **número con marcas** (ej. "1 ☑", "1 #", "1✓") → extraer **solo el número**, ignorando marcas.  
  - Si la celda está **vacía**, tiene **solo símbolos sin número**, **solo puntos/círculos** o **no hay número visible** → usar `""`.

- **Prohibido:**  
  - Inventar valores.  
  - Asumir valores por defecto.  
  - Usar valores de otras filas.  
  - Asignar secuencias (1, 2, 3, 4…).  
  - Usar el valor de `indice_fila` para CC.  
  - Asumir que “debe haber” valor porque otras filas lo tienen.

- **Casos especiales:**  
  - Si **solo** hay símbolos, puntos, círculos, marcas de verificación o la celda está vacía → `""`.  
  - Si **no se encuentra** la columna CC/ALC en la cabecera → `""` para **todas** las filas.  
  - Si **no hay 100% de seguridad** de que hay un número visible y claro → `""`.  
  - Es **perfectamente normal** que CC esté vacío en todas las filas; no “completar” valores faltantes.

#### Paso 3 – Validación antes de responder

- **Validación de CC:**  
  - Comprobar que `cc` contiene **exactamente** lo que aparece en la columna CC/ALC, o `""` si está vacío.  
  - **Rechazar cualquier patrón secuencial:** si CC sale como "1", "2", "3", "4"… en secuencia → **revisar la imagen** (se considera error).  
  - No debe haber valores inventados, secuenciales ni basados en `indice_fila`.  
  - Si en el documento **todas** las celdas CC están vacías → **todas** las filas deben tener `cc: ""`.

- **Separación CC vs indice_fila:**  
  - La regla de secuencia aplica **solo** a `indice_fila`, **no** a `cc`.  
  - `cc` es **completamente independiente** de `indice_fila`.  
  - `cc` debe extraerse exactamente como en la columna CC/ALC: sin secuencias, sin patrones, sin inventar.  
  - Que `indice_fila` sea 1, 2, 3… **no** implica que `cc` deba ser 1, 2, 3…  
  - **CC puede estar vacío en todas las filas** con independencia de `indice_fila`.

#### Formato JSON de ejemplo

- En el ejemplo del prompt, los artículos llevan `"cc": ""` en todas las filas (refuerzo de que vacío es válido).

---

### 1.2 Mención en el prompt de CABECERA (Paso 1)

En el prompt de cabecera (`_create_openai_prompt_header`) **no** se extrae la tabla; se dejan `articulos`, `accesorios`, `equipos_prueba` como listas vacías. No hay reglas adicionales de CC ahí.

---

### 1.3 Prompt unificado (legacy / otra ruta)

En `_create_openai_prompt` (prompt unificado, si se usa en algún flujo):

- Buscar **columna 12**: "12. ALC" (EN) o "12. CC" (ES) en cabecera de la tabla.  
- Mismas reglas: extraer solo número visible; si vacío/símbolos → `""`; prohibido inventar, secuencias y usar `indice_fila` para CC.  
- Si no se encuentra la columna CC/ALC → `""` para todas las filas.  
- Es normal que CC esté vacío en todas las filas.

---

### 1.4 Post-procesado en código (sanitize) – CC

En `sanitize_article_data()`:

- Si `cc` es `None` → se guarda `""`.  
- Si tiene valor: se hace `str(cc_value).strip()`.  
  - Si queda vacío → `""`.  
  - Si no está vacío: se intenta `int(float(cc_str))`.  
    - Si **convierte a número** → se guarda el string tal cual (`cc_str`).  
    - Si **no convierte** (símbolos no numéricos) → se imprime aviso y se guarda `""`.

**Resumen:** En código, CC solo se acepta como vacío o como string que represente un número; cualquier otra cosa se convierte a `""`.

---

## 2. EQUIPOS DE PRUEBA

### 2.1 Dónde se extraen

- **Solo en el Paso 2** (llamada de ítems: tabla de artículos, accesorios y equipos de prueba).  
- En el Paso 1 (cabecera) **no** se extraen; se devuelven como `equipos_prueba: []`.

### 2.2 Reglas en el prompt de ÍTEMS (Paso 2)

Bloque **"ACCESORIOS y EQUIPOS DE PRUEBA"**:

- **Ubicación:**  
  Esas secciones suelen estar **debajo** de la tabla principal de artículos, en una zona con dos columnas o dos bloques.

- **EQUIPOS DE PRUEBA:**  
  - **Títulos a buscar:** "EQUIPOS PRUEBAS AICOX", "EQUIPOS DE PRUEBA", "TEST EQUIPMENT" (EN) o similar.  
  - **Estructura:** Suele ser una tabla de **una columna** con códigos (cada fila = un equipo).  
  - **Qué hacer:** Extraer **todos** los códigos que aparezcan en esa tabla.  
  - **Formato:** Cada uno como `{ "codigo": "valor_extraído" }`. Si hay varias filas con código, un elemento por fila.  
  - Si la sección **no existe** o está **vacía** → devolver `[]`.

- **Norma crítica:**  
  Si en la imagen se ve una sección claramente etiquetada como equipos de prueba (o accesorios), **hay que extraerla**. No omitir estos bloques por estar al final del documento.

### 2.3 Formato JSON

- `equipos_prueba`: lista de objetos con clave `"codigo"`.  
- Ejemplo en el prompt: `"equipos_prueba": [ { "codigo": "..." } ]`.

### 2.4 Prompt unificado (legacy)

- Punto 4: extraer listas de "ACCESORIOS ENTREGADOS" y "EQUIPOS PRUEBAS".  
- Título puede variar (ej. "EQUIPOS DE PRUEBA AICOX"); el modelo debe manejar esas variaciones.  
- Estructura: `equipos_prueba`: `[ { "codigo": "String" } ]`.

### 2.5 Reparación de JSON (`_fix_json_with_openai`)

- Al reparar un JSON roto, se indica: mantener las mismas claves y el **mismo número de elementos** en `articulos`, `accesorios` y `equipos_prueba`. No eliminar objetos ni elementos de las listas.

### 2.6 Post-procesado en código (sanitize) – equipos de prueba

En `sanitize_equipos_prueba()`:

- Si el valor no es una lista → se devuelve lista vacía.  
- Para cada elemento de la lista:  
  - Si no es un dict, se ignora.  
  - Se construye `{ "codigo": str(item.get("codigo") or "").strip() }`.  
  - Solo se añade a la lista resultante si `codigo` **no está vacío** (`if sanitized_item["codigo"]`).

**Resumen:** Solo se conservan equipos cuyo `codigo` (después de trim) sea no vacío; el resto se descarta.

---

## 3. Resumen rápido

| Aspecto | CC | Equipos de prueba |
|--------|---|-------------------|
| **Dónde se extrae** | Columna "12. CC" / "12. ALC" de la tabla de artículos (Paso 2). | Sección debajo de la tabla (Paso 2); títulos "EQUIPOS PRUEBAS AICOX", "EQUIPOS DE PRUEBA", "TEST EQUIPMENT", etc. |
| **Valor vacío** | Permitido y normal en todas las filas; usar `""`. | Sección puede no existir o estar vacía → `[]`. |
| **Prohibiciones (CC)** | No inventar, no secuencias, no usar indice_fila para CC. | — |
| **Post-procesado** | Solo se acepta `""` o string que sea número; lo demás → `""`. | Solo se mantienen objetos con `codigo` no vacío. |

Este documento refleja el estado del prompt y del código en `ac21_processor.py` para la columna CC y para equipos de prueba.
