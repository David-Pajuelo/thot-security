# Checklist al actualizar el VPS

Usar este checklist cada vez que se actualice el código en el VPS (pull, despliegue nuevo, etc.) para no olvidar pasos críticos.

---

## 1. Migraciones de base de datos (CryptoTrace backend)

**Importante:** Tras actualizar el código, siempre ejecutar las migraciones para aplicar cambios en modelos (Django).

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

## Resumen rápido

1. **`migrate`** → obligatorio tras cambios en modelos o al subir migraciones nuevas (incl. HPS múltiples equipos).
2. **`collectstatic`** → si hubo cambios en estáticos.
3. **Reinicio/rebuild** → según cambios en env o en imágenes.

**Última actualización:** 2025-02-25
