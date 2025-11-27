#!/bin/bash
# Script para verificar y corregir el rol 'jefe_seguridad_suplente' en el VPS

echo "🔍 Verificando y corrigiendo el rol 'jefe_seguridad_suplente'..."

# Opción 1: Usar el script Python
if [ -f "backend/verify_and_fix_role.py" ]; then
    echo "Ejecutando script Python..."
    cd /opt/hps-system
    docker compose -f docker-compose.prod.yml exec backend python /app/verify_and_fix_role.py
    exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo "✅ Script ejecutado exitosamente"
    else
        echo "❌ Error ejecutando el script"
    fi
    exit $exit_code
fi

# Opción 2: Ejecutar SQL directamente
echo "Ejecutando SQL directamente..."
docker compose -f docker-compose.prod.yml exec db psql -U hps_user -d hps_system -c "
SELECT id, name, description 
FROM roles 
WHERE name = 'jefe_seguridad_suplente';
"

# Si no existe, crearlo
echo "Verificando si necesita crearse..."
EXISTS=$(docker compose -f docker-compose.prod.yml exec -T db psql -U hps_user -d hps_system -t -c "
SELECT COUNT(*) 
FROM roles 
WHERE name = 'jefe_seguridad_suplente';
" | tr -d ' ')

if [ "$EXISTS" = "0" ]; then
    echo "⚠️ El rol no existe. Creándolo..."
    docker compose -f docker-compose.prod.yml exec db psql -U hps_user -d hps_system -c "
    INSERT INTO roles (name, description, created_at, updated_at) 
    VALUES 
    ('jefe_seguridad_suplente', 'Jefe de Seguridad Suplente', NOW(), NOW())
    ON CONFLICT (name) DO NOTHING;
    "
    echo "✅ Rol creado (o ya existía)"
else
    echo "✅ El rol ya existe"
fi

# Verificar nuevamente
echo ""
echo "📋 Listando todos los roles:"
docker compose -f docker-compose.prod.yml exec db psql -U hps_user -d hps_system -c "
SELECT id, name, description 
FROM roles 
ORDER BY name;
"

