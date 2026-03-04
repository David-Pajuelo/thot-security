# Plan: Agente IA y “Mi equipo” por equipos liderados

## Objetivo

Que un **líder de equipo** (rol `team_lead`) que puede ser líder de **varios equipos** solo vea y actúe sobre:
- **Equipos que lidera** (donde `HpsTeam.team_lead = usuario`),  
y no sobre todos los equipos en los que es **miembro** (`team_ids` / `HpsTeamMembership`).

Esto afecta al **agente IA del chat** y al **dashboard “Mi equipo”** del frontend.

---

## Comportamiento actual (resumen)

### 1. Agente IA (`hps_agent/services/command_processor.py`)

| Funcionalidad | Criterio actual | Fuente |
|---------------|-----------------|--------|
| **“HPS de mi equipo”** (`_get_team_hps`) | HPS de usuarios que están en **cualquier equipo del que el usuario es miembro** | `user_team_ids` = `HpsTeamMembership` del usuario |
| **Listar usuarios** (`_get_users_list`) | Usuarios que comparten **al menos un equipo** con el líder (memberships) | Mismo `user_team_ids` |
| **Aprobar HPS** (`_approve_hps_in_db`) | Si el solicitante comparte **al menos un equipo** con el aprobador (memberships) | `approver_team_ids` ∩ `user_team_ids` |
| **Rechazar HPS** (`_reject_hps_in_db`) | Mismo criterio que aprobar | Idem |
| **Asignar usuario a equipo** | Solo a equipos en los que el líder **está** (memberships) | `user_context["team_ids"]` |

Es decir: hoy todo se basa en **equipos en los que el usuario es miembro** (`team_ids`), no en **equipos que lidera**.

### 2. Backend REST (`hps_core/views.py`)

| Vista / filtro | Criterio actual |
|----------------|------------------|
| **HpsRequestViewSet.get_queryset()** (solicitudes HPS) | Team lead ve solicitudes de usuarios que comparten **al menos un equipo** con él (memberships). |
| **HpsUserProfileViewSet.get_queryset()** (listado perfiles) | Team lead ve perfiles de usuarios que comparten **al menos un equipo** con él (memberships). |

Misma lógica: **memberships** del usuario, no equipos donde es **líder**.

### 3. Frontend

| Componente | Comportamiento actual |
|------------|------------------------|
| **Dashboard** | Muestra “Mi equipo” si `isTeamLeader()` (rol). No distingue equipos liderados. |
| **TeamManagement (“Mi equipo”)** | Usa **un solo** `user.team_id` (primer equipo del usuario) y carga `getTeamMembers(user.team_id)`. No hay noción de “equipos que lidero” ni selector. |
| **Chat** | Envía `team_ids` (equipos donde es miembro) en el contexto. No envía “equipos que lidero”. |
| **JWT / perfil** | El backend devuelve `team_ids` y `teams` (memberships). No expone `led_team_ids` ni “equipos que lidero”. |

---

## Cambio conceptual

- **Antes:** team_lead ve/actúa sobre usuarios de **todos los equipos en los que está** (memberships).
- **Después:** team_lead ve/actúa solo sobre usuarios de **los equipos que lidera** (`HpsTeam.team_lead = usuario`).

Para ello hace falta:

1. **Backend:** en los sitios donde hoy se usa “equipos del usuario” para permisos de team_lead, usar **“equipos que el usuario lidera”** (por ejemplo `led_team_ids` = IDs de `HpsTeam` donde `team_lead=request.user`).
2. **Agente IA:** mismo criterio en `_get_team_hps`, `_get_users_list`, aprobar, rechazar y asignar a equipo (usar equipos liderados, no `team_ids` del contexto).
3. **Frontend / API:** que el usuario tenga disponible **qué equipos lidera** (p. ej. `led_team_ids` / `led_teams` en perfil y/o JWT) y que “Mi equipo” y el chat usen esa información.

---

## Archivos a tocar (checklist de análisis)

- **Backend**
  - `hps_core/views.py`: filtros team_lead en `HpsRequestViewSet` y `HpsUserProfileViewSet` (usar equipos liderados).
  - `hps_core/permissions.py`: ya usa `is_team_lead`; podría añadirse `led_team_ids` al contexto si se usa en vistas.
  - `hps_core/urls.py` (o vista de perfil): devolver `led_team_ids` / `led_teams` en el perfil HPS.
  - `productos/serializers.py` (JWT): incluir `led_team_ids` (y quizá `led_teams`) en el token para el frontend y el chat.
  - `hps_agent/consumers.py`: construir contexto con `led_team_ids` (equipos que lidera) para el agente.
  - `hps_agent/services/command_processor.py`: en todas las funciones que hoy usan `team_ids` para team_lead, usar **equipos liderados** (por usuario o por contexto `led_team_ids`).
  - `hps_agent/services/openai_service.py`: si el prompt menciona “tu equipo”, aclarar que son “equipos que lideras”.
  - `hps_agent/services/role_config.py`: textos tipo “Estado de mi equipo” / “HPS de mi equipo” pueden precisar “equipos que lideras”.
- **Frontend**
  - `authStore` / tipo de usuario: guardar `led_team_ids` y/o `led_teams` si el backend los envía (perfil/JWT).
  - `TeamManagement.jsx`: en lugar de un solo `user.team_id`, usar **equipos que lidera** (lista); permitir elegir equipo o mostrar varios (según diseño acordado).
  - `Dashboard.jsx`: si “Mi equipo” depende del equipo, basarlo en equipos liderados.
  - `Chat.jsx`: enviar `led_team_ids` (o equivalente) en el contexto del WebSocket si el agente lo usa.
  - Servicios/API que llamen a “mis equipos” o “miembro de”: añadir o usar endpoint/objeto “equipos que lidero” donde corresponda.

---

## Preguntas para cerrar el plan de desarrollo

1. **Dashboard “Mi equipo”**  
   Cuando un líder tiene **varios equipos liderados**, ¿cómo debe verse?
   - **A)** Un solo bloque “Mi equipo” que agrupe todos los equipos que lidera (p. ej. por equipo, con sublistas de miembros).
   - **B)** Un **selector** (pestañas o desplegable) “Equipo: X / Y / Z” y al elegir uno se muestran solo los miembros de ese equipo.
   - **C)** Otra idea (describir).

2. **Chat – redacción**  
   En respuestas del agente tipo “HPS de tu equipo” o “usuarios de tu equipo”, cuando hay varios equipos liderados, ¿prefieres?
   - Frase tipo: “HPS de **tus equipos** (Equipo A, Equipo B)” y listar por equipo.
   - O mantener “tu equipo” en singular y que la lista sea la unión de todos los equipos que lidera sin destacar el nombre del equipo en cada línea.

3. **Asignar usuario a equipo (agente)**  
   Hoy un team_lead solo puede asignar a equipos en los que **está**. Con el cambio, ¿debe poder asignar solo a **equipos que lidera**? (Recomendación: sí, para ser coherente con “solo veo/gestiono equipos que lidero”.)

4. **Jefe de seguridad**  
   Los jefes de seguridad siguen viendo “todas las HPS” y no se limitan por equipo. ¿Confirmamos que no cambia nada para ellos y que solo se restringe la lógica de **team_lead**?

5. **Perfil / token**  
   ¿Quieres que en el **perfil** (y en el JWT) el backend exponga siempre `led_team_ids` y `led_teams` (lista de `{ id, name }`) para cualquier usuario (vacío si no es líder), para que el frontend no tenga que llamar a un endpoint extra de “mis equipos liderados”?

Con estas respuestas se puede bajar a **tareas concretas** (cambios por archivo y orden recomendado) para la implementación.
