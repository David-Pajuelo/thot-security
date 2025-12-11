#!/bin/bash

# =============================================================================
# Script de Configuración Inicial del VPS
# =============================================================================
# Este script configura el VPS desde cero
# Uso: ./configurar-vps-inicial.sh
# Ejecutar en el VPS como root

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Configuración Inicial del VPS                           ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Este script debe ejecutarse como root${NC}"
    echo "Usa: sudo ./configurar-vps-inicial.sh"
    exit 1
fi

# Paso 1: Verificar Sistema Operativo
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Paso 1: Verificando Sistema Operativo${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo -e "${GREEN}✓ Sistema operativo: $PRETTY_NAME${NC}"
else
    echo -e "${YELLOW}⚠️  No se pudo detectar el sistema operativo${NC}"
fi

echo ""
echo "Recursos del sistema:"
echo "  CPU: $(nproc) cores"
echo "  RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo "  Disco: $(df -h / | awk 'NR==2 {print $4}') disponibles"

# Paso 2: Actualizar Sistema
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Paso 2: Actualizando Sistema${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

if command -v apt &> /dev/null; then
    echo "Actualizando con apt..."
    apt update
    apt upgrade -y
    echo -e "${GREEN}✓ Sistema actualizado${NC}"
elif command -v yum &> /dev/null; then
    echo "Actualizando con yum..."
    yum update -y
    echo -e "${GREEN}✓ Sistema actualizado${NC}"
else
    echo -e "${YELLOW}⚠️  No se pudo detectar el gestor de paquetes${NC}"
fi

# Paso 3: Instalar Docker
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Paso 3: Instalando Docker${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker ya está instalado${NC}"
    docker --version
else
    echo "Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo -e "${GREEN}✓ Docker instalado${NC}"
    docker --version
fi

# Paso 4: Instalar Docker Compose
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Paso 4: Instalando Docker Compose${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose ya está instalado${NC}"
    docker-compose --version
else
    echo "Instalando Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✓ Docker Compose instalado${NC}"
    docker-compose --version
fi

# Paso 5: Configurar Firewall
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Paso 5: Configurando Firewall${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

if command -v ufw &> /dev/null; then
    echo "Configurando UFW..."
    ufw allow ssh
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Preguntar antes de habilitar
    read -p "¿Habilitar firewall ahora? (yes/no): " enable_firewall
    if [ "$enable_firewall" == "yes" ]; then
        ufw --force enable
        echo -e "${GREEN}✓ Firewall habilitado${NC}"
    else
        echo -e "${YELLOW}⚠️  Firewall no habilitado. Puedes habilitarlo después con: ufw enable${NC}"
    fi
    ufw status
else
    echo -e "${YELLOW}⚠️  UFW no está instalado${NC}"
    read -p "¿Instalar UFW? (yes/no): " install_ufw
    if [ "$install_ufw" == "yes" ]; then
        apt install ufw -y
        ufw allow ssh
        ufw allow 22/tcp
        ufw allow 80/tcp
        ufw allow 443/tcp
        read -p "¿Habilitar firewall ahora? (yes/no): " enable_firewall
        if [ "$enable_firewall" == "yes" ]; then
            ufw --force enable
        fi
        echo -e "${GREEN}✓ UFW instalado y configurado${NC}"
    fi
fi

# Paso 6: Preparar Directorios
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Paso 6: Preparando Directorios${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

mkdir -p /opt/thot-security
echo -e "${GREEN}✓ Directorio /opt/thot-security creado${NC}"

# Paso 7: Verificación Final
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Paso 7: Verificación Final${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

echo "Verificando instalaciones..."
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker: $(docker --version)${NC}"
else
    echo -e "${RED}❌ Docker no está instalado${NC}"
fi

if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose: $(docker-compose --version)${NC}"
else
    echo -e "${RED}❌ Docker Compose no está instalado${NC}"
fi

echo ""
echo -e "${GREEN}✅ Configuración inicial completada${NC}"
echo ""
echo "📝 Próximos pasos:"
echo "1. Clonar el repositorio: cd /opt && git clone -b production https://github.com/David-Pajuelo/thot-security.git"
echo "2. Configurar variables de entorno (.env.prod)"
echo "3. Desplegar las aplicaciones"
echo ""
echo "Para más información, consulta: GUIA-DESPLIEGUE-PRODUCCION-VPS.md"
echo ""

