# 📧 Lista Actualizada de Correos del Sistema HPS

## 🔄 **CORREOS ELIMINADOS**

### ❌ **Confirmación de Solicitud HPS**
- **Razón**: No es necesario confirmar manualmente cada solicitud
- **Impacto**: Reduce trabajo administrativo innecesario
- **Alternativa**: Los usuarios pueden ver el estado en el sistema

## 📋 **LISTA FINAL DE CORREOS (9 tipos)**

### 🔄 **CORREOS AUTOMÁTICOS (2 tipos):**

#### **1. Notificación de Nuevo Usuario**
- **Cuándo se envía**: Al crear un nuevo usuario a través del formulario
- **Quién lo recibe**: Jefes de Seguridad y Líder de Equipo del nuevo miembro
- **Template**: `new_user_notification`
- **Asunto**: `Nuevo usuario registrado: [Nombre]`
- **Código**: `backend/src/users/service.py` - `create_user()`

#### **2. Credenciales de Usuario Nuevo**
- **Cuándo se envía**: Al crear una HPS pública que genera un nuevo usuario
- **Quién lo recibe**: El usuario recién creado
- **Template**: `user_credentials`
- **Asunto**: `Credenciales de acceso - [Nombre]`
- **Código**: `backend/src/hps/router.py` - `create_hps_public()`

### 🎯 **CORREOS MANUALES (5 tipos):**

#### **3. Recordatorio de Solicitudes Pendientes** ⚠️ **MANTENER**
- **Cuándo se envía**: Cuando se envían manualmente recordatorios
- **Quién lo recibe**: Usuarios con solicitudes pendientes
- **Template**: `reminder`
- **Asunto**: `Recordatorio: Solicitud HPS pendiente - [Documento]`
- **Endpoint**: `POST /api/v1/email/send-reminders`
- **Nota**: Se mantiene para el nuevo recordatorio que necesitas

#### **4. Formulario HPS**
- **Cuándo se envía**: Cuando se envía manualmente un formulario HPS
- **Quién lo recibe**: El destinatario especificado
- **Template**: `hps_form`
- **Asunto**: `Formulario HPS - [Nombre]`
- **Endpoint**: `POST /api/v1/email/send-hps-form-async`

#### **5. HPS Aprobada**
- **Cuándo se envía**: Cuando se aprueba una HPS
- **Quién lo recibe**: El solicitante de la HPS
- **Template**: `hps_approved`
- **Asunto**: `HPS Aprobada - [Documento]`
- **Endpoint**: `POST /api/v1/email/send` (manual)

#### **6. HPS Rechazada**
- **Cuándo se envía**: Cuando se rechaza una HPS
- **Quién lo recibe**: El solicitante de la HPS
- **Template**: `hps_rejected`
- **Asunto**: `HPS Rechazada - [Documento]`
- **Endpoint**: `POST /api/v1/email/send` (manual)

#### **7. Envío Manual General**
- **Cuándo se envía**: Cuando se envía manualmente cualquier correo
- **Quién lo recibe**: Destinatario especificado
- **Template**: Cualquier template disponible
- **Asunto**: Personalizable
- **Endpoint**: `POST /api/v1/email/send`

### ⏰ **CORREOS PROGRAMADOS (2 tipos):**

#### **8. Monitorización Diaria de Correos**
- **Cuándo se envía**: Diariamente a las 9:00 AM
- **Qué hace**: Escanea correos del gobierno y actualiza estados
- **Emails generados**: Ninguno (solo procesamiento interno)
- **Código**: `backend/src/tasks/hps_monitor_tasks.py` - `daily_hps_monitoring_task()`

#### **9. Estadísticas Semanales**
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
- ✅ Recordatorios
- ✅ HPS aprobada
- ✅ HPS rechazada

### **Usuarios Generales:**
- ✅ Formularios HPS
- ✅ Notificaciones generales (envío manual)

## 🎨 **Diseño Visual de los Templates**

### **Colores por Tipo de Email:**
- 🟡 **Amarillo**: Recordatorio (atención, urgencia)
- 🟣 **Púrpura**: Notificación de usuario (nuevo, importante)
- 🔴 **Rojo**: Rechazo (alerta, problema)
- 🟢 **Verde**: Aprobación (éxito, finalización)
- 🔵 **Azul**: Formulario HPS (información, proceso)

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
- **Monitorización diaria**: 0 emails (solo procesamiento)

### **Emails Manuales:**
- **Depende del uso** del sistema
- **Sin límite** de envío
- **Controlado por permisos**

## 🚀 **Estado Final del Sistema**

### ✅ **Implementado y Funcionando:**
- Sistema de emails automáticos (2 tipos)
- Templates modulares (5 tipos manuales)
- Envío SMTP verificado
- Integración con backend
- Tareas programadas (2 tipos)
- Pruebas exitosas realizadas

### 📋 **Templates Disponibles:**
1. `new_user_notification` - Notificación de nuevo usuario
2. `user_credentials` - Credenciales de usuario
3. `reminder` - Recordatorio (para el nuevo que necesitas)
4. `hps_form` - Formulario HPS
5. `hps_approved` - HPS aprobada
6. `hps_rejected` - HPS rechazada

### 🔄 **Flujo de Emails por Acción:**

#### **Nuevo Usuario:**
```
Usuario creado → Notificar jefes → Email a jefes de seguridad y líder de equipo
```

#### **HPS Pública con Usuario Nuevo:**
```
HPS creada → Usuario nuevo generado → Email credenciales → Email a usuario
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
  "template": "reminder",
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

El sistema HPS envía **9 tipos diferentes de correos** en total:
- **2 automáticos** (nuevo usuario, credenciales)
- **5 manuales** (recordatorio, formulario, aprobación, rechazo, general)
- **2 programados** (monitorización diaria, estadísticas semanales)

**Total de correos**: 9 tipos
**Sistema de emails**: ✅ **FUNCIONANDO**
**Templates disponibles**: 6 tipos

---

## ⚠️ **PENDIENTE: Nuevo Recordatorio**

El template `reminder` se mantiene para el nuevo recordatorio que necesitas. Por favor, explica cuál será el nuevo recordatorio para implementarlo correctamente.



