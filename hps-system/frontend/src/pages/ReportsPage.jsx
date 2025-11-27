import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../store/authStore';
import { userService, hpsService } from '../services/apiService';
import {
  ChartBarIcon,
  UserGroupIcon,
  ClockIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  ArrowDownTrayIcon,
  CalendarIcon,
  EyeIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';

const ReportsPage = () => {
  const { user, canManageUsers } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [reports, setReports] = useState({
    generalStats: null,
    userAudit: [],
    pendingRequests: [],
    activityLog: [],
    teamStats: null
  });
  const [selectedPeriod, setSelectedPeriod] = useState('30'); // días
  const [selectedReport, setSelectedReport] = useState('overview');

  useEffect(() => {
    if (canManageUsers) {
      loadAllReports();
    }
  }, [canManageUsers, selectedPeriod]);

  const loadAllReports = async () => {
    setLoading(true);
    try {
      const [generalStats, userAudit, pendingRequests, activityLog, teamStats] = await Promise.all([
        loadGeneralStats(),
        loadUserAudit(),
        loadPendingRequests(),
        loadActivityLog(),
        loadTeamStats()
      ]);

      setReports({
        generalStats,
        userAudit,
        pendingRequests,
        activityLog,
        teamStats
      });
    } catch (error) {
      console.error('Error cargando reportes:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadGeneralStats = async () => {
    try {
      const hpsStats = await hpsService.getHPSStats();
      const userStats = await userService.getUserStats();
      
      return {
        hps: hpsStats,
        users: userStats,
        period: selectedPeriod
      };
    } catch (error) {
      console.error('Error cargando estadísticas generales:', error);
      return null;
    }
  };

  const loadUserAudit = async () => {
    try {
      // Simular datos de auditoría de usuarios eliminados
      return [
        {
          id: 1,
          user_email: 'carlos.alonso@techex.es',
          deleted_by: 'admin@hps-system.com',
          deleted_at: '2025-01-05T10:30:00Z',
          hps_deleted: 0,
          tokens_deleted: 0,
          reason: 'Usuario inactivo'
        },
        {
          id: 2,
          user_email: 'usuario.test@example.com',
          deleted_by: 'admin@hps-system.com',
          deleted_at: '2025-01-04T15:45:00Z',
          hps_deleted: 2,
          tokens_deleted: 1,
          reason: 'Solicitud del usuario'
        }
      ];
    } catch (error) {
      console.error('Error cargando auditoría de usuarios:', error);
      return [];
    }
  };

  const loadPendingRequests = async () => {
    try {
      const response = await hpsService.getHPSRequests({ status: 'pending' });
      return response.requests || [];
    } catch (error) {
      console.error('Error cargando solicitudes pendientes:', error);
      return [];
    }
  };

  const loadActivityLog = async () => {
    try {
      // Simular log de actividades
      return [
        {
          id: 1,
          action: 'Usuario eliminado',
          user: 'admin@hps-system.com',
          target: 'carlos.alonso@techex.es',
          timestamp: '2025-01-05T10:30:00Z',
          details: 'Solicitudes HPS eliminadas: 0, Tokens eliminados: 0'
        },
        {
          id: 2,
          action: 'Solicitud HPS creada',
          user: 'calonso@aicox.com',
          target: 'Nueva solicitud',
          timestamp: '2025-01-05T09:15:00Z',
          details: 'Tipo: Nueva, Estado: Pendiente'
        },
        {
          id: 3,
          action: 'Token HPS generado',
          user: 'admin@hps-system.com',
          target: 'Formulario público',
          timestamp: '2025-01-05T08:45:00Z',
          details: 'Token expira en 24 horas'
        }
      ];
    } catch (error) {
      console.error('Error cargando log de actividades:', error);
      return [];
    }
  };

  const loadTeamStats = async () => {
    try {
      const users = await userService.getUsers();
      const teams = {};
      
      users.users?.forEach(user => {
        const teamName = user.team?.name || 'Sin equipo';
        if (!teams[teamName]) {
          teams[teamName] = { total: 0, active: 0, inactive: 0 };
        }
        teams[teamName].total++;
        if (user.is_active) {
          teams[teamName].active++;
        } else {
          teams[teamName].inactive++;
        }
      });

      return teams;
    } catch (error) {
      console.error('Error cargando estadísticas de equipos:', error);
      return null;
    }
  };

  const exportReport = (reportType) => {
    // Simular exportación
    const data = reports[reportType];
    const csvContent = convertToCSV(data);
    downloadCSV(csvContent, `${reportType}_${new Date().toISOString().split('T')[0]}.csv`);
  };

  const convertToCSV = (data) => {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvRows = [
      headers.join(','),
      ...data.map(row => headers.map(header => JSON.stringify(row[header] || '')).join(','))
    ];
    
    return csvRows.join('\n');
  };

  const downloadCSV = (content, filename) => {
    const blob = new Blob([content], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('es-ES');
  };

  if (!canManageUsers) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="h-16 w-16 text-red-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Acceso Denegado</h1>
          <p className="text-gray-600">No tienes permisos para acceder a los reportes</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Cargando reportes...</p>
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
              <h1 className="text-3xl font-bold text-gray-900">
                Reportes del Sistema
              </h1>
              <p className="mt-2 text-gray-600">
                Análisis y estadísticas del sistema HPS
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="7">Últimos 7 días</option>
                <option value="30">Últimos 30 días</option>
                <option value="90">Últimos 90 días</option>
                <option value="365">Último año</option>
              </select>
              <button
                onClick={() => window.history.back()}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md flex items-center"
              >
                ← Volver al Dashboard
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="w-full px-4 sm:px-6 lg:px-8 py-8">
        {/* Navegación de reportes */}
        <div className="mb-8">
          <nav className="flex space-x-8">
            {[
              { id: 'overview', name: 'Resumen General', icon: ChartBarIcon },
              { id: 'users', name: 'Usuarios', icon: UserGroupIcon },
              { id: 'requests', name: 'Solicitudes', icon: DocumentTextIcon },
              { id: 'audit', name: 'Auditoría', icon: EyeIcon },
              { id: 'activity', name: 'Actividad', icon: ClockIcon }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setSelectedReport(tab.id)}
                className={`flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                  selectedReport === tab.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <tab.icon className="h-5 w-5 mr-2" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Contenido de reportes */}
        {selectedReport === 'overview' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">Resumen General</h2>
            
            {/* Estadísticas principales */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <DocumentTextIcon className="h-8 w-8 text-blue-500" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Total Solicitudes</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {reports.generalStats?.hps?.total_requests || 0}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <UserGroupIcon className="h-8 w-8 text-green-500" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Usuarios Activos</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {reports.generalStats?.users?.active_users || 0}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <ClockIcon className="h-8 w-8 text-yellow-500" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Pendientes</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {reports.generalStats?.hps?.pending_requests || 0}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <CheckCircleIcon className="h-8 w-8 text-green-500" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Aprobadas</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {reports.generalStats?.hps?.approved_requests || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Gráfico de tendencias */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Tendencias de Solicitudes</h3>
              <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
                <p className="text-gray-500">Gráfico de tendencias (implementar con Chart.js)</p>
              </div>
            </div>
          </div>
        )}

        {selectedReport === 'users' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">Reporte de Usuarios</h2>
              <button
                onClick={() => exportReport('userAudit')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center"
              >
                <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
                Exportar CSV
              </button>
            </div>

            {/* Estadísticas por equipo */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Distribución por Equipos</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Equipo
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Total
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Activos
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Inactivos
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {reports.teamStats && Object.entries(reports.teamStats).map(([team, stats]) => (
                      <tr key={team}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {team}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {stats.total}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                          {stats.active}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                          {stats.inactive}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {selectedReport === 'requests' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">Solicitudes Pendientes</h2>
              <button
                onClick={() => exportReport('pendingRequests')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center"
              >
                <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
                Exportar CSV
              </button>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Usuario
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tipo
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Estado
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Creado
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Acciones
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {reports.pendingRequests.map((request) => (
                      <tr key={request.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            {request.email}
                          </div>
                          <div className="text-sm text-gray-500">
                            {request.first_name} {request.first_last_name}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {request.request_type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                            {request.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(request.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button className="text-blue-600 hover:text-blue-900 mr-3">
                            <EyeIcon className="h-5 w-5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {selectedReport === 'audit' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">Auditoría de Usuarios Eliminados</h2>
              <button
                onClick={() => exportReport('userAudit')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center"
              >
                <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
                Exportar CSV
              </button>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Usuario Eliminado
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Eliminado por
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Fecha
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        HPS Eliminadas
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tokens Eliminados
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Motivo
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {reports.userAudit.map((audit) => (
                      <tr key={audit.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {audit.user_email}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {audit.deleted_by}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(audit.deleted_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                          {audit.hps_deleted}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                          {audit.tokens_deleted}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {audit.reason}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {selectedReport === 'activity' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">Log de Actividades</h2>
              <button
                onClick={() => exportReport('activityLog')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center"
              >
                <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
                Exportar CSV
              </button>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Acción
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Usuario
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Objetivo
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Fecha
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Detalles
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {reports.activityLog.map((activity) => (
                      <tr key={activity.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {activity.action}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {activity.user}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {activity.target}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(activity.timestamp)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {activity.details}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default ReportsPage;





