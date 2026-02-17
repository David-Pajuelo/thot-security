# Prompts actuales del OCR AC21

El procesador AC21 usa **dos llamadas a OpenAI (Vision)** con dos prompts distintos:

1. **Prompt CABECERA** (`_create_openai_prompt_header`): imagen completa → cabecera, empresas, estado material, firmas, observaciones.
2. **Prompt ARTÍCULOS** (`_create_openai_prompt_items`): imagen (opcionalmente recortada a la tabla) → tabla de artículos, accesorios, equipos de prueba.

Luego se **fusionan** los dos resultados en un único JSON.

---

## Reglas generales (comunes / de contexto)

- **NO inventar datos.** Si un campo está vacío o no es visible → `""` (cadena vacía).
- **NO confundir campos.** Cada campo tiene su ubicación en el documento.
- **NO usar valores por defecto** salvo cuando el prompt lo indique explícitamente.
- **Salida:** un único objeto JSON válido, sin texto adicional. Campos vacíos = `""` (no `null`).

*(En el prompt de artículos se repiten y amplían estas ideas con más detalle.)*

---

## Prompt 1: CABECERA (y firmas)

**Objetivo:** Extraer solo cabecera, empresas, estado del material, firmas y observaciones. **No** extraer la tabla de artículos (dejar `articulos`, `accesorios`, `equipos_prueba` como `[]`).

### Cabecera

| Campo | Instrucción |
|-------|-------------|
| `tipo_transaccion` | Buscar "1." y la casilla marcada: TRANSFER/TRANSFERENCIA → `"transferencia"`, INVENTORY/INVENTARIO → `"inventario"`, DESTRUCTION/DESTRUCCION → `"destruccion"`, HAND RECEIPT/RECIBO EN MANO → `"recibo_en_mano"`, OTHER/OTRO → `"otro"`. Si ninguna visible → `"transferencia"` (único valor por defecto). |
| `numero_registro_salida` | Buscar "4." y "Nº Registro de Salida" (ES) o "Outgoing Number" (EN). Extraer número/código alfanumérico. No usar fechas, direcciones ni ODMC. Vacío → `""`. |
| `fecha_informe` | Buscar "3." y "DATE OF REPORT" / "Fecha del Informe". Fecha en **YYYY-MM-DD** o **DD-MM-YYYY** (ambos aceptados; usar el que coincida con el documento). Vacío → `""`. |
| `fecha_transaccion` | Buscar "5." y "DATE OF TRANSACTION" / "Fecha de la Transacción". Fecha en **YYYY-MM-DD** o **DD-MM-YYYY** (ambos aceptados). No confundir con fecha_informe. Vacío → `""`. |
| `numero_registro_entrada` | Buscar "6." y "Nº Registro de Entrada" / "Incoming Number". Número/código alfanumérico. No usar ODMC (eso va en empresas). Vacío → `""`. |

### Empresas

- Dos secciones: **arriba** = `empresa_origen`, **abajo** = `empresa_destino`.
- Para cada empresa, en este orden:
  - `numero_odmc`: "ACCT. NO" o "ODMC" → código visible.
  - `nombre`: nombre de la empresa (después de ODMC, antes de dirección). No usar ciudad como nombre.
  - `direccion`: calle y número. Si solo hay ciudad → `""`.
  - `codigo_postal`: número de 5 dígitos (ej. 28071). Si no hay → `""`.
  - `ciudad`: ciudad después del código postal. Si no hay → `""`.
  - `provincia`: texto entre paréntesis tras ciudad, o igual que ciudad si es capital. Si no hay → `""`.

### Estado del material

- Buscar "14. EL MATERIAL HA SIDO:" / "14. THE MATERIAL HAS BEEN:".
- Casilla marcada: RECIBIDO/RECEIVED → `recibido: true`, INVENTARIADO/INVENTORIED → `inventariado: true`, DESTRUIDO/DESTROYED → `destruido: true`.
- Si ninguna marcada → todos `false`.

### Firmas

- Bloque **izquierda** = `destinatario`, bloque **derecha** = `testigo`.
- Por bloque: "Nombre y Apellidos"/"Name" → `nombre`, "Empleo"/"Rango"/"Grade" → `empleo_rango`, "Cargo"/"Service" → `cargo`.
- Sin valor visible → `""`.

### Observaciones generales

- Extraer "17. OBSERVACIONES DEL ODMC REMITENTE". Si no hay → `""`.

### Estructura JSON de salida (cabecera)

- Incluye también: `estado_material`, `testigo` (boolean), `otro` (boolean), `observaciones_generales`, y `articulos`, `accesorios`, `equipos_prueba` como `[]`.

---

## Prompt 2: ARTÍCULOS (tabla, CC, accesorios, equipos de prueba)

**Objetivo:** Extraer **solo** las tablas de inventario del AC-21 (artículos, accesorios, equipos de prueba). No cabecera ni empresas.

### Reglas fundamentales (obligatorias)

1. **NO inventar datos.** Vacío o no visible → `""`.
2. **NO omitir información.** Extraer todo lo visible.
3. **NO asumir valores.** Si no se ve un número, no poner "1" por defecto (salvo donde se indique).
4. **CC:** Para **cada** fila hay que leer la celda de la columna "12. CC"/"12. ALC" y asignar su valor a `cc` (o `""` si está vacía). Un valor CC por fila; no omitir la columna en ninguna fila; no inventar ni copiar de otra fila.

### Proceso de extracción

#### PASO 1 – Contar y verificar filas

- Contar **exactamente** cuántas filas de datos hay (sin cabeceras). Rango típico 1–35.
- **No inventar filas:** solo extraer filas que **realmente** se ven. No duplicar (`indice_fila` único). Si el documento no tiene fila 34, no extraer fila 34.
- **Verificar continuidad:** si hay saltos en los índices, comprobar si el salto existe en el documento o si se omitió una fila; si la fila está en el documento, debe extraerse.

#### PASO 2 – Extraer artículos

- Una fila del documento = un elemento. Orden según el documento (puede haber saltos de numeración).
- **No inventar filas.** **No omitir filas** visibles. Para cada fila extraída, validar que el contenido coincide con lo que se ve en esa fila.

Por cada fila, extraer:

| Campo | Regla |
|-------|--------|
| `indice_fila` | **Obligatorio.** Número de la **primera columna** de la tabla (1, 2, 3, 4, 5…). Respetar saltos del documento (ej. 1, 2, 5, 6). Si la primera columna no tiene número visible → `null` o `0`, **nunca** inventar secuencia. |
| `codigo_producto` | Columna "TÍTULO CORTO / EDICIÓN" (ES) o "SHORT TITLE / EDITION" (EN). No usar OBSERVACIONES/REMARKS. Vacío → `""`. |
| `observaciones` | Columna "OBSERVACIONES" (ES) o "REMARKS" (EN). **Extraer todo** el texto de la celda (negrita, normal, todas las líneas). No omitir. Si el texto es **exactamente igual** al de `codigo_producto` → `""`. Si hay cualquier diferencia → texto completo. |
| `cantidad` | Número entero de columna "CANTIDAD". Vacío o no visible → `1` (mínimo permitido). |
| `numero_serie_inicio` | Columna "NÚMERO DE SERIE - INICIO". Vacío → `""`. |
| `numero_serie_fin` | Columna "NÚMERO DE SERIE - FIN". Vacío → `""`. |
| `cc` | **Obligatorio por fila.** Localizar columna "12. CC" (ES) o "12. ALC" (EN). Para **cada** fila, leer la celda de **esa** fila en la columna CC/ALC. Contenido: si hay número o código ("1", "2", "3", "C", "1A", etc.) → string; si hay número con marcas ("1 ☑") → solo el número; celda vacía o solo símbolos sin dígito → `""`. **Prohibido:** inventar o copiar de otra fila. Si la columna CC/ALC no existe en cabecera → `""` en todas. |

#### PASO 3 – Validar antes de responder

- Comprobar: `len(articulos) == N` (N = filas contadas en Paso 1).
- **Sin `indice_fila` duplicados.** Cada uno debe aparecer una sola vez.
- **Validación de contenido:** cada fila (código, observaciones, cantidad, numero_serie, cc) debe coincidir con lo que se ve en esa fila.
- **CC:** debe haber exactamente un `cc` por artículo. Si falta en algún artículo, volver a la imagen y asignar el valor de esa celda (o `""`).
- **Índices:** comprobar saltos; si el documento tiene una fila visible que no se extrajo, es error y debe corregirse.

### Accesorios

- Buscar sección "ACCESORIOS ENTREGADOS CON CADA EQUIPO" (ES) o similar. Tabla con descripción y cantidad.
- Cada fila → `{ "descripcion": "...", "cantidad": N }`. Si no hay sección o está vacía → `[]`.

### Equipos de prueba

- Buscar etiquetas tipo "PRUEBAS AICOX", "EQUIPOS PRUEBAS AICOX", "EQUIPOS DE PRUEBA", "TEST EQUIPMENT" (EN), etc.
- **(A) Una sola línea:** título + código en la misma o siguiente línea (ej. "PRUEBAS AICOX" y "ATQH 54") → un elemento: `{ "codigo": "ATQH 54" }`. No usar el título como código.
- **(B) Tabla con varias filas:** una fila por equipo → un elemento `{ "codigo": "..." }` por fila.
- Si hay etiqueta pero ningún valor → `[]`. No omitir la sección por estar al final.

### Formato JSON (artículos)

- Un único objeto JSON. Campos vacíos = `""`.
- `indice_fila` obligatorio en todos los artículos; reflejar primera columna del documento (respetar saltos).
- Estructura:
  - `articulos`: array de `{ indice_fila, codigo_producto, observaciones, cantidad, numero_serie_inicio, numero_serie_fin, cc }`
  - `accesorios`: `[ { descripcion, cantidad } ]`
  - `equipos_prueba`: `[ { codigo } ]`

---

## Resumen por parte del PDF

| Parte del PDF | Prompt usado | Reglas específicas principales |
|---------------|--------------|---------------------------------|
| Puntos 1–6 (tipo, fechas, registros) | Cabecera | tipo_transaccion según casilla; fechas YYYY-MM-DD; números de registro sin ODMC. |
| Empresas origen/destino | Cabecera | ODMC, nombre, dirección, CP, ciudad, provincia; arriba=origen, abajo=destino. |
| Punto 14 (estado material) | Cabecera | recibido / inventariado / destruido según casilla. |
| Puntos 15–16 (firmas) | Cabecera | destinatario (izq.) y testigo (der.): nombre, empleo_rango, cargo. |
| Punto 17 (observaciones) | Cabecera | Texto de "OBSERVACIONES DEL ODMC REMITENTE". |
| Tabla de artículos | Artículos | indice_fila (1ª col.), codigo_producto, observaciones, cantidad, numero_serie_inicio/fin, **cc** (col. 12 CC/ALC por fila). |
| Accesorios | Artículos | Tabla "ACCESORIOS ENTREGADOS..."; descripcion + cantidad. |
| Equipos de prueba | Artículos | Título tipo "PRUEBAS AICOX" + valor, o tabla de códigos. |

---

## Nota sobre reparación de JSON

Existe un tercer uso de OpenAI (`_fix_json_with_openai`) que **no cambia el contenido**: solo recibe un JSON con errores de sintaxis y devuelve el mismo contenido con JSON válido (comas, llaves, comillas). No modifica valores ni número de elementos.

---

*Archivo de referencia: `cryptotrace/cryptotrace-ocr/app/ocr/processors/ac21_processor.py` (métodos `_create_openai_prompt_header` y `_create_openai_prompt_items`).*
