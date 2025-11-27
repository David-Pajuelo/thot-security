# Plan de Implementación: Microservicio Generador de PDF AC21

Este documento describe las tareas y subtareas para desarrollar el microservicio encargado de generar los documentos PDF para los Albaranes AC21.

## Fase 1: Configuración Inicial del Microservicio y Docker

### 1.1. Crear Estructura del Proyecto del Microservicio
  - [X] Crear directorio raíz: `cryptotrace-pdf-generator`
  - [X] Crear subdirectorio `app/` para el código fuente.
  - [X] Dentro de `app/`, crear `main.py` (o similar para Flask/FastAPI).
  - [X] Dentro de `app/`, crear directorio `templates/` (con `.gitkeep`).
  - [X] Dentro de `app/`, crear directorio `static/` (con `.gitkeep`).
  - [X] Crear `Dockerfile`.
  - [X] Crear `requirements.txt`.
  - [X] Crear `.dockerignore`.
  - [X] Crear `README.md` con descripción inicial e instrucciones.

### 1.2. Configurar Entorno de Desarrollo (local y Docker)
  - [X] Identificar conflicto de puerto con `docker-compose.yml` existente (puerto 5001 usado por `processing`).
  - [X] Cambiar puerto del microservicio PDF a `5003` (en `Dockerfile`, `app/main.py`, `README.md`).
  - [X] Probar la construcción de la imagen Docker con el nuevo puerto (`docker build -t cryptotrace-pdf-generator .`).
  - [X] Añadir servicio `pdf-generator` al `docker-compose.yml` principal del proyecto.
  - [X] Probar la ejecución del contenedor y el endpoint `/health` a través de `docker-compose up` (`http://localhost:5003/health`).
  - [ ] (Opcional) Configurar Gunicorn para hot-reloading en desarrollo si se usa con volúmenes en `docker-compose.yml`. (Ya incluido con --reload)

### 1.3. Escribir el `Dockerfile` Básico
  - [ ] Elegir imagen base de Python (ej. `python:3.9-slim`).
  - [ ] Añadir comandos para instalar dependencias de sistema operativo para WeasyPrint (Pango, Cairo, GDK-PixBuf, libffi-dev, pkg-config, etc.). Investigar dependencias exactas.
  - [ ] Configurar directorio de trabajo (`WORKDIR`).
  - [ ] Copiar `requirements.txt` al contenedor.
  - [ ] Instalar dependencias Python (`pip install -r requirements.txt`).
  - [ ] Copiar el contenido de `app/` al contenedor.
  - [ ] Definir `CMD` o `ENTRYPOINT` para ejecutar la aplicación (ej. Gunicorn/Uvicorn).

### 1.4. Definir `requirements.txt` Inicial
  - [ ] Añadir `Flask` o `FastAPI`.
  - [ ] Añadir `WeasyPrint`.
  - [ ] Añadir `Jinja2`.
  - [ ] Añadir `gunicorn` (para Flask) o `uvicorn` (para FastAPI).

### 1.5. Implementar Endpoint Básico en `main.py`
  - [ ] Elegir framework (Flask o FastAPI).
  - [ ] Crear un endpoint `POST /generate-ac21-pdf`.
  - [ ] El endpoint debe aceptar datos JSON.
  - [ ] Inicialmente, el endpoint puede solo loguear el JSON recibido y devolver una respuesta simple (ej. "OK") o un PDF muy básico.

### 1.6. Crear Prototipo de Plantilla HTML (`app/templates/ac21_pdf_template.html`)
  - [ ] Crear un archivo HTML básico.
  - [ ] Incluir una estructura mínima (ej. un título "AC21 Documento").
  - [ ] Añadir algunos marcadores de Jinja2 simples (ej. `<h1>AC21: {{ numero_albaran | default('N/A') }}</h1>`).

### 1.7. Pruebas Iniciales
  - [ ] **Prueba Local (sin Docker):**
    - [ ] Ejecutar el microservicio Python directamente.
    - [ ] Enviar una petición POST de prueba (con `curl`, Postman, o script) con un JSON de ejemplo.
    - [ ] Verificar que el endpoint responde y se loguea el JSON.
    - [ ] Si se genera un PDF básico, verificar su contenido.
  - [ ] **Prueba con Docker:**
    - [ ] Construir la imagen Docker (`docker build -t cryptotrace-pdf-generator .`).
    - [ ] Ejecutar el contenedor (`docker run -p 5003:5003 cryptotrace-pdf-generator`). (Ajustar puerto si es necesario).
    - [ ] Repetir la petición POST de prueba al contenedor.
    - [ ] Verificar la respuesta y logs del contenedor. Validar que WeasyPrint funciona en el entorno Docker.

## Fase 2: Desarrollo de la Plantilla HTML/CSS y Lógica de Renderizado

### 2.1. Desarrollar Plantilla HTML (`ac21_pdf_template.html`)
  - [ ] Basándose en `formulario AC21 en blanco.csv` y el diseño del Excel original:
    - [ ] **Sección 1 (Tipo Transacción):** Replicar la selección del tipo de transacción.
    - [ ] **Sección Cabecera (Campos 2-8):** ODMC N., Fecha Informe, N. Reg. Salida, DE (Empresa Origen), PARA (Empresa Destino), Fecha Transacción, N. Reg. Entrada, Códigos Contabilidad. Usar tablas o divs estilizados.
    - [ ] **Sección Líneas de Producto (Campos 9-13):**
      - [ ] Crear una tabla HTML para "TÍTULO CORTO / EDICIÓN", "CANTIDAD", "NÚMERO DE SERIE (INICIO, FIN, CC)", "OBSERVACIONES".
      - [ ] Usar un bucle de Jinja2 (`{% for linea in lineas_producto %}`) para iterar sobre las líneas.
      - [ ] Manejar la posible ausencia de "FIN" o "CC" en números de serie.
    - [ ] **Sección Pie de Página (Campos 14-17):**
      - [ ] Campo 14: "EL MATERIAL HA SIDO" (mostrar opción seleccionada).
      - [ ] Campo 15 y 16: "DESTINATARIO AUTORIZADO" y "TESTIGO/OTRO" (mostrar opciones seleccionadas).
      - [ ] Campo Firmas (a,b,c,d para dos firmantes): Replicar la estructura para nombres, cargos, etc.
      - [ ] Campo 17: "OBSERVACIONES DEL ODMC REMITENTE".
      - [ ] Información de paginación (ej. "Página X de Y").
  - [ ] Asegurar que todos los datos dinámicos se inserten con marcadores Jinja2 correctos.

### 2.2. Desarrollar Estilos CSS
  - [ ] Crear/editar archivo CSS (ej. `app/static/css/ac21_pdf_style.css`) o estilos en `<head>`.
  - [ ] **Configuración `@page`**:
    - [ ] Definir tamaño de página (ej. A4, landscape/portrait según el Excel).
    - [ ] Establecer márgenes.
    - [ ] (Opcional Avanzado) Definir cabeceras/pies de página repetitivos con `running elements` si es necesario (ej. número de albarán en cada página).
  - [ ] **Estilos de Tabla**: Bordes, padding, alineación, `colspan`/`rowspan` equivalentes.
  - [ ] **Estilos de Layout**: Posicionamiento de secciones, espaciado.
  - [ ] **Fuentes**: Definir familias de fuentes, tamaños. Considerar si se necesitan fuentes específicas y cómo WeasyPrint las accederá.
  - [ ] **Control de Saltos de Página**: `page-break-before`, `page-break-after`, `page-break-inside` para evitar cortes inoportunos.

### 2.3. Lógica de Renderizado en `main.py`
  - [ ] Cargar la plantilla HTML con Jinja2.
  - [ ] Renderizar la plantilla HTML pasándole el contexto de datos (JSON recibido).
  - [ ] Convertir el HTML renderizado a PDF usando `HTML(string=html_string).write_pdf()`.
  - [ ] (Opcional) Referenciar el archivo CSS externo en WeasyPrint si se usa uno.
  - [ ] Devolver el PDF como un archivo para descargar (`send_file` en Flask, `FileResponse` en FastAPI).

### 2.4. Iteración y Pruebas de PDF
  - [ ] Preparar diversos JSON de prueba que simulen diferentes AC21 (pocos/muchos productos, textos largos, campos vacíos, etc.).
  - [ ] Generar PDFs y revisarlos minuciosamente comparando con la plantilla Excel.
  - [ ] Ajustar HTML y CSS hasta lograr la fidelidad deseada.

## Fase 3: Integración con el Backend Django

### 3.1. Definir Estructura JSON del AC21 en Django
  - [ ] En la vista Django que solicitará el PDF, identificar todos los campos del modelo `Albaran` y relacionados que se necesitan.
  - [ ] Crear una función o método que construya un diccionario Python con esta información, estructurado de la manera que espera la plantilla Jinja2 del microservicio PDF.

### 3.2. Implementar Endpoint en Django para Solicitar PDF
  - [ ] Crear una nueva ruta y vista en Django (ej. `POST /api/albaranes/<int:albaran_id>/generar-pdf/`).
  - [ ] La vista recuperará el objeto `Albaran` por su ID.
  - [ ] Llamará a la función del paso 3.1 para obtener el diccionario de datos.

### 3.3. Implementar Llamada HTTP desde Django al Microservicio PDF
  - [ ] Usar `requests` (o `httpx`) en la vista Django para hacer una petición POST al endpoint `/generate-ac21-pdf` del microservicio.
  - [ ] Enviar el diccionario de datos como cuerpo JSON.
  - [ ] **Manejo Síncrono (Inicial):**
    - [ ] Recibir la respuesta del microservicio (que contendrá los bytes del PDF).
    - [ ] Crear una `HttpResponse` en Django con el contenido del PDF y el `content_type='application/pdf'`.
    - [ ] Añadir cabecera `Content-Disposition` para sugerir el nombre del archivo.
  - [ ] **Manejo Asíncrono (Consideración para el futuro si la generación es lenta):**
    - [ ] Investigar Celery para tareas en segundo plano.
    - [ ] El microservicio PDF guardaría el archivo y devolvería una URL o ID.
    - [ ] Django manejaría el estado de la tarea.

## Fase 4: Despliegue y Consideraciones Adicionales

### 4.1. Configuración de Despliegue
  - [ ] Integrar el `Dockerfile` del microservicio en el sistema de despliegue existente (ej. Docker Compose, Kubernetes).
  - [ ] Asegurar la comunicación de red entre el backend Django y el microservicio PDF.
  - [ ] Configurar variables de entorno si son necesarias para el microservicio.

### 4.2. Manejo de Errores y Logging
  - [ ] Implementar `try-except` bloques en el microservicio PDF y en la vista Django.
  - [ ] Añadir logging detallado en ambas partes para facilitar la depuración (ej. datos recibidos, errores de WeasyPrint, errores de comunicación).

### 4.3. Seguridad
  - [ ] Evaluar la necesidad de proteger el endpoint del microservicio PDF si no está en una red interna segura.
    - [ ] (Opcional) Considerar un token de API simple o autenticación basada en IP/red.

### 4.4. Pruebas End-to-End
  - [ ] Probar el flujo completo: desde el clic en el frontend (si ya existe la UI), pasando por Django, al microservicio PDF, y la descarga del archivo.
  - [ ] Validar con varios AC21 diferentes.

## Tareas Adicionales/Mejoras Futuras
  - [ ] **Almacenamiento de PDFs Generados**: Si los PDFs deben persistir, definir dónde (S3, GCS, disco local) y cómo se gestionan.
  - [ ] **Optimización de CSS para WeasyPrint**: Investigar características específicas de WeasyPrint para mejor control.
  - [ ] **Internacionalización (i18n)**: Si el AC21 necesita estar en varios idiomas.
  - [ ] **Pruebas Unitarias y de Integración** para el microservicio.

Este plan debería proporcionar una buena guía. ¡Avísame si quieres ajustar algo o añadir más detalles!
