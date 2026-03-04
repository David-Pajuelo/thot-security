# Por qué puedes tener "miembro" en HPS y "admin" en CryptoTrace a la vez

## Qué estás viendo

1. Entras a **HPS** con usuario **miembro** → todo bien.
2. Intentas entrar a la **URL de CryptoTrace** (área crypto) → te bloquea y muestra que hace falta ser admin, crypto o jefe de seguridad.
3. Aparece un **login** (o vas a “Cerrar sesión” y luego al login de CryptoTrace) y te logueas como **administrador**.
4. Puedes **cambiar de pestaña**: en una ves HPS como miembro y en otra CryptoTrace como admin, y el chat y el resto se comportan bien para cada uno.

La razón no es que el backend “gestione dos sesiones”, sino cómo está montado el frontend y el **origen** de cada app.

---

## Estructura: dos frontends, dos orígenes

Hay **dos aplicaciones frontend distintas**:

| Sistema       | Tecnología | Origen típico (local) | Puerto |
|---------------|------------|------------------------|--------|
| **HPS System**   | React      | `http://localhost:3001` | 3001   |
| **CryptoTrace**  | Next.js    | `http://localhost:3000` | 3000   |

Cada una se sirve en un **origen distinto** (dominio + puerto). El backend (Django) es común y suele estar en otro puerto (ej. 8080).

---

## Cómo funciona el almacenamiento en el navegador

En el navegador, **localStorage (y sessionStorage) son por origen**:

- Lo que guarda `http://localhost:3001` **solo** lo ve `http://localhost:3001`.
- Lo que guarda `http://localhost:3000` **solo** lo ve `http://localhost:3000`.

No se comparten entre orígenes por seguridad. Por tanto:

- **Pestaña/origen 3001 (HPS):** tiene su propio `localStorage` → su propio `accessToken` / `hps_token`.
- **Pestaña/origen 3000 (CryptoTrace):** tiene otro `localStorage` → otro `accessToken` / `hps_token`.

No hay un “único token global” entre HPS y CryptoTrace; hay **uno por origen**.

---

## Flujo que describes (paso a paso)

1. **Pestaña A – HPS (3001)**  
   - Te logueas como **miembro**.  
   - HPS guarda el JWT de miembro en `localStorage` **del origen 3001**.  
   - En esa pestaña sigues siendo miembro.

2. **Pestaña B – CryptoTrace (3000)**  
   - Abres la URL de CryptoTrace.  
   - CryptoTrace puede intentar reutilizar la sesión de HPS mediante **tokenSync** (iframe + `postMessage` a `http://localhost:3001/token-sync.html`).  
   - Si lo consigue, copia el token de **miembro** al `localStorage` **del origen 3000**.  
   - **ProtectedRoute** en CryptoTrace lee el JWT, ve `role === 'member'`, y como solo permite `admin` y `crypto`, muestra **“Acceso denegado”** y el mensaje de que hace falta ser admin/crypto/jefe.  
   - Importante: en ese bloqueo **no se borra el token** (está pensado para “mantener sesión activa para HPS” en el mensaje de la pantalla).

3. **En la misma pestaña de CryptoTrace (3000)**  
   - Haces “Cerrar sesión” (o vas al login) y te logueas como **administrador**.  
   - El login de CryptoTrace llama al **mismo backend** (Django) y guarda el **nuevo** JWT (admin) en el `localStorage` **del origen 3000**.  
   - A partir de ahí, en esa pestaña (3000) solo existe el token de **admin**.

4. **Vuelves a la pestaña de HPS (3001)**  
   - Esa pestaña **no se ha recargado ni ha hecho logout**.  
   - Su `localStorage` (origen 3001) **sigue teniendo el token de miembro**.  
   - Por tanto en HPS sigues viendo la sesión de **miembro**.

Resultado:

- **Una pestaña (HPS, 3001)** → token de **miembro** en su propio `localStorage`.
- **Otra pestaña (CryptoTrace, 3000)** → token de **admin** en su propio `localStorage`.

Por eso “gestiona bien dos accesos diferentes”: no es que el sistema tenga dos sesiones en el servidor, sino **dos almacenamientos locales distintos**, uno por aplicación/origen.

---

## Detalles de código que lo reflejan

- **CryptoTrace – `protectedRoute.tsx`**  
  - Comprueba `role` del JWT (`admin` / `crypto` permitidos).  
  - Si el rol no está permitido: **no borra el token** y muestra “Acceso denegado” con enlace a HPS y opción de “Cerrar sesión” (para poder hacer login con otro usuario en CryptoTrace).

- **CryptoTrace – `Layout.tsx`**  
  - Lee el token de `localStorage` (y cookies) del **mismo origen** (3000) para mostrar estado (autenticado, rol, etc.).

- **HPS – `authStore.js` / `apiService.js`**  
  - Guardan el token en `accessToken` y `hps_token` en el **localStorage del origen donde corre HPS** (3001).

- **Sincronización entre apps**  
  - `tokenSync` (iframe + `postMessage`) sirve para **copiar** el token de un origen al otro cuando abres CryptoTrace y ya estabas logueado en HPS (o al revés).  
  - No unifica un único “login global”; cada origen sigue teniendo su propia copia en su propio `localStorage`.

---

## Resumen

- **Por qué no te deja entrar a crypto como miembro:** CryptoTrace comprueba el `role` del JWT y solo permite `admin` y `crypto` en esa ruta; tu token en CryptoTrace era de miembro.  
- **Por qué ves un login:** Al no tener rol permitido, CryptoTrace te ofrece “Cerrar sesión” / login para iniciar sesión con un usuario que sí tenga permiso (admin/crypto).  
- **Por qué puedes estar como miembro en HPS y admin en CryptoTrace:** Son **dos orígenes** (dos puertos/dominios). Cada uno tiene su **propio `localStorage`** y su propio token. En la pestaña de HPS sigue el token de miembro; en la de CryptoTrace, después de loguearte como admin, solo está el token de admin. El backend no “mantiene dos sesiones”; simplemente cada pestaña envía el JWT que tiene en su origen y el backend responde según ese token.

Es el comportamiento esperado dado el diseño actual: dos frontends, dos orígenes, dos almacenamientos locales independientes.
