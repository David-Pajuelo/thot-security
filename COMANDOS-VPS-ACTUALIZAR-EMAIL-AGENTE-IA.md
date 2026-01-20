# Comandos para actualizar corrección de envío de correos del agente IA en VPS

## Cambios incluidos

Este despliegue incluye mejoras en:
- **Agente IA**: Ahora usa Celery para envío de correos
- **URL del formulario HPS**: Corregida para usar HPS_SYSTEM_URL
- **Logging**: Mejoras en logs para diagnóstico de envío de correos
- **Mensajes del agente IA**: Muestran correctamente si el correo se envió o no

## Pasos para aplicar los cambios

### 1. Actualizar código desde Git

```bash
# Ir al directorio del proyecto
cd /opt/thot-security

# Hacer pull de la rama production
git pull origin production
```

### 2. Actualizar servicio Backend (IMPORTANTE: Build completo para recargar .env.prod)

```bash
# Ir al directorio de CryptoTrace
cd cryptotrace

# Reconstruir el servicio backend (IMPORTANTE: con --no-cache para forzar rebuild completo)
docker compose -f docker-compose.prod.yml build --no-cache backend

# Reiniciar el contenedor del backend
docker compose -f docker-compose.prod.yml up -d backend

# Verificar que el contenedor está corriendo
docker compose -f docker-compose.prod.yml ps backend
```

### 3. Actualizar servicio Celery Worker (IMPORTANTE: Build completo para recargar .env.prod)

```bash
# Reconstruir el servicio celery-worker (IMPORTANTE: con --no-cache para forzar rebuild completo)
docker compose -f docker-compose.prod.yml build --no-cache celery-worker

# Reiniciar el contenedor del celery-worker
docker compose -f docker-compose.prod.yml up -d celery-worker

# Verificar que el contenedor está corriendo
docker compose -f docker-compose.prod.yml ps celery-worker
```

### 4. Verificar logs

```bash
# Ver logs del backend
docker compose -f docker-compose.prod.yml logs -f backend

# Ver logs de celery-worker
docker compose -f docker-compose.prod.yml logs -f celery-worker
```

## Comandos en una sola línea (opcional)

```bash
cd /opt/thot-security && git pull origin production && cd cryptotrace && docker compose -f docker-compose.prod.yml build --no-cache backend celery-worker && docker compose -f docker-compose.prod.yml up -d backend celery-worker
```

## Verificar que todo funciona

Después de reconstruir, prueba:

1. **Acceder al sistema**: `https://seguridad.idiaicox.com`
2. **Probar envío de correo desde el agente IA**:
   - El agente IA debe mostrar correctamente si el correo se envió o no
   - La URL del formulario debe apuntar a HPS System, no a CryptoTrace
   - Los logs deben mostrar información detallada del proceso de envío

## Verificar variables de entorno

Para verificar que las variables se cargaron correctamente:

```bash
# Verificar SMTP_PASSWORD (debe estar sin espacios)
docker exec cryptotrace-backend env | grep SMTP_PASSWORD

# Verificar HPS_SYSTEM_URL
docker exec cryptotrace-backend env | grep HPS_SYSTEM_URL

# Verificar FRONTEND_URL
docker exec cryptotrace-backend env | grep FRONTEND_URL
```

## Notas importantes

- **Tiempo de construcción**: La reconstrucción puede tardar varios minutos
- **Sin downtime**: Los contenedores se reinician uno por uno, pero puede haber un breve momento de indisponibilidad
- **Variables de entorno**: Asegúrate de que `cryptotrace-backend/.env.prod` tenga la contraseña SMTP correcta (sin espacios) y HPS_SYSTEM_URL configurada
- **Build completo necesario**: El `--no-cache` es importante para que se recarguen todas las variables de entorno desde el .env.prod

## Rollback (si es necesario)

Si algo sale mal, puedes volver a la versión anterior:

```bash
cd /opt/thot-security
git checkout <commit-anterior>
cd cryptotrace
docker compose -f docker-compose.prod.yml build --no-cache backend celery-worker
docker compose -f docker-compose.prod.yml up -d backend celery-worker
```
