# 📋 Plan de Implementación: Generación de Documentos AC21 de Salida

## 1. **Diseño y desarrollo de la nueva página de creación de AC21 de salida**

### 1.1. **Diseño del flujo de usuario**
- [ ] Bocetar el flujo de la página (wizard o formulario guiado)
- [ ] Definir los campos obligatorios y opcionales
- [ ] Definir validaciones y feedback de usuario
- [ ] Definir la vista previa del documento antes de generar el PDF

#### **Campos obligatorios y opcionales para la creación de un AC21 de salida**

##### **Empresa de origen**
- **Obligatorio:** Nombre, Dirección, Código postal, Ciudad, Provincia, País
- **Opcional:** Código ODMC, Código EMAD, NIF, Teléfono, Email

##### **Empresa de destino**
- **Obligatorio:** Nombre, Dirección, Código postal, Ciudad, Provincia, País
- **Opcional:** Código ODMC, Código EMAD, NIF, Teléfono, Email

##### **Tipo de transacción**
- **Obligatorio:** Selección entre: Transferencia, Inventario, Destrucción, Recibo en Mano, Otro

##### **Productos a incluir**
- **Obligatorio (al menos uno):** Código de producto, Descripción, Cantidad
- **Opcional:** Número de serie, Observaciones (por producto)

##### **Fechas y datos de registro**
- **Obligatorio:** Fecha del informe, Fecha de la transacción
- **Opcional:** Número de registro de salida, Número de registro de entrada

##### **Observaciones generales**
- **Opcional:** Observaciones generales del AC21

| Sección                | Campo                        | Obligatorio | Tipo         |
|------------------------|-----------------------------|-------------|--------------|
| Empresa Origen         | Nombre                      | Sí          | Texto        |
|                        | Dirección                   | Sí          | Texto        |
|                        | Código postal               | Sí          | Texto/Número |
|                        | Ciudad                      | Sí          | Texto        |
|                        | Provincia                   | Sí          | Texto        |
|                        | País                        | Sí          | Texto        |
|                        | Código ODMC                 | No          | Texto        |
|                        | Código EMAD                 | No          | Texto        |
|                        | NIF                         | No          | Texto        |
|                        | Teléfono                    | No          | Texto        |
|                        | Email                       | No          | Texto        |
| Empresa Destino        | (igual que origen)          |             |              |
| Tipo de transacción    | Tipo                        | Sí          | Selección    |
| Productos              | Código producto             | Sí          | Texto        |
|                        | Descripción                 | Sí          | Texto        |
|                        | Cantidad                    | Sí          | Número       |
|                        | Nº Serie                    | No          | Texto        |
|                        | Observaciones (producto)    | No          | Texto        |
| Fechas y registro      | Fecha informe               | Sí          | Fecha        |
|                        | Fecha transacción           | Sí          | Fecha        |
|                        | Nº registro salida          | No          | Texto        |
|                        | Nº registro entrada         | No          | Texto        |
| Observaciones generales| Observaciones               | No          | Texto        |

### 1.1.1. **Validaciones y feedback de usuario**

#### **Validaciones generales**
- [ ] Todos los campos obligatorios deben estar rellenados antes de avanzar al siguiente paso o generar el AC21.
- [ ] Mostrar mensajes de error claros y específicos junto a cada campo obligatorio no cumplimentado.
- [ ] Validar formato de email, teléfono y códigos postales.
- [ ] Validar que la cantidad de productos sea mayor que cero.
- [ ] Validar que al menos un producto esté seleccionado.
- [ ] Validar que las fechas sean válidas y no futuras (si aplica).
- [ ] Si se añade una nueva empresa, validar que no exista ya en la base de datos.

#### **Feedback de usuario**
- [ ] Mensaje de éxito al guardar cada paso o al generar el AC21.
- [ ] Mensaje de error si ocurre algún problema en la generación del PDF o en la comunicación con el backend.
- [ ] Vista previa actualizada en tiempo real conforme se rellenan los campos.
- [ ] Indicadores visuales de progreso (por ejemplo, barra de pasos o wizard).
- [ ] Botón de "Siguiente" deshabilitado hasta que se cumplan las validaciones del paso actual.
- [ ] Feedback visual (colores, iconos) para campos válidos/erróneos.

#### **Validaciones específicas por campo**
- **Empresa de origen/destino:**
  - Nombre, dirección, ciudad, provincia, país: no pueden estar vacíos.
  - Código postal: debe ser numérico y de 5 dígitos.
  - Email: debe tener formato válido.
  - Teléfono: debe tener formato válido (opcional, pero si se rellena debe ser correcto).
- **Tipo de transacción:**
  - Debe seleccionarse una opción.
- **Productos:**
  - Código, descripción y cantidad obligatorios.
  - Cantidad debe ser mayor que cero.
  - Si se requiere número de serie, debe estar rellenado.
- **Fechas:**
  - Deben tener formato válido (YYYY-MM-DD o DD/MM/YYYY).
  - No pueden ser futuras (opcional, según lógica de negocio).
- **Observaciones:**
  - Opcional, pero si se rellena debe permitir texto largo.

### 1.1.2. **Definir la vista previa del documento antes de generar el PDF**

- [ ] Implementar una vista previa interactiva del AC21 antes de la generación del PDF.
- [ ] La vista previa debe mostrar todos los datos introducidos por el usuario en el formato y disposición que tendrá el PDF final.
- [ ] Permitir al usuario revisar y, si es necesario, volver atrás para corregir cualquier campo antes de la generación definitiva.
- [ ] La vista previa debe incluir:
  - Datos de empresa de origen y destino
  - Tipo de transacción
  - Tabla de productos seleccionados (código, descripción, cantidad, nº de serie, observaciones)
  - Fechas y datos de registro
  - Observaciones generales
- [ ] La vista previa debe ser responsiva y clara, permitiendo al usuario identificar fácilmente cualquier error o campo incompleto.
- [ ] Opción de "Editar" en cada sección para volver rápidamente al paso correspondiente del wizard/formulario.
- [ ] Botón destacado para "Generar AC21" solo habilitado si todos los datos son válidos.

### 1.2. **Implementación frontend**
- [ ] Crear nueva ruta/página: `/albaranes/crear-ac21-salida`
- [ ] Añadir enlace a la nueva página en la barra de navegación principal
- [ ] Paso 1: Selección de empresa de origen y destino
  - [ ] Autocompletado de empresas existentes
  - [ ] Alta rápida de nueva empresa si no existe
- [ ] Paso 2: Selección de tipo de transacción
  - [ ] Opciones: Transferencia, Inventario, Destrucción, Recibo en Mano, Otro
- [ ] Paso 3: Selección de productos a incluir
  - [ ] Buscador de productos
  - [ ] Selección múltiple, cantidades, nº de serie, etc.
- [ ] Paso 4: Relleno de campos adicionales
  - [ ] Fechas, observaciones, campos libres
- [ ] Paso 5: Vista previa del AC21
  - [ ] Mostrar cómo quedará el documento antes de generar el PDF
- [ ] Paso 6: Botón "Generar AC21"
  - [ ] Llama al backend para generar el PDF y lo asocia al movimiento de salida

---

## 2. **Backend: Generación y gestión del documento AC21**

### 2.1. **API para recibir los datos del formulario**
- [ ] Crear endpoint para recibir los datos del AC21 de salida
- [ ] Validar los datos recibidos
- [ ] Guardar el movimiento de salida y los productos asociados

### 2.2. **Generación del PDF AC21**

#### **Opción recomendada: A. Usar el Excel como plantilla y convertir a PDF**
- [x] **Motivo de la elección:**  
  - Permite mantener el formato exacto del AC21 original.
  - Es rápido de implementar y fácil de mantener si el formato cambia.
  - No requiere replicar el diseño desde cero ni crear un PDF editable manualmente.

#### **Tareas para la generación del PDF:**
- [ ] Usar `openpyxl` o `xlsxwriter` para rellenar el Excel con los datos del formulario.
- [ ] Guardar el Excel rellenado como archivo temporal.
- [ ] Usar `libreoffice` (en modo headless) para convertir el Excel a PDF automáticamente.
- [ ] Guardar el PDF generado y asociarlo al movimiento de salida en la base de datos.
- [ ] Devolver el PDF al frontend para descarga o visualización.

---

## 3. **Integración y experiencia de usuario**

- [ ] Mostrar notificación de éxito/error tras la generación del AC21.
- [ ] Permitir descargar o visualizar el PDF generado desde la interfaz.
- [ ] Asociar el documento AC21 generado al historial de movimientos del producto.

---

## 4. **Pruebas y validación**

- [ ] Pruebas unitarias del backend (relleno de Excel, conversión a PDF, validación de datos)
- [ ] Pruebas de integración frontend-backend
- [ ] Pruebas de experiencia de usuario (flujo completo)
- [ ] Validación visual del PDF generado (debe ser idéntico al AC21 original)

---

## 5. **Documentación y despliegue**

- [ ] Documentar el flujo de usuario y la API
- [ ] Documentar el proceso de generación de PDFs y dependencias (libreoffice, etc.)
- [ ] Desplegar en entorno de pruebas
- [ ] Validar con usuarios finales
- [ ] Desplegar en producción

---

## **Flujo de la nueva página de creación de AC21 de salida**

1. **Inicio**  
   Usuario accede a `/albaranes/crear-ac21-salida`.

2. **Selección de empresas**  
   - Autocompleta o da de alta empresa de origen y destino.

3. **Tipo de transacción**  
   - Selecciona el tipo de movimiento (Transferencia, Inventario, etc.).

4. **Selección de productos**  
   - Busca y selecciona productos, añade cantidades y números de serie.

5. **Campos adicionales**  
   - Rellena fechas, observaciones, etc.

6. **Vista previa**  
   - Visualiza cómo quedará el AC21.

7. **Generar AC21**  
   - Se genera el PDF y se asocia al movimiento de salida.

8. **Descarga/visualización**  
   - El usuario puede descargar o ver el PDF generado.

---

## **Resumen de la opción técnica elegida**

**Opción A: Usar el Excel como plantilla y convertir a PDF**  
- Rellenar el Excel con los datos del formulario usando Python.
- Convertir el Excel rellenado a PDF automáticamente con LibreOffice.
- Ventajas: formato idéntico, rapidez de implementación, fácil mantenimiento. 