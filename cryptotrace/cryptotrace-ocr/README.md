# CryptoTrace OCR Service

Microservicio de procesamiento de documentos AC21 utilizando GPT-4 Vision para la extracción precisa de información.

## Descripción

Este microservicio forma parte del ecosistema CryptoTrace y se encarga de procesar documentos AC21 (documentos de transferencia de equipamiento) utilizando tecnología de visión artificial avanzada a través de GPT-4 Vision.

## Características

- Procesamiento de documentos AC21 mediante GPT-4 Vision
- Extracción precisa de:
  - Información de registro (fechas, números de registro)
  - Códigos de contabilidad
  - Información detallada de empresas (origen y destino)
  - Listado de artículos con números de serie
  - Observaciones y notas adicionales

## Tecnologías

- FastAPI
- GPT-4 Vision (OpenAI)
- Docker
- Python 3.9+

## Configuración

### Variables de Entorno
Crear un archivo `.env` con:
```
OPENAI_API_KEY=tu_api_key_aqui
```

### Instalación con Docker

```bash
# Construir la imagen
docker-compose build

# Levantar el servicio
docker-compose up
```

### Instalación Local

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el servicio
uvicorn app.main:app --reload --port 8002
```

## API Endpoints

### POST /process-image/
Procesa una imagen de documento AC21.

**Request:**
- Multipart form data con:
  - `file`: Archivo de imagen (jpg, png)

**Response:**
```json
{
    "informacion_registro": {
        "fecha_informe": "DD/MM/YYYY",
        "numero_registro_salida": "string",
        "fecha_transaccion": "DD/MM/YYYY",
        "numero_registro_entrada": "string"
    },
    "codigos_contabilidad": {
        "contabilizar_por_serie": boolean,
        "contabilizar_por_cantidad": boolean,
        "aviso_recibo_oficial": boolean
    },
    "empresa_origen": {
        "nombre": "string",
        "direccion": "string",
        "codigo_postal": "string",
        "ciudad": "string",
        "provincia": "string",
        "pais": "string",
        "codigo_odmc": "string",
        "codigo_emad": "string",
        "nif": "string",
        "telefono": "string",
        "email": "string"
    },
    "empresa_destino": {
        "nombre": "string",
        "direccion": "string",
        "codigo_postal": "string",
        "ciudad": "string",
        "provincia": "string",
        "pais": "string",
        "codigo_odmc": "string",
        "codigo_emad": "string",
        "nif": "string",
        "telefono": "string",
        "email": "string"
    },
    "articulos": [
        {
            "descripcion": "string",
            "cantidad": number,
            "numero_serie": "string",
            "kit": "string",
            "observaciones": "string"
        }
    ],
    "observaciones_generales": "string"
}
```

## Documentación

La documentación de la API está disponible en:
- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

## Licencia

MIT License - ver [LICENSE](LICENSE) para más detalles. 