import { useEffect, useRef } from 'react';
import { useAuthStore } from '../store/authStore';

/**
 * Hook para manejar la persistencia de sesión del usuario
 * Verifica el token periódicamente y mantiene la sesión activa
 */
export const useSessionPersistence = () => {
  const { isAuthenticated, checkAndRefreshToken, logout } = useAuthStore();
  const intervalRef = useRef(null);

  useEffect(() => {
    // Verificar sesión cada 2 horas si está autenticado (alineado con lifetime del access token)
    const SESSION_CHECK_MINUTES = 120;
    if (isAuthenticated) {
      console.log('useSessionPersistence - Iniciando verificación automática de sesión');
      
      // Verificar inmediatamente
      checkAndRefreshToken();
      
      // Configurar verificación periódica cada 2 horas
      intervalRef.current = setInterval(async () => {
        console.log('useSessionPersistence - Verificación periódica de sesión');
        const isValid = await checkAndRefreshToken();
        if (!isValid) {
          console.log('useSessionPersistence - Sesión inválida, limpiando intervalo');
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }, SESSION_CHECK_MINUTES * 60 * 1000);
    } else {
      // Limpiar intervalo si no está autenticado
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
    
    // Cleanup al desmontar
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isAuthenticated, checkAndRefreshToken, logout]);

  // Función para verificar la sesión manualmente
  const checkSession = async () => {
    if (isAuthenticated) {
      try {
        const isValid = await checkAndRefreshToken();
        return isValid;
      } catch (error) {
        console.error('Error verificando sesión manualmente:', error);
        return false;
      }
    }
    return false;
  };

  return { checkSession };
};







