import apiService from './apiService';

class TemplateService {
  constructor() {
    this.baseURL = '/api/hps/templates';
  }

  /**
   * Obtener lista de plantillas
   */
  async getTemplates(params = {}) {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page);
      if (params.per_page) queryParams.append('per_page', params.per_page);
      if (params.active !== undefined) queryParams.append('active', params.active);

      const url = queryParams.toString() ? `${this.baseURL}/?${queryParams}` : `${this.baseURL}/`;
      const response = await apiService.get(url);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching templates:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al obtener las plantillas' 
      };
    }
  }

  /**
   * Crear nueva plantilla
   */
  async createTemplate(templateData) {
    try {
      const formData = new FormData();
      formData.append('name', templateData.name);
      formData.append('template_type', templateData.template_type || 'jefe_seguridad');
      formData.append('active', true); // Siempre activa
      formData.append('template_pdf', templateData.template_pdf);

      const response = await apiService.post(`${this.baseURL}/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating template:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al crear la plantilla' 
      };
    }
  }

  /**
   * Obtener plantilla por ID
   */
  async getTemplate(id) {
    try {
      const response = await apiService.get(`${this.baseURL}/${id}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching template:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al obtener la plantilla' 
      };
    }
  }

  /**
   * Actualizar plantilla
   */
  async updateTemplate(id, templateData) {
    try {
      const formData = new FormData();
      if (templateData.name) formData.append('name', templateData.name);
      if (templateData.description !== undefined) formData.append('description', templateData.description);
      if (templateData.template_type) formData.append('template_type', templateData.template_type);
      if (templateData.version) formData.append('version', templateData.version);
      if (templateData.active !== undefined) formData.append('active', templateData.active);
      if (templateData.template_pdf) formData.append('template_pdf', templateData.template_pdf);

      // Si hay PDF, usar el endpoint con PDF, sino el normal
      if (templateData.template_pdf) {
        const response = await apiService.put(`${this.baseURL}/${id}/pdf`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        return { success: true, data: response.data };
      } else {
        // Convertir FormData a objeto para el endpoint normal
        const updateData = {};
        if (templateData.name) updateData.name = templateData.name;
        if (templateData.description !== undefined) updateData.description = templateData.description;
        if (templateData.template_type) updateData.template_type = templateData.template_type;
        if (templateData.version) updateData.version = templateData.version;
        if (templateData.active !== undefined) updateData.active = templateData.active;
        
        const response = await apiService.put(`${this.baseURL}/${id}`, updateData);
        return { success: true, data: response.data };
      }
    } catch (error) {
      console.error('Error updating template:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al actualizar la plantilla' 
      };
    }
  }

  /**
   * Eliminar plantilla
   */
  async deleteTemplate(id) {
    try {
      await apiService.delete(`${this.baseURL}/${id}`);
      return { success: true };
    } catch (error) {
      console.error('Error deleting template:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al eliminar la plantilla' 
      };
    }
  }

  /**
   * Descargar PDF de plantilla
   */
  async downloadTemplate(id) {
    try {
      const response = await apiService.get(`${this.baseURL}/${id}/pdf`, {
        responseType: 'blob'
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error downloading template:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al descargar la plantilla' 
      };
    }
  }

  /**
   * Obtener bytes del PDF de una plantilla
   */
  async getTemplatePDFBytes(templateId) {
    try {
      const response = await apiService.get(`${this.baseURL}/${templateId}/pdf`, {
        responseType: 'arraybuffer'
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error getting template PDF bytes:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al obtener el PDF' 
      };
    }
  }

  /**
   * Extraer campos del PDF de una plantilla
   */
  async extractTemplatePDFFields(templateId) {
    try {
      console.log(`🔍 Llamando a: ${this.baseURL}/${templateId}/extract-pdf-fields`);
      const response = await apiService.get(`${this.baseURL}/${templateId}/extract-pdf-fields`);
      console.log('📥 Respuesta completa del backend:', response);
      console.log('📦 response.data:', response.data);
      console.log('📊 Tipo de response.data:', typeof response.data);
      
      if (response.data && typeof response.data === 'object') {
        // Verificar si es un array o un objeto
        if (Array.isArray(response.data)) {
          console.warn('⚠️ La respuesta es un array, convirtiendo a objeto...');
          const dataObj = {};
          response.data.forEach((item, index) => {
            if (typeof item === 'object' && item !== null) {
              Object.assign(dataObj, item);
            } else {
              dataObj[`field_${index}`] = item;
            }
          });
          console.log('✅ Datos convertidos:', dataObj);
          return { success: true, data: dataObj };
        }
        
        // Verificar campos específicos
        const targetFields = ['Identificación', 'Correo electrónico_2', 'Teléfono_2'];
        console.log('🎯 Verificando campos en response.data:');
        targetFields.forEach(field => {
          if (field in response.data) {
            console.log(`   ✅ "${field}": "${response.data[field]}"`);
          } else {
            console.log(`   ❌ "${field}": NO ENCONTRADO`);
          }
        });
        
        return { success: true, data: response.data };
      } else {
        console.error('❌ response.data no es un objeto válido:', response.data);
        return { success: false, error: 'No se pudieron extraer los campos' };
      }
    } catch (error) {
      console.error('❌ Error extracting template PDF fields:', error);
      console.error('   Error response:', error.response);
      console.error('   Error data:', error.response?.data);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al extraer campos del PDF'
      };
    }
  }

  /**
   * Editar campos del PDF de una plantilla
   */
  async editTemplatePDF(templateId, fieldUpdates) {
    try {
      console.log(`📤 Enviando edición de PDF para plantilla ${templateId}:`, fieldUpdates);
      const response = await apiService.post(`${this.baseURL}/${templateId}/edit-pdf/`, fieldUpdates);
      console.log('📥 Respuesta del backend:', response.data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('❌ Error editing template PDF:', error);
      console.error('   Error response:', error.response);
      console.error('   Error data:', error.response?.data);
      return { 
        success: false, 
        error: error.response?.data?.detail || error.response?.data?.error || 'Error al editar el PDF' 
      };
    }
  }
}

export default new TemplateService();

