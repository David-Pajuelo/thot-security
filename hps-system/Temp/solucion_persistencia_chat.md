# 🔧 Solución: Persistencia del Estado del Chat

## 🎯 **Problema Identificado**

El chat se reinicia cada vez que el usuario navega entre páginas porque:

1. **No hay persistencia del estado** - Los mensajes se almacenan solo en el estado local del componente
2. **La conexión WebSocket se cierra** cuando cambias de página
3. **No hay almacenamiento del conversation_id** en el frontend
4. **El historial se pierde** al navegar

## 💡 **Solución Propuesta**

Implementar un **store de chat persistente** que mantenga:
- Mensajes del chat
- Conversation ID
- Estado de conexión
- Historial de conversaciones

### **Implementación:**

#### **1. Crear Store de Chat Persistente**

#### **Archivo**: `frontend/src/store/chatStore.js`

```javascript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useChatStore = create(
  persist(
    (set, get) => ({
      // Estado del chat
      messages: [],
      conversationId: null,
      isConnected: false,
      connectionStatus: 'Desconectado',
      
      // Acciones
      setMessages: (messages) => set({ messages }),
      addMessage: (message) => set((state) => ({
        messages: [...state.messages, message]
      })),
      setConversationId: (id) => set({ conversationId: id }),
      setConnectionStatus: (status) => set({ connectionStatus: status }),
      setIsConnected: (connected) => set({ isConnected: connected }),
      
      // Limpiar chat
      clearChat: () => set({
        messages: [],
        conversationId: null,
        isConnected: false,
        connectionStatus: 'Desconectado'
      }),
      
      // Cargar historial
      loadHistory: (historyMessages) => set({ messages: historyMessages }),
      
      // Obtener mensajes por conversation_id
      getMessagesByConversation: (conversationId) => {
        const state = get();
        return state.messages.filter(msg => msg.conversationId === conversationId);
      }
    }),
    {
      name: 'hps-chat-storage',
      partialize: (state) => ({
        messages: state.messages,
        conversationId: state.conversationId
      })
    }
  )
);

export default useChatStore;
```

#### **2. Modificar Componente Chat**

#### **Archivo**: `frontend/src/components/Chat.jsx`

```javascript
import React, { useState, useEffect, useRef } from 'react';
import { useAuthStore } from '../store/authStore';
import useChatStore from '../store/chatStore';

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
    clearChat,
    loadHistory
  } = useChatStore();

  // Estados locales
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [typingTimeout, setTypingTimeout] = useState(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // Referencias
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Store de autenticación
  const { user, token } = useAuthStore();

  // Inicializar conexión WebSocket
  useEffect(() => {
    if (token && user) {
      const timer = setTimeout(() => {
        connectWebSocket();
      }, 100);
      
      return () => {
        clearTimeout(timer);
        if (wsRef.current) {
          wsRef.current.close();
        }
      };
    }
  }, [token, user]);

  // Cargar historial cuando se establece conversationId
  useEffect(() => {
    if (conversationId && messages.length === 0) {
      loadConversationHistory();
    }
  }, [conversationId]);

  const loadConversationHistory = async () => {
    try {
      const response = await fetch(
        `/api/v1/chat/conversations/${conversationId}/messages`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        const historyMessages = data.messages.map(msg => ({
          id: msg.id,
          type: msg.message_type,
          content: msg.content,
          timestamp: new Date(msg.created_at),
          suggestions: msg.suggestions || [],
          conversationId: conversationId
        }));
        
        loadHistory(historyMessages);
      }
    } catch (error) {
      console.error('Error cargando historial:', error);
    }
  };

  const connectWebSocket = () => {
    // ... lógica de conexión existente ...
    
    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleIncomingMessage(data);
      } catch (error) {
        console.error('Error parseando mensaje:', error);
      }
    };
  };

  const handleIncomingMessage = (data) => {
    console.log('Mensaje recibido:', data);
    
    const message = {
      id: Date.now(),
      type: data.type,
      content: data.message,
      timestamp: new Date(data.timestamp),
      suggestions: data.suggestions || [],
      conversationId: conversationId
    };
    
    addMessage(message);
    
    // ... resto de la lógica existente ...
  };

  const sendMessage = () => {
    if (!inputMessage.trim() || !isConnected) {
      return;
    }
    
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date(),
      conversationId: conversationId
    };
    
    addMessage(userMessage);
    
    // ... resto de la lógica existente ...
  };

  // ... resto del componente existente ...
};
```

#### **3. Modificar WebSocket Router para Persistir Conversation ID**

#### **Archivo**: `agente-ia/src/websocket/router.py`

```python
async def send_conversation_history(websocket: WebSocket, conversation_id: str, user: dict, token: str):
    """Cargar y enviar historial de conversación existente"""
    try:
        # Obtener historial de mensajes de la conversación
        messages = await get_conversation_messages(conversation_id, token)
        
        if messages:
            logger.info(f"📜 Cargando {len(messages)} mensajes del historial")
            
            # Enviar conversation_id al frontend
            await websocket.send_text(json.dumps({
                "type": "conversation_id",
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }))
            
            # Enviar cada mensaje del historial
            for message in messages:
                await websocket.send_text(json.dumps({
                    "type": message.get("message_type", "assistant"),
                    "message": message.get("content", ""),
                    "timestamp": message.get("created_at", datetime.now().isoformat()),
                    "suggestions": message.get("suggestions", []),
                    "conversation_id": conversation_id
                }))
            
            logger.info(f"✅ Historial cargado exitosamente")
        else:
            # Si no hay historial, enviar mensaje de bienvenida
            logger.info("📜 No hay historial disponible, enviando mensaje de bienvenida")
            await send_welcome_message(websocket, user)
            
    except Exception as e:
        logger.error(f"❌ Error cargando historial: {e}")
        # En caso de error, enviar mensaje de bienvenida
        await send_welcome_message(websocket, user)
```

#### **4. Manejar Conversation ID en el Frontend**

```javascript
const handleIncomingMessage = (data) => {
  console.log('Mensaje recibido:', data);
  
  // Manejar conversation_id
  if (data.type === 'conversation_id') {
    setConversationId(data.conversation_id);
    return;
  }
  
  const message = {
    id: Date.now(),
    type: data.type,
    content: data.message,
    timestamp: new Date(data.timestamp),
    suggestions: data.suggestions || [],
    conversationId: data.conversation_id || conversationId
  };
  
  addMessage(message);
  
  // ... resto de la lógica existente ...
};
```

## 🎯 **Flujo de Trabajo Actualizado**

### **Primera Conexión:**
1. Usuario se conecta al chat
2. No hay conversación activa
3. Se crea nueva conversación
4. Se envía mensaje de bienvenida
5. Se almacena conversation_id en el store

### **Navegación y Reconexión:**
1. Usuario navega a otra página
2. Chat se desmonta pero el estado persiste
3. Usuario vuelve al chat
4. Se restaura el estado del store
5. Se reconecta WebSocket con conversation_id existente
6. Se carga el historial automáticamente

### **Conversación Existente:**
1. Usuario se conecta al chat
2. Hay conversación activa
3. Se carga el historial desde el store
4. Se muestra la conversación completa

## 📊 **Ventajas de la Solución**

### **Para el Usuario:**
- ✅ **Persistencia total** - El chat mantiene su estado al navegar
- ✅ **Historial completo** - No se pierden mensajes anteriores
- ✅ **Experiencia fluida** - Continúa donde lo dejó
- ✅ **Reconexión automática** - Se reconecta automáticamente

### **Para el Sistema:**
- ✅ **Eficiente** - No duplica mensajes
- ✅ **Robusto** - Maneja desconexiones y reconexiones
- ✅ **Escalable** - Funciona con múltiples conversaciones
- ✅ **Persistente** - Estado se mantiene entre sesiones

## 🚀 **Implementación Paso a Paso**

### **Paso 1: Crear store de chat persistente**
- Implementar `useChatStore` con Zustand
- Configurar persistencia con localStorage

### **Paso 2: Modificar componente Chat**
- Integrar store persistente
- Manejar conversation_id
- Cargar historial automáticamente

### **Paso 3: Actualizar WebSocket router**
- Enviar conversation_id al frontend
- Mejorar manejo de historial

### **Paso 4: Probar funcionalidad**
- Probar navegación entre páginas
- Verificar persistencia del estado
- Confirmar carga de historial

## 🎉 **Resultado Final**

- **Navegación fluida** - El chat mantiene su estado
- **Historial persistente** - No se pierden mensajes
- **Reconexión automática** - Se reconecta al volver
- **Experiencia consistente** - Para todos los usuarios

¿Quieres que implemente esta solución para la persistencia del chat?



