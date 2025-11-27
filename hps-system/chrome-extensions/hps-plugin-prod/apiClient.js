// Cliente API para el backend HPS
const API_BASE_URL = 'http://localhost:8001/api/v1/extension';

class ApiClient {
  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Obtener lista de solicitudes pendientes (nuevas y renovaciones)
  async getSolicitudes() {
    return this.request('/personas?tipo=solicitud');
  }

  // Obtener lista de traslados pendientes
  async getTraslados() {
    return this.request('/personas?tipo=traslado');
  }

  // Obtener datos de una persona por DNI
  async getPersonaPorDni(dni) {
    return this.request(`/persona/${dni}`);
  }

  // Actualizar estado de una solicitud
  async actualizarEstadoSolicitud(dni, estado) {
    return this.request(`/solicitud/${dni}/estado`, {
      method: 'PUT',
      body: JSON.stringify({ estado })
    });
  }

  // Marcar solicitud como enviada
  async marcarSolicitudEnviada(dni) {
    return this.request(`/solicitud/${dni}/enviada`, {
      method: 'PUT'
    });
  }

  // Marcar traslado como enviado
  async marcarTrasladoEnviado(dni) {
    return this.request(`/traslado/${dni}/enviado`, {
      method: 'PUT'
    });
  }

  // Descargar PDF de traslado - Solo devuelve la URL
  async descargarPdf(dni) {
    const url = `${this.baseUrl}/traslado/${dni}/pdf`;
    return { success: true, url: url };
  }
}

export const apiClient = new ApiClient();