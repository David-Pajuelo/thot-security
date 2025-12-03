// Store de autenticación usando Zustand
import { create } from 'zustand';
// import { persist } from 'zustand/middleware'; // Comentado temporalmente para debug
import { authService, apiUtils } from '../services/apiService';

const useAuthStore = create(
  // persist( // Comentado temporalmente para debug
    (set, get) => ({
      // Estado
      isAuthenticated: false,
      user: null,
      token: null,
      loading: false,
      verifying: false,
      error: null,
      errorType: null,
      showChangePasswordModal: false,

      // Acciones de autenticación
      login: async (email, password) => {
        set({ loading: true, error: null });
        
        try {
          const response = await authService.login(email, password);
          
          // Obtener información completa del usuario
          let userData;
          try {
            userData = await authService.getCurrentUser();
          } catch (error) {
            // Si falla obtener el perfil, usar información del token
            console.warn('No se pudo obtener perfil completo, usando información del token:', error);
            const tokenParts = response.access?.split('.') || response.access_token?.split('.') || [];
            if (tokenParts.length === 3) {
              const payload = JSON.parse(atob(tokenParts[1]));
              userData = {
                id: parseInt(payload.user_id),
                email: payload.username || email,
                first_name: payload.first_name || '',
                last_name: payload.last_name || '',
                full_name: `${payload.first_name || ''} ${payload.last_name || ''}`.trim(),
                role: null,
                is_active: true,
                is_temp_password: payload.must_change_password || false,
                team_id: null,
                team_name: null,
              };
            } else {
              throw new Error('No se pudo obtener información del usuario');
            }
          }
          
          const userInfo = {
            id: userData.id,
            email: userData.email,
            first_name: userData.first_name,
            last_name: userData.last_name,
            full_name: userData.full_name,
            role: userData.role,
            is_active: userData.is_active,
            is_temp_password: userData.is_temp_password,
            team_id: userData.team_id,
            team_name: userData.team_name
          };

          // Actualizar localStorage con la información completa (ambos sistemas)
          localStorage.setItem('user', JSON.stringify(userInfo));
          localStorage.setItem('hps_user', JSON.stringify(userInfo)); // Compatibilidad temporal
          
          // Limpiar email guardado cuando el login es exitoso
          localStorage.removeItem('hps_saved_email');
          
          // Guardar tokens en nombres estándar (compartidos con CryptoTrace)
          const accessToken = response.access || response.access_token;
          const refreshToken = response.refresh || response.refresh_token;
          
          if (accessToken) {
            localStorage.setItem('accessToken', accessToken);
            localStorage.setItem('hps_token', accessToken); // Compatibilidad temporal
          }
          if (refreshToken) {
            localStorage.setItem('refreshToken', refreshToken);
            localStorage.setItem('hps_refresh_token', refreshToken); // Compatibilidad temporal
          }
          
          set({
            isAuthenticated: true,
            user: userInfo,
            token: accessToken,
            loading: false,
            error: null,
            showChangePasswordModal: userData.is_temp_password || false
          });
          
          // Limpiar chat al hacer login para evitar mensajes duplicados
          const chatStore = (await import('./chatStore')).default;
          chatStore.getState().clearChatCompletely();
          
          return response;
        } catch (error) {
          let errorMessage = 'Error de autenticación';
          let errorType = 'general';
          
          // Manejar diferentes tipos de errores
          if (error instanceof Error) {
            // Error estándar de JavaScript
            if (error.message) {
              errorMessage = error.message;
            }
          } else if (error && typeof error === 'object') {
            // Error de axios o similar
            if (error.response?.status === 401) {
              // El backend devuelve 401 para ambos casos, usar el mensaje del servidor
              const serverMessage = error.response?.data?.detail || error.response?.data?.message || '';
              if (serverMessage.includes('Email o contraseña incorrectos') || serverMessage.includes('No active account')) {
                errorMessage = 'Credenciales incorrectas. Verifica tu email y contraseña.';
                errorType = 'credentials';
              } else {
                errorMessage = serverMessage || 'Credenciales incorrectas. Verifica tu email y contraseña.';
                errorType = 'credentials';
              }
            } else if (error.response?.status === 404) {
              errorMessage = 'Usuario no encontrado. Verifica tu email.';
              errorType = 'user_not_found';
            } else if (error.response?.status === 403) {
              errorMessage = 'Cuenta desactivada. Contacta al administrador.';
              errorType = 'account_disabled';
            } else if (error.response?.data?.detail) {
              errorMessage = typeof error.response.data.detail === 'string' 
                ? error.response.data.detail 
                : JSON.stringify(error.response.data.detail);
              errorType = 'server_error';
            } else if (error.response?.data?.message) {
              errorMessage = error.response.data.message;
              errorType = 'server_error';
            } else if (error.message) {
              errorMessage = error.message;
            } else if (error.code === 'NETWORK_ERROR' || error.code === 'ECONNREFUSED') {
              errorMessage = 'Error de conexión. Verifica tu internet y que el servidor esté funcionando.';
              errorType = 'network';
            }
          } else if (typeof error === 'string') {
            errorMessage = error;
          } else {
            // Cualquier otro tipo (Event, etc.)
            errorMessage = 'Error de autenticación. Por favor, intenta de nuevo.';
            console.error('Error inesperado en login:', error);
          }
          
          set({
            isAuthenticated: false,
            user: null,
            token: null,
            loading: false,
            error: errorMessage,
            errorType: errorType,
            showChangePasswordModal: false
          });
          throw error;
        }
      },

      logout: async () => {
        set({ loading: true });
        
        try {
          await authService.logout();
        } catch (error) {
          console.warn('Error en logout:', error);
        } finally {
          // Limpiar datos de sesión
            // Limpiar tokens de ambos sistemas
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('user');
            localStorage.removeItem('hps_token');
            localStorage.removeItem('hps_refresh_token');
            localStorage.removeItem('hps_user');
          localStorage.removeItem('hps_saved_email'); // Limpiar email guardado también
          
          set({
            isAuthenticated: false,
            user: null,
            token: null,
            loading: false,
            verifying: false,
            error: null,
            showChangePasswordModal: false
          });
        }
      },

      // Cargar usuario actual desde el backend
      loadCurrentUser: async () => {
        if (!apiUtils.hasToken()) {
          return;
        }

        set({ loading: true });
        
        try {
          const userData = await authService.getCurrentUser();
          
          const userInfo = {
            id: userData.id,
            email: userData.email,
            first_name: userData.first_name,
            last_name: userData.last_name,
            full_name: userData.full_name,
            role: userData.role,
            is_active: userData.is_active,
            team_id: userData.team_id,
            team_name: userData.team_name
          };

          // Actualizar localStorage con la información completa (ambos sistemas)
          localStorage.setItem('user', JSON.stringify(userInfo));
          localStorage.setItem('hps_user', JSON.stringify(userInfo)); // Compatibilidad temporal

          set({
            isAuthenticated: true,
            user: userInfo,
            token: localStorage.getItem('accessToken') || localStorage.getItem('hps_token'),
            loading: false,
            error: null
          });
        } catch (error) {
          console.error('Error cargando usuario:', error);
          // Si hay error, limpiar autenticación
          get().logout();
        }
      },

      // Verificar token (usando getCurrentUser en lugar de verifyToken que no existe en Django)
      verifyToken: async () => {
        if (!apiUtils.hasToken()) {
          console.log('verifyToken - No hay token en localStorage');
          return false;
        }

        try {
          console.log('verifyToken - Intentando verificar token obteniendo perfil...');
          // Usar getCurrentUser como verificación del token
          const userData = await authService.getCurrentUser();
          console.log('verifyToken - Token válido, usuario:', userData.email);
          
          // Actualizar información del usuario en el store
          const userInfo = {
            id: userData.id,
            email: userData.email,
            first_name: userData.first_name,
            last_name: userData.last_name,
            full_name: userData.full_name,
            role: userData.role,
            is_active: userData.is_active,
            is_temp_password: userData.is_temp_password,
            team_id: userData.team_id,
            team_name: userData.team_name
          };
          
          // Guardar en ambos lugares para compatibilidad
          localStorage.setItem('user', JSON.stringify(userInfo));
          localStorage.setItem('hps_user', JSON.stringify(userInfo));
          
          set({
            isAuthenticated: true,
            user: userInfo,
            token: apiUtils.hasToken() ? (localStorage.getItem('accessToken') || localStorage.getItem('hps_token')) : null,
            verifying: false
          });
          
          return true;
        } catch (error) {
          console.error('verifyToken - Error verificando token:', error);
          
          // Si es un error de autenticación (401 o 403), el token es inválido
          if (error.response?.status === 401 || error.response?.status === 403) {
            console.log('verifyToken - Token inválido (401/403), limpiando sesión');
            
            // Limpiar datos de sesión (ambos sistemas)
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('user');
            localStorage.removeItem('hps_token');
            localStorage.removeItem('hps_refresh_token');
            localStorage.removeItem('hps_user');
            localStorage.removeItem('hps_saved_email');
            
            // Actualizar estado
            set({
              isAuthenticated: false,
              user: null,
              token: null,
              loading: false,
              verifying: false,
              error: null,
              showChangePasswordModal: false
            });
            
            return false;
          }
          
          // Para otros errores (red, servidor, etc.), asumir que el token es válido
          // para evitar cerrar la sesión por problemas de conectividad
          console.log('verifyToken - Error de conectividad, asumiendo token válido');
          return true;
        }
      },

      // Verificar y renovar token si es necesario
      checkAndRefreshToken: async () => {
        if (!apiUtils.hasToken()) {
          return false;
        }

        try {
          // Intentar obtener el perfil del usuario como verificación del token
          const userData = await authService.getCurrentUser();
          
          // Actualizar información del usuario
          const userInfo = {
            id: userData.id,
            email: userData.email,
            first_name: userData.first_name,
            last_name: userData.last_name,
            full_name: userData.full_name,
            role: userData.role,
            is_active: userData.is_active,
            is_temp_password: userData.is_temp_password,
            team_id: userData.team_id,
            team_name: userData.team_name
          };
          
          // Guardar en ambos lugares para compatibilidad
          localStorage.setItem('user', JSON.stringify(userInfo));
          localStorage.setItem('hps_user', JSON.stringify(userInfo));
          set({ user: userInfo });
          
          return true;
        } catch (error) {
          console.error('checkAndRefreshToken - Error verificando token:', error);
          
          // Si es un error de autenticación, hacer logout
          if (error.response?.status === 401 || error.response?.status === 403) {
            get().logout();
            return false;
          }
          
          // Para otros errores, mantener el estado actual
          return true;
        }
      },

      // Cambiar contraseña
      changePassword: async (currentPassword, newPassword, confirmPassword) => {
        set({ loading: true, error: null });
        
        try {
          const response = await authService.changePassword(
            currentPassword,
            newPassword,
            confirmPassword
          );
          
          set({ loading: false });
          return response;
        } catch (error) {
          const errorMessage = error.response?.data?.detail || 'Error cambiando contraseña';
          set({ loading: false, error: errorMessage });
          throw error;
        }
      },

      // Controlar modal de cambio de contraseña
      openChangePasswordModal: () => {
        set({ showChangePasswordModal: true });
      },

      closeChangePasswordModal: () => {
        set({ showChangePasswordModal: false });
      },

      // Inicializar autenticación desde localStorage
      initializeAuth: async () => {
        // Verificar en ambos lugares (nuevo y antiguo)
        const token = localStorage.getItem('accessToken') || localStorage.getItem('hps_token');
        const user = apiUtils.getStoredUser();
        
        console.log('initializeAuth - Token:', !!token, 'User:', !!user);
        
        if (token && user) {
          console.log('initializeAuth - Hay token y usuario, verificando token...');
          
          // SIEMPRE verificar el token antes de establecer la sesión
          try {
            set({ verifying: true, loading: true });
            
            // Verificar token obteniendo el perfil del usuario
            const userData = await authService.getCurrentUser();
            console.log('initializeAuth - Token válido, usuario:', userData.email);
            
            // Actualizar información del usuario con datos del servidor
            const userInfo = {
              id: userData.id,
              email: userData.email,
              first_name: userData.first_name,
              last_name: userData.last_name,
              full_name: userData.full_name,
              role: userData.role,
              is_active: userData.is_active,
              is_temp_password: userData.is_temp_password,
              team_id: userData.team_id,
              team_name: userData.team_name
            };
            
            // Guardar en ambos lugares para compatibilidad
            localStorage.setItem('user', JSON.stringify(userInfo));
            localStorage.setItem('hps_user', JSON.stringify(userInfo));
            
            // Si la verificación es exitosa, establecer sesión
            console.log('initializeAuth - Token válido, estableciendo sesión');
            set({
              isAuthenticated: true,
              user: userInfo,
              token: token,
              loading: false,
              verifying: false,
              error: null,
              showChangePasswordModal: userInfo.is_temp_password || false
            });
            
            // Limpiar chat al inicializar autenticación para evitar mensajes duplicados
            const chatStore = (await import('./chatStore')).default;
            chatStore.getState().clearChatCompletely();
            
          } catch (error) {
            console.log('initializeAuth - Token inválido o error:', error);
            
            // Si el token es inválido, limpiar todo (ambos sistemas)
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('user');
            localStorage.removeItem('hps_token');
            localStorage.removeItem('hps_refresh_token');
            localStorage.removeItem('hps_user');
            localStorage.removeItem('hps_saved_email'); // Limpiar email guardado también
            
            set({
              isAuthenticated: false,
              user: null,
              token: null,
              loading: false,
              verifying: false,
              error: null,
              showChangePasswordModal: false
            });
          }
        } else {
          // No hay token o usuario, estado no autenticado
          console.log('initializeAuth - No hay token o usuario, estado no autenticado');
          set({
            isAuthenticated: false,
            user: null,
            token: null,
            loading: false,
            verifying: false,
            error: null,
            showChangePasswordModal: false
          });
        }
        
        console.log('initializeAuth - Finalizado');
      },

      // Limpiar errores
      clearError: () => {
        set({ error: null, errorType: null });
      },

      // Utilidades del usuario
      isAdmin: () => {
        const user = get().user;
        return user?.role === 'admin';
      },

      isTeamLeader: () => {
        const user = get().user;
        const role = user?.role || user?.role_name;
        console.log('isTeamLeader - User role:', role);
        return role === 'team_leader' || role === 'team_lead';
      },

      isSecurityChief: () => {
        const user = get().user;
        const role = user?.role || user?.role_name;
        console.log('isSecurityChief - User role:', role);
        return role === 'jefe_seguridad' || role === 'security_chief';
      },

      isCrypto: () => {
        const user = get().user;
        const role = user?.role || user?.role_name;
        console.log('isCrypto - User role:', role);
        return role === 'crypto';
      },

      canManageUsers: () => {
        const user = get().user;
        const role = user?.role || user?.role_name;
        return role === 'admin' || role === 'team_leader' || role === 'team_lead' || role === 'jefe_seguridad' || role === 'security_chief';
      },

      getUserRole: () => {
        return get().user?.role || 'guest';
      },

      getUserName: () => {
        const user = get().user;
        return user?.full_name || user?.email || 'Usuario';
      }
    })
  // } // Comentado temporalmente para debug
  // ,{
  //   name: 'hps-auth-store',
  //   partialize: (state) => ({
  //     isAuthenticated: state.isAuthenticated,
  //     user: state.user,
  //     token: state.token
  //   })
  // }
);

export default useAuthStore;
export { useAuthStore };
