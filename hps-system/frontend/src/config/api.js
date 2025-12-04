// Configuración de la API para el frontend HPS
// NOTA: Actualizado para usar el backend Django de cryptotrace
const config = {
  // URL base del backend API (Django en puerto 8080)
  API_BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8080',
  
  // Endpoints de la API (adaptados a Django REST Framework)
  endpoints: {
    // Autenticación (Django SimpleJWT)
    auth: {
      login: '/api/token/',  // Django SimpleJWT
      logout: '/api/token/logout/',  // Si está implementado
      me: '/api/hps/user/profile/',  // Endpoint de perfil HPS
      changePassword: '/api/auth/cambiar-password/',  // Endpoint Django
      verifyToken: '/api/token/verify/'  // Django SimpleJWT
    },
    
    // Usuarios (Django - usando perfiles HPS)
    users: {
      list: '/api/hps/user/profiles/',  // Lista de perfiles HPS
      create: '/api/hps/user/profiles/',  // Crear usuario (si está implementado)
      detail: (id) => `/api/hps/user/profiles/${id}/`,
      update: (id) => `/api/hps/user/profiles/${id}/`,
      delete: (id) => `/api/hps/user/profiles/${id}/`,
      permanentDelete: (id) => `/api/hps/user/profiles/${id}/permanent/`,  // TODO: Implementar si es necesario
      activate: (id) => `/api/hps/user/profiles/${id}/activate/`,  // TODO: Implementar si es necesario
      byTeam: (teamId) => `/api/hps/teams/${teamId}/members/`,
      byRole: (role) => `/api/hps/user/profiles/?role=${role}`,  // TODO: Implementar filtro por rol
      stats: '/api/hps/user/profiles/stats/',  // TODO: Implementar si es necesario
      search: '/api/hps/user/profiles/search/',  // TODO: Implementar si es necesario
      resetPassword: (id) => `/api/auth/cambiar-password/`  // Usar endpoint de cambio de contraseña
    },
    
    // HPS (Django hps_core)
    hps: {
      list: '/api/hps/requests/',
      create: '/api/hps/requests/',
      detail: (id) => `/api/hps/requests/${id}/`,
      approve: (id) => `/api/hps/requests/${id}/approve/`,
      reject: (id) => `/api/hps/requests/${id}/reject/`,
      submit: (id) => `/api/hps/requests/${id}/submit/`,
      stats: '/api/hps/requests/stats/',
      pending: '/api/hps/requests/pending/list/',
      submitted: '/api/hps/requests/submitted/list/',
      public: '/api/hps/requests/public/',
      team: (teamId) => `/api/hps/requests/team/${teamId}/`
    },
    
    // Templates (Django hps_core)
    templates: {
      list: '/api/hps/templates/',
      create: '/api/hps/templates/',
      detail: (id) => `/api/hps/templates/${id}/`,
      update: (id) => `/api/hps/templates/${id}/`,
      delete: (id) => `/api/hps/templates/${id}/`,
      pdf: (id) => `/api/hps/templates/${id}/pdf/`,
      extractFields: (id) => `/api/hps/templates/${id}/extract-pdf-fields/`,
      editPdf: (id) => `/api/hps/templates/${id}/edit-pdf/`
    },
    
    // Tokens (Django hps_core)
    tokens: {
      list: '/api/hps/tokens/',
      create: '/api/hps/tokens/',
      detail: (id) => `/api/hps/tokens/${id}/`,
      validate: '/api/hps/tokens/validate/',
      info: '/api/hps/tokens/info/'
    },
    
    // Teams (Django hps_core)
    teams: {
      list: '/api/hps/teams/',
      create: '/api/hps/teams/',
      detail: (id) => `/api/hps/teams/${id}/`,
      update: (id) => `/api/hps/teams/${id}/`,
      delete: (id) => `/api/hps/teams/${id}/`,
      members: (id) => `/api/hps/teams/${id}/members/`
    },
    
    // Chat/Agente IA (WebSocket)
    chat: {
      websocket: process.env.REACT_APP_AGENTE_IA_WS_URL || 'ws://localhost:8080',
      conversations: '/api/hps/chat/conversations/',
      metrics: '/api/hps/chat/metrics/',
      reset: '/api/hps/chat/conversations/reset/'
    }
  },
  
  // Configuración de timeouts y retries
  timeout: 10000,
  retries: 3,
  
  // Headers por defecto
  defaultHeaders: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
};

export default config;

