#!/bin/bash

# =============================================================================
# Script de Despliegue Completo - Producción
# =============================================================================
# Este script automatiza todo el proceso de despliegue en el VPS
# Uso: ./desplegar-produccion-completo.sh [hps|cryptotrace|ambos]

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
VPS_IP="187.33.154.156"
VPS_USER="root"
VPS_PASSWORD="41c0x1d1!"
DOMAIN="seguridad.idiaicox.com"
PROJECT_DIR="/opt/thot-security"
REPO_URL="https://github.com/David-Pajuelo/thot-security.git"
BRANCH="production"

# Determinar qué desplegar
DEPLOY_TARGET="${1:-hps}"  # Por defecto solo HPS

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Script de Despliegue en Producción - VPS                ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📌 Información del VPS:${NC}"
echo "   IP: $VPS_IP"
echo "   Usuario: $VPS_USER"
echo "   Dominio: $DOMAIN"
echo "   Desplegar: $DEPLOY_TARGET"
echo ""

# Función para ejecutar comandos en el VPS
execute_on_vps() {
    sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "$1"
}

# Función para copiar archivos al VPS
copy_to_vps() {
    sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no "$1" "$VPS_USER@$VPS_IP:$2"
}

echo -e "${YELLOW}⚠️  Este script ejecutará comandos en el VPS remoto${NC}"
read -p "¿Continuar? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Operación cancelada."
    exit 0
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Paso 1: Verificar conexión al VPS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

if execute_on_vps "echo 'Conexión exitosa'" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Conexión al VPS establecida${NC}"
else
    echo -e "${RED}❌ Error: No se pudo conectar al VPS${NC}"
    echo "Verifica:"
    echo "  - Que el VPS esté accesible"
    echo "  - Que SSH esté habilitado"
    echo "  - Que las credenciales sean correctas"
    exit 1
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Paso 2: Verificar Docker y Docker Compose${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

if execute_on_vps "docker --version && docker compose --version" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker y Docker Compose instalados${NC}"
    execute_on_vps "docker --version"
    execute_on_vps "docker compose --version"
else
    echo -e "${YELLOW}⚠️  Docker no está instalado. Instalando...${NC}"
    execute_on_vps "curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
    execute_on_vps "curl -L 'https://github.com/docker/compose/releases/latest/download/docker compose-$(uname -s)-$(uname -m)' -o /usr/local/bin/docker compose && chmod +x /usr/local/bin/docker compose"
    echo -e "${GREEN}✓ Docker instalado${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Paso 3: Preparar directorio del proyecto${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

# Crear directorio si no existe
execute_on_vps "mkdir -p $PROJECT_DIR"

# Verificar si el repositorio ya está clonado
if execute_on_vps "test -d $PROJECT_DIR/.git" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Repositorio ya existe, actualizando...${NC}"
    execute_on_vps "cd $PROJECT_DIR && git fetch origin && git checkout $BRANCH && git pull origin $BRANCH"
else
    echo -e "${YELLOW}⚠️  Clonando repositorio...${NC}"
    execute_on_vps "cd /opt && git clone -b $BRANCH $REPO_URL thot-security || (rm -rf thot-security && git clone -b $BRANCH $REPO_URL thot-security)"
    echo -e "${GREEN}✓ Repositorio clonado${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Paso 4: Copiar scripts de despliegue${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

# Copiar scripts al VPS
if [ -f "scripts/desplegar-hps-system.sh" ]; then
    copy_to_vps "scripts/desplegar-hps-system.sh" "$PROJECT_DIR/hps-system/desplegar-hps-system.sh"
    execute_on_vps "chmod +x $PROJECT_DIR/hps-system/desplegar-hps-system.sh"
    echo -e "${GREEN}✓ Script de HPS System copiado${NC}"
fi

if [ -f "scripts/desplegar-cryptotrace.sh" ]; then
    copy_to_vps "scripts/desplegar-cryptotrace.sh" "$PROJECT_DIR/cryptotrace/desplegar-cryptotrace.sh"
    execute_on_vps "chmod +x $PROJECT_DIR/cryptotrace/desplegar-cryptotrace.sh"
    echo -e "${GREEN}✓ Script de CryptoTrace copiado${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Paso 5: Desplegar aplicaciones${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

if [ "$DEPLOY_TARGET" == "hps" ] || [ "$DEPLOY_TARGET" == "ambos" ]; then
    echo ""
    echo -e "${YELLOW}🚀 Desplegando HPS System...${NC}"
    execute_on_vps "cd $PROJECT_DIR/hps-system && ./desplegar-hps-system.sh"
    echo -e "${GREEN}✓ HPS System desplegado${NC}"
fi

if [ "$DEPLOY_TARGET" == "cryptotrace" ] || [ "$DEPLOY_TARGET" == "ambos" ]; then
    echo ""
    echo -e "${YELLOW}🚀 Desplegando CryptoTrace...${NC}"
    execute_on_vps "cd $PROJECT_DIR/cryptotrace && ./desplegar-cryptotrace.sh"
    echo -e "${GREEN}✓ CryptoTrace desplegado${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Despliegue completado${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "📝 Próximos pasos manuales:"
echo "1. Configurar variables de entorno (.env.prod) en el VPS"
echo "2. Configurar Nginx para el dominio $DOMAIN"
echo "3. Obtener certificado SSL: certbot --nginx -d $DOMAIN"
echo "4. Verificar acceso: https://$DOMAIN"
echo ""
echo "Para ver los logs:"
echo "  ssh $VPS_USER@$VPS_IP"
echo "  cd $PROJECT_DIR/hps-system && docker compose -f docker compose.prod.yml logs -f"
echo ""

