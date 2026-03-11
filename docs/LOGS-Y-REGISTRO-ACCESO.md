# Logs estructurados y registro de acceso

## 1. Logs estructurados (criterios de calidad)

El backend escribe **logs en formato JSON** (una línea por evento) en:

- **Archivo:** `cryptotrace-backend/src/logs/django_structured.json`  
  (o la ruta equivalente según `BASE_DIR` en el proyecto).

Cada línea es un objeto JSON con campos como:

- `timestamp`: fecha/hora ISO
- `level`: nivel (INFO, WARNING, ERROR, etc.)
- `logger`: nombre del logger (django, hps_core, hps_agent, celery)
- `message`: mensaje
- `module`, `funcName`, `lineno`: ubicación en código
- Cualquier `extra` pasado al logger

**Configuración:** En `cryptotrace_backend/settings.py`, el formateador `json` y el handler `file_json` están definidos en `LOGGING`. Los loggers `django`, `hps_agent`, `hps_core` y `celery` envían también a `file_json`.

Para **exportar o analizar** estos logs: usar el archivo anterior (copiarlo, enviarlo a un sistema de análisis, o leerlo por líneas y parsear cada línea como JSON).

---

## 2. Registro de acceso de usuarios (UserAccessLog)

Cada petición HTTP (excepto estáticos, media y algunas rutas de desarrollo) se registra en la tabla **UserAccessLog** con:

- Usuario (o anónimo)
- Ruta (`path`) y método HTTP
- Código de respuesta
- IP (respeta `X-Forwarded-For` si hay proxy)
- User-Agent
- Tiempo de respuesta (ms)
- Fecha/hora

**Desactivar el registro:** En `settings.py` (o en `settings_prod.py` / `settings_dev.py`) añadir:

```python
ACCESS_LOG_ENABLED = False
```

**Rutas que no se registran:** `/static/`, `/media/`, `/favicon.ico`, `/__debug__/` (configurable en `hps_core.middleware.ACCESS_LOG_SKIP_PREFIXES`).

---

## 3. Exportar desde el admin de Django

### Registro de acceso (UserAccessLog)

1. Entrar en **Admin de Django** → sección **Monitorización** → **Registros de acceso**.
2. Aplicar filtros si se desea (fecha, método, código de respuesta, etc.).
3. Seleccionar los registros a exportar (o "Seleccionar todo" con el filtro aplicado).
4. En "Acción" elegir **Exportar a CSV** y pulsar "Ejecutar".
5. Se descargará un CSV con columnas: Fecha, Usuario, Método, Ruta, Código, IP, User-Agent, Tiempo (ms).

### Logs de auditoría HPS (HpsAuditLog)

1. **Admin** → **Logs de auditoría HPS**.
2. Filtrar si se desea por acción, tabla, fecha.
3. Seleccionar registros (o todos los del filtro).
4. Acción **Exportar a CSV** → Ejecutar.
5. CSV con: Fecha, Usuario, Acción, Tabla, ID Registro, IP, User-Agent.

Los CSV usan **UTF-8 con BOM** para abrirlos correctamente en Excel.

---

## 4. Migración en producción (VPS)

Para que el registro de acceso funcione en el VPS, hay que aplicar la migración **hps_core.0009_useraccesslog**:

```bash
cd /opt/thot-security/cryptotrace
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

Ver [Checklist de actualización VPS](produccion/CHECKLIST-ACTUALIZACION-VPS.md) (sección «Migración 0009 – Registro de acceso»).

---

## 5. Resumen

| Elemento | Dónde | Exportación |
|----------|--------|-------------|
| Logs estructurados (app) | Archivo `logs/django_structured.json` | Copiar archivo o ingestarlo en tu herramienta |
| Registro de acceso HTTP | Modelo `UserAccessLog` (admin) | Admin → Acción "Exportar a CSV" |
| Logs de auditoría HPS | Modelo `HpsAuditLog` (admin) | Admin → Acción "Exportar a CSV" |

**VPS:** aplicar migración `hps_core.0009_useraccesslog` con `python manage.py migrate` (véase sección 4).
