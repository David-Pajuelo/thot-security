# Resumen de Implementación: Separación Dev/Prod

## ✅ Cambios Implementados

### 1. Backend Django

#### Settings Separados
- **`settings.py`**: Configuración base sin fallbacks a localhost
- **`settings_dev.py`**: Extiende settings.py con fallbacks para desarrollo local
- **`settings_prod.py`**: Extiende settings.py con validación estricta (sin fallbacks)

#### Variables Requeridas en Producción
- `SECRET_KEY` - Clave secreta de Django
- `FRONTEND_URL` - URL del frontend CryptoTrace
- `HPS_SYSTEM_URL` - URL del sistema HPS
- `ALLOWED_HOSTS` - Hosts permitidos (separados por comas)
- `CORS_ALLOWED_ORIGINS` - Orígenes CORS permitidos (separados por comas)
- `REDIS_HOST` - Host de Redis
- `REDIS_URL` - URL completa de Redis

#### Eliminación de Fallbacks
- `command_processor.py`: Eliminado fallback a `http://localhost:3001`
- `email_service.py`: Eliminado fallback a `http://localhost:3001`
- `email_templates.py`: Eliminado fallback a `http://localhost:3000`

### 2. Frontend React (HPS System)

#### Validación de Variables
- **`config/api.js`**: Valida `REACT_APP_API_URL` y `REACT_APP_AGENTE_IA_WS_URL`
- **`services/websocketService.js`**: Valida `REACT_APP_AGENTE_IA_WS_URL` y `REACT_APP_API_URL`
- **`utils/tokenSync.js`**: Valida `REACT_APP_CRYPTOTRACE_URL`
- **`components/Dashboard.jsx`**: Valida `REACT_APP_CRYPTOTRACE_URL`
- **`pages/ChatMonitoringPage.jsx`**: Valida `REACT_APP_API_URL`

#### Comportamiento
- **Desarrollo**: Muestra warnings y usa fallbacks a localhost
- **Producción**: Lanza errores si las variables no están definidas

### 3. Frontend Next.js (CryptoTrace)

#### Validación de Variables
- **`utils/tokenSync.ts`**: Valida `NEXT_PUBLIC_HPS_SYSTEM_URL`
- **`components/ui/Layout.tsx`**: Valida `NEXT_PUBLIC_HPS_SYSTEM_URL`
- **`components/protectedRoute.tsx`**: Valida `NEXT_PUBLIC_HPS_SYSTEM_URL`

#### Comportamiento
- **Desarrollo**: Muestra warnings y usa fallbacks a localhost
- **Producción**: Muestra errores en consola si las variables no están definidas

### 4. Archivos HTML Estáticos

#### Placeholders
- **`hps-system/frontend/public/token-sync.html`**: Usa `__CRYPTOTRACE_URL__`
- **`cryptotrace/cryptotrace-frontend/public/token-sync.html`**: Usa `__HPS_SYSTEM_URL__`

#### Scripts de Build
- **`hps-system/frontend/scripts/inject-env-html.js`**: Reemplaza placeholders en build
- **`cryptotrace/cryptotrace-frontend/scripts/inject-env-html.js`**: Reemplaza placeholders en build
- **`package.json`**: Añadido `prebuild` script que ejecuta la inyección

### 5. Docker Compose

Los archivos docker-compose ya usan variables de entorno con `${VAR}`. En producción, se recomienda usar validación estricta con `${VAR:?error}` para fallar si falta una variable.

## 📋 Variables de Entorno Requeridas

### Backend Django (Producción)
```bash
SECRET_KEY=...
FRONTEND_URL=https://cryptotrace.idiaicox.com
HPS_SYSTEM_URL=https://hps.idiaicox.com
ALLOWED_HOSTS=cryptotrace.idiaicox.com,www.cryptotrace.idiaicox.com
CORS_ALLOWED_ORIGINS=https://cryptotrace.idiaicox.com,https://hps.idiaicox.com
REDIS_HOST=redis
REDIS_URL=redis://redis:6379/0
```

### Frontend React (Producción)
```bash
REACT_APP_API_URL=https://api.idiaicox.com
REACT_APP_AGENTE_IA_WS_URL=wss://api.idiaicox.com
REACT_APP_CRYPTOTRACE_URL=https://cryptotrace.idiaicox.com
```

### Frontend Next.js (Producción)
```bash
NEXT_PUBLIC_HPS_SYSTEM_URL=https://hps.idiaicox.com
NEXT_PUBLIC_API_URL=https://api.idiaicox.com
```

## 🔧 Uso

### Desarrollo
```bash
# Backend Django usa settings_dev.py automáticamente si DEBUG=True
# Frontends muestran warnings pero funcionan con fallbacks
```

### Producción
```bash
# Backend Django debe usar settings_prod.py
export DJANGO_SETTINGS_MODULE=cryptotrace_backend.settings_prod

# Todas las variables deben estar definidas
# El sistema fallará al iniciar si faltan variables requeridas
```

## ⚠️ Notas Importantes

1. **Settings Django**: En producción, usar `DJANGO_SETTINGS_MODULE=cryptotrace_backend.settings_prod`
2. **Validación**: `settings_prod.py` valida variables requeridas y falla si faltan
3. **Build Scripts**: Los scripts de inyección se ejecutan automáticamente antes de `npm run build`
4. **Fallbacks**: Solo en desarrollo. En producción, todas las variables deben estar definidas.

## 🚀 Próximos Pasos

1. Crear archivos `.env.prod` para producción
2. Actualizar docker-compose.prod.yml para usar validación estricta
3. Documentar proceso de despliegue en VPS
4. Crear scripts de validación de variables antes del despliegue

