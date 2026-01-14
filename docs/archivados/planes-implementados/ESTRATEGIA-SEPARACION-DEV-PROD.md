# Estrategia de Separación Dev/Prod - Sin Hardcodeos

## 🎯 Objetivo

Tener entornos completamente separados (dev y prod) donde **TODAS** las direcciones vengan de variables de entorno y docker-compose, evitando hardcodeos que compliquen los push y la gestión.

## 📋 Principios Fundamentales

### 1. **Código Único, Configuración Múltiple**
- ✅ El mismo código funciona en dev y prod
- ✅ Solo cambian las variables de entorno
- ✅ No hay código específico por entorno en el repositorio

### 2. **Variables de Entorno Obligatorias**
- ❌ **NO** fallbacks a localhost en producción
- ✅ Validación de variables requeridas al iniciar
- ✅ Fallbacks solo en desarrollo (y documentados)

### 3. **Docker Compose como Fuente de Verdad**
- ✅ Todas las URLs vienen de variables en docker-compose
- ✅ Docker-compose inyecta variables al código
- ✅ No hay valores hardcodeados en docker-compose

## 🔧 Estrategia por Tipo de Archivo

### A. Backend Django

#### Problema Actual:
```python
# ❌ MAL - Fallback hardcodeado
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
```

#### Solución Recomendada:
```python
# ✅ BIEN - Sin fallback en producción
FRONTEND_URL = os.getenv('FRONTEND_URL')
if not FRONTEND_URL:
    if DEBUG:
        FRONTEND_URL = 'http://localhost:3000'  # Solo en dev
    else:
        raise ValueError("FRONTEND_URL debe estar definida en producción")
```

**Alternativa más limpia** (usar settings separados):
```python
# settings.py (base)
FRONTEND_URL = os.getenv('FRONTEND_URL')

# settings_dev.py
if not FRONTEND_URL:
    FRONTEND_URL = 'http://localhost:3000'  # Fallback solo en dev

# settings_prod.py
if not FRONTEND_URL:
    raise ValueError("FRONTEND_URL es requerida en producción")
```

### B. Frontend React (HPS System)

#### Problema Actual:
```javascript
// ❌ MAL - Fallback hardcodeado
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';
```

#### Solución Recomendada:
```javascript
// ✅ BIEN - Validación en tiempo de build
const API_BASE_URL = process.env.REACT_APP_API_URL;
if (!API_BASE_URL) {
  if (process.env.NODE_ENV === 'development') {
    console.warn('⚠️ REACT_APP_API_URL no definida, usando localhost');
    // Fallback solo en desarrollo
  } else {
    throw new Error('REACT_APP_API_URL debe estar definida en producción');
  }
}
```

**Mejor aún** - Validar en docker-compose:
```yaml
# docker-compose.prod.yml
frontend:
  build:
    args:
      - REACT_APP_API_URL=${REACT_APP_API_URL}  # Sin fallback
  environment:
    - REACT_APP_API_URL=${REACT_APP_API_URL}
```

### C. Frontend Next.js (CryptoTrace)

#### Problema Actual:
```typescript
// ❌ MAL - Fallback hardcodeado
const HPS_SYSTEM_URL = process.env.NEXT_PUBLIC_HPS_SYSTEM_URL || 'http://localhost:3001';
```

#### Solución Recomendada:
```typescript
// ✅ BIEN - Validación
const HPS_SYSTEM_URL = process.env.NEXT_PUBLIC_HPS_SYSTEM_URL;
if (!HPS_SYSTEM_URL && process.env.NODE_ENV === 'production') {
  throw new Error('NEXT_PUBLIC_HPS_SYSTEM_URL debe estar definida');
}
```

### D. Archivos HTML Estáticos

#### Problema Actual:
```html
<!-- ❌ MAL - Hardcodeado -->
<script>
  const hpsSystemUrl = 'http://localhost:3001';
</script>
```

#### Solución Recomendada (Opción 1 - Inyección en Build):
```html
<!-- ✅ BIEN - Template con placeholder -->
<script>
  const hpsSystemUrl = '__HPS_SYSTEM_URL__';
</script>
```

**Build script**:
```bash
# build.sh
sed -i "s|__HPS_SYSTEM_URL__|${HPS_SYSTEM_URL}|g" public/token-sync.html
```

#### Solución Recomendada (Opción 2 - Runtime):
```html
<!-- ✅ BIEN - Cargar desde window.config -->
<script>
  // Configuración inyectada por el servidor
  const config = window.__APP_CONFIG__ || {};
  const hpsSystemUrl = config.HPS_SYSTEM_URL || 
    (process.env.NODE_ENV === 'development' ? 'http://localhost:3001' : null);
  
  if (!hpsSystemUrl && process.env.NODE_ENV === 'production') {
    console.error('HPS_SYSTEM_URL no configurada');
  }
</script>
```

### E. Extensiones Chrome

#### Problema Actual:
```javascript
// ❌ MAL - Hardcodeado
const API_BASE_URL = 'http://localhost:8080/api/v1/extension';
```

#### Solución Recomendada (Build Script):
```javascript
// ✅ BIEN - Template con placeholder
const API_BASE_URL = '__API_BASE_URL__';
```

**Build script** (`build-extension.sh`):
```bash
#!/bin/bash
ENV=${1:-dev}  # dev o prod
EXTENSION_DIR="hps-plugin-${ENV}"

# Cargar variables según entorno
if [ "$ENV" = "prod" ]; then
  source .env.prod
  API_URL="${API_BASE_URL}/api/v1/extension"
else
  source .env.dev
  API_URL="http://localhost:8080/api/v1/extension"
fi

# Reemplazar en archivos
sed -i "s|__API_BASE_URL__|${API_URL}|g" "${EXTENSION_DIR}/apiClient.js"
sed -i "s|__API_HOST__|${API_HOST}|g" "${EXTENSION_DIR}/manifest.json"

echo "✅ Extensión ${ENV} construida con URL: ${API_URL}"
```

## 📁 Estructura de Archivos Recomendada

```
proyecto/
├── .env.dev                    # ❌ NO en git (gitignored)
├── .env.prod                   # ❌ NO en git (gitignored)
├── .env.dev.example            # ✅ En git (template)
├── .env.prod.example           # ✅ En git (template)
├── docker-compose.dev.yml      # ✅ En git
├── docker-compose.prod.yml     # ✅ En git
├── scripts/
│   ├── build-extension.sh     # Build extensiones
│   ├── validate-env.sh         # Validar variables
│   └── inject-html-vars.sh    # Inyectar en HTML
└── [código fuente]
```

## 🔄 Flujo de Trabajo Recomendado

### Desarrollo Local:
```bash
# 1. Copiar template
cp .env.dev.example .env.dev

# 2. Editar con valores locales
nano .env.dev

# 3. Levantar servicios
docker-compose -f docker-compose.dev.yml --env-file .env.dev up
```

### Producción (VPS):
```bash
# 1. Copiar template
cp .env.prod.example .env.prod

# 2. Editar con valores de producción
nano .env.prod

# 3. Validar variables
./scripts/validate-env.sh .env.prod

# 4. Levantar servicios
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

## ✅ Checklist de Implementación

### Fase 1: Eliminar Hardcodeos Críticos
- [ ] Backend Django: Eliminar fallbacks a localhost
- [ ] Frontend React: Validar variables en build
- [ ] Frontend Next.js: Validar variables en build
- [ ] Archivos HTML: Implementar inyección de variables
- [ ] Extensiones Chrome: Crear build script

### Fase 2: Configuración Docker Compose
- [ ] Actualizar docker-compose.dev.yml (usar .env.dev)
- [ ] Actualizar docker-compose.prod.yml (usar .env.prod)
- [ ] Asegurar que todas las URLs vengan de variables
- [ ] Documentar todas las variables necesarias

### Fase 3: Scripts de Validación
- [ ] Script de validación de variables (.env)
- [ ] Script de build de extensiones
- [ ] Script de inyección en HTML
- [ ] Script de verificación pre-deploy

### Fase 4: Documentación
- [ ] Documentar todas las variables de entorno
- [ ] Crear guía de setup para dev
- [ ] Crear guía de setup para prod
- [ ] Documentar proceso de build

## 🚨 Reglas de Oro

### 1. **Nunca Hardcodear URLs en Código**
```javascript
// ❌ NUNCA
const API_URL = 'http://localhost:8080';

// ✅ SIEMPRE
const API_URL = process.env.REACT_APP_API_URL;
```

### 2. **Fallbacks Solo en Desarrollo**
```python
# ❌ NUNCA en producción
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# ✅ BIEN
FRONTEND_URL = os.getenv('FRONTEND_URL')
if not FRONTEND_URL and DEBUG:
    FRONTEND_URL = 'http://localhost:3000'
elif not FRONTEND_URL:
    raise ValueError("FRONTEND_URL requerida")
```

### 3. **Validar en Docker Compose**
```yaml
# ✅ BIEN - Validar que existe
frontend:
  environment:
    - REACT_APP_API_URL=${REACT_APP_API_URL:?REACT_APP_API_URL no definida}
```

### 4. **Separar Settings por Entorno**
```python
# settings.py - Base común
# settings_dev.py - Con fallbacks
# settings_prod.py - Sin fallbacks, validación estricta
```

## 📝 Ejemplo de .env.dev.example

```bash
# URLs (Desarrollo)
FRONTEND_URL=http://localhost:3000
HPS_SYSTEM_URL=http://localhost:3001
REACT_APP_API_URL=http://localhost:8080
REACT_APP_WS_URL=ws://localhost:8080
REACT_APP_AGENTE_IA_WS_URL=ws://localhost:8080/ws/chat

# CORS (Desarrollo)
ALLOWED_HOSTS=localhost,127.0.0.1,backend
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

## 📝 Ejemplo de .env.prod.example

```bash
# URLs (Producción) - SIN FALLBACKS
FRONTEND_URL=https://cryptotrace.tudominio.com
HPS_SYSTEM_URL=https://hps.tudominio.com
REACT_APP_API_URL=https://api.tudominio.com
REACT_APP_WS_URL=wss://api.tudominio.com
REACT_APP_AGENTE_IA_WS_URL=wss://api.tudominio.com/ws/chat

# CORS (Producción)
ALLOWED_HOSTS=cryptotrace.tudominio.com,hps.tudominio.com,api.tudominio.com
CORS_ORIGINS=https://cryptotrace.tudominio.com,https://hps.tudominio.com
```

## 🎯 Recomendación Final

**Estrategia en 3 Pasos:**

1. **Inmediato**: Eliminar todos los fallbacks a localhost del código base
2. **Corto Plazo**: Crear scripts de build/validación para extensiones y HTML
3. **Medio Plazo**: Implementar settings separados (dev/prod) en Django

**Ventajas:**
- ✅ Código limpio sin hardcodeos
- ✅ Fácil cambio entre entornos
- ✅ Menos errores en producción
- ✅ Push sin preocupaciones de entornos

**Desventajas (mitigables):**
- ⚠️ Requiere validación de variables (script)
- ⚠️ Build scripts adicionales (pero automatizables)
- ⚠️ Más configuración inicial (pero documentada)

## 🔍 Casos Especiales

### Extensiones Chrome
**Problema**: No pueden usar variables de entorno en runtime.

**Solución**: Build script que genere versiones dev/prod desde templates.

### Archivos HTML Estáticos
**Problema**: No pueden usar variables de entorno directamente.

**Solución**: Inyección en tiempo de build o carga dinámica desde JavaScript.

### Healthchecks en Docker
**Nota**: Los healthchecks usan `localhost` dentro del contenedor, lo cual es **correcto** y no debe cambiarse.

