# 📧 Acciones que Envían Emails en el Sistema HPS

## 📋 Resumen de Acciones con Envío de Emails

### 🔄 **Acciones Automáticas (Sin Intervención del Usuario)**

#### **1. Creación de Usuario**
- **Cuándo**: Al crear un nuevo usuario a través del formulario
- **Quién recibe**: Jefes de Seguridad y Líder de Equipo
- **Template**: `new_user_notification`
- **Contenido**: Información del nuevo usuario (nombre, email, rol, equipo, fecha)
- **Código**: `backend/src/users/service.py` - `create_user()`

#### **2. Creación de HPS con Usuario Nuevo**
- **Cuándo**: Al crear una HPS pública que genera un nuevo usuario
- **Quién recibe**: El usuario recién creado
- **Template**: `user_credentials`
- **Contenido**: Credenciales temporales (email, contraseña temporal, URL de login)
- **Código**: `backend/src/hps/router.py` - `create_hps_public()`

#### **3. Monitorización Automática de Estados HPS**
- **Cuándo**: Al detectar correos del gobierno que cambian estados
- **Quién recibe**: El solicitante de la HPS
- **Template**: `status_update`
- **Contenido**: Notificación de cambio de estado (pending → waiting_dps, etc.)
- **Código**: `backend/src/email/hps_monitor.py` - `_send_status_notification()`

### 🎯 **Acciones Manuales (Iniciadas por Usuario)**

#### **4. Envío Manual de Correos**
- **Cuándo**: Cuando un admin/envío manual envía un correo
- **Quién recibe**: Destinatario especificado
- **Templates**: Todos disponibles
- **Endpoint**: `POST /api/v1/email/send`
- **Código**: `backend/src/email/router.py` - `send_email()`

#### **5. Confirmación de Solicitud HPS**
- **Cuándo**: Cuando se envía manualmente confirmación de HPS
- **Quién recibe**: El solicitante de la HPS
- **Template**: `confirmation`
- **Contenido**: Confirmación de recepción de solicitud
- **Endpoint**: `POST /api/v1/email/send-confirmation/{hps_request_id}`
- **Código**: `backend/src/email/router.py` - `send_confirmation_email()`

#### **6. Actualización de Estado HPS**
- **Cuándo**: Cuando se envía manualmente actualización de estado
- **Quién recibe**: El solicitante de la HPS
- **Template**: `status_update`
- **Contenido**: Notificación de cambio de estado
- **Endpoint**: `POST /api/v1/email/send-status-update/{hps_request_id}`
- **Código**: `backend/src/email/router.py` - `send_status_update_email()`

#### **7. Recordatorios de Solicitudes Pendientes**
- **Cuándo**: Cuando se envían manualmente recordatorios
- **Quién recibe**: Usuarios con solicitudes pendientes
- **Template**: `reminder`
- **Contenido**: Recordatorio de solicitud pendiente
- **Endpoint**: `POST /api/v1/email/send-reminders`
- **Código**: `backend/src/email/router.py` - `send_reminder_emails()`

#### **8. Envío de Formularios HPS**
- **Cuándo**: Cuando se envía manualmente un formulario HPS
- **Quién recibe**: El destinatario especificado
- **Template**: `hps_form`
- **Contenido**: Formulario HPS con enlace
- **Endpoint**: `POST /api/v1/email/send-hps-form-async`
- **Código**: `backend/src/email/router.py` - `send_hps_form_email_async()`

### ⏰ **Tareas Automáticas Programadas**

#### **9. Monitorización Diaria de Correos**
- **Cuándo**: Diariamente a las 9:00 AM
- **Qué hace**: Escanea correos del gobierno y actualiza estados
- **Emails enviados**: Notificaciones de cambio de estado
- **Código**: `backend/src/tasks/hps_monitor_tasks.py` - `daily_hps_monitoring_task()`

#### **10. Estadísticas Semanales**
- **Cuándo**: Lunes a las 8:00 AM
- **Qué hace**: Genera estadísticas de monitorización
- **Emails enviados**: Reportes de estadísticas (si se configuran)
- **Código**: `backend/src/tasks/hps_monitor_tasks.py` - `weekly_hps_stats_task()`

## 📊 **Templates de Email Disponibles**

### **Templates Implementados:**
1. **`confirmation`** - Confirmación de solicitud HPS
2. **`status_update`** - Actualización de estado HPS
3. **`reminder`** - Recordatorio de solicitudes pendientes
4. **`new_user_notification`** - Notificación de nuevo usuario
5. **`user_credentials`** - Credenciales de usuario
6. **`hps_form`** - Formulario HPS
7. **`hps_approved`** - HPS aprobada
8. **`hps_rejected`** - HPS rechazada

### **Templates Pendientes de Migración:**
- `auto_reply` - Respuesta automática
- `notification` - Notificación general

## 🔄 **Flujo de Emails por Acción**

### **Flujo 1: Nuevo Usuario**
```
Usuario creado → Notificar jefes → Email a jefes de seguridad y líder de equipo
```

### **Flujo 2: HPS Pública con Usuario Nuevo**
```
HPS creada → Usuario nuevo generado → Email credenciales → Email a usuario
```

### **Flujo 3: Cambio de Estado Automático**
```
Correo gobierno → Detectar cambio → Actualizar estado → Notificar usuario
```

### **Flujo 4: Acciones Manuales**
```
Usuario inicia acción → Seleccionar template → Enviar email → Confirmar envío
```

## 🎯 **Destinatarios por Tipo de Email**

### **Jefes de Seguridad y Líderes de Equipo:**
- ✅ Notificaciones de nuevo usuario
- ✅ Reportes de estadísticas

### **Solicitantes de HPS:**
- ✅ Confirmación de solicitud
- ✅ Actualización de estado
- ✅ Recordatorios
- ✅ Credenciales de usuario

### **Usuarios Generales:**
- ✅ Formularios HPS
- ✅ Notificaciones generales

## ⚙️ **Configuración de Envío**

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

### **Emails Automáticos:**
- **Creación de usuario**: 1-3 emails por usuario
- **Monitorización diaria**: Variable según correos del gobierno
- **Estadísticas semanales**: 1 email de reporte

### **Emails Manuales:**
- **Depende del uso** del sistema
- **Sin límite** de envío
- **Controlado por permisos**

## 🔧 **Configuración Técnica**

### **Credenciales de Email:**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=aicoxidi@gmail.com
SMTP_PASSWORD=your_app_password

IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=aicoxidi@gmail.com
IMAP_PASSWORD=your_app_password
```

### **Tareas Celery:**
```python
# Tareas programadas
'daily-hps-monitoring': {
    'task': 'hps_monitor.daily_check',
    'schedule': crontab(hour=9, minute=0),  # Diario 9:00 AM
},
'weekly-hps-stats': {
    'task': 'hps_monitor.weekly_stats',
    'schedule': crontab(hour=8, minute=0, day_of_week=1),  # Lunes 8:00 AM
}
```

## 📝 **Logs y Monitoreo**

### **Logs Generados:**
- ✅ Inicio de envío de emails
- ✅ Destinatarios y templates
- ✅ Resultados de envío
- ✅ Errores y excepciones
- ✅ Estadísticas de procesamiento

### **Métricas Disponibles:**
- Emails enviados por día/semana
- Templates más utilizados
- Errores de envío
- Tiempo de procesamiento

## 🚀 **Estado del Sistema**

### ✅ **Completado:**
- Sistema de emails automáticos
- Templates modulares
- Tareas programadas
- Monitorización de correos
- Notificaciones de usuario

### 🔄 **En Desarrollo:**
- Migración de templates restantes
- Optimización de rendimiento
- Dashboard de estadísticas

### 📋 **Próximos Pasos:**
1. Probar con datos reales
2. Configurar credenciales definitivas
3. Monitorear funcionamiento
4. Agregar más templates según necesidades



