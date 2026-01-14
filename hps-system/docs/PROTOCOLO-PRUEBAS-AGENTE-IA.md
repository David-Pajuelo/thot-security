# Protocolo de Pruebas - Agente IA HPS System

## 📋 Índice
1. [Información General](#información-general)
2. [Roles y Permisos](#roles-y-permisos)
3. [Comandos por Rol](#comandos-por-rol)
4. [Casos de Prueba](#casos-de-prueba)
5. [Flujos Conversacionales](#flujos-conversacionales)
6. [Casos Límite y Errores](#casos-límite-y-errores)
7. [Checklist de Validación](#checklist-de-validación)

---

## 📌 Información General

### Objetivo
Verificar el correcto funcionamiento del chat del agente IA, incluyendo:
- Reconocimiento y ejecución de comandos
- Validación de permisos por rol
- Flujos conversacionales
- Manejo de errores
- Persistencia de conversaciones

### Roles Disponibles
1. **admin** - Administrador del sistema
2. **jefe_seguridad** - Jefe de Seguridad
3. **jefe_seguridad_suplente** - Jefe de Seguridad Suplente
4. **crypto** - Especialista en Crypto
5. **team_lead** / **team_leader** - Jefe de Equipo
6. **member** - Miembro (rol por defecto)

### Comandos Disponibles
- `consultar_estado_hps` - Consultar estado de HPS
- `consultar_hps_equipo` - Ver HPS del equipo
- `consultar_todas_hps` - Estadísticas globales
- `listar_usuarios` - Listar usuarios
- `listar_equipos` - Listar equipos
- `solicitar_hps` - Solicitar nueva HPS
- `trasladar_hps` / `traspasar_hps` - Trasladar HPS
- `renovar_hps` - Renovar HPS
- `crear_usuario` - Crear nuevo usuario
- `crear_equipo` - Crear nuevo equipo
- `asignar_usuario_equipo` - Asignar usuario a equipo
- `modificar_rol` - Modificar rol de usuario
- `aprobar_hps` - Aprobar solicitud HPS
- `rechazar_hps` - Rechazar solicitud HPS
- `dar_alta_jefe_equipo` - Crear jefe de equipo completo
- `comandos_disponibles` - Mostrar comandos disponibles
- `ayuda_hps` - Mostrar ayuda sobre HPS

---

## 🔐 Roles y Permisos

### Admin
**Permisos completos:**
- ✅ Consultar cualquier HPS
- ✅ Crear usuarios
- ✅ Crear equipos
- ✅ Asignar usuarios a equipos
- ✅ Modificar roles
- ✅ Aprobar/Rechazar HPS
- ✅ Solicitar/Trasladar/Renovar HPS
- ✅ Crear jefes de equipo
- ✅ Ver todas las HPS
- ✅ Listar todos los usuarios y equipos

### Jefe de Seguridad / Jefe de Seguridad Suplente
**Permisos:**
- ✅ Consultar cualquier HPS
- ✅ Ver todas las HPS (estadísticas globales)
- ✅ Modificar roles
- ✅ Aprobar/Rechazar HPS
- ✅ Solicitar/Trasladar/Renovar HPS
- ✅ Listar equipos
- ❌ Crear usuarios (solo admin y team_lead)
- ❌ Crear equipos (solo admin)
- ❌ Asignar usuarios a equipos (solo admin y team_lead)
- ❌ Crear jefes de equipo (solo admin)

### Crypto
**Permisos:**
- ✅ Consultar HPS
- ✅ Ver HPS de su equipo
- ✅ Solicitar HPS (nueva)
- ✅ Renovar HPS
- ✅ Listar usuarios de su equipo
- ✅ Listar equipos
- ❌ Aprobar/Rechazar HPS (solo admin, jefe_seguridad, team_lead)
- ❌ Trasladar HPS (solo jefe_seguridad)
- ❌ Crear usuarios (solo admin y team_lead)
- ❌ Modificar roles (solo admin y jefe_seguridad)

### Team Lead / Team Leader
**Permisos:**
- ✅ Consultar HPS
- ✅ Ver HPS de su equipo
- ✅ Crear usuarios (en su equipo)
- ✅ Asignar usuarios a su equipo
- ✅ Solicitar HPS (nueva)
- ✅ Renovar HPS
- ✅ Aprobar/Rechazar HPS (de su equipo)
- ✅ Listar usuarios de su equipo
- ✅ Listar equipos
- ❌ Ver todas las HPS (solo admin, jefe_seguridad)
- ❌ Trasladar HPS (solo jefe_seguridad)
- ❌ Modificar roles (solo admin y jefe_seguridad)
- ❌ Crear equipos (solo admin)

### Member
**Permisos:**
- ✅ Consultar su propia HPS
- ✅ Consultar HPS de otros (si tiene permisos)
- ❌ Todas las demás operaciones

---

## 📝 Comandos por Rol

### Admin - Comandos Disponibles

#### Consultas
- [ ] `estado hps de [email]` - Consultar estado de HPS
- [ ] `hps de mi equipo` - Ver HPS del equipo
- [ ] `todas las hps` - Estadísticas globales
- [ ] `listar usuarios` - Listar todos los usuarios
- [ ] `listar equipos` - Listar todos los equipos

#### Gestión de Usuarios
- [ ] `crear usuario [email]` - Crear nuevo usuario
- [ ] `modificar rol de [email] a [rol]` - Cambiar rol de usuario
- [ ] `asignar usuario [email] al equipo [nombre]` - Asignar usuario a equipo
- [ ] `dar alta jefe de equipo [nombre] [email] [equipo]` - Crear jefe de equipo completo

#### Gestión de Equipos
- [ ] `crear equipo [nombre]` - Crear nuevo equipo

#### Solicitudes HPS
- [ ] `envío hps a [email]` o `solicitar hps para [email]` - Solicitar nueva HPS
- [ ] `envío traspaso hps a [email]` o `trasladar hps de [email]` - Solicitar traspaso HPS
- [ ] `renovar hps de [email]` - Solicitar renovación HPS

#### Gestión de HPS
- [ ] `aprobar hps de [email]` - Aprobar solicitud HPS
- [ ] `rechazar hps de [email]` - Rechazar solicitud HPS

### Jefe de Seguridad - Comandos Disponibles

#### Consultas
- [ ] `estado hps de [email]` - Consultar estado de HPS
- [ ] `todas las hps` - Estadísticas globales
- [ ] `listar equipos` - Ver todos los equipos

#### Gestión de Usuarios
- [ ] `modificar rol de [email] a [rol]` - Cambiar rol de usuario

#### Solicitudes HPS
- [ ] `envío hps a [email]` o `solicitar hps para [email]` - Solicitar nueva HPS
- [ ] `envío traspaso hps a [email]` o `trasladar hps de [email]` - Solicitar traspaso HPS
- [ ] `renovar hps de [email]` - Solicitar renovación HPS

#### Gestión de HPS
- [ ] `aprobar hps de [email]` - Aprobar solicitud HPS
- [ ] `rechazar hps de [email]` - Rechazar solicitud HPS

### Team Lead - Comandos Disponibles

#### Consultas
- [ ] `estado hps de [email]` - Consultar estado de HPS
- [ ] `hps de mi equipo` - Ver HPS de tu equipo
- [ ] `listar usuarios` - Ver usuarios de tu equipo
- [ ] `listar equipos` - Ver todos los equipos

#### Gestión de Usuarios de tu Equipo
- [ ] `crear usuario [email]` - Crear usuario en tu equipo
- [ ] `asignar usuario [email] al equipo [nombre]` - Asignar usuario a tu equipo

#### Solicitudes HPS
- [ ] `envío hps a [email]` o `solicitar hps para [email]` - Solicitar nueva HPS
- [ ] `renovar hps de [email]` - Solicitar renovación HPS

#### Gestión de HPS de tu Equipo
- [ ] `aprobar hps de [email]` - Aprobar HPS de tu equipo
- [ ] `rechazar hps de [email]` - Rechazar HPS de tu equipo

### Member - Comandos Disponibles

#### Consultas
- [ ] `estado de mi hps` - Ver estado de tu HPS
- [ ] `estado hps de [email]` - Consultar estado de HPS (si tienes permisos)

---

## 🧪 Casos de Prueba

### 1. Conexión y Autenticación

#### TC-001: Conexión WebSocket exitosa
**Precondiciones:**
- Usuario autenticado con token válido
- Servicio backend funcionando

**Pasos:**
1. Abrir el chat del agente IA
2. Verificar que se establece la conexión WebSocket
3. Verificar que se recibe el mensaje de bienvenida

**Resultado Esperado:**
- ✅ Conexión establecida
- ✅ Mensaje de bienvenida personalizado según rol
- ✅ Sugerencias de comandos visibles

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-002: Conexión con token inválido
**Precondiciones:**
- Token JWT inválido o expirado

**Pasos:**
1. Intentar conectar con token inválido
2. Verificar respuesta del servidor

**Resultado Esperado:**
- ❌ Conexión rechazada
- ❌ Mensaje de error apropiado

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-003: Mensaje de bienvenida solo en primera vez
**Precondiciones:**
- Usuario con conversación existente

**Pasos:**
1. Conectar al chat
2. Verificar que NO se muestra mensaje de bienvenida si hay historial
3. Verificar que SÍ se muestra si no hay historial

**Resultado Esperado:**
- ✅ Bienvenida solo cuando no hay historial
- ✅ Historial cargado correctamente si existe

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

### 2. Comandos de Consulta

#### TC-004: Consultar estado HPS con email
**Precondiciones:**
- Usuario con rol que permita consultar HPS
- Usuario objetivo existe en el sistema

**Pasos:**
1. Escribir: `estado hps de usuario@ejemplo.com`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Estado HPS mostrado correctamente
- ✅ Información completa (estado, fechas)
- ✅ Emoji según estado (⏳ pending, ✅ approved, ❌ rejected, ⏰ expired)

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-005: Consultar estado HPS sin email (usuario actual)
**Precondiciones:**
- Usuario autenticado

**Pasos:**
1. Escribir: `estado de mi hps`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Estado HPS del usuario actual mostrado

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-006: Consultar estado HPS - usuario no existe
**Precondiciones:**
- Usuario con permisos

**Pasos:**
1. Escribir: `estado hps de noexiste@ejemplo.com`
2. Verificar respuesta

**Resultado Esperado:**
- ❌ Mensaje de error: "No se encontró ningún usuario con el email..."

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-007: Consultar HPS de equipo (team_lead)
**Precondiciones:**
- Usuario con rol team_lead
- Equipo tiene miembros con HPS

**Pasos:**
1. Escribir: `hps de mi equipo`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Lista de HPS del equipo mostrada
- ✅ Información de cada miembro
- ✅ Limitado a 10 resultados

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-008: Consultar todas las HPS (admin/jefe_seguridad)
**Precondiciones:**
- Usuario con rol admin o jefe_seguridad

**Pasos:**
1. Escribir: `todas las hps` o `dame un resumen de todas las hps`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Estadísticas globales mostradas
- ✅ Desglose por estado
- ✅ Total de HPS

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-009: Consultar todas las HPS sin permisos (member)
**Precondiciones:**
- Usuario con rol member

**Pasos:**
1. Escribir: `todas las hps`
2. Verificar respuesta

**Resultado Esperado:**
- ❌ Mensaje de error: "No tienes permisos..."

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-010: Listar usuarios (admin)
**Precondiciones:**
- Usuario con rol admin

**Pasos:**
1. Escribir: `listar usuarios`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Lista de usuarios mostrada
- ✅ Información relevante (email, nombre, rol)
- ✅ Limitado a 50 resultados

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-011: Listar equipos
**Precondiciones:**
- Usuario autenticado

**Pasos:**
1. Escribir: `listar equipos`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Lista de equipos mostrada
- ✅ Información de cada equipo

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

### 3. Gestión de Usuarios

#### TC-012: Crear usuario con email (admin)
**Precondiciones:**
- Usuario con rol admin
- Email válido no existente

**Pasos:**
1. Escribir: `crear usuario nuevo@ejemplo.com`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Usuario creado exitosamente
- ✅ Mensaje de confirmación
- ✅ Email con credenciales enviado (verificar logs)

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-013: Crear usuario - flujo conversacional (admin)
**Precondiciones:**
- Usuario con rol admin

**Pasos:**
1. Escribir: `crear usuario`
2. Verificar que se solicita email
3. Escribir: `nuevo@ejemplo.com`
4. Verificar creación

**Resultado Esperado:**
- ✅ Flujo conversacional iniciado
- ✅ Solicitud de email
- ✅ Usuario creado después de proporcionar email

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-014: Crear usuario sin permisos (member)
**Precondiciones:**
- Usuario con rol member

**Pasos:**
1. Escribir: `crear usuario nuevo@ejemplo.com`
2. Verificar respuesta

**Resultado Esperado:**
- ❌ Mensaje de error: "No tienes permisos para crear usuarios..."

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-015: Crear usuario - email ya existe
**Precondiciones:**
- Usuario con rol admin
- Email ya existe en el sistema

**Pasos:**
1. Escribir: `crear usuario existente@ejemplo.com`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Perfil HPS creado/actualizado para usuario existente
- ✅ Mensaje informativo

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-016: Modificar rol con email y rol (admin)
**Precondiciones:**
- Usuario con rol admin
- Usuario objetivo existe

**Pasos:**
1. Escribir: `modificar rol de usuario@ejemplo.com a team_lead`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Rol modificado exitosamente
- ✅ Mensaje de confirmación

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-017: Modificar rol - flujo conversacional (admin)
**Precondiciones:**
- Usuario con rol admin

**Pasos:**
1. Escribir: `modificar rol`
2. Verificar solicitud de email
3. Escribir: `usuario@ejemplo.com`
4. Verificar solicitud de rol
5. Escribir: `team_lead`
6. Verificar modificación

**Resultado Esperado:**
- ✅ Flujo conversacional correcto
- ✅ Rol modificado exitosamente

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-018: Modificar rol - email y rol juntos en un mensaje
**Precondiciones:**
- Usuario con rol admin

**Pasos:**
1. Escribir: `modificar rol`
2. Verificar solicitud de email
3. Escribir: `usuario@ejemplo.com team_lead`
4. Verificar modificación

**Resultado Esperado:**
- ✅ Email y rol detectados en un solo mensaje
- ✅ Rol modificado sin pedir confirmación adicional

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-019: Asignar usuario a equipo (admin)
**Precondiciones:**
- Usuario con rol admin
- Usuario y equipo existen

**Pasos:**
1. Escribir: `asignar usuario usuario@ejemplo.com al equipo Equipo1`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Usuario asignado al equipo
- ✅ Mensaje de confirmación

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-020: Dar alta jefe de equipo (admin)
**Precondiciones:**
- Usuario con rol admin
- Equipo existe

**Pasos:**
1. Escribir: `dar alta jefe de equipo Juan jefe@ejemplo.com Equipo1`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Jefe de equipo creado
- ✅ Usuario creado si no existe
- ✅ Asignado al equipo
- ✅ Rol team_lead asignado

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

### 4. Gestión de Equipos

#### TC-021: Crear equipo (admin)
**Precondiciones:**
- Usuario con rol admin
- Nombre de equipo no existe

**Pasos:**
1. Escribir: `crear equipo NuevoEquipo`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Equipo creado exitosamente
- ✅ Mensaje de confirmación

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-022: Crear equipo sin permisos (member)
**Precondiciones:**
- Usuario con rol member

**Pasos:**
1. Escribir: `crear equipo NuevoEquipo`
2. Verificar respuesta

**Resultado Esperado:**
- ❌ Mensaje de error: "No tienes permisos..."

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-023: Crear equipo - nombre ya existe
**Precondiciones:**
- Usuario con rol admin
- Equipo con ese nombre ya existe

**Pasos:**
1. Escribir: `crear equipo EquipoExistente`
2. Verificar respuesta

**Resultado Esperado:**
- ❌ Mensaje de error: "El equipo ya existe..."

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

### 5. Solicitudes HPS

#### TC-024: Solicitar nueva HPS (admin)
**Precondiciones:**
- Usuario con rol admin
- Email válido

**Pasos:**
1. Escribir: `solicitar hps para usuario@ejemplo.com` o `envío hps a usuario@ejemplo.com`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Token HPS generado
- ✅ Email con formulario enviado
- ✅ URL del formulario mostrada
- ✅ Token válido por 72 horas

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-025: Solicitar traspaso HPS (jefe_seguridad)
**Precondiciones:**
- Usuario con rol jefe_seguridad
- Email válido

**Pasos:**
1. Escribir: `trasladar hps de usuario@ejemplo.com` o `envío traspaso hps a usuario@ejemplo.com`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Token HPS generado (tipo traspaso)
- ✅ Email con formulario enviado
- ✅ URL del formulario mostrada

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-026: Solicitar traspaso HPS sin permisos (team_lead)
**Precondiciones:**
- Usuario con rol team_lead

**Pasos:**
1. Escribir: `trasladar hps de usuario@ejemplo.com`
2. Verificar respuesta

**Resultado Esperado:**
- ❌ Mensaje de error: "Solo los jefes de seguridad pueden solicitar traspasos..."

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-027: Renovar HPS (admin)
**Precondiciones:**
- Usuario con rol admin
- Email válido

**Pasos:**
1. Escribir: `renovar hps de usuario@ejemplo.com`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Token HPS generado (tipo renovación)
- ✅ Email con formulario enviado
- ✅ URL del formulario mostrada

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

### 6. Gestión de HPS

#### TC-028: Aprobar HPS (admin)
**Precondiciones:**
- Usuario con rol admin
- HPS pendiente existe

**Pasos:**
1. Escribir: `aprobar hps de usuario@ejemplo.com`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ HPS aprobada
- ✅ Estado actualizado a "approved"
- ✅ Mensaje de confirmación

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-029: Rechazar HPS (admin)
**Precondiciones:**
- Usuario con rol admin
- HPS pendiente existe

**Pasos:**
1. Escribir: `rechazar hps de usuario@ejemplo.com`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ HPS rechazada
- ✅ Estado actualizado a "rejected"
- ✅ Mensaje de confirmación

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-030: Aprobar HPS sin permisos (member)
**Precondiciones:**
- Usuario con rol member

**Pasos:**
1. Escribir: `aprobar hps de usuario@ejemplo.com`
2. Verificar respuesta

**Resultado Esperado:**
- ❌ Mensaje de error: "No tienes permisos..."

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

### 7. Comandos de Ayuda

#### TC-031: Mostrar comandos disponibles (admin)
**Precondiciones:**
- Usuario con rol admin

**Pasos:**
1. Escribir: `¿Qué comandos puedes ejecutar?` o `comandos disponibles`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Lista completa de comandos para admin
- ✅ Organizados por categorías
- ✅ Formato legible

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-032: Mostrar comandos disponibles (member)
**Precondiciones:**
- Usuario con rol member

**Pasos:**
1. Escribir: `¿Qué comandos puedes ejecutar?`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Lista de comandos limitada para member
- ✅ Solo comandos permitidos

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-033: Mostrar ayuda HPS
**Precondiciones:**
- Usuario autenticado

**Pasos:**
1. Escribir: `ayuda hps` o `información sobre hps`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Información sobre HPS mostrada
- ✅ Explicación clara

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

## 🔄 Flujos Conversacionales

### Flujo 1: Crear Usuario

#### TC-034: Flujo completo crear usuario
**Precondiciones:**
- Usuario con rol admin

**Pasos:**
1. Escribir: `crear usuario`
2. Verificar: Se solicita email
3. Escribir: `nuevo@ejemplo.com`
4. Verificar: Usuario creado

**Resultado Esperado:**
- ✅ Flujo iniciado correctamente
- ✅ Email solicitado
- ✅ Usuario creado después de proporcionar email

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-035: Cancelar flujo crear usuario con nuevo comando
**Precondiciones:**
- Usuario con rol admin
- Flujo crear_usuario activo

**Pasos:**
1. Escribir: `crear usuario`
2. Verificar: Se solicita email
3. Escribir: `listar usuarios`
4. Verificar: Flujo cancelado, comando ejecutado

**Resultado Esperado:**
- ✅ Flujo anterior cancelado
- ✅ Nuevo comando ejecutado
- ✅ No se solicita email

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

### Flujo 2: Modificar Rol

#### TC-036: Flujo completo modificar rol
**Precondiciones:**
- Usuario con rol admin

**Pasos:**
1. Escribir: `modificar rol`
2. Verificar: Se solicita email
3. Escribir: `usuario@ejemplo.com`
4. Verificar: Se solicita rol
5. Escribir: `team_lead`
6. Verificar: Rol modificado

**Resultado Esperado:**
- ✅ Flujo iniciado correctamente
- ✅ Email solicitado
- ✅ Rol solicitado después de email
- ✅ Rol modificado exitosamente

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

#### TC-037: Modificar rol - email y rol en un mensaje
**Precondiciones:**
- Usuario con rol admin

**Pasos:**
1. Escribir: `modificar rol`
2. Verificar: Se solicita email
3. Escribir: `usuario@ejemplo.com team_lead`
4. Verificar: Rol modificado directamente

**Resultado Esperado:**
- ✅ Email y rol detectados en un solo mensaje
- ✅ Rol modificado sin solicitar confirmación adicional

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

## ⚠️ Casos Límite y Errores

### TC-038: Comando no reconocido
**Precondiciones:**
- Usuario autenticado

**Pasos:**
1. Escribir: `comando_inexistente`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Mensaje amigable indicando que el comando no se reconoce
- ✅ Sugerencia de usar "¿Qué comandos puedes ejecutar?"

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

### TC-039: Email inválido
**Precondiciones:**
- Usuario con permisos

**Pasos:**
1. Escribir: `crear usuario email_invalido`
2. Verificar respuesta

**Resultado Esperado:**
- ❌ Mensaje de error indicando email inválido
- ✅ Solicitud de email válido

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

### TC-040: Consultar HPS escribiendo solo email
**Precondiciones:**
- Usuario con permisos
- Sin flujo activo

**Pasos:**
1. Escribir: `usuario@ejemplo.com`
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Se interpreta como consulta de estado HPS
- ✅ Estado HPS mostrado

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

### TC-041: Reconexión WebSocket
**Precondiciones:**
- Conversación existente

**Pasos:**
1. Cerrar conexión WebSocket
2. Reconectar
3. Verificar historial cargado

**Resultado Esperado:**
- ✅ Historial cargado correctamente
- ✅ Mensajes anteriores visibles
- ✅ No se duplica mensaje de bienvenida

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

### TC-042: Reset de conversación
**Precondiciones:**
- Conversación con mensajes

**Pasos:**
1. Pulsar botón "Reset"
2. Verificar que se limpia el chat
3. Verificar que se archiva la conversación
4. Verificar que aparece mensaje de bienvenida

**Resultado Esperado:**
- ✅ Chat limpiado
- ✅ Conversación archivada
- ✅ Mensaje de bienvenida mostrado

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

### TC-043: Múltiples comandos rápidos
**Precondiciones:**
- Usuario con permisos

**Pasos:**
1. Enviar múltiples comandos rápidamente
2. Verificar que todos se procesan correctamente

**Resultado Esperado:**
- ✅ Todos los comandos procesados
- ✅ Respuestas en orden correcto
- ✅ Sin errores de concurrencia

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

### TC-044: Comando con parámetros faltantes
**Precondiciones:**
- Usuario con permisos

**Pasos:**
1. Escribir: `estado hps de` (sin email)
2. Verificar respuesta

**Resultado Esperado:**
- ✅ Mensaje solicitando el parámetro faltante
- ✅ Guía clara de cómo usar el comando

**Resultado Obtenido:** ☐ ✅ / ☐ ❌

---

## ✅ Checklist de Validación

### Funcionalidad Básica
- [ ] Conexión WebSocket funciona correctamente
- [ ] Autenticación con token JWT funciona
- [ ] Mensaje de bienvenida se muestra solo cuando corresponde
- [ ] Historial de conversación se carga correctamente
- [ ] Reset de conversación funciona correctamente

### Comandos por Rol
- [ ] Todos los comandos de admin funcionan
- [ ] Todos los comandos de jefe_seguridad funcionan
- [ ] Todos los comandos de crypto funcionan
- [ ] Todos los comandos de team_lead funcionan
- [ ] Todos los comandos de member funcionan

### Permisos
- [ ] Comandos restringidos rechazan correctamente usuarios sin permisos
- [ ] Mensajes de error de permisos son claros
- [ ] Usuarios solo ven comandos permitidos en la lista de comandos disponibles

### Flujos Conversacionales
- [ ] Flujo crear_usuario funciona correctamente
- [ ] Flujo modificar_rol funciona correctamente
- [ ] Flujos se cancelan correctamente con nuevos comandos
- [ ] Flujos manejan email y rol en un solo mensaje

### Manejo de Errores
- [ ] Errores de base de datos se manejan correctamente
- [ ] Errores de validación muestran mensajes claros
- [ ] Comandos no reconocidos muestran mensaje amigable
- [ ] Emails inválidos se detectan y rechazan

### Persistencia
- [ ] Mensajes se guardan en la base de datos
- [ ] Conversaciones se archivan correctamente
- [ ] Historial se carga correctamente al reconectar

### Integración
- [ ] Emails se envían correctamente (verificar logs)
- [ ] Tokens HPS se generan correctamente
- [ ] URLs de formularios HPS son válidas

---

## 📊 Plantilla de Reporte de Pruebas

### Información General
- **Fecha de Pruebas:** ___________
- **Tester:** ___________
- **Versión del Sistema:** ___________
- **Ambiente:** ☐ Desarrollo / ☐ Producción

### Resumen
- **Total de Casos de Prueba:** ___________
- **Casos Exitosos:** ___________
- **Casos Fallidos:** ___________
- **Casos Bloqueados:** ___________
- **Tasa de Éxito:** ___________

### Casos Fallidos
| TC | Descripción | Error | Severidad |
|----|-------------|-------|-----------|
|    |             |       |           |

### Observaciones
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

## 🔍 Notas Adicionales

### Comandos de Prueba Rápida

Para probar rápidamente todos los comandos de un rol:

**Admin:**
```
¿Qué comandos puedes ejecutar?
estado hps de admin@hps-system.com
todas las hps
listar usuarios
listar equipos
crear usuario test@ejemplo.com
modificar rol de test@ejemplo.com a member
crear equipo TestEquipo
asignar usuario test@ejemplo.com al equipo TestEquipo
solicitar hps para test@ejemplo.com
renovar hps de test@ejemplo.com
aprobar hps de test@ejemplo.com
```

**Member:**
```
¿Qué comandos puedes ejecutar?
estado de mi hps
```

### Verificación de Logs

Para verificar el funcionamiento correcto, revisar logs del backend:
```bash
docker logs cryptotrace-backend --tail 100 | grep -i "comando\|error\|hps\|usuario"
```

### Datos de Prueba Recomendados

- **Usuarios de prueba:** Crear usuarios con diferentes roles
- **Equipos de prueba:** Crear equipos de prueba
- **HPS de prueba:** Crear solicitudes HPS en diferentes estados

---

**Última actualización:** 2026-01-07
**Versión del Protocolo:** 1.0

