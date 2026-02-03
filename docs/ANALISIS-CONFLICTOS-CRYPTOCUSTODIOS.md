# Análisis de conflictos: implementación Cryptocustodios

Este documento revisa el sistema actual y los puntos donde la implementación de **Cryptocustodios** podría afectar a la creación de AC21, al flujo de datos y al resto de pestañas, para detectar conflictos inesperados.

---

## 1. Resumen ejecutivo

- **Creación de AC21 (upload y guardado):** Sin cambios en payload ni en backend; solo se añade UI (desplegables que rellenan los mismos campos de texto). **Sin conflicto.**
- **Edición de AC21 (AC21Detail):** Misma idea: desplegables rellenan `firma_a_*` / `firma_b_*`; el PATCH sigue igual. **Sin conflicto.**
- **Generación de PDF:** Sigue leyendo `firma_a_*` y `firma_b_*` del Albaran; no se añade FK ni nuevo campo. **Sin conflicto.**
- **Pestañas Entradas / Salidas / Albaranes:** Siguen usando listados de albaranes y empresas sin cryptocustodios; la nueva API es independiente. **Sin conflicto.**
- **Empresas – eliminación:** La “baja” actual es lógica (`activa=False`). Los cryptocustodios solo se borran en cascada si se hace un borrado físico de la empresa (p. ej. en admin). **Sin conflicto;** se documenta el comportamiento.
- **OCR y flujo upload:** La estructura `firmas.firma_a` / `firma_b` no cambia; los desplegables solo rellenan sobre los mismos campos. **Sin conflicto.**

Se recomienda **registrar el modelo Cryptocustodio en el admin** (y opcionalmente un inline en Empresa) para consistencia con el resto del sistema.

---

## 2. Flujo de creación de AC21 (upload-ac21)

### 2.1 Cómo se crea hoy

1. **Frontend (`upload-ac21/page.tsx`):** El usuario sube PDF/imagen → OCR devuelve `empresa_origen`, `empresa_destino`, `firmas: { firma_a: { nombre, cargo, empleo_rango }, firma_b: { ... } }`, etc.
2. Los datos se guardan en `processedData`; el usuario puede editar empresas (selector, pestaña “Empresas”) y firmas (campos manuales en punto 15/16).
3. Al enviar:
   - Se construye payload con `empresa_origen`, `empresa_destino` (objetos con `id`), `firmas` (objeto con `firma_a` y `firma_b` con `nombre`, `cargo`, `empleo_rango`), más cabecera, artículos, etc.
   - Se llama al backend (POST a endpoint de creación de AC21 / línea temporal, etc.).

### 2.2 Dónde interviene el backend

- **Backend (`views.py`):** Parsea `parsed_data.get('firmas')`, luego `firma_a_data = firmas.get('firma_a', {})`, y asigna:
  - `firma_a_nombre_apellidos = firma_a_data.get('nombre', '')`
  - `firma_a_cargo`, `firma_a_empleo_rango`
  - e igual para `firma_b`.
- Crea el `Albaran` con `firma_a_*` y `firma_b_*` (y `empresa_origen_id`, `empresa_destino_id`).

### 2.3 Qué se añade con Cryptocustodios

- En la misma pantalla (punto 15): desplegables filtrados por **empresa destino** para firma A y firma B.
- Al elegir un cryptocustodio: se rellenan **solo** `firma_a_empleo_rango`, `firma_a_nombre_apellidos`, `firma_a_cargo` (y lo mismo para firma_b). El campo “Firma” sigue siendo manual.
- El payload que se envía **no cambia**: sigue habiendo `firmas.firma_a` y `firmas.firma_b` con `nombre`, `cargo`, `empleo_rango` (y opcionalmente el texto de firma si ya existía). El backend sigue leyendo los mismos campos.

**Conclusión:** No hay cambio en la estructura de datos ni en la API; solo en la UI que rellena esos datos. **No hay conflicto.**

---

## 3. Flujo de edición de AC21 (AC21Detail)

### 3.1 Cómo se edita hoy

- Se cargan `empresa_origen_info`, `empresa_destino_info` y los campos `firma_a_*`, `firma_b_*` del albarán (vía `AlbaranSerializer`).
- Al guardar se hace PATCH con `empresa_origen`, `empresa_destino` (IDs), `firma_a_nombre_apellidos`, `firma_a_cargo`, `firma_a_empleo_rango`, etc.
- El backend actualiza el `Albaran` con esos valores.

### 3.2 Qué se añade con Cryptocustodios

- Desplegables de cryptocustodios filtrados por `empresa_destino` para rellenar firma A y firma B (solo Empleo/Rango, Nombre y apellidos, Cargo).
- Sigue enviándose el mismo PATCH; no se añade FK a Cryptocustodio.

**Conclusión:** Misma estructura de edición y mismo backend. **No hay conflicto.**

---

## 4. Generación de PDF (AC21)

### 4.1 Flujo actual

- **Backend:** `AlbaranViewSet.generar_ac21_html()` construye `ac21_data` para el servicio PDF:
  - `firma_entrega` ← `pagina_principal.firma_a_nombre_apellidos`, `firma_a_cargo`, `firma_a_empleo_rango`, `firma_a` (firma_texto).
  - `firma_recibe` ← `pagina_principal.firma_b_*` y `firma_b`.
- **PDF generator:** Recibe ese JSON y la plantilla usa `firma_entrega` y `firma_recibe` (nombre_apellidos, cargo, empleo_rango, firma_texto).

### 4.2 Impacto de Cryptocustodios

- Los datos de firma siguen guardándose en los mismos campos del modelo `Albaran`; no se introduce FK ni campo nuevo para el PDF.
- El generador de PDF no necesita saber nada de cryptocustodios; solo lee los textos ya guardados.

**Conclusión:** No hay cambio en contrato ni en modelo. **No hay conflicto.**

---

## 5. Otras pestañas y listados

### 5.1 Entradas / Salidas

- **Entradas:** `AlbaranesTable` con `filterType="ENTRADA"` (AC21 de entrada).
- **Salidas:** `AlbaranesTable` con `filterType="SALIDA"` (AC21 de salida).
- Ambos cargan albaranes con `AlbaranSerializer` (incluye `empresa_origen_info`, `empresa_destino_info` y campos de firma). No usan cryptocustodios.
- La nueva funcionalidad es un endpoint y UI aparte: `GET /cryptocustodios/?empresa=<id>` y el modal en Empresas.

**Conclusión:** Ningún cambio en datos ni en filtros de estas pestañas. **No hay conflicto.**

### 5.2 Listado de empresas (pestaña Empresas)

- **Hoy:** Tabla de empresas (nombre, dirección, etc.) con acciones Crear / Editar / Eliminar.
- **Con Cryptocustodios:** Se añade un botón “Ver cryptocustodios” que abre un **modal** que hace `GET /cryptocustodios/?empresa=<id>` y muestra CRUD de cryptocustodios.
- El listado de empresas sigue siendo el mismo; el serializer de Empresa no tiene por qué incluir la lista de cryptocustodios (evitamos cargar datos innecesarios en GET /empresas/).

**Conclusión:** Cambio acotado a un nuevo botón y un modal; no altera el listado ni la estructura actual. **No hay conflicto.**

### 5.3 Crear AC21 de salida (crear-ac21-salida/nuevo)

- Flujo distinto: formulario con empresas origen/destino por nombre y campos de firma (`firma_a_nombre_apellidos`, etc.) que se envían directamente en el payload (no anidados en `firmas`).
- En el plan actual, los desplegables de cryptocustodios se añaden en **upload-ac21** y en **AC21Detail**, no en esta pantalla.
- Si en el futuro se añaden aquí, sería el mismo criterio: cryptocustodios de empresa destino para rellenar firma A y B; no cambia el contrato del backend.

**Conclusión:** No afectado en la primera fase. **No hay conflicto.**

---

## 6. Eliminación de empresas y CASCADE

### 6.1 Comportamiento actual

- **Frontend:** `deleteEmpresa(id)` llama a `DELETE /empresas/:id/`.
- **Backend:** `EmpresaViewSet.destroy()` hace **borrado lógico**: `empresa.activa = False` y `save()`. No se borra la fila de la base de datos.
- `get_queryset()` devuelve solo `Empresa.objects.filter(activa=True)`, por lo que la empresa “eliminada” deja de verse en el listado.

### 6.2 Con Cryptocustodio y CASCADE

- Modelo: `Cryptocustodio.empresa` con `on_delete=models.CASCADE`.
- **CASCADE** solo se ejecuta cuando se hace un **borrado físico** de la fila de `Empresa` (por ejemplo desde el admin de Django o con `Empresa.objects.filter(pk=...).delete()`).
- Al “eliminar” una empresa desde la UI actual, **no** se borra la fila; por tanto **no** se borran sus cryptocustodios. Esos registros siguen en BD asociados a una empresa inactiva.
- En la UI, esa empresa ya no aparece en la tabla, así que el usuario no puede abrir el modal de cryptocustodios para ella. No hay inconsistencia visible.
- Si en el futuro se implementa un “borrado definitivo” desde la app, entonces CASCADE eliminará los cryptocustodios de esa empresa, que es el comportamiento acordado.

**Conclusión:** Comportamiento coherente con el diseño actual. **No hay conflicto.** Conviene dejar documentado que la “baja” desde la UI es lógica y que CASCADE solo aplica al borrado físico.

---

## 7. OCR y estructura de firmas

### 7.1 Salida del OCR

- El OCR (AC21) devuelve, entre otras cosas, `firmas`: `{ firma_a: { nombre, cargo, empleo_rango }, firma_b: { ... } }` (y en el modelo Albaran existe además el campo “firma” texto).
- El frontend guarda eso en `processedData.firmas` y puede mostrarlo/editarse en los campos del punto 15/16.

### 7.2 Uso en backend

- En creación desde upload / línea temporal, el backend hace `firmas.get('firma_a', {})` y asigna `firma_a_nombre_apellidos = firma_a_data.get('nombre', '')`, etc.
- No se cambia ni el formato del OCR ni el parsing.

### 7.3 Con Cryptocustodios

- Los desplegables **sobrescriben** (o rellenan) los campos de firma en el estado del formulario a partir de cryptocustodios; el payload final sigue teniendo la misma forma `firmas.firma_a` / `firmas.firma_b` con `nombre`, `cargo`, `empleo_rango`.
- El OCR puede seguir rellenando por defecto; el usuario puede luego elegir un cryptocustodio y reemplazar solo esos tres campos (y “Firma” sigue manual).

**Conclusión:** Misma estructura de datos en toda la cadena. **No hay conflicto.**

---

## 8. Serializers y API

### 8.1 EmpresaSerializer

- Actualmente expone campos de Empresa (id, nombre, dirección, etc.). No incluye cryptocustodios.
- **Decisión:** No añadir lista de cryptocustodios en el serializer de Empresa para no cargar datos extra en GET /empresas/. Los cryptocustodios se piden bajo demanda con GET /cryptocustodios/?empresa=<id>.

**Conclusión:** Sin cambios en el contrato actual de empresas. **No hay conflicto.**

### 8.2 AlbaranSerializer

- Incluye `empresa_origen`, `empresa_destino`, `empresa_origen_info`, `empresa_destino_info` y todos los campos de firma (`firma_a_*`, `firma_b_*`).
- No se añade ninguna referencia a Cryptocustodio en el albarán.

**Conclusión:** Sin cambios. **No hay conflicto.**

---

## 9. Admin de Django

### 9.1 Estado actual

- `EmpresaAdmin`: list_display sin cryptocustodios.
- `AlbaranAdmin`: fieldsets con empresa_origen, empresa_destino y firmas (firma_a_*, firma_b_*).

### 9.2 Recomendación

- Registrar el modelo **Cryptocustodio** en el admin (list_display: empleo_rango, nombre_apellidos, cargo, empresa).
- Opcional: añadir un **inline** de Cryptocustodios en la ficha de Empresa para poder ver/editar desde el admin sin tocar el resto del sistema.

**Conclusión:** Solo añadidos; no se modifica el comportamiento actual. **No hay conflicto.**

---

## 10. Tabla de comprobación rápida

| Área / Flujo              | ¿Se modifica payload o API? | ¿Se modifica modelo Albaran/Empresa? | Riesgo de conflicto |
|---------------------------|------------------------------|--------------------------------------|----------------------|
| Creación AC21 (upload)    | No                           | No                                   | Ninguno              |
| Edición AC21 (AC21Detail) | No                           | No                                   | Ninguno              |
| Generación PDF AC21       | No                           | No                                   | Ninguno              |
| Entradas / Salidas        | No                           | No                                   | Ninguno              |
| Listado Empresas          | No (solo nuevo botón + modal)| No                                   | Ninguno              |
| Crear AC21 salida         | No (en esta fase)            | No                                   | Ninguno              |
| Eliminación empresa       | No                           | No (CASCADE solo en borrado físico)  | Ninguno              |
| OCR y firmas              | No                           | No                                   | Ninguno              |
| Serializers               | No                           | No                                   | Ninguno              |
| Admin                     | No (solo registro nuevo)     | No                                   | Ninguno              |

---

## 11. Conclusión

La implementación de Cryptocustodios tal como está definida en `docs/IMPLEMENTACION-CRYPTOCUSTODIOS.md`:

- No cambia la forma en que se **crean** los AC21 (upload ni backend).
- No cambia la forma en que se **mueve** la información (payloads, firmas, empresas).
- No afecta a **otras pestañas** (Entradas, Salidas, listado de albaranes, listado de empresas) más allá de añadir el botón y modal de cryptocustodios en Empresas.
- No introduce FK en Albaran ni cambios en el generador de PDF.
- La eliminación de empresas (baja lógica) sigue igual; CASCADE solo aplica a borrado físico y está alineado con lo acordado.

No se han detectado conflictos inesperados; el análisis apoya seguir con la implementación según el plan ya documentado.
