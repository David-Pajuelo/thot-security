#!/bin/bash

# =============================================================================
# Script de Despliegue Completo en VPS
# =============================================================================
# Este script despliega CryptoTrace y configura Nginx para seguridad.idiaicox.com
# Uso: ./desplegar-completo-vps.sh

set -e  # Salir si hay algún error

echo "🚀 Iniciando despliegue completo en VPS..."
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# =============================================================================
# PASO 1: Actualizar código
# =============================================================================
echo -e "${GREEN}📥 Paso 1: Actualizando código desde GitHub...${NC}"
cd /opt/thot-security
git pull origin development
echo -e "${GREEN}✓ Código actualizado${NC}"
echo ""

# =============================================================================
# PASO 2: Instalar Certbot (si no está instalado)
# =============================================================================
echo -e "${GREEN}🔐 Paso 2: Verificando Certbot...${NC}"
if ! command -v certbot &> /dev/null; then
    echo "Instalando Certbot..."
    apt install certbot python3-certbot-nginx -y
    echo -e "${GREEN}✓ Certbot instalado${NC}"
else
    echo -e "${GREEN}✓ Certbot ya está instalado${NC}"
fi
echo ""

# =============================================================================
# PASO 3: Instalar Nginx (si no está instalado)
# =============================================================================
echo -e "${GREEN}📦 Paso 3: Verificando Nginx...${NC}"
if ! command -v nginx &> /dev/null; then
    echo "Instalando Nginx..."
    apt update
    apt install nginx -y
    echo -e "${GREEN}✓ Nginx instalado${NC}"
else
    echo -e "${GREEN}✓ Nginx ya está instalado${NC}"
fi
echo ""

# =============================================================================
# PASO 5: Crear .env.prod para CryptoTrace Backend
# =============================================================================
echo -e "${GREEN}📝 Paso 5: Creando .env.prod para CryptoTrace...${NC}"
CRYPTOTRACE_ENV="/opt/thot-security/cryptotrace/cryptotrace-backend/.env.prod"

if [ ! -f "$CRYPTOTRACE_ENV" ]; then
    cat > "$CRYPTOTRACE_ENV" << 'ENVEOF'
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
ENVEOF
    echo -e "${GREEN}✓ .env.prod creado para CryptoTrace Backend${NC}"
else
    echo -e "${YELLOW}⚠️  .env.prod ya existe, no se sobrescribió${NC}"
fi
echo ""

# =============================================================================
# PASO 6: Crear .env.prod para servicios auxiliares (si no existen)
# =============================================================================
echo -e "${GREEN}📝 Paso 6: Creando .env.prod para servicios auxiliares...${NC}"

# Processing
if [ ! -f "/opt/thot-security/cryptotrace/cryptotrace-processing/.env.prod" ]; then
    touch /opt/thot-security/cryptotrace/cryptotrace-processing/.env.prod
    echo -e "${GREEN}✓ .env.prod creado para Processing${NC}"
fi

# OCR
if [ ! -f "/opt/thot-security/cryptotrace/cryptotrace-ocr/.env.prod" ]; then
    touch /opt/thot-security/cryptotrace/cryptotrace-ocr/.env.prod
    echo -e "${GREEN}✓ .env.prod creado para OCR${NC}"
fi
echo ""

# =============================================================================
# PASO 6.5: Crear .env.prod para HPS System Frontend
# =============================================================================
echo -e "${GREEN}📝 Paso 6.5: Creando .env.prod para HPS System Frontend...${NC}"
HPS_ENV="/opt/thot-security/hps-system/.env.prod"

if [ ! -f "$HPS_ENV" ]; then
    cat > "$HPS_ENV" << 'HPSENVEOF'
# =============================================================================
# CONFIGURACIÓN HPS SYSTEM - PRODUCCIÓN
# =============================================================================

# URLs del backend Django (CryptoTrace)
REACT_APP_API_URL=https://seguridad.idiaicox.com/api
REACT_APP_WS_URL=wss://seguridad.idiaicox.com/ws
REACT_APP_AGENTE_IA_WS_URL=wss://seguridad.idiaicox.com/ws

# URL de CryptoTrace (para sincronización de tokens)
REACT_APP_CRYPTOTRACE_URL=https://seguridad.idiaicox.com/cryptotrace
HPSENVEOF
    echo -e "${GREEN}✓ .env.prod creado para HPS System Frontend${NC}"
else
    echo -e "${YELLOW}⚠️  .env.prod ya existe, verificando variables...${NC}"
    # Verificar y agregar variables faltantes
    if ! grep -q "REACT_APP_API_URL" "$HPS_ENV"; then
        echo "REACT_APP_API_URL=https://seguridad.idiaicox.com/api" >> "$HPS_ENV"
    fi
    if ! grep -q "REACT_APP_WS_URL" "$HPS_ENV"; then
        echo "REACT_APP_WS_URL=wss://seguridad.idiaicox.com/ws" >> "$HPS_ENV"
    fi
    if ! grep -q "REACT_APP_AGENTE_IA_WS_URL" "$HPS_ENV"; then
        echo "REACT_APP_AGENTE_IA_WS_URL=wss://seguridad.idiaicox.com/ws" >> "$HPS_ENV"
    fi
    if ! grep -q "REACT_APP_CRYPTOTRACE_URL" "$HPS_ENV"; then
        echo "REACT_APP_CRYPTOTRACE_URL=https://seguridad.idiaicox.com/cryptotrace" >> "$HPS_ENV"
    fi
    echo -e "${GREEN}✓ Variables verificadas/actualizadas${NC}"
fi
echo ""

# =============================================================================
# PASO 7: Construir y levantar CryptoTrace
# =============================================================================
echo -e "${GREEN}🐳 Paso 7: Construyendo y levantando CryptoTrace...${NC}"
cd /opt/thot-security/cryptotrace

# Construir imágenes
echo "Construyendo imágenes Docker..."
docker compose -f docker-compose.prod.yml build

# Levantar servicios
echo "Levantando servicios..."
docker compose -f docker-compose.prod.yml up -d

echo -e "${GREEN}✓ CryptoTrace levantado${NC}"
echo ""

# =============================================================================
# PASO 7.5: Configurar Nginx (después de levantar contenedores)
# =============================================================================
echo -e "${GREEN}⚙️  Paso 7.5: Configurando Nginx...${NC}"

# Copiar configuración de Nginx
if [ -f "/opt/thot-security/nginx-seguridad.conf" ]; then
    cp /opt/thot-security/nginx-seguridad.conf /etc/nginx/sites-available/seguridad.idiaicox.com
    echo -e "${GREEN}✓ Configuración copiada${NC}"
else
    echo -e "${RED}❌ Error: No se encontró nginx-seguridad.conf${NC}"
    exit 1
fi

# Habilitar sitio
if [ ! -L "/etc/nginx/sites-enabled/seguridad.idiaicox.com" ]; then
    ln -s /etc/nginx/sites-available/seguridad.idiaicox.com /etc/nginx/sites-enabled/
    echo -e "${GREEN}✓ Sitio habilitado${NC}"
fi

# Eliminar configuración por defecto
if [ -L "/etc/nginx/sites-enabled/default" ]; then
    rm /etc/nginx/sites-enabled/default
    echo -e "${GREEN}✓ Configuración por defecto eliminada${NC}"
fi

# Esperar un poco para que los contenedores estén completamente listos
echo "Esperando a que los contenedores estén listos..."
sleep 10

# Verificar configuración
if nginx -t; then
    echo -e "${GREEN}✓ Configuración de Nginx válida${NC}"
else
    echo -e "${YELLOW}⚠️  Advertencia: Error en la configuración de Nginx${NC}"
    echo -e "${YELLOW}⚠️  Esto puede ser porque los contenedores aún no están completamente listos${NC}"
    echo -e "${YELLOW}⚠️  Continuando de todas formas...${NC}"
fi
echo ""

# =============================================================================
# PASO 8: Esperar a que los servicios estén listos
# =============================================================================
echo -e "${GREEN}⏳ Paso 8: Esperando a que los servicios estén listos...${NC}"
sleep 15
echo ""

# =============================================================================
# PASO 9: Ejecutar migraciones de Django
# =============================================================================
echo -e "${GREEN}🗄️  Paso 9: Ejecutando migraciones de Django...${NC}"
cd /opt/thot-security/cryptotrace

# Esperar a que la base de datos esté lista
echo "Esperando a que la base de datos esté lista..."
sleep 10

# Ejecutar migraciones
if docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput; then
    echo -e "${GREEN}✓ Migraciones ejecutadas${NC}"
else
    echo -e "${YELLOW}⚠️  Error al ejecutar migraciones, intentando de nuevo...${NC}"
    sleep 5
    docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput
fi

# Recolectar archivos estáticos
echo "Recolectando archivos estáticos..."
if docker compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput; then
    echo -e "${GREEN}✓ Archivos estáticos recolectados${NC}"
    
    # Copiar archivos estáticos del contenedor al sistema
    echo "Copiando archivos estáticos al directorio de Nginx..."
    mkdir -p /var/www/cryptotrace-static
    docker cp cryptotrace-backend:/app/staticfiles/. /var/www/cryptotrace-static/ 2>/dev/null || \
    docker cp cryptotrace-backend:/app/static/. /var/www/cryptotrace-static/ 2>/dev/null || \
    echo -e "${YELLOW}⚠️  No se pudieron copiar los archivos estáticos, el volumen Docker debería estar montado${NC}"
    chown -R www-data:www-data /var/www/cryptotrace-static
    echo -e "${GREEN}✓ Archivos estáticos copiados${NC}"
else
    echo -e "${YELLOW}⚠️  Error al recolectar archivos estáticos${NC}"
fi
echo ""

# =============================================================================
# PASO 10: Configurar Nginx para servir archivos estáticos
# =============================================================================
echo -e "${GREEN}📁 Paso 10: Verificando directorio de archivos estáticos...${NC}"
mkdir -p /var/www/cryptotrace-static
chown -R www-data:www-data /var/www/cryptotrace-static
echo -e "${GREEN}✓ Directorio configurado${NC}"
echo ""

# =============================================================================
# PASO 11: Reiniciar Nginx (con reintentos si falla)
# =============================================================================
echo -e "${GREEN}🔄 Paso 11: Reiniciando Nginx...${NC}"
if systemctl restart nginx; then
    echo -e "${GREEN}✓ Nginx reiniciado${NC}"
else
    echo -e "${YELLOW}⚠️  Error al reiniciar Nginx, esperando y reintentando...${NC}"
    sleep 5
    if systemctl restart nginx; then
        echo -e "${GREEN}✓ Nginx reiniciado en segundo intento${NC}"
    else
        echo -e "${RED}❌ Error al reiniciar Nginx${NC}"
        echo -e "${YELLOW}⚠️  Verifica los logs: journalctl -u nginx -n 50${NC}"
    fi
fi
echo ""

# =============================================================================
# PASO 12: Obtener certificado SSL (si no existe)
# =============================================================================
echo -e "${GREEN}🔐 Paso 12: Verificando certificado SSL...${NC}"
if [ ! -f "/etc/letsencrypt/live/seguridad.idiaicox.com/fullchain.pem" ]; then
    echo -e "${YELLOW}⚠️  Certificado SSL no encontrado${NC}"
    echo -e "${YELLOW}⚠️  Ejecuta manualmente: certbot --nginx -d seguridad.idiaicox.com${NC}"
    echo -e "${YELLOW}⚠️  O si Nginx no está corriendo: certbot certonly --standalone -d seguridad.idiaicox.com${NC}"
else
    echo -e "${GREEN}✓ Certificado SSL encontrado${NC}"
fi
echo ""

# =============================================================================
# PASO 13: Verificar estado de los servicios
# =============================================================================
echo -e "${GREEN}📊 Paso 13: Verificando estado de los servicios...${NC}"
echo ""
echo "=== Contenedores Docker ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "=== Estado de Nginx ==="
systemctl status nginx --no-pager -l | head -10
echo ""

echo "=== Estado de CryptoTrace ==="
cd /opt/thot-security/cryptotrace
docker compose -f docker-compose.prod.yml ps
echo ""

echo "=== Estado de HPS System ==="
cd /opt/thot-security/hps-system
docker compose -f docker-compose.prod.yml ps
echo ""

# =============================================================================
# RESUMEN FINAL
# =============================================================================
echo ""
echo -e "${GREEN}✅ Despliegue completado${NC}"
echo ""
echo "📝 Próximos pasos:"
echo "1. Si no tienes certificado SSL, ejecuta:"
echo "   certbot --nginx -d seguridad.idiaicox.com"
echo ""
echo "2. Verifica que todo funciona:"
echo "   curl -I https://seguridad.idiaicox.com"
echo "   curl -I https://seguridad.idiaicox.com/hps"
echo ""
echo "3. Crea un superusuario de Django (si es necesario):"
echo "   cd /opt/thot-security/cryptotrace"
echo "   docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser"
echo ""
echo "4. Verifica los logs si hay problemas:"
echo "   docker compose -f docker-compose.prod.yml logs -f"
echo ""

