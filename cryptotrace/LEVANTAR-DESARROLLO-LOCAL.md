# Guía para Levantar CryptoTrace en Desarrollo Local

## Prerrequisitos

1. Docker y Docker Compose instalados
2. Git configurado
3. Archivo `.env` configurado en `cryptotrace-backend/`

## Pasos para Levantar el Servicio

### 1. Verificar configuración del .env

Asegúrate de que el archivo `cryptotrace-backend/.env` tenga la API key de OpenAI en una sola línea:

```bash
# Verificar que OPENAI_API_KEY esté en una sola línea
cat cryptotrace-backend/.env | grep OPENAI_API_KEY
```

Si la API key está dividida en múltiples líneas, edítala para que esté en una sola línea sin saltos.

### 2. Levantar los servicios

```bash
cd cryptotrace
docker compose up -d
```

Esto levantará:
- **Backend Django** (puerto 8080)
- **Frontend Next.js** (puerto 3000)
- **Processing** (puerto 5001)
- **OCR** (puerto 8002)
- **PDF Generator** (puerto 5003)
- **PostgreSQL** (puerto 5432)
- **Redis** (puerto 6379)
- **Celery Worker** y **Celery Beat**

### 3. Ejecutar migraciones

```bash
docker compose exec backend python manage.py migrate
```

### 4. Crear superusuario (si es necesario)

```bash
docker compose exec backend python manage.py createsuperuser
```

### 5. Verificar que los servicios estén corriendo

```bash
docker compose ps
```

### 6. Ver logs del backend

```bash
docker compose logs backend -f
```

## URLs de Desarrollo

- **Backend API**: http://localhost:8080/api
- **Frontend CryptoTrace**: http://localhost:3000
- **Processing**: http://localhost:5001
- **OCR**: http://localhost:8002
- **PDF Generator**: http://localhost:5003
- **Admin Django**: http://localhost:8080/admin

## Probar la API Key de OpenAI

Una vez levantado el servicio, puedes probar la API key ejecutando:

```bash
docker compose exec backend python -c "
from openai import OpenAI
import os
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': 'test'}],
            max_tokens=5
        )
        print('✅ API key válida')
    except Exception as e:
        print(f'❌ Error: {e}')
else:
    print('❌ API key no encontrada')
"
```

## Probar el Agente IA

1. Accede al frontend: http://localhost:3000
2. Inicia sesión con un usuario
3. Abre el chat del agente IA
4. Prueba comandos como:
   - "listado de equipos"
   - "envia hps a test@example.com"
   - "estado hps de test@example.com"

## Detener los servicios

```bash
docker compose down
```

Para eliminar también los volúmenes (base de datos y Redis):

```bash
docker compose down -v
```

## Solución de Problemas

### Error: "OPENAI_API_KEY no está configurada"
- Verifica que el archivo `.env` exista en `cryptotrace-backend/`
- Verifica que la variable `OPENAI_API_KEY` esté definida
- Asegúrate de que la API key esté en una sola línea

### Error: "Error code: 401 - Incorrect API key provided"
- Verifica que la API key sea válida en https://platform.openai.com/account/api-keys
- Verifica que la API key no tenga espacios o saltos de línea
- Verifica que la cuenta de OpenAI tenga créditos disponibles

### Error: "Connection refused" o servicios no inician
- Verifica que los puertos no estén en uso: `netstat -an | grep -E "8080|3000|5001|8002|5432|6379"`
- Detén otros servicios que puedan estar usando esos puertos
- Revisa los logs: `docker compose logs [servicio]`

### Error: "Module not found" o errores de importación
- Reconstruye las imágenes: `docker compose build`
- Verifica que los volúmenes estén montados correctamente

## Reconstruir después de cambios en el código

```bash
docker compose build
docker compose up -d
```

## Ver logs de todos los servicios

```bash
docker compose logs -f
```

## Ver logs de un servicio específico

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f processing
```

