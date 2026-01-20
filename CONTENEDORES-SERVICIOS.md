# Contenedores y Servicios

## CryptoTrace

### Servicios en Producción

| Servicio | Contenedor | Puerto Interno | Puerto Externo | Descripción |
|----------|------------|---------------|----------------|-------------|
| **Backend Django** | `cryptotrace-backend` | 8080 | 127.0.0.1:8080 | API principal, WebSocket agente IA |
| **Frontend Next.js** | `cryptotrace-frontend` | 3000 | 127.0.0.1:3000 | Interfaz de usuario CryptoTrace |
| **OCR** | `cryptotrace-ocr` | 8000 | 127.0.0.1:8000 | Servicio de reconocimiento óptico |
| **Processing** | `cryptotrace-processing` | 5001 | 127.0.0.1:5001 | Procesamiento de documentos |
| **PDF Generator** | `cryptotrace-pdf-generator` | 5003 | 127.0.0.1:5003 | Generación de PDFs |
| **PostgreSQL** | `cryptotrace-db` | 5432 | (interno) | Base de datos compartida |
| **Redis** | `cryptotrace-redis` | 6379 | (interno) | Caché y broker Celery |
| **Celery Worker** | `cryptotrace-celery-worker` | - | - | Tareas asíncronas (emails, etc.) |
| **Celery Beat** | `cryptotrace-celery-beat` | - | - | Tareas periódicas |

### Servicios en Desarrollo

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **Backend Django** | 8080 | API principal |
| **Frontend Next.js** | 3000 | Interfaz de usuario |
| **OCR** | 8002 | Servicio OCR |
| **Processing** | 5001 | Procesamiento |
| **PDF Generator** | 5003 | Generación PDFs |
| **PostgreSQL** | 5432 | Base de datos |
| **Redis** | 6379 | Caché y Celery |

## HPS System

### Servicios en Producción

| Servicio | Contenedor | Puerto Interno | Puerto Externo | Descripción |
|----------|------------|---------------|----------------|-------------|
| **Frontend React** | `hps_frontend` | 80 | 127.0.0.1:3001 | Interfaz de usuario HPS |

**Nota:** El backend de HPS System está integrado en `cryptotrace-backend` (Django). El agente IA también corre dentro de Django Channels.

## Acceso desde Internet

Todos los servicios están detrás de Nginx (en el host) que actúa como reverse proxy:

- **CryptoTrace**: `https://seguridad.idiaicox.com`
- **HPS System**: `https://seguridad.idiaicox.com/hps`
- **API Backend**: `https://seguridad.idiaicox.com/api`
- **WebSocket**: `wss://seguridad.idiaicox.com/ws`

## Comandos Útiles

### Ver contenedores corriendo

```bash
# Todos los contenedores
docker ps

# Solo CryptoTrace
cd /opt/thot-security/cryptotrace
docker compose -f docker-compose.prod.yml ps

# Solo HPS System
cd /opt/thot-security/hps-system
docker compose -f docker-compose.prod.yml ps
```

### Ver logs

```bash
# Logs de un servicio específico
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend

# Logs de todos los servicios
docker compose -f docker-compose.prod.yml logs -f
```

### Reiniciar servicios

```bash
# Reiniciar un servicio específico
docker compose -f docker-compose.prod.yml restart backend

# Reiniciar todos los servicios
docker compose -f docker-compose.prod.yml restart
```

### Reconstruir y levantar

```bash
# Reconstruir un servicio
docker compose -f docker-compose.prod.yml build backend

# Reconstruir y levantar
docker compose -f docker-compose.prod.yml up -d --build backend
```
