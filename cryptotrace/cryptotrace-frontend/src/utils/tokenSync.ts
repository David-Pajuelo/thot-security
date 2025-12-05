/**
 * Utilidades para sincronizar tokens entre CryptoTrace y HPS System
 * Usa iframe + postMessage para comunicación entre diferentes orígenes
 */

// Validar variable de entorno (sin fallback en producción)
const HPS_SYSTEM_URL_ENV = process.env.NEXT_PUBLIC_HPS_SYSTEM_URL;
if (!HPS_SYSTEM_URL_ENV) {
  if (process.env.NODE_ENV === 'development') {
    console.warn('⚠️ NEXT_PUBLIC_HPS_SYSTEM_URL no definida, usando localhost (solo en desarrollo)');
  } else {
    console.error('❌ NEXT_PUBLIC_HPS_SYSTEM_URL debe estar definida en producción');
  }
}
const HPS_SYSTEM_URL = HPS_SYSTEM_URL_ENV || 'http://localhost:3001';  // Fallback solo en desarrollo

/**
 * Obtener token desde HPS System usando iframe
 * @returns {Promise<string|null>} Token o null si no está disponible
 */
export const getTokenFromHPS = (): Promise<string | null> => {
  return new Promise((resolve) => {
    // Crear iframe oculto que apunta a HPS System
    const iframe = document.createElement('iframe');
    iframe.style.position = 'fixed';
    iframe.style.top = '-9999px';
    iframe.style.left = '-9999px';
    iframe.style.width = '1px';
    iframe.style.height = '1px';
    iframe.style.border = 'none';
    iframe.src = `${HPS_SYSTEM_URL}/token-sync.html`;
    
    const timeout = setTimeout(() => {
      if (iframe.parentNode) {
        document.body.removeChild(iframe);
      }
      resolve(null);
    }, 3000); // Reducido de 5000ms a 3000ms para mejor rendimiento
    
    const messageHandler = (event: MessageEvent) => {
      if (event.origin === new URL(HPS_SYSTEM_URL).origin && event.data.type === 'TOKEN_SYNC_RESPONSE') {
        clearTimeout(timeout);
        window.removeEventListener('message', messageHandler);
        if (iframe.parentNode) {
          document.body.removeChild(iframe);
        }
        if (event.data.token) {
          console.log('[tokenSync] ✅ Token recibido desde HPS System');
          resolve(event.data.token);
        } else {
          resolve(null);
        }
      }
    };
    
    window.addEventListener('message', messageHandler);
    
    iframe.onload = () => {
      setTimeout(() => {
        try {
          iframe.contentWindow?.postMessage({ type: 'REQUEST_TOKEN_SYNC' }, HPS_SYSTEM_URL);
        } catch (e) {
          console.log('[tokenSync] Error comunicándose con iframe:', e);
          clearTimeout(timeout);
          window.removeEventListener('message', messageHandler);
          if (iframe.parentNode) {
            document.body.removeChild(iframe);
          }
          resolve(null);
        }
      }, 500);
    };
    
    iframe.onerror = () => {
      clearTimeout(timeout);
      window.removeEventListener('message', messageHandler);
      if (iframe.parentNode) {
        document.body.removeChild(iframe);
      }
      resolve(null);
    };
    
    document.body.appendChild(iframe);
  });
};

/**
 * Sincronizar logout con HPS System
 * @returns {Promise<boolean>} true si se sincronizó correctamente
 */
export const syncLogoutWithHPS = (): Promise<boolean> => {
  return new Promise((resolve) => {
    const iframe = document.createElement('iframe');
    iframe.style.position = 'fixed';
    iframe.style.top = '-9999px';
    iframe.style.left = '-9999px';
    iframe.style.width = '1px';
    iframe.style.height = '1px';
    iframe.style.border = 'none';
    iframe.src = `${HPS_SYSTEM_URL}/token-sync.html`;
    
    const timeout = setTimeout(() => {
      if (iframe.parentNode) {
        document.body.removeChild(iframe);
      }
      resolve(false);
    }, 3000);
    
    const messageHandler = (event: MessageEvent) => {
      if (event.origin === new URL(HPS_SYSTEM_URL).origin && event.data.type === 'LOGOUT_SYNC_RESPONSE') {
        clearTimeout(timeout);
        window.removeEventListener('message', messageHandler);
        if (iframe.parentNode) {
          document.body.removeChild(iframe);
        }
        console.log('[tokenSync] ✅ Logout sincronizado con HPS System');
        resolve(true);
      }
    };
    
    window.addEventListener('message', messageHandler);
    
    iframe.onload = () => {
      setTimeout(() => {
        try {
          iframe.contentWindow?.postMessage({ type: 'LOGOUT_SYNC' }, HPS_SYSTEM_URL);
        } catch (e) {
          console.log('[tokenSync] Error sincronizando logout:', e);
          clearTimeout(timeout);
          window.removeEventListener('message', messageHandler);
          if (iframe.parentNode) {
            document.body.removeChild(iframe);
          }
          resolve(false);
        }
      }, 500);
    };
    
    iframe.onerror = () => {
      clearTimeout(timeout);
      window.removeEventListener('message', messageHandler);
      if (iframe.parentNode) {
        document.body.removeChild(iframe);
      }
      resolve(false);
    };
    
    document.body.appendChild(iframe);
  });
};

