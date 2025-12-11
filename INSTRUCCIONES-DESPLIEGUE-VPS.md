# Instrucciones de Despliegue en VPS

## 1. Configurar Nginx

### Opción A: Nginx en el host (recomendado)

```bash
# Instalar Nginx
apt update
apt install nginx -y

# Crear directorio para certificados SSL
mkdir -p /etc/letsencrypt/live/seguridad.idiaicox.com

# Copiar configuración de Nginx
# (Copia el contenido de nginx-seguridad.conf a /etc/nginx/sites-available/seguridad.idiaicox.com)
nano /etc/nginx/sites-available/seguridad.idiaicox.com

# Habilitar el sitio
ln -s /etc/nginx/sites-available/seguridad.idiaicox.com /etc/nginx/sites-enabled/

# Eliminar configuración por defecto
rm /etc/nginx/sites-enabled/default

# Verificar configuración
nginx -t

# Reiniciar Nginx
systemctl restart nginx
```

### Opción B: Nginx en Docker (si prefieres)

Puedes usar el Nginx de CryptoTrace modificado para servir ambos sistemas.

## 2. Obtener Certificado SSL con Let's Encrypt

```bash
# Instalar Certbot
apt install certbot python3-certbot-nginx -y

# Obtener certificado (antes de levantar los servicios)
certbot --nginx -d seguridad.idiaicox.com

# O si prefieres standalone (sin Nginx corriendo)
certbot certonly --standalone -d seguridad.idiaicox.com
```

## 3. Configurar CryptoTrace

### 3.1 Crear .env.prod para CryptoTrace

```bash
cd /opt/thot-security/cryptotrace/cryptotrace-backend
nano .env.prod
```

**Contenido del .env.prod de CryptoTrace:**

```bash
# =============================================================================
# CONFIGURACIÓN CRYPTOTRACE - PRODUCCIÓN
# =============================================================================

# Base de datos
DATABASE_URL=postgres://cryptotrace_user:cryptotrace_pass@cryptotrace-db:5432/cryptotrace_db
DB_NAME=cryptotrace_db
DB_USER=cryptotrace_user
DB_PASSWORD=cryptotrace_pass
DB_HOST=cryptotrace-db
DB_PORT=5432

# Redis
REDIS_HOST=cryptotrace-redis
REDIS_PORT=6379
REDIS_URL=redis://cryptotrace-redis:6379/0
CELERY_BROKER_URL=redis://cryptotrace-redis:6379/0
CELERY_RESULT_BACKEND=redis://cryptotrace-redis:6379/0

# Email (Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=aicoxidi@gmail.com
SMTP_PASSWORD=wxnopfgcliyexyqf
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=noreply@hps-system.com
SMTP_FROM_NAME=Sistema HPS
SMTP_REPLY_TO=aicoxidi@gmail.com

IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=aicoxidi@gmail.com
IMAP_PASSWORD=wxnopfgcliyexyqf
IMAP_MAILBOX=INBOX

# OpenAI
OPENAI_API_KEY=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
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# JWT
SECRET_KEY=As_t7LfbpA_8cru4V2vZFteP1VVFf_GsaiW_Uj4tuhVpCtsjab9cSleN92w1C3EuyVE
JWT_SECRET_KEY=As_t7LfbpA_8cru4V2vZFteP1VVFf_GsaiW_Uj4tuhVpCtsjab9cSleN92w1C3EuyVE
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Django
DEBUG=False
ALLOWED_HOSTS=seguridad.idiaicox.com,localhost,127.0.0.1,cryptotrace-backend
DJANGO_SETTINGS_MODULE=cryptotrace_backend.settings_prod

# URLs
FRONTEND_URL=https://seguridad.idiaicox.com
HPS_SYSTEM_URL=https://seguridad.idiaicox.com/hps
CORS_ALLOWED_ORIGINS=https://seguridad.idiaicox.com
```

### 3.2 Crear .env.prod para servicios auxiliares

```bash
# Processing
cd /opt/thot-security/cryptotrace/cryptotrace-processing
nano .env.prod
# (Puede estar vacío o tener variables específicas si las necesitas)

# OCR
cd /opt/thot-security/cryptotrace/cryptotrace-ocr
nano .env.prod
# (Puede estar vacío o tener variables específicas si las necesitas)
```

## 4. Levantar CryptoTrace

```bash
cd /opt/thot-security/cryptotrace

# Construir imágenes
docker compose -f docker-compose.prod.yml build

# Levantar servicios
docker compose -f docker-compose.prod.yml up -d

# Verificar estado
docker compose -f docker-compose.prod.yml ps

# Ver logs
docker compose -f docker-compose.prod.yml logs -f
```

## 5. Ejecutar migraciones de Django

```bash
# Ejecutar migraciones
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Crear superusuario (si es necesario)
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Recolectar archivos estáticos
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

## 6. Conectar HPS System con CryptoTrace

El frontend de HPS System ya está configurado para conectarse a `https://seguridad.idiaicox.com` (que apunta al backend de CryptoTrace).

## 7. Verificar que todo funciona

```bash
# Verificar contenedores
docker ps

# Verificar Nginx
systemctl status nginx

# Verificar certificado SSL
certbot certificates

# Probar acceso
curl -I https://seguridad.idiaicox.com
curl -I https://seguridad.idiaicox.com/hps
```

## 8. Configurar auto-renovación de SSL

```bash
# Verificar que el timer está activo
systemctl status certbot.timer

# Si no está activo, habilitarlo
systemctl enable certbot.timer
systemctl start certbot.timer
```

## Notas importantes

1. **Red Docker**: Asegúrate de que HPS System y CryptoTrace estén en la misma red Docker o que puedan comunicarse.
2. **Puertos**: 
   - CryptoTrace frontend: 3000 (interno)
   - CryptoTrace backend: 8080 (interno)
   - HPS System frontend: 3001 (interno, mapeado a 3000 en el contenedor)
3. **Base de datos**: CryptoTrace y HPS System comparten la misma base de datos (cryptotrace_db).
4. **Redis**: CryptoTrace y HPS System comparten el mismo Redis (cryptotrace-redis).

