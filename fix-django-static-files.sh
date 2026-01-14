#!/bin/bash
# Script para sincronizar archivos estáticos de Django desde el contenedor al host

echo "🔧 Sincronizando archivos estáticos de Django..."

# 1. Verificar que el contenedor esté corriendo
if ! docker ps | grep -q cryptotrace-backend; then
    echo "❌ Error: El contenedor cryptotrace-backend no está corriendo"
    exit 1
fi

# 2. Ejecutar collectstatic en el contenedor
echo "📦 Ejecutando collectstatic..."
cd /opt/thot-security/cryptotrace
docker compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput

# 3. Crear el directorio en el host si no existe
echo "📁 Creando directorio en el host..."
sudo mkdir -p /var/www/cryptotrace-static
sudo chown -R www-data:www-data /var/www/cryptotrace-static

# 4. Copiar archivos estáticos del contenedor al host
echo "📋 Copiando archivos estáticos del contenedor al host..."
sudo docker cp cryptotrace-backend:/app/staticfiles/. /var/www/cryptotrace-static/

# 5. Ajustar permisos
echo "🔐 Ajustando permisos..."
sudo chown -R www-data:www-data /var/www/cryptotrace-static
sudo chmod -R 755 /var/www/cryptotrace-static

# 6. Verificar que los archivos se copiaron correctamente
echo "✅ Verificando archivos copiados..."
if [ -d "/var/www/cryptotrace-static/admin" ]; then
    echo "✅ Archivos estáticos copiados correctamente"
    echo "📊 Archivos encontrados:"
    ls -la /var/www/cryptotrace-static/ | head -20
else
    echo "⚠️  Advertencia: No se encontraron archivos estáticos en /var/www/cryptotrace-static/"
fi

echo ""
echo "✅ Proceso completado. Los archivos estáticos de Django deberían estar disponibles ahora."

