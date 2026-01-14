#!/bin/bash

# Script para configurar el entorno de desarrollo local de CryptoTrace
# Este script crea los archivos .env necesarios basados en env.example

set -e

echo "🔧 Configurando entorno de desarrollo local para CryptoTrace..."

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directorio base
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${BASE_DIR}/cryptotrace-backend"

# 1. Crear .env para el backend si no existe
if [ ! -f "${BACKEND_DIR}/.env" ]; then
    echo -e "${YELLOW}📝 Creando ${BACKEND_DIR}/.env desde env.example...${NC}"
    cp "${BACKEND_DIR}/env.example" "${BACKEND_DIR}/.env"
    
    # Ajustar configuración de base de datos para desarrollo local (docker-compose.yml usa postgres/postgres)
    sed -i.bak 's/DATABASE_URL=postgres:\/\/cryptotrace_user:cryptotrace_pass@db:5432\/cryptotrace_db/DATABASE_URL=postgres:\/\/postgres:postgres@db:5432\/cryptotrace/' "${BACKEND_DIR}/.env"
    sed -i.bak 's/DB_NAME=cryptotrace_db/DB_NAME=cryptotrace/' "${BACKEND_DIR}/.env"
    sed -i.bak 's/DB_USER=cryptotrace_user/DB_USER=postgres/' "${BACKEND_DIR}/.env"
    sed -i.bak 's/DB_PASSWORD=cryptotrace_pass/DB_PASSWORD=postgres/' "${BACKEND_DIR}/.env"
    
    # Eliminar archivo de backup
    rm -f "${BACKEND_DIR}/.env.bak"
    
    echo -e "${GREEN}✅ Archivo .env creado${NC}"
    echo -e "${YELLOW}⚠️  IMPORTANTE: Edita ${BACKEND_DIR}/.env y configura:${NC}"
    echo "   - OPENAI_API_KEY (línea 63)"
    echo "   - SMTP_USER y SMTP_PASSWORD (si necesitas enviar emails)"
    echo "   - IMAP_USER e IMAP_PASSWORD (si necesitas recibir emails)"
else
    echo -e "${GREEN}✅ ${BACKEND_DIR}/.env ya existe${NC}"
fi

# 2. Verificar si OPENAI_API_KEY está configurada
if grep -q "OPENAI_API_KEY=sk-tu-openai-api-key-aqui" "${BACKEND_DIR}/.env" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY no está configurada (usa el valor por defecto)${NC}"
    echo "   Edita ${BACKEND_DIR}/.env y configura tu API key de OpenAI"
fi

# 3. Crear .env para processing si no existe
if [ ! -f "${BASE_DIR}/cryptotrace-processing/.env" ]; then
    echo -e "${YELLOW}📝 Creando ${BASE_DIR}/cryptotrace-processing/.env...${NC}"
    cat > "${BASE_DIR}/cryptotrace-processing/.env" << EOF
# Configuración para desarrollo local
DEBUG=True
EOF
    echo -e "${GREEN}✅ Archivo .env creado para processing${NC}"
fi

# 4. Crear .env para OCR si no existe
if [ ! -f "${BASE_DIR}/cryptotrace-ocr/.env" ]; then
    echo -e "${YELLOW}📝 Creando ${BASE_DIR}/cryptotrace-ocr/.env...${NC}"
    cat > "${BASE_DIR}/cryptotrace-ocr/.env" << EOF
# Configuración para desarrollo local
OPENAI_API_KEY=sk-tu-openai-api-key-aqui
EOF
    echo -e "${GREEN}✅ Archivo .env creado para OCR${NC}"
    echo -e "${YELLOW}⚠️  IMPORTANTE: Edita ${BASE_DIR}/cryptotrace-ocr/.env y configura OPENAI_API_KEY${NC}"
fi

echo ""
echo -e "${GREEN}✅ Configuración completada!${NC}"
echo ""
echo "📋 Próximos pasos:"
echo "   1. Edita ${BACKEND_DIR}/.env y configura OPENAI_API_KEY"
echo "   2. (Opcional) Configura SMTP_* e IMAP_* si necesitas emails"
echo "   3. Ejecuta: docker compose up -d"
echo "   4. Ejecuta las migraciones: docker compose exec backend python manage.py migrate"
echo "   5. Crea un superusuario: docker compose exec backend python manage.py createsuperuser"
echo ""
echo "🌐 URLs de desarrollo:"
echo "   - Backend API: http://localhost:8080/api"
echo "   - Frontend: http://localhost:3000"
echo "   - Processing: http://localhost:5001"
echo "   - OCR: http://localhost:8002"
echo ""

