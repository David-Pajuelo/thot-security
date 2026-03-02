# Plan de mejoras: Chat HPS y historial de mensajes

## 1. Objetivo del sistema

- **Chat en tiempo real**: el usuario habla con el agente IA (HPS) por WebSocket; los mensajes se guardan en una conversación activa.
- **Reset**: archivar la conversación actual y abrir una nueva vacía, mostrando de inmediato el mensaje de bienvenida.
- **Histórico**: listar conversaciones pasadas (admin/staff) y ver detalle de cada una (mensajes, estado, métricas).

---

## 2. Arquitectura actual

### 2.1 Backend (Django)

| Componente | Ubicación | Función |
|------------|-----------|---------|
| **WebSocket consumer** | `hps_agent/consumers.py` | Acepta conexión, valida JWT, busca/crea conversación activa, carga historial o envía bienvenida, procesa mensajes y comandos. |
| **ChatService** | `hps_agent/services/chat_service.py` | `find_active_conversation`, `create_conversation`, `get_conversation_messages`, `log_user_message`, `log_assistant_message`, `user_has_welcome_in_any_conversation`, `conversation_belongs_to_user`. |
| **RoleConfig** | `hps_agent/services/role_config.py` | Mensajes de bienvenida y sugerencias por rol. |
| **API REST** | `hps_core/views.py` → `ChatConversationViewSet` | CRUD conversaciones, `reset`, `full` (conversación + mensajes), `all` (todas para admin). |
| **Modelos** | `hps_core/models.py` | `ChatConversation` (user, status, total_messages, …), `ChatMessage` (conversation, message_type, content, message_metadata). |

### 2.2 Frontend (HPS – React)

| Componente | Ubicación | Función |
|------------|-----------|---------|
| **Chat** | `components/Chat.jsx` | UI del chat: lista de mensajes, input, Reset, conexión WS. |
| **chatStore** | `store/chatStore.js` | Zustand persistido: `messages`, `conversationId`, `isConnected`, `clearChat`, `addMessage`, `loadHistory`. |
| **websocketService** | `services/websocketService.js` | Singleton: `connect`, `disconnect`, `sendMessage`, `addListener`, `notifyListeners`, keepalive. |
| **ChatMonitoringPage** | `pages/ChatMonitoringPage.jsx` | Histórico: lista de conversaciones (API `conversations/all`), detalle con `conversations/:id/full`. |

### 2.3 Flujos principales

1. **Primera carga / Refresh**  
   Frontend conecta WebSocket → backend `_initialize_conversation()` → `find_active_conversation()`; si hay activa, envía `conversation_id` y `_load_conversation_history()` (si 0 mensajes → bienvenida); si no, crea conversación y envía bienvenida.

2. **Reset (antes del cambio)**  
   POST `conversations/reset/` → backend cierra activas y crea nueva → frontend `clearChat()`, si WS conectado envía `use_conversation`, si no reconecta tras 1 s. La bienvenida dependía del WebSocket (envío tras `_load_conversation_history()` con 0 mensajes), y por timing/listener a veces no se veía.

3. **Histórico**  
   Admin: GET `conversations/all/` → lista; clic en conversación → GET `conversations/:id/full/` → mensajes. Solo lectura.

---

## 3. Problema analizado: bienvenida tras Reset

- **Síntoma**: Reset limpia el chat pero no muestra la bienvenida; al refrescar la página sí aparece.
- **Causas identificadas**:
  - La bienvenida se enviaba solo por WebSocket (tras `use_conversation` → `_load_conversation_history()` → 0 mensajes).
  - Dependencia del listener y del orden de mensajes: posible closure obsoleta en el listener o llegada de mensajes antes de que la UI esté lista.
  - `clearChat()` ponía `isConnected: false` en el store aunque el socket siguiera abierto, lo que podía afectar la lógica de actualización de la UI.

---

## 4. Cambios realizados (fix inmediato)

1. **Backend – Respuesta de reset**  
   - El endpoint `POST /api/hps/chat/conversations/reset/` ahora devuelve `welcome_message` y `suggestions` (según rol del usuario, vía `RoleConfig`).  
   - Se crea y persiste el primer mensaje de la nueva conversación (tipo `assistant`, metadata `type: welcome`) y se actualiza `total_messages`.

2. **Frontend – Bienvenida desde la respuesta**  
   - Tras un reset correcto: se hace `setMessages([])` y `setConversationId(newId)` (sin tocar `isConnected`).  
   - Si la respuesta trae `welcome_message`, se llama a `addMessage(...)` con ese contenido y las sugerencias.  
   - Se sigue enviando `use_conversation` por WebSocket para que el backend use la nueva conversación; si el backend reenvía el mismo mensaje de historial, el frontend lo considera duplicado y no lo vuelve a mostrar.

Con esto, la bienvenida aparece siempre tras un solo clic en Reset, sin depender del WebSocket.

---

## 5. Plan de mejoras (recomendaciones)

### 5.1 Robustez y consistencia del chat

- **Listener y estado**  
  - Revisar que el listener del WebSocket use siempre el estado actual del store (p. ej. leer desde `useChatStore.getState()` dentro del callback en lugar de depender de closures), para evitar duplicados o mensajes “perdidos” en reconexiones o tras Reset.

- **clearChat vs reset**  
  - Diferenciar bien: `clearChat()` para “borrar todo y desconectar” (p. ej. logout) y un flujo de reset que solo limpie mensajes y cambie `conversationId`, manteniendo conexión y mostrando bienvenida desde la API.

- **Reconexión**  
  - Tras reconexión, el backend ya envía `conversation_id` e historial (o bienvenida si 0 mensajes). Comprobar que el frontend no limpie mensajes al detectar “reconexión” si la conversación es la misma.

### 5.2 Histórico de conversaciones

- **Permisos y filtros**  
  - Mantener que solo staff/admin vean `conversations/all`. Valorar filtros por usuario, fecha, estado (activa/cerrada) y búsqueda por texto si crece el uso.

- **Paginación**  
  - El listado usa `limit=100`. Añadir paginación (offset/cursor o page size) para no cargar miles de conversaciones.

- **Detalle de conversación**  
  - El endpoint `full` está bien para “conversación + mensajes”. Valorar ordenación de mensajes y límite máximo para conversaciones muy largas.

- **Sincronización con chat activo**  
  - Si el usuario tiene el chat abierto y un admin mira el histórico de esa misma conversación, no hay actualización en tiempo real; es aceptable para un histórico de supervisión. Opcional: notificación o badge “nuevos mensajes” si se implementa notificación en tiempo real en el futuro.

### 5.3 Experiencia de usuario

- **Estados de conexión**  
  - Mostrar de forma clara “Conectado” / “Reconectando…” / “Desconectado” y, si aplica, un botón “Reintentar” cuando falle la conexión.

- **Reset**  
  - Dejar claro en la UI que “Reset” inicia una conversación nueva (y que la actual queda archivada). El fix actual asegura que la bienvenida se vea de inmediato.

- **Sugerencias**  
  - Las sugerencias por rol ya se envían con la bienvenida (API y WebSocket). Revisar que en la UI se muestren correctamente tras Reset y al cargar historial.

### 5.4 Operación y observabilidad

- **Logs**  
  - En el consumer, ya hay logs de conexión, `use_conversation` y envío de bienvenida. Mantenerlos y evitar loguear contenido completo de mensajes por privacidad.

- **Métricas**  
  - Si existe `ChatMetrics` o similar, seguir alimentándolo (conversaciones creadas/cerradas, mensajes por día) para dashboards o alertas.

### 5.5 Priorización sugerida (implementadas)

| Prioridad | Mejora | Estado |
|-----------|--------|--------|
| Alta | Fix bienvenida tras Reset (hecho) | Hecho |
| Media | Listener del WS usando getState() para evitar closures obsoletas | Implementado |
| Media | Paginación en listado de conversaciones (histórico) | Implementado |
| Baja | Filtros en histórico (usuario, fecha, estado) | Implementado |
| Baja | Indicadores claros de estado de conexión y “Reintentar” | Bajo |

---

## 6. Resumen de mejoras implementadas (sesión actual)

1. **Listener con getState()**  
   En `Chat.jsx`, `handleIncomingMessage` lee al inicio `useChatStore.getState()` y usa `currentMessages` y `currentConversationId` para la detección de duplicados y el fallback de `conversationId`. Así se evitan closures obsoletas tras Reset o reconexión.

2. **Indicadores de conexión y Reintentar**  
   - Indicador del header: verde (Conectado), ámbar (Conectando/Reconectando), rojo (Desconectado).  
   - Botón **"Reintentar conexión"** visible siempre que no hay conexión (no solo tras 5 intentos), con estado "Conectando..." durante el intento.

3. **Paginación en histórico**  
   - Backend: `all_conversations` devuelve `{ results, count, has_more }` con `limit` (default 20) y `offset`.  
   - Frontend: primera carga con 20 ítems; botón **"Cargar más conversaciones"** en el panel y en el modal que pide la siguiente página y la concatena.

4. **Filtros en histórico**  
   - Backend: query params opcionales `user_id`, `status`, `date_from`, `date_to`.  
   - Frontend (modal "Todas las conversaciones"): desplegable Estado (Todos / Activa / Cerrada / Archivada), fechas Desde/Hasta y botón **"Aplicar filtros"** que recarga la primera página con los filtros actuales.

---

## 7. Resumen

- **Objetivo**: Chat en tiempo real con agente HPS, reset que abre conversación nueva con bienvenida visible de inmediato, e histórico para supervisión.
- **Problema**: La bienvenida tras Reset no se mostraba por depender solo del WebSocket y del timing del listener.
- **Solución aplicada**: La API de reset devuelve `welcome_message` y `suggestions` y persiste el mensaje en la nueva conversación; el frontend muestra esa bienvenida en cuanto recibe la respuesta y sigue usando `use_conversation` para alinear el backend.
- **Próximos pasos recomendados**: Revisar listener/estado del store, paginación del histórico y pequeños ajustes de UX (estado de conexión y texto de Reset).
