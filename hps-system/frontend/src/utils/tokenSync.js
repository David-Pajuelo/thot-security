/**
 * Utilidades para sincronizar tokens entre HPS System y CryptoTrace
 * Usa iframe + postMessage para comunicación entre diferentes orígenes
 */

const CRYPTOTRACE_URL = process.env.REACT_APP_CRYPTOTRACE_URL || 'http://localhost:3000';

/**
 * Obtener token desde CryptoTrace usando iframe
 * @returns {Promise<string|null>} Token o null si no está disponible
 */
export const getTokenFromCryptoTrace = () => {
  return new Promise((resolve) => {
    // Crear iframe oculto que apunta a CryptoTrace
    const iframe = document.createElement('iframe');
    iframe.style.position = 'fixed';
    iframe.style.top = '-9999px';
    iframe.style.left = '-9999px';
    iframe.style.width = '1px';
    iframe.style.height = '1px';
    iframe.style.border = 'none';
    iframe.src = `${CRYPTOTRACE_URL}/token-sync.html`;
    
    const timeout = setTimeout(() => {
      if (iframe.parentNode) {
        document.body.removeChild(iframe);
      }
      resolve(null);
    }, 5000);
    
    const messageHandler = (event) => {
      if (event.origin === new URL(CRYPTOTRACE_URL).origin && event.data.type === 'TOKEN_SYNC_RESPONSE') {
        clearTimeout(timeout);
        window.removeEventListener('message', messageHandler);
        if (iframe.parentNode) {
          document.body.removeChild(iframe);
        }
        if (event.data.token) {
          console.log('[tokenSync] ✅ Token recibido desde CryptoTrace');
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
          iframe.contentWindow?.postMessage({ type: 'REQUEST_TOKEN_SYNC' }, CRYPTOTRACE_URL);
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
 * Sincronizar logout con CryptoTrace
 * @returns {Promise<boolean>} true si se sincronizó correctamente
 */
export const syncLogoutWithCryptoTrace = () => {
  return new Promise((resolve) => {
    const iframe = document.createElement('iframe');
    iframe.style.position = 'fixed';
    iframe.style.top = '-9999px';
    iframe.style.left = '-9999px';
    iframe.style.width = '1px';
    iframe.style.height = '1px';
    iframe.style.border = 'none';
    iframe.src = `${CRYPTOTRACE_URL}/token-sync.html`;
    
    const timeout = setTimeout(() => {
      if (iframe.parentNode) {
        document.body.removeChild(iframe);
      }
      resolve(false);
    }, 3000);
    
    const messageHandler = (event) => {
      if (event.origin === new URL(CRYPTOTRACE_URL).origin && event.data.type === 'LOGOUT_SYNC_RESPONSE') {
        clearTimeout(timeout);
        window.removeEventListener('message', messageHandler);
        if (iframe.parentNode) {
          document.body.removeChild(iframe);
        }
        console.log('[tokenSync] ✅ Logout sincronizado con CryptoTrace');
        resolve(true);
      }
    };
    
    window.addEventListener('message', messageHandler);
    
    iframe.onload = () => {
      setTimeout(() => {
        try {
          iframe.contentWindow?.postMessage({ type: 'LOGOUT_SYNC' }, CRYPTOTRACE_URL);
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

