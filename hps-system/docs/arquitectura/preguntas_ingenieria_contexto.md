# 📋 Documento de Ingeniería de Contexto - Sistema HPS con Streamlit

## 🎯 **Descripción del Proyecto**
Sistema web basado en Streamlit con gestión de usuarios, agente conversacional y formularios HPS (Habilitación Personal de Seguridad), desplegado en contenedores Docker con base de datos PostgreSQL y agente IA independiente.

---

## 🏗️ **Arquitectura General del Sistema**

### Contenedores y Orquestación
- [x] **PostgreSQL**: Versión 15 (LTS) - estable y con buen rendimiento
- [x] **Arquitectura**: Multi-contenedor: Base de datos, Streamlit, Agente IA y Redis separados
- [x] **Persistencia**: Volúmenes Docker para persistencia de datos
- [x] **Logs**: Cada servicio maneja sus logs por separado (no centralizado)
- [x] **Orquestación**: Docker Compose para simplicidad y facilidad de despliegue
- [x] **Redis**: Necesario para sesiones de usuario y cache de Streamlit
- [x] **Recursos**: PostgreSQL (2GB RAM, 1 CPU) | Streamlit (1GB RAM, 1 CPU) | Agente IA (2GB RAM, 1 CPU) | Redis (512MB RAM, 0.5 CPU)

### Redes y Comunicación
- [x] **Comunicación interna**: Red Docker interna para comunicación entre servicios
- [x] **Puertos**: Estándar de cada servicio (PostgreSQL: 5432, Streamlit: 8501, Redis: 6379)
- [x] **Proxy reverso**: Nginx en contenedor separado delante de Streamlit

---

## 🔐 **Sistema de Autenticación y Autorización**

### Métodos de Autenticación
- [x] **Método**: JWT (JSON Web Tokens) - robusto, seguro y minimalista
- [x] **Integración externa**: No se requiere LDAP/Active Directory por ahora
- [x] **Almacenamiento**: Credenciales en base de datos PostgreSQL

### Políticas de Seguridad
- [x] **Contraseñas**: Longitud mínima 8 caracteres, complejidad media, expiración 90 días
- [x] **2FA**: No requerido para MVP
- [x] **Sesión**: Timeout de 8 horas de inactividad
- [x] **Bloqueo**: 5 intentos fallidos bloquean cuenta por 30 minutos
- [x] **Encriptación**: Hash bcrypt con salt para contraseñas

---

## 👥 **Gestión de Usuarios y Roles**

### Estructura de Roles
- [x] **Administrador/Jefe de Seguridad**: Acceso total a todos los HPS de todos los equipos
- [x] **Jefe de Equipo**: Solo puede ver HPS de su equipo
- [x] **Usuario del Equipo**: Solo puede ver su propio HPS

### Organización de Equipos
- [x] **Múltiples equipos**: Los usuarios pueden pertenecer a varios equipos o cambiar entre ellos
- [x] **Jerarquía**: Sistema de equipos anidados (equipos dentro de equipos)
- [x] **Información usuario**: Todos los campos del formulario HPS + campos de sistema
- [x] **Campos adicionales**: Nombre completo, teléfono, departamento, fecha alta, estado activo/inactivo

### Gestión de Usuarios
- [x] **Perfil**: Los usuarios NO pueden cambiar su información de perfil
- [x] **Cambios de rol**: No se requiere sistema de aprobación
- [x] **Cambio de equipo**: Solo jefe de equipo o jefe de seguridad, con notificación por email
- [x] **Invitaciones**: Sistema de invitaciones por email para nuevos usuarios

---

## 💬 **Sistema de Chat y Agente Conversacional**

### Tipo de Agente
- [x] **Tecnología**: API externa OpenAI (GPT-4o-mini)
- [x] **Memoria**: Sí, memoria de conversaciones anteriores
- [x] **Acceso BD**: Acceso en tiempo real a la base de datos

### Funcionalidades del Chat
- [x] **Historial**: Una sola conversación por usuario (no múltiples conversaciones)
- [x] **Acceso usuario**: El agente accede a información específica del usuario que chatea
- [x] **Comandos implementados**: 6 comandos principales del sistema

### Comandos del Agente
- [x] **Dar alta jefe equipo**: Jefe de seguridad solicita alta con email, se crea en BD y se notifica
- [x] **Solicitar HPS**: Verifica si usuario existe, si no lo crea y envía formulario por email
- [x] **Renovación HPS**: Cambia estado y envía formulario de datos
- [x] **Traslado HPS**: Envía formulario y guarda como traslado
- [x] **Consultar estado HPS usuario**: Muestra estado del HPS del usuario
- [x] **Consultar estado HPS equipo**: Lista todos los estados HPS del equipo

---

## 📝 **Sistema de Formularios HPS**

### Estructura del Formulario
- [x] **Campos**: 11 campos obligatorios del formulario HPS
- [x] **Validación tiempo real**: No requerido para MVP
- [x] **Edición**: No editable después de envío
- [x] **Versionado**: No requerido para MVP

### Tipos de Datos
- [x] **Archivos adjuntos**: Ninguno
- [x] **Campos específicos**: Dropdowns, texto, fecha, email, teléfono
- [x] **Obligatorios**: Todos los campos son obligatorios
- [x] **Validación**: Formato email, teléfono y otros campos

### Flujo de Trabajo
- [x] **Aprobación**: Envío directo sin proceso de aprobación
- [x] **Notificaciones**: Sí, al jefe de equipo y jefes de seguridad
- [x] **Borradores**: No se pueden guardar borradores

---

## 📧 **Sistema de Notificaciones por Email**

### Proveedor de Email
- [x] **Proveedor**: SMTP propio
- [x] **Plantillas**: Plantillas básicas personalizables
- [x] **Credenciales**: Enlace a la aplicación para crear/actualizar contraseña

### Tipos de Notificaciones
- [x] **Alta usuario**: Enlace para cambio/creación de contraseña
- [x] **Solicitud HPS**: Enlace directo al formulario
- [x] **Recordatorios**: Automáticos para HPS vencidos

---

## 🗄️ **Base de Datos y Persistencia**

### Esquema de Base de Datos
- [x] **Tablas principales**: usuarios, equipos, hps, roles, sesiones, auditoria
- [x] **Auditoría**: Logs de cambios (quién, qué, cuándo)
- [x] **Índices**: Optimización para consultas por email, equipo, estado HPS

### Gestión de Datos
- [x] **Backup**: Automático diario con retención de 30 días
- [x] **Retención**: Datos HPS por 5 años, logs por 1 año
- [x] **Exportación**: CSV y Excel para reportes básicos
- [x] **Limpieza**: Automática de datos antiguos según políticas

### Seguridad de Datos
- [x] **Encriptación**: Datos sensibles encriptados en reposo
- [x] **Cumplimiento**: GDPR básico para datos personales
- [x] **Auditoría**: Logs de todas las acciones de usuarios

---

## 🚀 **Despliegue y Operaciones**

### Entorno de Despliegue
- [x] **Entorno**: Servidor interno con Docker
- [x] **CI/CD**: No requerido para MVP
- [x] **Puertos**: Estándar de cada servicio

### Configuración y Variables de Entorno
- [x] **Variables**: Configuración de BD, OpenAI API, SMTP, secretos
- [x] **Entornos**: Desarrollo y producción separados
- [x] **Secretos**: Variables de entorno para credenciales sensibles

### Monitoreo y Logs
- [x] **Salud servicios**: Monitoreo básico de estado de contenedores
- [x] **Logging**: Nivel INFO por defecto, ERROR para producción
- [x] **Formato**: Logs estructurados en formato JSON

---

## 🔒 **Seguridad y Cumplimiento**

### Encriptación y Protección
- [x] **HTTPS/TLS**: Certificado SSL para comunicación segura
- [x] **Hash contraseñas**: bcrypt con salt de 12 rounds
- [x] **Datos en reposo**: Encriptación AES-256 para datos sensibles

### Auditoría y Cumplimiento
- [x] **Logs auditoría**: Todas las acciones de usuarios registradas
- [x] **Backup/recuperación**: Backup diario con recuperación en 4 horas
- [x] **Cumplimiento**: GDPR básico, preparado para ISO 27001

### Control de Acceso
- [x] **Control IP**: No requerido para MVP
- [x] **Timeout sesión**: 8 horas de inactividad
- [x] **Blacklist/whitelist**: No requerido para MVP

---

## 📱 **Interfaz de Usuario**

### Diseño y Experiencia
- [x] **Responsive**: Sí, móvil y escritorio
- [x] **Temas**: Claro y oscuro
- [x] **Idiomas**: Solo español (no internacionalización)

### Componentes y Visualizaciones
- [x] **Gráficos**: Básicos para estadísticas de HPS
- [x] **Tablas**: Con paginación, filtros y ordenamiento básicos
- [x] **Dashboard**: Widgets simples para información clave
- [x] **Exportación**: CSV y Excel desde la interfaz

### Navegación
- [x] **Navegación**: Menú lateral simple
- [x] **Breadcrumbs**: No requerido para MVP
- [x] **Header**: Información básica del usuario y logout

---

## 🔄 **Integración con N8N**

- [x] **Decisión**: Eliminada integración con N8N
- [x] **Alternativa**: Agente IA implementado como servicio independiente
- [x] **Beneficio**: Mayor control y simplicidad en la arquitectura

---

## 📊 **Monitoreo y Analytics**

- [x] **Métricas**: Básicas de uso para MVP
- [x] **Reportes**: Simples de estado HPS y usuarios
- [x] **Dashboard admin**: Estadísticas básicas de la aplicación
- [x] **Funcionalidades avanzadas**: Para versiones posteriores

---

## 🧪 **Testing y Calidad**

- [x] **Tests unitarios**: Básicos para funciones principales
- [x] **Tests integración**: Para base de datos
- [x] **Tests E2E**: No requeridos para MVP
- [x] **Enfoque**: Testing incremental durante desarrollo

---

## 📚 **Documentación y Mantenimiento**

- [x] **Documentación**: README, API docs, manual usuario
- [x] **Diagramas**: Arquitectura y flujos de trabajo
- [x] **Despliegue**: Documentación completa de operaciones
- [x] **Mantenimiento**: Plan preventivo y procedimientos de backup
- [x] **SLA**: 8x5, resolución siguiente día laborable

---

## ⏱️ **Cronograma y Prioridades**

### Fases de Desarrollo
- [x] **Fase 1 (MVP)**: Autenticación, usuarios básicos, formulario HPS, agente IA
- [x] **Fase 2**: Reportes avanzados, dashboard admin, validaciones mejoradas
- [x] **Fase 3**: Analytics, monitoreo avanzado, integraciones externas

### Funcionalidades Críticas MVP
- [x] Sistema de autenticación JWT
- [x] Gestión de usuarios y roles
- [x] Formulario HPS funcional
- [x] Agente conversacional básico
- [x] Sistema de notificaciones por email
- [x] Base de datos con persistencia

### Funcionalidades Posteriores
- [x] Reportes avanzados y analytics
- [x] Dashboard administrativo completo
- [x] Sistema de auditoría avanzado
- [x] Integraciones con sistemas externos
- [x] Testing automatizado completo

---

## 🎯 **Conclusiones Finales**

### Arquitectura Definida
- **Sistema multi-contenedor** con Docker Compose
- **PostgreSQL 15** como base de datos principal
- **Redis** para sesiones y cache
- **Streamlit** como interfaz web principal
- **Agente IA independiente** con OpenAI
- **Nginx** como proxy reverso

### Tecnologías Seleccionadas
- **Backend**: Python/Streamlit con autenticación JWT
- **Base de datos**: PostgreSQL con encriptación
- **Cache/Sesiones**: Redis
- **IA**: OpenAI GPT-4o-mini
- **Contenedores**: Docker con volúmenes persistentes
- **Proxy**: Nginx para SSL y balanceo

### Seguridad Implementada
- **Autenticación JWT** con timeout configurable
- **Encriptación bcrypt** para contraseñas
- **HTTPS/TLS** obligatorio
- **Logs de auditoría** completos
- **Control de acceso** basado en roles
- **Backup automático** con encriptación

### Escalabilidad y Mantenimiento
- **Arquitectura modular** para fácil escalado
- **Logs separados** por servicio
- **Monitoreo básico** de salud de servicios
- **Documentación completa** para operaciones
- **SLA definido** para soporte

---

## 📋 **Próximos Pasos**

1. **Crear plan de implementación detallado** con tareas y subtareas
2. **Desarrollar MVP** siguiendo la arquitectura definida
3. **Implementar testing incremental** durante el desarrollo
4. **Documentar procesos** de despliegue y operación
5. **Preparar entorno de producción** con todas las configuraciones de seguridad

---

**✅ Estado**: Documento de ingeniería de contexto COMPLETADO  
**📅 Fecha**: Diciembre 2024  
**🎯 Objetivo**: MVP funcional con arquitectura escalable y segura
