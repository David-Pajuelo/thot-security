# 📧 Lista Completa de Correos del Sistema HPS

## 📋 **Resumen de Correos por Categoría**

### 🔄 **CORREOS AUTOMÁTICOS (Sin Intervención del Usuario)**

#### **1. Notificación de Nuevo Usuario**
- **Cuándo se envía**: Al crear un nuevo usuario a través del formulario
- **Quién lo recibe**: Jefes de Seguridad y Líder de Equipo del nuevo miembro
- **Template**: `new_user_notification`
- **Asunto**: `Nuevo usuario registrado: [Nombre]`
- **Contenido**: 
  - Información del nuevo usuario (nombre, email, rol, equipo)
  - Fecha de registro
  - Quién lo creó
  - Datos del equipo asignado
- **Código**: `backend/src/users/service.py` - `create_user()`

#### **2. Credenciales de Usuario Nuevo**
- **Cuándo se envía**: Al crear una HPS pública que genera un nuevo usuario
- **Quién lo recibe**: El usuario recién creado
- **Template**: `user_credentials`
- **Asunto**: `Credenciales de acceso - [Nombre]`
- **Contenido**:
  - Email del usuario
  - Contraseña temporal generada
  - URL de login
  - Instrucciones de acceso
  - Tiempo de expiración de la contraseña
- **Código**: `backend/src/hps/router.py` - `create_hps_public()`

#### **3. Notificación de Cambio de Estado Automático**
- **Cuándo se envía**: Al detectar correos del gobierno que cambian estados
- **Quién lo recibe**: El solicitante de la HPS
- **Template**: `status_update`
- **Asunto**: `Actualización de estado HPS - [Documento]`
- **Contenido**:
  - Estado anterior y nuevo estado
  - Número de documento
  - ID de solicitud
  - Fecha de actualización
  - Información adicional del cambio
- **Código**: `backend/src/email/hps_monitor.py` - `_send_status_notification()`

### 🎯 **CORREOS MANUALES (Iniciados por Usuario)**

#### **4. Confirmación de Solicitud HPS**
- **Cuándo se envía**: Cuando se envía manualmente confirmación de HPS
- **Quién lo recibe**: El solicitante de la HPS
- **Template**: `confirmation`
- **Asunto**: `Confirmación de solicitud HPS - [Documento]`
- **Contenido**:
  - Confirmación de recepción
  - Detalles de la solicitud
  - Número de documento
  - Tipo de solicitud
  - Estado actual
  - Fecha de solicitud
- **Endpoint**: `POST /api/v1/email/send-confirmation/{hps_request_id}`

#### **5. Actualización de Estado HPS**
- **Cuándo se envía**: Cuando se envía manualmente actualización de estado
- **Quién lo recibe**: El solicitante de la HPS
- **Template**: `status_update`
- **Asunto**: `Actualización de estado HPS - [Documento]`
- **Contenido**:
  - Estado anterior y nuevo estado
  - Badges de estado con colores
  - Información del cambio
  - Próximos pasos
- **Endpoint**: `POST /api/v1/email/send-status-update/{hps_request_id}`

#### **6. Recordatorio de Solicitudes Pendientes**
- **Cuándo se envía**: Cuando se envían manualmente recordatorios
- **Quién lo recibe**: Usuarios con solicitudes pendientes
- **Template**: `reminder`
- **Asunto**: `Recordatorio: Solicitud HPS pendiente - [Documento]`
- **Contenido**:
  - Recordatorio de solicitud pendiente
  - Días transcurridos
  - Fecha de solicitud
  - Acciones requeridas
  - Enlaces de acceso
- **Endpoint**: `POST /api/v1/email/send-reminders`

#### **7. Formulario HPS**
- **Cuándo se envía**: Cuando se envía manualmente un formulario HPS
- **Quién lo recibe**: El destinatario especificado
- **Template**: `hps_form`
- **Asunto**: `Formulario HPS - [Nombre]`
- **Contenido**:
  - Enlace al formulario
  - Instrucciones de llenado
  - Información del solicitante
  - Fecha límite
- **Endpoint**: `POST /api/v1/email/send-hps-form-async`

#### **8. HPS Aprobada**
- **Cuándo se envía**: Cuando se aprueba una HPS
- **Quién lo recibe**: El solicitante de la HPS
- **Template**: `hps_approved`
- **Asunto**: `HPS Aprobada - [Documento]`
- **Contenido**:
  - Notificación de aprobación
  - Detalles de la HPS
  - Próximos pasos
  - Documentos adjuntos
- **Endpoint**: `POST /api/v1/email/send` (manual)

#### **9. HPS Rechazada**
- **Cuándo se envía**: Cuando se rechaza una HPS
- **Quién lo recibe**: El solicitante de la HPS
- **Template**: `hps_rejected`
- **Asunto**: `HPS Rechazada - [Documento]`
- **Contenido**:
  - Notificación de rechazo
  - Motivos del rechazo
  - Información para reenvío
  - Contacto de soporte
- **Endpoint**: `POST /api/v1/email/send` (manual)

### ⏰ **CORREOS PROGRAMADOS (Tareas Automáticas)**

#### **10. Monitorización Diaria de Correos**
- **Cuándo se envía**: Diariamente a las 9:00 AM
- **Qué hace**: Escanea correos del gobierno y actualiza estados
- **Emails generados**: Notificaciones de cambio de estado automático
- **Código**: `backend/src/tasks/hps_monitor_tasks.py` - `daily_hps_monitoring_task()`

#### **11. Estadísticas Semanales**
- **Cuándo se envía**: Lunes a las 8:00 AM
- **Quién lo recibe**: Administradores (si se configura)
- **Contenido**: Reportes de estadísticas de monitorización
- **Código**: `backend/src/tasks/hps_monitor_tasks.py` - `weekly_hps_stats_task()`

## 📊 **Resumen por Destinatarios**

### **Jefes de Seguridad y Líderes de Equipo:**
- ✅ Notificación de nuevo usuario
- ✅ Reportes de estadísticas (opcional)

### **Solicitantes de HPS:**
- ✅ Credenciales de usuario (si es nuevo)
- ✅ Confirmación de solicitud
- ✅ Actualización de estado (manual y automática)
- ✅ Recordatorios
- ✅ HPS aprobada
- ✅ HPS rechazada

### **Usuarios Generales:**
- ✅ Formularios HPS
- ✅ Notificaciones generales

## 🎨 **Diseño Visual de los Templates**

### **Colores por Tipo de Email:**
- 🟢 **Verde**: Confirmación (tranquilidad, éxito)
- 🔵 **Azul**: Actualización de estado (información, cambio)
- 🟡 **Amarillo**: Recordatorio (atención, urgencia)
- 🟣 **Púrpura**: Notificación de usuario (nuevo, importante)
- 🔴 **Rojo**: Rechazo (alerta, problema)
- 🟢 **Verde**: Aprobación (éxito, finalización)

### **Elementos Visuales:**
- **Gradientes** en headers
- **Badges** de estado con colores
- **Cajas informativas** con bordes de color
- **Grids** para información organizada
- **Alertas** visuales para recordatorios

## 🔧 **Configuración Técnica**

### **Métodos de Envío:**
1. **Síncrono** - Envío inmediato
2. **Asíncrono** - Envío en segundo plano con Celery
3. **Programado** - Tareas automáticas con Celery Beat

### **Permisos Requeridos:**
- **Admin**: Todos los tipos de email
- **Team Leader**: Emails de su equipo
- **Jefe Seguridad**: Notificaciones de seguridad
- **Otros roles**: Sin permisos de envío

## 📈 **Estadísticas de Envío**

### **Emails Automáticos por Usuario:**
- **Creación de usuario**: 1-3 emails (notificaciones a jefes)
- **HPS con usuario nuevo**: 1 email (credenciales)
- **Monitorización diaria**: Variable según correos del gobierno

### **Emails Manuales:**
- **Depende del uso** del sistema
- **Sin límite** de envío
- **Controlado por permisos**

## 🚀 **Estado del Sistema**

### ✅ **Implementado y Funcionando:**
- Sistema de emails automáticos
- Templates modulares
- Envío SMTP verificado
- Integración con backend
- Tareas programadas
- Pruebas exitosas realizadas

### 📋 **Templates Disponibles:**
1. `confirmation` - Confirmación de solicitud
2. `status_update` - Actualización de estado
3. `reminder` - Recordatorio
4. `new_user_notification` - Notificación de nuevo usuario
5. `user_credentials` - Credenciales de usuario
6. `hps_form` - Formulario HPS
7. `hps_approved` - HPS aprobada
8. `hps_rejected` - HPS rechazada

### 🔄 **Flujo de Emails por Acción:**

#### **Nuevo Usuario:**
```
Usuario creado → Notificar jefes → Email a jefes de seguridad y líder de equipo
```

#### **HPS Pública con Usuario Nuevo:**
```
HPS creada → Usuario nuevo generado → Email credenciales → Email a usuario
```

#### **Cambio de Estado Automático:**
```
Correo gobierno → Detectar cambio → Actualizar estado → Notificar usuario
```

#### **Acciones Manuales:**
```
Usuario inicia acción → Seleccionar template → Enviar email → Confirmar envío
```

## 📞 **Instrucciones de Uso**

### **Para Enviar Emails Manualmente:**
```bash
POST /api/v1/email/send
{
  "to": "destinatario@email.com",
  "template": "confirmation",
  "template_data": {
    "user_name": "Nombre Usuario",
    "user_email": "usuario@email.com",
    "document_number": "12345678A",
    "request_type": "nueva",
    "status": "pending",
    "hps_request_id": 1
  }
}
```

### **Para Verificar Templates:**
```bash
GET /api/v1/email/templates
```

## 🎯 **Conclusión**

El sistema HPS envía **11 tipos diferentes de correos** en total:
- **3 automáticos** (nuevo usuario, credenciales, cambio de estado)
- **6 manuales** (confirmación, actualización, recordatorio, formulario, aprobación, rechazo)
- **2 programados** (monitorización diaria, estadísticas semanales)

Todos los correos están **implementados**, **probados** y **funcionando correctamente**.



