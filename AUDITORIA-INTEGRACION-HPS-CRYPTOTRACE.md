# Auditoría de integración `hps-system` ➜ `cryptotrace`

## Resumen ejecutivo
- **Objetivo**: migrar gradualmente el backend FastAPI de `hps-system` al stack Django de `cryptotrace`, unificando dominio, autenticación y despliegue bajo un solo servicio Django/DRF y reutilizando los microservicios existentes (OCR, processing, PDF).
- **Hallazgos clave**: ambos sistemas comparten PostgreSQL y Redis pero difieren en frameworks y modelos de datos. `cryptotrace` cubre inventario y AC21; `hps-system` aporta solicitudes HPS, chat IA, extensiones de navegador y pipeline de correo/Celery. La conversión exige mapear los modelos SQLAlchemy a Django ORM, portar endpoints FastAPI a DRF y absorber tareas Celery en la infraestructura de `cryptotrace`.
- **Recomendación general**: establecer un plan de migración en fases donde Django incorpora módulos equivalentes (usuarios/roles, HPS, chat, email) mientras FastAPI se congela. Durante la transición, exponer adaptadores temporales (APIs, ETL) hasta desactivar completamente el backend FastAPI.

## Alcance y supuestos
- Se audita únicamente el backend (`cryptotrace-backend` y `hps-system/backend` + servicios de soporte). Frontend y extensiones quedan fuera salvo dependencias críticas.
- No se contemplan aún cambios en agentes IA ni en OCR/PDF; se asume disponibilidad de los repos actuales y permisos sobre Docker/DB.
- Se asume que `cryptotrace` será el backend definitivo; `hps-system` servirá únicamente como fuente de funcionalidades/DOMINIO durante la migración, sin quedar como servicio independiente una vez completado el proceso.

## Inventario técnico actual

### CryptoTrace
- **Stack**: Django 4.2, DRF + JWT SimpleJWT, PostgreSQL, Redis, servicios auxiliares (processing FastAPI, OCR, PDF). Configuración CORS amplia y dependencias cargadas vía `.env`.  
```57:123:cryptotrace/cryptotrace-backend/src/cryptotrace_backend/settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}
...
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL', 'postgres://cryptotrace_user:cryptotrace_pass@db:5432/cryptotrace_db')
    )
}
```
- **Dominio principal**: módulo `productos` con modelos de inventario, albaranes AC21, empresas y perfiles extendidos; lógica de recalculo ante borrados y plantillas de correo.  
```80:205:cryptotrace/cryptotrace-backend/src/productos/models.py
class InventarioProducto(models.Model):
    producto = models.ForeignKey(CatalogoProducto, ...)
...
class Albaran(models.Model):
    TIPO_DOCUMENTO_CHOICES = [...]
    direccion_transferencia = models.CharField(...)
    accesorios = models.JSONField(...)
    estado_material = models.CharField(...)
```
- **Orquestación**: `docker-compose.yml` levanta backend Django (puerto 8080), servicios FastAPI (`cryptotrace-processing`, OCR, PDF), frontend Next.js y un PostgreSQL 15 compartido.  
```1:110:cryptotrace/docker-compose.yml
services:
  backend:
    build: ./cryptotrace-backend
    command: ["python", "manage.py", "runserver", "0.0.0.0:8080"]
  processing:
    build: ./cryptotrace-processing
    command: ["uvicorn", "app.main:app", "--port", "5001"]
  ocr:
    build: ./cryptotrace-ocr
...
  db:
    image: postgres:15
```

### HPS-System
- **Stack**: FastAPI 0.104 + SQLAlchemy 2, Celery con Redis, PostgreSQL, integración de correo SMTP/IMAP, agentes IA y chat. Arranque realiza health-check de DB, migraciones y creación de tablas automáticamente.  
```75:191:hps-system/backend/src/main.py
app = FastAPI(..., lifespan=lifespan)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(hps_router, prefix="/api/v1/hps")
...
@app.get("/health")
async def health_check():
    if check_db_connection():
        return {"status": "healthy", ...}
```
- **Infra**: `docker-compose.prod.yml` define servicios `backend`, `agente-ia`, `redis`, `celery-worker`, `frontend` y `db`, conectados por red dedicada e inician con healthchecks.  
```6:214:hps-system/docker-compose.prod.yml
services:
  db:
    image: postgres:15-alpine
  backend:
    build: ./backend
    environment:
      - POSTGRES_HOST=${POSTGRES_HOST}
      - REDIS_HOST=${REDIS_HOST}
  celery-worker:
    command: celery -A src.celery_app worker --queues=email,analysis,default
```
- **Asíncrono y colas**: Celery usa Redis broker/backend, rutas separan colas `email`, `analysis`, `default`.  
```1:63:hps-system/backend/src/celery_app.py
celery_app = Celery(
    "hps_system",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    include=[
        "src.tasks.email_tasks",
        "src.tasks.analysis_tasks"
    ]
)
```
- **Dominio**: modelos `User`, `Role`, `Team`, `HPSRequest`, `AuditLog`, tokens para plantillas y endpoints especiales para extensiones y chat.

## Análisis de compatibilidad
- **Frameworks**: Django será el runtime único. Se necesita inventariar controladores FastAPI y diseñar equivalentes en DRF (routers, serializers, viewsets). Algunas piezas (websocket/chat) requerirán Channels o servicio separado que Django orqueste.
- **Autenticación**: CryptoTrace usa SimpleJWT mientras HPS genera tokens propios. El plan es convertir todo al pipeline SimpleJWT (o equivalente OIDC) y reescribir el middleware FastAPI en DRF, asegurando paridad de claims (roles, teams, scopes).
- **Base de datos**: ambos usan PostgreSQL. La migración consiste en mapear modelos SQLAlchemy (`User`, `Role`, `Team`, `HPSRequest`, etc.) a modelos Django, crear migraciones y ejecutar scripts ETL para mover datos desde la base HPS (o desde dumps) hacia los nuevos modelos en la base de CryptoTrace.
- **Redis / Celery**: `cryptotrace` aún no expone Celery, pero la funcionalidad asíncrona de HPS (emails, análisis, agente IA) puede migrarse creando una app `celery.py` en Django y reutilizando la configuración actual de colas. Alternativa temporal: mantener el worker FastAPI hasta portar todas las tareas.
- **Correo e integraciones**: unificar configuración SMTP/IMAP en `settings.py` y portar lógica de plantillas y sincronización de buzón a Django.
- **Observabilidad**: Django ya genera logs centralizados; al absorber FastAPI desaparecerá la dispersión, pero se recomienda mantener health checks y métricas equivalentes.

## Brecha funcional
| Dominio | CryptoTrace | HPS-System | Necesidad de integración |
|---------|-------------|------------|--------------------------|
| Gestión de inventario y AC21 | Sí (`productos`, `Albaran`, recalculo inventario) | No | Exponer datos de inventario al flujo HPS para asociar material a solicitudes |
| Gestión de habilitaciones personales | No | Sí (`HPSRequest`, `teams`) | Añadir endpoints en Django que consuman HPS o migrar lógica |
| Usuarios y roles | Django Auth + `UserProfile` | SQLAlchemy `User`, `Role` | Unificar usuarios maestros y forzar sincronización de roles |
| Automatización/IA | OCR, processing, PDF | Agente IA, chat, Chrome extensions | Definir flujos cross-service (ej. IA dispara generación de AC21) |
| Asíncrono | No Celery | Celery (email, analysis) | Decidir si se incorpora Celery al stack general o se reimplementa con Django tasks |

## Plan de integración propuesto

### Fase 0 – Preparación
1. **Congelar nuevas features en FastAPI**: priorizar bugfixes únicamente. Documentar endpoints, modelos y tareas actuales.
2. **Inventario de variables y secretos**: centralizar `.env` en `cryptotrace` (JWT, SMTP, Redis, IMAP, OpenAI). Crear matriz de equivalencias.
3. **Dump de base HPS**: generar export SQL/CSV + diccionario de datos para planificar migraciones a Django.

### Fase 1 – Infraestructura base en Django
1. **Crear apps Django específicas** (todo bajo `cryptotrace`):
   - `hps_core` (ya iniciada) para roles, equipos, plantillas, solicitudes, tokens, auditoría.
   - `hps_auth` o integración directa con `rest_framework_simplejwt` para login/logout, gestión de usuarios y perfiles HPS.
   - `hps_chat` (Django Channels) y `hps_integrations` (extensiones, email).
2. **Modelado**: terminar la traducción de todos los modelos SQLAlchemy a Django (faltan chat, equipos avanzados, métricas, plantillas de email, etc.).
3. **Serializers y viewsets**: replicar endpoints `api/v1/...` usando DRF (autenticación, users, teams, HPS, chat, email, extension). Documentar mapping FastAPI ➜ DRF.
4. **Celery en CryptoTrace**: crear `cryptotrace-backend/celery.py`, configurar broker Redis y portar tareas `src.tasks.email_tasks` y `analysis_tasks`.

### Fase 2 – Migración de datos y autenticación
1. **ETL de usuarios/roles**: scripts de management Django que lean la BD FastAPI (o dumps) y creen usuarios, equipos y roles equivalentes, mapeando contraseñas y flags (`must_change_password`).
2. **Tokens y sesiones**: migrar a SimpleJWT, generando refresh tokens para usuarios activos. Reemplazar el emisor FastAPI por endpoints DRF.
3. **Solicitudes HPS**: importar registros históricos, incluyendo estados, logs y archivos asociados (PDF, plantillas). Ajustar `FileField`/`JSONField` según corresponda.
4. **Email y monitoreo**: mover configuración SMTP/IMAP a `settings.py` y portar servicios (lectura de bandeja, envío de notificaciones) a Celery Django.

### Fase 3 – Integraciones avanzadas (chat, extensiones, IA)
1. **Chat y agente IA**: decidir si se reescribe en Django Channels o se mantiene el servicio `agente-ia` independiente pero consumiendo APIs Django. Documentar contratos `/chat` y `/ws`.
2. **Extensiones navegador**: actualizar endpoints a las nuevas rutas DRF. Exponer compatibilidad temporal mediante proxy si aún se apoya en FastAPI.
3. **Automatización AC21 ↔ HPS**: crear señales/tareas en Django que conecten inventario con solicitudes HPS (generar AC21 al aprobar solicitud, actualizar inventario cuando se destruye material, etc.).

### Fase 4 – Retiro de FastAPI y hardening
1. **Plan de corte**: liberar versión Django con funcionalidades equivalentes, ejecutar pruebas E2E y, una vez verificada, poner FastAPI en modo read-only.
2. **Desmantelar servicios**: eliminar contenedores `hps-backend`, `celery-worker` y `redis` específicos, conservando solo los componentes migrados.
3. **Hardening**: reforzar CORS, CSRF, logging, métricas y backup dentro del stack Django ya unificado.
4. **Documentación final**: actualizar README y manuales para reflejar el nuevo backend único.

## Riesgos y mitigaciones
- **Desalineación de modelo de usuarios**: riesgo de dobles credenciales. Mitigar fijando autoridad única y bloqueando alta directa en HPS salvo API.
- **Sobrecarga instancia Postgres**: al compartir, se incrementan conexiones (Celery workers). Ajustar `pool_size` y habilitar PgBouncer.
- **Secretos expuestos**: `settings.py` contiene `SECRET_KEY` hardcodeado. Migrar a variables de entorno y rotar credenciales antes de exponer servicios.
- **Ancho de banda WebSocket**: las extensiones HPS necesitan tiempo real; asegurar que proxies soporten `upgrade`.
- **Compatibilidad de versiones Python**: verificar versiones base (Django Python 3.11?, FastAPI 3.11). Homologar imágenes para reducir superficie de vulnerabilidades.

## Checklist de acciones inmediatas
1. [ ] Inventariar endpoints/tareas críticos de FastAPI y definir equivalentes en Django.
2. [ ] Diseñar modelo de datos Django para roles, equipos y solicitudes HPS (diagramas + migraciones iniciales).
3. [ ] Configurar Celery dentro de `cryptotrace-backend` y validar conexión a Redis existente.
4. [ ] Preparar ETL de usuarios/roles desde la BD de `hps-system`.
5. [ ] Consolidar variables de entorno en `cryptotrace/.env` (JWT, SMTP, OpenAI, IMAP).
6. [ ] Documentar contratos API (OpenAPI FastAPI + blueprint DRF) y publicarlos en la raíz.
7. [ ] Definir plan de pruebas E2E para garantizar paridad de comportamiento antes de desconectar FastAPI.

---
**Seguimiento**: mantener este documento en la raíz del workspace y actualizarlo tras cada hito de integración.

