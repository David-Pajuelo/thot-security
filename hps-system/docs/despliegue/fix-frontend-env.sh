#!/bin/bash
# Script para verificar y corregir variables de entorno del frontend

cd /opt/hps-system

echo "Verificando archivo .env..."
cat .env | grep REACT_APP

echo ""
echo "Verificando cómo Docker Compose lee las variables..."
docker compose config | grep REACT_APP

echo ""
echo "Si las variables no se leen, intenta:"
echo "1. Verificar que el .env está en el mismo directorio que docker-compose.yml"
echo "2. Verificar que no hay espacios alrededor del signo ="
echo "3. Verificar que no hay comillas en los valores"

