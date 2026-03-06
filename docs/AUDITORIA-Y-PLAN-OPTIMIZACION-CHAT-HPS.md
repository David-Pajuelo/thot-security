# Auditoría y plan de optimización del chat HPS

## 0. Cambios implementados (resumen)

- **Conversación solo cuando hay mensajes:** La conversación en BD se crea al **primer mensaje del usuario**, no al conectar el WebSocket. Así no se guardan conversaciones vacías.
- **Bienvenida no se persiste:** El mensaje de bienvenida del bot se envía solo por WebSocket; no se guarda en BD. Solo se persisten mensajes de usuario y respuestas del bot.
- **Reset:** Al hacer "Nueva conversación" (reset) se crea una conversación nueva en BD pero sin mensaje de bienvenida guardado; la bienvenida se devuelve en la respuesta para mostrarla en el frontend.
- **Una conversación revisable:** Se reutiliza la conversación activa al reconectar; el frontend ya no archiva cuando el cierre es por "Nueva conexión" (reconexión), evitando multiplicar conversaciones.
- **Título útil:** Al crear la conversación en el primer mensaje, el título se rellena con el inicio del primer mensaje del usuario (hasta 200 caracteres) para que el admin pueda identificarla.
- **complete_conversation:** Se deja de usar satisfaction_rating/satisfaction_feedback en el modelo (no existían); se mantiene solo status='closed' y closed_at.

---

## 1. Resumen ejecutivo

El chat del agente IA (HPS) guarda conversaciones y mensajes en Django (`ChatConversation`, `ChatMessage`). La **creación de conversaciones vacías** y la **multiplicación de conversaciones por reconexión/refresco** se deben principalmente a que el frontend **archiva la conversación activa** cada vez que cierra el WebSocket con código 1000, y el backend **crea una nueva** al no encontrar ninguna activa. Además, el administrador tiene poca capacidad para revisar y monitorizar conversaciones de forma cómoda.

Este documento describe el flujo actual, los problemas detectados y un **plan de optimización** para el registro, la persistencia y la monitorización del chat.

---

## 2. Flujo actual del chat

### 2.1 Modelos (backend)

- **ChatConversation**: `id` (UUID), `user`, `session_id`, `title`, `status` (active/closed/archived), `total_messages`, `total_tokens_used`, `conversation_data` (JSON), `created_at`, `updated_at`, `completed_at`, `closed_at`.
- **ChatMessage**: `id` (UUID), `conversation`, `message_type` (user/assistant/system), `content`, `tokens_used`, `response_time_ms`, `is_error`, `error_message`, `message_metadata`, `created_at`.

Los mensajes se guardan correctamente cuando el usuario escribe y el agente responde (vía `ChatService.log_user_message` y `log_assistant_message` en el consumer).

### 2.2 Cuándo se crea una conversación

1. **WebSocket (consumer)**  
   En `connect()` se llama a `_initialize_conversation()`:
   - Se busca una conversación **activa** del usuario: `find_active_conversation(user_id)` (status='active').
   - Si **no hay activa** → se crea una nueva con `create_conversation(...)` y se envía mensaje de bienvenida (y se persiste).
   - Si **hay activa** → se reutiliza, se envía `conversation_id` y se carga historial con `_load_conversation_history()`.

2. **REST – Reset**  
   `POST /api/hps/chat/conversations/reset/`:
   - Cierra todas las conversaciones activas del usuario (`status='closed'`, `closed_at`).
   - Crea una **nueva** conversación activa con mensaje de bienvenida.

3. **REST – Archive**  
   `POST /api/hps/chat/conversations/archive-active/`:
   - Pone la conversación activa en `status='archived'` y `closed_at`.

### 2.3 Cuándo se archiva la conversación (origen del problema)

En el frontend (`websocketService.js`):

- Al **cerrar** el WebSocket se ejecuta `onclose`.
- Si el código de cierre es **1000** (cierre intencional), se llama a `archiveActiveConversation()`.
- **Además**, en `connect()`: si ya existía una conexión, se hace `this.ws.close(1000, 'Nueva conexión')` antes de abrir otra. Eso dispara `onclose` con código 1000 y, por tanto, **archiva la conversación activa**.

Consecuencia: cada vez que el frontend “reconecta” (por ejemplo tras refresco de token o doble llamada a `connect()`), se cierra la conexión con 1000 → se archiva la conversación → en la siguiente conexión no hay conversación activa → se **crea una nueva**. Muchas de esas conversaciones quedan vacías o solo con el mensaje de bienvenida, y el administrador ve muchas conversaciones por usuario sin contenido útil.

---

## 3. Problemas detectados

| # | Problema | Impacto |
|---|----------|--------|
| 1 | **Archivado en cada cierre 1000** (incluido “Nueva conexión”) | Multiplicación de conversaciones; muchas vacías o con solo bienvenida. |
| 2 | **Crear conversación en cada conexión WS** si no hay activa | Una sola reconexión genera una conversación nueva aunque la anterior fuera la misma “sesión” de usuario. |
| 3 | **Admin Django** sin vista integrada conversación + mensajes | El administrador no puede revisar una conversación y sus mensajes en una sola pantalla. |
| 4 | **Sin exportación** de conversaciones/mensajes para monitorización | No hay CSV/export para auditoría o análisis. |
| 5 | **Sin filtro por “conversaciones con mensajes”** en listados | Difícil centrarse en conversaciones útiles (con interacción real). |
| 6 | **ChatService.complete_conversation** usa `satisfaction_rating` / `satisfaction_feedback` en el modelo `ChatConversation`, pero esos campos no existen en el modelo (sí en `ChatMetrics`) | Riesgo de `AttributeError` al completar conversación. |
| 7 | **Título genérico** (“Nueva conversación”, “Nueva conversación iniciada”) | Poca ayuda para el administrador al escanear listados. |
| 8 | **Conversaciones vacías** (0 mensajes o solo bienvenida) no se distinguen ni se pueden ocultar fácilmente | Ruido en listados y en métricas. |

---

## 4. Plan de optimización

### 4.1 Evitar conversaciones vacías por reconexión (prioridad alta)

**Objetivo:** No archivar la conversación activa en cada cierre 1000 del WebSocket; no crear una conversación nueva en cada reconexión.

- **Backend**
  - Mantener la lógica actual de “reutilizar conversación activa” en `_initialize_conversation()` (ya correcta).
- **Frontend**
  - **No** llamar a `archiveActiveConversation()` cuando el cierre es por “Nueva conexión” (misma sesión, solo reconexión).
  - Archivar solo en **logout** o cierre explícito de la aplicación (por ejemplo solo en `disconnectIntentionally()`).
  - Opción: distinguir en `onclose`: si `event.reason === 'Nueva conexión'`, no archivar; si es logout/cierre de sesión, sí archivar (o llamar solo desde `disconnectIntentionally()` y no desde `onclose`).
- **Resultado esperado:** Una misma “sesión” de chat mantiene una sola conversación activa aunque el WebSocket se cierre y se vuelva a abrir; menos conversaciones vacías.

### 4.2 Crear conversación solo cuando haya interacción (opcional, prioridad media)

**Objetivo:** No crear conversación en BD hasta que el usuario envíe el primer mensaje (o hasta que se envíe la bienvenida persistida).

- **Alternativa A (recomendada para mínimos cambios):** Mantener “una conversación activa por usuario” pero evitar archivarla en reconexiones (como en 4.1). Así se reduce el número de conversaciones sin cambiar el momento de creación.
- **Alternativa B:** En el consumer, no crear conversación en `_initialize_conversation()`; crear la conversación en el primer `receive()` (primer mensaje del usuario) o al enviar la bienvenida persistida. Implica que hasta ese momento no haya `conversation_id` en BD y que el frontend pueda manejar un estado “conectado sin conversación”.

### 4.3 Registro y persistencia de mensajes (ya correcto; mejoras menores)

- Los mensajes ya se registran bien con `log_user_message` y `log_assistant_message`.
- **Mejora:** Actualizar `total_messages` de forma consistente (ya se hace con `conversation.messages.count()`); opcionalmente mantener un campo `last_message_at` en `ChatConversation` para ordenar y filtrar por “última actividad”.
- **Corregir:** Revisar `ChatService.complete_conversation`: si se desea guardar satisfacción por conversación, añadir campos `satisfaction_rating` y `satisfaction_feedback` a `ChatConversation`; si no, quitar su uso en `complete_conversation` para evitar errores.

### 4.4 Admin Django: monitorización y revisión

**Objetivo:** Que el administrador pueda revisar conversaciones y mensajes de forma clara y, si se desea, exportar.

- **ChatConversation (admin)**
  - Añadir en `list_display`: `total_messages`, `created_at`, `updated_at` (ya en parte); considerar `last_message_at` si se añade el campo.
  - Añadir **filtro** por “con conversación útil”: por ejemplo “Con mensajes” (total_messages > 1 o > 0 según criterio).
  - Inline de **ChatMessage** en la ficha de `ChatConversation`: listar mensajes en orden cronológico dentro de la misma pantalla de la conversación (solo lectura).
  - Acción de listado: “Exportar a CSV” (conversaciones seleccionadas con columnas: id, user, session_id, status, total_messages, created_at, closed_at; opcionalmente incluir resumen de mensajes o enlace).
- **ChatMessage (admin)**
  - Mantener o mejorar filtros por `conversation`, `message_type`, `is_error`, `created_at`.
  - Opcional: acción “Exportar mensajes a CSV” (para conversaciones seleccionadas o filtradas).
- **Vista de solo lectura** para conversación completa: ya existe el endpoint `GET .../conversations/<id>/full/`; el admin puede usar un enlace “Ver conversación completa” que abra esa API (o una página custom en el admin) para staff.

### 4.5 Títulos y calidad de datos

- **Título de conversación:** En lugar de siempre “Nueva conversación”, asignar un título cuando:
  - Se persiste el primer mensaje del usuario (por ejemplo primeros 50 caracteres del contenido), o
  - Se cierra/archiva la conversación (resumen o primera pregunta).
- **Limpieza de conversaciones vacías (opcional):** Tarea o comando de gestión que:
  - Marque o archive conversaciones con `total_messages == 0` (o solo bienvenida) y creadas hace más de X horas, o
  - Las elimine si la política lo permite (y si no se usan para métricas).

### 4.6 Exportación para auditoría y cumplimiento

- **Conversaciones:** Acción en admin “Exportar a CSV” (como en 4.4) con columnas: usuario (email), conversación (id/session_id), estado, total mensajes, fechas, etc.
- **Mensajes:** Export CSV por conversación o por rango de fechas (conversation_id, user/assistant, content, timestamp, is_error, etc.) para análisis y auditoría.
- Opcional: endpoint REST protegido (solo staff/admin) para descarga masiva de conversaciones y mensajes en un rango de fechas (CSV o JSON).

### 4.7 Resumen de prioridades recomendadas

1. **Alta:** Ajustar frontend para no archivar en cierre por “Nueva conexión” (4.1); corregir uso de `satisfaction_*` en `complete_conversation` (4.3).
2. **Alta:** Admin con inline de mensajes en conversación y filtro “con mensajes” (4.4).
3. **Media:** Export a CSV desde admin para conversaciones y mensajes (4.4, 4.6).
4. **Media:** Títulos automáticos y/o campo `last_message_at` (4.5).
5. **Baja:** Limpieza de conversaciones vacías antiguas; política de retención (4.5).

---

## 5. Cambios técnicos sugeridos (resumen)

| Componente | Cambio |
|------------|--------|
| **Frontend (websocketService.js)** | En `onclose`, no llamar a `archiveActiveConversation()` cuando `event.reason === 'Nueva conexión'` (o archivar solo en `disconnectIntentionally()`). |
| **Backend (ChatService)** | Corregir `complete_conversation`: quitar asignación a `satisfaction_rating`/`satisfaction_feedback` en el modelo o añadir esos campos a `ChatConversation`. |
| **Backend (admin)** | ChatConversationAdmin: inline de ChatMessage (readonly), filtro por total_messages, acción “Exportar a CSV”. |
| **Backend (modelo, opcional)** | ChatConversation: campo `last_message_at` (DateTimeField, null=True); actualizarlo al guardar cada mensaje. |
| **Backend (consumer, opcional)** | Al crear conversación, no asignar título hasta el primer mensaje del usuario; luego actualizar título con extracto del primer mensaje. |

---

## 6. Conclusión

El problema principal es **archivar la conversación activa en cada cierre del WebSocket con código 1000**, incluido el cierre por “Nueva conexión”, lo que provoca que en la siguiente conexión se cree una nueva conversación y se multipliquen conversaciones vacías o con solo bienvenida. Corregir el comportamiento del frontend ante el cierre 1000 y mejorar el admin (inline de mensajes, filtros, exportación) permitirá un registro de chats más limpio y una monitorización útil para el administrador. El resto de mejoras (títulos, last_message_at, limpieza) son opcionales y pueden aplicarse en fases posteriores.
