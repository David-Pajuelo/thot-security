# Actualización VPS: RBAC (permisos por roles)

Este documento describe los pasos necesarios en producción (VPS) para desplegar la implementación de **RBAC** (control de acceso basado en permisos asignados a roles): modelo `HpsPermission`, relación rol–permisos y migración de la lógica de autorización.

---

## 1. Qué incluye esta actualización

- **Nuevas migraciones en `hps_core`:**
  - **0007_add_hps_permission_and_role_m2m:** Crea la tabla `HpsPermission` y el campo M2M `granted_permissions` en `HpsRole`.
  - **0008_populate_rbac_permissions:** Inserta los permisos (codename, name, category) y los asigna a cada rol según la matriz definida en la auditoría.

- **Cambios en el backend:** Toda la autorización de vistas HPS y de productos (línea temporal, chat) pasa a basarse en estos permisos en lugar de comprobaciones por nombre de rol en código. No se requieren nuevas variables de entorno.

- **Frontends:** Sin cambios de rutas ni de lógica de login; el JWT sigue incluyendo `role`. No es obligatorio reconstruir los frontends solo por RBAC, pero si en la misma actualización hay otros cambios en frontend, sí hay que reconstruirlos.

---

## 2. Pasos en la VPS

### 2.1 Actualizar código

Desde el directorio del repositorio en la VPS (por ejemplo `/opt/thot-security`):

```bash
cd /opt/thot-security
git pull origin development
# o, si despliegas desde rama production:
# git pull origin production
```

### 2.2 Aplicar migraciones (obligatorio)

Las migraciones **0007** y **0008** deben ejecutarse para que existan la tabla de permisos y las asignaciones rol–permiso. Sin ellas, el backend puede fallar al comprobar permisos.

**CryptoTrace (compose de producción):**

```bash
cd /opt/thot-security/cryptotrace
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

Comprobar que las migraciones de `hps_core` están aplicadas (deben aparecer con `[X]` las 0007 y 0008):

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py showmigrations hps_core
```

Salida esperada (entre otras):

```
hps_core
 ...
 [X] 0007_add_hps_permission_and_role_m2m
 [X] 0008_populate_rbac_permissions
```

### 2.3 Reiniciar o reconstruir el backend

Para que el backend cargue el código nuevo (permisos RBAC, vistas y serializers actualizados):

```bash
cd /opt/thot-security/cryptotrace
docker compose -f docker-compose.prod.yml up -d --build backend
```

Si Celery worker y beat usan la misma imagen que el backend, reconstruir también:

```bash
docker compose -f docker-compose.prod.yml up -d --build celery-worker celery-beat
```

O en un solo paso:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### 2.4 (Opcional) Archivos estáticos

Solo si en esta misma actualización hubo cambios en el frontend de CryptoTrace:

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

---

## 3. Verificación rápida

1. **Login:** Iniciar sesión con un usuario con perfil HPS (cualquier rol). Debe poder entrar y ver el menú según su rol.
2. **Roles:** Un usuario **admin** debe poder acceder a la gestión de roles (y ver en el admin de Django los permisos concedidos por rol).
3. **CryptoTrace (crypto):** Un usuario **member** no debe poder acceder al área crypto; **admin** o **crypto** sí.
4. **Chat:** Solo usuarios con permiso correspondiente (p. ej. admin) deben ver el listado global de conversaciones.

Si algo falla, revisar logs del backend:

```bash
docker compose -f docker-compose.prod.yml logs -f backend
```

---

## 4. Rollback (solo si es necesario)

Si hubiera que volver atrás (código anterior a RBAC):

1. Revertir el código al commit anterior a la implementación RBAC.
2. Desaplicar migraciones hasta 0006:
   ```bash
   docker compose -f docker-compose.prod.yml exec backend python manage.py migrate hps_core 0006_hpsuserprofile_default_team
   ```
3. Reiniciar/reconstruir el backend.

**Nota:** La migración 0008 solo inserta datos (permisos y asignaciones). El reverse de 0008 los deja en la BD; 0007 crea tablas/campo que quedarían sin usar con código antiguo. No es necesario borrar manualmente los datos para un rollback de código.

---

## 5. Resumen

| Paso | Comando / acción |
|------|-------------------|
| 1 | `git pull` en la VPS |
| 2 | `docker compose -f docker-compose.prod.yml exec backend python manage.py migrate` |
| 3 | `docker compose -f docker-compose.prod.yml up -d --build backend` (y celery si aplica) |
| 4 | (Opcional) `collectstatic` si hubo cambios en frontend |

No se requieren nuevas variables de entorno ni cambios en Nginx para esta actualización.

**Última actualización:** 2025-02-19
