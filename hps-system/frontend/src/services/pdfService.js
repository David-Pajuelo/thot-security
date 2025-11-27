import apiService from './apiService';

class PDFService {
  /**
   * Descargar un PDF desde una URL
   */
  async downloadPDF(url) {
    try {
      const response = await apiService.get(url, {
        responseType: 'blob'
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error downloading PDF:', error);
      
      // Manejar diferentes tipos de errores
      if (error.response?.status === 404) {
        return { 
          success: false, 
          error: '404 - Recurso no encontrado' 
        };
      }
      
      if (error.response?.status === 401) {
        return { 
          success: false, 
          error: '401 - No autorizado' 
        };
      }
      
      return { 
        success: false, 
        error: error.response?.data?.detail || `Error ${error.response?.status || 'desconocido'} al descargar el PDF` 
      };
    }
  }

  /**
   * Previsualizar un PDF en nueva ventana
   */
  async previewPDF(url) {
    try {
      const result = await this.downloadPDF(url);
      if (result.success) {
        // Crear blob con tipo MIME correcto
        const blob = new Blob([result.data], { type: 'application/pdf' });
        const objectUrl = window.URL.createObjectURL(blob);
        
        // Abrir en nueva ventana
        const newWindow = window.open(objectUrl, '_blank');
        if (newWindow) {
          // Limpiar URL después de un tiempo
          setTimeout(() => {
            window.URL.revokeObjectURL(objectUrl);
          }, 10000);
        }
        return { success: true };
      } else {
        return result;
      }
    } catch (err) {
      return { 
        success: false, 
        error: 'Error al previsualizar el PDF' 
      };
    }
  }

  /**
   * Descargar un PDF como archivo
   */
  async downloadPDFAsFile(url, filename) {
    try {
      const result = await this.downloadPDF(url);
      if (result.success) {
        const downloadUrl = window.URL.createObjectURL(new Blob([result.data]));
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(downloadUrl);
        return { success: true };
      } else {
        return result;
      }
    } catch (err) {
      return { 
        success: false, 
        error: 'Error al descargar el PDF' 
      };
    }
  }
}

export default new PDFService();
