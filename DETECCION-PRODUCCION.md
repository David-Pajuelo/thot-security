# 🔍 Detección de Entorno de Producción

## Formas de Detectar Producción

El sistema detecta producción de **3 formas** (en orden de prioridad):

### 1. **Variable de Entorno Explícita** (Recomendada) ⭐
```bash
ENVIRONMENT=production
```
**Ventaja**: Más explícita y clara

### 2. **Usar settings_prod.py Explícitamente** (Recomendada) ⭐
```bash
DJANGO_SETTINGS_MODULE=cryptotrace_backend.settings_prod
```
**Ventaja**: Fuerza validación estricta y configuración de producción

### 3. **DEBUG=False Implícito**
Si `DEBUG=False` y no hay indicadores de desarrollo, se asume producción.

## 📋 Configuración por Entorno

### Desarrollo (Local)
```bash
# .env
DEBUG=True
ENVIRONMENT=development  # Opcional
# O simplemente DEBUG=True es suficiente
```

### Producción (VPS)
```bash
# .env.prod
DEBUG=False
ENVIRONMENT=production
DJANGO_SETTINGS_MODULE=cryptotrace_backend.settings_prod

# Variables requeridas (sin fallbacks)
SECRET_KEY=...
FRONTEND_URL=https://cryptotrace.idiaicox.com
HPS_SYSTEM_URL=https://hps.idiaicox.com
ALLOWED_HOSTS=cryptotrace.idiaicox.com,www.cryptotrace.idiaicox.com
CORS_ALLOWED_ORIGINS=https://cryptotrace.idiaicox.com,https://hps.idiaicox.com
REDIS_HOST=redis
REDIS_URL=redis://redis:6379/0
```

## 🐳 Docker Compose

### Desarrollo
```yaml
# docker-compose.yml (o docker-compose.dev.yml)
environment:
  - DEBUG=True
  # settings.py detecta desarrollo automáticamente
```

### Producción
```yaml
# docker-compose.prod.yml
environment:
  - DEBUG=False
  - ENVIRONMENT=production
  - DJANGO_SETTINGS_MODULE=cryptotrace_backend.settings_prod
```

## ✅ Comportamiento

### En Desarrollo
- ✅ Aplica fallbacks a localhost automáticamente
- ✅ No requiere todas las variables
- ✅ Funciona con `.env` mínimo

### En Producción
- ❌ **NO** aplica fallbacks
- ❌ **FALLA** si faltan variables requeridas
- ✅ Validación estricta en `settings_prod.py`

## 🎯 Recomendación

**Para producción, usa siempre:**
```bash
DJANGO_SETTINGS_MODULE=cryptotrace_backend.settings_prod
```

Esto garantiza:
1. Validación estricta de variables
2. Configuración de seguridad optimizada
3. Sin fallbacks inesperados

