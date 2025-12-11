#!/bin/bash

# =============================================================================
# Script de Despliegue - CryptoTrace en Producción
# =============================================================================
# Uso: ./desplegar-cryptotrace.sh
# Ejecutar desde: /opt/thot-security/cryptotrace

set -e  # Salir si hay algún error

echo "🚀 Iniciando despliegue de CryptoTrace en producción..."
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}❌ Error: No se encontró docker-compose.prod.yml${NC}"
    echo "Ejecuta este script desde /opt/thot-security/cryptotrace"
    exit 1
fi

# Verificar que existe .env.prod en backend
if [ ! -f "cryptotrace-backend/.env.prod" ]; then
    echo -e "${YELLOW}⚠️  No se encontró cryptotrace-backend/.env.prod${NC}"
    echo "Creando desde env.example..."
    if [ -f "cryptotrace-backend/env.example" ]; then
        cp cryptotrace-backend/env.example cryptotrace-backend/.env.prod
        echo -e "${YELLOW}⚠️  IMPORTANTE: Edita cryptotrace-backend/.env.prod con las credenciales correctas antes de continuar${NC}"
        exit 1
    else
        echo -e "${RED}❌ Error: No se encontró cryptotrace-backend/env.example${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Verificaciones completadas${NC}"
echo ""

# Paso 1: Construir imágenes
echo "📦 Construyendo imágenes Docker..."
docker-compose -f docker-compose.prod.yml build
echo -e "${GREEN}✓ Imágenes construidas${NC}"
echo ""

# Paso 2: Detener contenedores existentes (si hay)
echo "🛑 Deteniendo contenedores existentes..."
docker-compose -f docker-compose.prod.yml down || true
echo -e "${GREEN}✓ Contenedores detenidos${NC}"
echo ""

# Paso 3: Levantar contenedores
echo "🚀 Levantando contenedores..."
docker-compose -f docker-compose.prod.yml up -d
echo -e "${GREEN}✓ Contenedores levantados${NC}"
echo ""

# Paso 4: Esperar a que los servicios estén listos
echo "⏳ Esperando a que los servicios estén listos..."
sleep 15

# Verificar estado de contenedores
echo "📊 Estado de los contenedores:"
docker-compose -f docker-compose.prod.yml ps
echo ""

# Paso 5: Ejecutar migraciones
echo "🗄️  Ejecutando migraciones de base de datos..."
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py migrate
echo -e "${GREEN}✓ Migraciones ejecutadas${NC}"
echo ""

# Paso 6: Recolectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput
echo -e "${GREEN}✓ Archivos estáticos recolectados${NC}"
echo ""

# Paso 7: Verificar salud de los servicios
echo "🏥 Verificando salud de los servicios..."
sleep 5

# Verificar backend
if curl -f http://localhost:8080/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend respondiendo correctamente${NC}"
else
    echo -e "${YELLOW}⚠️  Backend no responde aún, revisa los logs${NC}"
fi

# Verificar frontend
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend respondiendo correctamente${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend no responde aún, revisa los logs${NC}"
fi

echo ""
echo -e "${GREEN}✅ Despliegue de CryptoTrace completado${NC}"
echo ""
echo "📝 Próximos pasos:"
echo "1. Verifica los logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "2. Crea superusuario (si es necesario): docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser"
echo "3. Configura Nginx para el dominio seguridad.idiaicox.com"
echo "4. Obtén el certificado SSL: certbot --nginx -d seguridad.idiaicox.com"
echo "5. Verifica el acceso: https://seguridad.idiaicox.com"
echo ""

