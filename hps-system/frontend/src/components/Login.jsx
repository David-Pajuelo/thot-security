// Componente de Login para el sistema HPS
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import useAuthStore from '../store/authStore';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import { formatErrorForDisplay } from '../utils/errorHandler';
import { getTokenFromCryptoTrace } from '../utils/tokenSync';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, loading, error, errorType, clearError, isAuthenticated, verifyToken } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    setFocus,
    setValue
  } = useForm();

  // Verificar si hay token desde CryptoTrace al cargar
  useEffect(() => {
    const checkTokenFromCryptoTrace = async () => {
      // Solo verificar si no hay token en localStorage
      const existingToken = localStorage.getItem('accessToken') || localStorage.getItem('hps_token');
      if (!existingToken) {
        console.log('[Login] Verificando token desde CryptoTrace...');
        const token = await getTokenFromCryptoTrace();
        if (token) {
          console.log('[Login] ✅ Token encontrado en CryptoTrace, guardando...');
          localStorage.setItem('accessToken', token);
          localStorage.setItem('hps_token', token); // Compatibilidad
          
          // Verificar el token y obtener el perfil del usuario
          // Esto establecerá la sesión correctamente
          const isValid = await verifyToken();
          
          if (isValid) {
            console.log('[Login] ✅ Token verificado, sesión establecida desde CryptoTrace');
            // Redirigir al dashboard
            const from = location.state?.from?.pathname || '/dashboard';
            navigate(from, { replace: true });
          } else {
            console.log('[Login] ⚠️ Token inválido, limpiando...');
            localStorage.removeItem('accessToken');
            localStorage.removeItem('hps_token');
          }
        }
      }
    };
    
    checkTokenFromCryptoTrace();
  }, [navigate, location]);

  // Redirigir si ya está autenticado
  useEffect(() => {
    if (isAuthenticated) {
      const from = location.state?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  // Solo enfocar el campo email al cargar (sin cargar email guardado)
  useEffect(() => {
    setFocus('email');
  }, [setFocus]);

  // NO cargar email guardado automáticamente - solo usar el que el usuario introdujo
  // Esto previene que se muestre el email de otro usuario

  // Limpiar errores solo cuando el usuario empiece a escribir
  const handleEmailChange = (e) => {
    if (error) {
      clearError();
    }
  };

  const handlePasswordChange = (e) => {
    if (error) {
      clearError();
    }
  };

  const onSubmit = async (data) => {
    console.log('🔄 Intentando login con:', data.email);
    
    try {
      await login(data.email, data.password);
      // Si llegamos aquí, el login fue exitoso
      // La redirección se maneja en el useEffect de isAuthenticated
    } catch (err) {
      console.error('❌ Error en login:', err);
      
      // Mantener el email que el usuario acaba de introducir (ya está en el campo)
      // NO guardar en localStorage para evitar problemas de privacidad entre usuarios
      // El email ya está en el campo del formulario, no necesitamos guardarlo
      
      // El error ya se maneja en el authStore y se mostrará automáticamente
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-blue-600 rounded-full flex items-center justify-center">
            <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Sistema HPS
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Habilitación Personal de Seguridad
          </p>
          <p className="text-xs text-gray-500">
            Inicia sesión con tu cuenta
          </p>
        </div>

        {/* Formulario */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="bg-white p-8 rounded-lg shadow-md space-y-6">
            
            {/* Error Alert */}
            {error && (
              <div className={`border rounded-md p-4 ${
                errorType === 'credentials' ? 'bg-red-50 border-red-200' :
                errorType === 'user_not_found' ? 'bg-yellow-50 border-yellow-200' :
                errorType === 'account_disabled' ? 'bg-orange-50 border-orange-200' :
                errorType === 'network' ? 'bg-blue-50 border-blue-200' :
                'bg-red-50 border-red-200'
              }`}>
                <div className="flex">
                  <div className="flex-shrink-0">
                    {errorType === 'credentials' ? (
                      <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                    ) : errorType === 'user_not_found' ? (
                      <svg className="h-5 w-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    ) : errorType === 'network' ? (
                      <svg className="h-5 w-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
                      </svg>
                    ) : (
                      <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    )}
                  </div>
                  <div className="ml-3">
                    <p className={`text-sm ${
                      errorType === 'credentials' ? 'text-red-800' :
                      errorType === 'user_not_found' ? 'text-yellow-800' :
                      errorType === 'account_disabled' ? 'text-orange-800' :
                      errorType === 'network' ? 'text-blue-800' :
                      'text-red-800'
                    }`}>
                      {formatErrorForDisplay(error)}
                    </p>
                    {errorType === 'credentials' && (
                      <p className="mt-1 text-xs text-red-600">
                        💡 Verifica que el email y contraseña sean correctos
                      </p>
                    )}
                    {errorType === 'user_not_found' && (
                      <p className="mt-1 text-xs text-yellow-600">
                        💡 Asegúrate de que el email esté bien escrito
                      </p>
                    )}
                    {errorType === 'network' && (
                      <p className="mt-1 text-xs text-blue-600">
                        💡 Verifica tu conexión a internet
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Campo Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Correo Electrónico
              </label>
              <input
                {...register('email', {
                  required: 'El email es requerido',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Email inválido'
                  },
                  onChange: handleEmailChange
                })}
                type="email"
                className={`w-full px-3 py-2 border rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white ${
                  errors.email ? 'border-red-300' : 
                  errorType === 'credentials' ? 'border-red-300' :
                  errorType === 'user_not_found' ? 'border-yellow-300' :
                  'border-gray-300'
                }`}
                placeholder="admin@hps-system.com"
                autoComplete="email"
                style={{ color: '#111827' }}
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
              )}
            </div>

            {/* Campo Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Contraseña
              </label>
              <div className="relative">
                <input
                  {...register('password', {
                    required: 'La contraseña es requerida',
                    minLength: {
                      value: 3,
                      message: 'La contraseña debe tener al menos 3 caracteres'
                    },
                    onChange: handlePasswordChange
                  })}
                  type={showPassword ? 'text' : 'password'}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-10 text-gray-900 bg-white ${
                    errors.password ? 'border-red-300' : 
                    errorType === 'credentials' ? 'border-red-300' :
                    'border-gray-300'
                  }`}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  style={{ color: '#111827' }}
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                  ) : (
                    <EyeIcon className="h-5 w-5 text-gray-400" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
              )}
            </div>

            {/* Botón Submit */}
            <button
              type="submit"
              disabled={loading}
              className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                loading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Iniciando sesión...
                </>
              ) : (
                'Iniciar Sesión'
              )}
            </button>
          </div>

          {/* Credenciales de prueba */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-xs text-gray-600 text-center mb-2">
              <strong>Credenciales de prueba:</strong>
            </p>
            <div className="grid grid-cols-1 gap-2 text-xs text-gray-600">
              <div className="text-center">
                <span className="font-medium">Admin:</span> admin@hps-system.com / admin123
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;

