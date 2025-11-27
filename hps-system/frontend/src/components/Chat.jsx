import React, { useState, useEffect, useRef } from 'react';
import { useAuthStore } from '../store/authStore';
import useChatStore from '../store/chatStore';
import config from '../config/api';
import websocketService from '../services/websocketService';
import { formatErrorForDisplay } from '../utils/errorHandler';

// Estilos CSS personalizados para las animaciones
const thinkingStyles = `
  @keyframes thinking-pulse {
    0%, 100% { opacity: 0.4; transform: scale(0.8); }
    50% { opacity: 1; transform: scale(1.2); }
  }
  
  @keyframes thinking-float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-4px); }
  }
  
  .thinking-dot {
    animation: thinking-pulse 1.5s ease-in-out infinite;
  }
  
  .thinking-dot:nth-child(1) { animation-delay: 0s; }
  .thinking-dot:nth-child(2) { animation-delay: 0.2s; }
  .thinking-dot:nth-child(3) { animation-delay: 0.4s; }
  
  .thinking-avatar {
    animation: thinking-float 2s ease-in-out infinite;
  }
`;

const Chat = () => {
  // Store de chat persistente
  const {
    messages,
    conversationId,
    isConnected,
    connectionStatus,
    setMessages,
    addMessage,
    setConversationId,
    setConnectionStatus,
    setIsConnected,
    clearChat
  } = useChatStore();

  // Estados locales
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [typingTimeout, setTypingTimeout] = useState(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [isResetting, setIsResetting] = useState(false);

  // Referencias
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const listenerId = useRef(null);
  const messageCountRef = useRef(0);

  // Store de autenticación
  const { user, token } = useAuthStore();

  // Scroll automático al último mensaje
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Inicializar conexión WebSocket global
  useEffect(() => {
    if (token && user) {
      const connectToWebSocket = async () => {
        try {
          // Solo conectar si no hay conexión activa
          if (!websocketService.isConnected()) {
            await websocketService.connect(token);
            setIsConnected(true);
            setConnectionStatus('Conectado');
          }
          
          // Configurar listener para mensajes (solo si no existe)
          if (!listenerId.current) {
            listenerId.current = `chat-${Date.now()}`;
            websocketService.addListener(listenerId.current, handleIncomingMessage);
          }
          
        } catch (error) {
          const errorMsg = formatErrorForDisplay(error);
          console.error('Error conectando WebSocket:', errorMsg);
          setConnectionStatus(`Error de conexión: ${errorMsg}`);
        }
      };
      
      connectToWebSocket();
      
      return () => {
        // Remover listener al desmontar
        if (listenerId.current) {
          websocketService.removeListener(listenerId.current);
          listenerId.current = null;
        }
      };
    }
  }, [token, user]);

  // Limpiar timeout al desmontar
  useEffect(() => {
    return () => {
      if (typingTimeout) {
        clearTimeout(typingTimeout);
      }
    };
  }, [typingTimeout]);

  // El historial se carga automáticamente desde el WebSocket
  // No necesitamos cargar desde el frontend

  const handleIncomingMessage = (data) => {
    messageCountRef.current += 1;
    console.log(`Mensaje #${messageCountRef.current} recibido en Chat:`, data);
    console.log('Listener ID actual:', listenerId.current);
    console.log('Tipo de mensaje:', data.type);
    
    // Manejar conversation_id
    if (data.type === 'conversation_id') {
      console.log('Recibido conversation_id:', data.conversation_id);
      setConversationId(data.conversation_id);
      return;
    }
    
    switch (data.type) {
      case 'system':
      case 'assistant':
        // Verificar si el mensaje ya existe para evitar duplicados
        const messageContent = data.message;
        const existingMessage = messages.find(msg => 
          msg.content === messageContent && 
          msg.type === data.type &&
          Math.abs(new Date(msg.timestamp) - new Date(data.timestamp)) < 1000 // Dentro de 1 segundo
        );
        
        if (existingMessage) {
          console.log('Mensaje duplicado detectado, ignorando:', messageContent);
          return;
        }
        
        // Mensaje del sistema o asistente
        addMessage({
          id: Date.now(),
          type: data.type,
          content: data.message,
          timestamp: new Date(data.timestamp),
          suggestions: data.suggestions || [],
          data: data.data || {},
          conversationId: data.conversation_id || conversationId
        });
        
        // Desactivar indicador de "pensando" y limpiar timeout
        setIsTyping(false);
        if (typingTimeout) {
          clearTimeout(typingTimeout);
          setTypingTimeout(null);
        }
        
        // Enfocar el input después de que el agente responda
        setTimeout(() => {
          inputRef.current?.focus();
        }, 100);
        break;
        
      case 'typing':
        // Indicador de escritura
        setIsTyping(data.is_typing);
        break;
        
      case 'error':
        // Mensaje de error
        const errorContent = formatErrorForDisplay(data.message || data.error || data);
        setMessages(prev => [...prev, {
          id: Date.now(),
          type: 'error',
          content: errorContent,
          timestamp: new Date(),
        }]);
        
        // Desactivar indicador de "pensando" y limpiar timeout
        setIsTyping(false);
        if (typingTimeout) {
          clearTimeout(typingTimeout);
          setTypingTimeout(null);
        }
        
        // Enfocar el input después de un error
        setTimeout(() => {
          inputRef.current?.focus();
        }, 100);
        break;
        
      default:
        console.warn('Tipo de mensaje no reconocido:', data.type);
    }
  };

  const sendMessage = () => {
    if (!inputMessage.trim() || !isConnected) {
      console.log('No se puede enviar mensaje:', { 
        hasMessage: !!inputMessage.trim(), 
        isConnected 
      });
      return;
    }
    
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date(),
      conversationId: conversationId
    };
    
    console.log('Enviando mensaje:', userMessage);
    
    // Agregar mensaje del usuario a la lista
    addMessage(userMessage);
    
    // Activar indicador de "pensando"
    setIsTyping(true);
    
    // Timeout de seguridad: si no hay respuesta en 30 segundos, desactivar
    const timeout = setTimeout(() => {
      setIsTyping(false);
      console.warn('Timeout: No se recibió respuesta en 30 segundos');
    }, 30000);
    
    setTypingTimeout(timeout);
    
    // Enviar mensaje por WebSocket
    if (websocketService.isConnected()) {
      const messageData = {
        message: inputMessage.trim(),
        timestamp: new Date().toISOString(),
        context: {
          user_id: user?.id || 'unknown',
          email: user?.email || 'unknown',
          role: user?.role || 'member',
          team_id: user?.team_id || null,
          team_name: user?.team_name || null
        }
      };
      
      console.log('Enviando por WebSocket:', messageData);
      websocketService.sendMessage(messageData);
    } else {
      console.error('WebSocket no está conectado');
    }
    
    // Limpiar input
    setInputMessage('');
    
    // Enfocar input
    inputRef.current?.focus();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    // Crear el mensaje del usuario directamente
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: suggestion.trim(),
      timestamp: new Date(),
      conversationId: conversationId
    };
    
    console.log('Enviando sugerencia:', userMessage);
    
    // Agregar mensaje del usuario a la lista
    addMessage(userMessage);
    
    // Limpiar el input
    setInputMessage('');
    
    // Activar indicador de "pensando"
    setIsTyping(true);
    
    // Timeout de seguridad: si no hay respuesta en 30 segundos, desactivar
    const timeout = setTimeout(() => {
      setIsTyping(false);
      console.warn('Timeout: No se recibió respuesta en 30 segundos');
    }, 30000);
    
    setTypingTimeout(timeout);
    
    // Enviar mensaje por WebSocket
    if (websocketService.isConnected()) {
      const messageData = {
        message: suggestion.trim(),
        timestamp: new Date().toISOString(),
        context: {
          user_id: user?.id || 'unknown',
          email: user?.email || 'unknown',
          role: user?.role || 'member',
          team_id: user?.team_id || null,
          team_name: user?.team_name || null
        }
      };
      
      console.log('Enviando por WebSocket:', messageData);
      websocketService.sendMessage(messageData);
    } else {
      console.error('WebSocket no está conectado');
    }
  };

  const handleResetChat = async () => {
    if (isResetting) return; // Evitar múltiples clicks
    
    try {
      setIsResetting(true);
      console.log('🔄 Reseteando conversación...');
      console.log('Token:', token ? 'Presente' : 'Ausente');
      
      // Llamar al endpoint de reset
      const response = await fetch(`${config.API_BASE_URL}/api/hps/chat/conversations/reset/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Conversación reseteada:', data);
        
        // Limpiar el chat actual
        clearChat();
        
        // Reconectar WebSocket para obtener nueva conversación
        websocketService.disconnect();
        
        // Reconectar después de un breve delay
        setTimeout(async () => {
          try {
            await websocketService.connect(token);
            setIsConnected(true);
            setConnectionStatus('Conectado');
            
            // Reconfigurar listener
            if (listenerId.current) {
              websocketService.removeListener(listenerId.current);
            }
            listenerId.current = `chat-${Date.now()}`;
            websocketService.addListener(listenerId.current, handleIncomingMessage);
          } catch (error) {
            const errorMsg = formatErrorForDisplay(error);
            console.error('Error reconectando WebSocket:', errorMsg);
            setConnectionStatus(`Error de reconexión: ${errorMsg}`);
          }
        }, 1000);
        
        console.log('✅ Chat reseteado exitosamente');
      } else {
        const errorText = await response.text();
        console.error('❌ Error reseteando chat:', response.status, errorText);
        addMessage({
          id: Date.now(),
          type: 'error',
          content: `❌ Error al resetear la conversación (${response.status}). Inténtalo de nuevo.`,
          timestamp: new Date(),
          conversationId: null
        });
      }
    } catch (error) {
      const errorMsg = formatErrorForDisplay(error);
      console.error('❌ Error reseteando chat:', errorMsg);
      addMessage({
        id: Date.now(),
        type: 'error',
        content: `❌ Error al resetear la conversación: ${errorMsg}`,
        timestamp: new Date(),
        conversationId: null
      });
    } finally {
      setIsResetting(false);
    }
  };

  // Función para detectar y renderizar URLs de formularios HPS
  const renderHPSFormLink = (content) => {
    // Patrón para detectar URLs de formularios HPS
    const hpsUrlPattern = /(https?:\/\/[^\s]+hps-form\?[^\s]+)/g;
    const parts = content.split(hpsUrlPattern);
    
    return parts.map((part, index) => {
      if (hpsUrlPattern.test(part)) {
        // Extraer email de la URL para mostrar en el botón
        const emailMatch = part.match(/email=([^&]+)/);
        const email = emailMatch ? emailMatch[1] : 'usuario';
        
        return (
          <div key={index} className="mt-3">
            <a
              href={part}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white text-sm font-medium rounded-lg hover:from-green-600 hover:to-emerald-700 transform hover:scale-105 transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              📋 Abrir formulario HPS para {email}
            </a>
          </div>
        );
      }
      return part;
    });
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getMessageIcon = (type) => {
    switch (type) {
      case 'user':
        return '👤';
      case 'assistant':
        return '🤖';
      case 'system':
        return '⚙️';
      case 'error':
        return '❌';
      default:
        return '💬';
    }
  };

  const getMessageBgColor = (type) => {
    switch (type) {
      case 'user':
        return 'bg-blue-500 text-white ml-auto';
      case 'assistant':
        return 'bg-gray-100 text-gray-800';
      case 'system':
        return 'bg-green-100 text-green-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <>
      <style>{thinkingStyles}</style>
      <div className="flex flex-col h-full bg-white rounded-lg shadow-lg w-full">
      {/* Header del Chat */}
      <div className="flex items-center justify-between p-3 sm:p-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-blue-50 rounded-t-lg">
        <div className="flex items-center space-x-3">
          <div className="w-3 h-3 rounded-full flex-shrink-0 shadow-sm" 
               style={{ backgroundColor: isConnected ? '#10B981' : '#EF4444' }}></div>
          <div>
            <h3 className="text-base sm:text-lg font-semibold text-gray-900">Asistente IA</h3>
            <p className={`text-xs sm:text-sm font-medium ${
              isConnected ? 'text-green-600' : 'text-red-600'
            }`}>
              {connectionStatus}
            </p>
          </div>
        </div>
        
        {/* Botón Reset Chat */}
        <button
          onClick={handleResetChat}
          disabled={isResetting}
          className={`flex items-center px-3 py-2 text-sm font-medium text-white rounded-lg transform transition-all duration-200 shadow-md hover:shadow-lg ${
            isResetting 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 hover:scale-105'
          }`}
          title={isResetting ? "Reseteando conversación..." : "Resetear conversación (archivar actual y crear nueva)"}
        >
          {isResetting ? (
            <>
              <svg className="w-4 h-4 mr-1 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Reseteando...
            </>
          ) : (
            <>
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Reset
            </>
          )}
        </button>
      </div>

      {/* Área de Mensajes */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {Array.isArray(messages) && messages.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-4">🤖</div>
            <p className="text-sm">Escribe un mensaje para comenzar la conversación</p>
          </div>
        )}

        {Array.isArray(messages) && messages.map((message) => (
          <div key={message.id} className="flex flex-col space-y-1">
            <div className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${getMessageBgColor(message.type)}`}>
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-sm">{getMessageIcon(message.type)}</span>
                  <span className="text-xs opacity-75">{formatTime(message.timestamp)}</span>
                </div>
                <div className="text-sm whitespace-pre-wrap">
                  {renderHPSFormLink(message.content)}
                </div>
              </div>
            </div>
            
            {/* Sugerencias */}
            {message.suggestions && message.suggestions.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2 ml-4">
                {message.suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="text-xs px-3 py-1 bg-blue-50 text-blue-600 rounded-full hover:bg-blue-100 hover:shadow-sm active:bg-blue-200 transition-all duration-150 cursor-pointer border border-blue-200"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}

        {/* Indicador de "pensando" */}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 px-4 py-3 rounded-lg max-w-xs shadow-sm">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full flex items-center justify-center thinking-avatar">
                  <span className="text-lg">🤖</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-medium text-blue-800">IA pensando...</span>
                  <div className="flex space-x-1 mt-1">
                    <div className="w-2 h-2 bg-blue-500 rounded-full thinking-dot"></div>
                    <div className="w-2 h-2 bg-blue-500 rounded-full thinking-dot"></div>
                    <div className="w-2 h-2 bg-blue-500 rounded-full thinking-dot"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input de Mensaje */}
      <div className="border-t border-gray-200 p-3 sm:p-4 bg-gray-50 rounded-b-lg">
        <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
          <textarea
            ref={inputRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              !isConnected ? "Conectando..." :
              isTyping ? "IA procesando mensaje..." :
              "Escribe tu mensaje..."
            }
            disabled={!isConnected || isTyping}
            className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed text-sm sm:text-base"
            rows="1"
            style={{ minHeight: '40px', maxHeight: '120px' }}
          />
          <button
            onClick={sendMessage}
            disabled={!isConnected || !inputMessage.trim() || isTyping}
            className={`w-full sm:w-auto px-3 sm:px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center ${
              isTyping 
                ? 'bg-gray-400 text-gray-600' 
                : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
          >
            {isTyping ? (
              <>
                <div className="w-4 h-4 sm:w-5 sm:h-5 border-2 border-gray-600 border-t-transparent rounded-full animate-spin"></div>
                <span className="ml-2 text-xs sm:text-sm">Procesando...</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                <span className="ml-1 sm:hidden">Enviar</span>
              </>
            )}
          </button>
        </div>
        
        {!isConnected && (
          <div className="mt-2 flex flex-col sm:flex-row items-start sm:items-center justify-between space-y-2 sm:space-y-0">
            <p className="text-xs text-red-500">
              Estado: {typeof connectionStatus === 'string' ? connectionStatus : formatErrorForDisplay(connectionStatus)}
              {reconnectAttempts > 0 && reconnectAttempts < 5 && (
                <span className="ml-1">(Intento {reconnectAttempts}/5)</span>
              )}
            </p>
            {reconnectAttempts >= 5 && (
              <button
                onClick={async () => {
                  setReconnectAttempts(0);
                  try {
                    await websocketService.connect(token);
                    setIsConnected(true);
                    setConnectionStatus('Conectado');
                    
                    // Reconfigurar listener
                    if (listenerId.current) {
                      websocketService.removeListener(listenerId.current);
                    }
                    listenerId.current = `chat-${Date.now()}`;
                    websocketService.addListener(listenerId.current, handleIncomingMessage);
                  } catch (error) {
                    const errorMsg = formatErrorForDisplay(error);
                    console.error('Error reconectando:', errorMsg);
                    setConnectionStatus(`Error de reconexión: ${errorMsg}`);
                  }
                }}
                className="text-xs bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600 transition-colors"
              >
                Reconectar
              </button>
            )}
          </div>
        )}
      </div>
      </div>
    </>
  );
};

export default Chat;