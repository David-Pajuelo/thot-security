import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../store/authStore';
import chatMonitoringService from '../services/chatMonitoringService';
import {
  ChatBubbleLeftRightIcon,
  UserGroupIcon,
  ClockIcon,
  ChartBarIcon,
  EyeIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  CpuChipIcon,
  HeartIcon,
  LightBulbIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const ChatMonitoringPage = () => {
  const { canManageUsers } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [chatData, setChatData] = useState({
    realTimeStats: null,
    recentConversations: [],
    topQuestions: [],
    userActivity: [],
    agentPerformance: null,
    systemHealth: null
  });
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [showConversationModal, setShowConversationModal] = useState(false);
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [showAllConversations, setShowAllConversations] = useState(false);
  const [allConversations, setAllConversations] = useState([]);
  const [selectedUser, setSelectedUser] = useState('');
  const [allUsers, setAllUsers] = useState([]);
  const [userSearchTerm, setUserSearchTerm] = useState('');
  const [showUserModal, setShowUserModal] = useState(false);
  const [showAllConversationsModal, setShowAllConversationsModal] = useState(false);

  useEffect(() => {
    if (canManageUsers) {
      loadChatData();
      
      // Auto-refresh cada 30 segundos si está habilitado
      const interval = autoRefresh ? setInterval(loadChatData, 30000) : null;
      return () => {
        if (interval) clearInterval(interval);
      };
    }
  }, [canManageUsers, selectedTimeRange, autoRefresh]);

  // Prevenir scroll del body cuando el modal esté abierto
  useEffect(() => {
    if (showConversationModal) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    
    // Cleanup al desmontar
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [showConversationModal]);

  // Prevenir scroll del body cuando los modales estén abiertos
  useEffect(() => {
    if (showUserModal || showAllConversationsModal) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    
    // Cleanup al desmontar
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [showUserModal, showAllConversationsModal]);

  const loadChatData = async () => {
    setLoading(true);
    try {
      // Cargar datos reales del chat
      const analytics = await chatMonitoringService.getChatAnalytics(7);
      
      setChatData({
        realTimeStats: analytics.realtime_metrics,
        recentConversations: analytics.recent_conversations || [],
        topQuestions: analytics.top_topics || [],
        userActivity: analytics.historical_metrics || [],
        agentPerformance: analytics.agent_performance,
        systemHealth: {
          score: analytics.realtime_metrics?.system_health_score || 0,
          status: analytics.realtime_metrics?.system_health_score > 80 ? 'healthy' : 
                  analytics.realtime_metrics?.system_health_score > 60 ? 'warning' : 'critical'
        }
      });
    } catch (error) {
      console.error('Error cargando datos del chat:', error);
      // En caso de error, mostrar datos vacíos
      setChatData({
        realTimeStats: null,
        recentConversations: [],
        topQuestions: [],
        userActivity: [],
        agentPerformance: null,
        systemHealth: null
      });
    } finally {
      setLoading(false);
    }
  };

  const loadAllConversations = async () => {
    try {
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';
      const token = localStorage.getItem('hps_token');
      
      // Cargar todas las conversaciones usando el nuevo endpoint
      // TODO: Implementar endpoint en Django si es necesario
      const response = await fetch(`${API_BASE_URL}/api/hps/chat/conversations/all/?limit=100`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const conversations = await response.json();
        setAllConversations(conversations);
        
        // Extraer usuarios únicos
        const users = [...new Set(conversations.map(conv => conv.user_id))];
        setAllUsers(users);
      } else {
        console.error('Error cargando todas las conversaciones:', response.status);
        setAllConversations([]);
      }
    } catch (error) {
      console.error('Error cargando todas las conversaciones:', error);
      setAllConversations([]);
    }
  };

  const loadUsers = async () => {
    try {
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';
      const token = localStorage.getItem('hps_token');
      
      // Cargar usuarios desde el endpoint de perfiles HPS
      // TODO: Implementar endpoint de usuarios en Django si es necesario
      const response = await fetch(`${API_BASE_URL}/api/hps/user/profiles/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const users = await response.json();
        setAllUsers(Array.isArray(users) ? users : []);
      } else {
        console.error('Error cargando usuarios:', response.status);
        setAllUsers([]);
      }
    } catch (error) {
      console.error('Error cargando usuarios:', error);
      setAllUsers([]);
    }
  };

  const viewConversationDetails = async (conversationId) => {
    try {
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';
      const token = localStorage.getItem('hps_token');
      
      console.log('🔍 Token:', token ? `${token.substring(0, 20)}...` : 'No token');
      console.log('🔍 URL:', `${API_BASE_URL}/api/hps/chat/conversations/${conversationId}/full/`);
      
      // TODO: Implementar endpoint en Django si es necesario
      const response = await fetch(`${API_BASE_URL}/api/hps/chat/conversations/${conversationId}/full/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('🔍 Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        setSelectedConversation(data.conversation);
        setShowConversationModal(true);
        
        // Scroll automático al final después de un pequeño delay para que se renderice
        setTimeout(() => {
          const messagesContainer = document.getElementById('messages-container');
          if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
          }
        }, 100);
      } else if (response.status === 401) {
        console.error('❌ Error 401: Token expirado o inválido');
        alert('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.');
        // Opcional: redirigir al login
        // window.location.href = '/login';
      } else {
        const errorText = await response.text();
        console.error('❌ Error obteniendo detalles:', response.status, errorText);
        alert(`Error ${response.status}: ${errorText}`);
      }
    } catch (error) {
      console.error('❌ Error obteniendo detalles de la conversación:', error);
      alert('Error de conexión. Verifica que el servidor esté funcionando.');
    }
  };




  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('es-ES');
  };

  const handleShowAllConversations = async () => {
    setShowAllConversationsModal(true);
    await loadAllConversations();
    await loadUsers();
  };

  const handleBackToRecent = () => {
    setShowAllConversationsModal(false);
    setSelectedUser('');
    setAllConversations([]);
  };

  const getFilteredConversations = () => {
    return chatData.recentConversations?.filter(conversation => conversation.total_messages > 0) || [];
  };

  const getModalFilteredConversations = () => {
    let filtered = allConversations.filter(conversation => conversation.total_messages > 0);
    
    if (selectedUser) {
      filtered = filtered.filter(conversation => conversation.user_id === selectedUser);
    }
    
    return filtered;
  };

  const getUserName = (userId) => {
    if (!Array.isArray(allUsers)) return `Usuario ${userId}`;
    const user = allUsers.find(u => u.id === userId);
    return user ? `${user.first_name} ${user.last_name}` : `Usuario ${userId}`;
  };

  const getFilteredUsers = () => {
    if (!Array.isArray(allUsers)) return [];
    return allUsers.filter(user => {
      const fullName = `${user.first_name} ${user.last_name}`.toLowerCase();
      const email = user.email.toLowerCase();
      const searchTerm = userSearchTerm.toLowerCase();
      return fullName.includes(searchTerm) || email.includes(searchTerm);
    });
  };

  const handleUserSelect = (userId) => {
    setSelectedUser(userId);
    setUserSearchTerm('');
    setShowUserModal(false);
  };

  const handleUserSearchChange = (e) => {
    setUserSearchTerm(e.target.value);
  };

  const handleOpenUserModal = () => {
    setShowUserModal(true);
    setUserSearchTerm('');
  };

  const getSelectedUserName = () => {
    if (!selectedUser) return '';
    const user = allUsers.find(u => u.id === selectedUser);
    return user ? `${user.first_name} ${user.last_name}` : '';
  };


  if (!canManageUsers) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="h-16 w-16 text-red-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Acceso Denegado</h1>
          <p className="text-gray-600">No tienes permisos para acceder al monitoreo del chat</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Cargando datos del chat...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <ChatBubbleLeftRightIcon className="h-8 w-8 mr-3 text-blue-600" />
                Monitoreo del Chat IA
              </h1>
              <p className="mt-2 text-gray-600">
                Observabilidad y análisis del agente de inteligencia artificial
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="autoRefresh"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="autoRefresh" className="text-sm text-gray-600">
                  Auto-actualizar
                </label>
              </div>
              <select
                value={selectedTimeRange}
                onChange={(e) => setSelectedTimeRange(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="1h">Última hora</option>
                <option value="24h">Últimas 24 horas</option>
                <option value="7d">Últimos 7 días</option>
                <option value="30d">Últimos 30 días</option>
              </select>
              <button
                onClick={loadChatData}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center"
              >
                <ArrowPathIcon className="h-5 w-5 mr-2" />
                Actualizar
              </button>
              <button
                onClick={() => window.history.back()}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md"
              >
                ← Volver al Dashboard
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="w-full px-4 sm:px-6 lg:px-8 py-8">
        {/* Estadísticas en tiempo real */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <UserGroupIcon className="h-8 w-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Usuarios Activos (24h)</p>
                <p className="text-2xl font-bold text-gray-900">
                  {chatData.realTimeStats?.active_users_24h || 0}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <ChatBubbleLeftRightIcon className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Mensajes Hoy</p>
                <p className="text-2xl font-bold text-gray-900">
                  {chatData.realTimeStats?.total_messages_today || 0}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <ClockIcon className="h-8 w-8 text-yellow-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Tiempo Respuesta</p>
                <p className="text-2xl font-bold text-gray-900">
                  {chatData.realTimeStats?.avg_response_time_ms ? 
                    (chatData.realTimeStats.avg_response_time_ms / 1000).toFixed(1) + 's' : '0s'}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <HeartIcon className="h-8 w-8 text-red-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Satisfacción</p>
                <p className="text-2xl font-bold text-gray-900">
                  {chatData.realTimeStats?.avg_satisfaction_rating ? 
                    (chatData.realTimeStats.avg_satisfaction_rating * 20).toFixed(0) + '%' : '0%'}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Conversaciones recientes */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  <EyeIcon className="h-5 w-5 mr-2" />
                  Conversaciones Recientes
                </h3>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleShowAllConversations}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-md text-sm font-medium"
                  >
                    Ver Todas
                  </button>
                </div>
              </div>
            </div>
            <div className="divide-y divide-gray-200">
              {getFilteredConversations().length > 0 ? (
                getFilteredConversations().map((conversation, index) => (
                  <div key={conversation.id} className={`p-3 hover:bg-gray-50 transition-colors duration-200 ${index > 0 ? 'border-t border-gray-100' : ''}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        {/* Header con usuario y estado */}
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center space-x-2">
                            <div className="flex-shrink-0">
                              <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                                <span className="text-sm font-medium text-blue-600">
                                  {conversation.user?.first_name ? conversation.user.first_name.charAt(0).toUpperCase() : 'U'}
                                </span>
                              </div>
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-gray-900">
                                {showAllConversations 
                                  ? getUserName(conversation.user_id)
                                  : (conversation.user?.first_name && conversation.user?.last_name 
                                    ? `${conversation.user.first_name} ${conversation.user.last_name}`
                                    : conversation.user?.email || 'Usuario')
                                }
                              </p>
                              <p className="text-xs text-gray-500">
                                {formatTime(conversation.created_at)}
                              </p>
                            </div>
                          </div>
                          
                          {/* Estado de la conversación */}
                          <div className="flex items-center space-x-2">
                            {conversation.status === 'completed' ? (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                <CheckCircleIcon className="h-3 w-3 mr-1" />
                                Completada
                              </span>
                            ) : conversation.status === 'active' ? (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                <div className="h-2 w-2 rounded-full bg-blue-500 animate-pulse mr-1"></div>
                                Activa
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                <XCircleIcon className="h-3 w-3 mr-1" />
                                Cerrada
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Footer con métricas */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4 text-xs text-gray-500">
                            <span className="flex items-center">
                              <ChatBubbleLeftRightIcon className="h-3 w-3 mr-1" />
                              {conversation.total_messages} mensajes
                            </span>
                          </div>
                          
                          <button
                            onClick={() => viewConversationDetails(conversation.id)}
                            className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
                          >
                            <EyeIcon className="h-3 w-3 mr-1" />
                            Ver detalles
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-6 text-center text-gray-500">
                  <ChatBubbleLeftRightIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p className="text-lg font-medium">
                    {showAllConversations 
                      ? (selectedUser ? 'No hay conversaciones para este usuario' : 'No hay conversaciones con mensajes')
                      : 'No hay conversaciones con mensajes'
                    }
                  </p>
                  <p className="text-sm">
                    {showAllConversations 
                      ? (selectedUser ? 'Este usuario no tiene conversaciones activas' : 'Las conversaciones vacías se han filtrado automáticamente')
                      : 'Las conversaciones vacías se han filtrado automáticamente'
                    }
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Preguntas más frecuentes */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 flex items-center">
                <LightBulbIcon className="h-5 w-5 mr-2" />
                Preguntas Más Frecuentes
              </h3>
            </div>
            <div className="divide-y divide-gray-200">
              {chatData.topQuestions?.map((question, index) => (
                <div key={index} className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {question.topic}
                      </p>
                    </div>
                    <div className="ml-4">
                      <span className="text-sm font-medium text-gray-900">
                        {question.count}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Rendimiento del agente y salud del sistema */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
          {/* Rendimiento del agente */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 flex items-center">
                <CpuChipIcon className="h-5 w-5 mr-2" />
                Rendimiento del Agente IA
              </h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-900">
                    {chatData.agentPerformance?.total_responses || 0}
                  </p>
                  <p className="text-sm text-gray-500">Respuestas del Agente</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">
                    {chatData.agentPerformance?.success_rate_percent || 0}%
                  </p>
                  <p className="text-sm text-gray-500">Tasa de Éxito</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">
                    {chatData.agentPerformance?.avg_response_time_ms ? 
                      (chatData.agentPerformance.avg_response_time_ms / 1000).toFixed(1) + 's' : '0s'}
                  </p>
                  <p className="text-sm text-gray-500">Tiempo Promedio</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-yellow-600">
                    {chatData.agentPerformance?.error_rate_percent || 0}%
                  </p>
                  <p className="text-sm text-gray-500">Tasa de Error</p>
                </div>
              </div>
            </div>
          </div>

          {/* Salud del sistema */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 flex items-center">
                <ChartBarIcon className="h-5 w-5 mr-2" />
                Salud del Sistema
              </h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Puntuación de Salud</span>
                  <span className={`text-sm font-medium ${
                    chatData.systemHealth?.score > 80 ? 'text-green-600' : 
                    chatData.systemHealth?.score > 60 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {chatData.systemHealth?.score || 0}/100
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${
                      chatData.systemHealth?.score > 80 ? 'bg-green-600' : 
                      chatData.systemHealth?.score > 60 ? 'bg-yellow-600' : 'bg-red-600'
                    }`}
                    style={{ width: `${chatData.systemHealth?.score || 0}%` }}
                  ></div>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Estado</span>
                  <span className={`text-sm font-medium ${
                    chatData.systemHealth?.status === 'healthy' ? 'text-green-600' : 
                    chatData.systemHealth?.status === 'warning' ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {chatData.systemHealth?.status === 'healthy' ? 'Saludable' : 
                     chatData.systemHealth?.status === 'warning' ? 'Advertencia' : 'Crítico'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Modal de detalles de conversación */}
      {showConversationModal && selectedConversation && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-2">
          <div className="relative mx-auto border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white max-h-[95vh] flex flex-col">
            <div className="p-4 border-b">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">
                  Detalles de la Conversación
                </h3>
                <button
                  onClick={() => setShowConversationModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
              
              <div className="mt-3 space-y-1">
                <p className="text-sm text-gray-600">
                  <strong>Usuario:</strong> {selectedConversation.user?.first_name} {selectedConversation.user?.last_name} ({selectedConversation.user?.email})
                </p>
                <p className="text-sm text-gray-600">
                  <strong>Mensajes:</strong> {selectedConversation.total_messages}
                </p>
                <p className="text-sm text-gray-600">
                  <strong>Creada:</strong> {new Date(selectedConversation.created_at).toLocaleString()}
                </p>
              </div>
            </div>

            <div id="messages-container" className="flex-1 overflow-y-auto p-4">
              {selectedConversation.conversation_data?.messages?.map((message, index) => (
                <div key={index} className={`mb-3 p-3 rounded-lg ${
                  message.type === 'user' ? 'bg-blue-50 ml-8' : 
                  message.type === 'assistant' ? 'bg-gray-50 mr-8' : 'bg-yellow-50'
                }`}>
                  <div className="flex items-center mb-1">
                    <span className={`text-xs font-medium ${
                      message.type === 'user' ? 'text-blue-600' : 
                      message.type === 'assistant' ? 'text-gray-600' : 'text-yellow-600'
                    }`}>
                      {message.type === 'user' ? '👤 Usuario' : 
                     message.type === 'assistant' ? '🤖 Asistente' : '⚙️ Sistema'}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">
                      {new Date(message.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-800 whitespace-pre-wrap">{message.content}</p>
                  {message.metadata && (
                    <div className="mt-2 text-xs text-gray-500">
                      <details>
                        <summary>Metadatos</summary>
                        <pre className="mt-1 text-xs bg-gray-100 p-2 rounded">
                          {JSON.stringify(message.metadata, null, 2)}
                        </pre>
                      </details>
                    </div>
                  )}
                </div>
              )) || (
                <p className="text-gray-500 text-sm">No hay mensajes disponibles</p>
              )}
              {/* Espacio inferior mínimo */}
              <div className="h-4"></div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de todas las conversaciones */}
      {showAllConversationsModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowAllConversationsModal(false)}></div>
            
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      Todas las Conversaciones
                    </h3>
                    
                    {/* Filtro por usuario */}
                    <div className="mb-4 flex items-center space-x-4">
                      <label className="text-sm font-medium text-gray-700">
                        Filtrar por usuario:
                      </label>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={handleOpenUserModal}
                          className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                          <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                          </svg>
                          {selectedUser ? getSelectedUserName() : 'Seleccionar usuario'}
                        </button>
                        
                        {selectedUser && (
                          <button
                            onClick={() => {
                              setSelectedUser('');
                              setUserSearchTerm('');
                            }}
                            className="text-gray-400 hover:text-gray-600"
                            title="Limpiar filtro"
                          >
                            ✕
                          </button>
                        )}
                      </div>
                    </div>
                    
                    {/* Lista de conversaciones */}
                    <div className="max-h-96 overflow-y-auto border border-gray-200 rounded-md">
                      <div className="divide-y divide-gray-200">
                        {getModalFilteredConversations().length > 0 ? (
                          getModalFilteredConversations().map((conversation, index) => (
                            <div key={conversation.id} className={`p-4 hover:bg-gray-50 transition-colors duration-200 ${index > 0 ? 'border-t border-gray-100' : ''}`}>
                              <div className="flex items-start justify-between">
                                <div className="flex-1 min-w-0">
                                  {/* Header con usuario y estado */}
                                  <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center space-x-3">
                                      <div className="flex-shrink-0">
                                        <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                                          <span className="text-sm font-medium text-blue-600">
                                            {conversation.user?.first_name ? conversation.user.first_name.charAt(0).toUpperCase() : 'U'}
                                          </span>
                                        </div>
                                      </div>
                                      <div>
                                        <p className="text-sm font-semibold text-gray-900">
                                          {conversation.user?.first_name && conversation.user?.last_name 
                                            ? `${conversation.user.first_name} ${conversation.user.last_name}`
                                            : conversation.user?.email || 'Usuario'
                                          }
                                        </p>
                                        <p className="text-xs text-gray-500">
                                          {formatTime(conversation.created_at)}
                                        </p>
                                      </div>
                                    </div>
                                    
                                    {/* Estado de la conversación */}
                                    <div className="flex items-center space-x-2">
                                      {conversation.status === 'completed' ? (
                                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                          <CheckCircleIcon className="h-3 w-3 mr-1" />
                                          Completada
                                        </span>
                                      ) : conversation.status === 'active' ? (
                                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                          <div className="h-2 w-2 rounded-full bg-blue-500 animate-pulse mr-1"></div>
                                          Activa
                                        </span>
                                      ) : (
                                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                          <XCircleIcon className="h-3 w-3 mr-1" />
                                          Cerrada
                                        </span>
                                      )}
                                    </div>
                                  </div>

                                  {/* Footer con métricas */}
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                                      <span className="flex items-center">
                                        <ChatBubbleLeftRightIcon className="h-3 w-3 mr-1" />
                                        {conversation.total_messages} mensajes
                                      </span>
                                    </div>
                                    
                                    <button
                                      onClick={() => {
                                        setShowAllConversationsModal(false);
                                        viewConversationDetails(conversation.id);
                                      }}
                                      className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
                                    >
                                      <EyeIcon className="h-3 w-3 mr-1" />
                                      Ver conversación
                                    </button>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className="p-6 text-center text-gray-500">
                            <ChatBubbleLeftRightIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                            <p className="text-lg font-medium">
                              {selectedUser ? 'No hay conversaciones para este usuario' : 'No hay conversaciones con mensajes'}
                            </p>
                            <p className="text-sm">
                              {selectedUser ? 'Este usuario no tiene conversaciones activas' : 'Las conversaciones vacías se han filtrado automáticamente'}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={() => setShowAllConversationsModal(false)}
                  className="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de selección de usuarios */}
      {showUserModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowUserModal(false)}></div>
            
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      Seleccionar Usuario
                    </h3>
                    
                    {/* Campo de búsqueda */}
                    <div className="mb-4">
                      <input
                        type="text"
                        placeholder="Buscar usuario por nombre o email..."
                        value={userSearchTerm}
                        onChange={handleUserSearchChange}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    
                    {/* Lista de usuarios */}
                    <div className="max-h-96 overflow-y-auto border border-gray-200 rounded-md">
                      <div className="divide-y divide-gray-200">
                        <button
                          onClick={() => handleUserSelect('')}
                          className="w-full text-left px-4 py-3 hover:bg-gray-50 flex items-center"
                        >
                          <div className="flex-shrink-0 h-8 w-8 bg-gray-100 rounded-full flex items-center justify-center mr-3">
                            <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                            </svg>
                          </div>
                          <div>
                            <div className="font-medium text-gray-900">Todos los usuarios</div>
                            <div className="text-sm text-gray-500">Ver conversaciones de todos los usuarios</div>
                          </div>
                        </button>
                        
                        {getFilteredUsers().map(user => (
                          <button
                            key={user.id}
                            onClick={() => handleUserSelect(user.id)}
                            className="w-full text-left px-4 py-3 hover:bg-gray-50 flex items-center"
                          >
                            <div className="flex-shrink-0 h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                              <span className="text-sm font-medium text-blue-600">
                                {user.first_name.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <div>
                              <div className="font-medium text-gray-900">
                                {user.first_name} {user.last_name}
                              </div>
                              <div className="text-sm text-gray-500">{user.email}</div>
                            </div>
                          </button>
                        ))}
                        
                        {getFilteredUsers().length === 0 && (
                          <div className="px-4 py-8 text-center text-gray-500">
                            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0112 15c-2.34 0-4.29-1.009-5.824-2.709M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                            <p className="mt-2 text-sm">No se encontraron usuarios</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={() => setShowUserModal(false)}
                  className="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatMonitoringPage;
