#!/bin/bash

# Script para build del frontend Next.js para producción
# Genera archivos estáticos optimizados

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Variables
FRONTEND_DIR="cryptotrace-frontend"
DIST_DIR="$FRONTEND_DIR/dist"
BUILD_DIR="$FRONTEND_DIR/.next"

log_info "=== INICIANDO BUILD DEL FRONTEND ==="

# Verificar que existe el directorio del frontend
if [ ! -d "$FRONTEND_DIR" ]; then
    log_error "Directorio del frontend no encontrado: $FRONTEND_DIR"
    exit 1
fi

# Ir al directorio del frontend
cd "$FRONTEND_DIR"

# Verificar que Node.js está instalado
if ! command -v node &> /dev/null; then
    log_error "Node.js no está instalado"
    exit 1
fi

# Verificar que npm está instalado
if ! command -v npm &> /dev/null; then
    log_error "npm no está instalado"
    exit 1
fi

log_info "Versión de Node.js: $(node --version)"
log_info "Versión de npm: $(npm --version)"

# Limpiar builds anteriores
log_info "Limpiando builds anteriores..."
rm -rf .next
rm -rf dist
rm -rf out

# Instalar dependencias
log_info "Instalando dependencias..."
npm ci --production=false

# Configurar variables de entorno para build
log_info "Configurando variables de entorno para producción..."
export NODE_ENV=production
export NEXT_PUBLIC_API_URL=https://cryptotrace.idiaicox.com/api
export NEXT_PUBLIC_PROCESSING_URL=https://cryptotrace.idiaicox.com/processing
export NEXT_PUBLIC_OCR_URL=https://cryptotrace.idiaicox.com/ocr

# Realizar build de producción
log_info "Realizando build de producción..."
npm run build

# Verificar que el build fue exitoso
if [ ! -d ".next" ]; then
    log_error "Error en el build de Next.js"
    exit 1
fi

# Crear directorio de distribución
log_info "Preparando archivos para distribución..."
mkdir -p dist

# Verificar si Next.js está configurado para export estático
if [ -f ".next/export" ] || [ -d "out" ]; then
    log_info "Usando export estático de Next.js..."
    cp -r out/* dist/
else
    log_info "Copiando build de Next.js..."
    # Copiar archivos del build
    cp -r .next/static dist/_next/
    
    # Si existe standalone, usarlo
    if [ -d ".next/standalone" ]; then
        log_info "Usando build standalone..."
        cp -r .next/standalone/* dist/
    fi
    
    # Copiar archivos públicos
    if [ -d "public" ]; then
        cp -r public/* dist/
    fi
fi

# Crear archivo index.html si no existe (para SPAs)
if [ ! -f "dist/index.html" ]; then
    log_warning "No se encontró index.html, creando uno básico..."
    cat > dist/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>CryptoTrace</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
    <div id="__next"></div>
    <script src="/_next/static/chunks/main.js"></script>
</body>
</html>
EOF
fi

# Verificar que los archivos se copiaron correctamente
if [ ! -d "dist" ] || [ -z "$(ls -A dist)" ]; then
    log_error "Error al crear archivos de distribución"
    exit 1
fi

# Mostrar tamaño del build
DIST_SIZE=$(du -sh dist | cut -f1)
log_success "Build completado. Tamaño: $DIST_SIZE"

# Mostrar estructura básica
log_info "Estructura del build:"
ls -la dist/ | head -10

# Volver al directorio raíz
cd ..

log_success "=== BUILD DEL FRONTEND COMPLETADO ==="
log_info "Archivos listos en: $DIST_DIR"
log_info "Estos archivos serán servidos por Nginx en producción" 