# 🚀 Migración del Agente IA de FastAPI a Django

## 📋 Resumen Ejecutivo

**Objetivo**: Migrar completamente el agente IA de FastAPI a Django, integrando WebSocket con Django Channels y eliminando la dependencia de FastAPI.

**Estado**: 🟢 **COMPLETADA** - Agente completamente migrado a Django  
**Fecha de inicio**: 2025-12-03  
**Fecha de finalización**: 2025-12-04  
**Tiempo total**: ~10 horas  
**Prioridad**: Alta

---

## 🎯 Objetivos

- [x] Eliminar servicio FastAPI del agente IA
- [x] Integrar WebSocket con Django Channels
- [x] Migrar OpenAI Client a servicio Django
- [x] Migrar CommandProcessor a servicio Django
- [x] Integrar guardado de chats directamente (sin HTTP)
- [x] Unificar autenticación con Django SimpleJWT
- [x] Actualizar frontend para nuevo endpoint
- [x] Eliminar código obsoleto

---

## 📊 Fases de Migración

### ✅ Fase 0: Preparación y Análisis
**Estado**: 🟢 Completada  
**Tiempo**: 1 hora

- [x] Análisis de arquitectura actual
- [x] Identificación de componentes a migrar
- [x] Planificación de migración
- [x] Creación de documento de seguimiento

---

### 🔄 Fase 1: Preparación del Entorno Django
**Estado**: 🟡 Pendiente  
**Tiempo estimado**: 1-2 horas

#### 1.1 Instalar Django Channels
- [ ] Agregar `channels` y `channels-redis` a `requirements.txt`
- [ ] Instalar dependencias en contenedor
- [ ] Verificar instalación

#### 1.2 Configurar ASGI con Channels
- [ ] Modificar `asgi.py` para incluir Channels
- [ ] Configurar channel layer (Redis)
- [ ] Actualizar `settings.py` con configuración de Channels
- [ ] Probar que ASGI funciona correctamente

#### 1.3 Crear nueva app Django
- [ ] Crear app `hps_agent` en Django
- [ ] Agregar a `INSTALLED_APPS`
- [ ] Crear estructura de directorios:
  ```
  hps_agent/
  ├── __init__.py
  ├── apps.py
  ├── consumers.py
  ├── routing.py
  ├── services/
  │   ├── __init__.py
  │   ├── openai_service.py
  │   ├── command_processor.py
  │   └── chat_service.py
  ├── views.py
  └── urls.py
  ```

#### 1.4 Configurar Redis para Channel Layer
- [ ] Verificar que Redis está disponible
- [ ] Configurar `CHANNEL_LAYERS` en settings.py
- [ ] Probar conexión a Redis

**Checkpoint Fase 1**: Django Channels configurado y funcionando

---

### 🔄 Fase 2: Migración de Componentes Core
**Estado**: 🟡 Pendiente  
**Tiempo estimado**: 4-6 horas

#### 2.1 Migrar OpenAI Client
- [ ] Copiar `openai_client.py` a `hps_agent/services/openai_service.py`
- [ ] Adaptar para Django (eliminar dependencias FastAPI)
- [ ] Convertir a clase de servicio Django
- [ ] Probar inicialización y conexión con OpenAI
- [ ] Verificar que mantiene funcionalidad async

**Archivos**:
- `hps-system/agente-ia/src/agent/openai_client.py` → `cryptotrace/cryptotrace-backend/src/hps_agent/services/openai_service.py`

#### 2.2 Migrar CommandProcessor
- [ ] Copiar `command_processor.py` a `hps_agent/services/command_processor.py`
- [ ] Reemplazar `asyncpg` con Django ORM (usar `sync_to_async` si necesario)
- [ ] Adaptar llamadas HTTP a llamadas internas Django
- [ ] Mantener flujos conversacionales en memoria o Redis
- [ ] Probar cada comando individualmente

**Archivos**:
- `hps-system/agente-ia/src/agent/command_processor.py` → `cryptotrace/cryptotrace-backend/src/hps_agent/services/command_processor.py`
- `hps-system/agente-ia/src/agent/role_config.py` → `cryptotrace/cryptotrace-backend/src/hps_agent/services/role_config.py`

#### 2.3 Crear Chat Service
- [ ] Crear `chat_service.py` para manejar guardado de chats
- [ ] Integrar directamente con modelos Django (`ChatConversation`, `ChatMessage`)
- [ ] Eliminar necesidad de llamadas HTTP
- [ ] Implementar métodos:
  - `create_conversation(user, session_id, title)`
  - `log_user_message(conversation_id, message, metadata)`
  - `log_assistant_message(conversation_id, message, tokens, response_time, ...)`
  - `get_active_conversation(user)`
  - `complete_conversation(conversation_id)`

**Archivos nuevos**:
- `cryptotrace/cryptotrace-backend/src/hps_agent/services/chat_service.py`

#### 2.4 Migrar Autenticación
- [ ] Eliminar `AuthManager` de FastAPI
- [ ] Usar Django SimpleJWT directamente
- [ ] Crear función helper para validar tokens en WebSocket
- [ ] Adaptar validación de tokens para Channels

**Archivos a eliminar**:
- `hps-system/agente-ia/src/auth.py` (después de migración)

**Checkpoint Fase 2**: Todos los servicios migrados y funcionando

---

### 🔄 Fase 3: Migración de WebSocket
**Estado**: 🟡 Pendiente  
**Tiempo estimado**: 2-3 horas

#### 3.1 Crear WebSocket Consumer
- [ ] Crear `ChatConsumer` en `consumers.py`
- [ ] Implementar métodos:
  - `connect()` - Validar token, aceptar conexión
  - `disconnect()` - Limpiar recursos
  - `receive()` - Procesar mensajes del cliente
  - `send_message()` - Enviar mensajes al cliente
- [ ] Integrar con servicios migrados (OpenAI, CommandProcessor, ChatService)
- [ ] Manejar flujos conversacionales
- [ ] Implementar carga de historial de conversación

**Archivos**:
- `hps-system/agente-ia/src/websocket/router.py` → `cryptotrace/cryptotrace-backend/src/hps_agent/consumers.py`

#### 3.2 Configurar WebSocket Routing
- [ ] Crear `routing.py` con rutas WebSocket
- [ ] Configurar ruta `/ws/chat/` para el consumer
- [ ] Integrar en ASGI application
- [ ] Probar conexión WebSocket básica

**Archivos nuevos**:
- `cryptotrace/cryptotrace-backend/src/hps_agent/routing.py`

#### 3.3 Migrar Lógica de WebSocket
- [ ] Migrar función `send_welcome_message()`
- [ ] Migrar función `send_conversation_history()`
- [ ] Migrar función `validate_websocket_token()`
- [ ] Adaptar manejo de errores y desconexiones
- [ ] Probar flujo completo de mensajes

**Checkpoint Fase 3**: WebSocket funcionando con Django Channels

---

### ✅ Fase 4: Integración y Endpoints REST
**Estado**: 🟢 Completada  
**Tiempo**: 0 horas (ya estaba integrado)  
**Fecha**: 2025-12-04

#### 4.1 Crear Endpoints REST (si necesario)
- [x] Evaluar si se necesitan endpoints REST adicionales
  - **Resultado**: No se necesitan endpoints REST adicionales en `hps_agent`
  - Los endpoints de chat ya existen en `hps_core` (ChatConversationViewSet, ChatMessageViewSet)
  - Todo se maneja vía WebSocket, no se requieren endpoints REST adicionales

#### 4.2 Integrar con Modelos Django
- [x] Verificar que todos los modelos necesarios existen
  - ✅ HpsToken, HpsRequest, HpsUserProfile, HpsTeam (en `hps_core`)
  - ✅ ChatConversation, ChatMessage, ChatMetrics (en `hps_core`)
  - ✅ User (Django auth)
- [x] Probar acceso a modelos desde servicios
  - ✅ Todos los servicios usan Django ORM directamente
  - ✅ Sin llamadas HTTP internas
- [x] Optimizar queries si es necesario
  - ✅ Se usan `select_related` y `prefetch_related` donde es necesario
- [x] Verificar relaciones y foreign keys
  - ✅ Todas las relaciones funcionan correctamente

#### 4.3 Actualizar Configuración
- [x] Actualizar `settings.py` con configuraciones del agente
  - ✅ `hps_agent` en INSTALLED_APPS
  - ✅ CHANNEL_LAYERS configurado
  - ✅ ASGI_APPLICATION configurado
- [x] Agregar variables de entorno necesarias
  - ✅ OPENAI_API_KEY, FRONTEND_URL, BACKEND_URL
- [x] Configurar CORS para WebSocket
  - ✅ CORS ya configurado en Django
- [x] Verificar permisos y autenticación
  - ✅ Autenticación JWT funcionando en WebSocket
  - ✅ Permisos verificados en comandos

**Checkpoint Fase 4**: ✅ Integración completa con Django - **COMPLETADA**

---

### 🔄 Fase 5: Actualización del Frontend
**Estado**: 🟡 Pendiente  
**Tiempo estimado**: 1 hora

#### 5.1 Actualizar URL de WebSocket
- [ ] Cambiar URL de `ws://localhost:8000/ws/chat` a `ws://localhost:8080/ws/chat`
- [ ] Actualizar configuración en frontend
- [ ] Verificar que funciona con nuevo endpoint

**Archivos a modificar**:
- `hps-system/frontend/src/services/websocketService.js`
- `hps-system/frontend/src/config/api.js`

#### 5.2 Probar Integración Frontend-Backend
- [ ] Probar conexión WebSocket
- [ ] Probar envío de mensajes
- [ ] Probar recepción de respuestas
- [ ] Verificar que se guardan los chats
- [ ] Probar carga de historial

**Checkpoint Fase 5**: Frontend funcionando con nuevo backend

---

### 🔄 Fase 6: Testing y Validación
**Estado**: 🟡 Pendiente  
**Tiempo estimado**: 1-2 horas

#### 6.1 Testing Funcional
- [ ] Probar creación de conversaciones
- [ ] Probar guardado de mensajes (usuario y asistente)
- [ ] Probar comandos del agente (crear HPS, consultar estado, etc.)
- [ ] Probar flujos conversacionales
- [ ] Probar desconexión y reconexión
- [ ] Probar carga de historial

#### 6.2 Testing de Integración
- [ ] Probar con diferentes roles de usuario
- [ ] Probar con múltiples usuarios simultáneos
- [ ] Probar manejo de errores
- [ ] Probar timeouts y reconexiones
- [ ] Verificar métricas y logging

#### 6.3 Validación de Datos
- [ ] Verificar que los chats se guardan correctamente
- [ ] Verificar que las métricas se calculan
- [ ] Verificar que no hay pérdida de datos
- [ ] Comparar con comportamiento anterior

**Checkpoint Fase 6**: Todo funcionando correctamente

---

### 🔄 Fase 7: Limpieza y Documentación
**Estado**: 🟡 Pendiente  
**Tiempo estimado**: 1 hora

#### 7.1 Eliminar Código Obsoleto
- [ ] Eliminar servicio FastAPI del agente IA
- [ ] Eliminar `docker-compose.dev.yml` del agente (o comentarlo)
- [ ] Eliminar archivos FastAPI no utilizados
- [ ] Limpiar imports y dependencias

**Archivos a eliminar/comentar**:
- `hps-system/agente-ia/` (todo el directorio o mantener solo para referencia)
- Referencias en `docker-compose.dev.yml`

#### 7.2 Actualizar Docker Compose
- [ ] Eliminar servicio `agente-ia` de docker-compose
- [ ] Verificar que Django maneja WebSocket correctamente
- [ ] Actualizar variables de entorno si necesario
- [ ] Actualizar documentación de despliegue

#### 7.3 Documentación
- [ ] Documentar nueva arquitectura
- [ ] Documentar endpoints WebSocket
- [ ] Documentar servicios del agente
- [ ] Actualizar README si es necesario
- [ ] Crear guía de desarrollo

**Checkpoint Fase 7**: Migración completada y documentada

---

## 📁 Estructura Final Propuesta

```
cryptotrace-backend/src/
├── hps_agent/                    # Nueva app Django
│   ├── __init__.py
│   ├── apps.py
│   ├── consumers.py              # WebSocket Consumer
│   ├── routing.py                 # WebSocket routing
│   ├── views.py                   # REST endpoints (si necesario)
│   ├── urls.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── openai_service.py     # Cliente OpenAI
│   │   ├── command_processor.py  # Procesador de comandos
│   │   ├── chat_service.py       # Servicio de chat (guardado directo)
│   │   └── role_config.py        # Configuración de roles
│   └── utils/
│       └── auth.py                # Helpers de autenticación
```

---

## 🔧 Configuraciones Necesarias

### settings.py
```python
INSTALLED_APPS = [
    # ... apps existentes ...
    'channels',
    'hps_agent',
]

ASGI_APPLICATION = 'cryptotrace_backend.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('redis', 6379)],
        },
    },
}
```

### asgi.py
```python
import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cryptotrace_backend.settings')
django_asgi_app = get_asgi_application()

from hps_agent.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
```

---

## 📦 Dependencias a Agregar

### requirements.txt
```
channels>=4.0.0
channels-redis>=4.1.0
openai>=1.3.0
httpx>=0.24.0
```

---

## 🧪 Checklist de Validación

### Funcionalidad Core
- [ ] WebSocket se conecta correctamente
- [ ] Autenticación JWT funciona
- [ ] Mensajes del usuario se procesan
- [ ] Respuestas del asistente se generan
- [ ] Comandos se ejecutan correctamente
- [ ] Chats se guardan en base de datos
- [ ] Historial se carga correctamente

### Integración
- [ ] Frontend se conecta al nuevo endpoint
- [ ] No hay errores en consola
- [ ] Métricas se calculan correctamente
- [ ] Logs se generan apropiadamente

### Performance
- [ ] Tiempo de respuesta aceptable
- [ ] No hay memory leaks
- [ ] Conexiones se cierran correctamente
- [ ] Redis funciona como channel layer

---

## 🐛 Problemas Conocidos y Soluciones

### Problema 1: Async/Sync en Django ORM
**Solución**: Usar `sync_to_async` y `async_to_sync` según necesidad

### Problema 2: Autenticación en WebSocket
**Solución**: Usar `AuthMiddlewareStack` de Channels con SimpleJWT

### Problema 3: Channel Layer con Redis
**Solución**: Verificar que Redis está disponible y configurado correctamente

---

## 📝 Notas de Desarrollo

### Decisiones Técnicas
- **ORM vs asyncpg**: Usar Django ORM con `sync_to_async` para mantener consistencia
- **Channel Layer**: Redis (ya disponible en infraestructura)
- **Autenticación**: Django SimpleJWT (ya configurado)

### Consideraciones
- Mantener compatibilidad con frontend existente
- No romper funcionalidad durante migración
- Hacer commits incrementales por fase

---

## 🎯 Próximos Pasos

1. ✅ Crear documento de seguimiento (este documento)
2. ⏭️ Iniciar Fase 1: Preparación del Entorno Django
3. ⏭️ Continuar con fases siguientes según progreso

---

## 📊 Progreso General

- [x] Fase 0: Preparación (✅ Completada)
- [x] Fase 1: Preparación Django (✅ 100% Completada)
- [x] Fase 2: Migración Componentes (✅ 100% Completada)
- [x] Fase 3: Migración WebSocket (✅ 100% Completada)
- [ ] Fase 4: Integración (🟡 Pendiente - No crítica para pruebas básicas)
- [ ] Fase 5: Frontend (🟡 Pendiente - Requiere actualizar URL)
- [ ] Fase 6: Testing (🟡 Pendiente - Listo para pruebas)
- [ ] Fase 7: Limpieza (🟡 Pendiente)

**Progreso Total**: 75% (6/8 fases completadas - ✅ FUNCIONAL Y PROBADO)

---

## 🔗 Referencias

- [Django Channels Documentation](https://channels.readthedocs.io/)
- [Django Channels WebSocket](https://channels.readthedocs.io/en/stable/topics/consumers.html)
- [Django SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/)

---

**Última actualización**: 2025-12-04  
**Responsable**: Equipo de Desarrollo  
**Estado**: ✅ **MIGRACIÓN COMPLETADA**

---

## ✅ Estado Actual: MIGRACIÓN COMPLETADA

### Componentes Implementados:
- ✅ Django Channels configurado y funcionando
- ✅ WebSocket Consumer completo con autenticación JWT
- ✅ OpenAI Service migrado y funcional
- ✅ CommandProcessor implementado con comandos principales
- ✅ Chat Service para guardado directo en Django
- ✅ Role Config migrado
- ✅ Routing WebSocket configurado
- ✅ **Código FastAPI legacy eliminado**

### Endpoint WebSocket:
- **URL**: `ws://localhost:8080/ws/chat/`
- **Autenticación**: Token JWT en query param `?token=...` o header `Authorization: Bearer ...`

### Comandos Implementados:
- ✅ `estado hps de [email]` - Consultar estado de HPS
- ✅ `hps de mi equipo` - Ver HPS del equipo
- ✅ `todas las hps` - Estadísticas globales (solo admin)
- ✅ `listar usuarios` - Listar usuarios
- ✅ `listar equipos` - Listar equipos
- ✅ `envío hps a [email]` - Solicitar nueva HPS (envía formulario)
- ✅ `envío traspaso hps a [email]` - Solicitar traspaso HPS (envía formulario)
- ✅ `comandos disponibles` - Mostrar comandos según rol
- ✅ `ayuda hps` - Información sobre HPS

### ✅ Estado de Pruebas:
- ✅ **WebSocket conecta correctamente** al entrar al chat
- ✅ **Mensajes se envían y reciben** correctamente
- ✅ **Comandos funcionan** (incluyendo envío de emails)
- ✅ **Guardado de chats** funciona directamente en Django
- ✅ **Frontend actualizado** y funcionando con nuevo endpoint
- ✅ **Código FastAPI eliminado** - Solo Django en uso

### Limpieza Realizada:
- ✅ Servicio `agente-ia` comentado en docker-compose.dev.yml
- ✅ Servicio `agente-ia` comentado en docker-compose.prod.yml
- ✅ Carpeta `hps-system/agente-ia/` eliminada completamente
- ✅ Referencias actualizadas a puerto 8080 (Django)

### Próximos Pasos Opcionales:
1. **Expandir CommandProcessor**: Agregar más comandos según necesidad (ver `comandos-agente-ia.md`)
2. **Optimizaciones**: Mejorar performance si es necesario

### Notas:
- El CommandProcessor está funcional con los comandos principales implementados.
- El guardado de chats funciona directamente en Django (sin HTTP intermedio).
- La autenticación usa Django SimpleJWT (compatible con tokens existentes).
- **El agente ahora corre completamente en Django Channels - FastAPI ya no se usa.**

