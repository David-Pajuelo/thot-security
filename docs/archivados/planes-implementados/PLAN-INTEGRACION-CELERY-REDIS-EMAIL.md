# Plan de Integración: Celery, Redis y Envío de Correos

## Objetivo
Unificar la infraestructura de tareas asíncronas (Celery + Redis) y el sistema de envío de correos en el backend Django de cryptotrace, eliminando la dependencia de hps-system para estos servicios.

---

## 1. Estado Actual

### 1.1 Celery y Redis en hps-system (FastAPI)
- **Ubicación**: `hps-system/backend/src/celery_app.py`
- **Configuración**:
  - Broker: Redis en `REDIS_HOST:REDIS_PORT/0`
  - Backend: Redis en `REDIS_HOST:REDIS_PORT/0`
  - Colas: `default`, `email`, `analysis`
  - Tareas:
    - `email_tasks.py`: Envío de emails
    - `hps_expiration_tasks.py`: Verificación de HPS próximas a caducar
    - `hps_monitor_tasks.py`: Monitorización de correos HPS
    - `analysis_tasks.py`: Análisis de correos y generación de reportes
- **Celery Beat**: Tareas periódicas configuradas

### 1.2 Celery y Redis en cryptotrace (Django)
- **Ubicación**: `cryptotrace/cryptotrace-backend/src/cryptotrace_backend/celery.py`
- **Configuración**: Ya existe en `settings.py`
  - Broker: Redis
  - Backend: Redis
  - Colas: `default`, `email`, `analysis`
  - Tareas: `hps_core/tasks.py` (envío de emails HPS)
- **Celery Beat**: Configurado para verificación de expiración HPS

### 1.3 Servicio de Email

#### hps-system (FastAPI)
- **Ubicación**: `hps-system/backend/src/email/service.py`
- **Características**:
  - Cliente SMTP (`smtp_client.py`)
  - Cliente IMAP (`imap_client.py`) para recibir correos
  - Gestor de templates (`template_manager.py`)
  - Monitorización de correos entrantes (`hps_monitor.py`)
  - Templates HTML personalizados

#### cryptotrace (Django)
- **Ubicación**: `cryptotrace/cryptotrace-backend/src/hps_core/email_service.py`
- **Características**:
  - Usa Django `EmailMultiAlternatives`
  - Templates en `email_templates.py`
  - Sin funcionalidad IMAP (solo envío)

---

## 2. Plan de Integración

### Fase 1: Migración de Tareas Celery de hps-system a Django

#### 2.1 Tareas a Migrar

1. **Tareas de Email** (`email_tasks.py`)
   - ✅ Ya migradas parcialmente (solo tareas HPS básicas)
   - ⚠️ Faltan: Tareas genéricas de envío de email

2. **Tareas de Expiración HPS** (`hps_expiration_tasks.py`)
   - ✅ Ya migrada: `check_hps_expiration_task` en `hps_core/tasks.py`
   - ✅ Configurada en Celery Beat

3. **Tareas de Monitorización** (`hps_monitor_tasks.py`)
   - ❌ **PENDIENTE**: Monitorización de correos entrantes (IMAP)
   - Funcionalidad: Procesar correos del gobierno para actualizar estados HPS

4. **Tareas de Análisis** (`analysis_tasks.py`)
   - ❌ **PENDIENTE**: Análisis de correos y generación de reportes
   - Funcionalidad: Procesar correos para extraer información

#### 2.2 Pasos de Migración

**Paso 1.1: Migrar tareas genéricas de email**
```python
# cryptotrace/cryptotrace-backend/src/hps_core/tasks.py
@shared_task(bind=True, name="hps_core.send_generic_email")
def send_generic_email_task(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tarea genérica para envío de emails con templates
    """
    # Adaptar lógica de hps-system/backend/src/tasks/email_tasks.py
    pass
```

**Paso 1.2: Migrar tareas de monitorización**
```python
# cryptotrace/cryptotrace-backend/src/hps_core/tasks.py
@shared_task(bind=True, name="hps_core.monitor_hps_emails")
def monitor_hps_emails_task(self, since_days: int = 1) -> Dict[str, Any]:
    """
    Monitorización automática de correos HPS entrantes
    """
    # Adaptar lógica de hps-system/backend/src/tasks/hps_monitor_tasks.py
    # Requiere: Implementar cliente IMAP en Django
    pass
```

**Paso 1.3: Migrar tareas de análisis**
```python
# cryptotrace/cryptotrace-backend/src/hps_core/tasks.py
@shared_task(bind=True, name="hps_core.analyze_emails")
def analyze_emails_task(self, analysis_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Análisis de correos para extraer información
    """
    # Adaptar lógica de hps-system/backend/src/tasks/analysis_tasks.py
    pass
```

**Paso 1.4: Actualizar rutas de tareas en settings.py**
```python
# cryptotrace/cryptotrace-backend/src/cryptotrace_backend/settings.py
CELERY_TASK_ROUTES = {
    # Tareas de email
    "hps_core.tasks.send_*": {"queue": "email"},
    "hps_core.tasks.*email*": {"queue": "email"},
    
    # Tareas de monitorización
    "hps_core.tasks.monitor_*": {"queue": "email"},
    
    # Tareas de análisis
    "hps_core.tasks.analyze_*": {"queue": "analysis"},
    "hps_core.tasks.process_*": {"queue": "analysis"},
    "hps_core.tasks.generate_*": {"queue": "analysis"},
    
    # Tareas de expiración
    "hps_core.tasks.check_*": {"queue": "email"},
}
```

**Paso 1.5: Actualizar Celery Beat Schedule**
```python
# cryptotrace/cryptotrace-backend/src/cryptotrace_backend/settings.py
CELERY_BEAT_SCHEDULE = {
    # Verificación de HPS próximas a caducar (L-V a las 9:00 AM)
    'check-hps-expiration': {
        'task': 'hps_core.tasks.check_hps_expiration_task',
        'schedule': crontab(hour=9, minute=0, day_of_week='1-5'),
    },
    # Monitorización horaria de correos (8:00 AM - 6:00 PM)
    'hourly-hps-monitoring': {
        'task': 'hps_core.tasks.monitor_hps_emails_task',
        'schedule': crontab(hour='8-18', minute=0),
    },
    # Estadísticas semanales (Lunes a las 8:00 AM)
    'weekly-hps-stats': {
        'task': 'hps_core.tasks.weekly_hps_stats_task',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),
    },
}
```

---

### Fase 2: Unificación del Servicio de Email

#### 2.1 Funcionalidades a Migrar desde hps-system

1. **Cliente IMAP** (`imap_client.py`)
   - Leer correos entrantes
   - Procesar correos del gobierno
   - Marcar correos como leídos

2. **Monitorización de Correos** (`hps_monitor.py`)
   - Detectar correos relacionados con HPS
   - Actualizar estados de solicitudes HPS
   - Extraer información de correos del gobierno

3. **Gestor de Templates Mejorado** (`template_manager.py`)
   - Sistema de templates más robusto
   - Soporte para múltiples tipos de templates

#### 2.2 Pasos de Migración

**Paso 2.1: Crear cliente IMAP para Django**
```python
# cryptotrace/cryptotrace-backend/src/hps_core/imap_client.py
"""
Cliente IMAP para leer correos entrantes en Django
Adaptado desde hps-system/backend/src/email/imap_client.py
"""
import imaplib
import email
from typing import List, Dict, Any
from django.conf import settings

class IMAPClient:
    def __init__(self):
        self.host = getattr(settings, 'IMAP_HOST', 'imap.gmail.com')
        self.port = getattr(settings, 'IMAP_PORT', 993)
        self.username = getattr(settings, 'IMAP_USER', '')
        self.password = getattr(settings, 'IMAP_PASSWORD', '')
        self.mailbox = getattr(settings, 'IMAP_MAILBOX', 'INBOX')
    
    def connect(self):
        """Conectar al servidor IMAP"""
        # Implementar conexión IMAP
        pass
    
    def fetch_emails(self, since_days: int = 1) -> List[Dict[str, Any]]:
        """Obtener correos desde hace X días"""
        # Implementar obtención de correos
        pass
```

**Paso 2.2: Crear monitor de correos HPS**
```python
# cryptotrace/cryptotrace-backend/src/hps_core/email_monitor.py
"""
Monitor de correos HPS entrantes
Adaptado desde hps-system/backend/src/email/hps_monitor.py
"""
from .imap_client import IMAPClient
from .models import HpsRequest

class HPSEmailMonitor:
    def __init__(self):
        self.imap_client = IMAPClient()
    
    def process_incoming_emails(self, since_days: int = 1):
        """Procesar correos entrantes y actualizar HPS"""
        # Implementar lógica de procesamiento
        pass
    
    def update_hps_from_email(self, email_data: Dict, hps_request: HpsRequest):
        """Actualizar estado HPS basado en correo recibido"""
        # Implementar actualización
        pass
```

**Paso 2.3: Mejorar servicio de email existente**
```python
# cryptotrace/cryptotrace-backend/src/hps_core/email_service.py
# Agregar métodos adicionales desde hps-system:
# - send_email_with_template (genérico)
# - send_bulk_emails
# - get_email_status
```

**Paso 2.4: Unificar Templates de Email**

⚠️ **IMPORTANTE**: Los templates deben ser **exactamente los mismos** que en hps-system para mantener consistencia.

**Estrategia de Unificación:**

1. **Copiar templates desde hps-system a Django:**
   - `hps-system/backend/src/email/templates/user_credentials.py` → `cryptotrace/cryptotrace-backend/src/hps_core/email_templates.py` (clase `UserCredentialsTemplate`)
   - `hps-system/backend/src/email/templates/status_update.py` → `cryptotrace/cryptotrace-backend/src/hps_core/email_templates.py` (clase `StatusUpdateTemplate`)
   - `hps-system/backend/src/email/templates/hps_approved.py` → `cryptotrace/cryptotrace-backend/src/hps_core/email_templates.py` (clase `HpsApprovedTemplate`)
   - `hps-system/backend/src/email/templates/hps_rejected.py` → `cryptotrace/cryptotrace-backend/src/hps_core/email_templates.py` (clase `HpsRejectedTemplate`)
   - `hps-system/backend/src/email/templates/hps_expiration_reminder.py` → `cryptotrace/cryptotrace-backend/src/hps_core/email_templates.py` (clase `HpsExpirationReminderTemplate`)
   - `hps-system/backend/src/email/templates/hps_form.py` → `cryptotrace/cryptotrace-backend/src/hps_core/email_templates.py` (clase `HpsFormTemplate`)

2. **Adaptar imports y dependencias:**
   - Cambiar imports de FastAPI a Django
   - Usar `django.conf.settings` en lugar de `settings` de FastAPI
   - Mantener la misma estructura HTML y contenido

3. **Verificar que los templates sean idénticos:**
   - Comparar HTML generado
   - Verificar que las variables se reemplacen correctamente
   - Probar envío de emails con ambos sistemas (temporalmente) para comparar

4. **Eliminar templates duplicados:**
   - Una vez unificados, los templates solo existirán en Django
   - hps-system ya no generará emails directamente (todo vía Django)

---

### Fase 3: Actualización de Docker Compose

#### 3.1 Servicios a Unificar

**Servicios actuales en cryptotrace:**
- `redis`: Servicio Redis compartido ✅
- `celery-worker`: Worker de Celery ✅
- `celery-beat`: Scheduler de Celery ✅

**Servicios a eliminar de hps-system:**
- `celery-worker` (si existe)
- `celery-beat` (si existe)
- `redis` (si existe como servicio separado)

#### 3.2 Configuración Docker Compose Unificada

```yaml
# docker-compose.yml (raíz del proyecto)
services:
  # Redis compartido
  redis:
    image: redis:7-alpine
    container_name: cryptotrace-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    networks:
      - cryptotrace_network

  # Celery Worker (Django)
  celery-worker:
    build:
      context: ./cryptotrace/cryptotrace-backend
      dockerfile: docker/Dockerfile
    container_name: cryptotrace-celery-worker
    command: celery -A cryptotrace_backend worker --loglevel=info --queues=email,analysis,default
    volumes:
      - ./cryptotrace/cryptotrace-backend/src:/app
    env_file:
      - ./cryptotrace/cryptotrace-backend/.env
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
      - db
    networks:
      - cryptotrace_network

  # Celery Beat (Django)
  celery-beat:
    build:
      context: ./cryptotrace/cryptotrace-backend
      dockerfile: docker/Dockerfile
    container_name: cryptotrace-celery-beat
    command: celery -A cryptotrace_backend beat --loglevel=info
    volumes:
      - ./cryptotrace/cryptotrace-backend/src:/app
    env_file:
      - ./cryptotrace/cryptotrace-backend/.env
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
      - db
    networks:
      - cryptotrace_network
```

#### 3.3 Variables de Entorno

**⚠️ IMPORTANTE: Unificación de Variables de Entorno**

Todas las variables de email deben estar **SOLO en el `.env` de cryptotrace-backend**, no en hps-system.

**Pasos para unificar variables de entorno:**

1. **✅ COMPLETADO: Actualizado `cryptotrace-backend/env.example`**
   - Incluye todas las variables SMTP, IMAP, Redis y Celery
   - Documentación completa con instrucciones para Gmail
   - Variables organizadas por secciones

2. **Acciones requeridas del usuario:**
   ```bash
   # 1. Copiar env.example a .env en cryptotrace-backend
   cd cryptotrace/cryptotrace-backend
   cp env.example .env
   
   # 2. Editar .env y configurar:
   #    - SMTP_USER: tu_email@gmail.com
   #    - SMTP_PASSWORD: tu_contraseña_aplicacion_gmail (misma para IMAP_PASSWORD)
   #    - IMAP_USER: mismo que SMTP_USER
   #    - IMAP_PASSWORD: misma que SMTP_PASSWORD
   #    - SECRET_KEY: cambiar por una clave segura
   #    - JWT_SECRET_KEY: mismo que SECRET_KEY (o diferente si prefieres)
   ```

3. **Eliminar variables de hps-system (si existen):**
   - Remover variables SMTP/IMAP de `hps-system/.env.dev` (si existen)
   - Remover variables Redis/Celery de `hps-system/.env.dev` (si existen)
   - **NOTA**: hps-system ya no necesita estas variables, todo se gestiona desde Django

4. **Verificar Docker Compose:**
   - ✅ `celery-worker` y `celery-beat` ya están configurados para usar `.env`
   - ✅ Variables de Redis/Celery ya están en el docker-compose.yml
   - ✅ Las variables de email se cargan desde `.env` automáticamente

**Confirmación:**
- ✅ Variables de email: **SOLO en cryptotrace-backend/.env**
- ✅ Variables de Redis/Celery: **SOLO en cryptotrace-backend/.env**
- ✅ hps-system: **NO necesita estas variables** (todo se gestiona desde Django)
- ✅ **Misma cuenta de correo**: Todas las variables SMTP/IMAP apuntan a la misma cuenta (configurada en cryptotrace-backend/.env)
- ✅ **Templates unificados**: Los templates de email son exactamente los mismos que en hps-system
- ✅ **env.example actualizado**: Incluye todas las variables necesarias con documentación

---

### Fase 4: Actualización del Frontend hps-system

#### 4.1 Endpoints a Actualizar

Los endpoints del frontend que llaman a tareas Celery deben actualizarse para usar los endpoints de Django:

**Antes (FastAPI):**
```javascript
// hps-system/frontend/src/services/apiService.js
POST /api/v1/email/send
POST /api/v1/tasks/email/send
```

**Después (Django):**
```javascript
// hps-system/frontend/src/services/apiService.js
POST /api/hps/email/send  // Nuevo endpoint en Django
// O usar directamente las tareas Celery desde Django
```

#### 4.2 Crear Endpoints en Django

```python
# cryptotrace/cryptotrace-backend/src/hps_core/views.py
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_email_async(request):
    """
    Endpoint para envío asíncrono de emails
    """
    from .tasks import send_generic_email_task
    
    email_data = request.data
    task = send_generic_email_task.delay(email_data)
    
    return Response({
        'task_id': task.id,
        'status': 'queued'
    }, status=status.HTTP_202_ACCEPTED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_status(request, task_id):
    """
    Obtener estado de una tarea Celery
    """
    from celery.result import AsyncResult
    
    task_result = AsyncResult(task_id)
    
    return Response({
        'task_id': task_id,
        'status': task_result.status,
        'result': task_result.result if task_result.ready() else None
    })
```

---

## 3. Plan de Envío de Correos

### 3.1 Arquitectura Unificada

```
┌─────────────────┐
│   Django API    │
│   (Endpoints)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Celery Task    │
│  (Queue: email) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Email Service   │
│ (Django)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SMTP Server    │
│  (Gmail/etc)    │
└─────────────────┘
```

### 3.2 Flujo de Envío

1. **Frontend/API** → Llama a endpoint Django
2. **Django View** → Crea tarea Celery asíncrona
3. **Celery Worker** → Procesa tarea de la cola `email`
4. **Email Service** → Usa Django `EmailMultiAlternatives`
5. **SMTP** → Envía correo

### 3.3 Tipos de Correos

1. **Credenciales de Usuario**
   - Template: `UserCredentialsTemplate`
   - Tarea: `send_hps_credentials_email`

2. **Confirmación de Solicitud HPS**
   - Template: `ConfirmationTemplate`
   - Tarea: `send_hps_confirmation_email`

3. **Actualización de Estado HPS**
   - Template: `StatusUpdateTemplate`
   - Tarea: `send_hps_status_update_email`

4. **Aprobación HPS**
   - Template: `HpsApprovedTemplate`
   - Tarea: `send_hps_approved_email`

5. **Rechazo HPS**
   - Template: `HpsRejectedTemplate`
   - Tarea: `send_hps_rejected_email`

6. **Formulario HPS**
   - Template: Simple (en `email_service.py`)
   - Tarea: `send_hps_form_email_task`

7. **Recordatorio de Expiración**
   - Template: Nuevo (crear)
   - Tarea: `check_hps_expiration_task` (envía recordatorios)

### 3.4 Configuración de Email

**Opciones:**

1. **Gmail (Actual)**
   - SMTP: `smtp.gmail.com:587`
   - IMAP: `imap.gmail.com:993`
   - Requiere: Contraseña de aplicación

2. **SendGrid (Recomendado para producción)**
   - API Key más seguro
   - Mejor deliverability
   - Analytics integrados

3. **Amazon SES**
   - Escalable
   - Costo por uso
   - Requiere configuración AWS

**Recomendación**: Mantener Gmail para desarrollo, considerar SendGrid para producción.

---

## 4. Checklist de Implementación

### Fase 1: Migración de Tareas
- [x] Migrar `send_generic_email_task` a Django ✅
- [x] Migrar `monitor_hps_emails_task` a Django ✅
- [ ] Migrar `analyze_emails_task` a Django (Pendiente - opcional)
- [x] Actualizar rutas de tareas en `settings.py` ✅
- [x] Actualizar `CELERY_BEAT_SCHEDULE` ✅
- [ ] Probar tareas migradas (Pendiente - requiere configuración de .env)

### Fase 2: Servicio de Email
- [x] Crear `imap_client.py` en Django ✅
- [x] Crear `email_monitor.py` en Django ✅
- [x] Mejorar `email_service.py` con métodos adicionales ✅
- [x] Migrar templates mejorados ✅
- [ ] Probar envío de correos (Pendiente - requiere configuración de .env)
- [ ] Probar monitorización IMAP (Pendiente - requiere configuración de .env)

### Fase 3: Docker Compose
- [x] Verificar servicio Redis compartido ✅
- [x] Actualizar `celery-worker` para usar todas las colas ✅
- [x] Actualizar `celery-beat` con nuevas tareas ✅
- [x] Actualizar `env.example` con todas las variables necesarias ✅
- [x] Documentar variables de entorno en el plan ✅
- [ ] Eliminar servicios Celery de hps-system (si existen) - Verificar manualmente
- [ ] Probar servicios en Docker (Pendiente - requiere configuración de .env)

### Fase 4: Frontend
- [x] Crear endpoints Django para envío de emails ✅
- [x] Crear endpoint para estado de tareas Celery ✅
- [x] Crear endpoint para envío masivo de emails ✅
- [ ] Actualizar frontend para usar nuevos endpoints (Pendiente - si es necesario)
- [ ] Probar flujo completo (Pendiente - requiere configuración de .env)

### Fase 5: Testing
- [ ] Probar envío de todos los tipos de correos
- [ ] Probar monitorización de correos entrantes
- [ ] Probar tareas periódicas (Celery Beat)
- [ ] Probar manejo de errores
- [ ] Probar escalabilidad (múltiples workers)

---

## 5. Consideraciones Importantes

### 5.1 Seguridad
- **Contraseñas de aplicación**: Usar contraseñas de aplicación, no contraseñas normales
- **Variables de entorno**: Todas las credenciales en `.env`, nunca en código
- **IMAP**: Considerar usar OAuth2 en lugar de contraseñas

### 5.2 Performance
- **Colas separadas**: Mantener `email`, `analysis`, `default` para balancear carga
- **Workers múltiples**: Considerar múltiples workers para cola `email`
- **Rate limiting**: Implementar límites de envío para evitar spam

### 5.3 Monitoreo
- **Flower**: Herramienta de monitoreo de Celery (opcional)
- **Logs**: Centralizar logs de tareas Celery
- **Alertas**: Configurar alertas para tareas fallidas

### 5.4 Backup y Recuperación
- **Redis persistence**: Configurar `appendonly yes` en Redis
- **Task retry**: Configurar reintentos automáticos para tareas fallidas
- **Dead letter queue**: Configurar cola para tareas que fallan repetidamente

---

## 6. Orden de Implementación Recomendado

1. **Semana 1**: Fase 1 (Migración de tareas básicas)
2. **Semana 2**: Fase 2 (Servicio de email + IMAP)
3. **Semana 3**: Fase 3 (Docker Compose) + Fase 4 (Frontend)
4. **Semana 4**: Fase 5 (Testing y ajustes)

---

## 7. Documentación Adicional

- [Configuración de Gmail para SMTP/IMAP](https://support.google.com/mail/answer/7126229)
- [Documentación de Celery](https://docs.celeryproject.org/)
- [Django Email Backend](https://docs.djangoproject.com/en/4.2/topics/email/)

