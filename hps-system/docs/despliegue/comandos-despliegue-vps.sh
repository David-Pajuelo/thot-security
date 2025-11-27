#!/bin/bash
# Script de despliegue para VPS - Sistema HPS
# Servidor: hps.aicoxidi.com (46.183.119.90)

echo "🚀 Iniciando despliegue del Sistema HPS en VPS..."

# =============================================================================
# PASO 1: PREPARACIÓN DEL SISTEMA
# =============================================================================

echo "📦 Paso 1: Actualizando sistema..."
apt update && apt upgrade -y
apt install -y git curl wget nano ufw

# =============================================================================
# PASO 2: CONFIGURACIÓN DE FIREWALL
# =============================================================================

echo "🔥 Paso 2: Configurando firewall..."
ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw status

# =============================================================================
# PASO 3: INSTALACIÓN DE DOCKER
# =============================================================================

echo "🐳 Paso 3: Instalando Docker..."

# Instalar dependencias
apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Agregar clave GPG de Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Agregar repositorio de Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verificar instalación
docker --version
docker compose version

# =============================================================================
# PASO 4: INSTALACIÓN DE NGINX
# =============================================================================

echo "🌐 Paso 4: Instalando Nginx..."
apt install -y nginx
systemctl enable nginx
systemctl start nginx
systemctl status nginx

# =============================================================================
# PASO 5: INSTALACIÓN DE CERTBOT
# =============================================================================

echo "🔒 Paso 5: Instalando Certbot..."
apt install -y certbot python3-certbot-nginx

# =============================================================================
# PASO 6: CLONAR REPOSITORIO
# =============================================================================

echo "📥 Paso 6: Clonando repositorio..."
mkdir -p /opt/hps-system
cd /opt
git clone https://github.com/calonsoaicox/hps-system.git hps-system
cd hps-system

echo "✅ Preparación del sistema completada!"
echo "📝 Próximos pasos:"
echo "   1. Configurar archivo .env con tus credenciales"
echo "   2. Construir y levantar contenedores"
echo "   3. Configurar Nginx y SSL"

