# Comandos para actualizar mejoras AC21 en VPS

## Cambios incluidos

Este despliegue incluye mejoras en:
- **OCR**: Mejoras en el prompt para extracción de datos AC21
- **Frontend**: Mejoras en validaciones, checkboxes, empresas editables, etc.

## Pasos para aplicar los cambios

### 1. Actualizar código desde Git

```bash
# Ir al directorio del proyecto
cd /opt/thot-security

# Hacer pull de la rama production
git pull origin production
```

### 2. Actualizar servicio OCR

```bash
# Ir al directorio de CryptoTrace
cd cryptotrace

# Reconstruir el servicio OCR (IMPORTANTE: con --no-cache para forzar rebuild)
docker compose -f docker-compose.prod.yml build --no-cache ocr

# Reiniciar el contenedor del OCR
docker compose -f docker-compose.prod.yml up -d ocr

# Verificar que el contenedor está corriendo
docker compose -f docker-compose.prod.yml ps ocr
```

### 3. Actualizar servicio Frontend

```bash
# Reconstruir el servicio frontend (IMPORTANTE: con --no-cache para forzar rebuild)
docker compose -f docker-compose.prod.yml build --no-cache frontend

# Reiniciar el contenedor del frontend
docker compose -f docker-compose.prod.yml up -d frontend

# Verificar que el contenedor está corriendo
docker compose -f docker-compose.prod.yml ps frontend
```

### 4. Verificar logs

```bash
# Ver logs del OCR
docker compose -f docker-compose.prod.yml logs -f ocr

# Ver logs del frontend
docker compose -f docker-compose.prod.yml logs -f frontend
```

## Comandos en una sola línea (opcional)

```bash
cd /opt/thot-security && git pull origin production && cd cryptotrace && docker compose -f docker-compose.prod.yml build --no-cache ocr frontend && docker compose -f docker-compose.prod.yml up -d ocr frontend
```

## Verificar que todo funciona

Después de reconstruir, prueba:

1. **Acceder al frontend**: `https://seguridad.idiaicox.com`
2. **Subir un documento AC21** y verificar que:
   - El OCR extrae correctamente los datos
   - Las empresas se auto-seleccionan en el dropdown
   - Los checkboxes de "14. EL MATERIAL HA SIDO" funcionan correctamente
   - Los campos de empresas son editables en la pestaña "Empresas"
   - Al insertar líneas en el inventario, los índices se actualizan correctamente

## Notas importantes

- **Tiempo de construcción**: La reconstrucción puede tardar varios minutos, especialmente el frontend
- **Sin downtime**: Los contenedores se reinician uno por uno, pero puede haber un breve momento de indisponibilidad
- **Verificar API key**: Asegúrate de que `cryptotrace-ocr/.env.prod` tenga la API key de OpenAI configurada

## Rollback (si es necesario)

Si algo sale mal, puedes volver a la versión anterior:

```bash
cd /opt/thot-security
git checkout <commit-anterior>
cd cryptotrace
docker compose -f docker-compose.prod.yml build --no-cache ocr frontend
docker compose -f docker-compose.prod.yml up -d ocr frontend
```

