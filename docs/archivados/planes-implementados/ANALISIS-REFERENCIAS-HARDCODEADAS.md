# Análisis de Referencias Hardcodeadas - Preparación para Producción

## 📋 Resumen Ejecutivo

Este documento identifica todas las referencias hardcodeadas a URLs, direcciones IP, puertos y configuraciones de desarrollo que deben ser parametrizadas para producción.

## 🔴 Referencias Críticas (Deben ser Variables de Entorno)

### 1. Extensiones Chrome
**Ubicación**: `hps-system/chrome-extensions/`
- ❌ **CRÍTICO**: `apiClient.js` - URL base hardcodeada
  - `hps-plugin-test/apiClient.js`: `http://localhost:8080/api/v1/extension`
  - `hps-plugin-prod/apiClient.js`: `http://localhost:8080/api/v1/extension`
- ❌ **CRÍTICO**: `manifest.json` - Permisos hardcodeados
  - `hps-plugin-test/manifest.json`: `http://localhost:8080/*`
  - `hps-plugin-prod/manifest.json`: `http://localhost:8080/*`

**Solución**: Las extensiones deben usar variables de entorno o configuración dinámica. Para producción, necesitamos crear versiones con URLs de producción.

### 2. Frontend React (HPS System)
**Ubicación**: `hps-system/frontend/`

#### Archivos con URLs hardcodeadas:
- ✅ `src/config/api.js` - Usa variables de entorno con fallback a localhost
- ✅ `src/services/websocketService.js` - Usa variables de entorno con fallback
- ✅ `src/pages/ChatMonitoringPage.jsx` - Usa variables de entorno con fallback
- ❌ `public/token-sync.html` - **HARDCODEADO**: `http://localhost:3000`
- ❌ `src/components/Dashboard.jsx` - Fallback hardcodeado: `http://localhost:3000`
- ❌ `src/utils/tokenSync.js` - Fallback hardcodeado: `http://localhost:3000`

### 3. Frontend Next.js (CryptoTrace)
**Ubicación**: `cryptotrace/cryptotrace-frontend/`

#### Archivos con URLs hardcodeadas:
- ✅ `src/components/ui/Layout.tsx` - Usa variables de entorno con fallback
- ✅ `src/utils/tokenSync.ts` - Usa variables de entorno con fallback
- ✅ `src/components/protectedRoute.tsx` - Usa variables de entorno con fallback
- ❌ `public/token-sync.html` - **HARDCODEADO**: `http://localhost:3001`

### 4. Backend Django
**Ubicación**: `cryptotrace/cryptotrace-backend/`

#### Archivos con URLs hardcodeadas:
- ✅ `src/cryptotrace_backend/settings.py` - Usa variables de entorno con fallbacks
  - Fallbacks: `http://localhost:3000`, `http://localhost:3001`
- ✅ `src/hps_agent/services/command_processor.py` - Usa variables de entorno
  - Fallback: `http://localhost:3001`
- ✅ `src/hps_core/email_service.py` - Usa variables de entorno
- ✅ `src/hps_core/email_templates.py` - Usa variables de entorno

**Problema**: Los fallbacks están hardcodeados a localhost. En producción deben fallar si no están definidas las variables.

### 5. Docker Compose
**Ubicación**: Varios archivos

#### `cryptotrace/docker-compose.yml` (Desarrollo)
- ✅ Usa variables de entorno en su mayoría
- ⚠️ Algunos valores por defecto hardcodeados

#### `cryptotrace/docker-compose.prod.yml` (Producción)
- ⚠️ Revisar que todas las URLs sean variables

#### `hps-system/docker-compose.dev.yml` (Desarrollo)
- ⚠️ Valores por defecto hardcodeados: `http://localhost:8080`

#### `hps-system/docker-compose.prod.yml` (Producción)
- ⚠️ Revisar configuración completa

## 📝 Referencias por Categoría

### A. URLs de Backend
| Ubicación | Tipo | Valor Actual | Debe Ser |
|-----------|------|--------------|----------|
| `hps-system/chrome-extensions/*/apiClient.js` | Hardcodeado | `http://localhost:8080` | Variable de entorno |
| `hps-system/frontend/src/config/api.js` | Fallback | `http://localhost:8080` | Sin fallback en prod |
| `hps-system/frontend/src/services/websocketService.js` | Fallback | `ws://localhost:8080` | Sin fallback en prod |
| `cryptotrace/cryptotrace-backend/src/hps_agent/services/command_processor.py` | Fallback | `http://localhost:3001` | Variable requerida |

### B. URLs de Frontend
| Ubicación | Tipo | Valor Actual | Debe Ser |
|-----------|------|--------------|----------|
| `cryptotrace/cryptotrace-frontend/public/token-sync.html` | Hardcodeado | `http://localhost:3001` | Variable de entorno |
| `hps-system/frontend/public/token-sync.html` | Hardcodeado | `http://localhost:3000` | Variable de entorno |
| `hps-system/frontend/src/utils/tokenSync.js` | Fallback | `http://localhost:3000` | Sin fallback en prod |
| `hps-system/frontend/src/components/Dashboard.jsx` | Fallback | `http://localhost:3000` | Sin fallback en prod |

### C. URLs de Servicios Internos (Docker)
| Ubicación | Tipo | Valor Actual | Debe Ser |
|-----------|------|--------------|----------|
| `cryptotrace/cryptotrace-backend/src/hps_agent/services/command_processor.py` | Fallback | `http://cryptotrace-backend:8080` | ✅ Correcto (interno) |
| `cryptotrace/cryptotrace-backend/src/cryptotrace_backend/settings.py` | Fallback | `localhost` (Redis) | Variable de entorno |

### D. CORS y ALLOWED_HOSTS
| Ubicación | Tipo | Valor Actual | Debe Ser |
|-----------|------|--------------|----------|
| `cryptotrace/cryptotrace-backend/src/cryptotrace_backend/settings.py` | Hardcodeado | `localhost,127.0.0.1` | Variable de entorno |
| `cryptotrace/cryptotrace-backend/env.example` | Ejemplo | `localhost,127.0.0.1` | Ejemplo de producción |

### E. Puertos Hardcodeados
| Ubicación | Tipo | Valor Actual | Nota |
|-----------|------|--------------|------|
| `docker-compose*.yml` | Mapeo de puertos | Varios | ✅ Normal en Docker Compose |
| Healthchecks | URLs | `http://localhost:PORT` | ⚠️ Deben usar nombres de servicio |

## 🔧 Archivos que Requieren Cambios

### Prioridad Alta (Críticos para Producción)

1. **Extensiones Chrome**
   - `hps-system/chrome-extensions/hps-plugin-prod/apiClient.js`
   - `hps-system/chrome-extensions/hps-plugin-prod/manifest.json`
   - **Solución**: Crear build script que inyecte URLs de producción

2. **Archivos HTML Estáticos**
   - `cryptotrace/cryptotrace-frontend/public/token-sync.html`
   - `hps-system/frontend/public/token-sync.html`
   - **Solución**: Usar variables de entorno en tiempo de build o inyectar en runtime

3. **Backend Django - Fallbacks**
   - `cryptotrace/cryptotrace-backend/src/cryptotrace_backend/settings.py`
   - **Solución**: Eliminar fallbacks a localhost en modo producción

### Prioridad Media

4. **Frontend React - Fallbacks**
   - `hps-system/frontend/src/config/api.js`
   - `hps-system/frontend/src/services/websocketService.js`
   - `hps-system/frontend/src/utils/tokenSync.js`
   - `hps-system/frontend/src/components/Dashboard.jsx`
   - **Solución**: Validar que variables de entorno estén definidas en producción

5. **Docker Compose**
   - Revisar todos los archivos `docker-compose.prod.yml`
   - Asegurar que no haya valores hardcodeados

## 📋 Variables de Entorno Necesarias

### Backend Django
```bash
# URLs Externas
FRONTEND_URL=https://cryptotrace.tudominio.com
HPS_SYSTEM_URL=https://hps.tudominio.com
NEXT_PUBLIC_HPS_SYSTEM_URL=https://hps.tudominio.com

# CORS y Seguridad
ALLOWED_HOSTS=cryptotrace.tudominio.com,hps.tudominio.com
CORS_ORIGINS=https://cryptotrace.tudominio.com,https://hps.tudominio.com

# Redis (interno)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0
```

### Frontend React (HPS System)
```bash
REACT_APP_API_URL=https://api.tudominio.com
REACT_APP_WS_URL=wss://api.tudominio.com
REACT_APP_AGENTE_IA_WS_URL=wss://api.tudominio.com/ws/chat
REACT_APP_CRYPTOTRACE_URL=https://cryptotrace.tudominio.com
```

### Frontend Next.js (CryptoTrace)
```bash
NEXT_PUBLIC_API_URL=https://api.tudominio.com/api
NEXT_PUBLIC_HPS_SYSTEM_URL=https://hps.tudominio.com
```

### Extensiones Chrome
**Nota**: Las extensiones no pueden usar variables de entorno directamente. Necesitan:
- Build script que reemplace URLs en tiempo de build
- O configuración dinámica desde un endpoint del backend

## 🚨 Problemas Especiales

### 1. Extensiones Chrome
Las extensiones de Chrome no pueden usar variables de entorno en runtime. Soluciones:
- **Opción A**: Build script que reemplace URLs antes de empaquetar
- **Opción B**: Endpoint de configuración en el backend que la extensión consulta al iniciar
- **Opción C**: Múltiples builds (dev, staging, prod)

### 2. Archivos HTML Estáticos
Los archivos HTML estáticos no pueden usar variables de entorno directamente. Soluciones:
- **Opción A**: Template engine en tiempo de build
- **Opción B**: Inyección de variables en runtime mediante JavaScript
- **Opción C**: Generar archivos HTML desde templates

### 3. Fallbacks a Localhost
En producción, los fallbacks a localhost deben eliminarse o hacer que la aplicación falle si las variables no están definidas.

## ✅ Checklist de Preparación para Producción

- [ ] Crear archivos `.env.prod` para todos los servicios
- [ ] Eliminar fallbacks a localhost en código de producción
- [ ] Configurar CORS con dominios de producción
- [ ] Configurar ALLOWED_HOSTS con dominios de producción
- [ ] Crear build script para extensiones Chrome
- [ ] Modificar archivos HTML estáticos para usar variables
- [ ] Revisar y actualizar docker-compose.prod.yml
- [ ] Documentar todas las variables de entorno necesarias
- [ ] Crear script de validación de variables de entorno
- [ ] Configurar SSL/TLS (HTTPS/WSS)

## 📝 Notas Adicionales

1. **Puertos en Docker**: Los puertos mapeados en docker-compose son normales, pero las URLs internas deben usar nombres de servicios.

2. **Healthchecks**: Los healthchecks en docker-compose usan `localhost` dentro del contenedor, lo cual es correcto.

3. **Documentación**: Muchos archivos `.md` contienen referencias a localhost, pero son solo documentación y no afectan el código.

4. **Archivos de Ejemplo**: Los archivos `*.example` pueden tener localhost como ejemplos, pero deben documentar valores de producción.

