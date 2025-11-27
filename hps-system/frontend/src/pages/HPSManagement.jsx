/**
 * Componente principal para gestión de solicitudes HPS
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DocumentTextIcon, ClockIcon, CheckCircleIcon, XCircleIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';
import hpsService from '../services/hpsService';
import useAuthStore from '../store/authStore';
// import HPSForm from '../components/HPSForm'; // Removido - ahora en página independiente
import HPSList from '../components/HPSList';

const HPSManagement = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  // Removido activeTab - ya no hay pestañas
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Cargar estadísticas al montar el componente
  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setLoading(true);
    const result = await hpsService.getStats();
    
    if (result.success && result.data) {
      setStats(result.data);
      setError('');
    } else {
      setError(result.error || 'Error al cargar las estadísticas');
      setStats(null);
    }
    setLoading(false);
  };

  // Removido handleFormSuccess - ya no hay formulario en esta página

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando solicitudes HPS...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <XCircleIcon className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <p className="text-red-600">{error}</p>
          <button 
            onClick={loadStats}
            className="mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Reintentar
          </button>
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
                Estado HPS
              </h1>
              <p className="text-sm text-gray-600">
                Ver estado de solicitudes y traspasos HPS
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

      <main className="w-full px-4 sm:px-6 lg:px-8 py-8">
        {/* Estadísticas */}
        {stats && (
          <div className="mb-8">
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-6 gap-3">
            <div className="bg-white overflow-hidden shadow rounded-lg p-3">
              <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <DocumentTextIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <div className="ml-3 w-0 flex-1">
                    <dl>
                      <dt className="text-xs font-medium text-gray-500 truncate">
                        Total
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {stats.total_requests}
                      </dd>
                    </dl>
                  </div>
                </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg p-3">
              <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <ClockIcon className="h-5 w-5 text-yellow-400" />
                  </div>
                  <div className="ml-3 w-0 flex-1">
                    <dl>
                      <dt className="text-xs font-medium text-gray-500 truncate">
                        Pendientes
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {stats.pending_requests}
                      </dd>
                    </dl>
                  </div>
                </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg p-3">
              <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <ClockIcon className="h-5 w-5 text-orange-400" />
                  </div>
                  <div className="ml-3 w-0 flex-1">
                    <dl>
                      <dt className="text-xs font-medium text-gray-500 truncate">
                        Esperando DPS
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {stats.waiting_dps_requests}
                      </dd>
                    </dl>
                  </div>
                </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg p-3">
              <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <ClockIcon className="h-5 w-5 text-blue-400" />
                  </div>
                  <div className="ml-3 w-0 flex-1">
                    <dl>
                      <dt className="text-xs font-medium text-gray-500 truncate">
                        Enviadas
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {stats.submitted_requests}
                      </dd>
                    </dl>
                  </div>
                </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg p-3">
              <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <CheckCircleIcon className="h-5 w-5 text-green-400" />
                  </div>
                  <div className="ml-3 w-0 flex-1">
                    <dl>
                      <dt className="text-xs font-medium text-gray-500 truncate">
                        Aprobadas
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {stats.approved_requests}
                      </dd>
                    </dl>
                  </div>
                </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg p-3">
              <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <XCircleIcon className="h-5 w-5 text-red-400" />
                  </div>
                  <div className="ml-3 w-0 flex-1">
                    <dl>
                      <dt className="text-xs font-medium text-gray-500 truncate">
                        Rechazadas
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {stats.rejected_requests}
                      </dd>
                    </dl>
                  </div>
                </div>
            </div>
            </div>
          </div>
        )}

        {/* Lista de Solicitudes */}
        <div className="bg-white shadow rounded-lg w-full p-6">
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 flex items-center">
              <DocumentTextIcon className="h-5 w-5 mr-2" />
              Lista de Solicitudes HPS
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Gestión y seguimiento de todas las solicitudes de Habilitación Personal de Seguridad
            </p>
          </div>

          <HPSList onStatsUpdate={loadStats} />
        </div>
      </main>
    </div>
  );
};

export default HPSManagement;
