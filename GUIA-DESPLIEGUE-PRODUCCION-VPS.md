# 🚀 Guía Completa de Despliegue en Producción - VPS

Esta guía te llevará paso a paso para desplegar el sistema completo (CryptoTrace + HPS System) en el VPS de producción.

## 📌 Información del VPS

**Datos del servidor:**
- **IP del VPS:** `46.183.119.90`
- **DNS:** `071fb23c-d520-4dbd-9664-ca358dd46e9e.clouding.host`
- **Usuario Linux:** `root`
- **Contraseña:** `XJrdNfXBm2k-7HG`
- **Dominio:** `seguridad.idiaicox.com` (para ambas aplicaciones)

**Nota importante:** Como estás usando el usuario `root`, no necesitarás usar `sudo` en los comandos.

## 📋 Índice

1. [Preparación del Repositorio](#1-preparación-del-repositorio)
2. [Preparación del VPS](#2-preparación-del-vps)
3. [Clonar y Configurar el Repositorio](#3-clonar-y-configurar-el-repositorio)
4. [Configurar Variables de Entorno](#4-configurar-variables-de-entorno)
5. [Configurar Docker Compose de Producción](#5-configurar-docker-compose-de-producción)
6. [Construir y Levantar Contenedores](#6-construir-y-levantar-contenedores)
7. [Configurar Nginx y SSL](#7-configurar-nginx-y-ssl)
8. [Verificación y Pruebas](#8-verificación-y-pruebas)
9. [Mantenimiento y Actualizaciones](#9-mantenimiento-y-actualizaciones)

---

## 1. Preparación del Repositorio

### 1.1 Crear Rama de Producción

**En tu máquina local (desde la rama development):**

```bash
# Asegúrate de estar en development y tener los últimos cambios
git checkout development
git pull origin development

# Crear y cambiar a la rama production
git checkout -b production

# Subir la rama production al remoto
git push -u origin production
```

### 1.2 Verificar Estado del Repositorio

```bash
# Verificar que no hay cambios sin commitear
git status

# Verificar la última versión
git log --oneline -5
```

---

## 2. Preparación del VPS

### 2.1 Información del VPS

**Datos del servidor:**
- **IP del VPS:** `46.183.119.90`
- **DNS:** `071fb23c-d520-4dbd-9664-ca358dd46e9e.clouding.host`
- **Usuario Linux:** `root`
- **Contraseña:** `XJrdNfXBm2k-7HG`
- **Dominio:** `seguridad.idiaicox.com` (para ambas aplicaciones)

### 2.2 Verificar Requisitos del Sistema

```bash
# Verificar versión del sistema
lsb_release -a

# Verificar recursos disponibles
free -h
df -h
nproc
```

**Requisitos mínimos:**
- RAM: 4GB mínimo (8GB recomendado)
- CPU: 2 cores mínimo (4 cores recomendado)
- Almacenamiento: 50GB mínimo (SSD recomendado)
- SO: Ubuntu 20.04+ / Debian 11+

### 2.2 Actualizar el Sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 2.3 Instalar Docker y Docker Compose

**Nota:** Como estás usando el usuario `root`, no necesitas `sudo` ni añadir al grupo docker.

```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar Docker Compose (si no está instalado)
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verificar instalación
docker --version
docker-compose --version
```

### 2.4 Configurar Firewall (UFW)

```bash
# Habilitar firewall
ufw enable

# Permitir SSH (IMPORTANTE: hacerlo primero para no perder acceso)
ufw allow ssh
ufw allow 22/tcp

# Permitir HTTP y HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Verificar estado
ufw status
```

---

## 3. Clonar y Configurar el Repositorio

### 3.1 Crear Directorio y Clonar

```bash
# Ir al directorio /opt
cd /opt

# Crear directorio para el proyecto
mkdir -p thot-security
cd thot-security

# Clonar el repositorio (usando la rama production)
git clone -b production https://github.com/David-Pajuelo/thot-security.git .

# O si ya tienes el repositorio configurado:
# git remote add origin https://github.com/David-Pajuelo/thot-security.git
# git fetch origin
# git checkout production
```

### 3.2 Verificar Estructura del Proyecto

```bash
# Ver estructura de directorios
ls -la

# Deberías ver:
# - cryptotrace/
# - hps-system/
# - README.md
# - etc.
```

---

## 4. Configurar Variables de Entorno

### 4.1 Configurar CryptoTrace Backend

```bash
# Ir al directorio de cryptotrace-backend
cd /opt/thot-security/cryptotrace/cryptotrace-backend

# Copiar archivo de ejemplo
cp env.example .env.prod

# Editar el archivo .env.prod
nano .env.prod
```

**Variables a configurar en `.env.prod`:**

```bash
# =============================================================================
# BASE DE DATOS POSTGRESQL
# =============================================================================
DATABASE_URL=postgres://cryptotrace_user:SAmSPFVFKvlYZn_Z2Z1SGzwHdRs2WNW88FsuOZ-33eI@db:5432/cryptotrace_prod
DB_NAME=cryptotrace_prod
DB_USER=cryptotrace_user
DB_PASSWORD=SAmSPFVFKvlYZn_Z2Z1SGzwHdRs2WNW88FsuOZ-33eI
DB_HOST=db
DB_PORT=5432

# =============================================================================
# CONFIGURACIÓN DE EMAIL (GMAIL)
# =============================================================================
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

# =============================================================================
# CONFIGURACIÓN REDIS Y CELERY
# =============================================================================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_TIMEZONE=UTC

# =============================================================================
# CONFIGURACIÓN OPENAI (Agente IA)
# =============================================================================
OPENAI_API_KEY=sk-tu-openai-api-key-aqui
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# =============================================================================
# CONFIGURACIÓN DEL FRONTEND (REQUERIDAS EN PRODUCCIÓN)
# =============================================================================
FRONTEND_URL=https://seguridad.idiaicox.com
HPS_SYSTEM_URL=https://seguridad.idiaicox.com
NEXT_PUBLIC_HPS_SYSTEM_URL=https://seguridad.idiaicox.com

# =============================================================================
# CONFIGURACIÓN CORS (REQUERIDAS EN PRODUCCIÓN)
# =============================================================================
CORS_ALLOWED_ORIGINS=https://seguridad.idiaicox.com,https://www.seguridad.idiaicox.com
CORS_ALLOW_ALL_ORIGINS=False

# =============================================================================
# CONFIGURACIÓN JWT
# =============================================================================
SECRET_KEY=qpfOHYiJSQ_09OJsV1Nl3hhRRvgx2nODjETUlxQFAcUCUtfg-j6EwSnwUi1fFVYZeFE
JWT_SECRET_KEY=As_t7LfbpA_8cru4V2vZFteP1VVFf_GsaiW_Uj4tuhVpCtsjab9cSleN92w1C3EuyVE
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# =============================================================================
# CONFIGURACIÓN DJANGO (REQUERIDAS EN PRODUCCIÓN)
# =============================================================================
DEBUG=False
ENVIRONMENT=production
DJANGO_SETTINGS_MODULE=cryptotrace_backend.settings_prod
ALLOWED_HOSTS=seguridad.idiaicox.com,www.seguridad.idiaicox.com,46.183.119.90
```

**Nota:** Las SECRET_KEY ya están generadas y configuradas arriba. Si necesitas generar nuevas:

```bash
# Generar SECRET_KEY aleatorio
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 4.2 Configurar CryptoTrace Processing

```bash
# Ir al directorio de processing
cd /opt/thot-security/cryptotrace/cryptotrace-processing

# Crear archivo .env.prod
cat > .env.prod << EOF
BACKEND_URL=http://backend:8080
REDIS_HOST=redis
REDIS_PORT=6379
EOF
```

### 4.3 Configurar CryptoTrace OCR

```bash
# Ir al directorio de OCR
cd /opt/thot-security/cryptotrace/cryptotrace-ocr

# Crear archivo .env.prod
cat > .env.prod << EOF
OPENAI_API_KEY=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
BACKEND_URL=http://backend:8080
EOF
```

### 4.4 Configurar HPS System

```bash
# Ir al directorio de hps-system
cd /opt/thot-security/hps-system

# Copiar archivo de ejemplo
cp env.prod.example .env.prod

# Editar el archivo .env.prod
nano .env.prod
```

**Variables a configurar en `hps-system/.env.prod`:**

```bash
# =============================================================================
# BASE DE DATOS POSTGRESQL
# =============================================================================
POSTGRES_DB=hps_system
POSTGRES_USER=hps_user
POSTGRES_PASSWORD=Vd3GNWIEzha4-vb63mWvPhb612hKWRMFEKzh0bJonnQ
POSTGRES_HOST=db
POSTGRES_PORT=5432

# =============================================================================
# OPENAI API
# =============================================================================
OPENAI_API_KEY=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
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# =============================================================================
# CONFIGURACIÓN EMAIL (GMAIL)
# =============================================================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=aicoxidi@gmail.com
SMTP_PASSWORD=wxnopfgcliyexyqf
SMTP_FROM_NAME=HPS System
SMTP_REPLY_TO=aicoxidi@gmail.com

IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=aicoxidi@gmail.com
IMAP_PASSWORD=wxnopfgcliyexyqf
IMAP_MAILBOX=INBOX

# =============================================================================
# CONFIGURACIÓN JWT
# =============================================================================
JWT_SECRET_KEY=As_t7LfbpA_8cru4V2vZFteP1VVFf_GsaiW_Uj4tuhVpCtsjab9cSleN92w1C3EuyVE
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# =============================================================================
# CONFIGURACIÓN FRONTEND REACT (PRODUCCIÓN)
# =============================================================================
REACT_APP_API_URL=https://seguridad.idiaicox.com
REACT_APP_WS_URL=wss://seguridad.idiaicox.com
REACT_APP_AGENTE_IA_WS_URL=wss://seguridad.idiaicox.com/agente-ia/
REACT_APP_ENVIRONMENT=production
REACT_APP_VERSION=0.1.0

FRONTEND_URL=https://seguridad.idiaicox.com

# =============================================================================
# CONFIGURACIÓN BACKEND FASTAPI
# =============================================================================
BACKEND_HOST=backend
BACKEND_PORT=8001
BACKEND_WORKERS=1
BACKEND_RELOAD=false
BACKEND_URL=http://backend:8001

# =============================================================================
# CONFIGURACIÓN AGENTE IA (MIGRADO A DJANGO)
# =============================================================================
# NOTA: El agente IA ahora corre en Django Channels dentro de cryptotrace-backend
# Estas variables se mantienen por compatibilidad pero no se usan
AGENTE_IA_HOST=backend
AGENTE_IA_PORT=8000
AGENTE_IA_TIMEOUT=30
AGENTE_IA_URL=http://backend:8000

# =============================================================================
# CONFIGURACIÓN REDIS
# =============================================================================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# =============================================================================
# CONFIGURACIÓN SEGURIDAD
# =============================================================================
CORS_ORIGINS=https://seguridad.idiaicox.com
SECRET_KEY=As_t7LfbpA_8cru4V2vZFteP1VVFf_GsaiW_Uj4tuhVpCtsjab9cSleN92w1C3EuyVE
ENVIRONMENT=production
```

---

## 5. Configurar Docker Compose de Producción

### 5.1 Verificar y Ajustar docker-compose.prod.yml de CryptoTrace

```bash
# Ir al directorio de cryptotrace
cd /opt/thot-security/cryptotrace

# Revisar el archivo docker-compose.prod.yml
cat docker-compose.prod.yml
```

**Ajustes necesarios en `cryptotrace/docker-compose.prod.yml`:**

1. **Verificar URLs del frontend:**
   ```yaml
   environment:
     - NEXT_PUBLIC_API_URL=https://seguridad.idiaicox.com/api
     - NEXT_PUBLIC_PROCESSING_URL=https://seguridad.idiaicox.com/processing
     - NEXT_PUBLIC_OCR_URL=https://seguridad.idiaicox.com/ocr
   ```

2. **Verificar contraseñas de base de datos:**
   ```yaml
   environment:
     - POSTGRES_DB=${DB_NAME:-cryptotrace_prod}
     - POSTGRES_USER=${DB_USER:-cryptotrace_user}
     - POSTGRES_PASSWORD=${DB_PASSWORD:-CAMBIAR_AQUI}
   ```

3. **Verificar volúmenes:**
   ```yaml
   volumes:
     - ./cryptotrace-backend/src/albaranes/documentos:/app/albaranes/documentos
     - ./cryptotrace-backend/src/temp_documentos:/app/temp_documentos
     - backend_static:/app/static
     - backend_media:/app/media
   ```

### 5.2 Verificar y Ajustar docker-compose.prod.yml de HPS System

```bash
# Ir al directorio de hps-system
cd /opt/thot-security/hps-system

# Revisar el archivo docker-compose.prod.yml
cat docker-compose.prod.yml
```

**Ajustes necesarios en `hps-system/docker-compose.prod.yml`:**

1. **Verificar URLs del frontend:**
   ```yaml
   args:
     - REACT_APP_API_URL=${REACT_APP_API_URL}
     - REACT_APP_WS_URL=${REACT_APP_WS_URL}
     - REACT_APP_AGENTE_IA_WS_URL=${REACT_APP_AGENTE_IA_WS_URL}
   ```

2. **Verificar que el servicio agente-ia esté comentado** (ya migrado a Django)

---

## 6. Construir y Levantar Contenedores

### 6.1 Construir y Levantar CryptoTrace

```bash
# Ir al directorio de cryptotrace
cd /opt/thot-security/cryptotrace

# Construir las imágenes
docker-compose -f docker-compose.prod.yml build

# Levantar los contenedores
docker-compose -f docker-compose.prod.yml up -d

# Ver logs para verificar que todo está funcionando
docker-compose -f docker-compose.prod.yml logs -f
```

**Esperar a que todos los contenedores estén "healthy" o "Up":**

```bash
# Ver estado de los contenedores
docker-compose -f docker-compose.prod.yml ps
```

### 6.2 Ejecutar Migraciones de Base de Datos (CryptoTrace)

```bash
# Ejecutar migraciones
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Crear superusuario (opcional)
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Recolectar archivos estáticos
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

### 6.3 Construir y Levantar HPS System

```bash
# Ir al directorio de hps-system
cd /opt/thot-security/hps-system

# Construir las imágenes
docker-compose -f docker-compose.prod.yml build

# Levantar los contenedores
docker-compose -f docker-compose.prod.yml up -d

# Ver logs para verificar que todo está funcionando
docker-compose -f docker-compose.prod.yml logs -f
```

**Esperar a que todos los contenedores estén "healthy" o "Up":**

```bash
# Ver estado de los contenedores
docker-compose -f docker-compose.prod.yml ps
```

### 6.4 Ejecutar Migraciones de Base de Datos (HPS System)

```bash
# Ejecutar migraciones (si usa Alembic)
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# O si usa otro sistema de migraciones, seguir la documentación específica
```

---

## 7. Configurar Nginx y SSL

### 7.1 Instalar Certbot (Let's Encrypt)

```bash
# Instalar certbot
apt install certbot python3-certbot-nginx -y
```

### 7.2 Configurar Nginx para CryptoTrace

```bash
# Ir al directorio de cryptotrace
cd /opt/thot-security/cryptotrace

# Revisar configuración de nginx
cat nginx/conf.d/cryptotrace.conf
```

**Ajustar `nginx/conf.d/cryptotrace.conf` si es necesario:**

```nginx
server {
    listen 80;
    server_name seguridad.idiaicox.com www.seguridad.idiaicox.com;

    # Redirección a HTTPS (después de obtener certificado)
    # return 301 https://$server_name$request_uri;

    # Temporalmente, permitir HTTP para obtener certificado
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://backend:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /processing {
        proxy_pass http://processing:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ocr {
        proxy_pass http://ocr:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 7.3 Obtener Certificado SSL para CryptoTrace

```bash
# Obtener certificado SSL (asegúrate de que el dominio apunte al VPS)
certbot --nginx -d seguridad.idiaicox.com -d www.seguridad.idiaicox.com

# Seguir las instrucciones interactivas
# Certbot modificará automáticamente la configuración de nginx
```

### 7.4 Configurar Nginx para HPS System

**Nota:** HPS System puede usar su propio nginx o un proxy reverso externo. Verificar la configuración específica.

Si HPS System necesita nginx separado:

```bash
# Crear configuración de nginx para HPS System
nano /etc/nginx/sites-available/hps-system

# Configuración básica:
server {
    listen 80;
    server_name seguridad.idiaicox.com www.seguridad.idiaicox.com;

    location / {
        proxy_pass http://localhost:3000;  # Puerto del frontend de HPS
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://localhost:8001;  # Puerto del backend de HPS
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Habilitar el sitio
ln -s /etc/nginx/sites-available/hps-system /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### 7.5 Obtener Certificado SSL para HPS System

```bash
# Obtener certificado SSL
certbot --nginx -d seguridad.idiaicox.com -d www.seguridad.idiaicox.com
```

### 7.6 Configurar Renovación Automática de Certificados

```bash
# Verificar que el timer de renovación esté activo
systemctl status certbot.timer

# Probar renovación manual
certbot renew --dry-run
```

---

## 8. Verificación y Pruebas

### 8.1 Verificar Contenedores en Ejecución

```bash
# Ver todos los contenedores
docker ps -a

# Ver logs de un contenedor específico
docker logs cryptotrace-backend
docker logs cryptotrace-frontend
docker logs hps_backend
docker logs hps_frontend
```

### 8.2 Verificar Salud de los Servicios

```bash
# CryptoTrace - Verificar backend
curl http://localhost:8080/api/health
# O desde fuera del contenedor:
curl https://seguridad.idiaicox.com/api/health

# CryptoTrace - Verificar frontend
curl http://localhost:3000
# O desde fuera:
curl https://seguridad.idiaicox.com

# HPS System - Verificar backend
curl http://localhost:8001/health
# O desde fuera:
curl https://seguridad.idiaicox.com/api/health

# HPS System - Verificar frontend
curl http://localhost:3000
# O desde fuera:
curl https://seguridad.idiaicox.com
```

### 8.3 Verificar Base de Datos

```bash
# CryptoTrace - Conectar a la base de datos
docker-compose -f cryptotrace/docker-compose.prod.yml exec db psql -U cryptotrace_user -d cryptotrace_prod

# Dentro de psql:
\dt  # Ver tablas
\q   # Salir

# HPS System - Conectar a la base de datos
docker-compose -f hps-system/docker-compose.prod.yml exec db psql -U hps_user -d hps_system

# Dentro de psql:
\dt  # Ver tablas
\q   # Salir
```

### 8.4 Verificar Redis

```bash
# CryptoTrace - Verificar Redis
docker-compose -f cryptotrace/docker-compose.prod.yml exec redis redis-cli ping
# Debe responder: PONG

# HPS System - Verificar Redis
docker-compose -f hps-system/docker-compose.prod.yml exec redis redis-cli ping
# Debe responder: PONG
```

### 8.5 Pruebas de Funcionalidad

1. **Acceder a CryptoTrace:**
   - Abrir navegador: `https://seguridad.idiaicox.com`
   - Verificar que carga correctamente
   - Intentar login

2. **Acceder a HPS System:**
   - Abrir navegador: `https://seguridad.idiaicox.com`
   - Verificar que carga correctamente
   - Intentar login

3. **Verificar APIs:**
   - Probar endpoints de API desde Postman o curl
   - Verificar autenticación JWT

---

## 9. Mantenimiento y Actualizaciones

### 9.1 Actualizar Código desde Git

```bash
# Ir al directorio del proyecto
cd /opt/thot-security

# Cambiar a la rama production
git checkout production

# Obtener últimos cambios
git pull origin production

# Reconstruir y reiniciar contenedores
cd cryptotrace
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

cd ../hps-system
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### 9.2 Ver Logs

```bash
# Ver logs de todos los servicios
docker-compose -f cryptotrace/docker-compose.prod.yml logs -f
docker-compose -f hps-system/docker-compose.prod.yml logs -f

# Ver logs de un servicio específico
docker logs cryptotrace-backend -f
docker logs hps_backend -f
```

### 9.3 Backup de Base de Datos

```bash
# Backup CryptoTrace
docker-compose -f cryptotrace/docker-compose.prod.yml exec db pg_dump -U cryptotrace_user cryptotrace_prod > /opt/backups/cryptotrace_$(date +%Y%m%d_%H%M%S).sql

# Backup HPS System
docker-compose -f hps-system/docker-compose.prod.yml exec db pg_dump -U hps_user hps_system > /opt/backups/hps_$(date +%Y%m%d_%H%M%S).sql
```

### 9.4 Reiniciar Servicios

```bash
# Reiniciar todos los servicios de CryptoTrace
docker-compose -f cryptotrace/docker-compose.prod.yml restart

# Reiniciar todos los servicios de HPS System
docker-compose -f hps-system/docker-compose.prod.yml restart

# Reiniciar un servicio específico
docker-compose -f cryptotrace/docker-compose.prod.yml restart backend
```

### 9.5 Detener Servicios

```bash
# Detener todos los servicios de CryptoTrace
docker-compose -f cryptotrace/docker-compose.prod.yml down

# Detener todos los servicios de HPS System
docker-compose -f hps-system/docker-compose.prod.yml down

# Detener y eliminar volúmenes (¡CUIDADO! Esto elimina datos)
docker-compose -f cryptotrace/docker-compose.prod.yml down -v
```

---

## 📝 Checklist de Despliegue

Usa este checklist para asegurarte de que todo está configurado correctamente:

### Pre-despliegue
- [ ] Rama `production` creada y subida a Git
- [ ] VPS preparado (Docker, Docker Compose instalados)
- [ ] Firewall configurado (puertos 22, 80, 443 abiertos)
- [ ] Dominios apuntando a la IP del VPS

### Configuración
- [ ] Repositorio clonado en `/opt/thot-security`
- [ ] Variables de entorno configuradas (`.env.prod` en cada servicio)
- [ ] `SECRET_KEY` y `JWT_SECRET_KEY` generados y configurados
- [ ] Contraseñas de base de datos configuradas
- [ ] URLs de producción configuradas en `.env.prod`
- [ ] `docker-compose.prod.yml` revisado y ajustado

### Despliegue
- [ ] Contenedores de CryptoTrace construidos y levantados
- [ ] Migraciones de base de datos ejecutadas (CryptoTrace)
- [ ] Archivos estáticos recolectados (CryptoTrace)
- [ ] Contenedores de HPS System construidos y levantados
- [ ] Migraciones de base de datos ejecutadas (HPS System)
- [ ] Nginx configurado para ambos sistemas
- [ ] Certificados SSL obtenidos y configurados

### Verificación
- [ ] Todos los contenedores en estado "healthy" o "Up"
- [ ] Backends responden correctamente (`/health` o `/api/health`)
- [ ] Frontends cargan correctamente en el navegador
- [ ] SSL funcionando (HTTPS)
- [ ] Login funciona en ambos sistemas
- [ ] APIs responden correctamente
- [ ] Base de datos accesible y con datos

### Post-despliegue
- [ ] Superusuario creado (si es necesario)
- [ ] Logs revisados (sin errores críticos)
- [ ] Backup inicial realizado
- [ ] Renovación automática de SSL configurada

---

## 🔧 Solución de Problemas Comunes

### Problema: Contenedor no inicia

```bash
# Ver logs del contenedor
docker logs <nombre_contenedor>

# Verificar variables de entorno
docker-compose -f docker-compose.prod.yml config

# Verificar que los puertos no estén en uso
netstat -tulpn | grep :8080
```

### Problema: Base de datos no conecta

```bash
# Verificar que el contenedor de BD esté corriendo
docker ps | grep postgres

# Verificar logs de la BD
docker logs cryptotrace-db

# Verificar variables de conexión en .env.prod
cat cryptotrace-backend/.env.prod | grep DB_
```

### Problema: Frontend no carga

```bash
# Verificar que el frontend esté construido correctamente
docker logs cryptotrace-frontend

# Verificar variables de entorno del frontend
docker-compose -f docker-compose.prod.yml config | grep NEXT_PUBLIC
```

### Problema: SSL no funciona

```bash
# Verificar certificados
certbot certificates

# Verificar configuración de nginx
nginx -t

# Ver logs de nginx
tail -f /var/log/nginx/error.log
```

---

## 🚀 Comandos Rápidos de Referencia

### Conectar al VPS
```bash
ssh root@46.183.119.90
# Contraseña: XJrdNfXBm2k-7HG
```

### Comandos Esenciales CryptoTrace
```bash
cd /opt/thot-security/cryptotrace

# Ver estado
docker-compose -f docker-compose.prod.yml ps

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f

# Reiniciar
docker-compose -f docker-compose.prod.yml restart

# Detener
docker-compose -f docker-compose.prod.yml down

# Levantar
docker-compose -f docker-compose.prod.yml up -d

# Migraciones
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Crear superusuario
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

### Comandos Esenciales HPS System
```bash
cd /opt/thot-security/hps-system

# Ver estado
docker-compose -f docker-compose.prod.yml ps

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f

# Reiniciar
docker-compose -f docker-compose.prod.yml restart

# Detener
docker-compose -f docker-compose.prod.yml down

# Levantar
docker-compose -f docker-compose.prod.yml up -d
```

### URLs de Acceso
- **HPS System:** https://seguridad.idiaicox.com
- **CryptoTrace:** https://seguridad.idiaicox.com

---

## 📞 Información de Contacto y Soporte

Si encuentras problemas durante el despliegue:

1. Revisar los logs de los contenedores
2. Verificar las variables de entorno
3. Consultar la documentación específica de cada servicio
4. Revisar los archivos de configuración

---

## ✅ Notas Finales

- **Seguridad**: Asegúrate de cambiar todas las contraseñas por defecto
- **Backups**: Configura backups automáticos de las bases de datos
- **Monitoreo**: Considera implementar un sistema de monitoreo (Prometheus, Grafana, etc.)
- **Actualizaciones**: Mantén el sistema actualizado regularmente
- **Logs**: Revisa los logs periódicamente para detectar problemas

---

**Última actualización:** $(date +%Y-%m-%d)
**Versión del documento:** 1.0

