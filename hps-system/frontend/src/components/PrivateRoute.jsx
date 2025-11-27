// Componente para proteger rutas que requieren autenticación
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import useAuthStore from '../store/authStore';

const PrivateRoute = ({ 
  children, 
  requiredRole = null,
  requireAuth = true 
}) => {
  const { isAuthenticated, user, loading, verifying } = useAuthStore();
  const location = useLocation();

  // Debug logs
  console.log('PrivateRoute - Estado:', { isAuthenticated, user, loading, verifying, requiredRole, requireAuth });

  // Si está cargando o verificando, mostrar spinner
  if (loading || verifying) {
    console.log('PrivateRoute - Mostrando spinner (loading/verifying)');
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Si requiere autenticación y no está autenticado
  if (requireAuth && !isAuthenticated) {
    console.log('PrivateRoute - No autenticado, redirigiendo a login');
    // Limpiar cualquier dato residual de localStorage
    localStorage.removeItem('hps_token');
    localStorage.removeItem('hps_user');
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Si requiere un rol específico
  if (requiredRole) {
    // Obtener el rol del usuario (puede ser 'role' o 'role_name')
    const userRole = user?.role || user?.role_name;
    
    // Si es admin, puede acceder a todo
    if (userRole === 'admin') {
      return children;
    }
    
    // Si es team_leader y el rol requerido es member, puede acceder
    if (userRole === 'team_leader' && requiredRole === 'member') {
      return children;
    }
    
    // Si el rol coincide exactamente
    if (userRole === requiredRole) {
      return children;
    }
    
    // Si es team_lead y el rol requerido es team_leader, puede acceder
    if (userRole === 'team_lead' && requiredRole === 'team_leader') {
      return children;
    }
    
    // En caso contrario, acceso denegado
    console.log('PrivateRoute - Acceso denegado por rol, redirigiendo a /unauthorized');
    return <Navigate to="/unauthorized" replace />;
  }

  console.log('PrivateRoute - Acceso permitido');
  return children;
};

// Componente específico para solo admins
export const AdminRoute = ({ children }) => {
  return (
    <PrivateRoute requiredRole="admin">
      {children}
    </PrivateRoute>
  );
};

// Componente específico para admins y team leaders
export const ManagerRoute = ({ children }) => {
  const { user, loading, verifying } = useAuthStore();
  
  // Debug logs
  console.log('ManagerRoute - Estado:', { user, loading, verifying });
  
  // Si está cargando o verificando, mostrar spinner
  if (loading || verifying) {
    console.log('ManagerRoute - Mostrando spinner (loading/verifying)');
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  // Obtener el rol del usuario (puede ser 'role' o 'role_name')
  const userRole = user?.role || user?.role_name;
  console.log('ManagerRoute - Rol del usuario:', userRole);
  
  if (!user || (userRole !== 'admin' && userRole !== 'team_leader')) {
    console.log('ManagerRoute - Acceso denegado, redirigiendo a /unauthorized');
    return <Navigate to="/unauthorized" replace />;
  }
  
  console.log('ManagerRoute - Acceso permitido');
  return children;
};

// Componente específico para admins y jefes de seguridad
export const AdminSecurityRoute = ({ children }) => {
  const { user, loading, verifying } = useAuthStore();
  
  // Debug logs
  console.log('AdminSecurityRoute - Estado:', { user, loading, verifying });
  
  // Si está cargando o verificando, mostrar spinner
  if (loading || verifying) {
    console.log('AdminSecurityRoute - Mostrando spinner (loading/verifying)');
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  // Obtener el rol del usuario (puede ser 'role' o 'role_name')
  const userRole = user?.role || user?.role_name;
  console.log('AdminSecurityRoute - Usuario completo:', user);
  console.log('AdminSecurityRoute - user.role:', user?.role);
  console.log('AdminSecurityRoute - user.role_name:', user?.role_name);
  console.log('AdminSecurityRoute - Rol del usuario:', userRole);
  
  if (!user || (userRole !== 'admin' && userRole !== 'jefe_seguridad' && userRole !== 'security_chief')) {
    console.log('AdminSecurityRoute - Acceso denegado, redirigiendo a /unauthorized');
    console.log('AdminSecurityRoute - Razón: usuario no válido o rol no permitido');
    console.log('AdminSecurityRoute - Roles permitidos: admin, jefe_seguridad, security_chief');
    return <Navigate to="/unauthorized" replace />;
  }
  
  console.log('AdminSecurityRoute - Acceso permitido');
  return children;
};

// Componente para rutas públicas (cuando NO debe estar autenticado)
export const PublicRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  
  if (isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }
  
  return children;
};

export default PrivateRoute;

