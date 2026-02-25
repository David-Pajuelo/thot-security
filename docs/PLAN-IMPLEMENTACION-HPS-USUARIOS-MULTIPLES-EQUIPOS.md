# Plan de implementación: usuarios HPS asociados a múltiples equipos

## 1. Objetivo

Permitir que **un usuario HPS pueda pertenecer a más de un equipo**. Esto implica:

- **Visualización**: Mostrar a qué equipos pertenece cada usuario (listas, perfiles, informes).
- **Chat IA**: Cuando un jefe de equipo o jefe de seguridad busque miembros, el agente debe considerar **todos los equipos a los que pertenece el usuario** y no asumir un único equipo.
- **Tipado**: Evitar errores de tipo en frontend (JS/TS) y backend (Python): todos los puntos que hoy usan `team_id` / `team_name` (singular) deben actualizarse a estructuras que soporten varios equipos donde corresponda.

**Estado actual**: La relación efectiva es **1:1** mediante `HpsUserProfile.team` (ForeignKey nullable). Existe el modelo `HpsTeamMembership` (team, user, is_active, is_lead) con `unique_together = ("team", "user")` pero **no se usa** para listar miembros ni para permisos; los miembros se obtienen con `HpsUserProfile.objects.filter(team=team)`.

---

## 2. Estrategia de modelo y datos

### 2.1 Fuente de verdad: HpsTeamMembership

- **Usar `HpsTeamMembership`** como fuente de verdad para la relación usuario ↔ equipos (N:N).
- **Migración de datos**: Para cada `HpsUserProfile` que tenga `team` no nulo, crear (si no existe) `HpsTeamMembership(team=profile.team, user=profile.user, is_active=True, is_lead=(profile.user_id == profile.team.team_lead_id))`.
- **`HpsUserProfile.team`**: Mantener el campo de forma **opcional y derivada** durante la transición (por ejemplo, sincronizar con “primer equipo” de memberships para compatibilidad) y documentar como deprecado; en una fase posterior se puede eliminar en una migración futura para simplificar. Alternativa: eliminar su uso en lectura y dejar solo para escritura legacy si algún flujo lo requiere.

### 2.2 Conteo y listado de miembros por equipo

- **`HpsTeam.member_count`**: Cambiar de `HpsUserProfile.objects.filter(team=self)` a `HpsTeamMembership.objects.filter(team=self, is_active=True).count()`.
- **Miembros de un equipo**: Obtener vía `HpsTeamMembership.objects.filter(team=team, is_active=True).select_related('user')` (y perfil/rol según necesidad), no vía `HpsUserProfile.objects.filter(team=team)`.

### 2.3 “Usuario pertenece al equipo X”

- Sustituir todas las comprobaciones del tipo `profile.team_id == team_id` o `user.hps_profile.team == team` por:  
  `HpsTeamMembership.objects.filter(user=user, team=team, is_active=True).exists()`  
  o, si se expone desde el perfil, un helper/property en el perfil que consulte memberships.

---

## 3. Archivos a modificar (por área)

### 3.1 Backend – Modelos y migraciones

| Archivo | Acción |
|--------|--------|
| `cryptotrace/cryptotrace-backend/src/hps_core/models.py` | (1) Añadir en `HpsTeam` un método o property `get_member_ids()` (o equivalente) que use `HpsTeamMembership`. (2) Cambiar `member_count` para que use `HpsTeamMembership`. (3) En `HpsUserProfile` opcional: añadir property `teams` que devuelva los equipos vía memberships (y opcionalmente mantener `team` como “primer equipo” si se mantiene el campo). |
| Nueva migración en `hps_core/migrations/` | (1) Migración de datos: crear `HpsTeamMembership` para cada perfil con `team` no nulo. (2) No eliminar aún la columna `HpsUserProfile.team` si se mantiene como deprecada. |

### 3.2 Backend – Serializers

| Archivo | Acción |
|--------|--------|
| `cryptotrace/cryptotrace-backend/src/hps_core/serializers.py` | (1) **HpsUserProfileSerializer**: Sustituir `team_id` / `team_name` (singular) por `team_ids` (lista de UUIDs) y `teams` (lista de `{ id, name }`). Mantener opcionalmente `team_id`/`team_name` como “primer equipo” para compatibilidad si se desea. (2) Escritura: aceptar `team_ids` (lista) y/o `team_id_writable` (singular) y actualizar **HpsTeamMembership** (añadir/eliminar memberships) en lugar de asignar solo `profile.team`. (3) **HpsTeamSerializer.get_members**: Obtener miembros vía `HpsTeamMembership.objects.filter(team=obj, is_active=True)` y construir la lista desde ahí (user, role desde perfil). (4) Validaciones y `create`/`update`: asegurar que al crear/actualizar usuario se crean/actualizan memberships y, si se mantiene, se sincroniza `profile.team` con el primer equipo. |

### 3.3 Backend – Vistas y URLs

| Archivo | Acción |
|--------|--------|
| `cryptotrace/cryptotrace-backend/src/hps_core/views.py` | (1) Filtros por equipo: donde se use `user__hps_profile__team_id=team_id`, cambiar a “usuario que tenga membership activa en ese equipo” (p. ej. filtro por `user__hps_team_memberships__team_id=team_id`, `user__hps_team_memberships__is_active=True`). (2) Permisos team_lead: si un jefe solo puede ver “su equipo”, considerar “cualquiera de sus equipos” (donde sea team_lead) y filtrar por memberships. (3) `search_users` y respuestas que incluyan equipo: devolver `team_ids` y `teams` (lista) en lugar de un solo `team_id`/`team_name`. |
| `cryptotrace/cryptotrace-backend/src/hps_core/urls.py` | (1) Vista que devuelve perfil (`hps_user_profile`): devolver `team_ids` y `teams` (lista); opcional mantener `team_id`/`team_name` como primer equipo. |

### 3.4 Backend – Permisos y contexto

| Archivo | Acción |
|--------|--------|
| `cryptotrace/cryptotrace-backend/src/hps_core/permissions.py` | (1) Donde se construye contexto con `team_id` (singular), cambiar a `team_ids` (lista) y opcionalmente `team_id` como primer equipo. Asegurar que los tipos (Optional[int] vs list, etc.) sean coherentes. |

### 3.5 Backend – Agente IA (Chat)

| Archivo | Acción |
|--------|--------|
| `cryptotrace/cryptotrace-backend/src/hps_agent/services/command_processor.py` | (1) **_get_team_hps**: En lugar de `user.hps_profile.team`, obtener todos los equipos del usuario vía `HpsTeamMembership`; para cada equipo, obtener user_ids de miembros y reunir HPS de todos esos usuarios (o definir si “HPS de mi equipo” es por cada equipo por separado). (2) **_get_users_list**: team_lead debe ver usuarios que compartan **al menos un equipo** con él (memberships). (3) **_consultar_hps_equipo**: Basar en equipos del usuario (memberships). (4) **_asignar_usuario_equipo** / **_assign_user_to_team_in_db**: Añadir usuario al equipo = crear/activar `HpsTeamMembership`; no sobrescribir un único `profile.team`. Si se permite “quitar de un equipo”, desactivar o eliminar membership. (5) **_dar_alta_jefe_equipo** / **_create_team_lead_in_db**: Asignar equipos vía memberships. (6) Creación de usuario desde chat: asignar a uno o varios equipos vía memberships. (7) Cualquier comparación `user.hps_profile.team == team` o `profile.team_id` sustituir por comprobación de membership. |
| `cryptotrace/cryptotrace-backend/src/hps_agent/consumers.py` | (1) Contexto enviado al agente: incluir `team_ids` (lista) y opcionalmente `team_id` (primer equipo). Evitar que el agente asuma un único equipo. |
| `cryptotrace/cryptotrace-backend/src/hps_agent/services/openai_service.py` | (1) Prompts que usen “Equipo: …” o “team_id”: actualizar a “Equipos: …” / lista de equipos para no inducir un único equipo. |
| `cryptotrace/cryptotrace-backend/src/hps_agent/services/role_config.py` | (1) Textos que digan “tu equipo” o “mi equipo”: ajustar a “tus equipos” / “los equipos a los que perteneces” donde tenga sentido. |

### 3.6 Backend – Servicios, señales y comandos de gestión

| Archivo | Acción |
|--------|--------|
| `cryptotrace/cryptotrace-backend/src/hps_core/signals.py` | (1) Donde se asigna `profile.team = aicox_team`: crear `HpsTeamMembership(team=aicox_team, user=profile.user, is_active=True)` y opcionalmente mantener `profile.team = aicox_team`. |
| `cryptotrace/cryptotrace-backend/src/hps_core/services.py` | (1) Cualquier asignación a `profile.team`: sustituir o complementar con creación/actualización de memberships. |
| `cryptotrace/cryptotrace-backend/src/hps_core/management/commands/assign_all_users_to_aicox.py` | (1) Asegurar que se crea membership en AICOX (y opcionalmente `profile.team`). |
| `cryptotrace/cryptotrace-backend/src/hps_core/management/commands/create_users_from_existing_roles.py` | (1) Asignación a equipo: usar memberships. |
| `cryptotrace/cryptotrace-backend/src/hps_core/management/commands/setup_hps_initial_data.py` | (1) Crear memberships además de asignar `profile.team` si se mantiene. |
| `cryptotrace/cryptotrace-backend/src/hps_core/management/commands/check_user_data.py` | (1) Mostrar equipos del usuario vía memberships (y opcionalmente “equipo principal”). |
| `cryptotrace/cryptotrace-backend/src/hps_core/management/commands/check_hps_data.py` | (1) Listar miembros por equipo vía `HpsTeamMembership`. |
| `cryptotrace/cryptotrace-backend/src/hps_core/management/commands/test_authentication.py` | (1) Mostrar equipos (lista) del usuario. |
| Resto de commands en `hps_core/management/commands/` | Revisar cualquier uso de `profile.team` o filtro por equipo y actualizar a memberships. |

### 3.7 Frontend HPS

| Archivo | Acción |
|--------|--------|
| `hps-system/frontend/src/store/authStore.js` | (1) Estado de usuario: además de o en lugar de `team_id`/`team_name`, guardar `team_ids` (array) y `teams` (array de `{ id, name }`). (2) Inicialización desde perfil/API: mapear respuesta a `teams`/`team_ids`. (3) Evitar asumir un único equipo en lógica de permisos o navegación. |
| `hps-system/frontend/src/services/apiService.js` | (1) Transformación de perfiles: si la API devuelve `teams`/`team_ids`, conservarlos; si solo devuelve `team_id`/`team_name`, construir array de un elemento para compatibilidad. (2) Tipos/documentación: usuario debe tener `teams: Array<{ id, name }>`, `team_ids: Array<string>`. |
| `hps-system/frontend/src/config/api.js` | Sin cambios de rutas si los endpoints siguen siendo por team_id para “miembros de un equipo”; revisar si hace falta algún endpoint nuevo (ej. “equipos del usuario” ya puede ser el perfil). |
| `hps-system/frontend/src/pages/UserManagement.jsx` | (1) Tabla: mostrar “Equipos” como lista de nombres (o “Equipo 1, Equipo 2”) en lugar de una sola celda “Equipo”. (2) Detalle y formularios: selector **múltiple** de equipos (multi-select); guardar como `team_ids`. (3) Crear/editar usuario: enviar `team_ids` (array); no depender de un solo `team_id`. |
| `hps-system/frontend/src/pages/TeamManagement.jsx` | (1) Si se usa “mi equipo” para el jefe: considerar “mis equipos” (donde es team_lead o donde tiene membership). (2) Carga de miembros: seguir usando endpoint por team_id; la API ya devolverá miembros vía memberships. (3) Mensaje “No tienes un equipo asignado”: cambiar a “No tienes equipos asignados” si se muestra cuando `teams` está vacío. |
| `hps-system/frontend/src/components/Dashboard.jsx` | (1) Referencias a “tu equipo” / “team_id”: usar “tus equipos” / `teams` (array). |
| `hps-system/frontend/src/pages/ReportsPage.jsx` | (1) Mostrar equipos del usuario como lista (p. ej. “Equipo A, Equipo B”) en lugar de un solo `user.team?.name`. |
| `hps-system/frontend/src/components/Chat.jsx` | (1) Contexto enviado al backend: incluir `team_ids` (array) y opcionalmente `teams`; no enviar solo `team_id`/`team_name` como si fuera único. |

### 3.8 Tipado y contratos

- **Backend**: En serializers y vistas, documentar o tipar (type hints) que los campos de equipos del usuario son listas (`team_ids: list[str]`, `teams: list[dict]`). Revisar `permissions.HpsProfileContext` para que `team_ids` sea lista.
- **Frontend**: Si existe tipado (TypeScript o JSDoc), actualizar interfaces de usuario para que `team_id`/`team_name` sean opcionales o deprecados y usar `teams: Array<{ id: string, name: string }>`, `team_ids: string[]`. Evitar código que asuma `user.team_id` como único.

### 3.9 Documentación y pruebas

| Área | Acción |
|------|--------|
| `hps-system/docs/` (planificacion, arquitectura, testing, estado-integracion-agente, migracion-agente-ia-django) | Actualizar menciones de “un equipo por usuario” a “usuarios pueden pertenecer a varios equipos”. Documentar que la fuente de verdad es `HpsTeamMembership` y que `HpsUserProfile.team` está deprecado o es secundario. |
| `docs/AUDITORIA-PARIDAD-HPS-DJANGO-VS-FASTAPI.md`, `docs/produccion/GUIA-PRUEBAS-HPS-INTEGRACION.md`, archivados | Revisar y actualizar descripción de equipos y miembros. |
| Tests (si existen) en backend/frontend para equipos y chat | Ajustar fixtures y aserciones a múltiples equipos y a memberships. |

---

## 4. Orden sugerido de implementación

1. **Migración de datos y modelo**  
   - Migración que cree `HpsTeamMembership` desde `HpsUserProfile.team`.  
   - Ajustar `HpsTeam.member_count` y cualquier helper de “miembros” a memberships.

2. **Backend: serializers y API**  
   - Serializers: leer/escribir `teams`/`team_ids` y actualizar memberships.  
   - Views y URLs: filtros por membership; respuestas con listas de equipos.

3. **Backend: permisos y contexto**  
   - `team_ids` en contexto de perfil y permisos.

4. **Agente IA**  
   - command_processor, consumers, openai_service, role_config: equipos como lista y lógica por memberships.

5. **Frontend**  
   - authStore, apiService, UserManagement (multi-select equipos), TeamManagement, Dashboard, ReportsPage, Chat.

6. **Señales, servicios y management commands**  
   - Sustituir o complementar asignaciones a `profile.team` con memberships.

7. **Documentación y pruebas**  
   - Actualizar docs y tests; comprobar que no quede ninguna referencia a “un solo equipo” que rompa el flujo.

---

## 5. Comprobación final (checklist)

- [ ] Ningún filtro de “miembros del equipo” usa solo `HpsUserProfile.team`; todos usan `HpsTeamMembership`.
- [ ] Ningún serializer ni respuesta de API asume un único `team_id`/`team_name` para el usuario sin ofrecer `teams`/`team_ids`.
- [ ] Chat: jefe de equipo / jefe de seguridad ven miembros de **todos los equipos** a los que pertenecen (o por equipo según regla de negocio).
- [ ] Frontend: formularios de usuario permiten seleccionar varios equipos y envían `team_ids`.
- [ ] Frontend: listados y perfiles muestran varios equipos (nombres o badges).
- [ ] Tipado: no hay usos de `user.team_id` como único en lugares que deban soportar varios equipos; tipos reflejan listas donde corresponda.
- [ ] Documentación y comentarios actualizados; management commands y señales coherentes con memberships.

---

## 6. Lista única de archivos (referencia rápida)

**Backend (cryptotrace):**  
`hps_core/models.py`, `hps_core/serializers.py`, `hps_core/views.py`, `hps_core/urls.py`, `hps_core/permissions.py`, `hps_core/signals.py`, `hps_core/services.py`, `hps_core/admin.py` (si lista miembros por equipo), `hps_agent/services/command_processor.py`, `hps_agent/consumers.py`, `hps_agent/services/openai_service.py`, `hps_agent/services/role_config.py`, migración nueva en `hps_core/migrations/`, y todos los `hps_core/management/commands/*.py` que usen `profile.team` o equipos.

**Frontend (hps-system):**  
`frontend/src/store/authStore.js`, `frontend/src/services/apiService.js`, `frontend/src/pages/UserManagement.jsx`, `frontend/src/pages/TeamManagement.jsx`, `frontend/src/components/Dashboard.jsx`, `frontend/src/pages/ReportsPage.jsx`, `frontend/src/components/Chat.jsx`, y si aplica `config/api.js`, `services/hpsService.js`.

**Documentación:**  
Todos los documentos listados en la sección 3.9 y cualquier otro que mencione “equipo del usuario” o “user.team” en el contexto HPS.

Este plan debe ejecutarse sin dejar referencias sin actualizar a “un equipo por usuario” en los flujos críticos (API, chat, permisos, UI) para evitar errores de comportamiento y de tipado.
