# Análisis: uso de clases de permisos legacy (RBAC)

## Alcance del análisis

- **Repositorio:** thot-security (HPS, Cryptotrace backend/frontend, extensiones de navegador).
- **Objetivo:** Comprobar si las clases antiguas de permisos (`IsHpsAdmin`, `IsHpsAdminOrTeamLead`, etc.) se usan en algún sitio antes de borrarlas.

---

## Clases legacy (definidas en `hps_core/permissions.py`)

| Clase | Sustituida por (RBAC) |
|-------|------------------------|
| `IsHpsAdmin` | `HasHpsPerm("hps.gestionar_roles")`, `HasHpsPerm("hps.ver_todos_tokens")` |
| `IsHpsAdminOrTeamLead` | `HasHpsPermAny(["hps.ver_equipos_todos", "hps.ver_equipos_liderados"])`, `HasHpsPerm("hps.crear_perfil")` |
| `IsHpsAdminOrSecurityChief` | `HasHpsPerm("hps.crear_tokens")`, `HasHpsPerm("hps.gestionar_plantillas")` |
| `IsHpsAdminOrSelf` | `CanViewAuditLog` |
| `IsHpsAdminOrTeamLeadEditingLedMember` | `CanEditHpsProfileLedMember` |

---

## Resultados de la búsqueda

### Backend (cryptotrace-backend/src)

- **hps_core/views.py:** No importa ni usa ninguna de las cinco clases legacy. Usa `HasHpsProfile`, `HasHpsPerm`, `HasHpsPermAny`, `CanViewAuditLog`, `CanEditHpsProfileLedMember`, `user_has_perm`.
- **hps_core/serializers.py:** Solo importa `user_has_perm`. No usa las clases legacy.
- **productos/views.py:** Solo importa `user_has_perm`. No usa las clases legacy.
- **hps_agent:** Usa `profile.role.name` para lógica de comandos y el campo `permissions` (JSON) del modelo al crear roles. No importa clases de `hps_core.permissions`.

### Frontend y extensiones

- **cryptotrace-frontend:** No hay referencias a nombres de clases de permisos del backend.
- **hps-system (extensiones, frontend):** No hay referencias a esas clases (no hay Python de permisos DRF).

### Documentación

- **docs/ANALISIS-CONTROL-ACCESO-RBAC.md** y **docs/AUDITORIA-Y-PLAN-RBAC-GLOBAL.md:** Solo mencionan las clases para describir el estado anterior; no son código que las importe.

---

## Conclusión

- **Ningún código** (vistas, serializers, productos, hps_agent, frontend, extensiones) **importa ni usa** las cinco clases legacy ni las constantes `ADMIN_ROLES` / `TEAM_LEADS` fuera de `hps_core/permissions.py`.
- **HasHpsProfile** sí se sigue usando en varias vistas y debe mantenerse. Usa `_extract_profile_context` y `HpsProfileContext`, que también se mantienen.

**Acción:** Se pueden eliminar de `hps_core/permissions.py` las cinco clases legacy y las constantes `ADMIN_ROLES` y `TEAM_LEADS` sin romper ningún uso en el sistema.
