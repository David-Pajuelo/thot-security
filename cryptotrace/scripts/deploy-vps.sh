#!/bin/bash
# Despliegue en VPS: actualizar código, backup DB, migraciones (0033→0036), rebuild y reinicio.
# Ejecutar desde el directorio cryptotrace en el VPS: /opt/thot-security/cryptotrace
# Uso: ./scripts/deploy-vps.sh
# O desde fuera: ssh root@187.33.154.156 'cd /opt/thot-security/cryptotrace && bash scripts/deploy-vps.sh'

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

COMPOSE="docker-compose -f docker-compose.prod.yml"
# Nombre de la BD en prod (por defecto en docker-compose.prod.yml)
DB_NAME="${DB_NAME:-cryptotrace_db}"
DB_USER="${DB_USER:-cryptotrace_user}"

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok()      { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err()     { echo -e "${RED}[ERROR]${NC} $1"; }

# Comprobar que estamos en el directorio cryptotrace (tiene docker-compose.prod.yml)
if [ ! -f "docker-compose.prod.yml" ]; then
  log_err "Ejecuta este script desde el directorio cryptotrace (donde está docker-compose.prod.yml)."
  exit 1
fi

log_info "=== 1/7 Actualizando código (development) ==="
git fetch origin
git checkout development
git pull origin development
log_ok "Código actualizado."

log_info "=== 2/7 Backup de la base de datos ==="
BACKUP_FILE="backup_pre_despliegue_$(date +%Y%m%d_%H%M%S).sql"
if $COMPOSE exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null; then
  log_ok "Backup guardado: $BACKUP_FILE"
else
  log_warn "Backup falló (¿contenedor db levantado?). Continuando sin backup."
  rm -f "$BACKUP_FILE"
fi

log_info "=== 3/7 Estado actual de migraciones (productos) ==="
$COMPOSE exec backend python manage.py showmigrations productos || true

log_info "=== 4/7 Aplicando migraciones (productos) ==="
$COMPOSE exec backend python manage.py migrate productos
log_ok "Migraciones aplicadas."

log_info "=== 5/7 Recolectando estáticos ==="
$COMPOSE exec backend python manage.py collectstatic --noinput
log_ok "Estáticos recolectados."

log_info "=== 6/7 Reconstruyendo imágenes (backend, frontend, ocr, processing, pdf-generator, celery) ==="
$COMPOSE build --no-cache backend frontend ocr processing pdf-generator celery-worker celery-beat
log_ok "Build completado."

log_info "=== 7/7 Reiniciando contenedores ==="
$COMPOSE up -d
log_ok "Contenedores levantados."

echo ""
log_ok "=== DESPLIEGUE COMPLETADO ==="
echo "  - Backend:  https://seguridad.idiaicox.com/cryptotrace/api/"
echo "  - Frontend: abrir en navegador y probar AC21 y cryptocustodios."
echo "  - Backup (si se generó): $BACKUP_FILE — guárdalo en lugar seguro."
