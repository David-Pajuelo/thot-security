/**
 * Servicio global de WebSocket para mantener una conexión persistente
 */

class WebSocketService {
  constructor() {
    this.ws = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.isConnecting = false;
  }

  connect(token) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket ya está conectado, reutilizando conexión existente');
      return Promise.resolve();
    }

    if (this.isConnecting) {
      console.log('Ya hay una conexión en progreso, esperando...');
      return Promise.resolve();
    }
    
    // Cerrar conexión anterior si existe
    if (this.ws) {
      console.log('Cerrando conexión anterior antes de crear nueva');
      this.ws.close(1000, 'Nueva conexión');
      this.ws = null;
    }

    return new Promise((resolve, reject) => {
      this.isConnecting = true;
      
      try {
        const wsHost = process.env.REACT_APP_AGENTE_IA_WS_URL || 'ws://localhost:8080';
        const wsUrl = `${wsHost}/ws/chat?token=${token}`;
        
        console.log('Conectando a WebSocket:', wsUrl);
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
          console.log('WebSocket conectado globalmente - ID:', this.ws?.url);
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.notifyListeners(data);
          } catch (error) {
            console.error('Error parseando mensaje WebSocket:', error);
          }
        };
        
        this.ws.onclose = (event) => {
          console.log('WebSocket cerrado:', event.code, event.reason);
          this.isConnecting = false;
          
          // Archivar conversación activa si existe
          this.archiveActiveConversation();
          
          // Reconexión automática solo si no fue cierre intencional
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts), 10000);
            setTimeout(() => {
              console.log(`Intentando reconectar... (intento ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
              this.reconnectAttempts++;
              this.connect(token);
            }, delay);
          }
        };
        
        this.ws.onerror = (error) => {
          console.error('Error de WebSocket:', error);
          this.isConnecting = false;
          // Convertir Event a Error con mensaje legible
          const errorMessage = error instanceof Event 
            ? 'Error de conexión WebSocket. Por favor, intenta de nuevo.'
            : (error?.message || String(error) || 'Error de conexión WebSocket');
          const wsError = new Error(errorMessage);
          wsError.originalError = error;
          reject(wsError);
        };
        
      } catch (error) {
        this.isConnecting = false;
        // Asegurar que el error tenga un mensaje legible
        if (error instanceof Event) {
          const wsError = new Error('Error de conexión WebSocket. Por favor, intenta de nuevo.');
          wsError.originalError = error;
          reject(wsError);
        } else if (!error.message && typeof error === 'object') {
          const wsError = new Error(error.toString && error.toString() !== '[object Object]' 
            ? error.toString() 
            : 'Error de conexión WebSocket');
          wsError.originalError = error;
          reject(wsError);
        } else {
          reject(error);
        }
      }
    });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Desconexión intencional');
      this.ws = null;
    }
    this.listeners.clear();
  }

  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket no está conectado');
    }
  }

  addListener(id, callback) {
    console.log(`Agregando listener: ${id}`);
    console.log(`Listeners actuales:`, Array.from(this.listeners.keys()));
    this.listeners.set(id, callback);
    console.log(`Total listeners: ${this.listeners.size}`);
  }

  removeListener(id) {
    console.log(`Removiendo listener: ${id}`);
    this.listeners.delete(id);
    console.log(`Total listeners después de remover: ${this.listeners.size}`);
  }

  notifyListeners(data) {
    console.log(`Notificando a ${this.listeners.size} listeners:`, Array.from(this.listeners.keys()));
    this.listeners.forEach((callback, id) => {
      try {
        console.log(`Ejecutando listener: ${id}`);
        callback(data);
      } catch (error) {
        // Formatear el error antes de loguearlo
        const errorMsg = error instanceof Error ? error.message : String(error);
        console.error('Error en listener WebSocket:', errorMsg, error);
      }
    });
  }

  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  async archiveActiveConversation() {
    try {
      // Obtener token del localStorage (compartido con CryptoTrace)
      const token = localStorage.getItem('accessToken') || localStorage.getItem('hps_token');
      if (!token) {
        console.log('No hay token para archivar conversación');
        return;
      }

      // Llamar al endpoint de archivado
      const response = await fetch('/api/v1/chat/conversations/archive-active', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        console.log('Conversación archivada automáticamente');
      } else {
        console.error('Error archivando conversación:', response.status);
      }
    } catch (error) {
      console.error('Error en archivado automático:', error);
    }
  }

  // Método para desconexión intencional (logout)
  async disconnectIntentionally() {
    await this.archiveActiveConversation();
    this.disconnect();
  }
}

// Instancia singleton
const websocketService = new WebSocketService();
export default websocketService;
