# 🚀 Guía de Migración a VPS - Sistema HPS

Esta guía te acompañará paso a paso en la migración del Sistema HPS a una VPS en producción.

## 📋 Índice

1. [Requisitos Previos](#requisitos-previos)
2. [Preparación de la VPS](#preparación-de-la-vps)
3. [Instalación de Dependencias](#instalación-de-dependencias)
4. [Configuración del Entorno](#configuración-del-entorno)
5. [Despliegue de la Aplicación](#despliegue-de-la-aplicación)
6. [Configuración de Dominio y SSL](#configuración-de-dominio-y-ssl)
7. [Configuración de Backups](#configuración-de-backups)
8. [Monitoreo y Mantenimiento](#monitoreo-y-mantenimiento)
9. [Solución de Problemas](#solución-de-problemas)

---

## 🔐 Requisitos Previos

### Información Necesaria

Antes de comenzar, asegúrate de tener:

- [ ] **Acceso SSH a la VPS**
  - IP o dominio de la VPS
  - Usuario y contraseña/SSH key
  - Permisos de sudo/root

- [ ] **Credenciales del Sistema**
  - Base de datos (PostgreSQL): usuario, contraseña, nombre de BD
  - Email (SMTP/IMAP): host, puerto, usuario, contraseña
  - OpenAI API Key
  - JWT Secret Key (generar uno seguro)

- [ ] **Dominio (opcional pero recomendado)**
  - Nombre de dominio
  - Acceso al panel DNS
  - Registro A/AAAA apuntando a la IP de la VPS

- [ ] **Puertos a Abrir**
  - 80 (HTTP)
  - 443 (HTTPS)
  - 22 (SSH)
  - 8000 (Agente IA - interno)
  - 8001 (Backend - interno)
  - 3000 (Frontend - interno)

---

## 🖥️ Preparación de la VPS

### Paso 1: Conectar y Actualizar el Sistema

```bash
# Conectar a la VPS
ssh usuario@tu-vps-ip

# Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# Instalar herramientas básicas
sudo apt install -y git curl wget nano ufw
```

### Paso 2: Configurar Firewall

```bash
# Habilitar firewall
sudo ufw enable

# Permitir SSH
sudo ufw allow 22/tcp

# Permitir HTTP y HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Verificar estado
sudo ufw status
```

### Paso 3: Crear Usuario para la Aplicación (Opcional pero recomendado)

```bash
# Crear usuario no-root
sudo adduser hps-app
sudo usermod -aG sudo hps-app

# Cambiar al nuevo usuario
su - hps-app
```

---

## 📦 Instalación de Dependencias

### Paso 1: Instalar Docker

```bash
# Instalar dependencias
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Agregar clave GPG de Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Agregar repositorio de Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Agregar usuario al grupo docker
sudo usermod -aG docker $USER

# Verificar instalación
docker --version
docker compose version

# Reiniciar sesión para aplicar cambios de grupo
# (o ejecutar: newgrp docker)
```

### Paso 2: Instalar Nginx (Proxy Reverso)

```bash
# Instalar Nginx
sudo apt install -y nginx

# Habilitar Nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Verificar estado
sudo systemctl status nginx
```

### Paso 3: Instalar Certbot (Para SSL)

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx
```

---

## ⚙️ Configuración del Entorno

### Paso 1: Clonar el Repositorio

```bash
# Crear directorio para la aplicación
sudo mkdir -p /opt/hps-system
sudo chown $USER:$USER /opt/hps-system

# Clonar repositorio
cd /opt
git clone https://github.com/calonsoaicox/hps-system.git hps-system
cd hps-system
```

### Paso 2: Crear Archivo .env

```bash
# Copiar archivo de ejemplo
cp env.example .env

# Editar con tus credenciales
nano .env
```

### Paso 3: Configurar Variables de Entorno

Edita el archivo `.env` con las siguientes variables:

```bash
# =============================================================================
# CONFIGURACIÓN DEL SISTEMA HPS - PRODUCCIÓN
# =============================================================================

# -----------------------------------------------------------------------------
# BASE DE DATOS POSTGRESQL
# -----------------------------------------------------------------------------
POSTGRES_DB=hps_system
POSTGRES_USER=hps_user
POSTGRES_PASSWORD=TU_PASSWORD_SEGURO_AQUI
POSTGRES_HOST=db
POSTGRES_PORT=5432

# -----------------------------------------------------------------------------
# OPENAI API
# -----------------------------------------------------------------------------
OPENAI_API_KEY=tu_openai_api_key_aqui
OPENAI_MODEL=gpt-4o-mini

# -----------------------------------------------------------------------------
# CONFIGURACIÓN EMAIL (PRIVATE MAIL)
# -----------------------------------------------------------------------------
SMTP_HOST=mail.privateemail.com
SMTP_PORT=587
SMTP_USER=seguridad@idiaicox.com
SMTP_PASSWORD=TU_PASSWORD_EMAIL_AQUI
SMTP_FROM_NAME=HPS System
SMTP_REPLY_TO=seguridad@idiaicox.com

IMAP_HOST=mail.privateemail.com
IMAP_PORT=993
IMAP_USER=seguridad@idiaicox.com
IMAP_PASSWORD=TU_PASSWORD_EMAIL_AQUI
IMAP_MAILBOX=INBOX

# -----------------------------------------------------------------------------
# CONFIGURACIÓN JWT
# -----------------------------------------------------------------------------
JWT_SECRET_KEY=GENERAR_UNA_CLAVE_SECRETA_MUY_SEGURA_AQUI
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DEL AGENTE IA
# -----------------------------------------------------------------------------
AGENTE_IA_HOST=agente-ia
AGENTE_IA_PORT=8000
AGENTE_IA_URL=http://agente-ia:8000

# -----------------------------------------------------------------------------
# CONFIGURACIÓN REDIS
# -----------------------------------------------------------------------------
REDIS_HOST=redis
REDIS_PORT=6379

# -----------------------------------------------------------------------------
# CONFIGURACIÓN FRONTEND REACT (AJUSTAR CON TU DOMINIO)
# -----------------------------------------------------------------------------
REACT_APP_API_URL=https://tu-dominio.com/api
REACT_APP_WS_URL=wss://tu-dominio.com/api
REACT_APP_AGENTE_IA_WS_URL=wss://tu-dominio.com/agente-ia

# -----------------------------------------------------------------------------
# CONFIGURACIÓN BACKEND FASTAPI
# -----------------------------------------------------------------------------
BACKEND_HOST=backend
BACKEND_PORT=8001

# -----------------------------------------------------------------------------
# CONFIGURACIÓN SEGURIDAD
# -----------------------------------------------------------------------------
ENVIRONMENT=production
DEBUG=false
```

**Nota importante**: Genera una `JWT_SECRET_KEY` segura:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Paso 4: Actualizar docker-compose.yml para Producción

Revisa el `docker-compose.yml` y ajusta si es necesario:

- Los puertos expuestos deben estar solo en la red interna
- Frontend debe usar variables de entorno para las URLs del API
- Verificar que todos los servicios tengan `restart: unless-stopped`

---

## 🚀 Despliegue de la Aplicación

### Paso 1: Construir y Levantar Contenedores

```bash
# Ir al directorio del proyecto
cd /opt/hps-system

# Construir imágenes
docker compose build

# Levantar servicios
docker compose up -d

# Verificar estado
docker compose ps
```

### Paso 2: Verificar Logs

```bash
# Ver logs de todos los servicios
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

### Paso 3: Verificar Health Checks

```bash
# Verificar que los servicios estén saludables
docker compose ps

# Todos deberían mostrar "healthy" o "Up"
```

---

## 🌐 Configuración de Dominio y SSL

### Paso 1: Configurar DNS

En tu panel de DNS, crea los siguientes registros:

```
A     @                    tu-ip-vps
A     www                  tu-ip-vps
```

### Paso 2: Configurar Nginx como Proxy Reverso

```bash
# Crear configuración de Nginx
sudo nano /etc/nginx/sites-available/hps-system
```

Contenido de la configuración:

```nginx
# Redirigir HTTP a HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name tu-dominio.com www.tu-dominio.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# Configuración HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name tu-dominio.com www.tu-dominio.com;

    # Certificados SSL (se generarán con Certbot)
    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;
    
    # Configuración SSL recomendada
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Tamaño máximo de carga
    client_max_body_size 10M;

    # Frontend React
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket para API
    location /api/ws {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Agente IA WebSocket
    location /agente-ia {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Paso 3: Habilitar Configuración de Nginx

```bash
# Crear enlace simbólico
sudo ln -s /etc/nginx/sites-available/hps-system /etc/nginx/sites-enabled/

# Eliminar configuración por defecto
sudo rm /etc/nginx/sites-enabled/default

# Verificar configuración
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx
```

### Paso 4: Obtener Certificado SSL

```bash
# Obtener certificado con Certbot
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Seguir las instrucciones interactivas
# Certbot configurará automáticamente Nginx para usar HTTPS
```

### Paso 5: Configurar Renovación Automática de SSL

```bash
# Verificar que el cron job esté configurado
sudo certbot renew --dry-run
```

---

## 💾 Configuración de Backups

### Paso 1: Crear Script de Backup

```bash
# Crear directorio para backups
sudo mkdir -p /opt/backups/hps-system
sudo chown $USER:$USER /opt/backups/hps-system

# Crear script de backup
nano /opt/backups/hps-system/backup.sh
```

Contenido del script:

```bash
#!/bin/bash

# Configuración
BACKUP_DIR="/opt/backups/hps-system"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="hps_backup_${DATE}.sql"

# Crear backup de PostgreSQL
docker exec hps_postgres pg_dump -U hps_user hps_system > "${BACKUP_DIR}/${BACKUP_FILE}"

# Comprimir backup
gzip "${BACKUP_DIR}/${BACKUP_FILE}"

# Eliminar backups antiguos (más de 30 días)
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +30 -delete

echo "Backup completado: ${BACKUP_FILE}.gz"
```

### Paso 2: Hacer Ejecutable y Probar

```bash
# Hacer ejecutable
chmod +x /opt/backups/hps-system/backup.sh

# Probar manualmente
/opt/backups/hps-system/backup.sh
```

### Paso 3: Configurar Cron para Backups Automáticos

```bash
# Editar crontab
crontab -e

# Agregar línea para backup diario a las 2 AM
0 2 * * * /opt/backups/hps-system/backup.sh >> /opt/backups/hps-system/backup.log 2>&1
```

---

## 📊 Monitoreo y Mantenimiento

### Comandos Útiles

```bash
# Ver estado de servicios
docker compose ps

# Ver logs en tiempo real
docker compose logs -f

# Reiniciar un servicio
docker compose restart backend

# Reiniciar todos los servicios
docker compose restart

# Ver uso de recursos
docker stats

# Actualizar la aplicación
cd /opt/hps-system
git pull
docker compose build
docker compose up -d
```

### Verificar Salud del Sistema

```bash
# Verificar contenedores
docker ps

# Verificar logs de errores
docker compose logs | grep -i error

# Verificar espacio en disco
df -h

# Verificar uso de memoria
free -h
```

---

## 🔧 Solución de Problemas

### Problema: Contenedores no inician

```bash
# Ver logs detallados
docker compose logs

# Verificar archivo .env
cat .env

# Verificar recursos del sistema
docker system df
```

### Problema: Error de conexión a base de datos

```bash
# Verificar que el contenedor de BD esté corriendo
docker compose ps db

# Ver logs de la BD
docker compose logs db

# Probar conexión manual
docker exec -it hps_postgres psql -U hps_user -d hps_system
```

### Problema: Error de SSL/Nginx

```bash
# Verificar configuración de Nginx
sudo nginx -t

# Ver logs de Nginx
sudo tail -f /var/log/nginx/error.log

# Reiniciar Nginx
sudo systemctl restart nginx
```

### Problema: Frontend no carga

```bash
# Verificar que el contenedor esté corriendo
docker compose ps frontend

# Ver logs del frontend
docker compose logs frontend

# Verificar variables de entorno
docker exec hps_frontend env | grep REACT_APP
```

---

## ✅ Checklist Final

Antes de considerar el despliegue completo, verifica:

- [ ] Todos los servicios están corriendo (`docker compose ps`)
- [ ] El dominio apunta correctamente a la VPS
- [ ] SSL está configurado y funcionando (https://)
- [ ] Puedes acceder al frontend desde el navegador
- [ ] La API responde correctamente
- [ ] El agente IA funciona
- [ ] Los emails se envían correctamente
- [ ] Los backups están configurados
- [ ] El firewall está configurado correctamente
- [ ] Los logs no muestran errores críticos

---

## 📞 Próximos Pasos

Una vez completado el despliegue:

1. **Crear usuario administrador inicial**
2. **Configurar monitoreo adicional** (opcional: Prometheus, Grafana)
3. **Configurar alertas de seguridad**
4. **Documentar credenciales de forma segura**
5. **Realizar pruebas de carga** (opcional)

---

**¡Despliegue completado!** 🎉

Si encuentras algún problema durante el despliegue, revisa la sección de "Solución de Problemas" o consulta los logs de los servicios.

