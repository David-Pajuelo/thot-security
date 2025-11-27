# Integración de Email - HPS System

## Descripción

El módulo de email del sistema HPS permite el envío y recepción de correos electrónicos via Gmail, integrado con el agente de IA para automatización de comunicaciones.

## Características

### ✅ Funcionalidades Implementadas

- **Envío de correos SMTP** via Gmail
- **Recepción de correos IMAP** via Gmail  
- **Templates HTML** profesionales
- **Integración con agente IA**
- **Logs de correos** completos
- **Endpoints REST** para todas las operaciones

### 📧 Tipos de Correos

1. **Confirmación de solicitud** - Al crear nueva solicitud HPS
2. **Actualización de estado** - Cuando cambia el estado de una solicitud
3. **Recordatorios** - Para solicitudes pendientes
4. **Respuesta automática** - Respuestas automáticas a consultas
5. **Notificaciones** - Notificaciones generales del sistema

## Arquitectura

```
backend/src/email/
├── __init__.py          # Inicialización del módulo
├── schemas.py           # Modelos Pydantic
├── smtp_client.py       # Cliente SMTP para envío
├── imap_client.py       # Cliente IMAP para recepción
├── service.py           # Lógica de negocio
├── templates.py         # Templates HTML/texto
└── router.py            # Endpoints REST
```

## Configuración

### Variables de Entorno

```env
# SMTP para envío
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=aicoxidi@gmail.com
SMTP_PASSWORD=tu_app_password_aqui
SMTP_FROM_NAME=HPS System
SMTP_REPLY_TO=aicoxidi@gmail.com

# IMAP para recepción
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=aicoxidi@gmail.com
IMAP_PASSWORD=tu_app_password_aqui
IMAP_MAILBOX=INBOX
```

### Configuración Gmail

1. **Activar 2-Step Verification** en Google Account
2. **Generar App Password** para la aplicación
3. **Usar App Password** en lugar de contraseña normal

## Endpoints API

### Envío de Correos

```http
POST /api/v1/email/send
Content-Type: application/json

{
  "to": "usuario@ejemplo.com",
  "template": "confirmation",
  "template_data": {
    "user_name": "Juan Pérez",
    "user_email": "usuario@ejemplo.com",
    "hps_request_id": 123,
    "document_number": "12345678A",
    "request_type": "Nueva solicitud",
    "status": "pending"
  }
}
```

### Correos Automáticos

```http
# Confirmación de solicitud
POST /api/v1/email/send-confirmation/{hps_request_id}

# Actualización de estado
POST /api/v1/email/send-status-update/{hps_request_id}?new_status=approved

# Recordatorios
POST /api/v1/email/send-reminders
```

### Recepción de Correos

```http
# Revisar correos nuevos
GET /api/v1/email/check-new-emails?since_days=1

# Marcar como leído
POST /api/v1/email/mark-as-read/{message_id}
```

### Utilidades

```http
# Probar conexiones
GET /api/v1/email/test-connections

# Ver logs
GET /api/v1/email/logs?limit=100&offset=0

# Templates disponibles
GET /api/v1/email/templates
```

## Integración con Agente IA

### Comandos Disponibles

El agente IA puede ejecutar los siguientes comandos:

```python
# Enviar correo de confirmación
await agente.enviar_correo_confirmacion(hps_request_id=123)

# Enviar correo de actualización de estado
await agente.enviar_correo_estado(hps_request_id=123, nuevo_estado="approved")

# Enviar recordatorios
await agente.enviar_recordatorios()

# Revisar correos nuevos
correos = await agente.revisar_correos_pendientes()

# Responder correo automáticamente
await agente.responder_correo_usuario(email_id="123", respuesta="Gracias por su consulta...")
```

### Flujo de Trabajo

1. **Usuario completa formulario** → Sistema crea solicitud HPS
2. **Agente recibe notificación** → "Nueva solicitud HPS creada"
3. **Agente envía confirmación** → Email automático al usuario
4. **Agente procesa solicitud** → Revisa y actualiza estado
5. **Agente notifica cambio** → Email de actualización al usuario
6. **Agente revisa correos** → Polling cada 5-10 minutos
7. **Agente responde consultas** → Respuestas automáticas

## Templates

### Estructura de Template

```python
{
  "subject": "Asunto del correo",
  "body": "Versión texto plano",
  "html_body": "Versión HTML con estilos"
}
```

### Variables Disponibles

- `user_name` - Nombre del usuario
- `user_email` - Email del usuario
- `hps_request_id` - ID de solicitud HPS
- `document_number` - Número de documento
- `request_type` - Tipo de solicitud
- `status` - Estado actual
- `additional_data` - Datos adicionales

## Seguridad

### Autenticación

- **Solo usuarios admin** pueden enviar correos
- **JWT tokens** requeridos para todos los endpoints
- **App Passwords** para Gmail (más seguro que contraseñas normales)

### Rate Limits

- **Gmail**: 500 correos/día para cuentas normales
- **IMAP**: Polling cada 5-10 minutos máximo
- **Logs**: Todos los correos quedan registrados

## Monitoreo

### Logs de Email

```python
{
  "message_id": "unique_message_id",
  "to": "destinatario@ejemplo.com",
  "from_email": "aicoxidi@gmail.com",
  "subject": "Asunto del correo",
  "status": "sent|failed|received|processed",
  "template_used": "confirmation",
  "hps_request_id": 123,
  "sent_at": "2024-01-01T10:00:00Z",
  "error_message": null
}
```

### Métricas

- **Correos enviados** por día/semana/mes
- **Tasa de éxito** de envío
- **Correos recibidos** y procesados
- **Tiempo de respuesta** del agente IA

## Troubleshooting

### Errores Comunes

1. **SMTPAuthenticationError**
   - Verificar App Password de Gmail
   - Confirmar 2-Step Verification activado

2. **IMAPConnectionError**
   - Verificar configuración IMAP
   - Confirmar puerto 993 y SSL

3. **TemplateNotFound**
   - Verificar nombre del template
   - Confirmar template existe en `templates.py`

### Logs de Debug

```bash
# Ver logs del servicio de email
docker logs hps_backend | grep "email"

# Probar conexiones
curl -X GET "http://localhost:8001/api/v1/email/test-connections" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## Próximos Pasos

### Funcionalidades Futuras

- [ ] **Tabla de logs** en base de datos
- [ ] **Scheduler** para correos automáticos
- [ ] **Templates personalizables** via UI
- [ ] **Métricas avanzadas** y dashboards
- [ ] **Integración con otros proveedores** (Outlook, etc.)
- [ ] **Filtros avanzados** para correos recibidos
- [ ] **Respuestas automáticas** basadas en IA

### Mejoras Técnicas

- [ ] **Async/await** para operaciones de email
- [ ] **Queue system** para envío masivo
- [ ] **Retry logic** para correos fallidos
- [ ] **Template engine** más avanzado
- [ ] **Email validation** mejorada

