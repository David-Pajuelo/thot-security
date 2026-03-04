# Checklist al actualizar el VPS

Usar este checklist cada vez que se actualice el código en el VPS (pull, despliegue nuevo, etc.) para no olvidar pasos críticos.

**En la VPS** el despliegue es un único Docker con ambos bloques de servicio:
- **HPS:** su frontend (React).
- **CryptoTrace:** frontend (Next.js), backend (Django), OCR, processing, pdf-generator, Celery, etc.

Si usas un solo `docker-compose` en la raíz que incluye ambos, ejecuta los comandos desde ese directorio. Si tienes dos composes separados (`cryptotrace/` y `hps-system/`), sigue las secciones que indican cada directorio.

---

## 0. Si se queda en "Removing" (red o contenedores)

Al hacer `docker compose down` (o un rebuild que pare los servicios), puede aparecer algo como:

```text
⠋ Network cryptotrace_cryptotrace-network Removing
```

**Es normal que tarde 1–2 minutos.** Docker desconecta los contenedores de la red y luego la elimina. Espera un poco.

- Si lleva **más de 4–5 minutos** sin avanzar: pulsa `Ctrl+C`, comprueba contenedores y redes, y si hace falta elimina la red a mano:
  ```bash
  docker ps -a
  docker network ls
  docker network rm cryptotrace_cryptotrace-network
  ```
- Para **evitar** este paso cuando solo quieres actualizar: no hagas `down`; usa solo `up -d --build` (véase sección 4). Así no se elimina la red.

---

## 1. Migraciones de base de datos (CryptoTrace backend)

**Importante:** En la VPS las **adiciones a la base de datos** (nuevas columnas, tablas o datos) solo se aplican cuando ejecutas las migraciones. Si actualizas el código pero no ejecutas `migrate`, el backend puede fallar (por ejemplo, error al hacer login o al cargar el perfil si falta una columna). **Tras cada actualización de código**, ejecutar las migraciones en el VPS:

```bash
cd /opt/thot-security/cryptotrace
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

### Migración a recordar: HPS – usuarios con múltiples equipos

Si en el repositorio está la migración **`hps_core.0005_populate_team_memberships_from_profile`** (usuarios HPS con múltiples equipos / `HpsTeamMembership`), **hay que ejecutar `migrate` en el VPS** para:

- Poblar la tabla de membresías de equipo a partir de los perfiles existentes (`HpsUserProfile.team`).
- Dejar el sistema usando `HpsTeamMembership` como fuente de verdad para la relación usuario–equipo(s).

Sin este paso, la funcionalidad de varios equipos por usuario no quedará aplicada en producción.

**Comandos (producción):**

```bash
cd /opt/thot-security/cryptotrace
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
# Ver estado de migraciones (opcional):
docker compose -f docker-compose.prod.yml exec backend python manage.py showmigrations hps_core
```

---

### Revertir la migración HPS 0005 (volver al punto anterior)

Solo tiene sentido si haces **rollback de código** (volver al commit anterior a esta actualización). La migración 0005 **solo inserta datos** en la tabla `hps_core_hpsteammembership`; no crea tablas nuevas (la tabla ya existe desde 0001). El reverse de 0005 es un no-op (no borra filas).

**Pasos para revertir al estado anterior:**

1. **Revertir el código** al commit anterior (por ejemplo el commit antes de “HPS: usuarios multi-equipo…”):
   ```bash
   cd /opt/thot-security
   git log --oneline -5   # anotar el commit anterior al actual
   git checkout <commit-anterior>
   # o: git revert HEAD --no-edit  (crea un commit que deshace el último)
   ```

2. **Desaplicar la migración 0005** (Django marcará 0005 como no aplicada; los datos insertados por 0005 **se quedan** en la BD porque el reverse es no-op):
   ```bash
   cd /opt/thot-security/cryptotrace
   docker compose -f docker-compose.prod.yml exec backend python manage.py migrate hps_core 0004_add_waiting_dps_status
   ```

3. **Opcional – vaciar la tabla de membresías** si quieres dejar la BD sin los datos que insertó 0005 (el código antiguo usa solo `HpsUserProfile.team`):
   ```bash
   docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
   from hps_core.models import HpsTeamMembership
   n = HpsTeamMembership.objects.count()
   HpsTeamMembership.objects.all().delete()
   print(f'Eliminadas {n} filas de HpsTeamMembership')
   "
   ```

4. **Reiniciar backend** tras el cambio de código:
   ```bash
   docker compose -f docker-compose.prod.yml restart backend
   ```

**Resumen:** Con código revertido + `migrate hps_core 0004` vuelves a un estado funcional anterior. Borrar `HpsTeamMembership` es opcional; el código antiguo no usa esa tabla para la lógica principal (usa `profile.team`).

---

### Actualización: Equipos liderados y equipo predeterminado (HPS)

Si en el repositorio están los cambios de **equipos liderados** (team_lead solo ve equipos que lidera), **equipo predeterminado** (jefe/admin) y **formato por equipo en el chat**, en la VPS hay que **aplicar las adiciones a la base de datos** y luego reiniciar/reconstruir servicios:

1. **Aplicar en la base de datos la migración 0006** (nueva columna `default_team_id` en `hps_core_hpsuserprofile`). Sin este paso, el login y el perfil HPS fallan con error tipo «column default_team_id does not exist»:

   ```bash
   cd /opt/thot-security/cryptotrace
   docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
   # Verificar que hps_core 0006 esté aplicada:
   docker compose -f docker-compose.prod.yml exec backend python manage.py showmigrations hps_core
   ```

2. **Reiniciar (o reconstruir) el backend de CryptoTrace** para cargar el nuevo código del agente y las vistas:

   ```bash
   cd /opt/thot-security/cryptotrace
   docker compose -f docker-compose.prod.yml up -d --build backend
   # o solo reinicio si no cambiaste Dockerfile:
   docker compose -f docker-compose.prod.yml restart backend
   ```

3. **Reconstruir y levantar el frontend de HPS System** para que se apliquen los cambios de UI (selector de equipos en «Mi equipo», equipo predeterminado en edición de usuario, `led_teams` en el cliente):

   ```bash
   cd /opt/thot-security/hps-system
   docker compose -f docker-compose.prod.yml --env-file .env.prod build frontend
   docker compose -f docker-compose.prod.yml --env-file .env.prod up -d frontend
   ```

**No se requieren** nuevas variables de entorno ni cambios en Nginx.

---

### Actualización: RBAC (permisos por roles)

Si en el repositorio está la implementación de **RBAC** (modelo `HpsPermission`, permisos asignados a roles), en la VPS hay que aplicar las migraciones **0007** y **0008** de `hps_core` y reconstruir el backend. Guía detallada:

- **Documento completo:** [ACTUALIZACION-VPS-RBAC.md](ACTUALIZACION-VPS-RBAC.md)

**Pasos mínimos:**

1. **Migrar:**
   ```bash
   cd /opt/thot-security/cryptotrace
   docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
   ```

2. **Reconstruir backend (y celery si usan la misma imagen):**
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build backend
   ```

No se requieren nuevas variables de entorno.

---

## 2. Archivos estáticos (si cambió el frontend)

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

---

## 3. Reinicio de servicios (si aplica)

Si se han cambiado variables de entorno o configuración:

```bash
docker compose -f docker-compose.prod.yml restart
# o, si hace falta reconstruir:
docker compose -f docker-compose.prod.yml up -d --build
```

---

---

## 4. Actualización completa tras un pull (varios servicios tocados)

Cuando el merge incluye **backend, frontend CryptoTrace, processing, OCR, PDF, frontend HPS**, hay que reconstruir y levantar cada servicio cuyo código cambió.

**Recomendación:** no hagas `down` salvo que sea necesario; usa solo `up -d --build` para no quedarte en "Removing" de redes. Si en la VPS tienes **un solo compose** que incluye CryptoTrace + HPS, ejecuta todo desde el directorio de ese compose (por ejemplo `/opt/thot-security` si el compose está ahí). Si tienes **dos composes** (cryptotrace y hps-system por separado), sigue los bloques siguientes.

### CryptoTrace (directorio `/opt/thot-security/cryptotrace`)

```bash
cd /opt/thot-security/cryptotrace

# 1. Backend Django (agente HPS, API, hps_core, productos...) + Celery (misma imagen)
docker compose -f docker-compose.prod.yml up -d --build backend
docker compose -f docker-compose.prod.yml up -d --build celery-worker celery-beat

# 2. Frontend CryptoTrace (Next.js)
docker compose -f docker-compose.prod.yml up -d --build frontend

# 3. Processing (FastAPI)
docker compose -f docker-compose.prod.yml up -d --build processing

# 4. OCR (si hubo cambios en cryptotrace-ocr)
docker compose -f docker-compose.prod.yml up -d --build ocr

# 5. PDF generator (si hubo cambios en cryptotrace-pdf-generator)
docker compose -f docker-compose.prod.yml up -d --build pdf-generator
```

**O en un solo comando** (reconstruye y levanta todo lo que tenga `build:`):

```bash
cd /opt/thot-security/cryptotrace
docker compose -f docker-compose.prod.yml up -d --build
```

### Frontend HPS System (directorio `/opt/thot-security/hps-system`)

```bash
cd /opt/thot-security/hps-system
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build frontend
```

### Collectstatic (si cambió el frontend CryptoTrace):

```bash
cd /opt/thot-security/cryptotrace
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

---

## Resumen rápido

1. **`migrate`** → obligatorio tras cambios en modelos o al subir migraciones nuevas (incl. HPS múltiples equipos y migración 0006 `default_team`).
2. **`collectstatic`** → si hubo cambios en estáticos (frontend CryptoTrace).
3. **Reinicio/rebuild** → según cambios en env o en imágenes.
4. **Actualización HPS (equipos liderados / equipo predeterminado):** además de `migrate`, reiniciar o reconstruir **backend CryptoTrace** y **reconstruir y levantar frontend HPS** (ver sección «Actualización: Equipos liderados y equipo predeterminado»).
5. **Pull con muchos cambios:** usar sección «Actualización completa tras un pull» para reconstruir backend, frontend, processing, ocr, pdf-generator (CryptoTrace) y frontend HPS.

**Última actualización:** 2025-02-19
