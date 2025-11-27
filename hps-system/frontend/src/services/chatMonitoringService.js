/**
 * Servicio para APIs de monitoreo del chat IA
 */
import apiUtils from './apiService';

const CHAT_API_BASE = '/api/hps/chat';

class ChatMonitoringService {
  /**
   * Obtener métricas en tiempo real del chat
   */
  async getRealtimeMetrics() {
    try {
      const response = await apiUtils.get(`${CHAT_API_BASE}/metrics/realtime`);
      return response.data;
    } catch (error) {
      console.error('Error obteniendo métricas en tiempo real:', error);
      throw error;
    }
  }

  /**
   * Obtener métricas históricas del chat
   */
  async getHistoricalMetrics(days = 7) {
    try {
      const response = await apiUtils.get(`${CHAT_API_BASE}/metrics/historical?days=${days}`);
      return response.data;
    } catch (error) {
      console.error('Error obteniendo métricas históricas:', error);
      throw error;
    }
  }

  /**
   * Obtener rendimiento del agente IA
   */
  async getAgentPerformance() {
    try {
      const response = await apiUtils.get(`${CHAT_API_BASE}/performance`);
      return response.data;
    } catch (error) {
      console.error('Error obteniendo rendimiento del agente:', error);
      throw error;
    }
  }

  /**
   * Obtener temas más frecuentes
   */
  async getTopTopics(limit = 10) {
    try {
      const response = await apiUtils.get(`${CHAT_API_BASE}/topics?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Error obteniendo temas frecuentes:', error);
      throw error;
    }
  }

  /**
   * Obtener análisis completo del chat
   */
  async getChatAnalytics(days = 7) {
    try {
      const response = await apiUtils.get(`${CHAT_API_BASE}/analytics?days=${days}`);
      return response.data;
    } catch (error) {
      console.error('Error obteniendo análisis del chat:', error);
      throw error;
    }
  }

  /**
   * Obtener conversaciones del usuario actual
   */
  async getUserConversations(limit = 50, offset = 0) {
    try {
      const response = await apiUtils.get(`${CHAT_API_BASE}/conversations?limit=${limit}&offset=${offset}`);
      return response.data;
    } catch (error) {
      console.error('Error obteniendo conversaciones del usuario:', error);
      throw error;
    }
  }

  /**
   * Obtener estadísticas de una conversación específica
   */
  async getConversationStats(conversationId) {
    try {
      const response = await apiUtils.get(`${CHAT_API_BASE}/conversations/${conversationId}/stats`);
      return response.data;
    } catch (error) {
      console.error('Error obteniendo estadísticas de conversación:', error);
      throw error;
    }
  }

  /**
   * Enviar calificación de satisfacción
   */
  async submitSatisfaction(conversationId, rating, feedback = null, category = null, isAnonymous = false) {
    try {
      const response = await apiUtils.post(`${CHAT_API_BASE}/satisfaction`, {
        conversation_id: conversationId,
        rating,
        feedback,
        category,
        is_anonymous: isAnonymous
      });
      return response.data;
    } catch (error) {
      console.error('Error enviando calificación de satisfacción:', error);
      throw error;
    }
  }

  /**
   * Completar una conversación
   */
  async completeConversation(conversationId, satisfactionRating = null, satisfactionFeedback = null) {
    try {
      const params = new URLSearchParams();
      if (satisfactionRating) params.append('satisfaction_rating', satisfactionRating);
      if (satisfactionFeedback) params.append('satisfaction_feedback', satisfactionFeedback);
      
      const response = await apiUtils.post(`${CHAT_API_BASE}/conversations/${conversationId}/complete?${params}`);
      return response.data;
    } catch (error) {
      console.error('Error completando conversación:', error);
      throw error;
    }
  }

  /**
   * Abandonar una conversación
   */
  async abandonConversation(conversationId) {
    try {
      const response = await apiUtils.post(`${CHAT_API_BASE}/conversations/${conversationId}/abandon`);
      return response.data;
    } catch (error) {
      console.error('Error abandonando conversación:', error);
      throw error;
    }
  }
}

// Crear instancia única del servicio
const chatMonitoringService = new ChatMonitoringService();

export default chatMonitoringService;





