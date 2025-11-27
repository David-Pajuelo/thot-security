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
      setMessages: (messages) => {
        console.log('Store: setMessages llamado con:', messages);
        // Asegurar que messages siempre sea un array
        const safeMessages = Array.isArray(messages) ? messages : [];
        set({ messages: safeMessages });
      },
      addMessage: (message) => {
        console.log('Store: addMessage llamado con:', message);
        set((state) => ({
          messages: [...(Array.isArray(state.messages) ? state.messages : []), message]
        }));
      },
      setConversationId: (id) => {
        console.log('Store: setConversationId llamado con:', id);
        set({ conversationId: id });
      },
      setConnectionStatus: (status) => {
        console.log('Store: setConnectionStatus llamado con:', status);
        set({ connectionStatus: status });
      },
      setIsConnected: (connected) => {
        console.log('Store: setIsConnected llamado con:', connected);
        set({ isConnected: connected });
      },
      
      // Limpiar chat
      clearChat: () => set({
        messages: [],
        conversationId: null,
        isConnected: false,
        connectionStatus: 'Desconectado'
      }),
      
      // Limpiar chat completamente (incluyendo localStorage)
      clearChatCompletely: () => {
        // Limpiar localStorage del chat
        localStorage.removeItem('hps-chat-storage');
        set({
          messages: [],
          conversationId: null,
          isConnected: false,
          connectionStatus: 'Desconectado'
        });
      },
      
      // Cargar historial
      loadHistory: (historyMessages) => {
        console.log('Store: loadHistory llamado con:', historyMessages);
        set({ messages: historyMessages });
      },
      
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
