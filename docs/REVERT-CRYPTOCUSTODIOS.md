# Cómo revertir la implementación de Cryptocustodios

**Importante:** Revertir solo con `git pull` o `git reset` **no basta**. La base de datos tendrá la tabla `productos_cryptocustodio` y Django tendrá la migración aplicada. Hay que **revertir primero la migración** y luego el código (o en el orden indicado abajo).

---

## 1. Resumen del orden de reversión

1. **Opcional:** Hacer backup de la BD si quieres conservar datos de cryptocustodios.
2. **Revertir la migración** de Cryptocustodio en la base de datos (Django desaplica la migración).
3. **Revertir el código** (git) para quitar modelo, API, frontend y admin.

Si solo reviertes código y no la migración, Django seguirá esperando la tabla `productos_cryptocustodio` y el backend fallará al arrancar o al ejecutar migraciones.

---

## 2. Antes de revertir: backup (opcional)

Si quieres conservar los datos de cryptocustodios por si acaso:

```bash
# Con Docker
docker-compose exec db pg_dump -U postgres cryptotrace_db > backup_cryptocustodios_$(date +%Y%m%d_%H%M%S).sql

# Sin Docker
pg_dump -U postgres cryptotrace_db > backup_cryptocustodios_$(date +%Y%m%d_%H%M%S).sql
```

Guarda el archivo fuera del repo.

---

## 3. Revertir la migración (base de datos)

Hay que **desaplicar** la migración que creó la tabla Cryptocustodio, dejando la BD en el estado anterior (por ejemplo en `0035_allow_null_cc_in_movimiento`).

### 3.1 Ver qué migración creó Cryptocustodio

En el proyecto, la migración de cryptocustodios es:

- **`0036_add_cryptocustodio.py`**

Comprueba el estado actual:

```bash
# Con Docker
docker-compose exec backend python manage.py showmigrations productos

# Sin Docker (desde el directorio del backend)
python manage.py showmigrations productos
```

Verás una línea `[X]` para la migración de cryptocustodios (p. ej. `0036_add_cryptocustodio`).

### 3.2 Desaplicar hasta la migración anterior

Vuelve a la **última migración antes** de cryptocustodios (por ejemplo `0035_allow_null_cc_in_movimiento`):

```bash
# Con Docker
docker-compose exec backend python manage.py migrate productos 0035_allow_null_cc_in_movimiento

# Sin Docker
python manage.py migrate productos 0035_allow_null_cc_in_movimiento
```

Eso **elimina la tabla** `productos_cryptocustodio` (y sus datos). Django marca la migración de cryptocustodios como no aplicada.

### 3.3 Comprobar

```bash
docker-compose exec backend python manage.py showmigrations productos
```

La migración de cryptocustodios debe aparecer sin `[X]`. La última aplicada debe ser `0035_allow_null_cc_in_movimiento` (o la que corresponda).

---

## 4. Revertir el código (Git)

Después de revertir la migración, hay que quitar todo el código añadido para cryptocustodios.

### 4.1 Opción A: Volver al commit anterior (descartar commits de cryptocustodios)

Si todos los cambios de cryptocustodios están en uno o más commits que quieres quitar:

```bash
# Ver el historial para localizar el commit anterior a cryptocustodios
git log --oneline

# Volver el branch a ese commit (sustituir <commit-anterior> por el hash, p. ej. f37907b)
git reset --hard <commit-anterior>

# Si ya habías pusheado y quieres actualizar el remoto (reescribe historia)
# git push origin development --force
```

Con esto se eliminan también los **archivos de migración** nuevos (p. ej. `0036_add_cryptocustodio.py`). Si en otro entorno solo haces `git pull`, no tendrás esos archivos y Django no intentará aplicar esa migración; en ese entorno solo hace falta **revertir la migración en la BD** (paso 3) si ya se había aplicado.

### 4.2 Opción B: Mantener historia y revertir con un commit de reversión

Si prefieres no reescribir historia:

```bash
# Crear un commit que deshace los cambios de cryptocustodios
git revert --no-commit <último-commit-cryptocustodios>   # o varios commits
git commit -m "Revert: implementación Cryptocustodios"
git push origin development
```

**Cuidado:** Con `git revert` se revierten los commits; si entre medias hay otros cambios, puede haber conflictos. Además, los **archivos de migración** seguirán en el repo; Django los verá pero la migración ya estará desaplicada en la BD (por el paso 3). En ese caso, si quieres que en el repo tampoco exista la migración, tendrías que borrar a mano el archivo `0036_add_cryptocustodio.py` (o el que sea) y hacer un commit que lo elimine.

### 4.3 Archivos que debe quitar / revertir la reversión

Para comprobar que no queda nada de cryptocustodios:

- **Backend:**  
  - `productos/models.py`: quitar la clase `Cryptocustodio`.  
  - `productos/serializers.py`: quitar `CryptocustodioSerializer` y su uso si se usa en otro serializer.  
  - `productos/views.py`: quitar `CryptocustodioViewSet` y la acción que lo use.  
  - `productos/urls.py`: quitar el registro `router.register(r'cryptocustodios', ...)`.  
  - `productos/admin.py`: quitar el registro de `Cryptocustodio` (y el inline en Empresa si se añadió).  
  - `productos/migrations/0036_add_cryptocustodio.py`: eliminarlo (o revertir su creación según opción 4.1/4.2).

- **Frontend:**  
  - `lib/types.ts`: quitar tipo `Cryptocustodio`.  
  - `lib/api.ts`: quitar `fetchCryptocustodios`, `createCryptocustodio`, `updateCryptocustodio`, `deleteCryptocustodio`.  
  - Componentes de empresas: quitar botón “Ver cryptocustodios”, modal de cryptocustodios y formulario.  
  - `upload-ac21/page.tsx` y `AC21Detail.tsx`: quitar desplegables de cryptocustodios para firma A/B y lógica asociada.

---

## 5. Reiniciar servicios (recomendado)

Después de revertir migración y código:

```bash
docker-compose restart backend
docker-compose restart frontend
```

(O reiniciar solo backend si no tocaste frontend en la reversión.)

---

## 6. Si algo sale mal

- **Error “relation productos_cryptocustodio does not exist”**  
  La migración ya se revirtió pero el código aún tiene el modelo. Solución: completar la reversión del código (paso 4).

- **Error “No such table” o migraciones inconsistentes**  
  En la BD la migración de cryptocustodios sigue aplicada pero el archivo de migración se borró (o no existe en ese clone). Opciones:  
  - Restaurar el archivo de migración desde git y luego revertir con `migrate productos 0035_...`,  
  - o marcar esa migración como no aplicada a mano en la tabla `django_migrations` (avanzado).

- **Quieres volver a aplicar cryptocustodios después**  
  Restaurar el código desde git (commit de cryptocustodios) y ejecutar de nuevo:  
  `python manage.py migrate productos`  
  para aplicar de nuevo la migración de cryptocustodios.

---

## 7. Checklist de reversión

- [ ] Backup de BD (opcional).
- [ ] Revertir migración: `migrate productos 0035_allow_null_cc_in_movimiento` (o la anterior a cryptocustodios).
- [ ] Comprobar: `showmigrations productos`.
- [ ] Revertir código (git reset/revert o borrar/editar archivos a mano).
- [ ] Eliminar archivo de migración `0036_*` si sigue en repo y no quieres que exista.
- [ ] Reiniciar backend (y frontend si aplica).
