#!/bin/sh
# Script para iniciar el servidor de desarrollo
# En desarrollo, necesitamos que el servidor sirva desde la raíz (sin /hps)
# En producción, se usa homepage="/hps"

# Si PUBLIC_URL está vacío o no definido, modificar temporalmente package.json
# para eliminar el homepage y que el servidor sirva desde la raíz
if [ -z "$PUBLIC_URL" ] || [ "$PUBLIC_URL" = "" ]; then
  # Crear backup del package.json
  cp package.json package.json.bak
  
  # Modificar package.json para eliminar homepage temporalmente
  # Usar node para modificar el JSON de forma segura
  node -e "
    const fs = require('fs');
    const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    delete pkg.homepage;
    fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2));
  "
  
  # Función para restaurar package.json al salir
  trap 'mv package.json.bak package.json' EXIT INT TERM
fi

# Establecer PUBLIC_URL si no está definido
export PUBLIC_URL="${PUBLIC_URL:-}"

# Iniciar el servidor de desarrollo
exec npx react-scripts start

