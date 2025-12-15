#!/bin/sh
# Script para iniciar el servidor de desarrollo
# En desarrollo, PUBLIC_URL="" hace que el servidor sirva desde la raíz
# En producción, PUBLIC_URL="/hps" o se usa homepage="/hps"

# Si PUBLIC_URL no está definido, establecerlo como cadena vacía para desarrollo
# Esto hace que react-scripts ignore el homepage="/hps" y sirva desde la raíz
export PUBLIC_URL="${PUBLIC_URL:-}"

# Iniciar el servidor de desarrollo
# El servidor de desarrollo de react-scripts usa PUBLIC_URL para determinar la base URL
exec react-scripts start

