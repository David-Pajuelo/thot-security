# Análisis de Correos Automáticos y Actualizaciones de Estados HPS

## 📧 Configuración de Correo

### Correo Remitente (Desde dónde se envían)
- **Variable de entorno**: `SMTP_FROM_EMAIL` o `DEFAULT_FROM_EMAIL`
- **Valor por defecto**: `noreply@hps-system.com` (si `SMTP_FROM_EMAIL` está definido)
- **Fallback**: Si no está definido, se construye como `"{SMTP_FROM_NAME} <{SMTP_USER}>"`
- **Reply-To**: `SMTP_REPLY_TO` (por defecto usa `EMAIL_HOST_USER`/`SMTP_USER`)
- **SMTP Server**: `smtp.gmail.com:587` (configurado en `SMTP_HOST` y `SMTP_PORT`)
- **Credenciales**: `SMTP_USER` y `SMTP_PASSWORD` (contraseña de aplicación Gmail)

### Correo Receptor (Desde dónde se leen los correos del gobierno)
- **Variable de entorno**: `IMAP_USER` (fallback a `SMTP_USER` si no está definido)
- **IMAP Server**: `imap.gmail.com:993` (configurado en `IMAP_HOST` e `IMAP_PORT`)
- **Credenciales**: `IMAP_PASSWORD` (fallback a `SMTP_PASSWORD` si no está definido)
- **Buzón**: `INBOX` (configurado en `IMAP_MAILBOX`)
- **Nota**: Por defecto, se usa la misma cuenta de Gmail para enviar y recibir correos

### Correos del Gobierno que se Monitorean
El sistema busca correos de los siguientes remitentes:
- `no-reply@ccn-cert.cni.es`
- `noreply@ccn-cert.cni.es`
- `solicitudes@ccn-cert.cni.es`
- `hps@ccn-cert.cni.es`

---

## 📧 Correos Automáticos Enviados

### 1. **Correo de Confirmación de Solicitud HPS**
- **Método**: `HpsEmailService.send_hps_confirmation_email()`
- **Tarea Celery**: `send_hps_confirmation_email`
- **Cuándo se envía**:
  - Cuando se crea una nueva solicitud HPS desde un token público
  - Estado inicial: `PENDING`
- **Remitente**: `SMTP_FROM_EMAIL` o `DEFAULT_FROM_EMAIL` (configurado en `.env`)
- **Reply-To**: `SMTP_REPLY_TO` (por defecto `EMAIL_HOST_USER`)
- **Destinatario**: `hps_request.user.email` (email del usuario que creó la solicitud)
- **Template**: `ConfirmationTemplate`
- **Contenido**:
  - Nombre del usuario
  - Email del usuario
  - Número de documento (DNI/NIE)
  - Tipo de solicitud (Alta/Renovación/Traslado)
  - Estado actual (Pendiente)

### 2. **Correo de Actualización de Estado**
- **Método**: `HpsEmailService.send_hps_status_update_email()`
- **Tarea Celery**: `send_hps_status_update_email`
- **Cuándo se envía**:
  - Cuando cambia el estado de una solicitud HPS
  - Estados que disparan este correo:
    - `PENDING` → `SUBMITTED` (solicitud enviada)
    - `PENDING` → `WAITING_DPS` (esperando DPS)
    - `PENDING` → `APPROVED` (aprobada)
    - `PENDING` → `REJECTED` (rechazada)
    - Cualquier cambio de estado
- **Remitente**: `SMTP_FROM_EMAIL` o `DEFAULT_FROM_EMAIL`
- **Reply-To**: `SMTP_REPLY_TO`
- **Destinatario**: `hps_request.user.email` (email del usuario propietario de la solicitud)
- **Templates según estado**:
  - **`approved`**: `HpsApprovedTemplate` (incluye fecha de expiración y notas)
  - **`rejected`**: `HpsRejectedTemplate` (incluye motivo de rechazo)
  - **Otros estados**: `StatusUpdateTemplate` (genérico)
- **Contenido**:
  - Nombre del usuario
  - Número de documento
  - Tipo de solicitud
  - Estado anterior (si existe)
  - Estado nuevo
  - Información adicional según el estado (fecha expiración, motivo rechazo, etc.)

### 3. **Correo de Aprobación HPS**
- **Método**: `HpsEmailService.send_hps_status_update_email()` con estado `approved`
- **Tarea Celery**: `send_hps_approved_email`
- **Cuándo se envía**:
  - Cuando un administrador/jefe de seguridad aprueba una solicitud HPS
  - Estado: `PENDING` → `APPROVED`
  - Endpoint: `POST /api/hps/requests/{id}/approve/`
- **Remitente**: `SMTP_FROM_EMAIL` o `DEFAULT_FROM_EMAIL`
- **Reply-To**: `SMTP_REPLY_TO`
- **Destinatario**: `hps_request.user.email` (email del usuario propietario de la solicitud)
- **Template**: `HpsApprovedTemplate`
- **Contenido adicional**:
  - Fecha de expiración (`expires_at`)
  - Notas de aprobación

### 4. **Correo de Rechazo HPS**
- **Método**: `HpsEmailService.send_hps_status_update_email()` con estado `rejected`
- **Tarea Celery**: `send_hps_rejected_email`
- **Cuándo se envía**:
  - Cuando un administrador/jefe de seguridad rechaza una solicitud HPS
  - Estado: `PENDING` → `REJECTED`
  - Endpoint: `POST /api/hps/requests/{id}/reject/`
- **Remitente**: `SMTP_FROM_EMAIL` o `DEFAULT_FROM_EMAIL`
- **Reply-To**: `SMTP_REPLY_TO`
- **Destinatario**: `hps_request.user.email` (email del usuario propietario de la solicitud)
- **Template**: `HpsRejectedTemplate`
- **Contenido adicional**:
  - Motivo de rechazo (`notes`)

### 5. **Correo con Formulario HPS**
- **Método**: `HpsEmailService.send_hps_form_email()`
- **Tarea Celery**: `send_hps_form_email_task`
- **Cuándo se envía**:
  - Cuando el agente IA genera un formulario HPS para un usuario
  - Comando del agente: "solicitar hps", "crear formulario hps", etc.
  - También se puede enviar para traslados y renovaciones
- **Remitente**: `SMTP_FROM_EMAIL` o `DEFAULT_FROM_EMAIL`
- **Reply-To**: `SMTP_REPLY_TO`
- **Destinatario**: Email proporcionado por el usuario o agente IA (parámetro `email` del método)
- **Template**: Mensaje simple con enlace al formulario
- **Contenido**:
  - Nombre del usuario (opcional)
  - URL del formulario HPS (token único, válido por 72 horas)
  - Instrucciones para completar el formulario

### 6. **Correo con Credenciales de Usuario**
- **Método**: `HpsEmailService.send_user_credentials_email()`
- **Tarea Celery**: `send_hps_credentials_email`
- **Cuándo se envía**:
  - Cuando se crea un nuevo usuario automáticamente desde un formulario HPS
  - Solo si el usuario no existía previamente
  - Cuando el email del formulario coincide con el email del token
- **Remitente**: `SMTP_FROM_EMAIL` o `DEFAULT_FROM_EMAIL`
- **Reply-To**: `SMTP_REPLY_TO`
- **Destinatario**: Email del nuevo usuario (parámetro `email` del método, coincide con `token.email`)
- **Template**: `UserCredentialsTemplate`
- **Contenido**:
  - Nombre del usuario
  - Email (usuario)
  - Contraseña temporal generada automáticamente
  - URL de login al sistema HPS
  - Instrucciones para cambiar la contraseña

### 7. **Correo de Recordatorio de Expiración (Pendiente de implementar)**
- **Tarea Celery**: `check_hps_expiration_task`
- **Cuándo se ejecuta**:
  - Tarea periódica (configurada en Celery Beat)
  - Verifica HPS que están próximas a caducar (9 meses)
  - Solo en horario laboral (L-V 08:00-19:00)
- **Estado objetivo**: HPS con estado `APPROVED` y `expires_at` dentro de 9 meses
- **Estado actual**: La tarea existe pero **NO envía correos todavía** (TODO pendiente)
- **Nota**: Requiere agregar campo `expiration_reminder_sent` al modelo para evitar duplicados

---

## 🔄 Actualizaciones de Estados HPS

### Estados Disponibles

1. **`PENDING`** (Pendiente)
   - Estado inicial cuando se crea una solicitud HPS
   - El usuario ha completado el formulario pero aún no se ha procesado

2. **`WAITING_DPS`** (Esperando DPS)
   - La solicitud ha sido enviada al gobierno
   - Se está esperando que el usuario complete el formulario DPS gubernamental

3. **`SUBMITTED`** (Enviada)
   - La solicitud ha sido enviada a la entidad competente
   - En trámite administrativo

4. **`APPROVED`** (Aprobada)
   - La solicitud ha sido aprobada
   - Incluye fecha de expiración (`expires_at`)

5. **`REJECTED`** (Rechazada)
   - La solicitud ha sido rechazada
   - Incluye motivo de rechazo (`notes`)

6. **`EXPIRED`** (Expirada)
   - La habilitación ha expirado
   - Requiere renovación

---

## 📋 Casos de Actualización de Estados

### Caso 1: Creación de Solicitud HPS desde Token
- **Trigger**: Usuario completa formulario HPS usando token público
- **Endpoint**: `POST /api/hps/public/create-from-token/`
- **Estado inicial**: `PENDING`
- **Correos enviados**:
  1. ✅ Correo de confirmación (`send_hps_confirmation_email`)
  2. ✅ Correo con credenciales (solo si se creó nuevo usuario)

### Caso 2: Envío Manual de Solicitud
- **Trigger**: Usuario/Admin marca solicitud como "enviada"
- **Endpoint**: `POST /api/hps/requests/{id}/submit/`
- **Cambio de estado**: `PENDING` → `SUBMITTED`
- **Correos enviados**:
  1. ✅ Correo de actualización de estado (`send_hps_status_update_email`)

### Caso 3: Aprobación Manual de Solicitud
- **Trigger**: Admin/Jefe de Seguridad aprueba solicitud
- **Endpoint**: `POST /api/hps/requests/{id}/approve/`
- **Cambio de estado**: `PENDING` → `APPROVED`
- **Datos adicionales**: `expires_at`, `notes`
- **Correos enviados**:
  1. ✅ Correo de aprobación (`send_hps_status_update_email` con template `HpsApprovedTemplate`)

### Caso 4: Rechazo Manual de Solicitud
- **Trigger**: Admin/Jefe de Seguridad rechaza solicitud
- **Endpoint**: `POST /api/hps/requests/{id}/reject/`
- **Cambio de estado**: `PENDING` → `REJECTED`
- **Datos adicionales**: `notes` (motivo de rechazo)
- **Correos enviados**:
  1. ✅ Correo de rechazo (`send_hps_status_update_email` con template `HpsRejectedTemplate`)

### Caso 5: Actualización Automática desde Correo del Gobierno
- **Trigger**: Monitor de correos detecta correo del gobierno
- **Tarea Celery**: `monitor_hps_emails_task` (ejecutada periódicamente)
- **Buzón IMAP**: Lee correos desde la cuenta configurada en `IMAP_USER` (por defecto `SMTP_USER`)
- **Buzón**: `INBOX` (configurado en `IMAP_MAILBOX`)
- **Proceso**:
  1. Monitor se conecta a `imap.gmail.com:993` usando `IMAP_USER` e `IMAP_PASSWORD`
  2. Lee correos no leídos (`UNSEEN`) desde los últimos X días (configurable)
  3. Identifica correos del gobierno (remitentes: `no-reply@ccn-cert.cni.es`, `noreply@ccn-cert.cni.es`, `solicitudes@ccn-cert.cni.es`, `hps@ccn-cert.cni.es`)
  4. Extrae información del correo (nombre, DNI, estado)
  5. Busca solicitud HPS correspondiente
  6. Actualiza estado según patrones detectados en el correo
  7. Marca el correo como leído después de procesarlo
- **Patrones de detección**:
  - **`waiting_dps`**: "ha sido enviada al interesado para su realización", "formulario DPS enviado"
  - **`submitted`**: "ha sido enviada a la entidad competente", "en trámite administrativo"
  - **`approved`**: "ha sido aprobada", "habilitación concedida", "autorización otorgada"
  - **`rejected`**: "ha sido rechazada", "solicitud denegada", "no cumple los requisitos"
  - **`expired`**: "ha expirado", "vencimiento de la habilitación"
- **Cambios de estado posibles**:
  - `PENDING` → `WAITING_DPS`
  - `PENDING` → `SUBMITTED`
  - `PENDING` → `APPROVED`
  - `PENDING` → `REJECTED`
  - `APPROVED` → `EXPIRED`
- **Correos enviados**:
  1. ✅ Correo de actualización de estado (`send_hps_status_update_email`)
- **Nota**: El monitor marca los correos como leídos después de procesarlos

### Caso 6: Generación de Formulario HPS por Agente IA
- **Trigger**: Usuario solicita formulario HPS al agente IA
- **Comandos**: "solicitar hps", "crear formulario hps", "necesito formulario hps"
- **Proceso**:
  1. Agente IA crea token HPS único
  2. Genera URL del formulario
  3. Envía correo con enlace al formulario
- **Correos enviados**:
  1. ✅ Correo con formulario HPS (`send_hps_form_email_task`)
- **Nota**: Si el envío falla, el agente IA notifica al usuario y proporciona el enlace para compartir manualmente

---

## 🔍 Flujo Completo de una Solicitud HPS

### Flujo Normal (Nueva Solicitud)

1. **Usuario solicita formulario HPS** (vía agente IA o admin)
   - ✅ Correo con formulario HPS

2. **Usuario completa formulario HPS**
   - Estado: `PENDING`
   - ✅ Correo de confirmación
   - ✅ Correo con credenciales (si es nuevo usuario)

3. **Admin/Jefe marca como enviada** (opcional)
   - Estado: `PENDING` → `SUBMITTED`
   - ✅ Correo de actualización de estado

4. **Monitor detecta correo del gobierno** (automático)
   - Estado: `PENDING` → `WAITING_DPS` o `SUBMITTED`
   - ✅ Correo de actualización de estado

5. **Monitor detecta aprobación del gobierno** (automático)
   - Estado: `SUBMITTED` → `APPROVED`
   - ✅ Correo de aprobación

6. **Admin aprueba manualmente** (alternativa al paso 5)
   - Estado: `PENDING` → `APPROVED`
   - ✅ Correo de aprobación

### Flujo de Rechazo

1. **Admin/Jefe rechaza solicitud**
   - Estado: `PENDING` → `REJECTED`
   - ✅ Correo de rechazo

2. **Monitor detecta rechazo del gobierno** (automático)
   - Estado: `PENDING` → `REJECTED`
   - ✅ Correo de rechazo

### Flujo de Traslado

1. **Admin/Jefe solicita traslado HPS** (vía agente IA)
   - Se genera token para el nuevo usuario
   - ✅ Correo con formulario HPS de traslado

2. **Nuevo usuario completa formulario de traslado**
   - Estado: `PENDING`
   - Se genera PDF rellenado automáticamente
   - ✅ Correo de confirmación
   - ✅ Correo con credenciales (si es nuevo usuario)

3. **Sigue el flujo normal** (aprobación/rechazo)

---

## ⚙️ Configuración de Tareas Celery

### Tareas Periódicas (Celery Beat)

1. **`check_hps_expiration_task`**
   - **Frecuencia**: Configurada en `settings.py` (CELERY_BEAT_SCHEDULE)
   - **Horario**: Solo L-V 08:00-19:00
   - **Propósito**: Verificar HPS próximas a caducar (9 meses)
   - **Estado**: ⚠️ Implementada pero NO envía correos todavía

2. **`monitor_hps_emails_task`**
   - **Frecuencia**: Configurada en `settings.py` (CELERY_BEAT_SCHEDULE)
   - **Propósito**: Monitorear correos del gobierno y actualizar estados
   - **Parámetro**: `since_days` (días hacia atrás para buscar correos)

### Tareas Asíncronas (On-Demand)

- `send_hps_credentials_email`: Envío de credenciales
- `send_hps_confirmation_email`: Confirmación de solicitud
- `send_hps_status_update_email`: Actualización de estado
- `send_hps_approved_email`: Notificación de aprobación
- `send_hps_rejected_email`: Notificación de rechazo
- `send_hps_form_email_task`: Envío de formulario HPS

---

## 📝 Notas Importantes

1. **Todos los correos se envían a través de Celery** para no bloquear las peticiones HTTP
2. **Los correos de actualización de estado** usan templates diferentes según el estado (approved/rejected/genérico)
3. **El monitor de correos** procesa correos del gobierno automáticamente y actualiza estados sin intervención manual
4. **Los correos de recordatorio de expiración** están implementados pero NO envían correos todavía (requiere campo adicional en el modelo)
5. **Los correos de credenciales** solo se envían cuando se crea un nuevo usuario automáticamente
6. **El agente IA** puede generar formularios HPS y enviar correos, con fallback a notificación manual si falla

## 🔐 Configuración de Correo

### Variables de Entorno Requeridas

#### Para Envío de Correos (SMTP)
- `SMTP_HOST`: Servidor SMTP (ej: `smtp.gmail.com`)
- `SMTP_PORT`: Puerto SMTP (ej: `587`)
- `SMTP_USER`: Email de la cuenta Gmail
- `SMTP_PASSWORD`: Contraseña de aplicación Gmail (16 caracteres)
- `SMTP_FROM_EMAIL`: Email remitente (ej: `noreply@hps-system.com`)
- `SMTP_FROM_NAME`: Nombre del remitente (ej: `Sistema HPS`)
- `SMTP_REPLY_TO`: Email para respuestas (por defecto usa `SMTP_USER`)

#### Para Recepción de Correos (IMAP)
- `IMAP_HOST`: Servidor IMAP (ej: `imap.gmail.com`)
- `IMAP_PORT`: Puerto IMAP (ej: `993`)
- `IMAP_USER`: Email de la cuenta Gmail (opcional, usa `SMTP_USER` si no está definido)
- `IMAP_PASSWORD`: Contraseña de aplicación Gmail (opcional, usa `SMTP_PASSWORD` si no está definido)
- `IMAP_MAILBOX`: Buzón a monitorear (por defecto: `INBOX`)

### Nota sobre Cuentas de Correo
- **Por defecto**: Se usa la misma cuenta de Gmail para enviar (SMTP) y recibir (IMAP)
- **Si usas la misma cuenta**: No necesitas definir `IMAP_USER` e `IMAP_PASSWORD`, Django usará `SMTP_USER` y `SMTP_PASSWORD` como fallback
- **Si usas cuentas diferentes**: Define `IMAP_USER` e `IMAP_PASSWORD` explícitamente

---

## 🔗 Archivos Relacionados

- **Servicio de Email**: `cryptotrace/cryptotrace-backend/src/hps_core/email_service.py`
- **Tareas Celery**: `cryptotrace/cryptotrace-backend/src/hps_core/tasks.py`
- **Templates de Email**: `cryptotrace/cryptotrace-backend/src/hps_core/email_templates.py`
- **Vistas/Endpoints**: `cryptotrace/cryptotrace-backend/src/hps_core/views.py`
- **Servicios de Negocio**: `cryptotrace/cryptotrace-backend/src/hps_core/services.py`
- **Monitor de Correos**: `cryptotrace/cryptotrace-backend/src/hps_core/email_monitor.py`
- **Modelos**: `cryptotrace/cryptotrace-backend/src/hps_core/models.py`
