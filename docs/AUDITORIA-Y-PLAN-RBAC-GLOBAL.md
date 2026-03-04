# Auditoría y plan de implementación RBAC global

Este documento contiene la **auditoría completa** del control de acceso actual y un **plan de implementación** para un RBAC "de libro" (permisos como entidades, asignación Rol–Permiso, y migración de la lógica en código a ese modelo).

---

## 1. Resumen ejecutivo

| Aspecto | Estado actual | Objetivo |
|--------|----------------|----------|
| **Roles** | Sí: `HpsRole` + asignación en `HpsUserProfile` | Mantener; añadir relación Rol → Permisos |
| **Permisos como entidades** | No; `HpsRole.permissions` (JSON) no se usa para autorización | Sí: modelo `HpsPermission` + M2M con `HpsRole` |
| **Quién puede hacer qué** | Definido en código: `ADMIN_ROLES`, `TEAM_LEADS`, clases en `hps_core.permissions` y lógica inline en vistas/serializers | Definido en BD: permisos asignados a cada rol |
| **Alcance (scope)** | Por rol + "solo los míos" / "solo equipos que lidero" en código | Mantener scope en lógica, pero disparado por permisos (ej. `hps.ver_solo_propios`) |
| **Django staff/superuser** | Usado en chat (ver todas las conversaciones) y fallback en productos | Reemplazar por permiso explícito o mantener como bypass opcional |

Tras la implementación, toda decisión de autorización debería basarse en **permisos** asociados al rol del usuario (y opcionalmente en contexto como "dueño del recurso" o "líder del equipo del recurso"), no en nombres de rol en código.

---

## 2. Auditoría: inventario de roles

Roles existentes en el sistema (nombres usados en código y en `HpsRole`):

| Rol | Uso en código |
|-----|----------------|
| `admin` | ADMIN_ROLES; puede todo (roles, equipos, tokens, plantillas, perfiles, solicitudes, ver todas conversaciones vía is_staff/superuser). |
| `jefe_seguridad` | ADMIN_ROLES; igual que admin en HPS; en productos no se usa "admin permissions" pero en análisis se incluye en mismo conjunto que admin/crypto/jefe_suplente. |
| `jefe_seguridad_suplente` | ADMIN_ROLES y TEAM_LEADS; puede crear tokens y plantillas; puede asignar solo roles `crypto` y `member`. |
| `team_lead` | TEAM_LEADS; ve equipos que lidera, perfiles de miembros de esos equipos; puede crear/editar perfiles en equipos que lidera; no puede asignar roles (se fuerza member). |
| `member` | Rol por defecto; ve solo sus solicitudes y sus datos; no asigna roles. |
| `crypto` | Ver todos los perfiles (junto con admin/jefes); en productos tiene "admin permissions" (ver toda línea temporal, limpiar todos los registros). |

Conjuntos definidos en código:

- **ADMIN_ROLES**: `admin`, `jefe_seguridad`, `jefe_seguridad_suplente` (en `hps_core/permissions.py` y `hps_core/views.py`).
- **TEAM_LEADS**: `team_lead`, `jefe_seguridad_suplente` (en `hps_core/permissions.py`).
- **TEAM_ROLES**: `team_lead`, `jefe_seguridad_suplente` (en `hps_core/views.py`; usado para `has_team_lead_permissions`).
- **Roles con "admin permissions" en productos**: `admin`, `crypto`, `jefe_seguridad`, `jefe_seguridad_suplente` (en `productos/views.py`).

---

## 3. Auditoría: permisos implícitos (clases y lógica en código)

### 3.1 Clases en `hps_core/permissions.py`

| Clase | Condición | Uso |
|-------|-----------|-----|
| `HasHpsProfile` | Usuario tiene `hps_profile` | Acceso mínimo HPS (listar solicitudes, perfiles, etc.). |
| `IsHpsAdmin` | `role_name in ADMIN_ROLES` | CRUD roles; list/retrieve tokens; get_queryset equipos/solicitudes "todos". |
| `IsHpsAdminOrTeamLead` | Admin o rol en TEAM_LEADS o es líder de algún equipo activo | CRUD equipos (get_queryset: admin todos, team_lead solo equipos que lidera); crear perfiles. |
| `IsHpsAdminOrSecurityChief` | Admin o `jefe_seguridad` o `jefe_seguridad_suplente` | CRUD plantillas; crear tokens. |
| `IsHpsAdminOrSelf` | Admin o objeto.user_id == request.user.id | Audit logs: ver solo los propios. |
| `IsHpsAdminOrTeamLeadEditingLedMember` | Admin o (team lead y el perfil pertenece a usuario en equipo que lidera) | update/destroy/activate/deactivate perfiles. |

### 3.2 Lógica adicional en vistas (`hps_core/views.py`)

| Vista / método | Dónde | Lógica basada en rol |
|----------------|--------|------------------------|
| `HpsTeamViewSet.get_queryset` | L87-91 | `role_name in ADMIN_ROLES` → todos los equipos; si no, `has_team_lead_permissions` → solo equipos que lidera. |
| `HpsRequestViewSet.get_queryset` | L361-379 | `role_name in ADMIN_ROLES` → todas las solicitudes; team lead → solicitudes de usuarios de equipos que lidera; resto → solo propias. |
| `HpsTeamViewSet.add_member` | L253-258 | Si `profile.role.name == 'member'` y es el primer miembro, se asigna rol `team_lead`. |
| `HpsUserProfileViewSet.get_queryset` | L1379-1401 | `role_name in ADMIN_ROLES or role_name == "crypto"` → todos los perfiles; team lead → perfiles de equipos que lidera; resto → todos (según requerimiento). |
| `HpsUserProfileViewSet.perform_create` | L1426-1447 | Si no es admin, team_lead solo puede crear en equipos que lidera (validación por team_ids). |
| `HpsUserProfileViewSet.get_permissions` | L1410-1420 | create → IsHpsAdminOrTeamLead; update/destroy/activate/deactivate → IsHpsAdminOrTeamLeadEditingLedMember. |
| `ChatConversationViewSet.get_queryset` | L1817-1824 | `is_staff or is_superuser` → todas las conversaciones; si no, solo las del usuario. |
| `ChatConversationViewSet.full` | L1938 | Mismo usuario o `is_staff or is_superuser`. |
| `ChatConversationViewSet.all_conversations` | L1960-1965 | `is_staff or is_superuser` para ver listado global. |
| Chat: `open_or_create` (perform_create / mensaje bienvenida) | L2042-2046 | `profile.role.name` para RoleConfig (bienvenida y sugerencias por rol). |

### 3.3 Lógica en `productos/views.py`

| Vista / acción | Dónde | Lógica |
|----------------|--------|--------|
| `LineaTemporalProductoViewSet.get_queryset` | L1777-1788 | `has_admin_permissions`: role_name in ['admin','crypto','jefe_seguridad','jefe_seguridad_suplente'] o is_superuser → ver todos; si no, solo usuario. |
| Acción limpiar registros (línea temporal) | L2275-2295 | Mismo `has_admin_permissions` para decidir si borrar todos los registros antiguos o solo los del usuario. |

### 3.4 Serializers: asignación de roles (`hps_core/serializers.py`)

| Contexto | Regla en código |
|----------|------------------|
| Crear perfil (HpsUserProfileCreateSerializer) | admin: cualquier rol; jefe_seguridad / jefe_seguridad_suplente: solo `crypto` o `member`; team_lead: forzar `member`; otros: forzar `member`. |
| Actualizar perfil (HpsUserProfileSerializer.update) | admin: cualquier rol; jefes seguridad: solo `crypto` o `member`; team_lead: no puede cambiar rol (mantener actual); otros: error "No tienes permisos para cambiar roles". |

### 3.5 Servicios y otros

| Archivo | Uso de rol |
|---------|------------|
| `hps_core/services.py` (L195-214) | `requested_by_role` para elegir plantilla de email (jefe_seguridad vs jefe_seguridad_suplente) en tokens de traspaso. |
| `hps_core/urls.py` (L189) | Respuesta `me`: incluye `role: profile.role.name`. |
| `productos/serializers.py` (CustomTokenObtainPairSerializer) | JWT: `role`, `is_superuser` desde `user.hps_profile.role.name` y `user.is_superuser`. |
| `hps_agent/services/role_config.py` | Mensajes de bienvenida y sugerencias por `role_name` (member, admin, jefe_seguridad, etc.). |
| `hps_agent/consumers.py` (referido en resumen) | Uso de RoleConfig por rol para sugerencias/bienvenida. |

---

## 4. Tabla resumen: endpoints y control de acceso

### 4.1 HPS Core

| Recurso / endpoint | Clase de permiso | Filtro get_queryset / condición objeto | Permiso implícito (a extraer) |
|--------------------|------------------|----------------------------------------|--------------------------------|
| `GET/POST /hps/roles/` (CRUD) | IsAuthenticated, IsHpsAdmin | — | hps.gestionar_roles |
| `GET/POST/PUT... /hps/teams/` | IsAuthenticated, IsHpsAdminOrTeamLead | Admin: todos; team_lead: solo equipos que lidera | hps.ver_equipos (scope: all | team_led) |
| `GET/POST... /hps/requests/` | IsAuthenticated, HasHpsProfile | Admin: todos; team_lead: equipos que lidera; resto: propios | hps.ver_solicitudes (scope: all | team_led | own) |
| `POST /hps/requests/public/` | AllowAny | — | (público) |
| `GET/POST... /hps/tokens/` | create: IsHpsAdminOrSecurityChief; list/retrieve: IsHpsAdmin | — | hps.crear_tokens, hps.ver_tokens |
| `GET /hps/tokens/validate/` | AllowAny | — | (público) |
| `GET/POST... /hps/templates/` | IsAuthenticated, IsHpsAdminOrSecurityChief | — | hps.gestionar_plantillas |
| `GET... /hps/audit-logs/` | IsAuthenticated, IsHpsAdminOrSelf | Solo propios si no admin | hps.ver_audit_logs (scope: all | own) |
| `GET/POST/PUT... /hps/user/profiles/` | HasHpsProfile; create: IsHpsAdminOrTeamLead; update/destroy: IsHpsAdminOrTeamLeadEditingLedMember | Admin/crypto: todos; team_lead: equipos que lidera; create solo en equipos que lidera | hps.ver_perfiles, hps.crear_perfil (scope), hps.editar_perfil_equipo (object) |
| Extension (personas, estado, etc.) | AllowAny | — | (público / extensión) |
| `GET/POST... /hps/chat/conversations/` | IsAuthenticated | is_staff/superuser: todas; resto: propias | hps.ver_todas_conversaciones (o solo propias) |
| `GET /hps/chat/conversations/all/` | IsAuthenticated | is_staff o is_superuser | hps.ver_todas_conversaciones |
| `GET/POST... /hps/chat/messages/` | IsAuthenticated | — | (por conversación: propio o admin) |

### 4.2 Productos (CryptoTrace)

| Recurso / lógica | Permiso de clase | Lógica adicional | Permiso implícito |
|------------------|------------------|------------------|--------------------|
| LineaTemporalProducto: list/retrieve | IsAuthenticated | has_admin_permissions → todos o solo usuario | productos.ver_toda_linea_temporal (all) vs solo propios |
| LineaTemporalProducto: limpiar registros | IsAuthenticated | has_admin_permissions → borrar todos o solo propios | productos.limpiar_toda_linea_temporal |
| Resto ViewSets productos | IsAuthenticated | — | (autenticado basta) |

---

## 5. Diseño RBAC "de libro"

### 5.1 Modelo de permisos

Se propone un único modelo de permisos dentro del dominio HPS, pero con codenames que permitan extender a productos u otras apps:

- **Modelo:** `HpsPermission` (en `hps_core`).
- **Campos sugeridos:**
  - `codename`: único, ej. `hps.gestionar_roles`, `productos.ver_toda_linea_temporal`.
  - `name`: descripción legible.
  - `category`: opcional, ej. `hps`, `productos`, `chat`.

Relación:

- **HpsRole** ↔ **HpsPermission**: ManyToMany (tabla intermedia `hps_role_permissions` o `HpsRole.permissions` M2M).
- El campo actual `HpsRole.permissions` (JSONField) puede dejarse para metadata o deprecarse tras migración.

Obtención de permisos del usuario:

- Usuario → `hps_profile` → `role` → `role.permissions.all()` (codename).
- Helper: `user_has_perm(user, codename)` que tenga en cuenta también `is_superuser` como bypass opcional si se desea.

### 5.2 Listado de permisos propuestos

Permisos a crear y asignar a roles según comportamiento actual:

| Codename | Nombre (resumen) | Asignar a roles (actual) |
|----------|-------------------|---------------------------|
| `hps.ver_perfil` | Tener perfil HPS (acceso mínimo) | Todos los que tienen perfil (implícito al tener rol) |
| `hps.gestionar_roles` | Gestionar roles HPS | admin |
| `hps.ver_equipos_todos` | Ver todos los equipos | admin |
| `hps.ver_equipos_liderados` | Ver equipos que lidera | team_lead, jefe_seguridad_suplente |
| `hps.gestionar_equipos` | Crear/editar/eliminar equipos | admin, team_lead, jefe_seguridad_suplente (según scope) |
| `hps.ver_solicitudes_todas` | Ver todas las solicitudes HPS | admin |
| `hps.ver_solicitudes_equipos` | Ver solicitudes de equipos que lidera | team_lead, jefe_seguridad_suplente |
| `hps.ver_solicitudes_propias` | Ver propias solicitudes | member, crypto, todos |
| `hps.crear_tokens` | Crear tokens HPS | admin, jefe_seguridad, jefe_seguridad_suplente |
| `hps.ver_todos_tokens` | Listar/ver todos los tokens | admin |
| `hps.gestionar_plantillas` | Gestionar plantillas PDF | admin, jefe_seguridad, jefe_seguridad_suplente |
| `hps.ver_audit_logs_todos` | Ver todos los audit logs | admin |
| `hps.ver_audit_logs_propios` | Ver propios audit logs | member, team_lead, crypto, etc. |
| `hps.ver_perfiles_todos` | Ver todos los perfiles | admin, jefe_seguridad, jefe_seguridad_suplente, crypto |
| `hps.ver_perfiles_equipos` | Ver perfiles de equipos que lidera | team_lead |
| `hps.crear_perfil` | Crear perfiles (en equipos que lidera si no admin) | admin, team_lead, jefe_seguridad_suplente |
| `hps.editar_perfil_equipo` | Editar/activar/desactivar perfiles de miembros de equipos que lidera | admin, team_lead (object-level) |
| `hps.asignar_rol` | Asignar roles a usuarios | admin (cualquier rol); jefe_seguridad/jefe_suplente (solo crypto, member) — puede modelarse con permiso + allowed_roles en BD o lógica por rol hasta tener permisos más finos |
| `chat.ver_todas_conversaciones` | Ver listado global de conversaciones | admin (hoy is_staff/superuser) |
| `productos.ver_toda_linea_temporal` | Ver toda la línea temporal de productos | admin, crypto, jefe_seguridad, jefe_seguridad_suplente |
| `productos.limpiar_toda_linea_temporal` | Limpiar registros de cualquier usuario en línea temporal | Mismos que ver_toda_linea_temporal |

La asignación "quién puede asignar qué rol" puede quedarse en una tabla o en reglas por permiso (ej. `hps.asignar_rol_admin`, `hps.asignar_rol_crypto_member`) en una segunda fase.

### 5.3 Alcance (scope) y permisos por objeto

- Donde hoy se filtra por "solo equipos que lidero" o "solo propios", se mantiene la **lógica de filtrado** en `get_queryset` o `has_object_permission`, pero la **condición de entrada** (¿puede este usuario acceder a este recurso?) se basa en si tiene el permiso correspondiente (ej. `hps.ver_solicitudes_equipos` + pertenencia al equipo liderado).
- Es decir: el permiso abre la "puerta" (p.ej. ver solicitudes de equipos); el queryset/object permission restringe a "equipos que lidera" o "objeto es propio".

### 5.4 JWT y frontend

- El JWT puede seguir incluyendo `role` (nombre) para compatibilidad con el frontend.
- Opcional: añadir `permissions: ["hps.ver_solicitudes_todas", ...]` para que el frontend oculte/muestre acciones sin round-trip. No es obligatorio para el RBAC en backend.

### 5.5 Chat: reemplazo de is_staff / is_superuser

- Crear permiso `chat.ver_todas_conversaciones`.
- Asignarlo al rol `admin` (y si se desea a staff/superuser por defecto en el helper).
- En `ChatConversationViewSet.get_queryset` y en `all_conversations` / `full`: comprobar `user_has_perm(user, 'chat.ver_todas_conversaciones')` en lugar de `is_staff or is_superuser`, o además de ellos durante transición.

---

## 6. Estrategia de migración

### Fase 1: Modelos y datos

1. Crear modelo `HpsPermission` (codename, name, category).
2. Añadir M2M `HpsRole.permissions` (through opcional si no se necesita metadata).
3. Migración de datos: insertar todos los codenames de la tabla anterior; asignar a cada `HpsRole` los permisos según la matriz (tabla 5.2).
4. Mantener `HpsRole.permissions` (JSON) sin uso en autorización hasta decidir eliminación.

### Fase 2: Helper y clases de permiso

1. Implementar `user_has_perm(user, codename)` (y opcionalmente `get_user_permissions(user)`).
   - Considerar: usuario sin perfil HPS → sin permisos HPS; `is_superuser` → todos los permisos si se desea.
2. Crear clases de permiso genéricas que usen el helper, por ejemplo:
   - `HasHpsPerm('hps.gestionar_roles')`
   - `HasHpsPermAny(['hps.ver_solicitudes_todas', 'hps.ver_solicitudes_equipos'])` para combinar con get_queryset por scope.
3. Sustituir progresivamente `IsHpsAdmin`, `IsHpsAdminOrTeamLead`, etc., por estas clases basadas en permisos.

### Fase 3: Vistas y get_queryset

1. Reemplazar en cada vista la lectura de `role_name in ADMIN_ROLES` / `has_team_lead_permissions` por comprobaciones `user_has_perm(user, '...')` y el mismo filtrado por scope (equipos liderados, propio).
2. En productos: sustituir `has_admin_permissions` por `user_has_perm(user, 'productos.ver_toda_linea_temporal')` y `productos.limpiar_toda_linea_temporal`.
3. En chat: sustituir `is_staff or is_superuser` por `user_has_perm(user, 'chat.ver_todas_conversaciones')` (con o sin fallback a staff/superuser en transición).

### Fase 4: Serializers (asignación de roles)

1. Introducir permiso `hps.asignar_rol` (y opcionalmente permisos más granulares por rol destino).
2. En `HpsUserProfileCreateSerializer` y `HpsUserProfileSerializer.update`: en lugar de ramas por `current_role_name`, usar:
   - Si no tiene `hps.asignar_rol` → no puede cambiar rol (o forzar member según regla).
   - Si tiene permiso, opción A: mantener matriz "allowed_roles" por rol en código una temporada; opción B: tabla RoleAssignmentRule (quién puede asignar qué roles) y validar contra ella.

### Fase 5: JWT y RoleConfig

1. JWT: mantener `role`; opcional añadir `permissions` para frontend.
2. RoleConfig (agente): puede seguir usando `role_name` para sugerencias/bienvenida; no es autorización, solo UX.

### Fase 6: Limpieza

1. Eliminar constantes `ADMIN_ROLES`, `TEAM_LEADS`, `TEAM_ROLES` de permisos y vistas una vez todo use permisos.
2. Revisar que no queden referencias a `role.name` para autorización (sí para mostrar en UI o para RoleConfig).
3. Documentar en código que la fuente de verdad para autorización son los permisos del rol.

---

## 7. Fases resumidas (checklist para revisión)

| Fase | Contenido |
|------|------------|
| 1 | Modelo `HpsPermission`, M2M con `HpsRole`, migración de datos (matriz rol–permiso). |
| 2 | Helper `user_has_perm`, clases `HasHpsPerm` / `HasHpsPermAny`, sustituir clases actuales en vistas. |
| 3 | Sustituir lógica inline en get_queryset y acciones (hps_core, productos, chat) por chequeos de permisos. |
| 4 | Serializers: permiso `hps.asignar_rol` y reglas de asignación (en código o BD). |
| 5 | JWT (opcional permissions) y RoleConfig sin cambios de autorización. |
| 6 | Eliminar constantes de roles en código y documentar RBAC. |

---

## 8. Referencias de código

- Roles y perfiles: `hps_core/models.py` (HpsRole, HpsUserProfile).
- Permisos actuales: `hps_core/permissions.py`.
- Vistas HPS: `hps_core/views.py`.
- Serializers HPS (asignación de roles): `hps_core/serializers.py` (create/update con role_writable).
- Productos (línea temporal): `productos/views.py` (LineaTemporalProductoViewSet, acción limpiar).
- JWT: `productos/serializers.py` (CustomTokenObtainPairSerializer).
- Chat: `hps_core/views.py` (ChatConversationViewSet, ChatMessageViewSet).
- Servicios: `hps_core/services.py` (plantilla por rol solicitante).
- Agente: `hps_agent/services/role_config.py`, `hps_agent/consumers.py`.

Este documento sirve como base para la revisión y, una vez aprobado, para implementar el RBAC global por fases sin romper el comportamiento actual.
