# Microservicio Generador de PDF para AC21 (cryptotrace-pdf-generator)

Este microservicio es responsable de generar documentos PDF para los Albaranes AC21. Utiliza Flask como framework web, Jinja2 para la gestión de plantillas HTML, y WeasyPrint para la conversión de HTML+CSS a PDF.

## Descripción General

El servicio expone un endpoint HTTP al que se le pueden enviar los datos de un AC21 en formato JSON. A partir de estos datos y una plantilla HTML/CSS interna (basada en el diseño del formulario oficial AC21), genera un documento PDF que se devuelve en la respuesta o se gestiona de forma asíncrona (pendiente de definir según necesidad).

## Prerrequisitos para Desarrollo Local

- Python 3.9+
- pip (gestor de paquetes de Python)
- Docker (y Docker Compose, opcionalmente para orquestación local)
- Dependencias de sistema para WeasyPrint (consultar `Dockerfile` o documentación de WeasyPrint, ej. Pango, Cairo, GDK-PixBuf).

## Configuración y Ejecución Local (sin Docker)

1.  **Clonar el repositorio (si aplica) y navegar al directorio `cryptotrace-pdf-generator`.**
2.  **Crear un entorno virtual (recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```
3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Ejecutar la aplicación Flask (para desarrollo):**
    El archivo `app/main.py` se puede ejecutar directamente:
    ```bash
    python app/main.py
    ```
    Esto iniciará un servidor de desarrollo Flask (usualmente en `http://127.0.0.1:5003` o `http://0.0.0.0:5003`).

## Construcción y Ejecución con Docker

1.  **Construir la imagen Docker:**
    Desde el directorio raíz (`cryptotrace-pdf-generator`), ejecutar:
    ```bash
    docker build -t cryptotrace-pdf-generator .
    ```
2.  **Ejecutar el contenedor Docker:**
    ```bash
    docker run -p 5003:5003 --name pdf_generator_service cryptotrace-pdf-generator
    ```
    Esto expondrá el puerto 5003 del contenedor al puerto 5003 de la máquina host. La aplicación será accesible en `http://localhost:5003`.

## Endpoints de la API

-   **`POST /generate-ac21-pdf`**: 
    -   **Descripción**: Genera un PDF para un AC21.
    -   **Cuerpo de la Petición (Request Body)**: JSON con los datos del AC21. La estructura exacta se definirá según los campos necesarios en la plantilla `ac21_pdf_template.html`.
    -   **Respuesta Exitosa (Success Response)**:
        -   Código: `200 OK`
        -   Contenido: El archivo PDF generado (Content-Type: `application/pdf`), o un JSON con un mensaje de estado y/o URL al PDF si la generación es asíncrona.
    -   **Respuesta de Error (Error Response)**:
        -   Código: `400 Bad Request` (si los datos son inválidos o faltan).
        -   Código: `500 Internal Server Error` (si ocurre un error durante la generación del PDF).
-   **`GET /health`**: 
    -   **Descripción**: Verifica el estado de salud del servicio.
    -   **Respuesta Exitosa (Success Response)**:
        -   Código: `200 OK`
        -   Contenido: `{"status": "ok"}`

## Plantillas

-   La plantilla principal para el PDF del AC21 se encuentra en `app/templates/ac21_pdf_template.html`.
-   Los estilos CSS asociados pueden estar en `app/static/css/` o incrustados en la plantilla HTML.

## Variables de Entorno (si se implementan)

-   (Por definir, si son necesarias para la configuración en producción, ej. `LOG_LEVEL`).

## Tareas Pendientes y Hoja de Ruta

Consultar el archivo `TASK.md` para ver el plan de implementación detallado y el estado de las tareas.