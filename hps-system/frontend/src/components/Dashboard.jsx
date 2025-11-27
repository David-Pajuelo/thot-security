// Dashboard principal del sistema HPS
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import { userService } from '../services/apiService';
import hpsService from '../services/hpsService';
import {
  UserGroupIcon,
  ChartBarIcon,
  CogIcon,
  ChatBubbleLeftRightIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';

const Dashboard = () => {
  const navigate = useNavigate();
  const { user, logout, getUserName, isAdmin, isTeamLeader, isSecurityChief, canManageUsers } = useAuthStore();
  
  // Debug: verificar el rol del usuario
  console.log('Dashboard - User:', user);
  console.log('Dashboard - User role:', user?.role);
  console.log('Dashboard - User role_name:', user?.role_name);
  console.log('Dashboard - isTeamLeader():', isTeamLeader());
  console.log('Dashboard - isAdmin():', isAdmin());
  console.log('Dashboard - isSecurityChief():', isSecurityChief());
  console.log('Dashboard - canManageUsers():', canManageUsers());
  const [stats, setStats] = useState(null);
  const [hpsStats, setHpsStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, [canManageUsers]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadDashboardData = async () => {
    try {
      // Cargar estadísticas de usuarios (solo si puede gestionarlos)
      if (canManageUsers()) {
        const userStats = await userService.getStats();
        setStats(userStats);
      }

      // Cargar estadísticas de HPS (todos los roles excepto miembros)
      const userRole = user?.role;
      if (userRole && userRole !== 'member') {
        const hpsResult = await hpsService.getStats();
        if (hpsResult.success) {
          setHpsStats(hpsResult.data);
        }
      }

    } catch (error) {
      console.error('Error cargando datos del dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Error en logout:', error);
    }
  };

  const menuItems = [
    {
      name: 'Gestión de Usuarios',
      description: 'Administrar usuarios del sistema',
      icon: UserGroupIcon,
      path: '/users',
      color: 'bg-blue-500',
      visible: isAdmin() || isSecurityChief()
    },
    {
      name: 'Mi Equipo',
      description: 'Gestionar miembros y HPS de tu equipo',
      icon: UserGroupIcon,
      path: '/team',
      color: 'bg-indigo-500',
      visible: isTeamLeader()
    },
    {
      name: 'Estado HPS',
      description: 'Ver estado de solicitudes y traspasos HPS',
      icon: DocumentTextIcon,
      path: '/hps',
      color: 'bg-green-500',
      visible: true
    },
    {
      name: 'Gestión de Plantillas',
      description: 'Administrar plantillas PDF para traspasos',
      icon: DocumentTextIcon,
      path: '/templates',
      color: 'bg-purple-500',
      visible: isAdmin()
    },
    {
      name: 'Chat IA',
      description: 'Asistente virtual del sistema',
      icon: ChatBubbleLeftRightIcon,
      path: '/chat',
      color: 'bg-purple-500',
      visible: true
    },
    {
      name: 'Monitoreo Chat IA',
      description: 'Observabilidad del agente IA',
      icon: ChatBubbleLeftRightIcon,
      path: '/reports',
      color: 'bg-purple-500',
      visible: isAdmin()
    },
    {
      name: 'Configuración',
      description: 'Ajustes del sistema',
      icon: CogIcon,
      path: '/settings',
      color: 'bg-gray-500',
      visible: isAdmin()
    }
  ].filter(item => item.visible);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
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
              <h1 className="text-3xl font-bold text-gray-900">
                Sistema HPS
              </h1>
              <p className="text-sm text-gray-600">
                Habilitación Personal de Seguridad
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">
                  {getUserName()}
                </p>
                <p className="text-xs text-gray-600 capitalize">
                  {user?.role?.replace('_', ' ')}
                </p>
              </div>
              
              <button
                onClick={handleLogout}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Cerrar Sesión
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="w-full px-4 sm:px-6 lg:px-8 py-8">


        {/* Estadísticas de Usuarios (solo para usuarios con permisos) */}
        {stats && (
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Estadísticas de Usuarios</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
              <div className="bg-white rounded-lg shadow-sm border p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <UserGroupIcon className="h-4 w-4 text-gray-400 mr-2" />
                    <span className="text-xs text-gray-500">Total</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {stats.total_users}
                  </span>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="h-3 w-3 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-500">Activos</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {stats.active_users}
                  </span>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="h-3 w-3 bg-yellow-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-500">Crypto</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {stats.crypto || 0}
                  </span>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="h-3 w-3 bg-blue-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-500">Líderes</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {stats.team_leaders}
                  </span>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="h-3 w-3 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-500">Miembros</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {stats.members || 0}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Estadísticas de HPS - Solo para roles que no sean miembros */}
        {hpsStats && user?.role !== 'member' && (
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Estadísticas de Solicitudes HPS</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="bg-white rounded-lg shadow-sm border p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <DocumentTextIcon className="h-4 w-4 text-gray-400 mr-2" />
                    <span className="text-xs text-gray-500">Total</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {hpsStats.total_requests}
                  </span>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="h-3 w-3 bg-yellow-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-500">Pendientes</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {hpsStats.pending_requests}
                  </span>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="h-3 w-3 bg-orange-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-500">En espera DPS</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {hpsStats.waiting_dps_requests}
                  </span>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="h-3 w-3 bg-blue-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-500">Enviadas</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {hpsStats.submitted_requests}
                  </span>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="h-3 w-3 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-500">Aprobadas</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {hpsStats.approved_requests}
                  </span>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="h-3 w-3 bg-red-500 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-500">Rechazadas</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {hpsStats.rejected_requests}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Menú de navegación */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.name}
                onClick={() => {
                  console.log(`Dashboard - Haciendo clic en: ${item.name}`);
                  console.log(`Dashboard - Navegando a: ${item.path}`);
                  console.log(`Dashboard - Usuario actual:`, user);
                  console.log(`Dashboard - isSecurityChief():`, isSecurityChief());
                  navigate(item.path);
                }}
                className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow duration-200 text-left group"
              >
                <div className="flex items-center mb-4">
                  <div className={`p-3 rounded-lg ${item.color}`}>
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                </div>
                <h3 className="text-lg font-medium text-gray-900 group-hover:text-blue-600 transition-colors">
                  {item.name}
                </h3>
                <p className="text-sm text-gray-500 mt-1">
                  {item.description}
                </p>
              </button>
            );
          })}
        </div>

        {/* Estado del sistema - Solo para administradores (al final) */}
        {isAdmin() && (
          <div className="mt-8 bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Estado del Sistema
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center">
                <div className="h-3 w-3 bg-green-400 rounded-full mr-3"></div>
                <span className="text-sm text-gray-600">API Backend: Conectado</span>
              </div>
              <div className="flex items-center">
                <div className="h-3 w-3 bg-green-400 rounded-full mr-3"></div>
                <span className="text-sm text-gray-600">Base de Datos: Operativa</span>
              </div>
              <div className="flex items-center">
                <div className="h-3 w-3 bg-yellow-400 rounded-full mr-3"></div>
                <span className="text-sm text-gray-600">Agente IA: En desarrollo</span>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  );
};

export default Dashboard;
