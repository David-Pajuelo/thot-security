// API utility functions for CryptoTrace frontend
// Sesión: ver docs/ANALISIS-Y-PLAN-MEJORA-SESION-USUARIO.md

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api';
const PROCESSING_URL = process.env.NEXT_PUBLIC_PROCESSING_URL || 'http://localhost:5001';
const OCR_URL = process.env.NEXT_PUBLIC_OCR_URL || 'http://localhost:8000';

const TOKEN_KEYS = ['accessToken', 'refreshToken', 'hps_token', 'hps_refresh_token', 'user', 'hps_user', 'hps_saved_email'] as const;

/** Limpia todos los datos de sesión y redirige a login. Usar cuando el refresh falle o la sesión sea inválida. */
export function clearSessionAndRedirect(): void {
  if (typeof window === 'undefined') return;
  for (const key of TOKEN_KEYS) {
    localStorage.removeItem(key);
  }
  const base = typeof window !== 'undefined' && window.location.pathname.startsWith('/cryptotrace') ? '/cryptotrace' : '';
  window.location.href = base ? `${base}/login` : '/login';
}

// Helper function to get auth token (compatibilidad con hps_token)
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('accessToken') || localStorage.getItem('hps_token');
}

/** Nombre de archivo para enviar imagen (File o Blob) en FormData; evita "blob" sin extensión. */
function nombreArchivoImagen(imagen: File | Blob): string {
  return imagen instanceof File ? imagen.name : 'documento.png';
}

/** Devuelve la fecha de expiración del JWT (claim exp) en segundos, o null si no se puede leer. */
export function getTokenExpiration(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return typeof payload.exp === 'number' ? payload.exp : null;
  } catch {
    return null;
  }
}

/** Minutos antes de expirar el access token para hacer el refresh proactivo. El lifetime del token se configura en backend (p. ej. 2 h). */
const PROACTIVE_REFRESH_MINUTES = 5;

/** Intenta renovar el access token. Devuelve true solo si se renovó correctamente. */
export async function refreshTokenAsync(): Promise<boolean> {
  const result = await doRefreshTokenDetailed();
  return result === 'ok';
}

type RefreshResult = 'ok' | 'invalid' | 'transient';

/**
 * Resultado del refresh:
 * - ok: token renovado
 * - invalid: refresh inválido/caducado (se debe cerrar sesión)
 * - transient: error temporal (red/5xx). No forzar logout inmediato.
 */
async function doRefreshTokenDetailed(): Promise<RefreshResult> {
  if (typeof window === 'undefined') return 'transient';
  const refresh = localStorage.getItem('refreshToken') || localStorage.getItem('hps_refresh_token');
  if (!refresh) return 'invalid';

  try {
    const response = await fetch(`${API_URL}/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });

    if (response.ok) {
      const data = await response.json();
      const access = data.access;
      const newRefresh = data.refresh;
      if (access) {
        localStorage.setItem('accessToken', access);
        localStorage.setItem('hps_token', access);
      }
      if (newRefresh) {
        localStorage.setItem('refreshToken', newRefresh);
        localStorage.setItem('hps_refresh_token', newRefresh);
      }
      return 'ok';
    }

    // 400/401/403 => refresh inválido o expirado
    if ([400, 401, 403].includes(response.status)) {
      return 'invalid';
    }
  } catch (error) {
    console.error('Error refreshing token:', error);
    return 'transient';
  }

  // Otros códigos (5xx, etc.) se consideran transitorios
  return 'transient';
}

async function doRefreshToken(): Promise<boolean> {
  return (await doRefreshTokenDetailed()) === 'ok';
}

/**
 * fetch con autenticación: añade Bearer, ante 401 intenta refresh y reintenta una vez.
 * Si el refresh falla, limpia sesión y redirige a /login (no retorna).
 * Usar para peticiones que necesitan URL completa (blob, HTML, etc.).
 */
export async function fetchWithAuth(
  input: RequestInfo | URL,
  init?: RequestInit,
  options?: { skipRetry?: boolean }
): Promise<Response> {
  const skipRetry = options?.skipRetry ?? false;
  const token = getAuthToken();
  const headers = new Headers(init?.headers);
  if (token) headers.set('Authorization', `Bearer ${token}`);

  let response = await fetch(input, { ...init, headers });

  if (response.status === 401 && token && !skipRetry) {
    const refreshResult = await doRefreshTokenDetailed();
    if (refreshResult === 'ok') {
      const newToken = getAuthToken();
      if (newToken) {
        headers.set('Authorization', `Bearer ${newToken}`);
        return fetch(input, { ...init, headers });
      }
    }
    if (refreshResult === 'invalid') {
      clearSessionAndRedirect();
      throw new Error('Sesión expirada. Redirigiendo al login.');
    }
    throw new Error('No se pudo refrescar la sesión temporalmente. Reintenta.');
  }

  return response;
}

/**
 * Programa un refresh proactivo del access token X minutos antes de que expire.
 * Si el refresh falla, limpia sesión y redirige a login.
 * @returns Función de limpieza (cancelar el programado).
 */
export function scheduleProactiveRefresh(): () => void {
  if (typeof window === 'undefined') return () => {};

  const token = getAuthToken();
  if (!token) return () => {};

  const exp = getTokenExpiration(token);
  if (!exp) return () => {};

  const nowSec = Math.floor(Date.now() / 1000);
  const delaySec = exp - nowSec - PROACTIVE_REFRESH_MINUTES * 60;
  if (delaySec <= 0) {
    // Ya está próximo a expirar o expirado; intentar refresh ya
    doRefreshTokenDetailed().then((result) => {
      if (result === 'ok') {
        window.dispatchEvent(new Event('tokenUpdated'));
      } else if (result === 'invalid') {
        clearSessionAndRedirect();
      } else {
        // Error temporal (red/5xx): no cerrar sesión; reintentar en 60s
        window.setTimeout(() => scheduleProactiveRefresh(), 60 * 1000);
      }
    });
    return () => {};
  }

  const timeoutId = window.setTimeout(async () => {
    const result = await doRefreshTokenDetailed();
    if (result === 'invalid') {
      clearSessionAndRedirect();
      return;
    }
    if (result === 'ok') {
      window.dispatchEvent(new Event('tokenUpdated'));
      // Reprogramar con el nuevo token
      scheduleProactiveRefresh();
      return;
    }
    // Error transitorio: reintentar pronto sin tirar sesión
    window.setTimeout(() => scheduleProactiveRefresh(), 60 * 1000);
  }, delaySec * 1000);

  return () => window.clearTimeout(timeoutId);
}

// Generic API fetch function with auth
export const apiFetch = async (
  endpoint: string,
  options: RequestInit = {}
): Promise<any> => {
  const token = getAuthToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // If unauthorized, try to refresh token; if refresh fails, clear session and redirect to login
  if (response.status === 401 && token) {
    const refreshResult = await doRefreshTokenDetailed();
    if (refreshResult === 'ok') {
      const newToken = getAuthToken();
      if (newToken) {
        headers['Authorization'] = `Bearer ${newToken}`;
        response = await fetch(`${API_URL}${endpoint}`, {
          ...options,
          headers,
        });
      }
    }
    if (response.status === 401 && refreshResult === 'invalid') {
      clearSessionAndRedirect();
      throw new Error('Sesión expirada. Redirigiendo al login.');
    }
    if (response.status === 401 && refreshResult === 'transient') {
      throw new Error('No se pudo validar sesión temporalmente. Reintenta.');
    }
  }

  if (!response.ok) {
    // Try to get error message from response
    let errorMessage = `API error: ${response.status} ${response.statusText}`;
    let errorData: any = null;
    try {
      const text = await response.text();
      if (text.trim()) {
        try {
          errorData = JSON.parse(text);
          errorMessage = errorData.detail || errorData.message || errorData.error || errorMessage;
        } catch {
          // Si no es JSON válido, usar el texto como mensaje
          errorMessage = text || errorMessage;
        }
      }
    } catch (e) {
      // Si hay error al leer la respuesta, usar status text
      console.warn('Error al leer respuesta de error:', e);
    }
    const error = new Error(errorMessage);
    (error as any).status = response.status;
    (error as any).data = errorData || {};
    // Log error with endpoint information
    console.error('❌ API Error:', { 
      status: response.status, 
      errorData, 
      errorMessage, 
      endpoint: endpoint || 'unknown'
    });
    throw error;
  }

  // Handle 204 No Content responses (common for DELETE operations)
  if (response.status === 204) {
    return;
  }

  // Check if response has content before trying to parse JSON
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    const text = await response.text();
    if (text.trim() === '') {
      return;
    }
    try {
      return JSON.parse(text);
    } catch (e) {
      // If JSON parsing fails, return empty
      return;
    }
  }

  // If no JSON content type, return empty
  return;
};

// Productos
export const fetchProductos = async (): Promise<any[]> => {
  return apiFetch('/productos/');
};

export const fetchProductosAgrupados = async (): Promise<{
  productos: any[];
  tipos_disponibles: string[];
}> => {
  return apiFetch('/lineas-temporales/agrupados/');
};

export const fetchProductoById = async (id: number): Promise<any> => {
  return apiFetch(`/productos/${id}/`);
};

export const fetchTiposProducto = async (): Promise<{ id: number; nombre: string }[]> => {
  return apiFetch('/tipos-producto/');
};

export const crearProductoCatalogo = async (producto: any): Promise<any> => {
  return apiFetch('/productos/', {
    method: 'POST',
    body: JSON.stringify(producto),
  });
};

export const guardarTipoProducto = async (codigoProducto: string, tipo: string): Promise<any> => {
  return apiFetch('/lineas-temporales/asignar-tipo/', {
    method: 'POST',
    body: JSON.stringify({ codigo_producto: codigoProducto, tipo }),
  });
};

// Actualizar el tipo de cryptocustodio (tipo_producto) de las líneas temporales
export const guardarTipoCryptocustodio = async (codigoProducto: string, tipoProductoId: number): Promise<any> => {
  return apiFetch('/lineas-temporales/actualizar-cc/', {
    method: 'POST',
    body: JSON.stringify({ codigo_producto: codigoProducto, tipo_producto_id: tipoProductoId }),
  });
};

// Inventario
export const fetchInventario = async (): Promise<any[]> => {
  return apiFetch('/inventario/');
};

export const fetchInventarioResumen = async (): Promise<any> => {
  return apiFetch('/inventario/resumen/');
};

// Albaranes
export const fetchAlbaranById = async (id: number): Promise<any> => {
  return apiFetch(`/albaranes/${id}/`);
};

export const fetchDocumentosPrincipales = async (): Promise<any[]> => {
  return apiFetch('/albaranes/principales/');
};

export const deleteAlbaran = async (id: number): Promise<void> => {
  return apiFetch(`/albaranes/${id}/`, { method: 'DELETE' });
};

export const fetchMovimientosAlbaran = async (albaranId: number): Promise<any[]> => {
  return apiFetch(`/albaranes/${albaranId}/movimientos/`);
};

export const obtenerSiguienteNumeroRegistroSalida = async (): Promise<string> => {
  const data = await apiFetch('/albaranes/siguiente-numero-registro-salida/');
  return data.numero_registro_salida;
};

export const obtenerProductosDeAlbaran = async (numeroAlbaran: string): Promise<any> => {
  return apiFetch('/albaranes/productos-de-albaran/', {
    method: 'POST',
    body: JSON.stringify({ numero: numeroAlbaran }),
  });
};

export const verificarDocumentoExistente = async (numeroRegistro: string): Promise<{ existe: boolean; documento: any | null }> => {
  // Buscar albarán por número de registro
  const albaranes = await apiFetch(`/albaranes/?numero_registro=${numeroRegistro}`);
  if (albaranes.length > 0) {
    return {
      existe: true,
      documento: albaranes[0]
    };
  }
  return {
    existe: false,
    documento: null
  };
};

export const obtenerPaginasDocumento = async (albaranId: number): Promise<any[]> => {
  return apiFetch(`/albaranes/${albaranId}/paginas/`, {
    method: 'GET',
  });
};

export const crearPaginaAdicional = async (albaranId: number, payload: any): Promise<any> => {
  return apiFetch(`/albaranes/${albaranId}/paginas/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
};

// Empresas
export const fetchEmpresas = async (): Promise<any[]> => {
  return apiFetch('/empresas/');
};

export const createEmpresa = async (empresa: any): Promise<any> => {
  return apiFetch('/empresas/', {
    method: 'POST',
    body: JSON.stringify(empresa),
  });
};

export const updateEmpresa = async (id: number, empresa: any): Promise<any> => {
  return apiFetch(`/empresas/${id}/`, {
    method: 'PUT',
    body: JSON.stringify(empresa),
  });
};

export const deleteEmpresa = async (id: number): Promise<void> => {
  return apiFetch(`/empresas/${id}/`, { method: 'DELETE' });
};

// Cryptocustodios
export const fetchCryptocustodios = async (empresaId?: number): Promise<any[]> => {
  const url = empresaId != null ? `/cryptocustodios/?empresa=${empresaId}` : '/cryptocustodios/';
  return apiFetch(url);
};

export const createCryptocustodio = async (data: { empleo_rango?: string; nombre_apellidos: string; cargo?: string; empresa: number }): Promise<any> => {
  return apiFetch('/cryptocustodios/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const updateCryptocustodio = async (id: number, data: Partial<{ empleo_rango: string; nombre_apellidos: string; cargo: string }>): Promise<any> => {
  return apiFetch(`/cryptocustodios/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
};

export const deleteCryptocustodio = async (id: number): Promise<void> => {
  return apiFetch(`/cryptocustodios/${id}/`, { method: 'DELETE' });
};

// AC21 Processing
export const processAC21Image = async (formData: FormData): Promise<any> => {
  const token = getAuthToken();
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${OCR_URL}/process-image/`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`OCR error: ${response.status} ${response.statusText}`);
  }

  return response.json();
};

export const processAC21Companies = async (formData: FormData): Promise<any> => {
  const token = getAuthToken();
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Nota: Este endpoint puede no existir en el OCR actual
  // Si se necesita, debería usar /process-image/ con document_type=ac21
  const response = await fetch(`${OCR_URL}/process-image/`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`OCR error: ${response.status} ${response.statusText}`);
  }

  return response.json();
};

export const saveAC21Data = async (data: any, imagen?: File | Blob): Promise<any> => {
  const token = getAuthToken();
  if (imagen) {
    const formData = new FormData();
    formData.append('data', JSON.stringify(data));
    formData.append('imagen_documento', imagen, nombreArchivoImagen(imagen));

    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}/albaranes/`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Error desconocido' }));
      throw new Error(error.error || error.message || error.detail || `Error: ${response.status}`);
    }

    return response.json();
  } else {
    // Sin imagen, enviar como JSON
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}/albaranes/`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Error desconocido' }));
      throw new Error(error.error || error.message || error.detail || `Error: ${response.status}`);
    }

    return response.json();
  }
};

// Excel Upload
export const uploadExcel = async (file: File): Promise<any> => {
  const token = getAuthToken();
  const formData = new FormData();
  formData.append('file', file);

  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${PROCESSING_URL}/upload-excel/`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload error: ${response.status} ${response.statusText}`);
  }

  return response.json();
};

// Catalog Management
export const obtenerProductosSinTipo = async (): Promise<any> => {
  // El endpoint está en CatalogoProductoViewSet con url_path='productos-sin-tipo'
  // Devuelve { productos: [], total: 0, huerfanos: 0, con_movimientos: 0 }
  return apiFetch('/productos/productos-sin-tipo/');
};

export const limpiarProductosHuerfanos = async (): Promise<any> => {
  return apiFetch('/productos/limpiar-huerfanos/', { method: 'POST' });
};

export const asignarTiposAutomatico = async (): Promise<any> => {
  return apiFetch('/productos/asignar-tipos-automatico/', { method: 'POST' });
};

export const procesarAlbaran = async (): Promise<any> => {
  // El backend procesa todos los productos temporales no procesados del usuario
  // No requiere payload, solo hace POST al endpoint
  return apiFetch('/lineas-temporales/procesar/', { method: 'POST' });
};

// Procesar AC21 directamente sin usar línea temporal (nuevo flujo)
export const procesarAlbaranDirecto = async (data: any, imagen?: File | Blob): Promise<any> => {
  const token = getAuthToken();
  if (imagen) {
    const formData = new FormData();
    formData.append('data', JSON.stringify(data));
    formData.append('imagen_documento', imagen, nombreArchivoImagen(imagen));

    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}/lineas-temporales/procesar-directo/`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = new Error(errorData.detail || errorData.error || `Error ${response.status}`);
      (error as any).status = response.status;
      (error as any).data = errorData;
      throw error;
    }

    return await response.json();
  } else {
    // Sin imagen, usar JSON
    return apiFetch('/lineas-temporales/procesar-directo/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
};

// Guardar productos en línea temporal sin crear albarán (para AC21 de ENTRADA)
export const guardarEnLineaTemporal = async (data: any, imagen?: File | Blob): Promise<any> => {
  const token = getAuthToken();
  if (imagen) {
    const formData = new FormData();
    formData.append('data', JSON.stringify(data));
    formData.append('imagen_documento', imagen, nombreArchivoImagen(imagen));

    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}/lineas-temporales/bulk_create/`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Error desconocido' }));
      throw new Error(error.error || error.message || error.detail || `Error: ${response.status}`);
    }

    return response.json();
  } else {
    // Sin imagen, enviar como JSON
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}/lineas-temporales/bulk_create/`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Error desconocido' }));
      throw new Error(error.error || error.message || error.detail || `Error: ${response.status}`);
    }

    return response.json();
  }
};

// User Profile
export const obtenerPerfilUsuario = async (): Promise<any> => {
  return apiFetch('/auth/perfil/');
};

export const cambiarPassword = async (passwords: { current_password: string; new_password: string; confirm_password: string }): Promise<any> => {
  return apiFetch('/auth/cambiar-password/', {
    method: 'POST',
    body: JSON.stringify(passwords),
  });
};

// Types
export interface ProductoCatalogo {
  id: number;
  codigo_producto: string;
  descripcion: string;
  tipo?: string;
  tipo_nombre?: string;
}

