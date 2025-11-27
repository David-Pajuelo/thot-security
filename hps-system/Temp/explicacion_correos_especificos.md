# 📧 Explicación de Correos Específicos del Sistema HPS

## 🔍 **1. Confirmación de Solicitud HPS**

### **¿Qué hace este correo?**
Este correo se envía **manualmente** cuando un administrador o jefe de seguridad quiere **confirmar al solicitante** que su solicitud HPS ha sido recibida y está siendo procesada.

### **¿Cuándo se envía?**
- **Acción manual** del administrador/jefe de seguridad
- **Después** de que el usuario haya enviado su solicitud HPS
- **Para tranquilizar** al solicitante de que su trámite está en proceso

### **¿Quién lo envía?**
- **Administradores** del sistema
- **Jefes de seguridad** 
- **Líderes de equipo** (según permisos)

### **¿Quién lo recibe?**
- **El solicitante** de la HPS (la persona que envió la solicitud)

### **¿Qué contiene?**
```
Asunto: "Confirmación de solicitud HPS - 12345678A"

Contenido:
- Mensaje de confirmación de recepción
- Detalles de la solicitud:
  * Número de documento
  * Tipo de solicitud (nueva, renovación, traslado)
  * Estado actual (pending)
  * ID de solicitud
  * Fecha de solicitud
- Información sobre próximos pasos
- Contacto para consultas
```

### **¿Para qué sirve?**
- **Tranquilizar** al solicitante
- **Confirmar** que la solicitud llegó correctamente
- **Proporcionar** información de seguimiento
- **Establecer** comunicación oficial

### **Ejemplo de uso:**
```
Usuario envía HPS → Administrador revisa → Administrador envía confirmación → Solicitante recibe confirmación
```

---

## ⏰ **2. Recordatorio de Solicitudes Pendientes**

### **¿Qué hace este correo?**
Este correo se envía **manualmente** para **recordar a los usuarios** que tienen solicitudes HPS que llevan tiempo pendientes y requieren acción.

### **¿Cuándo se envía?**
- **Acción manual** del administrador/jefe de seguridad
- **Cuando hay solicitudes** que llevan varios días pendientes
- **Para acelerar** el proceso de solicitudes olvidadas

### **¿Quién lo envía?**
- **Administradores** del sistema
- **Jefes de seguridad**
- **Líderes de equipo**

### **¿Quién lo recibe?**
- **Usuarios con solicitudes pendientes** (solicitantes de HPS)

### **¿Qué contiene?**
```
Asunto: "Recordatorio: Solicitud HPS pendiente - 11223344C"

Contenido:
- Mensaje de recordatorio
- Detalles de la solicitud pendiente:
  * Número de documento
  * Tipo de solicitud
  * Estado actual (pending)
  * Fecha de solicitud
  * Días transcurridos
  * ID de solicitud
- Acciones requeridas
- Enlaces de acceso
- Información de contacto
```

### **¿Para qué sirve?**
- **Recordar** a los usuarios sobre solicitudes olvidadas
- **Acelerar** el proceso de solicitudes pendientes
- **Reducir** el tiempo de procesamiento
- **Mejorar** la comunicación con solicitantes

### **Ejemplo de uso:**
```
Solicitud pendiente 4 días → Administrador envía recordatorio → Usuario recibe recordatorio → Usuario completa acción
```

---

## 🔄 **Actualización de la Lista de Correos**

### **CORREOS ELIMINADOS:**

#### ❌ **Notificación Automática de Cambio de Estado HPS**
- **Razón**: No es necesario notificar a usuarios sobre modificaciones
- **Impacto**: Reduce spam y mejora experiencia del usuario
- **Alternativa**: Los usuarios pueden consultar el estado en el sistema

### **CORREOS MANTENIDOS:**

#### ✅ **Confirmación de Solicitud HPS** (Manual)
- **Propósito**: Confirmar recepción de solicitud
- **Cuándo**: Después de recibir solicitud
- **Beneficio**: Tranquiliza al solicitante

#### ✅ **Recordatorio de Solicitudes Pendientes** (Manual)
- **Propósito**: Recordar solicitudes olvidadas
- **Cuándo**: Cuando hay solicitudes pendientes
- **Beneficio**: Acelera el proceso

---

## 📊 **Lista Actualizada de Correos**

### **CORREOS AUTOMÁTICOS (2 tipos):**
1. **Notificación de Nuevo Usuario** - A jefes de seguridad
2. **Credenciales de Usuario Nuevo** - A usuario recién creado

### **CORREOS MANUALES (6 tipos):**
3. **Confirmación de Solicitud HPS** - A solicitante
4. **Recordatorio de Solicitudes Pendientes** - A solicitantes pendientes
5. **Formulario HPS** - A destinatario especificado
6. **HPS Aprobada** - A solicitante
7. **HPS Rechazada** - A solicitante
8. **Envío Manual General** - A destinatario especificado

### **CORREOS PROGRAMADOS (2 tipos):**
9. **Monitorización Diaria** - Escanea correos del gobierno
10. **Estadísticas Semanales** - A administradores

---

## 🎯 **Flujo de Trabajo Actualizado**

### **Flujo de Confirmación:**
```
Usuario envía HPS → Administrador revisa → Administrador envía confirmación → Solicitante recibe confirmación
```

### **Flujo de Recordatorio:**
```
Solicitud pendiente → Administrador identifica → Administrador envía recordatorio → Usuario recibe recordatorio
```

### **Flujo de Nuevo Usuario:**
```
Usuario creado → Sistema envía notificación → Jefes reciben notificación
```

---

## 🔧 **Configuración Técnica**

### **Endpoints Disponibles:**
- `POST /api/v1/email/send-confirmation/{hps_request_id}` - Confirmación
- `POST /api/v1/email/send-reminders` - Recordatorios
- `POST /api/v1/email/send` - Envío manual general

### **Permisos Requeridos:**
- **Confirmación**: Admin, Jefe Seguridad, Líder Equipo
- **Recordatorio**: Admin, Jefe Seguridad, Líder Equipo
- **Envío Manual**: Admin, Jefe Seguridad, Líder Equipo

---

## 📈 **Beneficios de la Actualización**

### **Ventajas de Eliminar Notificaciones Automáticas:**
- ✅ **Menos spam** para usuarios
- ✅ **Mejor experiencia** del usuario
- ✅ **Reducción** de correos innecesarios
- ✅ **Enfoque** en correos importantes

### **Ventajas de Mantener Confirmación y Recordatorio:**
- ✅ **Confirmación** tranquiliza al solicitante
- ✅ **Recordatorio** acelera procesos pendientes
- ✅ **Control manual** sobre cuándo enviar
- ✅ **Flexibilidad** en la comunicación

---

## 🚀 **Estado Final del Sistema**

### **Total de Correos**: **10 tipos**
- **2 automáticos** (nuevo usuario, credenciales)
- **6 manuales** (confirmación, recordatorio, formulario, aprobación, rechazo, general)
- **2 programados** (monitorización, estadísticas)

### **Sistema Optimizado**:
- ✅ **Menos correos automáticos**
- ✅ **Mejor control manual**
- ✅ **Enfoque en correos importantes**
- ✅ **Experiencia de usuario mejorada**



