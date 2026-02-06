#!/bin/bash

# =============================================================================
# Script de Despliegue - HPS System en Producción
# =============================================================================
# Uso: ./desplegar-hps-system.sh
# Ejecutar desde: /opt/thot-security/hps-system

set -e  # Salir si hay algún error

echo "🚀 Iniciando despliegue de HPS System en producción..."
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}❌ Error: No se encontró docker-compose.prod.yml${NC}"
    echo "Ejecuta este script desde /opt/thot-security/hps-system"
    exit 1
fi

# Verificar que existe .env.prod
if [ ! -f ".env.prod" ]; then
    echo -e "${YELLOW}⚠️  No se encontró .env.prod${NC}"
    echo "Creando desde env.prod.example..."
    if [ -f "env.prod.example" ]; then
        cp env.prod.example .env.prod
        echo -e "${YELLOW}⚠️  IMPORTANTE: Edita .env.prod con las credenciales correctas antes de continuar${NC}"
        exit 1
    else
        echo -e "${RED}❌ Error: No se encontró env.prod.example${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Verificaciones completadas${NC}"
echo ""

# Paso 1: Construir imágenes
echo "📦 Construyendo imágenes Docker..."
docker compose -f docker-compose.prod.yml --env-file .env.prod build
echo -e "${GREEN}✓ Imágenes construidas${NC}"
echo ""

# Paso 2: Detener contenedores existentes (si hay)
echo "🛑 Deteniendo contenedores existentes..."
docker compose -f docker-compose.prod.yml --env-file .env.prod down || true
echo -e "${GREEN}✓ Contenedores detenidos${NC}"
echo ""

# Paso 3: Levantar contenedores
echo "🚀 Levantando contenedores..."
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
echo -e "${GREEN}✓ Contenedores levantados${NC}"
echo ""

# Paso 4: Esperar a que los servicios estén listos
echo "⏳ Esperando a que los servicios estén listos..."
sleep 10

# Verificar estado de contenedores
echo "📊 Estado de los contenedores:"
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
echo ""

# Paso 5: Migraciones (HPS está en Django/cryptotrace-backend; no hay backend FastAPI)
echo "🗄️  Migraciones HPS: se ejecutan en cryptotrace-backend (Django). Si despliegas solo HPS frontend, asegúrate de que cryptotrace-backend esté al día."
echo ""

# Paso 6: Verificar salud del frontend
echo "🏥 Verificando salud del frontend..."
sleep 5

# Verificar frontend (puerto 80 dentro del contenedor; mapeado a 3001 en host según compose)
if curl -f http://localhost:3001 > /dev/null 2>&1 || curl -f http://127.0.0.1:3001 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend respondiendo correctamente${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend no responde aún, revisa los logs${NC}"
fi

echo ""
echo -e "${GREEN}✅ Despliegue de HPS System completado${NC}"
echo ""
echo "📝 Próximos pasos:"
echo "1. Verifica los logs: docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f"
echo "2. Configura Nginx para el dominio seguridad.idiaicox.com"
echo "3. Obtén el certificado SSL: certbot --nginx -d seguridad.idiaicox.com"
echo "4. Verifica el acceso: https://seguridad.idiaicox.com"
echo ""

