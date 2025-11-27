# Protocolo de Pruebas Visuales Manuales - Sistema HPS

## 📋 Estado de Ejecución
- **Fecha de Ejecución:** ___________
- **Ejecutado por:** ___________
- **Versión del Sistema:** ___________
- **Tiempo Total:** ___________

---

## 🎯 Objetivo
Este protocolo está diseñado para ser ejecutado **después** de completar las pruebas programáticas. Se enfoca en la experiencia visual del usuario y la funcionalidad de la interfaz.

---

## 1. Preparación del Entorno Visual

### 1.1 Verificación de Servicios
- [X] Abrir navegador web (Chrome/Firefox/Edge)
- [X] Navegar a http://localhost:3000
- [X] Verificar que la página carga completamente
- [X] Verificar que no hay errores en la consola del navegador (F12)
- [X] **Resultado:** ✅/❌ - Interfaz carga sin errores

### 1.2 Verificación de Responsividad
- [X] Redimensionar ventana del navegador
- [X] Probar en modo móvil (F12 → Device Toolbar)
- [X] Verificar que la interfaz se adapta correctamente
- [X] **Resultado:** ✅/❌ - Interfaz responsive

---

## 2. Pruebas de Autenticación Visual

### 2.1 Pantalla de Login
- [X] Verificar que aparece la pantalla de login
- [X] Verificar que los campos de email y password están visibles
- [X] Verificar que el botón "Iniciar Sesión" está presente
- [X] Verificar que no hay elementos rotos o mal alineados
- [X] **Resultado:** ✅/❌ - Pantalla de login correcta

### 2.2 Proceso de Login
- [X] Ingresar email: `admin@hps-system.com`
- [X] Ingresar password: `admin123`
- [X] Hacer clic en "Iniciar Sesión"
- [X] Verificar que aparece un indicador de carga
- [X] Verificar que se redirige al Dashboard
- [X] **Resultado:** ✅/❌ - Login exitoso y redirección correcta

### 2.3 Verificación de Sesión
- [X] Verificar que aparece el nombre del usuario en la interfaz
- [X] Verificar que aparece el rol del usuario
- [X] Verificar que el menú de navegación está visible
- [X] Verificar que no aparece "Acceso Denegado"
- [X] **Resultado:** ✅/❌ - Sesión establecida correctamente

---

## 3. Pruebas del Dashboard

### 3.1 Visualización del Dashboard
- [X] Verificar que aparece el Dashboard principal
- [X] Verificar que las tarjetas de estadísticas están visibles
- [X] Verificar que los gráficos se renderizan correctamente
- [X] Verificar que no hay elementos superpuestos
- [X] **Resultado:** ✅/❌ - Dashboard se muestra correctamente

### 3.2 Navegación del Menú
- [X] Hacer clic en cada elemento del menú:
  - [X] Dashboard
  - [X] Gestión de Usuarios
  - [X] Gestión HPS
  - [X] Chat con Agente IA
  - [X] Monitoreo Chat IA
- [X] Verificar que cada página carga correctamente
- 
- [X] Verificar que el nombre de la página aparece en la navegación superior
- [X] Verificar que se puede regresar al Dashboard desde cualquier página
- [X] Verificar que el botón "Volver al Dashboard" está en la misma ubicación en todas las páginas
- [X] **Resultado:** ✅ - Navegación funciona correctamente y es consistente

---

## 4. Pruebas de Gestión de Usuarios

### 4.1 Lista de Usuarios
- [X] Ir a "Gestión de Usuarios"
- [X] Verificar que aparece la lista de usuarios
- [X] Verificar que cada usuario muestra:
  - [X] Email
  - [X] Nombre completo (corregido: ahora muestra full_name)
  - [X] Rol
  - [X] Estado (activo/inactivo)
- [X] Verificar que los botones de acción están visibles:
  - [X] Botón "Ver detalles" (ojo)
  - [X] Botón "Generar Token HPS" (enlace)
  - [X] Botón "Editar" (lápiz)
  - [X] Botón "Eliminar" (papelera) para usuarios activos
  - [X] Botón "Activar" (flecha circular) para usuarios inactivos
- [X] **Resultado:** ✅ - Lista de usuarios correcta

### 4.2 Activar/Desactivar Usuario
- [X] **Activar usuario inactivo:**
  - [X] Verificar que usuarios inactivos muestran botón "Activar" (flecha circular verde)
  - [X] Hacer clic en "Activar" en un usuario inactivo
  - [X] Confirmar en el diálogo de confirmación
  - [X] Verificar que aparece mensaje de éxito
  - [X] Verificar que el usuario ahora aparece como activo
  - [X] Verificar que el botón cambia a "Eliminar" (papelera roja)
- [X] **Desactivar usuario activo:**
  - [X] Hacer clic en "Eliminar" en un usuario activo
  - [X] Confirmar en el diálogo de confirmación
  - [X] Verificar que aparece mensaje de éxito con detalles de eliminación
  - [X] Verificar que el usuario ahora aparece como inactivo
  - [X] Verificar que el botón cambia a "Activar" (flecha circular verde)
- [X] **Resultado:** ✅ - Funcionalidad de activar/desactivar funciona correctamente

### 4.3 Modal de Detalles del Usuario
- [X] **Diseño del modal:**
  - [X] Verificar que el modal tiene un diseño moderno y profesional
  - [X] Verificar que tiene header con gradiente y avatar del usuario
  - [X] Verificar que la información está organizada en dos columnas
  - [X] Verificar que cada campo tiene iconos temáticos
- [X] **Información mostrada:**
  - [X] Verificar que el rol se muestra correctamente (corregido: ahora muestra el valor del rol)
  - [X] Verificar que el equipo se muestra correctamente (corregido: ahora muestra "AICOX" en lugar de "Sin equipo")
  - [X] Verificar que el estado se muestra con badge de color
  - [X] Verificar que las fechas se formatean correctamente
  - [X] Verificar que la lista de usuarios también muestra equipos correctamente (corregido: UserListResponse ahora usa UserDetailResponse)
- [X] **Resultado:** ✅ - Modal de detalles funciona correctamente y muestra toda la información
- [X] **Nota:** ✅ - Después de refrescar la página (F5), el modal ahora muestra "AICOX" correctamente
- [X] **Último Acceso:** ✅ - Campo "Último Acceso" ahora se actualiza correctamente cuando los usuarios inician sesión

### 4.4 Crear Usuario
- [X] Hacer clic en "Nuevo Usuario"
- [X] Verificar que aparece el formulario modal
- [X] Completar formulario:
  - [X] Email: `test.visual@example.com`
  - [X] Nombre: `Test Visual Usuario`
  - [X] Rol: `member` (o cualquier otro rol)
- [X] Hacer clic en "Crear Usuario"
- [X] Verificar que aparece mensaje de éxito
- [X] Verificar que el usuario aparece en la lista
- [X] **Resultado:** ✅ - Usuario creado exitosamente
- [X] **Nota:** ✅ - Corregidos todos los errores de creación (Network Error, roles, atributos)

### 4.5 Editar Usuario
- [X] Hacer clic en "Editar" en el usuario creado
- [X] Verificar que aparece el formulario con datos prellenados
- [X] Cambiar nombre a "Test Visual Modificado"
- [X] Hacer clic en "Guardar"
- [X] Verificar que aparece mensaje de éxito
- [X] Verificar que los cambios se reflejan en la lista
- [X] **Resultado:** ✅ - Usuario editado exitosamente
- [X] **Nota:** ✅ - Corregido problema de visualización del rol en el modal de edición
- [X] **Nota:** ✅ - Corregido problema de "Sin Apellido" en la edición de usuarios

### 4.6 Eliminar Usuario
- [X] Hacer clic en "Eliminar" en el usuario creado
- [X] Verificar que aparece confirmación de eliminación
- [X] Hacer clic en "Confirmar"
- [X] Verificar que aparece mensaje de éxito
- [X] Verificar que el usuario desaparece de la lista
- [X] Activar "Mostrar eliminados"
- [X] Verificar que el usuario aparece marcado como inactivo
- [X] **Resultado:** ✅ - Usuario eliminado correctamente
- [X] **Nota:** ✅ - UX mejorada con modales profesionales en lugar de alertas nativas

---

## 5. Pruebas de Chat con Agente IA

### 5.1 Interfaz de Chat
- [X] Ir a "Chat con Agente IA"
- [X] Verificar que aparece la interfaz de chat
- [X] Verificar que aparece "Conectado" en la parte superior
- [X] Verificar que el área de mensajes está visible
- [X] Verificar que el campo de entrada está visible
- [X] **Resultado:** ✅/❌ - Interfaz de chat correcta

### 5.2 Envío de Mensajes
- [X] Escribir mensaje: "Hola, necesito ayuda"
- [X] Hacer clic en "Enviar" o presionar Enter
- [X] Verificar que el mensaje aparece en el chat
- [X] Verificar que aparece indicador de "Escribiendo..."
- [X] Esperar respuesta del agente
- [X] Verificar que la respuesta aparece correctamente
- [X] **Resultado:** ✅/❌ - Mensajes enviados y recibidos

### 5.3 Comandos del Agente
- [X] Enviar: "¿Qué comandos tienes disponibles?"
- [X] Verificar que el agente responde con lista de comandos
- [X] Enviar: "dar alta jefe de equipo Juan juan@test.com AICOX"
- [X] Verificar que el agente procesa el comando
- [X] Verificar que aparece confirmación del comando
- [X] Enviar: "hps de mi equipo"
- [X] Verificar que el agente muestra HPS del equipo (admin ve todas, team_lead solo su equipo)
- [X] Enviar: "pide un hps para abonacasa@aicox.com"
- [X] Verificar que el agente genera URL de solicitud HPS
- [X] Enviar: "en que estado esta la HPS de carlos.alonso@techex.es"
- [X] Verificar que el agente consulta estado de HPS específica
- [X] **Resultado:** ✅ - Comandos procesados correctamente
- [X] **Nota:** ✅ - Corregido error de rol 'team_leader' → 'team_lead'
- [X] **Nota:** ✅ - Mejorado comando para incluir especificación de equipo
- [X] **Nota:** ✅ - Corregido reconocimiento de comandos naturales
- [X] **Nota:** ✅ - Corregidos errores de consola del navegador

---

## 6. Pruebas de Comandos del Agente IA (Sesión Actual)

ado los test 

### 6.2 Comandos de Gestión de Usuarios
- [X] **Comando:** "dar alta jefe de equipo Maria maria@test.com AICOX"
- [X] **Ejemplo:** "Necesito dar de alta un jefe de equipo llamado Maria con email maria@test.com en el equipo AICOX"
- [ ] **Resultado esperado:** Usuario creado exitosamente como jefe de equipo
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "crear jefe de equipo Pedro pedro@test.com IDI"
- [ ] **Ejemplo:** "Crear jefe de equipo Pedro pedro@test.com IDI"
- [ ] **Resultado esperado:** Usuario creado exitosamente como jefe de equipo del equipo IDI
- [ ] **Estado:** ⏳ Pendiente
- [ ] **Nota:** ❌ **BUG IDENTIFICADO:** El agente creaba usuarios en AICOX aunque se especificara IDI. ✅ **CORREGIDO:** Añadido ejemplo específico para "crear jefe de equipo" con equipo IDI.

- [ ] **Comando:** "nuevo jefe de equipo Ana ana@test.com AICOX"
- [ ] **Ejemplo:** "Quiero un nuevo jefe de equipo Ana ana@test.com AICOX"
- [ ] **Resultado esperado:** Usuario creado exitosamente como jefe de equipo
- [ ] **Estado:** ⏳ Pendiente

### 6.3 Comandos de Solicitud de HPS
- [ ] **Comando:** "solicitar hps para test@example.com"
- [ ] **Ejemplo:** "Necesito solicitar una HPS para test@example.com"
- [ ] **Resultado esperado:** URL de solicitud HPS generada
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "quiero solicitar hps para usuario@test.com"
- [ ] **Ejemplo:** "Quiero solicitar hps para usuario@test.com"
- [ ] **Resultado esperado:** URL de solicitud HPS generada
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "generar hps para nuevo@test.com"
- [ ] **Ejemplo:** "Genera una HPS para nuevo@test.com"
- [ ] **Resultado esperado:** URL de solicitud HPS generada
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "crear hps para empleado@test.com"
- [ ] **Ejemplo:** "Crear hps para empleado@test.com"
- [ ] **Resultado esperado:** URL de solicitud HPS generada
- [ ] **Estado:** ⏳ Pendiente

### 6.4 Comandos de Consulta de Estado de HPS
- [ ] **Comando:** "estado hps de carlos.alonso@techex.es"
- [ ] **Ejemplo:** "¿Cuál es el estado hps de carlos.alonso@techex.es?"
- [ ] **Resultado esperado:** Estado actual de la HPS del usuario
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "en que estado esta la HPS de admin@hps-system.com"
- [ ] **Ejemplo:** "En qué estado está la HPS de admin@hps-system.com"
- [ ] **Resultado esperado:** Estado de HPS del usuario admin
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "cual es el estado de la hps de test@example.com"
- [ ] **Ejemplo:** "¿Cuál es el estado de la hps de test@example.com?"
- [ ] **Resultado esperado:** Estado de HPS del usuario
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "como esta la hps de usuario@test.com"
- [ ] **Ejemplo:** "¿Cómo está la hps de usuario@test.com?"
- [ ] **Resultado esperado:** Estado de HPS del usuario
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "mi estado hps"
- [ ] **Ejemplo:** "¿Cuál es mi estado hps?"
- [ ] **Resultado esperado:** Estado de HPS del usuario actual
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "consultar hps de empleado@test.com"
- [ ] **Ejemplo:** "Quiero consultar la hps de empleado@test.com"
- [ ] **Resultado esperado:** Estado de HPS del usuario
- [ ] **Estado:** ⏳ Pendiente

### 6.5 Comandos de HPS del Equipo
- [ ] **Comando:** "hps de mi equipo"
- [ ] **Ejemplo:** "¿Cuáles son las hps de mi equipo?"
- [ ] **Resultado esperado:** Muestra HPS del equipo (admin ve todas, team_lead solo su equipo)
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "hps del equipo"
- [ ] **Ejemplo:** "Muéstrame las hps del equipo"
- [ ] **Resultado esperado:** Muestra HPS del equipo
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "dame las hps de mi equipo"
- [ ] **Ejemplo:** "Dame las hps de mi equipo"
- [ ] **Resultado esperado:** Muestra HPS del equipo
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "muestrame las hps del equipo"
- [ ] **Ejemplo:** "Muéstrame las hps del equipo"
- [ ] **Resultado esperado:** Muestra HPS del equipo
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "ver hps del equipo"
- [ ] **Ejemplo:** "Quiero ver las hps del equipo"
- [ ] **Resultado esperado:** Muestra HPS del equipo
- [ ] **Estado:** ⏳ Pendiente

### 6.6 Comandos de Todas las HPS
- [ ] **Comando:** "todas las hps"
- [ ] **Ejemplo:** "¿Cuáles son todas las hps del sistema?"
- [ ] **Resultado esperado:** Resumen general de todas las HPS del sistema
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "todas las hps del sistema"
- [ ] **Ejemplo:** "Muéstrame todas las hps del sistema"
- [ ] **Resultado esperado:** Resumen general de todas las HPS del sistema
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "estadísticas hps"
- [ ] **Ejemplo:** "¿Cuáles son las estadísticas hps?"
- [ ] **Resultado esperado:** Estadísticas de todas las HPS
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "resumen hps"
- [ ] **Ejemplo:** "Dame un resumen de las hps"
- [ ] **Resultado esperado:** Resumen de todas las HPS
- [ ] **Estado:** ⏳ Pendiente

### 6.7 Comandos de Renovación de HPS
- [ ] **Comando:** "renovar hps de carlos.alonso@techex.es"
- [ ] **Ejemplo:** "Necesito renovar la hps de carlos.alonso@techex.es"
- [ ] **Resultado esperado:** HPS renovada exitosamente
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "renovar hps para admin@hps-system.com"
- [ ] **Ejemplo:** "Renovar hps para admin@hps-system.com"
- [ ] **Resultado esperado:** HPS renovada exitosamente
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "renovar hps"
- [ ] **Ejemplo:** "¿Cómo puedo renovar una hps?"
- [ ] **Resultado esperado:** Instrucciones para renovar HPS
- [ ] **Estado:** ⏳ Pendiente

### 6.8 Comandos de Traslado de HPS
- [ ] **Comando:** "trasladar hps de carlos.alonso@techex.es a nuevo@test.com"
- [ ] **Ejemplo:** "Quiero trasladar la hps de carlos.alonso@techex.es a nuevo@test.com"
- [ ] **Resultado esperado:** HPS trasladada exitosamente
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "trasladar hps para admin@hps-system.com desde test@example.com"
- [ ] **Ejemplo:** "Trasladar hps para admin@hps-system.com desde test@example.com"
- [ ] **Resultado esperado:** HPS trasladada exitosamente
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "trasladar hps"
- [ ] **Ejemplo:** "¿Cómo puedo trasladar una hps?"
- [ ] **Resultado esperado:** Instrucciones para trasladar HPS
- [ ] **Estado:** ⏳ Pendiente

### 6.9 Comandos de Administrador (Nuevos)
- [ ] **Comando:** "listar usuarios" / "ver usuarios" / "mostrar usuarios"
- [ ] **Ejemplo:** "listar usuarios"
- [ ] **Resultado esperado:** Lista completa de usuarios con roles, equipos y estado
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "listar equipos" / "ver equipos" / "mostrar equipos"
- [ ] **Ejemplo:** "listar equipos"
- [ ] **Resultado esperado:** Lista completa de equipos con líderes y descripciones
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "crear usuario [email]" / "dar alta usuario [email]"
- [ ] **Ejemplo:** "crear usuario test@example.com"
- [ ] **Resultado esperado:** Usuario creado como miembro con credenciales enviadas por email
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "crear equipo [nombre]" / "nuevo equipo [nombre]"
- [ ] **Ejemplo:** "crear equipo NUEVO"
- [ ] **Resultado esperado:** Equipo creado exitosamente
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "asignar usuario [email] al equipo [nombre]"
- [ ] **Ejemplo:** "asignar usuario test@example.com al equipo AICOX"
- [ ] **Resultado esperado:** Usuario asignado al equipo especificado
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "modificar rol de [email] a [rol]"
- [ ] **Ejemplo:** "modificar rol de test@example.com a team_lead"
- [ ] **Resultado esperado:** Rol del usuario modificado exitosamente
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "aprobar hps de [email]" / "aceptar hps de [email]"
- [ ] **Ejemplo:** "aprobar hps de test@example.com"
- [ ] **Resultado esperado:** HPS del usuario aprobada exitosamente
- [ ] **Estado:** ⏳ Pendiente

- [ ] **Comando:** "rechazar hps de [email]" / "denegar hps de [email]"
- [ ] **Ejemplo:** "rechazar hps de test@example.com"
- [ ] **Resultado esperado:** HPS del usuario rechazada exitosamente
- [ ] **Estado:** ⏳ Pendiente

### 6.10 Notas de Pruebas
```
Comandos probados:
- 
- 
- 

Errores encontrados:
- 
- 
- 

Observaciones:
- 
- 
- 
```

---

## 7. Pruebas de Monitoreo de Chat

### 7.1 Página de Monitoreo
- [ ] Ir a "Monitoreo Chat IA"
- [ ] Verificar que aparece la página de monitoreo
- [ ] Verificar que aparecen las métricas en tiempo real
- [ ] Verificar que aparecen las conversaciones recientes
- [ ] Verificar que aparecen las preguntas frecuentes
- [ ] **Resultado:** ✅/❌ - Página de monitoreo correcta

### 6.2 Visualización de Conversaciones
- [ ] Verificar que las conversaciones aparecen como listas
- [ ] Verificar que cada conversación muestra:
  - [ ] Avatar del usuario
  - [ ] Nombre del usuario
  - [ ] Título de la conversación
  - [ ] Número de mensajes
  - [ ] Estado (activa/completada)
  - [ ] Botón "Ver detalles"
- [ ] **Resultado:** ✅/❌ - Conversaciones visualizadas correctamente

### 6.3 Detalles de Conversación
- [ ] Hacer clic en "Ver detalles" en una conversación
- [ ] Verificar que se abre el modal
- [ ] Verificar que se muestra la conversación completa
- [ ] Verificar que se pueden ver todos los mensajes
- [ ] Hacer clic en "Cerrar" (X)
- [ ] Verificar que el modal se cierra
- [ ] **Resultado:** ✅/❌ - Detalles de conversación funcionan

### 6.4 Métricas en Tiempo Real
- [ ] Verificar que las métricas se actualizan
- [ ] Verificar que aparecen:
  - [ ] Conversaciones activas
  - [ ] Total de mensajes
  - [ ] Tiempo promedio de respuesta
  - [ ] Salud del sistema
- [ ] **Resultado:** ✅/❌ - Métricas actualizadas

---

## 7. Pruebas de Gestión HPS

### 7.1 Lista de Solicitudes HPS
- [ ] Ir a "Gestión HPS"
- [ ] Verificar que aparece la lista de solicitudes
- [ ] Verificar que cada solicitud muestra:
  - [ ] Descripción
  - [ ] Tipo
  - [ ] Estado
  - [ ] Fecha
  - [ ] Botones de acción
- [ ] **Resultado:** ✅/❌ - Lista de HPS correcta

### 7.2 Crear Solicitud HPS
- [ ] Hacer clic en "Nueva Solicitud"
- [ ] Verificar que aparece el formulario
- [ ] Completar formulario con datos válidos
- [ ] Hacer clic en "Guardar"
- [ ] Verificar que aparece mensaje de éxito
- [ ] Verificar que la solicitud aparece en la lista
- [ ] **Resultado:** ✅/❌ - Solicitud HPS creada

### 7.3 Aprobar/Rechazar Solicitud
- [ ] Hacer clic en "Aprobar" en una solicitud
- [ ] Verificar que aparece confirmación
- [ ] Confirmar aprobación
- [ ] Verificar que el estado cambia a "Aprobada"
- [ ] Repetir con "Rechazar"
- [ ] **Resultado:** ✅/❌ - Aprobación/Rechazo funcionan

---

## 8. Pruebas de Persistencia de Sesión

### 8.1 Recarga de Página
- [ ] Estar autenticado en cualquier página
- [ ] Recargar la página (F5)
- [ ] Verificar que permanece autenticado
- [ ] Verificar que no aparece "Acceso Denegado"
- [ ] Repetir en diferentes páginas
- [ ] **Resultado:** ✅/❌ - Sesión persiste

### 8.2 Navegación entre Páginas
- [ ] Navegar entre todas las páginas del menú
- [ ] Verificar que no aparece "Acceso Denegado"
- [ ] Verificar que el usuario permanece autenticado
- [ ] Verificar que el menú activo se actualiza
- [ ] **Resultado:** ✅/❌ - Navegación fluida

---

## 9. Pruebas de Rendimiento Visual

### 9.1 Tiempo de Carga
- [ ] Medir tiempo de carga de cada página principal
- [ ] Verificar que todas cargan en menos de 3 segundos
- [ ] Verificar que no hay elementos que tardan en cargar
- [ ] **Resultado:** ✅/❌ - Tiempos de carga aceptables

### 9.2 Animaciones y Transiciones
- [ ] Verificar que las transiciones entre páginas son suaves
- [ ] Verificar que los modales se abren/cierran correctamente
- [ ] Verificar que los botones responden al hover
- [ ] Verificar que no hay elementos que parpadean
- [ ] **Resultado:** ✅/❌ - Animaciones suaves

---

## 10. Pruebas de Accesibilidad

### 10.1 Navegación por Teclado
- [ ] Usar Tab para navegar entre elementos
- [ ] Verificar que todos los elementos son accesibles
- [ ] Verificar que el foco es visible
- [ ] **Resultado:** ✅/❌ - Navegación por teclado funciona

### 10.2 Contraste y Legibilidad
- [ ] Verificar que el texto es legible
- [ ] Verificar que hay suficiente contraste
- [ ] Verificar que los botones son claramente visibles
- [ ] **Resultado:** ✅/❌ - Contraste adecuado

---

## 11. Pruebas de Responsividad

### 11.1 Diferentes Tamaños de Pantalla
- [ ] Probar en pantalla grande (1920x1080)
- [ ] Probar en pantalla mediana (1366x768)
- [ ] Probar en pantalla pequeña (1024x768)
- [ ] Verificar que la interfaz se adapta
- [ ] **Resultado:** ✅/❌ - Responsividad correcta

### 11.2 Modo Móvil
- [ ] Activar modo móvil en DevTools
- [ ] Verificar que el menú se convierte en hamburguesa
- [ ] Verificar que las tablas se adaptan
- [ ] Verificar que los botones son táctiles
- [ ] **Resultado:** ✅/❌ - Modo móvil funciona

---

## 12. Pruebas de Errores Visuales

### 12.1 Manejo de Errores
- [ ] Intentar acceder a URL inexistente
- [ ] Verificar que aparece página 404
- [ ] Intentar enviar formulario vacío
- [ ] Verificar que aparecen mensajes de error
- [ ] **Resultado:** ✅/❌ - Errores manejados correctamente

### 12.2 Estados de Carga
- [ ] Verificar que aparecen indicadores de carga
- [ ] Verificar que los botones se deshabilitan durante carga
- [ ] Verificar que no hay elementos que se duplican
- [ ] **Resultado:** ✅/❌ - Estados de carga correctos

---

## 13. Criterios de Aceptación Visual

### ✅ Pruebas Exitosas
- [ ] Todas las páginas cargan correctamente
- [ ] Navegación fluida entre secciones
- [ ] Formularios funcionan correctamente
- [ ] Chat con agente IA operativo
- [ ] Monitoreo de chat funcional
- [ ] Gestión de usuarios completa
- [ ] Gestión HPS operativa
- [ ] Sesión persiste correctamente
- [ ] Interfaz responsive
- [ ] Sin errores visuales

### ❌ Criterios de Fallo
- [ ] Páginas que no cargan
- [ ] Elementos rotos o mal alineados
- [ ] Formularios que no funcionan
- [ ] Navegación que falla
- [ ] Errores en consola del navegador
- [ ] Interfaz no responsive
- [ ] Elementos que parpadean o se duplican

---

## 14. Resumen Final

### 📊 Estadísticas de Pruebas Visuales
- **Total de Pruebas:** 50
- **Pruebas Exitosas:** ___/50
- **Pruebas Fallidas:** ___/50
- **Porcentaje de Éxito:** ___%

### 🎯 Estado General
- [ ] **INTERFAZ APROBADA** - Todas las pruebas visuales pasaron
- [ ] **INTERFAZ CONDICIONAL** - Algunas pruebas fallaron pero no críticas
- [ ] **INTERFAZ RECHAZADA** - Pruebas críticas fallaron

### 📝 Notas Adicionales
```
Observaciones:
- 
- 
- 
```

### ✅ Firma de Aprobación
- **Ejecutado por:** _________________ Fecha: ___________
- **Revisado por:** _________________ Fecha: ___________
- **Aprobado por:** _________________ Fecha: ___________

---

## 15. Notas Adicionales

- **Tiempo estimado:** 2-3 horas para ejecución completa
- **Frecuencia:** Ejecutar después de cada cambio visual
- **Responsable:** Equipo de desarrollo/QA
- **Herramientas:** Navegador web, DevTools
- **Prerequisito:** Completar protocolo de pruebas programáticas

