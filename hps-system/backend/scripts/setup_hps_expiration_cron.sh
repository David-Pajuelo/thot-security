#!/bin/bash

# Script para configurar la verificación automática de HPS próximas a caducar
# Ejecuta la verificación todos los días a las 9:00 AM

echo "🔧 Configurando verificación automática de HPS próximas a caducar..."

# Directorio del proyecto
PROJECT_DIR="/app"
SCRIPT_PATH="$PROJECT_DIR/backend/src/commands/check_hps_expiration.py"

# Crear entrada de cron para ejecutar todos los días a las 9:00 AM
CRON_ENTRY="0 9 * * * cd $PROJECT_DIR && python $SCRIPT_PATH >> /var/log/hps_expiration_check.log 2>&1"

# Agregar al crontab
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron job configurado:"
echo "   📅 Frecuencia: Todos los días a las 9:00 AM"
echo "   📝 Log: /var/log/hps_expiration_check.log"
echo "   🔧 Comando: $CRON_ENTRY"

# Mostrar crontab actual
echo ""
echo "📋 Crontab actual:"
crontab -l

echo ""
echo "✅ Configuración completada"
echo "💡 Para verificar manualmente: python $SCRIPT_PATH --manual"
