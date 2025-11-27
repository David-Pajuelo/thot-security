# Protocolo de Pruebas Exhaustivo - Sistema HPS

## 📋 Estado de Ejecución
- **Fecha de Ejecución:** ___________
- **Ejecutado por:** ___________
- **Versión del Sistema:** ___________

---

## 1. Preparación del Entorno

### 1.1 Iniciar Servicios
- [ ] `docker-compose up -d`
- [ ] `docker-compose ps` - Verificar que todos estén "healthy"
- [ ] **Resultado:** ✅/❌

### 1.2 Verificar Conectividad
- [ ] `curl http://localhost:3000` - Frontend
- [ ] `curl http://localhost:8001/health` - Backend
- [ ] `curl http://localhost:8000/health` - Agente IA
- [ ] **Resultado:** ✅/❌

## 2. Pruebas de Autenticación

### 2.1 Login de Administrador
**Objetivo:** Verificar login con credenciales de admin
- [ ] Acceder a http://localhost:3000
- [ ] Ingresar email: `admin@hps-system.com`
- [ ] Ingresar password: `admin123`
- [ ] Hacer clic en "Iniciar Sesión"
- [ ] **Resultado:** ✅/❌ - Redirección al Dashboard con usuario autenticado

### 2.2 Verificación de Token
**Objetivo:** Confirmar que el token JWT se genera y valida correctamente
- [ ] Abrir DevTools → Application → Local Storage
- [ ] Verificar que existe `hps_token`
- [ ] Recargar la página
- [ ] **Resultado:** ✅/❌ - Usuario permanece autenticado

### 2.3 Logout
**Objetivo:** Verificar cierre de sesión
- [ ] Hacer clic en el menú de usuario
- [ ] Seleccionar "Cerrar Sesión"
- [ ] **Resultado:** ✅/❌ - Redirección a login, token eliminado

## 3. Pruebas de Gestión de Usuarios

### 3.1 Crear Usuario
**Objetivo:** Crear nuevo jefe de equipo
- [ ] Ir a "Gestión de Usuarios"
- [ ] Hacer clic en "Nuevo Usuario"
- [ ] Completar formulario:
  - [ ] Email: `test@example.com`
  - [ ] Nombre: `Test User`
  - [ ] Apellido: `Testing`
  - [ ] Rol: `Jefe de Equipo`
- [ ] Hacer clic en "Crear Usuario"
- [ ] **Resultado:** ✅/❌ - Usuario creado y visible en la lista

### 3.2 Editar Usuario
**Objetivo:** Modificar datos de usuario existente
- [ ] En la lista de usuarios, hacer clic en "Editar" en el usuario creado
- [ ] Cambiar nombre a "Test User Modified"
- [ ] Guardar cambios
- [ ] **Resultado:** ✅/❌ - Cambios reflejados en la lista

### 3.3 Eliminar Usuario
**Objetivo:** Eliminar usuario (soft delete)
- [ ] Hacer clic en "Eliminar" en el usuario creado
- [ ] Confirmar eliminación
- [ ] Verificar que el usuario no aparece en la lista
- [ ] Activar "Mostrar eliminados" y verificar que aparece marcado como inactivo
- [ ] **Resultado:** ✅/❌ - Usuario eliminado pero conservado en BD

## 4. Pruebas de Chat con Agente IA

### 4.1 Conexión WebSocket
**Objetivo:** Verificar conexión al chat
**Pasos:**
1. Ir a "Chat con Agente IA"
2. Verificar que aparece "Conectado" en la interfaz
3. Abrir DevTools → Network → WS
4. Confirmar conexión WebSocket activa
**Resultado esperado:** Conexión establecida, estado "Conectado"

### 4.2 Envío de Mensajes
**Objetivo:** Probar comunicación bidireccional
**Pasos:**
1. Enviar mensaje: "Hola, necesito ayuda"
2. Verificar que aparece en el chat
3. Esperar respuesta del agente
4. Verificar que la respuesta aparece correctamente
**Resultado esperado:** Mensajes enviados y recibidos correctamente

### 4.3 Comandos del Agente
**Objetivo:** Probar comandos específicos del sistema
**Pasos:**
1. Enviar: "¿Qué comandos tienes disponibles?"
2. Verificar respuesta con lista de comandos
3. Enviar: "dar alta jefe de equipo Juan juan@test.com"
4. Verificar respuesta del comando
**Resultado esperado:** Comandos procesados correctamente

## 5. Pruebas de Monitoreo de Chat

### 5.1 Visualización de Conversaciones
**Objetivo:** Verificar que las conversaciones se registran
**Pasos:**
1. Ir a "Monitoreo Chat IA"
2. Verificar que aparece la conversación del test anterior
3. Hacer clic en "Ver detalles"
4. Verificar que se abre el modal con la conversación completa
**Resultado esperado:** Conversaciones visibles y detalladas

### 5.2 Métricas en Tiempo Real
**Objetivo:** Verificar métricas del sistema
**Pasos:**
1. En la página de monitoreo, verificar:
   - Número de conversaciones activas
   - Total de mensajes
   - Tiempo promedio de respuesta
   - Salud del sistema
**Resultado esperado:** Métricas actualizadas y coherentes

### 5.3 Preguntas Frecuentes
**Objetivo:** Verificar análisis de temas
**Pasos:**
1. En la sección "Preguntas Más Frecuentes"
2. Verificar que aparecen preguntas categorizadas
3. Confirmar que no aparecen palabras sueltas
**Resultado esperado:** Preguntas completas y categorizadas

## 6. Pruebas de Solicitudes HPS

### 6.1 Crear Solicitud HPS
**Objetivo:** Crear nueva solicitud de habilitación
**Pasos:**
1. Ir a "Gestión HPS"
2. Hacer clic en "Nueva Solicitud"
3. Completar formulario:
   - Tipo: "Personal"
   - Descripción: "Solicitud de prueba"
   - Fecha inicio: Fecha actual
4. Guardar solicitud
**Resultado esperado:** Solicitud creada y visible en la lista

### 6.2 Aprobar Solicitud
**Objetivo:** Probar flujo de aprobación
**Pasos:**
1. En la lista de solicitudes, hacer clic en "Aprobar"
2. Confirmar aprobación
3. Verificar cambio de estado
**Resultado esperado:** Estado cambiado a "Aprobada"

### 6.3 Rechazar Solicitud
**Objetivo:** Probar flujo de rechazo
**Pasos:**
1. Crear nueva solicitud
2. Hacer clic en "Rechazar"
3. Ingresar motivo: "Prueba de rechazo"
4. Confirmar rechazo
**Resultado esperado:** Estado cambiado a "Rechazada"

## 7. Pruebas de Persistencia de Sesión

### 7.1 Recarga de Página
**Objetivo:** Verificar que la sesión persiste
**Pasos:**
1. Estar autenticado en cualquier página
2. Recargar la página (F5)
3. Verificar que permanece autenticado
4. Repetir en diferentes páginas (Dashboard, Gestión Usuarios, etc.)
**Resultado esperado:** Sesión mantenida en todas las páginas

### 7.2 Navegación entre Páginas
**Objetivo:** Verificar navegación sin pérdida de sesión
**Pasos:**
1. Navegar entre todas las páginas del menú
2. Verificar que no aparece "Acceso Denegado"
3. Confirmar que el usuario permanece autenticado
**Resultado esperado:** Navegación fluida sin errores

## 8. Pruebas de Rendimiento

### 8.1 Tiempo de Carga
**Objetivo:** Verificar tiempos de respuesta aceptables
**Pasos:**
1. Medir tiempo de carga de cada página principal
2. Verificar que todas cargan en menos de 3 segundos
3. Probar con diferentes cantidades de datos
**Resultado esperado:** Tiempos de carga < 3 segundos

### 8.2 Responsividad
**Objetivo:** Verificar funcionamiento en diferentes tamaños
**Pasos:**
1. Redimensionar ventana del navegador
2. Probar en modo móvil (DevTools)
3. Verificar que la interfaz se adapta correctamente
**Resultado esperado:** Interfaz responsive y funcional

## 9. Pruebas de Seguridad

### 9.1 Acceso No Autorizado
**Objetivo:** Verificar protección de rutas
**Pasos:**
1. Cerrar sesión
2. Intentar acceder directamente a URLs protegidas:
   - http://localhost:3000/dashboard
   - http://localhost:3000/usuarios
   - http://localhost:3000/monitoreo-chat
3. Verificar redirección a login
**Resultado esperado:** Todas las rutas protegidas redirigen a login

### 9.2 Validación de Tokens
**Objetivo:** Verificar que tokens expirados no funcionan
**Pasos:**
1. Modificar token en localStorage a un valor inválido
2. Intentar realizar acciones
3. Verificar que se solicita re-autenticación
**Resultado esperado:** Token inválido detectado y sesión cerrada

## 10. Pruebas de Integridad de Datos

### 10.1 Consistencia de Base de Datos
**Objetivo:** Verificar integridad referencial
**Pasos:**
```bash
docker-compose exec backend python -c "
from src.database.database import get_db
from src.models.user import User
from src.models.chat_conversation import ChatConversation
from src.models.chat_message import ChatMessage

db = next(get_db())
users = db.query(User).count()
conversations = db.query(ChatConversation).count()
messages = db.query(ChatMessage).count()

print(f'Usuarios: {users}')
print(f'Conversaciones: {conversations}')
print(f'Mensajes: {messages}')

# Verificar integridad
invalid_conv = db.query(ChatConversation).filter(
    ~ChatConversation.user_id.in_([str(u.id) for u in db.query(User).all()])
).count()
print(f'Conversaciones inválidas: {invalid_conv}')
"
```
**Resultado esperado:** Sin inconsistencias en la BD

### 10.2 Logs del Sistema
**Objetivo:** Verificar que no hay errores críticos
**Pasos:**
```bash
docker-compose logs backend --tail=50 | grep ERROR
docker-compose logs agente-ia --tail=50 | grep ERROR
docker-compose logs frontend --tail=50 | grep ERROR
```
**Resultado esperado:** Mínimos o ningún error crítico

## 11. Criterios de Aceptación

### ✅ Pruebas Exitosas
- Todas las funcionalidades principales operativas
- Sin errores críticos en logs
- Tiempos de respuesta aceptables
- Datos consistentes en BD
- Sesiones persistentes correctamente
- Seguridad de rutas implementada

### ❌ Criterios de Fallo
- Cualquier funcionalidad principal no funciona
- Errores 500 en el backend
- Pérdida de sesión inesperada
- Datos inconsistentes en BD
- Tiempos de carga > 5 segundos

## 12. Limpieza Post-Pruebas

```bash
# Limpiar datos de prueba
docker-compose exec backend python -c "
from src.database.database import get_db
from src.models.chat_conversation import ChatConversation
from src.models.chat_message import ChatMessage

db = next(get_db())
db.query(ChatMessage).delete()
db.query(ChatConversation).delete()
db.commit()
print('Datos de prueba eliminados')
"

# Verificar limpieza
docker-compose exec backend python -c "
from src.database.database import get_db
from src.models.chat_conversation import ChatConversation
print(f'Conversaciones restantes: {db.query(ChatConversation).count()}')
"
```

## 13. Checklist de Ejecución

### Pre-Pruebas
- [ ] Servicios Docker iniciados y saludables
- [ ] Conectividad verificada
- [ ] Base de datos limpia

### Durante las Pruebas
- [ ] Autenticación funcional
- [ ] Gestión de usuarios operativa
- [ ] Chat con agente IA conectado
- [ ] Monitoreo de chat funcionando
- [ ] Solicitudes HPS procesables
- [ ] Sesiones persistentes
- [ ] Rendimiento aceptable
- [ ] Seguridad implementada
- [ ] Datos consistentes

### Post-Pruebas
- [ ] Datos de prueba eliminados
- [ ] Logs revisados
- [ ] Documentación actualizada

## 14. Notas Adicionales

- **Tiempo estimado:** 2-3 horas para ejecución completa
- **Frecuencia:** Ejecutar antes de cada release
- **Responsable:** Equipo de desarrollo
- **Herramientas:** Navegador, DevTools, Terminal, Docker
