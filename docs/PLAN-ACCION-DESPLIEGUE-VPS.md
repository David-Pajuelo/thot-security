# Plan de acción: implementación de cambios en el VPS

Checklist para desplegar en el VPS todos los cambios recientes: migraciones (CC, tipo_producto, cryptocustodios), código backend/frontend/OCR.

**Última actualización:** 2026-02-02

---

## 1. Migraciones a aplicar (orden obligatorio)

Aplicar en el backend CryptoTrace, dentro del contenedor, en este orden:

| Orden | Migración | Descripción breve |
|-------|-----------|-------------------|
| 1 | `0033_remove_catalogoproducto_tipo_cryptocustodio` | Elimina campo obsoleto `tipo_cryptocustodio` de catálogo |
| 2 | `0034_replace_cc_with_tipo_producto` | Sustituye `cc` por `tipo_producto` (FK) en LineaTemporalProducto; CC del OCR en datos_adicionales |
| 3 | `0035_allow_null_cc_in_movimiento` | Permite CC NULL en MovimientoProducto (informativo del AC21) |
| 4 | `0036_add_cryptocustodio` | Crea tabla Cryptocustodio (1-N con Empresa) para selector de firmas AC21 |

**Dependencias:** 0034 → 0033; 0035 → 0034; 0036 → 0035.

---

## 2. Pasos en el VPS (CryptoTrace)

### 2.1 Conectar y ubicar proyecto

```bash
ssh root@187.33.154.156
# (o la IP/host configurado para el VPS)

cd /opt/thot-security/cryptotrace
# (o la ruta donde esté clonado el repo en el VPS)
```

### 2.2 Actualizar código desde la rama development

```bash
git fetch origin
git checkout development
git pull origin development
```

### 2.3 Backup de la base de datos (obligatorio antes de migrar)

```bash
docker-compose exec -T db pg_dump -U postgres cryptotrace > backup_pre_despliegue_$(date +%Y%m%d_%H%M%S).sql
```

Guardar el archivo en un lugar seguro (ej. copiarlo fuera del servidor).

### 2.4 Ver estado actual de migraciones

```bash
docker-compose exec backend python manage.py showmigrations productos
```

Anotar hasta qué migración está aplicada (ej. 0032 o 0035). Si ya está 0035, solo faltará aplicar 0036.

### 2.5 Aplicar migraciones

```bash
docker-compose exec backend python manage.py migrate productos
```

Esto aplicará todas las pendientes (0033, 0034, 0035, 0036) en orden.

### 2.6 Recolectar estáticos (Django, si aplica)

```bash
docker-compose exec backend python manage.py collectstatic --noinput
```

### 2.7 Reconstruir y reiniciar contenedores

Para que el nuevo código (backend, frontend, OCR) se use:

```bash
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

O si en el VPS usan otro compose:

```bash
docker-compose build backend frontend ocr
docker-compose up -d
```

### 2.8 Verificación rápida

- Backend: `curl -I https://seguridad.idiaicox.com/cryptotrace/api/` (o la URL del API).
- Frontend: abrir en navegador y probar login y flujo AC21.
- OCR: subir un AC21 y comprobar que extrae cabecera, artículos, CC y equipos de prueba.
- Cryptocustodios: en Empresas, botón "Ver cryptocustodios"; en subida AC21, selector de cryptocustodio para Firma A/B.

---

## 3. Resumen de cambios por componente

| Componente | Cambios relevantes |
|------------|---------------------|
| **Backend** | Modelo Cryptocustodio, API /cryptocustodios/, CC nullable, tipo_producto en línea temporal, serializers/views actualizados. |
| **Frontend** | Selector cryptocustodio en upload-ac21 y AC21Detail, modal cryptocustodios en Empresas, resolución 2200px para PDF. |
| **OCR** | Prompt CC (obligatorio por fila), equipos de prueba (línea única + tabla), sanitización CC acepta alfanumérico. |

No hay migraciones en frontend ni OCR; solo en backend (productos).

---

## 4. Rollback de migraciones (solo si algo falla)

Si tras aplicar 0036 hay que volver atrás:

```bash
docker-compose exec backend python manage.py migrate productos 0035_allow_null_cc_in_movimiento
```

Para volver al estado anterior a todas estas migraciones:

```bash
docker-compose exec backend python manage.py migrate productos 0032_add_imagen_documento_field
```

Luego restaurar el backup de la base de datos si se ha hecho alguna migración destructiva y se necesita recuperar datos.

---

## 5. Referencias

- Migraciones detalladas: `docs/MIGRACIONES-PENDIENTES-PRODUCCION.md`
- Backup y rollback: `docs/PLAN-BACKUP-ROLLBACK-COMMIT-ACTUAL.md`
- Revertir cryptocustodios: `docs/REVERT-CRYPTOCUSTODIOS.md`
- Despliegue completo VPS: `docs/produccion/GUIA-DESPLIEGUE-PRODUCCION-VPS.md`
