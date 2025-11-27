// Servicio de API para comunicación con el backend
import axios from 'axios';
import config from '../config/api';

// Crear instancia de axios con configuración base
const apiClient = axios.create({
  baseURL: config.API_BASE_URL,
  timeout: config.timeout,
  headers: config.defaultHeaders
});

// Interceptor para agregar token de autorización
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('hps_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para refrescar token automáticamente
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Si no hay config, es un error de red o similar
    if (!error.config) {
      // Crear un error más descriptivo
      let errorMessage = 'Error de conexión. Verifica que el servidor esté funcionando.';
      
      // Si el error original es un Event, extraer información útil
      if (error instanceof Event) {
        errorMessage = 'Error de conexión. Por favor, intenta de nuevo.';
      } else if (error && typeof error === 'object') {
        // Intentar extraer un mensaje del error
        if (error.message) {
          errorMessage = error.message;
        } else if (error.toString && error.toString() !== '[object Object]' && error.toString() !== '[object Event]') {
          errorMessage = error.toString();
        }
      }
      
      const networkError = new Error(errorMessage);
      networkError.code = 'NETWORK_ERROR';
      networkError.originalError = error;
      return Promise.reject(networkError);
    }
    
    const originalRequest = error.config;
    
    // Si el error es 401 y no hemos intentado refrescar el token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('hps_refresh_token');
        if (refreshToken) {
          const response = await apiClient.post('/api/token/refresh/', {
            refresh: refreshToken
          });
          
          const { access } = response.data;
          localStorage.setItem('hps_token', access);
          
          // Reintentar la petición original con el nuevo token
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Si el refresh falla, limpiar tokens y redirigir al login
        localStorage.removeItem('hps_token');
        localStorage.removeItem('hps_refresh_token');
        localStorage.removeItem('hps_user');
        // No redirigir automáticamente, dejar que el componente maneje el error
        return Promise.reject(refreshError);
      }
    }
    
    // Asegurar que el error tenga un formato consistente
    if (!error.message) {
      if (error.response?.data) {
        error.message = error.response.data.detail || error.response.data.message || 'Error en la petición';
      } else if (error instanceof Event) {
        error.message = 'Error de conexión. Por favor, intenta de nuevo.';
      } else if (error && typeof error === 'object' && error.toString && error.toString() !== '[object Object]' && error.toString() !== '[object Event]') {
        error.message = error.toString();
      } else {
        error.message = 'Error desconocido';
      }
    }
    
    return Promise.reject(error);
  }
);

// (El interceptor de respuesta se movió arriba para manejar refresh de tokens)

// Servicios de autenticación (adaptado para Django SimpleJWT)
export const authService = {
  // Login (Django SimpleJWT usa 'username' y devuelve 'access' y 'refresh')
  login: async (email, password) => {
    const response = await apiClient.post(config.endpoints.auth.login, {
      username: email,  // Django usa 'username' (que puede ser el email)
      password: password
    });
    
    // Django SimpleJWT devuelve 'access' y 'refresh' en lugar de 'access_token'
    if (response.data.access) {
      localStorage.setItem('hps_token', response.data.access);
      localStorage.setItem('hps_refresh_token', response.data.refresh);
      
      // Decodificar token para obtener información del usuario
      try {
        const tokenParts = response.data.access.split('.');
        if (tokenParts.length === 3) {
          const payload = JSON.parse(atob(tokenParts[1]));
          localStorage.setItem('hps_user', JSON.stringify({
            id: payload.user_id,
            email: payload.username || email,
            role: payload.role || 'user',
            is_superuser: payload.is_superuser || false
          }));
        }
      } catch (e) {
        console.warn('Error decodificando token:', e);
      }
    }
    
    return response.data;
  },
  
  // Logout
  logout: async () => {
    try {
      // Archivar conversación activa antes del logout
      const websocketService = (await import('./websocketService')).default;
      await websocketService.disconnectIntentionally();
      
      await apiClient.post(config.endpoints.auth.logout);
    } catch (error) {
      console.warn('Error en logout del servidor:', error);
    } finally {
      localStorage.removeItem('hps_token');
      localStorage.removeItem('hps_user');
    }
  },
  
  // Obtener usuario actual
  getCurrentUser: async () => {
    const response = await apiClient.get(config.endpoints.auth.me);
    return response.data;
  },
  
  // Verificar token (Django SimpleJWT no tiene endpoint verify por defecto)
  // En su lugar, intentamos obtener el perfil del usuario
  verifyToken: async () => {
    try {
      // Intentar obtener el perfil del usuario como verificación del token
      const response = await apiClient.get(config.endpoints.auth.me);
      return response.data; // Devolver los datos del usuario directamente
    } catch (error) {
      // Si falla, lanzar el error para que el store lo maneje
      throw error;
    }
  },
  
  // Cambiar contraseña
  changePassword: async (currentPassword, newPassword, confirmPassword) => {
    const response = await apiClient.post(config.endpoints.auth.changePassword, {
      current_password: currentPassword,
      new_password: newPassword,
      confirm_password: confirmPassword
    });
    return response.data;
  }
};

// Servicios de usuarios
export const userService = {
  // Listar usuarios (perfiles HPS)
  getUsers: async (params = {}) => {
    const response = await apiClient.get(config.endpoints.users.list, { params });
    
    // Django REST Framework puede devolver:
    // - Array directo: [obj1, obj2, ...]
    // - Objeto paginado: {count: X, next: null, previous: null, results: [...]}
    let users = [];
    
    if (Array.isArray(response.data)) {
      users = response.data;
    } else if (response.data && Array.isArray(response.data.results)) {
      users = response.data.results;
    } else if (response.data && Array.isArray(response.data.users)) {
      users = response.data.users;
    } else {
      users = [];
      console.warn('Formato de respuesta de usuarios desconocido:', response.data);
    }
    
    // Transformar perfiles HPS al formato esperado por el frontend
    const transformedUsers = users.map(profile => ({
      id: profile.user_id || profile.id,
      email: profile.email || (profile.user && profile.user.email),
      username: profile.username || (profile.user && profile.user.username),
      first_name: profile.first_name || (profile.user && profile.user.first_name),
      last_name: profile.last_name || (profile.user && profile.user.last_name),
      full_name: profile.full_name || `${profile.first_name || ''} ${profile.last_name || ''}`.trim() || (profile.user && `${profile.user.first_name || ''} ${profile.user.last_name || ''}`.trim()),
      role: profile.role || (profile.role_name || (profile.role && profile.role.name)),
      team_id: profile.team_id || (profile.team && profile.team.id),
      team_name: profile.team_name || (profile.team && profile.team.name),
      is_active: profile.is_active !== undefined ? profile.is_active : (profile.user && profile.user.is_active),
      is_temp_password: profile.is_temp_password || false,
      must_change_password: profile.must_change_password || false,
      email_verified: profile.email_verified || false,
      created_at: profile.created_at,
      updated_at: profile.updated_at
    }));
    
    return { users: transformedUsers };
  },
  
  // Crear usuario
  createUser: async (userData) => {
    const response = await apiClient.post(config.endpoints.users.create, userData);
    return response.data;
  },
  
  // Obtener usuario por ID
  getUserById: async (id) => {
    const response = await apiClient.get(config.endpoints.users.detail(id));
    return response.data;
  },
  
  // Actualizar usuario
  updateUser: async (id, userData) => {
    const response = await apiClient.put(config.endpoints.users.update(id), userData);
    return response.data;
  },
  
  // Eliminar usuario
  deleteUser: async (id) => {
    const response = await apiClient.delete(config.endpoints.users.delete(id));
    return response.data;
  },
  
  // Eliminar usuario definitivamente
  permanentlyDeleteUser: async (id) => {
    const response = await apiClient.delete(config.endpoints.users.permanentDelete(id));
    return response.data;
  },
  
  // Activar usuario
  activateUser: async (id) => {
    const response = await apiClient.post(config.endpoints.users.activate(id));
    return response.data;
  },
  
  // Obtener usuarios por equipo
  getUsersByTeam: async (teamId) => {
    const response = await apiClient.get(config.endpoints.users.byTeam(teamId));
    return response.data;
  },

  // Obtener miembros del equipo
  getTeamMembers: async (teamId) => {
    try {
      const response = await apiClient.get(`/api/hps/teams/${teamId}/members/`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching team members:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al obtener miembros del equipo' 
      };
    }
  },
  
  // Obtener usuarios por rol
  getUsersByRole: async (role) => {
    const response = await apiClient.get(config.endpoints.users.byRole(role));
    return response.data;
  },
  
  // Obtener estadísticas
  getStats: async () => {
    const response = await apiClient.get(config.endpoints.users.stats);
    return response.data;
  },
  
  // Buscar usuarios
  searchUsers: async (query, limit = 10) => {
    const response = await apiClient.get(config.endpoints.users.search, {
      params: { q: query, limit }
    });
    return response.data;
  },
  
  // Resetear contraseña
  resetPassword: async (id, newPassword, confirmPassword) => {
    const response = await apiClient.post(config.endpoints.users.resetPassword(id), {
      new_password: newPassword,
      confirm_password: confirmPassword
    });
    return response.data;
  }
};

// Utilidades
export const apiUtils = {
  // Verificar si hay token
  hasToken: () => {
    return !!localStorage.getItem('hps_token');
  },
  
  // Obtener usuario almacenado
  getStoredUser: () => {
    const user = localStorage.getItem('hps_user');
    return user ? JSON.parse(user) : null;
  },
  
  // Verificar si el usuario es admin
  isAdmin: () => {
    const user = apiUtils.getStoredUser();
    return user?.role === 'admin';
  },
  
  // Verificar si el usuario es team leader
  isTeamLeader: () => {
    const user = apiUtils.getStoredUser();
    return user?.role === 'team_leader';
  },
  
  // Verificar si el usuario puede gestionar usuarios
  canManageUsers: () => {
    const user = apiUtils.getStoredUser();
    return user?.role === 'admin' || user?.role === 'team_leader';
  }
};

// Servicio HPS
export const hpsService = {
  // Obtener solicitudes HPS
  getHPSRequests: async (params = {}) => {
    const response = await apiClient.get(config.endpoints.hps.list, { params });
    return response.data;
  },

  // Obtener una solicitud HPS por ID
  getHPSRequest: async (id) => {
    const response = await apiClient.get(config.endpoints.hps.detail(id));
    return response.data;
  },

  // Crear solicitud HPS
  createHPSRequest: async (data) => {
    const response = await apiClient.post(config.endpoints.hps.create, data);
    return response.data;
  },

  // Actualizar solicitud HPS
  updateHPSRequest: async (id, data) => {
    const response = await apiClient.put(config.endpoints.hps.detail(id), data);
    return response.data;
  },

  // Eliminar solicitud HPS
  deleteHPSRequest: async (id) => {
    const response = await apiClient.delete(config.endpoints.hps.detail(id));
    return response.data;
  },

  // Aprobar solicitud HPS
  approveHPSRequest: async (id, data) => {
    const response = await apiClient.post(config.endpoints.hps.approve(id), data);
    return response.data;
  },

  // Rechazar solicitud HPS
  rejectHPSRequest: async (id, data) => {
    const response = await apiClient.post(config.endpoints.hps.reject(id), data);
    return response.data;
  },

  // Obtener estadísticas HPS
  getHPSStats: async () => {
    const response = await apiClient.get('/api/hps/requests/stats/');
    return response.data;
  }
};

// Servicio de Equipos
export const teamService = {
  // Obtener lista de equipos
  getTeams: async (params = {}) => {
    const response = await apiClient.get('/api/hps/teams/', { params });
    return response.data;
  },

  // Obtener un equipo por ID
  getTeam: async (id) => {
    const response = await apiClient.get(`/api/hps/teams/${id}/`);
    return response.data;
  },

  // Crear equipo
  createTeam: async (data) => {
    const response = await apiClient.post('/api/hps/teams/', data);
    return response.data;
  },

  // Actualizar equipo
  updateTeam: async (id, data) => {
    const response = await apiClient.put(`/api/hps/teams/${id}/`, data);
    return response.data;
  },

  // Eliminar equipo
  deleteTeam: async (id) => {
    const response = await apiClient.delete(`/api/hps/teams/${id}/`);
    return response.data;
  },

  // Obtener estadísticas de equipos (no implementado en Django aún)
  getTeamStats: async () => {
    // TODO: Implementar endpoint en Django si es necesario
    return { total: 0, active: 0, members: 0 };
  },

  // Obtener líderes disponibles (no implementado en Django aún)
  getAvailableLeaders: async (teamId = null) => {
    // TODO: Implementar endpoint en Django si es necesario
    return [];
  },

  // Obtener detalles del equipo con miembros
  getTeamDetail: async (id) => {
    const response = await apiClient.get(`/api/hps/teams/${id}/`);
    return response.data;
  },

  // Obtener miembros del equipo para asignar como líder
  getTeamMembers: async (id) => {
    const response = await apiClient.get(`/api/hps/teams/${id}/members/`);
    return response.data;
  }
};

export default apiClient;

