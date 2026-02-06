# Eliminación del backend FastAPI de HPS (obsoleto)

**Fecha:** 2026-02

## Resumen

Se eliminó la carpeta `hps-system/backend` (backend FastAPI) por estar **obsoleto**: la API HPS está integrada en Django (`cryptotrace-backend`, app `hps_core`) y no existía ninguna referencia en tiempo de ejecución al FastAPI.

## Verificación previa

- **Frontend HPS** (`hps-system/frontend`): usa `apiService` con `API_BASE_URL` que apunta al backend Django (configuración por entorno), no al FastAPI.
- **Docker Compose** (hps-system): el servicio `backend` estaba comentado en `docker-compose.prod.yml` y `docker-compose.dev.yml` (“Backend FastAPI se ha migrado a Django”).
- **Extensiones Chrome**: configuradas para hablar con el API en Django (seguridad.idiaicox.com / localhost según entorno).
- **Código en cryptotrace-backend**: solo había comentarios del tipo “Adaptado desde hps-system/backend/...”; no hay imports ni dependencias del código FastAPI.
- **Documentación**: en `docs/archivados/` se menciona el backend como origen de la migración; se mantiene como referencia histórica.

## Contenido eliminado

- **`hps-system/backend/`** – Código completo del backend FastAPI (src/, Dockerfile, requirements, migraciones Alembic, etc.).
- **`hps-system/Temp/`** – Scripts de prueba y utilidades que importaban `src.*` del backend FastAPI; sin el backend carecen de sentido y se consideraron obsoletos.

## Dónde está ahora la lógica HPS

- **API y modelos:** `cryptotrace/cryptotrace-backend/src/hps_core/`
- **Emails HPS:** `hps_core/email_service.py`, `hps_core/tasks.py`, `hps_core/email_templates.py`
- **Notificación a jefes de seguridad (nuevo usuario por formulario):** `hps_core/email_service.py` → `send_new_user_notification_to_security_chiefs`; variable `NOTIFICATION_SECURITY_CHIEFS_EMAIL` en el `.env` del contenedor **cryptotrace-backend**.

## Scripts/docs que siguen mencionando "backend" (legacy)

- `hps-system/docs/despliegue/fix-role-vps.sh` – Referenciaba `backend/verify_and_fix_role.py`; obsoleto (roles se gestionan en Django).
- `scripts/desplegar-hps-system.sh` – Actualizado: ya no ejecuta migraciones ni health check contra un contenedor backend.
- Otras guías en `hps-system/docs/` pueden citar el backend FastAPI; la API real es Django.

## Referencias

- `docs/archivados/planes-implementados/RESUMEN-INTEGRACION-COMPLETA.md`
- `docs/archivados/planes-implementados/PLAN-INTEGRACION-CELERY-REDIS-EMAIL.md`
- `CONTENEDORES-SERVICIOS.md` – Backend HPS integrado en cryptotrace-backend (Django).
