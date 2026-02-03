// API utility functions for CryptoTrace frontend

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api';
const PROCESSING_URL = process.env.NEXT_PUBLIC_PROCESSING_URL || 'http://localhost:5001';
const OCR_URL = process.env.NEXT_PUBLIC_OCR_URL || 'http://localhost:8000';

// Helper function to get auth token
const getAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('accessToken');
};

// Helper function to refresh token
const refreshToken = async (): Promise<boolean> => {
  if (typeof window === 'undefined') return false;
  const refresh = localStorage.getItem('refreshToken');
  if (!refresh) return false;

  try {
    const response = await fetch(`${API_URL}/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('accessToken', data.access);
      return true;
    }
  } catch (error) {
    console.error('Error refreshing token:', error);
  }
  return false;
};

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

  // If unauthorized, try to refresh token
  if (response.status === 401 && token) {
    const refreshed = await refreshToken();
    if (refreshed) {
      const newToken = getAuthToken();
      if (newToken) {
        headers['Authorization'] = `Bearer ${newToken}`;
        response = await fetch(`${API_URL}${endpoint}`, {
          ...options,
          headers,
        });
      }
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

export const saveAC21Data = async (data: any, imagen?: File): Promise<any> => {
  const token = getAuthToken();
  
  // Si hay imagen, usar FormData; si no, usar JSON
  if (imagen) {
    const formData = new FormData();
    // El backend espera los datos en un campo 'data' cuando es FormData
    formData.append('data', JSON.stringify(data));
    formData.append('imagen_documento', imagen);

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
export const procesarAlbaranDirecto = async (data: any, imagen?: File): Promise<any> => {
  const token = getAuthToken();
  
  // Si hay imagen, usar FormData; si no, usar JSON
  if (imagen) {
    const formData = new FormData();
    formData.append('data', JSON.stringify(data));
    formData.append('imagen_documento', imagen);

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
export const guardarEnLineaTemporal = async (data: any, imagen?: File): Promise<any> => {
  const token = getAuthToken();
  
  // Si hay imagen, usar FormData; si no, usar JSON
  if (imagen) {
    const formData = new FormData();
    formData.append('data', JSON.stringify(data));
    formData.append('imagen_documento', imagen);

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

