import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';
import { useAuthStore } from './store/authStore';
import { useSessionPersistence } from './hooks/useSessionPersistence';
import PrivateRoute, { PublicRoute, AdminRoute, AdminSecurityRoute } from './components/PrivateRoute';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import ChangePasswordModal from './components/ChangePasswordModal';

import './App.css';

// Nota: La sincronización de tokens se hace mediante iframe + postMessage
// en lugar de BroadcastChannel, ya que BroadcastChannel no funciona
// entre diferentes orígenes (localhost:3001 y localhost:3000)

// Componentes de páginas
import UserManagement from './pages/UserManagement';
import TeamManagement from './pages/TeamManagement';
import HPSManagement from './pages/HPSManagement';
import HPSFormPage from './pages/HPSFormPage';
import ChatPage from './pages/ChatPage';
import ChatMonitoringPage from './pages/ChatMonitoringPage';
import TemplateManagement from './pages/TemplateManagement';
import HPSTransferPage from './pages/HPSTransferPage';
import TestWidth from './pages/TestWidth';
import CompareWidth from './pages/CompareWidth';

// Componente para redirección basada en roles
const RoleBasedRedirect = ({ isAuthenticated, user }) => {
  console.log('RoleBasedRedirect - Props:', { isAuthenticated, user });
  
  if (!isAuthenticated) {
    console.log('RoleBasedRedirect - No autenticado, redirigiendo a login');
    return <Navigate to="/login" replace />;
  }
  
  // Redirección basada en el rol del usuario
  const userRole = (user?.role_name || user?.role)?.toLowerCase();
  console.log('RoleBasedRedirect - Rol del usuario:', userRole);
  
  // Todos los usuarios van al Chat IA por defecto
  console.log('RoleBasedRedirect - Redirigiendo usuario a chat');
  return <Navigate to="/chat" replace />;
};

// Reports component moved to ReportsPage.jsx

const Settings = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Configuración
              </h1>
              <p className="text-sm text-gray-600">
                Panel de administración
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center"
              >
                <ArrowLeftIcon className="h-4 w-4 mr-2" />
                Volver al Dashboard
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Contenido */}
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="text-center">
            <p className="text-gray-600">Contenido de configuración</p>
          </div>
        </div>
      </div>
    </div>
  );
};

const Unauthorized = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center">
      <div className="mx-auto h-16 w-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
        <svg className="h-8 w-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Acceso Denegado</h1>
      <p className="text-gray-600 mb-4">No tienes permisos para acceder a esta página</p>
      <button 
        onClick={() => window.history.back()}
        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md"
      >
        Volver
      </button>
    </div>
  </div>
);

// Componente interno para manejar el modal de cambio de contraseña
// Debe estar dentro del Router para usar useLocation
const ChangePasswordModalWrapper = () => {
  const location = useLocation();
  const { 
    isAuthenticated, 
    user, 
    showChangePasswordModal, 
    closeChangePasswordModal 
  } = useAuthStore();
  
  // Rutas públicas donde NO se debe mostrar el modal de cambio de contraseña
  const publicRoutes = ['/login', '/hps-form'];
  const isPublicRoute = publicRoutes.some(route => location.pathname.startsWith(route));
  
  // Solo mostrar el modal si está autenticado Y NO está en una ruta pública
  if (!isAuthenticated || isPublicRoute) {
    return null;
  }
  
  return (
    <ChangePasswordModal
      isOpen={showChangePasswordModal}
      onClose={closeChangePasswordModal}
      isRequired={user?.is_temp_password || false}
    />
  );
};

function App() {
  const { 
    initializeAuth, 
    isAuthenticated, 
    loading, 
    verifying, 
    user, 
    showChangePasswordModal, 
    closeChangePasswordModal 
  } = useAuthStore();
  const [isInitialized, setIsInitialized] = React.useState(false);
  
  // Usar el hook de persistencia de sesión
  useSessionPersistence();

  // Inicializar autenticación al cargar la app
  useEffect(() => {
    const initAuth = async () => {
      console.log('App - Iniciando autenticación...');
      await initializeAuth();
      console.log('App - Autenticación inicializada');
      setIsInitialized(true);
    };
    initAuth();
  }, [initializeAuth]);

  // Debug: mostrar estado de autenticación
  console.log('App State:', { isAuthenticated, loading, verifying, user, isInitialized });

  // Mostrar loading durante inicialización o verificación
  if (!isInitialized || loading || verifying) {
    console.log('App - Mostrando loading:', { isInitialized, loading, verifying });
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">
            {verifying ? 'Verificando sesión...' : 'Cargando Sistema HPS...'}
          </p>
        </div>
      </div>
    );
  }

  console.log('App - Renderizando aplicación principal');

  return (
    <Router>
      <div className="App">
        {/* Componente de debug temporal */}

        <Routes>
          {/* Ruta raíz - redirigir según autenticación y rol */}
          <Route 
            path="/" 
            element={<RoleBasedRedirect isAuthenticated={isAuthenticated} user={user} />} 
          />
          
          {/* Rutas públicas */}
          <Route 
            path="/login" 
            element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            } 
          />
          
          {/* Formulario HPS - Acceso público */}
          <Route 
            path="/hps-form" 
            element={<HPSFormPage />}
          />
          
          {/* Traspaso HPS - Acceso público */}
          <Route 
            path="/hps-transfer/:transferId" 
            element={<HPSTransferPage />}
          />
          
          {/* Rutas protegidas */}
          <Route 
            path="/dashboard" 
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            } 
          />
          
          <Route 
            path="/users" 
            element={
              <AdminSecurityRoute>
                <UserManagement />
              </AdminSecurityRoute>
            } 
          />
          
          <Route 
            path="/team" 
            element={
              <PrivateRoute requiredRole="team_leader">
                <TeamManagement />
              </PrivateRoute>
            } 
          />
          
          <Route 
            path="/hps" 
            element={
              <PrivateRoute>
                <HPSManagement />
              </PrivateRoute>
            } 
          />
          
          <Route 
            path="/templates" 
            element={
              <AdminRoute>
                <TemplateManagement />
              </AdminRoute>
            } 
          />
          
          <Route 
            path="/chat" 
            element={
              <PrivateRoute>
                <ChatPage />
              </PrivateRoute>
            } 
          />

          <Route 
            path="/test-width" 
            element={
              <PrivateRoute>
                <TestWidth />
              </PrivateRoute>
            } 
          />

          <Route 
            path="/compare-width" 
            element={
              <PrivateRoute>
                <CompareWidth />
              </PrivateRoute>
            } 
          />

          <Route 
            path="/reports" 
            element={
              <AdminRoute>
                <ChatMonitoringPage />
              </AdminRoute>
            } 
          />

          
          <Route 
            path="/settings" 
            element={
              <AdminRoute>
                <Settings />
              </AdminRoute>
            } 
          />
          
          {/* Ruta de acceso denegado */}
          <Route 
            path="/unauthorized" 
            element={<Unauthorized />} 
          />
          
          {/* Ruta 404 */}
          <Route 
            path="*" 
            element={
              <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                  <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
                  <p className="text-gray-600 mb-4">Página no encontrada</p>
                  <button 
                    onClick={() => window.history.back()}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md"
                  >
                    Volver
                  </button>
                </div>
              </div>
            } 
          />
        </Routes>
      </div>
      
      {/* Modal de cambio de contraseña - Solo mostrar si está autenticado Y NO está en una ruta pública */}
      <ChangePasswordModalWrapper />
    </Router>
  );
}

export default App;
