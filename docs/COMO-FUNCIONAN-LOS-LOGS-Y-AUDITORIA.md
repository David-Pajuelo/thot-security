# Cómo funcionan los logs y la auditoría

En el proyecto hay **tres cosas** distintas que a veces se nombran como “logs” o “auditoría”. Aquí se explica qué es cada una, cómo se crean y en qué se basan.

---

## 1. Registro de acceso HTTP (UserAccessLog) — lo que sí implementamos

### Qué es

Un **registro de cada petición HTTP** que llega al backend: quién (usuario o anónimo), a qué ruta, con qué método, código de respuesta, IP, user-agent y tiempo de respuesta. Sirve para trazabilidad de accesos y criterios de calidad.

### En qué se basa

- **Middleware de Django.** No depende de que ninguna vista o modelo “decida” registrar: todas las peticiones pasan por el middleware.

### Cómo se crea

1. En **`hps_core/middleware.py`** está `AccessLogMiddleware`.
2. En **`process_request`**: si la ruta no está excluida y el registro está activo, se guarda en `request._access_log_start` el momento de inicio (para medir tiempo).
3. En **`process_response`**:  
   - Si no está excluida la ruta y existe `_access_log_start`, se crea **un registro en la tabla `UserAccessLog`** con:
     - `user` (el `request.user` si está autenticado, si no `null`)
     - `path` (ruta, hasta 500 caracteres)
     - `method` (GET, POST, etc.)
     - `status_code` (código HTTP de la respuesta)
     - `ip_address` (de `REMOTE_ADDR` o del primer valor de `X-Forwarded-For` si hay proxy)
     - `user_agent`
     - `response_time_ms` (tiempo desde `process_request` hasta `process_response`)
     - `created_at` (automático)

4. El middleware se registra en **`cryptotrace_backend/settings.py`** en `MIDDLEWARE` (al final):  
   `'hps_core.middleware.AccessLogMiddleware'`.

### Qué rutas no se registran

Las que empiezan por: `/static/`, `/media/`, `/favicon.ico`, `/__debug__`. Están en `ACCESS_LOG_SKIP_PREFIXES` en el mismo middleware.

### Cómo desactivarlo

En settings: `ACCESS_LOG_ENABLED = False`.

### Dónde se guarda

En la base de datos, tabla del modelo **`UserAccessLog`** (app **Monitorización**, `monitorizacion/models.py`). En el admin: **Monitorización** → Registros de acceso. Se puede ver y exportar desde el admin de Django (acción “Exportar a CSV”).

---

## 2. Logs de auditoría HPS (HpsAuditLog) — modelo legacy, sin escritura actual

### Qué es

Un modelo pensado como **bitácora de acciones del sistema HPS**: qué usuario hizo qué acción sobre qué tabla/registro, con valores antiguos y nuevos (auditoría de cambios).

### Estructura del modelo (resumen)

- `user`, `action` (ej. "create", "update"), `table_name`, `record_id` (UUID)
- `old_values` / `new_values` (JSON)
- `ip_address`, `user_agent`, `created_at`

Está en **`hps_core/models.py`**, clase `HpsAuditLog`.

### En qué se basa

- En el **antiguo HPS-System** (otra aplicación) había una tabla `audit_logs` que guardaba estas acciones.
- En Django ese modelo existe para **leer y mostrar** esos datos una vez migrados, y para poder exportarlos desde el admin.

### Cómo se crean actualmente

- **En el código Django actual no se crean nuevos registros.** No hay ningún `HpsAuditLog.objects.create(...)` en vistas, señales ni servicios.
- Los únicos registros que hay son los que se **migraron** desde la base del viejo HPS con el comando:
  - `python manage.py migrate_hps_audit_logs --hps-db-url=...`
- En las vistas (por ejemplo al enviar/rechazar una solicitud HPS) hay comentarios del tipo “crear un audit log”, pero no hay implementación que escriba en `HpsAuditLog`.

Por tanto: **los “logs de auditoría” que ves en el admin son datos históricos/migrados; a partir de ahora no se generan solos.** Si quieres auditoría de acciones en Django, habría que llamar a `HpsAuditLog.objects.create(...)` en los sitios adecuados (vistas, señales, etc.).

---

## 3. Logs estructurados en JSON (archivo)

### Qué es

Los **logs de aplicación** (lo que escribe el módulo `logging` de Python) en un archivo, en formato **una línea JSON por evento**. Sirven para criterios de calidad y análisis (timestamp, nivel, logger, mensaje, módulo, línea, etc.).

### En qué se basa

- Configuración estándar de **logging** de Django/Python.
- Un **formateador custom** que convierte cada registro en un objeto JSON.

### Cómo se crean

- Cualquier `logger.info()`, `logger.warning()`, etc. en el backend (django, hps_core, hps_agent, celery) que use los loggers configurados con el handler `file_json`.
- El **formateador** está en **`cryptotrace_backend/logging_formatters.py`** (clase `JsonFormatter`).
- En **`settings.py`**, en el dict **`LOGGING`**:
  - Se define el formateador `json` y el handler `file_json` que escribe en `logs/django_structured.json`.
  - Los loggers correspondientes tienen asignado ese handler.

No tienen relación directa con “auditoría” de usuarios; son logs de funcionamiento de la aplicación.

---

## Resumen rápido

| Qué | Dónde se guarda | Quién lo crea |
|-----|------------------|----------------|
| **Registro de acceso (UserAccessLog)** | BD, tabla UserAccessLog | Middleware en cada petición HTTP (automático) |
| **Logs de auditoría HPS (HpsAuditLog)** | BD, tabla HpsAuditLog | Solo migración desde el viejo HPS; en Django no se escriben nuevos |
| **Logs estructurados JSON** | Archivo `logs/django_structured.json` | Módulo logging (app, django, hps_agent, celery) |

Si quieres que las **acciones de negocio** (crear/editar solicitudes HPS, cambios de estado, etc.) queden registradas como “auditoría”, habría que añadir en esas vistas (o en señales) la creación de registros en **HpsAuditLog** con `action`, `table_name`, `record_id`, `old_values`, `new_values`, `user`, IP y user-agent.
