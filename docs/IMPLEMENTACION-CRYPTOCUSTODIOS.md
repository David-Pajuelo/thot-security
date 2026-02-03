# Implementación: tabla Cryptocustodios y uso en AC21

Este documento describe el estudio y el plan de implementación para la nueva entidad **Cryptocustodios**, su relación con **Empresas**, la gestión en la pestaña Empresas y el uso en el procesamiento de AC21 (punto 15 – Destinatario autorizado del material de cifra).

---

## 1. Objetivos

1. **Nueva tabla `cryptocustodios`** relacionada con `empresas` (1-N: una empresa tiene muchos cryptocustodios).
2. **Pestaña Empresas:** para cada empresa guardada, poder ver, añadir, editar y eliminar cryptocustodios asociados.
3. **Procesamiento AC21:** en el punto 15 (DESTINATARIO AUTORIZADO DEL MATERIAL DE CIFRA), disponer de:
   - Desplegables filtrados por **empresa destino** con los cryptocustodios asociados (tanto para firma A como para firma B).
   - Posibilidad de guardar un nuevo cryptocustodio y rellenar automáticamente los campos del formulario (Empleo/Rango, Nombre y apellidos, Cargo). El campo "Firma" queda siempre manual.
   - Un único selector de cryptocustodios de la empresa destino para cada bloque (firma A y firma B).

---

## 2. Análisis del código existente

### 2.1 Backend

- **Modelo `Empresa`** (`productos/models.py`): campos `nombre`, `direccion`, `ciudad`, `codigo_postal`, `provincia`, `numero_odmc`, `activa`. Sin relación actual con personas/cryptocustodios.
- **Modelo `Albaran`** (y página principal AC21): 
  - `empresa_origen`, `empresa_destino` (FK a `Empresa`).
  - Punto 15 se guarda en campos de firma:
    - **Firma A (destinatario):** `firma_a`, `firma_a_empleo_rango`, `firma_a_nombre_apellidos`, `firma_a_cargo` (y legacy: `destinatario_autorizado_nombre`, `destinatario_autorizado_cargo`).
    - **Firma B (testigo/otro):** `firma_b`, `firma_b_empleo_rango`, `firma_b_nombre_apellidos`, `firma_b_cargo`.
  - No hay FK a ninguna tabla de “personas”; todo es texto libre.
- **API Empresas:** `EmpresaViewSet` (CRUD) en `/empresas/`. Serializer: `EmpresaSerializer` con todos los campos de empresa.

### 2.2 Frontend

- **Empresas:** `app/empresas/page.tsx` → `EmpresasTable`. Listado en tabla, creación/edición en `Dialog` con `EmpresaForm`. No hay página de detalle por empresa (`/empresas/[id]`); todo es modal.
- **Upload AC21** (`app/albaranes/upload-ac21/page.tsx`):
  - Selectores de **empresa origen** y **empresa destino** (dropdown + datos debajo).
  - Pestañas/zonas para editar datos de empresa origen y empresa destino (guardar nueva empresa y rellenar formulario).
  - Punto 15: bloque “15. DESTINATARIO AUTORIZADO DEL MATERIAL DE CIFRA” con campos manuales para **firma_a** (Firma, Empleo/Rango, Nombre y Apellidos, Cargo) y **firma_b** (misma estructura). Sin desplegables de personas.
- **Detalle AC21** (`AC21Detail.tsx`): misma estructura de firmas en modo lectura/edición; datos en `firma_a_*` y `firma_b_*`.

### 2.3 Rutas y tipos

- API: `GET/POST /empresas/`, `GET/PUT/PATCH/DELETE /empresas/:id/`.
- Tipo `Empresa` en `lib/types.ts`: `id`, `nombre`, `codigo`, `activa`, etc. (no incluye todos los campos del backend; conviene alinear si hace falta).

---

## 3. Modelo de datos propuesto

### 3.1 Tabla `Cryptocustodio` (nueva)

| Campo             | Tipo           | Descripción                          |
|-------------------|----------------|--------------------------------------|
| `id`              | AutoField (PK) | Identificador numérico               |
| `empleo_rango`    | CharField(100) | Empleo/Rango                         |
| `nombre_apellidos`| CharField(200) | Nombre y apellidos                   |
| `cargo`           | CharField(100) | Cargo                                |
| `empresa`         | ForeignKey(Empresa) | Relación N-1 con Empresa (related_name p. ej. `cryptocustodios`) |

- `blank=True`/`null=True` según necesidad (p. ej. cargo u empleo_rango opcionales).
- `ordering = ['nombre_apellidos']` o `['empresa', 'nombre_apellidos']`.
- En la relación: **`on_delete=models.CASCADE`** (al borrar una empresa se borran sus cryptocustodios).

### 3.2 Relación con Empresa

- **Empresa** 1 —— N **Cryptocustodio**.
- Un cryptocustodio pertenece a una sola empresa; una empresa puede tener muchos cryptocustodios.

### 3.3 Albarán / AC21 (sin cambiar modelo)

- Los campos actuales de firma (`firma_a_*`, `firma_b_*`) se mantienen como están. El desplegable de cryptocustodios solo **copia** Empleo/Rango, Nombre y apellidos y Cargo a los campos de texto; **no** se guarda FK a Cryptocustodio en el albarán.
- El campo "a. Firma" (texto) **siempre es manual**; no se rellena automáticamente al seleccionar un cryptocustodio.

---

## 4. Backend

### 4.1 Modelo y migración

- Añadir en `productos/models.py` el modelo `Cryptocustodio` con los campos anteriores.
- Generar migración: `python manage.py makemigrations productos --name add_cryptocustodio` (o similar).
- **Anotar** en `docs/PLAN-BACKUP-ROLLBACK-COMMIT-ACTUAL.md` el nombre de la nueva migración (p. ej. `0036_add_cryptocustodio`) para poder revertir a `0035_allow_null_cc_in_movimiento` si hace falta.

### 4.2 API

- **Opción A – ViewSet propio:**  
  - `CryptocustodioViewSet` con CRUD en `/cryptocustodios/`.  
  - Filtro por empresa: `GET /cryptocustodios/?empresa=<id>`.
- **Opción B – Anidado bajo empresa:**  
  - `GET /empresas/<id>/cryptocustodios/` (listar), `POST /empresas/<id>/cryptocustodios/` (crear), `GET/PUT/PATCH/DELETE /empresas/<id>/cryptocustodios/<id_cc>/` (detalle/actualizar/borrar).

Recomendación: **Opción A** + filtro `?empresa=` para reutilizar el mismo endpoint en Empresas (listado por empresa) y en AC21 (desplegables por empresa destino). Incluir en el serializer el `empresa` (id o nombre) para mostrar en listados.

### 4.3 Serializer

- `CryptocustodioSerializer`: `id`, `empleo_rango`, `nombre_apellidos`, `cargo`, `empresa` (id). Opcional: `empresa_nombre` (read_only) para listados.
- Registrar en el router: `router.register(r'cryptocustodios', views.CryptocustodioViewSet)`.

### 4.4 Permisos

- Mismos criterios que Empresas (autenticación + permisos de producto/empresa si los hay).

---

## 5. Frontend – Pestaña Empresas

### 5.1 Dónde mostrar el listado de cryptocustodios (decisión)

- En el **listado de empresas** (tabla), añadir un botón por fila (p. ej. “Ver cryptocustodios” o icono) que **abra un modal**.
- Dentro del modal: mostrar los cryptocustodios asociados a esa empresa (tabla, lista o cards) con opciones de **añadir**, **editar** y **eliminar**. No se crea página de detalle `/empresas/[id]`; todo en modal.

### 5.2 Componentes necesarios

- Tipo `Cryptocustodio` en `lib/types.ts`.
- Funciones en `lib/api.ts`: `fetchCryptocustodios(empresaId?)`, `createCryptocustodio`, `updateCryptocustodio`, `deleteCryptocustodio` (y si aplica `fetchCryptocustodio(id)`).
- **Modal de cryptocustodios:** se abre desde el botón “Ver cryptocustodios” en cada fila de la tabla de empresas; incluye lista de cryptocustodios (tabla/cards) y acciones añadir/editar/eliminar.
- Formulario cryptocustodio (dentro del modal o en sub-modal): `empleo_rango`, `nombre_apellidos`, `cargo`, `empresa` (fijado por la empresa seleccionada al abrir el modal).

---

## 6. Frontend – Procesamiento AC21 (upload y detalle)

### 6.1 Punto 15 – Firma A y Firma B (decisión)

- **Firma A** y **Firma B** son ambas cryptocustodios de la **empresa destino** (quien recibe el material).
- Por tanto: **un único filtro** para los desplegables de cryptocustodios: **`empresa_destino`**. Tanto el desplegable de firma A como el de firma B se filtran por la empresa destino seleccionada en el AC21.

### 6.2 Comportamiento en la pantalla de upload AC21

- Junto a los campos de **firma_a** (bloque 15):  
  - Desplegable “Cryptocustodio” filtrado por `processedData.empresa_destino?.id`.  
  - Al seleccionar uno: rellenar **solo** `firma_a_empleo_rango`, `firma_a_nombre_apellidos`, `firma_a_cargo`. El campo “a. Firma” **no** se rellena (siempre manual).  
  - Opción “Añadir cryptocustodio”: abre modal con formulario asociado a **empresa_destino**; al guardar, se añade a la lista y se puede seleccionar para rellenar automáticamente los tres campos.
- Junto a los campos de **firma_b** (bloque 16):  
  - Mismo desplegable filtrado por `processedData.empresa_destino?.id`.  
  - Al seleccionar uno: rellenar solo `firma_b_empleo_rango`, `firma_b_nombre_apellidos`, `firma_b_cargo`. El campo “a. Firma” de firma_b **no** se rellena (siempre manual).  
  - Misma opción “Añadir cryptocustodio” para empresa destino.

Si no hay empresa destino seleccionada, los desplegables se ocultan o muestran vacíos con mensaje “Seleccione empresa destino”.

### 6.3 Detalle AC21 (AC21Detail.tsx)

- En modo edición: desplegables de cryptocustodios filtrados por `empresa_destino` para rellenar firma_a y firma_b (solo Empleo/Rango, Nombre y apellidos, Cargo). Opción “Añadir cryptocustodio” para empresa destino si aplica.

### 6.4 Persistencia

- No se guarda FK a Cryptocustodio en Albaran. Solo se copian los datos del cryptocustodio elegido a los campos de texto `firma_a_*` y `firma_b_*`.

---

## 7. Resumen de tareas técnicas

| Área        | Tarea |
|------------|--------|
| Backend    | Modelo `Cryptocustodio` + migración (`on_delete=CASCADE`); anotar en plan de rollback. |
| Backend    | `CryptocustodioSerializer`, `CryptocustodioViewSet`, ruta `/cryptocustodios/` y filtro `?empresa=`. |
| Frontend   | Tipo y API de cryptocustodios. |
| Frontend   | Empresas: botón “Ver cryptocustodios” en cada fila → modal con listado y CRUD (añadir/editar/eliminar). |
| Frontend   | Upload AC21: desplegables firma_a y firma_b filtrados por **empresa_destino**; relleno solo Empleo/Rango, Nombre, Cargo; “Firma” siempre manual; opción “Añadir cryptocustodio”. |
| Frontend   | AC21Detail: mismos desplegables y relleno en modo edición. |

---

## 8. Decisiones tomadas

| Tema | Decisión |
|------|----------|
| **Empresas – listado cryptocustodios** | Botón en el listado que abre un **modal** con los cryptocustodios de esa empresa (ver, añadir, editar, eliminar). |
| **Firma A y Firma B** | Ambas son cryptocustodios de la **empresa destino**. Desplegables filtrados por `empresa_destino`. |
| **Borrado de empresa** | **CASCADE**: al eliminar una empresa se borran sus cryptocustodios. |
| **Campo “Firma” (texto)** | Siempre **manual**; no se rellena al seleccionar un cryptocustodio. |
| **Trazabilidad en Albaran** | Solo copiar datos a los campos de texto; **no** guardar FK a Cryptocustodio en el albarán. |
