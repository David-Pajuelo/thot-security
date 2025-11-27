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
    // Verificar sesión cada 5 minutos si está autenticado
    if (isAuthenticated) {
      console.log('useSessionPersistence - Iniciando verificación automática de sesión');
      
      // Verificar inmediatamente
      checkAndRefreshToken();
      
      // Configurar verificación periódica cada 5 minutos
      intervalRef.current = setInterval(async () => {
        console.log('useSessionPersistence - Verificación periódica de sesión');
        const isValid = await checkAndRefreshToken();
        if (!isValid) {
          console.log('useSessionPersistence - Sesión inválida, limpiando intervalo');
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }, 5 * 60 * 1000); // 5 minutos
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







