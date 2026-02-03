# Plan de backup y vuelta al commit actual

Este documento describe cómo hacer backup y cómo volver al estado del repositorio y de la base de datos correspondiente a este commit, por si los cambios futuros (p. ej. cryptocustodios y sus migraciones) deben revertirse.

---

## Commit de referencia (punto de retorno)

- **Rama:** `development`
- **Commit:** `f37907b`
- **Mensaje:** `AC21/OCR: mejoras OCR, CC nullable, recarga tras guardar, detección AC21`

Para comprobar que estás en ese commit:

```bash
git rev-parse HEAD
# Debe mostrar: f37907b (o el hash completo que corresponda)

git log -1 --oneline
# Debe mostrar: f37907b AC21/OCR: mejoras OCR, CC nullable, ...
```

---

## 1. Backup antes de empezar cambios nuevos

### 1.1 Base de datos

Hacer un volcado de la base de datos **antes** de aplicar cualquier migración nueva (p. ej. cryptocustodios):

```bash
# Con Docker (ajustar nombre del servicio y de la DB si aplica)
docker-compose exec db pg_dump -U postgres cryptotrace_db > backup_pre_cryptocustodios_$(date +%Y%m%d_%H%M%S).sql

# Sin Docker (PostgreSQL local)
pg_dump -U postgres cryptotrace_db > backup_pre_cryptocustodios_$(date +%Y%m%d_%H%M%S).sql
```

Guarda el archivo en un lugar seguro (fuera del repo si es sensible).

### 1.2 Código (Git)

El código de este punto está fijado en el commit indicado. Para guardar una “etiqueta” por si luego quieres volver:

```bash
git tag -a punto-antes-cryptocustodios -m "Estado antes de implementar cryptocustodios (f37907b)"
git push origin punto-antes-cryptocustodios
```

(Opcional; si no usas tags, basta con recordar el hash `f37907b`.)

---

## 2. Cómo volver al commit actual (revertir código)

Si ya has hecho commits nuevos y quieres **dejar el código** como en este punto:

```bash
# Ver el historial
git log --oneline

# Opción A: Volver el branch a este commit (descartando commits posteriores)
# ¡Cuidado! Esto reescribe la historia si ya has hecho push.
git reset --hard f37907b

# Si ya habías pusheado la rama y quieres actualizar el remoto (solo si tienes claro que quieres reescribir development)
# git push origin development --force
```

Si prefieres **no reescribir historia** y solo dejar el working tree como en ese commit:

```bash
git checkout f37907b -- .
# Esto deja los archivos del working tree como en f37907b; luego puedes hacer un nuevo commit "Revert to f37907b".
```

---

## 3. Migraciones: estado actual y futuras

### 3.1 Última migración aplicada en este commit

En este punto, la última migración de la app `productos` es:

- **0035_allow_null_cc_in_movimiento**

Comprobar en tu entorno:

```bash
docker-compose exec backend python manage.py showmigrations productos
```

Debe estar marcada como aplicada hasta `0035_allow_null_cc_in_movimiento`.

### 3.2 Migraciones que se añadirán con cryptocustodios

Cuando se implemente la tabla `cryptocustodios`, se generarán una o más migraciones nuevas (por ejemplo `0036_...`, `0037_...`). En este documento se irán anotando para poder revertirlas si hace falta.

**Anotación:**

| Migración | Descripción breve | Revertir a |
|-----------|-------------------|------------|
| **0036_add_cryptocustodio** | Creación tabla Cryptocustodio (1-N con Empresa) | 0035_allow_null_cc_in_movimiento |

---

## 4. Cómo revertir migraciones (volver al estado de BD de este commit)

Si en el futuro aplicas migraciones nuevas (p. ej. cryptocustodios) y quieres **volver la base de datos** al estado que tenía con el commit actual, hay que **revertir migraciones** hasta la que corresponde a este commit.

### 4.1 Revertir hasta la migración 0035

Con el backend en Docker:

```bash
docker-compose exec backend python manage.py migrate productos 0035_allow_null_cc_in_movimiento
```

Eso desaplica las migraciones posteriores a 0035 (por ejemplo 0036, 0037). La base de datos quedará consistente con el código del commit `f37907b`.

### 4.2 Restaurar desde un backup (alternativa)

Si prefieres restaurar el volcado que hiciste antes de cryptocustodios:

```bash
# Con Docker
docker-compose exec -T db psql -U postgres cryptotrace_db < backup_pre_cryptocustodios_YYYYMMDD_HHMMSS.sql

# Sin Docker
psql -U postgres cryptotrace_db < backup_pre_cryptocustodios_YYYYMMDD_HHMMSS.sql
```

Después de restaurar, conviene comprobar que las migraciones que Django cree que están aplicadas coinciden con la BD (no haya migraciones “fantasma”). En caso de duda, usar `showmigrations` y, si hace falta, marcar migraciones como aplicadas o no con `migrate --fake` (con cuidado).

---

## 5. Resumen rápido

| Objetivo                         | Acción |
|----------------------------------|--------|
| Backup de BD antes de cambios   | `pg_dump ... > backup_pre_cryptocustodios_*.sql` |
| Marcar punto de retorno en código | `git tag punto-antes-cryptocustodios` (opcional) |
| Volver código a este commit     | `git reset --hard f37907b` (o `git checkout f37907b -- .`) |
| Última migración en este commit | `0035_allow_null_cc_in_movimiento` |
| Revertir migraciones futuras    | `python manage.py migrate productos 0035_allow_null_cc_in_movimiento` |
| Restaurar BD desde backup       | `psql ... < backup_pre_cryptocustodios_*.sql` |

---

## 6. Actualización de este documento

- Al crear **nuevas migraciones** (p. ej. cryptocustodios), añadir su nombre y descripción en la sección **3.2** y en la tabla de “Revertir a”.
- Si cambia el **commit de referencia** (por ejemplo un nuevo tag), actualizar la sección **Commit de referencia** y los comandos que usen el hash.
