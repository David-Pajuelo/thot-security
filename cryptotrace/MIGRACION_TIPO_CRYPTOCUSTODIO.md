# Migración: Tipo de Cryptocustodio en Líneas Temporales

**Fecha de Creación**: 2025-01-XX  
**Versión**: 1.0  
**Estado**: Pendiente de Aplicación

## 🎯 Resumen Ejecutivo

Esta migración separa el campo `cc` del AC21 (columna del PDF) del tipo de cryptocustodio seleccionado por el usuario. Añade asignación automática del tipo desde el catálogo de productos.

**Impacto**: Bajo - Solo añade campos nuevos, no modifica datos existentes  
**Tiempo Estimado**: 15-30 minutos en producción  
**Reversibilidad**: Sí - Migraciones reversibles con backup

## 📋 Resumen de Cambios

Esta migración implementa la separación entre:
- **`cc`**: Campo del AC21 (columna del PDF) que viene del OCR (1, 2, 3 o vacío). **NO se modifica**.
- **`tipo_cryptocustodio`**: Tipo seleccionado por el usuario ('c', 'CC', 'Ninguno'). Se almacena en el catálogo para asignación automática.

### Cambios Principales

1. **Modelo `LineaTemporalProducto`**:
   - Añadido campo `tipo_cryptocustodio` (CharField con choices: 'c', 'CC', 'Ninguno')
   - Campo `cc` ahora tiene help_text aclarando que viene del OCR y no debe modificarse

2. **Modelo `CatalogoProducto`**:
   - Añadido campo `tipo_cryptocustodio` para almacenar el tipo por defecto de cada producto
   - Permite asignación automática cuando se procesan líneas temporales

3. **Backend - Lógica de Asignación Automática**:
   - Al crear líneas temporales: busca `tipo_cryptocustodio` en `CatalogoProducto` y lo asigna automáticamente
   - Al cargar líneas temporales (`agrupados`): busca en catálogo y actualiza líneas si existe
   - Al actualizar tipo: también actualiza el catálogo para futuras referencias

4. **Frontend**:
   - Eliminadas columnas de "Descripción" y "Números de Serie" de la tabla
   - Tabla muestra solo: Código, Cantidad, Tipo Cryptocustodio
   - Dropdown con valores: 'c', 'CC', 'Ninguno' (texto directo, sin mapeo numérico)

## 📁 Archivos Modificados

### Backend
- `cryptotrace-backend/src/productos/models.py`
- `cryptotrace-backend/src/productos/views.py`
- `cryptotrace-backend/src/productos/migrations/0033_add_tipo_cryptocustodio.py` (nuevo)
- `cryptotrace-backend/src/productos/migrations/0034_add_tipo_cryptocustodio_to_catalogo.py` (nuevo)

### Frontend
- `cryptotrace-frontend/src/components/albaranes/LineaTemporalTable.tsx`
- `cryptotrace-frontend/src/components/albaranes/GestionLineaTemporal.tsx`
- `cryptotrace-frontend/src/lib/api.ts`

## 🔄 Migraciones Necesarias

### Migración 1: `0033_add_tipo_cryptocustodio`
- Añade campo `tipo_cryptocustodio` a `LineaTemporalProducto`
- Actualiza help_text del campo `cc`

### Migración 2: `0034_add_tipo_cryptocustodio_to_catalogo`
- Añade campo `tipo_cryptocustodio` a `CatalogoProducto`

## 🚀 Pasos para Desarrollo Local

### 1. Verificar Estado Actual
```bash
cd cryptotrace/cryptotrace-backend/src
python manage.py showmigrations productos
```

### 2. Aplicar Migraciones
```bash
cd cryptotrace/cryptotrace-backend/src
python manage.py migrate productos
```

### 3. Verificar Migraciones Aplicadas
```bash
python manage.py showmigrations productos
# Debe mostrar [X] 0033_add_tipo_cryptocustodio
# Debe mostrar [X] 0034_add_tipo_cryptocustodio_to_catalogo
```

### 4. Reiniciar Contenedores
```bash
cd cryptotrace
docker compose restart backend frontend
```

### 5. Verificar Funcionamiento
1. Acceder a la gestión de líneas temporales
2. Verificar que la tabla muestra solo: Código, Cantidad, Tipo Cryptocustodio
3. Verificar que el dropdown tiene opciones: 'c', 'CC', 'Ninguno'
4. Probar asignación automática:
   - Crear/actualizar un producto en catálogo con `tipo_cryptocustodio='CC'`
   - Procesar AC21 con ese código de producto
   - Verificar que la línea temporal se crea automáticamente con `tipo_cryptocustodio='CC'`
   - Abrir gestión de líneas temporales y verificar que el dropdown muestra 'CC'

## 🏭 Pasos para Producción (VPS)

### 1. Conectar al VPS
```bash
ssh root@seguridad.idiaicox.com
# O usar tu método de conexión habitual
```

### 2. Navegar al Directorio del Proyecto
```bash
cd /opt/thot-security/cryptotrace
```

### 3. Hacer Backup de la Base de Datos (IMPORTANTE - OBLIGATORIO)
```bash
# Backup completo de PostgreSQL
BACKUP_FILE="/tmp/backup_pre_tipo_cryptocustodio_$(date +%Y%m%d_%H%M%S).sql"
docker exec cryptotrace-db pg_dump -U postgres cryptotrace_db > "$BACKUP_FILE"

# Verificar que el backup se creó correctamente
ls -lh "$BACKUP_FILE"

# Verificar tamaño del backup (debe ser > 0)
if [ -s "$BACKUP_FILE" ]; then
    echo "✅ Backup creado correctamente: $BACKUP_FILE"
    echo "📦 Tamaño: $(du -h "$BACKUP_FILE" | cut -f1)"
else
    echo "❌ ERROR: El backup está vacío o no se creó"
    exit 1
fi

# Guardar la ruta del backup para referencia
echo "Backup guardado en: $BACKUP_FILE"
```

### 4. Actualizar Código en VPS
```bash
cd /opt/thot-security/cryptotrace

# Si usas git, hacer pull de los cambios
git pull origin development  # o la rama correspondiente

# Verificar que los archivos de migración existen
ls -la cryptotrace-backend/src/productos/migrations/0033_add_tipo_cryptocustodio.py
ls -la cryptotrace-backend/src/productos/migrations/0034_add_tipo_cryptocustodio_to_catalogo.py

# Verificar que los modelos tienen los cambios
grep -A 5 "tipo_cryptocustodio" cryptotrace-backend/src/productos/models.py
```

### 5. Detener Contenedores (Opcional, pero recomendado)
```bash
cd /opt/thot-security/cryptotrace
docker compose -f docker-compose.prod.yml stop backend
```

### 6. Aplicar Migraciones
```bash
cd /opt/thot-security/cryptotrace
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate productos
```

**Alternativa si el contenedor está detenido:**
```bash
# Iniciar temporalmente solo el backend y la BD
docker compose -f docker-compose.prod.yml up -d db
docker compose -f docker-compose.prod.yml run --rm backend python manage.py migrate productos
```

### 7. Verificar Migraciones Aplicadas
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py showmigrations productos
# Debe mostrar [X] 0033_add_tipo_cryptocustodio
# Debe mostrar [X] 0034_add_tipo_cryptocustodio_to_catalogo
```

### 8. Reconstruir y Reiniciar Contenedores
```bash
cd /opt/thot-security/cryptotrace

# Reconstruir backend y frontend con los nuevos cambios
docker compose -f docker-compose.prod.yml build --no-cache backend frontend

# Reiniciar servicios
docker compose -f docker-compose.prod.yml up -d backend frontend

# Verificar que los contenedores están corriendo
docker compose -f docker-compose.prod.yml ps
```

### 9. Verificar Logs
```bash
# Verificar logs del backend
docker compose -f docker-compose.prod.yml logs backend --tail=50

# Verificar logs del frontend
docker compose -f docker-compose.prod.yml logs frontend --tail=50

# Verificar que no hay errores de migración
docker compose -f docker-compose.prod.yml logs backend | grep -i "migrate\|error\|exception"
```

### 10. Verificar Funcionamiento en Producción
1. Acceder a la aplicación en producción
2. Ir a la gestión de líneas temporales
3. Verificar que:
   - La tabla muestra solo: Código, Cantidad, Tipo Cryptocustodio
   - El dropdown tiene opciones: 'c', 'CC', 'Ninguno'
   - No hay errores en la consola del navegador
   - Los tipos se guardan correctamente

## ✅ Verificaciones Post-Migración

### Verificar en Base de Datos
```bash
# Conectar a la base de datos
docker compose -f docker-compose.prod.yml exec db psql -U postgres -d cryptotrace_db

# Verificar que el campo existe en LineaTemporalProducto
\d productos_lineatemporalproducto
# Debe mostrar: tipo_cryptocustodio | character varying(10)

# Verificar que el campo existe en CatalogoProducto
\d productos_catalogoproducto
# Debe mostrar: tipo_cryptocustodio | character varying(10)

# Verificar valores por defecto
SELECT codigo_producto, tipo_cryptocustodio FROM productos_lineatemporalproducto LIMIT 5;
SELECT codigo_producto, tipo_cryptocustodio FROM productos_catalogoproducto LIMIT 5;

# Salir de psql
\q
```

### Verificar en Django Admin (si está disponible)
1. Acceder a Django Admin
2. Ir a `Productos > Linea temporal productos`
3. Verificar que existe la columna `tipo_cryptocustodio`
4. Verificar que los valores son 'c', 'CC' o 'Ninguno'

### Verificar API Endpoints
```bash
# Probar endpoint de productos agrupados (requiere autenticación)
curl -X GET "https://seguridad.idiaicox.com/api/lineas-temporales/agrupados/" \
  -H "Authorization: Bearer <token>"

# Verificar que la respuesta incluye 'tipo_cryptocustodio'
```

## 🔙 Rollback (Si es Necesario)

### Si algo sale mal, revertir migraciones:

```bash
# En producción
cd /opt/thot-security/cryptotrace

# 1. Revertir migraciones (en orden inverso)
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate productos 0034_add_tipo_cryptocustodio_to_catalogo
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate productos 0033_add_tipo_cryptocustodio
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate productos 0032_add_imagen_documento_field

# 2. Restaurar backup de base de datos (si es necesario)
docker exec -i cryptotrace-db psql -U postgres cryptotrace_db < /tmp/backup_pre_tipo_cryptocustodio_YYYYMMDD_HHMMSS.sql

# 3. Revertir código a commit anterior
git checkout <commit_anterior>
docker compose -f docker-compose.prod.yml build --no-cache backend frontend
docker compose -f docker-compose.prod.yml up -d backend frontend
```

## ✅ Checklist Pre-Migración Producción

Antes de aplicar en producción, verificar:

- [ ] Backup de base de datos realizado y verificado
- [ ] Código actualizado en el repositorio (commit y push realizado)
- [ ] Migraciones creadas y verificadas localmente
- [ ] Pruebas realizadas en desarrollo local
- [ ] Documentación revisada
- [ ] Ventana de mantenimiento coordinada (si es necesario)
- [ ] Acceso al VPS verificado

## ✅ Checklist Post-Migración Producción

Después de aplicar en producción, verificar:

- [ ] Migraciones aplicadas correctamente (sin errores)
- [ ] Contenedores backend y frontend reiniciados
- [ ] Logs sin errores críticos
- [ ] Tabla de líneas temporales muestra solo: Código, Cantidad, Tipo Cryptocustodio
- [ ] Dropdown funciona correctamente ('c', 'CC', 'Ninguno')
- [ ] Asignación automática funciona (producto en catálogo con tipo se asigna automáticamente)
- [ ] Actualización de tipo funciona (cambiar tipo actualiza líneas temporales y catálogo)
- [ ] No hay errores en consola del navegador
- [ ] API responde correctamente

## 📝 Notas Importantes

1. **Datos Existentes**: 
   - Las líneas temporales existentes tendrán `tipo_cryptocustodio='Ninguno'` por defecto
   - Los productos del catálogo existentes tendrán `tipo_cryptocustodio='Ninguno'` por defecto
   - Los usuarios deberán asignar manualmente los tipos a productos existentes si es necesario

2. **Compatibilidad**:
   - El campo `cc` del AC21 se mantiene intacto y sigue funcionando igual
   - No se pierde información existente

3. **Asignación Automática**:
   - Solo funciona si el producto ya existe en `CatalogoProducto` con un `tipo_cryptocustodio` asignado
   - Si el tipo en el catálogo es 'Ninguno', se usa 'Ninguno' en las líneas temporales
   - Cuando el usuario cambia el tipo en el dropdown, se actualiza tanto las líneas temporales como el catálogo

4. **Frontend**:
   - La tabla ya no muestra descripción ni números de serie
   - Solo muestra: Código, Cantidad, Tipo Cryptocustodio

## 🐛 Troubleshooting

### Error: "column does not exist"
- **Causa**: Migración no aplicada
- **Solución**: Aplicar migraciones manualmente

### Error: "default value does not match"
- **Causa**: Conflicto con datos existentes
- **Solución**: Verificar que la migración se aplicó correctamente, puede requerir ajuste manual de datos

### Frontend no muestra cambios
- **Causa**: Contenedor frontend no reconstruido
- **Solución**: Reconstruir frontend con `--no-cache`

### Tipos no se asignan automáticamente
- **Causa**: Producto no existe en catálogo o tiene 'Ninguno'
- **Solución**: Verificar que el producto existe en `CatalogoProducto` y tiene un `tipo_cryptocustodio` asignado

## 🔍 Scripts de Verificación

### Script para Verificar Migraciones Aplicadas
```bash
#!/bin/bash
# Verificar que las migraciones están aplicadas

cd /opt/thot-security/cryptotrace
docker compose -f docker-compose.prod.yml exec backend python manage.py showmigrations productos | grep -E "0033|0034"

# Debe mostrar:
# [X] 0033_add_tipo_cryptocustodio
# [X] 0034_add_tipo_cryptocustodio_to_catalogo
```

### Script para Verificar Campos en Base de Datos
```bash
#!/bin/bash
# Verificar que los campos existen en la BD

docker compose -f docker-compose.prod.yml exec db psql -U postgres -d cryptotrace_db -c "
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'productos_lineatemporalproducto' 
AND column_name = 'tipo_cryptocustodio';

SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'productos_catalogoproducto' 
AND column_name = 'tipo_cryptocustodio';
"
```

### Script para Verificar Valores por Defecto
```bash
#!/bin/bash
# Verificar que los valores por defecto son correctos

docker compose -f docker-compose.prod.yml exec db psql -U postgres -d cryptotrace_db -c "
SELECT 
    COUNT(*) as total_lineas,
    COUNT(CASE WHEN tipo_cryptocustodio = 'Ninguno' THEN 1 END) as ninguno,
    COUNT(CASE WHEN tipo_cryptocustodio = 'c' THEN 1 END) as c,
    COUNT(CASE WHEN tipo_cryptocustodio = 'CC' THEN 1 END) as cc
FROM productos_lineatemporalproducto;

SELECT 
    COUNT(*) as total_catalogo,
    COUNT(CASE WHEN tipo_cryptocustodio = 'Ninguno' THEN 1 END) as ninguno,
    COUNT(CASE WHEN tipo_cryptocustodio = 'c' THEN 1 END) as c,
    COUNT(CASE WHEN tipo_cryptocustodio = 'CC' THEN 1 END) as cc
FROM productos_catalogoproducto;
"
```

## 📊 Datos de Ejemplo para Pruebas

### Crear Producto en Catálogo con Tipo Cryptocustodio
```bash
# Via Django shell
docker compose -f docker-compose.prod.yml exec backend python manage.py shell

# En el shell de Python:
from productos.models import CatalogoProducto
producto = CatalogoProducto.objects.get_or_create(
    codigo_producto='ABC1',
    defaults={'descripcion': 'Producto de prueba', 'tipo_cryptocustodio': 'CC'}
)[0]
producto.tipo_cryptocustodio = 'CC'
producto.save()
print(f"Producto {producto.codigo_producto} tiene tipo_cryptocustodio: {producto.tipo_cryptocustodio}")
exit()
```

## ⚡ Comandos Rápidos (Producción)

### Aplicación Completa en un Solo Bloque
```bash
# 1. Backup
BACKUP_FILE="/tmp/backup_pre_tipo_cryptocustodio_$(date +%Y%m%d_%H%M%S).sql"
docker exec cryptotrace-db pg_dump -U postgres cryptotrace_db > "$BACKUP_FILE"
echo "✅ Backup: $BACKUP_FILE"

# 2. Actualizar código (si es necesario)
cd /opt/thot-security/cryptotrace
git pull origin development  # o la rama correspondiente

# 3. Aplicar migraciones
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate productos

# 4. Verificar migraciones
docker compose -f docker-compose.prod.yml exec backend python manage.py showmigrations productos | grep -E "0033|0034"

# 5. Reconstruir y reiniciar
docker compose -f docker-compose.prod.yml build --no-cache backend frontend
docker compose -f docker-compose.prod.yml up -d backend frontend

# 6. Verificar logs
docker compose -f docker-compose.prod.yml logs backend --tail=20
docker compose -f docker-compose.prod.yml logs frontend --tail=20
```

## 📞 Troubleshooting Detallado

### Error: "django.db.utils.IntegrityError"
- **Causa**: Datos existentes incompatibles
- **Solución**: 
  1. Verificar backup
  2. Revisar logs detallados: `docker compose logs backend | grep -i integrity`
  3. Puede requerir migración de datos manual

### Error: "No such file or directory" en migraciones
- **Causa**: Archivos de migración no están en el contenedor
- **Solución**: 
  1. Verificar que los archivos existen: `ls -la cryptotrace-backend/src/productos/migrations/003*.py`
  2. Reconstruir contenedor: `docker compose build --no-cache backend`

### Frontend muestra valores antiguos
- **Causa**: Cache del navegador o contenedor no reconstruido
- **Solución**: 
  1. Limpiar cache del navegador (Ctrl+Shift+R)
  2. Reconstruir frontend: `docker compose build --no-cache frontend`
  3. Verificar que los archivos .tsx tienen los cambios

### Tipos no se asignan automáticamente
- **Causa**: Producto no existe en catálogo o lógica no funciona
- **Solución**:
  1. Verificar que el producto existe: `SELECT * FROM productos_catalogoproducto WHERE codigo_producto = 'ABC1';`
  2. Verificar que tiene tipo_cryptocustodio: `SELECT codigo_producto, tipo_cryptocustodio FROM productos_catalogoproducto WHERE codigo_producto = 'ABC1';`
  3. Revisar logs del backend al crear línea temporal: `docker compose logs backend | grep -i "tipo_cryptocustodio"`

## 📝 Notas Finales

- **Orden de Migraciones**: Las migraciones deben aplicarse en orden (0033 primero, luego 0034)
- **Tiempo Estimado**: 
  - Desarrollo local: 5-10 minutos
  - Producción: 15-30 minutos (incluyendo backups y verificaciones)
- **Impacto**: 
  - Bajo impacto: No modifica datos existentes, solo añade campos nuevos
  - Los valores por defecto son 'Ninguno', por lo que no afecta funcionalidad existente
- **Reversibilidad**: 
  - Las migraciones son reversibles
  - Se puede hacer rollback si es necesario
  - El backup permite restaurar completamente el estado anterior
