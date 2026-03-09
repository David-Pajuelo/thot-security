# Estados de conversaciones de chat – Propuesta

## Objetivo

Poder mostrar al admin las conversaciones para su monitorización, con **simplicidad** y **registro correcto**. No hay más requisitos que listar/filtrar conversaciones por estado.

---

## Necesidad de los estados actuales

| Estado actual | ¿Necesario para el admin? | Uso real en código |
|--------------|---------------------------|---------------------|
| **active**   | **Sí**                    | La conversación “en curso” del usuario; solo una por usuario. Es la que recibe mensajes. |
| **closed**   | **Sí**                    | Conversación terminada: por “Nueva conversación” (reset), por completar o abandonar. |
| **archived** | **Dudoso**                | Se usa al cerrar pestaña o hacer logout (WS cierra con code 1000). Semánticamente es “usuario salió sin reset”. |

Para monitorización basta distinguir:

- **En curso** → una conversación activa por usuario.
- **Finalizada** → el resto (ya no reciben mensajes).

Por tanto, **no hace falta** un tercer estado para el admin si el único objetivo es “ver y filtrar bien”. Se puede simplificar a **dos estados**.

---

## Propuesta: dos estados (active / closed)

### 1. Estados en BD

- **`active`**: conversación en uso. Como máximo una por usuario.
- **`closed`**: conversación terminada (cualquier motivo: reset, completar, abandonar, cerrar pestaña, logout).

Ventajas:

- Reglas fáciles de explicar y depurar.
- Filtro admin: “Activa” vs “Cerrada” (o “En curso” vs “Finalizada”).
- Misma lógica de listados y permisos que ahora, con un estado menos.

### 2. Lógica de registro (qué hacer en cada caso)

Regla única: **solo una conversación `active` por usuario; todo lo que deja de ser “la actual” pasa a `closed`.**

| Acción / evento | Qué hacer |
|----------------|-----------|
| **Crear conversación** (primera vez o tras reset) | Nueva con `status='active'`. |
| **Reset (“Nueva conversación”)** | Todas las `active` del usuario → `closed`, `closed_at=now`. Luego crear nueva `active`. *(Ya está así.)* |
| **Cerrar pestaña / logout / WS cierra “bien”** | La conversación activa actual → `closed`, `closed_at=now`. *(Sustituir la llamada a `archive-active` por esta lógica.)* |
| **Completar conversación** (botón/acción explícita) | Esa conversación → `closed`, `completed_at=now` si quieres distinguir “completada” de “cerrada por salir”. *(Opcional: mismo estado `closed` y solo `closed_at`.)* |
| **Abandonar conversación** | Esa conversación → `closed`, `closed_at=now`. |

No hace falta acción “archivar” distinta: todo lo que no es “la actual” queda `closed`.

### 3. Cambios concretos recomendados

1. **Backend**
   - Mantener en el modelo solo dos opciones: `active` y `closed` (o mantener `archived` en el modelo por compatibilidad pero **tratarlo igual que `closed`** en vistas y filtros).
   - Endpoint **`archive-active`**: que haga lo mismo que “cerrar la activa”: poner `status='closed'` y `closed_at=now` (y opcionalmente dejar de escribir `archived` si se elimina ese valor).
   - Así el frontend puede seguir llamando a `archive-active` al cerrar WS/logout; solo cambia el valor que se escribe (`closed` en lugar de `archived`).

2. **Frontend (admin)**
   - Filtro de estado: **Activa** | **Cerrada** (y si se mantiene `archived` en BD por migraciones, mostrar “Archivada” como “Cerrada” o agrupar bajo “Finalizada”).
   - Listados: sin cambiar lógica; solo interpretar “archived” como “cerrada” si se unifica.

3. **Registro correcto**
   - Cada vez que el usuario deje de usar una conversación (reset, cerrar, completar, abandonar), esa conversación debe quedar con `status='closed'` y una fecha (`closed_at` o `completed_at`).
   - La “conversación activa” se obtiene siempre con: `Conversation.objects.filter(user=..., status='active').order_by('-created_at').first()`.

---

## Resumen

- **Necesidad**: un solo estado “en curso” (`active`) y el resto “finalizado” (`closed`) para que el admin pueda monitorizar con filtros simples.
- **Propuesta**: dos estados, una regla (“solo una activa por usuario; al dejar de usarla → closed”) y reutilizar `archive-active` para “cerrar al salir” escribiendo `closed` en lugar de `archived`.
- **Objetivo**: simplicidad y que el registro sea correcto (cada conversación termina en `closed` y el admin ve claramente “Activa” vs “Cerrada”).

Si en el futuro se necesita distinguir “cerrada por reset” vs “cerrada por cierre de sesión”, se puede usar un campo extra (por ejemplo `closed_reason`) sin añadir un tercer estado principal.

---

## Implementación realizada

- **Backend** `archive_active`: ahora asigna `status='closed'` y `closed_at` (ya no `archived`). Las conversaciones al cerrar pestaña o logout quedan como cerradas.
- **Backend** `all_conversations`: cuando el filtro es `status=closed`, se devuelven también las filas con `status=archived` (legacy), para que el admin vea todas las finalizadas con un solo filtro “Cerrada”.
- **Frontend** (monitorización): el desplegable de estado solo ofrece **Todos**, **Activa** y **Cerrada**. En cada fila se sigue mostrando el badge real (Activa / Archivada / Cerrada) por si hay datos legacy con `archived`.

### Regla "una activa + N cerradas"

Para que en monitorización no se acumulen muchas conversaciones por usuario:

- Siempre hay **como máximo una conversación activa** por usuario.
- Al cerrar esa activa (botón "Nueva conversación" o cierre de pestaña/logout), se **cierra la actual** y se **crea una nueva activa (vacía)**. Resultado: conv 1 y 2 cerradas, conv 3 abierta.
- Tanto **reset** como **archive_active** aplican esta regla: cierran la activa y crean la siguiente, de modo que el usuario nunca queda con 0 activas.
