#!/bin/bash

# Script para configurar Let's Encrypt SSL en CryptoTrace
# Ejecutar después del primer despliegue con certificados temporales

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Variables
DOMAIN_NAME="${DOMAIN_NAME:-cryptotrace.idiaicox.com}"
EMAIL="${EMAIL:-admin@idiaicox.com}"
COMPOSE_FILE="docker-compose.prod.yml"

# Verificar que el dominio esté configurado
if [ "$DOMAIN_NAME" == "cryptotrace.idiaicox.com" ]; then
    log_info "Usando dominio configurado: $DOMAIN_NAME"
elif [ "$DOMAIN_NAME" == "tu-dominio.com" ]; then
    log_error "Por favor, configura la variable DOMAIN_NAME"
    echo "Ejemplo: DOMAIN_NAME=cryptotrace.idiaicox.com ./scripts/setup-letsencrypt.sh"
    exit 1
fi

log_info "=== CONFIGURANDO LET'S ENCRYPT PARA $DOMAIN_NAME ==="

# Verificar que la aplicación esté corriendo
if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q "cryptotrace-nginx.*Up"; then
    log_error "Nginx no está corriendo. Ejecuta primero el despliegue completo."
    exit 1
fi

# Crear configuración temporal para obtener certificados
log_info "Creando configuración temporal para certificación..."

# Detener nginx temporalmente
docker-compose -f "$COMPOSE_FILE" stop nginx

# Configuración temporal para verificación HTTP
cat > nginx/conf.d/letsencrypt-temp.conf << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF

# Crear directorio para certbot
mkdir -p certbot/www

# Añadir servicio certbot temporal al docker-compose
log_info "Ejecutando certbot para obtener certificados..."

# Ejecutar certbot standalone (solo para el dominio principal)
docker run --rm -p 80:80 -p 443:443 \
    -v "./nginx/ssl:/etc/letsencrypt" \
    -v "./certbot/www:/var/www/certbot" \
    certbot/certbot certonly \
    --standalone \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --domains "$DOMAIN_NAME"

# Verificar que los certificados se generaron
if [ -f "nginx/ssl/live/$DOMAIN_NAME/fullchain.pem" ]; then
    log_success "Certificados SSL generados correctamente"
    
    # Copiar certificados a la ubicación correcta
    cp "nginx/ssl/live/$DOMAIN_NAME/fullchain.pem" nginx/ssl/fullchain.pem
    cp "nginx/ssl/live/$DOMAIN_NAME/privkey.pem" nginx/ssl/privkey.pem
    
    # Restaurar configuración original
    rm nginx/conf.d/letsencrypt-temp.conf
    
    # Reiniciar nginx
    docker-compose -f "$COMPOSE_FILE" start nginx
    
    log_success "Certificados SSL configurados correctamente"
    
else
    log_error "Error al generar certificados SSL"
    exit 1
fi

# Crear script de renovación automática
log_info "Configurando renovación automática..."

cat > scripts/renew-ssl.sh << 'EOF'
#!/bin/bash

# Script para renovar certificados SSL automáticamente
# Configurar en crontab: 0 3 * * * /path/to/cryptotrace/scripts/renew-ssl.sh

DOMAIN_NAME="${DOMAIN_NAME:-cryptotrace.idiaicox.com}"
COMPOSE_FILE="docker-compose.prod.yml"

# Intentar renovar certificados
docker run --rm \
    -v "./nginx/ssl:/etc/letsencrypt" \
    -v "./certbot/www:/var/www/certbot" \
    certbot/certbot renew \
    --webroot \
    --webroot-path=/var/www/certbot

# Si la renovación fue exitosa, recargar nginx
if [ $? -eq 0 ]; then
    # Copiar certificados renovados
    cp "nginx/ssl/live/$DOMAIN_NAME/fullchain.pem" nginx/ssl/fullchain.pem
    cp "nginx/ssl/live/$DOMAIN_NAME/privkey.pem" nginx/ssl/privkey.pem
    
    # Recargar nginx
    docker-compose -f "$COMPOSE_FILE" exec nginx nginx -s reload
    
    echo "$(date): Certificados SSL renovados correctamente" >> /var/log/letsencrypt-renew.log
else
    echo "$(date): Error al renovar certificados SSL" >> /var/log/letsencrypt-renew.log
fi
EOF

chmod +x scripts/renew-ssl.sh

log_success "Script de renovación creado: scripts/renew-ssl.sh"
log_info "Para configurar renovación automática, añade a crontab:"
log_info "0 3 * * * /ruta/completa/a/cryptotrace/scripts/renew-ssl.sh"

# Verificar que HTTPS funciona
log_info "Verificando configuración SSL..."
sleep 5

if curl -f -s -k "https://$DOMAIN_NAME/" > /dev/null; then
    log_success "¡SSL configurado correctamente! Tu aplicación está disponible en:"
    log_success "https://$DOMAIN_NAME"
else
    log_warning "Puede haber un problema con la configuración SSL"
    log_info "Verifica los logs: docker-compose -f $COMPOSE_FILE logs nginx"
fi

log_success "=== CONFIGURACIÓN SSL COMPLETADA ===" 