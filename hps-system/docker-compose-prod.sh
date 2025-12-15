#!/bin/bash

# =============================================================================
# Script Helper - Docker Compose con .env.prod
# =============================================================================
# Este script carga automáticamente .env.prod antes de ejecutar docker compose
# Uso: ./docker-compose-prod.sh [comando docker compose]
# Ejemplos:
#   ./docker-compose-prod.sh up -d frontend
#   ./docker-compose-prod.sh build frontend
#   ./docker-compose-prod.sh logs frontend

set -e

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ Error: No se encontró docker-compose.prod.yml"
    echo "Ejecuta este script desde /opt/thot-security/hps-system"
    exit 1
fi

# Verificar que existe .env.prod
if [ ! -f ".env.prod" ]; then
    echo "❌ Error: No se encontró .env.prod"
    echo "Crea el archivo .env.prod desde env.prod.example"
    exit 1
fi

# Ejecutar docker compose con --env-file .env.prod
docker compose -f docker-compose.prod.yml --env-file .env.prod "$@"

