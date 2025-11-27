# 📧 Sistema de Notificaciones de Usuario

## 📋 Descripción

Sistema automatizado para notificar a jefes de seguridad y líderes de equipo cuando se crea un nuevo usuario en el sistema HPS. El sistema envía correos informativos con los detalles del nuevo usuario.

## 🏗️ Arquitectura Implementada

### **Estructura Modular de Templates**
```
backend/src/email/templates/
├── __init__.py                    # Inicialización del módulo
└── new_user_notification.py       # Template de notificación de nuevo usuario
```

### **Servicios Implementados**
```
backend/src/email/
├── user_notification_service.py   # Servicio de notificaciones de usuario
├── service.py                     # Servicio base de email (actualizado)
└── schemas.py                     # Esquemas actualizados
```

## 🔧 Funcionalidades Implementadas

### ✅ **Template Modular**
- **Archivo separado** para cada template
- **Diseño HTML profesional** con estilos CSS
- **Información completa** del nuevo usuario
- **Badges de roles** con colores distintivos
- **Responsive design** para diferentes dispositivos

### ✅ **Servicio de Notificaciones**
- **Detección automática** de destinatarios
- **Jefes de Seguridad**: Siempre notificados
- **Líder de Equipo**: Notificado si el usuario tiene equipo
- **Admins**: Notificados como fallback si no hay otros destinatarios

### ✅ **Integración Automática**
- **Activación automática** al crear usuario
- **No bloquea** la creación si fallan las notificaciones
- **Logs completos** de todas las operaciones
- **Manejo de errores** robusto

## 📧 Destinatarios de Notificación

### **Prioridad de Notificación:**
1. **Jefes de Seguridad** (`jefe_seguridad`) - Siempre notificados
2. **Líder del Equipo** (`team_lead`) - Si el usuario tiene equipo asignado
3. **Admins** (`admin`) - Como fallback si no hay otros destinatarios

### **Información Incluida:**
- **Nombre completo** del nuevo usuario
- **Email** del nuevo usuario
- **Rol asignado** con badge de color
- **Equipo asignado**
- **Fecha de registro**
- **Usuario que lo creó**

## 🎨 Template de Correo

### **Diseño Visual:**
- **Header con gradiente** azul-púrpura
- **Grid de información** organizada
- **Badges de roles** con colores específicos:
  - 🔴 **Admin**: Rojo
  - 🟠 **Jefe Seguridad**: Naranja
  - 🟡 **Crypto**: Amarillo
  - 🔵 **Líder Equipo**: Azul
  - 🟢 **Miembro**: Verde
- **Footer informativo** con disclaimer

### **Contenido del Correo:**
```
Asunto: Nuevo usuario registrado: [Nombre del Usuario]

Estimado/a [Destinatario],

Se ha registrado un nuevo usuario en el sistema HPS:

👤 Información del Nuevo Usuario:
- Nombre: Juan Pérez García
- Email: juan.perez@empresa.com
- Rol: [Badge con color]
- Equipo: Equipo AICOX
- Fecha: 09/10/2025 14:30
- Creado por: Carlos Alonso
```

## 🔄 Flujo de Notificación

```
1. Usuario creado en BD
   ↓
2. Identificar destinatarios
   ├── Jefes de Seguridad
   ├── Líder del Equipo (si aplica)
   └── Admins (fallback)
   ↓
3. Preparar datos del template
   ↓
4. Enviar correos personalizados
   ↓
5. Registrar logs de resultado
```

## 🛠️ Implementación Técnica

### **Integración en UserService:**
```python
def create_user(self, user_data: UserCreate, created_by: User) -> User:
    # ... crear usuario en BD ...
    
    # Enviar notificaciones automáticamente
    try:
        notification_service = UserNotificationService(email_service)
        result = notification_service.notify_new_user(db_user, created_by, self.db)
        logger.info(f"Notificaciones enviadas: {result['notifications_sent']}")
    except Exception as e:
        logger.error(f"Error en notificaciones: {str(e)}")
        # No fallar la creación del usuario
    
    return db_user
```

### **Servicio de Notificaciones:**
```python
class UserNotificationService:
    def notify_new_user(self, new_user: User, created_by: User, db: Session):
        # 1. Obtener destinatarios
        recipients = self._get_notification_recipients(new_user, db)
        
        # 2. Preparar datos del template
        template_data = self._prepare_template_data(new_user, created_by, db)
        
        # 3. Enviar correos personalizados
        for recipient in recipients:
            # Personalizar para cada destinatario
            # Enviar correo
            # Registrar resultado
```

## 📊 Logs y Monitoreo

### **Logs Generados:**
- Inicio de notificaciones
- Destinatarios encontrados
- Correos enviados exitosamente
- Errores de envío
- Estadísticas finales

### **Ejemplo de Logs:**
```
INFO: Iniciando notificaciones para nuevo usuario: juan.perez@empresa.com
INFO: Jefes de seguridad encontrados: 2
INFO: Líder de equipo encontrado: abonacasa@aicox.com
INFO: Total destinatarios para notificación: 3
INFO: Notificación enviada a abonacasa@aicox.com
INFO: Notificaciones enviadas para nuevo usuario juan.perez@empresa.com: 3 correos
```

## 🔧 Configuración

### **Variables de Entorno:**
```env
# SMTP para envío (mantener existente)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=aicoxidi@gmail.com
SMTP_PASSWORD=your_app_password

# IMAP para recepción (mantener existente)
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=aicoxidi@gmail.com
IMAP_PASSWORD=your_app_password
```

### **Credenciales Temporales:**
```python
# TEMPORAL - Usar credenciales compartidas para testeo
SMTP_USER = "aicoxidi@gmail.com"
IMAP_USER = "aicoxidi@gmail.com"
# TODO: Cambiar por credenciales separadas en producción
```

## 🧪 Pruebas

### **Script de Prueba:**
```bash
python Temp/test_user_notifications.py
```

### **Pruebas Incluidas:**
1. **Template de notificación** - Generación de correo
2. **Conexión de email** - Verificación de credenciales
3. **Servicio de notificaciones** - Lógica completa
4. **Base de datos** - Búsqueda de destinatarios

## ⚠️ Consideraciones Importantes

### **No Bloquea Creación:**
- Las notificaciones **no deben fallar** la creación del usuario
- Errores de notificación se registran en logs
- El usuario se crea exitosamente independientemente

### **Destinatarios Inteligentes:**
- **Jefes de Seguridad**: Siempre notificados (máxima prioridad)
- **Líder de Equipo**: Solo si el usuario tiene equipo asignado
- **Admins**: Solo como fallback si no hay otros destinatarios

### **Templates Modulares:**
- **Un archivo por template** para mejor mantenimiento
- **Fácil agregar nuevos templates** sin modificar archivos grandes
- **Reutilización** de componentes comunes

## 🚀 Estado del Sistema

### ✅ **Completado:**
- Sistema de notificaciones implementado
- Templates modulares creados
- Integración automática en creación de usuarios
- Scripts de prueba funcionales
- Documentación completa

### 🔄 **Próximos Pasos:**
1. Probar con usuarios reales
2. Ajustar templates según feedback
3. Configurar credenciales definitivas
4. Monitorear funcionamiento en producción

## 📞 Soporte

Para cualquier duda o problema con el sistema de notificaciones:
- Revisar logs del sistema
- Probar con script de prueba
- Verificar configuración de email
- Consultar documentación en `Temp/user_notification_system.md`



