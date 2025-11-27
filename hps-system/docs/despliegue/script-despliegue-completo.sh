#!/bin/bash
# Script completo de despliegue para VPS - Sistema HPS
# Servidor: hps.aicoxidi.com (46.183.119.90)
# Ejecutar como root en la VPS

set -e  # Salir si hay error

echo "🚀 Iniciando despliegue del Sistema HPS en VPS..."
echo "📋 Servidor: hps.aicoxidi.com (46.183.119.90)"
echo ""

# =============================================================================
# PASO 1: VERIFICAR SISTEMA
# =============================================================================

echo "📦 Paso 1: Verificando sistema..."
OS_VERSION=$(cat /etc/os-release | grep "^ID=" | cut -d'=' -f2 | tr -d '"')
echo "Sistema operativo detectado: $OS_VERSION"

# =============================================================================
# PASO 2: ACTUALIZAR SISTEMA
# =============================================================================

echo ""
echo "📦 Paso 2: Actualizando sistema..."
apt update && apt upgrade -y
apt install -y git curl wget nano ufw

# =============================================================================
# PASO 3: CONFIGURAR FIREWALL
# =============================================================================

echo ""
echo "🔥 Paso 3: Configurando firewall..."
ufw --force enable
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw status

# =============================================================================
# PASO 4: INSTALAR DOCKER
# =============================================================================

echo ""
echo "🐳 Paso 4: Instalando Docker..."

# Verificar si Docker ya está instalado
if command -v docker &> /dev/null; then
    echo "Docker ya está instalado. Versión:"
    docker --version
else
    echo "Instalando Docker..."
    
    # Instalar dependencias
    apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
    
    # Agregar clave GPG de Docker
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    
    # Determinar distribución
    if [ "$OS_VERSION" = "ubuntu" ]; then
        DISTRO=$(lsb_release -cs)
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $DISTRO stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    elif [ "$OS_VERSION" = "debian" ]; then
        DISTRO=$(lsb_release -cs)
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $DISTRO stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    else
        echo "⚠️  Distribución no reconocida. Intentando instalación genérica..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
    fi
    
    # Instalar Docker
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    echo "✅ Docker instalado correctamente"
fi

# Verificar instalación
docker --version
docker compose version

# =============================================================================
# PASO 5: INSTALAR NGINX
# =============================================================================

echo ""
echo "🌐 Paso 5: Instalando Nginx..."

if command -v nginx &> /dev/null; then
    echo "Nginx ya está instalado"
else
    apt install -y nginx
fi

systemctl enable nginx
systemctl start nginx
systemctl status nginx --no-pager

# =============================================================================
# PASO 6: INSTALAR CERTBOT
# =============================================================================

echo ""
echo "🔒 Paso 6: Instalando Certbot..."

if command -v certbot &> /dev/null; then
    echo "Certbot ya está instalado"
else
    apt install -y certbot python3-certbot-nginx
fi

# =============================================================================
# PASO 7: CLONAR REPOSITORIO
# =============================================================================

echo ""
echo "📥 Paso 7: Clonando repositorio..."

if [ -d "/opt/hps-system" ]; then
    echo "⚠️  El directorio /opt/hps-system ya existe"
    read -p "¿Deseas actualizar el repositorio? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        cd /opt/hps-system
        git pull
    fi
else
    mkdir -p /opt
    cd /opt
    git clone https://github.com/calonsoaicox/hps-system.git hps-system
    cd hps-system
fi

echo "✅ Repositorio clonado en /opt/hps-system"

# =============================================================================
# PASO 8: GENERAR CLAVES SEGURAS
# =============================================================================

echo ""
echo "🔐 Paso 8: Generando claves seguras..."

# Verificar si Python está disponible
if command -v python3 &> /dev/null; then
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
else
    # Fallback: usar openssl
    JWT_SECRET=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    DB_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)
fi

echo "✅ Claves generadas:"
echo "   JWT_SECRET_KEY: ${JWT_SECRET:0:20}..."
echo "   DB_PASSWORD: ${DB_PASSWORD:0:20}..."

# =============================================================================
# PASO 9: CREAR ARCHIVO .env
# =============================================================================

echo ""
echo "⚙️  Paso 9: Configurando archivo .env..."

cd /opt/hps-system

if [ -f ".env" ]; then
    echo "⚠️  El archivo .env ya existe"
    read -p "¿Deseas sobrescribirlo? (s/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "⚠️  Manteniendo archivo .env existente"
        echo "📝 Por favor, edítalo manualmente con: nano /opt/hps-system/.env"
    else
        echo "📝 Creando nuevo archivo .env..."
        CREATE_ENV=true
    fi
else
    CREATE_ENV=true
fi

if [ "$CREATE_ENV" = true ]; then
    cat > .env << EOF
# =============================================================================
# CONFIGURACIÓN DEL SISTEMA HPS - PRODUCCIÓN
# =============================================================================

# -----------------------------------------------------------------------------
# BASE DE DATOS POSTGRESQL
# -----------------------------------------------------------------------------
POSTGRES_DB=hps_system
POSTGRES_USER=hps_user
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_HOST=db
POSTGRES_PORT=5432

# -----------------------------------------------------------------------------
# OPENAI API
# -----------------------------------------------------------------------------
OPENAI_API_KEY=TU_OPENAI_API_KEY_AQUI
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
JWT_SECRET_KEY=${JWT_SECRET}
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
# CONFIGURACIÓN FRONTEND REACT (PRODUCCIÓN)
# -----------------------------------------------------------------------------
REACT_APP_API_URL=https://hps.aicoxidi.com/api
REACT_APP_WS_URL=wss://hps.aicoxidi.com/api
REACT_APP_AGENTE_IA_WS_URL=wss://hps.aicoxidi.com/agente-ia

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
EOF

    echo "✅ Archivo .env creado"
    echo ""
    echo "⚠️  IMPORTANTE: Edita el archivo .env y configura:"
    echo "   1. OPENAI_API_KEY"
    echo "   2. SMTP_PASSWORD e IMAP_PASSWORD"
    echo ""
    read -p "Presiona Enter cuando hayas editado el .env..."
fi

# =============================================================================
# PASO 10: CONSTRUIR Y LEVANTAR SERVICIOS
# =============================================================================

echo ""
echo "🚀 Paso 10: Construyendo y levantando servicios..."

cd /opt/hps-system

echo "Construyendo imágenes Docker (esto puede tardar varios minutos)..."
docker compose build

echo "Levantando servicios..."
docker compose up -d

echo "Esperando a que los servicios estén listos..."
sleep 10

echo "Estado de los servicios:"
docker compose ps

# =============================================================================
# PASO 11: CONFIGURAR NGINX
# =============================================================================

echo ""
echo "🌐 Paso 11: Configurando Nginx..."

# Crear configuración de Nginx
cat > /etc/nginx/sites-available/hps-system << 'NGINX_CONFIG'
# Redirigir HTTP a HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name hps.aicoxidi.com;

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
    server_name hps.aicoxidi.com;

    # Certificados SSL (se generarán con Certbot)
    ssl_certificate /etc/letsencrypt/live/hps.aicoxidi.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hps.aicoxidi.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    client_max_body_size 10M;

    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    # Frontend React
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # WebSocket para API
    location /api/ws {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    # Agente IA WebSocket
    location /agente-ia {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    location /health {
        proxy_pass http://127.0.0.1:8001/health;
        access_log off;
    }
}
NGINX_CONFIG

# Habilitar sitio
ln -sf /etc/nginx/sites-available/hps-system /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Verificar configuración
nginx -t

# Recargar Nginx
systemctl reload nginx

echo "✅ Nginx configurado"

# =============================================================================
# PASO 12: OBTENER CERTIFICADO SSL
# =============================================================================

echo ""
echo "🔒 Paso 12: Obteniendo certificado SSL..."

echo "⚠️  IMPORTANTE: Asegúrate de que el DNS apunta a esta IP antes de continuar"
echo "   Dominio: hps.aicoxidi.com → 46.183.119.90"
echo ""
read -p "¿El DNS está configurado correctamente? (s/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "⚠️  Configura el DNS primero y luego ejecuta:"
    echo "   certbot --nginx -d hps.aicoxidi.com"
else
    certbot --nginx -d hps.aicoxidi.com --non-interactive --agree-tos --redirect
    echo "✅ Certificado SSL obtenido"
fi

# =============================================================================
# RESUMEN FINAL
# =============================================================================

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ DESPLIEGUE COMPLETADO"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📋 Información del despliegue:"
echo "   URL: https://hps.aicoxidi.com"
echo "   Directorio: /opt/hps-system"
echo "   Archivo .env: /opt/hps-system/.env"
echo ""
echo "📊 Comandos útiles:"
echo "   Ver estado: docker compose -f /opt/hps-system/docker-compose.yml ps"
echo "   Ver logs: docker compose -f /opt/hps-system/docker-compose.yml logs -f"
echo "   Reiniciar: docker compose -f /opt/hps-system/docker-compose.yml restart"
echo ""
echo "🔐 Próximos pasos:"
echo "   1. Verificar que puedes acceder a https://hps.aicoxidi.com"
echo "   2. Verificar que todos los servicios están corriendo"
echo "   3. Configurar backups automáticos"
echo ""
echo "═══════════════════════════════════════════════════════════════"

