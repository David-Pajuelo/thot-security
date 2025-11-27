/**
 * Servicio para gestión de solicitudes HPS
 */
import apiService from './apiService';

class HPSService {
  constructor() {
    this.baseURL = '/api/hps/requests';
  }

  /**
   * Crear una nueva solicitud HPS (autenticado)
   */
  async createRequest(requestData) {
    try {
      const response = await apiService.post(`${this.baseURL}/`, requestData);
      return { success: true, data: response };
    } catch (error) {
      console.error('Error creating HPS request:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al crear la solicitud HPS' 
      };
    }
  }

  /**
   * Crear una nueva solicitud HPS usando token (público)
   */
  async createRequestWithToken(requestData, token, hpsType = 'solicitud') {
    try {
      const response = await apiService.post(`${this.baseURL}/public/?token=${token}&hps_type=${hpsType}`, requestData);
      return { success: true, data: response };
    } catch (error) {
      console.error('Error creating HPS request with token:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al crear la solicitud HPS' 
      };
    }
  }

  /**
   * Crear un token HPS seguro (solo admin/leaders)
   */
  async createToken(tokenData) {
    try {
      const response = await apiService.post('/api/hps/tokens/', tokenData);
      console.log('HPS Token API response:', response);
      console.log('HPS Token API response data:', response.data);
      return { success: true, data: response.data || response };
    } catch (error) {
      console.error('Error creating HPS token:', error);
      console.error('Error details:', error.response);
      
      if (error.response?.status === 403) {
        return { 
          success: false, 
          error: 'No tienes permisos para crear tokens HPS. Solo administradores y líderes de equipo pueden crear tokens.' 
        };
      }
      
      if (error.response?.status === 401) {
        return { 
          success: false, 
          error: 'Debes estar autenticado para crear tokens HPS. Por favor, inicia sesión.' 
        };
      }
      
      return { 
        success: false, 
        error: error.response?.data?.detail || `Error al crear el token HPS: ${error.message}` 
      };
    }
  }

  /**
   * Validar un token HPS
   */
  async validateToken(token, email = null) {
    try {
      const params = new URLSearchParams({ token });
      if (email) params.append('email', email);
      
      const response = await apiService.get(`/api/hps/tokens/validate/?${params}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error validating HPS token:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al validar el token HPS' 
      };
    }
  }

  /**
   * Obtener lista de solicitudes HPS
   */
  async getRequests(params = {}) {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page);
      if (params.per_page) queryParams.append('per_page', params.per_page);
      if (params.status) queryParams.append('status', params.status);
      if (params.request_type) queryParams.append('request_type', params.request_type);
      if (params.form_type) queryParams.append('form_type', params.form_type);
      if (params.hps_type) queryParams.append('hps_type', params.hps_type);
      if (params.user_id) queryParams.append('user_id', params.user_id);
      if (params.team_id) queryParams.append('team_id', params.team_id);

      const url = queryParams.toString() ? `${this.baseURL}/?${queryParams}` : `${this.baseURL}/`;
      const response = await apiService.get(url);
      
      // Django REST Framework puede devolver:
      // - Array directo: [obj1, obj2, ...]
      // - Objeto paginado: {count: X, next: null, previous: null, results: [...]}
      let requests = [];
      let total = 0;
      let pages = 1;
      let page = 1;
      
      if (Array.isArray(response.data)) {
        // Respuesta directa sin paginación
        requests = response.data;
        total = requests.length;
        pages = 1;
        page = 1;
      } else if (response.data && Array.isArray(response.data.results)) {
        // Respuesta paginada
        requests = response.data.results;
        total = response.data.count || requests.length;
        pages = Math.ceil(total / (params.per_page || 10));
        page = response.data.page || parseInt(params.page) || 1;
      } else if (response.data && Array.isArray(response.data.requests)) {
        // Formato antiguo del frontend
        requests = response.data.requests;
        total = response.data.total || requests.length;
        pages = response.data.pages || 1;
        page = response.data.page || 1;
      } else {
        // Formato desconocido, intentar usar directamente
        requests = [];
        console.warn('Formato de respuesta desconocido:', response.data);
      }
      
      return { 
        success: true, 
        data: {
          requests: requests,
          total: total,
          pages: pages,
          page: page
        }
      };
    } catch (error) {
      console.error('Error fetching HPS requests:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al obtener las solicitudes HPS' 
      };
    }
  }

  /**
   * Obtener una solicitud HPS específica
   */
  async getRequest(requestId) {
    try {
      const response = await apiService.get(`${this.baseURL}/${requestId}/`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching HPS request:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al obtener la solicitud HPS' 
      };
    }
  }

  /**
   * Actualizar una solicitud HPS
   */
  async updateRequest(requestId, updateData) {
    try {
      const response = await apiService.put(`${this.baseURL}/${requestId}/`, updateData);
      return { success: true, data: response };
    } catch (error) {
      console.error('Error updating HPS request:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al actualizar la solicitud HPS' 
      };
    }
  }

  /**
   * Marcar solicitud como enviada
   */
  async submitRequest(requestId, notes = '') {
    try {
      // Django usa el endpoint submit como acción del ViewSet
      const url = `${this.baseURL}/${requestId}/submit/`;
      const response = await apiService.post(url, notes ? { notes } : {});
      return { success: true, data: response };
    } catch (error) {
      console.error('Error submitting HPS request:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al marcar la solicitud como enviada' 
      };
    }
  }

  /**
   * Aprobar solicitud HPS
   */
  async approveRequest(requestId, expiresAt = null, notes = '') {
    try {
      const queryParams = new URLSearchParams();
      if (expiresAt) queryParams.append('expires_at', expiresAt);
      if (notes) queryParams.append('notes', notes);

      const url = `${this.baseURL}/${requestId}/approve/${queryParams.toString() ? `?${queryParams}` : ''}`;
      const response = await apiService.post(url);
      return { success: true, data: response };
    } catch (error) {
      console.error('Error approving HPS request:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al aprobar la solicitud HPS' 
      };
    }
  }

  /**
   * Rechazar solicitud HPS
   */
  async rejectRequest(requestId, notes = '') {
    try {
      const url = `${this.baseURL}/${requestId}/reject/${notes ? `?notes=${encodeURIComponent(notes)}` : ''}`;
      const response = await apiService.post(url);
      return { success: true, data: response };
    } catch (error) {
      console.error('Error rejecting HPS request:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al rechazar la solicitud HPS' 
      };
    }
  }

  /**
   * Eliminar solicitud HPS (solo admin)
   */
  async deleteRequest(requestId) {
    try {
      await apiService.delete(`${this.baseURL}/${requestId}/`);
      return { success: true };
    } catch (error) {
      console.error('Error deleting HPS request:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al eliminar la solicitud HPS' 
      };
    }
  }

  /**
   * Obtener estadísticas de solicitudes HPS
   */
  async getStats() {
    try {
      const response = await apiService.get(`${this.baseURL}/stats/`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching HPS stats:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al obtener las estadísticas HPS' 
      };
    }
  }

  /**
   * Obtener HPS del equipo
   */
  async getTeamHps(teamId) {
    try {
      const response = await apiService.get(`${this.baseURL}/team/${teamId}/`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching team HPS:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al obtener HPS del equipo' 
      };
    }
  }

  /**
   * Obtener solicitudes pendientes
   */
  async getPendingRequests() {
    try {
      const response = await apiService.get(`${this.baseURL}/pending/list/`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching pending HPS requests:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al obtener las solicitudes pendientes' 
      };
    }
  }

  /**
   * Obtener solicitudes enviadas
   */
  async getSubmittedRequests() {
    try {
      const response = await apiService.get(`${this.baseURL}/submitted/list/`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching submitted HPS requests:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al obtener las solicitudes enviadas' 
      };
    }
  }

  /**
   * Constantes para el frontend
   */
  static get REQUEST_TYPES() {
    return {
      NEW: 'new',
      RENEWAL: 'renewal',
      TRANSFER: 'transfer'
    };
  }

  static get DOCUMENT_TYPES() {
    return {
      DNI: 'DNI',
      NIE: 'NIE',
      PASSPORT: 'PASSPORT'
    };
  }

  static get STATUS() {
    return {
      PENDING: 'pending',
      WAITING_DPS: 'waiting_dps',
      SUBMITTED: 'submitted',
      APPROVED: 'approved',
      REJECTED: 'rejected',
      EXPIRED: 'expired'
    };
  }

  static get STATUS_LABELS() {
    return {
      pending: 'Pendiente',
      waiting_dps: 'En espera DPS',
      submitted: 'Enviada',
      approved: 'Aprobada',
      rejected: 'Rechazada',
      expired: 'Expirada'
    };
  }

  static get REQUEST_TYPE_LABELS() {
    return {
      new: 'Nueva',
      renewal: 'Renovación',
      transfer: 'Traspaso'
    };
  }

  static get DOCUMENT_TYPE_LABELS() {
    return {
      DNI: 'DNI',
      NIE: 'NIE',
      PASSPORT: 'Pasaporte'
    };
  }

  /**
   * Obtener información de token HPS
   */
  async getTokenInfo(token) {
    try {
      const response = await apiService.get(`/api/hps/tokens/info/?token=${token}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error getting token info:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al obtener información del token' 
      };
    }
  }

  /**
   * Previsualizar PDF rellenado de una solicitud HPS
   */
  async previewFilledPDF(hpsId) {
    try {
      const pdfService = (await import('./pdfService')).default;
      const url = `${this.baseURL}/${hpsId}/filled-pdf/`;
      const result = await pdfService.previewPDF(url);
      
      // Manejar específicamente el error 404
      if (!result.success && result.error && result.error.includes('404')) {
        return {
          success: false,
          error: 'No hay PDF rellenado disponible para esta solicitud'
        };
      }
      
      return result;
    } catch (error) {
      console.error('Error previewing filled PDF:', error);
      return { 
        success: false, 
        error: 'Error al previsualizar el PDF rellenado' 
      };
    }
  }

  /**
   * Obtener PDF rellenado como bytes para edición
   */
  async getFilledPDFBytes(hpsId) {
    try {
      const response = await apiService.get(`${this.baseURL}/${hpsId}/filled-pdf/`, {
        responseType: 'arraybuffer'
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error getting filled PDF bytes:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al obtener el PDF' 
      };
    }
  }

  /**
   * Descargar PDF rellenado de una solicitud HPS
   */
  async downloadFilledPDF(hpsId, filename = null) {
    try {
      const pdfService = (await import('./pdfService')).default;
      const url = `${this.baseURL}/${hpsId}/filled-pdf/`;
      const finalFilename = filename || `hps_filled_${hpsId}.pdf`;
      const result = await pdfService.downloadPDFAsFile(url, finalFilename);
      
      // Manejar específicamente el error 404
      if (!result.success && result.error && result.error.includes('404')) {
        return {
          success: false,
          error: 'No hay PDF rellenado disponible para esta solicitud'
        };
      }
      
      return result;
    } catch (error) {
      console.error('Error downloading filled PDF:', error);
      return { 
        success: false, 
        error: 'Error al descargar el PDF rellenado' 
      };
    }
  }

  /**
   * Previsualizar PDF de respuesta de una solicitud HPS
   */
  async previewResponsePDF(hpsId) {
    try {
      const pdfService = (await import('./pdfService')).default;
      const url = `${this.baseURL}/${hpsId}/response-pdf/`;
      return await pdfService.previewPDF(url);
    } catch (error) {
      console.error('Error previewing response PDF:', error);
      return { 
        success: false, 
        error: 'Error al previsualizar el PDF de respuesta' 
      };
    }
  }

  /**
   * Descargar PDF de respuesta de una solicitud HPS
   */
  async downloadResponsePDF(hpsId, filename = null) {
    try {
      const pdfService = (await import('./pdfService')).default;
      const url = `${this.baseURL}/${hpsId}/response-pdf/`;
      const finalFilename = filename || `hps_response_${hpsId}.pdf`;
      return await pdfService.downloadPDFAsFile(url, finalFilename);
    } catch (error) {
      console.error('Error downloading response PDF:', error);
      return { 
        success: false, 
        error: 'Error al descargar el PDF de respuesta' 
      };
    }
  }

  /**
   * Editar campos específicos del PDF rellenado
   */
  async editFilledPDF(hpsId, fieldUpdates) {
    try {
      const response = await apiService.post(`${this.baseURL}/${hpsId}/edit-filled-pdf/`, fieldUpdates);
      return { success: true, data: response };
    } catch (error) {
      console.error('Error editing filled PDF:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al editar el PDF' 
      };
    }
  }

  /**
   * Subir PDF modificado
   */
  async uploadModifiedPDF(hpsId, pdfBytes) {
    try {
      const formData = new FormData();
      const blob = new Blob([pdfBytes], { type: 'application/pdf' });
      formData.append('pdf_file', blob, 'modified.pdf');
      
      const response = await apiService.post(`${this.baseURL}/${hpsId}/upload-filled-pdf/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return { success: true, data: response };
    } catch (error) {
      console.error('Error uploading modified PDF:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al subir el PDF modificado' 
      };
    }
  }

  /**
   * Extraer campos del PDF usando PyMuPDF en el backend
   */
  async extractPDFFields(hpsId) {
    try {
      const response = await apiService.get(`${this.baseURL}/${hpsId}/extract-pdf-fields/`);
      console.log('Respuesta del backend:', response);
      
      // El backend devuelve los campos en response.data
      if (response.data && typeof response.data === 'object') {
        return { success: true, data: response.data };
      } else {
        return { success: false, error: 'No se pudieron extraer los campos' };
      }
    } catch (error) {
      console.error('Error extracting PDF fields:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al extraer campos del PDF' 
      };
    }
  }
}

const hpsService = new HPSService();
export default hpsService;
