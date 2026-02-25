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

**Última actualización:** 2025-02-19
