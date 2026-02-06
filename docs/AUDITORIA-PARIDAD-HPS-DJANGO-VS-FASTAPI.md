# Auditoría: paridad funcional HPS (Django vs FastAPI eliminado)

**Fecha:** 2026-02  
**Objetivo:** Verificar que todas las funcionalidades que estaban en el backend FastAPI de HPS están implementadas en Django (`hps_core`) antes de dar por cerrada la eliminación del FastAPI.

## Fuentes de verdad

- **Frontend HPS** (`hps-system/frontend/src/services/hpsService.js`): endpoints que llama el React.
- **Extensiones Chrome** (`apiClient.js`): endpoints que llama el complemento (personas, traslados, PDF).
- **Documentación de migración** (`docs/archivados/`, `chrome-extensions/ANALISIS-MIGRACION-DJANGO.md`): lista de endpoints migrados.
- **Django** (`cryptotrace-backend/src/hps_core/urls.py` y `views.py`): lo que existe hoy.

## Checklist por área

### 1. Solicitudes HPS (CRUD y flujo)

| Funcionalidad | Frontend/uso | Django | Estado |
|---------------|--------------|--------|--------|
| Listar solicitudes | GET /api/hps/requests/ | HpsRequestViewSet.list | ✅ |
| Crear (autenticado) | POST /api/hps/requests/ | create | ✅ |
| Crear con token (público) | POST /api/hps/requests/public/?token=&hps_type= | create_public | ✅ |
| Detalle | GET /api/hps/requests/{id}/ | retrieve | ✅ |
| Actualizar | PUT /api/hps/requests/{id}/ | update | ✅ |
| Eliminar | DELETE /api/hps/requests/{id}/ | destroy | ✅ |
| Enviar | POST .../submit/ | submit | ✅ |
| Aprobar | POST .../approve/ | approve | ✅ |
| Rechazar | POST .../reject/ | reject | ✅ |
| Estadísticas | GET .../stats/ | stats | ✅ |
| Por equipo | GET .../team/{teamId}/ | team_requests | ✅ |
| Pendientes | GET .../pending/list/ | pending | ✅ |
| Enviadas | GET .../submitted/list/ | submitted | ✅ |

### 2. PDFs (rellenado y respuesta)

| Funcionalidad | Frontend/uso | Django | Estado |
|---------------|--------------|--------|--------|
| Descargar/ver filled PDF | GET .../filled-pdf/ | filled_pdf | ✅ |
| Descargar/ver response PDF | GET .../response-pdf/ | response_pdf | ✅ |
| Editar campos del filled PDF | POST .../edit-filled-pdf/ | edit_filled_pdf | ✅ |
| **Subir PDF rellenado** | POST .../upload-filled-pdf/ | **upload_filled_pdf** | ✅ **Añadido en esta auditoría** |
| Extraer campos del PDF | GET .../extract-pdf-fields/ | extract_pdf_fields | ✅ |

### 3. Tokens HPS

| Funcionalidad | Frontend/uso | Django | Estado |
|---------------|--------------|--------|--------|
| Crear token | POST /api/hps/tokens/ | HpsTokenViewSet.create | ✅ |
| Validar token | GET /api/hps/tokens/validate/?token=&email= | validate (action) | ✅ |
| Info token | GET /api/hps/tokens/info/?token= | list/query o action | ✅ (vía ViewSet) |

### 4. Perfiles, equipos, roles

| Funcionalidad | Django | Estado |
|---------------|--------|--------|
| Perfil usuario HPS | GET /api/hps/user/profile/ | ✅ |
| Roles | HpsRoleViewSet | ✅ |
| Equipos | HpsTeamViewSet (stats, members) | ✅ |
| Perfiles (admin) | HpsUserProfileViewSet | ✅ |

### 5. Extensiones de navegador (API pública)

| Endpoint | Extension llama | Django | Estado |
|----------|-----------------|--------|--------|
| Personas pendientes | GET /api/extension/personas/?tipo= | extension_personas_pendientes | ✅ |
| Persona por DNI | GET /api/extension/persona/{dni}/ | extension_persona_por_dni | ✅ |
| Actualizar estado solicitud | PUT .../solicitud/{dni}/estado/ | extension_actualizar_estado | ✅ |
| Marcar enviada | PUT .../solicitud/{dni}/enviada/ | extension_marcar_enviada | ✅ |
| Marcar traslado enviado | PUT .../traslado/{dni}/enviado/ | extension_marcar_traslado_enviado | ✅ |
| Descargar PDF traslado | GET .../traslado/{dni}/pdf/ | extension_descargar_pdf_traslado | ✅ |

### 6. Emails y otros

| Funcionalidad | Django | Estado |
|---------------|--------|--------|
| Envío email genérico (async) | send_email_async, send_bulk_emails_async | ✅ |
| Estado tarea email | get_task_status | ✅ |
| Enviar formulario HPS por email | send_hps_form_email_async | ✅ |
| Aprobar HPS por email | approve_hps_by_email | ✅ |
| Búsqueda usuarios | search_users | ✅ |
| Comprobar usuario existe | check_user_exists | ✅ |
| Plantillas HPS | HpsTemplateViewSet | ✅ |
| Audit logs | HpsAuditLogViewSet | ✅ |
| Chat (conversaciones, mensajes) | ChatConversationViewSet, ChatMessageViewSet | ✅ |
| Métricas chat | get_chat_realtime_metrics, etc. | ✅ |

### 7. Notificación a jefes de seguridad

| Funcionalidad | FastAPI (eliminado) | Django | Estado |
|---------------|----------------------|--------|--------|
| Aviso al crear usuario por formulario | UserNotificationService → NOTIFICATION_SECURITY_CHIEFS_EMAIL | send_new_user_notification_to_security_chiefs + NOTIFICATION_SECURITY_CHIEFS_EMAIL en settings | ✅ Implementado en Django (variable en .env de **cryptotrace-backend**) |

## Brecha detectada y corrección

- **Falta:** El frontend (HPSTransferPage y hpsService.uploadModifiedPDF) llama a `POST /api/hps/requests/{id}/upload-filled-pdf/` para subir un PDF rellenado (multipart). En Django no existía ese endpoint.
- **Corrección:** Se añadió la acción `upload_filled_pdf` en `HpsRequestViewSet` con `url_path="upload-filled-pdf"`, aceptando `pdf_file` o `filled_pdf` en el body multipart y guardando en `hps_request.filled_pdf`.

## Conclusión

- **Sí:** Tras esta auditoría y la corrección del endpoint de subida de PDF, las funcionalidades usadas por el frontend y las extensiones están cubiertas en Django.
- **No se había comprobado** antes de borrar el FastAPI; esta auditoría se hizo después. Si en producción aparece algún 404 o flujo roto, conviene revisar de nuevo este doc y el ViewSet/urls de `hps_core`.

## Referencias

- `cryptotrace/cryptotrace-backend/src/hps_core/views.py` (HpsRequestViewSet)
- `cryptotrace/cryptotrace-backend/src/hps_core/urls.py`
- `hps-system/frontend/src/services/hpsService.js`
- `docs/ELIMINACION-BACKEND-FASTAPI-HPS.md`
