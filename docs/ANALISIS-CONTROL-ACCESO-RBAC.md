# Análisis del control de acceso en el sistema

## ¿Tenemos RBAC (control de acceso basado en roles)?

**Sí, con matices.** El sistema usa **control de acceso basado en roles (RBAC)** en el sentido de que las decisiones de autorización dependen del **rol** del usuario. No es un RBAC “puro” con entidades Permiso asignadas a roles; el vínculo rol → qué puede hacer está **en código** (clases de permisos y lógica en vistas).

---

## 1. Dónde están los roles

- **Modelo:** `hps_core.models.HpsRole`  
  - Campos: `name`, `description`, `permissions` (JSONField; no se usa para autorización en la práctica).
- **Asignación al usuario:** `hps_core.models.HpsUserProfile`  
  - Cada usuario (Django) puede tener un perfil HPS con `role` (FK a `HpsRole`).
- **Nombres de rol usados en código:**  
  `admin`, `jefe_seguridad`, `jefe_seguridad_suplente`, `team_lead`, `member`, `crypto`.

El rol se obtiene siempre de `user.hps_profile.role.name` (o del JWT, que incluye ese rol).

---

## 2. Cómo se controla el acceso

### 2.1 Autenticación

- **JWT (SimpleJWT):** login en `api/token/` con `CustomTokenObtainPairSerializer`.
- El token incluye, entre otros: `role`, `team_id`, `team_ids`, `led_team_ids`, `default_team_id`, `must_change_password`, además de los claims estándar.
- El rol en el token viene de `user.hps_profile.role.name`.

### 2.2 Autorización (permisos en backend)

Hay dos capas:

**A) Permisos de Django REST / clases de permiso**

- **`IsAuthenticated`**  
  Solo exige usuario autenticado. Se usa en la mayoría de vistas de `productos` y en muchas de `hps_core` (chat, etc.).
- **Clases propias en `hps_core.permissions`** (todas basadas en el **rol** y, en su caso, en equipos):
  - **`HasHpsProfile`**  
    Exige que el usuario tenga perfil HPS.
  - **`IsHpsAdmin`**  
    Solo si `role_name in ADMIN_ROLES` → `admin`, `jefe_seguridad`, `jefe_seguridad_suplente`.
  - **`IsHpsAdminOrTeamLead`**  
    Admin o rol en `TEAM_LEADS` (`team_lead`, `jefe_seguridad_suplente`) o ser líder de algún equipo activo.
  - **`IsHpsAdminOrSecurityChief`**  
    Admin o `jefe_seguridad` o `jefe_seguridad_suplente`.
  - **`IsHpsAdminOrSelf`**  
    Admin puede todo; el resto solo puede acceder al objeto si es “suyo” (`user_id == request.user.id`).
  - **`IsHpsAdminOrTeamLeadEditingLedMember`**  
    Admin puede todo; team lead solo puede editar perfiles de usuarios que pertenecen a equipos que él lidera.

**B) Lógica adicional en vistas**

- **Chat / conversaciones:**  
  Por ejemplo `ChatConversationViewSet.all_conversations` exige `request.user.is_staff or request.user.is_superuser` (Django nativo).
- **Productos (CryptoTrace):**  
  - La mayoría de ViewSets usan solo `IsAuthenticated`.
  - En `LineaTemporalProductoViewSet` y en la acción de “limpiar” registros se calcula `has_admin_permissions` con:
    - `user.hps_profile.role.name in ['admin', 'crypto', 'jefe_seguridad', 'jefe_seguridad_suplente']`
    - o `user.is_superuser` como respaldo.
  - Así se decide si el usuario ve solo sus registros o todos.

En conjunto: el control es **por rol** (y a veces por “ser dueño del recurso” o “liderar el equipo del recurso”), no por una tabla de “permisos” asociados al rol.

---

## 3. Resumen: tipo de control de acceso

| Aspecto | Qué hay en el sistema |
|--------|------------------------|
| **Modelo de roles** | Sí: `HpsRole` + asignación en `HpsUserProfile`. |
| **Permisos como entidades** | No. El campo `HpsRole.permissions` (JSON) no se usa para autorización. |
| **Quién puede hacer qué** | Definido en código: conjuntos de roles (`ADMIN_ROLES`, `TEAM_LEADS`) y reglas en clases de permiso y en vistas. |
| **Alcance del acceso** | Por rol y por recurso: “solo los míos”, “solo usuarios de equipos que lidero”, “solo si soy admin/jefe_seguridad/…”. |
| **Django staff/superuser** | Se usa en algunos sitios (p. ej. listado de todas las conversaciones de chat). |

Es decir: **RBAC por rol**, con **reglas de alcance** (propietario, equipo liderado) y uso puntual de **staff/superuser** de Django. No es un RBAC con tabla de permisos granulares (p. ej. “crear_solicitud”, “aprobar_hps”) asignados a cada rol.

---

## 4. Mapa rápido por área

- **HPS (solicitudes, equipos, perfiles, chat):**  
  `hps_core.permissions` + rol en perfil HPS (+ equipos/membresías y “líder de equipo”).
- **Chat (listado global de conversaciones):**  
  `is_staff` o `is_superuser`.
- **Productos / CryptoTrace (albaranes, línea temporal, empresas, etc.):**  
  En su mayoría solo `IsAuthenticated`; la parte “admin” (ver todo / limpiar) usa rol HPS `admin`, `crypto`, `jefe_seguridad`, `jefe_seguridad_suplente` o `is_superuser`.

Si quieres, el siguiente paso puede ser proponer una tabla “Rol → acciones permitidas” a partir de este análisis o esbozar un RBAC más fino con permisos explícitos.
