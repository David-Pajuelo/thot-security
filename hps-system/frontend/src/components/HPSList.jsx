/**
 * Componente para listar y gestionar solicitudes HPS
 */
import React, { useState, useEffect } from 'react';
import { 
  EyeIcon, 
  CheckCircleIcon, 
  XCircleIcon, 
  ClockIcon,
  PaperAirplaneIcon,
  TrashIcon,
  DocumentTextIcon,
  ArrowDownTrayIcon,
  PencilIcon,
  CheckIcon
} from '@heroicons/react/24/outline';
import hpsService from '../services/hpsService';
import useAuthStore from '../store/authStore';
import PDFViewerEditor from './PDFViewerEditor';

const HPSList = ({ onStatsUpdate }) => {
  const { user } = useAuthStore();
  const [requests, setRequests] = useState([]);

  // Función auxiliar para obtener el label del tipo de solicitud de forma segura
  const getRequestTypeLabel = (requestType) => {
    const labels = {
      new: 'Nueva',
      renewal: 'Renovación',
      transfer: 'Traspaso'
    };
    return labels[requestType] || requestType || 'No especificado';
  };

  // Función auxiliar para obtener el label del tipo de HPS (solicitud o traslado)
  const getHPSTypeLabel = (hpsType) => {
    const labels = {
      solicitud: 'Solicitud',
      traslado: 'Traspaso'
    };
    return labels[hpsType] || hpsType || 'Solicitud';
  };
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [actionLoading, setActionLoading] = useState('');
  const [isEditingDetails, setIsEditingDetails] = useState(false);
  const [editFormData, setEditFormData] = useState({});
  const [saveLoading, setSaveLoading] = useState(false);
  const [pdfViewerOpen, setPdfViewerOpen] = useState(false);
  const [viewingHpsId, setViewingHpsId] = useState(null);
  
  // Filtros
  const [filters, setFilters] = useState({
    status: '',
    hps_type: '',
    page: 1,
    per_page: 10
  });
  
  const [pagination, setPagination] = useState({
    total: 0,
    pages: 0,
    current_page: 1
  });

  useEffect(() => {
    loadRequests();
  }, [filters]);

  const loadRequests = async () => {
    setLoading(true);
    const result = await hpsService.getRequests(filters);
    
    if (result.success && result.data) {
      console.log('Raw requests data:', result.data.requests);
      const safeRequests = (result.data.requests || []).map((req, index) => {
        console.log(`Request ${index}:`, req);
        return req;
      });
      setRequests(safeRequests);
      setPagination({
        total: result.data.total || 0,
        pages: result.data.pages || 0,
        current_page: result.data.page || 1
      });
      setError('');
    } else {
      setError(result.error || 'Error al cargar las solicitudes');
      setRequests([]);
      setPagination({
        total: 0,
        pages: 0,
        current_page: 1
      });
    }
    setLoading(false);
  };

  const handleAction = async (action, requestId, data = {}) => {
    setActionLoading(action + requestId);
    let result;

    try {
      switch (action) {
        case 'submit':
          result = await hpsService.submitRequest(requestId, data.notes);
          break;
        case 'approve':
          result = await hpsService.approveRequest(requestId, data.expires_at, data.notes);
          break;
        case 'reject':
          result = await hpsService.rejectRequest(requestId, data.notes);
          break;
        case 'delete':
          result = await hpsService.deleteRequest(requestId);
          break;
        default:
          return;
      }

      if (result.success) {
        await loadRequests();
        if (onStatsUpdate) onStatsUpdate();
        setSelectedRequest(null);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Error al realizar la acción');
    } finally {
      setActionLoading('');
    }
  };

  const handlePreviewFilledPDF = async (requestId) => {
    // Abrir directamente el visualizador/editor de PDF
    setViewingHpsId(requestId);
    setPdfViewerOpen(true);
  };

  const handleDownloadFilledPDF = async (requestId) => {
    try {
      const result = await hpsService.downloadFilledPDF(requestId);
      if (!result.success) {
        // Mostrar error específico
        if (result.error.includes('No hay PDF rellenado disponible')) {
          setError('⚠️ No hay PDF rellenado para esta solicitud. El usuario debe completar el formulario primero.');
        } else {
          setError(result.error);
        }
      }
    } catch (err) {
      setError('Error al descargar el PDF rellenado');
    }
  };

  const handlePreviewResponsePDF = async (requestId) => {
    try {
      const result = await hpsService.previewResponsePDF(requestId);
      if (!result.success) {
        setError(result.error);
      }
    } catch (err) {
      setError('Error al previsualizar el PDF de respuesta');
    }
  };

  const handleDownloadResponsePDF = async (requestId) => {
    try {
      const result = await hpsService.downloadResponsePDF(requestId);
      if (!result.success) {
        setError(result.error);
      }
    } catch (err) {
      setError('Error al descargar el PDF de respuesta');
    }
  };


  const handleStartEdit = () => {
    if (selectedRequest) {
      // Inicializar los datos del formulario con los datos actuales
      setEditFormData({
        'Nombre': selectedRequest.first_name || '',
        'Apellidos': `${selectedRequest.first_last_name || ''} ${selectedRequest.second_last_name || ''}`.trim(),
        'DNI': selectedRequest.document_number || '',
        'Fecha de nacimiento': selectedRequest.birth_date || '',
        'Nacionalidad': selectedRequest.nationality || '',
        'LugarNacimiento': selectedRequest.birth_place || '',
        'Teléfono': selectedRequest.phone || '',
        'Email': selectedRequest.email || ''
      });
      setIsEditingDetails(true);
    }
  };

  const handleCancelEdit = () => {
    setIsEditingDetails(false);
    setEditFormData({});
  };

  const handleFieldChange = (field, value) => {
    setEditFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSaveChanges = async () => {
    if (!selectedRequest) return;
    
    setSaveLoading(true);
    setError('');

    try {
      const result = await hpsService.editFilledPDF(selectedRequest.id, editFormData);
      
      if (result.success) {
        // Actualizar el request seleccionado con los nuevos datos
        setSelectedRequest(prev => ({
          ...prev,
          ...result.data
        }));
        setIsEditingDetails(false);
        setEditFormData({});
        // Recargar la lista
        loadRequests();
      } else {
        setError(result.error || 'Error al guardar los cambios');
      }
    } catch (err) {
      setError('Error al guardar los cambios');
    } finally {
      setSaveLoading(false);
    }
  };

  const handlePDFViewerClose = () => {
    setPdfViewerOpen(false);
    setViewingHpsId(null);
  };

  const handlePDFViewerSave = () => {
    // Recargar la lista para mostrar los cambios
    loadRequests();
    setPdfViewerOpen(false);
    setViewingHpsId(null);
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { color: 'bg-yellow-100 text-yellow-800', icon: ClockIcon, text: 'Pendiente' },
      waiting_dps: { color: 'bg-orange-100 text-orange-800', icon: ClockIcon, text: 'Esperando DPS' },
      submitted: { color: 'bg-blue-100 text-blue-800', icon: PaperAirplaneIcon, text: 'Enviada' },
      approved: { color: 'bg-green-100 text-green-800', icon: CheckCircleIcon, text: 'Aprobada' },
      rejected: { color: 'bg-red-100 text-red-800', icon: XCircleIcon, text: 'Rechazada' },
      expired: { color: 'bg-gray-100 text-gray-800', icon: XCircleIcon, text: 'Expirada' }
    };

    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="w-4 h-4 mr-1" />
        {config.text}
      </span>
    );
  };

  const canPerformAction = (request, action) => {
    const isAdmin = user.role === 'admin';
    const isTeamLeader = user.role === 'team_leader';
    const isSecurityChief = user.role === 'jefe_seguridad' || user.role === 'security_chief';

    switch (action) {
      case 'view':
        return true;
      case 'submit':
        return (isAdmin || isTeamLeader || isSecurityChief) && request?.status === 'pending';
      case 'approve':
      case 'reject':
        return (isAdmin || isTeamLeader || isSecurityChief) && request?.status === 'submitted';
      case 'delete':
        return isAdmin;
      default:
        return false;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('es-ES');
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
        <p className="mt-4 text-gray-600">Cargando solicitudes...</p>
      </div>
    );
  }

  return (
    <>
      {/* Filtros */}
      <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label htmlFor="status_filter" className="block text-sm font-medium text-gray-700 mb-1">
            Estado
          </label>
          <select
            id="status_filter"
            value={filters.status}
            onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value, page: 1 }))}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="">Todos los estados</option>
            <option value="pending">Pendiente</option>
            <option value="waiting_dps">Esperando DPS</option>
            <option value="submitted">Enviada</option>
            <option value="approved">Aprobada</option>
            <option value="rejected">Rechazada</option>
            <option value="expired">Expirada</option>
          </select>
        </div>


        <div>
          <label htmlFor="hps_type_filter" className="block text-sm font-medium text-gray-700 mb-1">
            Tipo HPS
          </label>
          <select
            id="hps_type_filter"
            value={filters.hps_type || ''}
            onChange={(e) => setFilters(prev => ({ ...prev, hps_type: e.target.value, page: 1 }))}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="">Todos los tipos HPS</option>
            <option value="solicitud">Solicitud</option>
            <option value="traslado">Traspaso</option>
          </select>
        </div>

        <div>
          <label htmlFor="per_page" className="block text-sm font-medium text-gray-700 mb-1">
            Por página
          </label>
          <select
            id="per_page"
            value={filters.per_page}
            onChange={(e) => setFilters(prev => ({ ...prev, per_page: parseInt(e.target.value), page: 1 }))}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value={5}>5</option>
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </select>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <XCircleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Lista de solicitudes */}
      {!requests || !Array.isArray(requests) || requests.length === 0 ? (
        <div className="text-center py-8">
          <ClockIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No hay solicitudes HPS que mostrar</p>
        </div>
      ) : (
        <ul className="divide-y divide-gray-200 bg-white shadow overflow-hidden sm:rounded-md">
          {requests.map((request) => (
            <li key={request?.id || Math.random()} className="px-4 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        {getStatusBadge(request?.status)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {request?.first_name || ''} {request?.first_last_name || ''} {request?.second_last_name || ''}
                        </p>
                        <p className="text-sm text-gray-500 truncate">
                          {request?.document_type || ''}: {request?.document_number || ''} • {getRequestTypeLabel(request?.request_type)} • {getHPSTypeLabel(request?.type)}
                        </p>
                      </div>
                    </div>
                    <div className="mt-2 flex items-center text-xs text-gray-500">
                      <span>Creado: {formatDate(request?.created_at)}</span>
                      {request?.expires_at && (
                        <span className="ml-4">Expira: {formatDate(request?.expires_at)}</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {/* Botón Ver */}
                    <button
                      onClick={() => setSelectedRequest(request)}
                      className="text-gray-400 hover:text-gray-600"
                      title="Ver detalles"
                    >
                      <EyeIcon className="h-5 w-5" />
                    </button>

                    {/* Botones para PDFs - solo para traspasos */}
                    {request?.type === 'traslado' && (
                      <>
                        {/* PDF Rellenado */}
                        <button
                          onClick={() => handlePreviewFilledPDF(request?.id)}
                          className="text-blue-400 hover:text-blue-600 disabled:opacity-50"
                          title="Previsualizar PDF rellenado"
                        >
                          <DocumentTextIcon className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => handleDownloadFilledPDF(request?.id)}
                          className="text-blue-400 hover:text-blue-600 disabled:opacity-50"
                          title="Descargar PDF rellenado"
                        >
                          <ArrowDownTrayIcon className="h-5 w-5" />
                        </button>
                      </>
                    )}

                    {/* Botón Enviar */}
                    {canPerformAction(request, 'submit') && (
                      <button
                        onClick={() => handleAction('submit', request?.id, { notes: 'Enviada a entidad externa' })}
                        disabled={actionLoading === 'submit' + request?.id}
                        className="text-blue-400 hover:text-blue-600 disabled:opacity-50"
                      >
                        <PaperAirplaneIcon className="h-5 w-5" />
                      </button>
                    )}

                    {/* Botón Aprobar */}
                    {canPerformAction(request, 'approve') && (
                      <button
                        onClick={() => handleAction('approve', request?.id, { 
                          expires_at: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
                          notes: 'Aprobada automáticamente' 
                        })}
                        disabled={actionLoading === 'approve' + request?.id}
                        className="text-green-400 hover:text-green-600 disabled:opacity-50"
                      >
                        <CheckCircleIcon className="h-5 w-5" />
                      </button>
                    )}

                    {/* Botón Rechazar */}
                    {canPerformAction(request, 'reject') && (
                      <button
                        onClick={() => handleAction('reject', request?.id, { notes: 'Rechazada' })}
                        disabled={actionLoading === 'reject' + request?.id}
                        className="text-red-400 hover:text-red-600 disabled:opacity-50"
                      >
                        <XCircleIcon className="h-5 w-5" />
                      </button>
                    )}

                    {/* Botón Eliminar */}
                    {canPerformAction(request, 'delete') && (
                      <button
                        onClick={() => {
                          if (window.confirm('¿Está seguro de que desea eliminar esta solicitud?')) {
                            handleAction('delete', request?.id);
                          }
                        }}
                        disabled={actionLoading === 'delete' + request?.id}
                        className="text-red-400 hover:text-red-600 disabled:opacity-50"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    )}
                  </div>
                </div>
              </li>
            ))}
        </ul>
      )}

      {/* Paginación */}
      {pagination.pages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Mostrando {((pagination.current_page - 1) * filters.per_page) + 1} a{' '}
            {Math.min(pagination.current_page * filters.per_page, pagination.total)} de{' '}
            {pagination.total} resultados
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={() => setFilters(prev => ({ ...prev, page: Math.max(1, prev.page - 1) }))}
              disabled={pagination.current_page === 1}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Anterior
            </button>
            
            <span className="px-3 py-2 text-sm text-gray-700">
              Página {pagination.current_page} de {pagination.pages}
            </span>
            
            <button
              onClick={() => setFilters(prev => ({ ...prev, page: Math.min(pagination.pages, prev.page + 1) }))}
              disabled={pagination.current_page === pagination.pages}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}

      {/* Modal de detalles */}
      {selectedRequest && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Detalles de Solicitud HPS
                </h3>
                <button
                  onClick={() => setSelectedRequest(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircleIcon className="h-6 w-6" />
                </button>
              </div>
              
              <div className="space-y-4">
                {/* Botón de editar para traspasos pendientes */}
                {selectedRequest?.type === 'traslado' && selectedRequest?.status === 'pending' && !isEditingDetails && (
                  <div className="flex justify-end">
                    <button
                      onClick={handleStartEdit}
                      className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 flex items-center"
                    >
                      <PencilIcon className="h-4 w-4 mr-2" />
                      Editar PDF
                    </button>
                  </div>
                )}

                {isEditingDetails ? (
                  // Vista de edición
                  <div className="space-y-4">
                    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                      <p className="text-yellow-800">
                        ⚠️ Los cambios se aplicarán directamente al PDF. Asegúrate de que los datos sean correctos.
                      </p>
                    </div>

                    {error && (
                      <div className="bg-red-50 border border-red-200 rounded-md p-4">
                        <p className="text-red-800">{error}</p>
                      </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
                        <input
                          type="text"
                          value={editFormData['Nombre'] || ''}
                          onChange={(e) => handleFieldChange('Nombre', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Apellidos</label>
                        <input
                          type="text"
                          value={editFormData['Apellidos'] || ''}
                          onChange={(e) => handleFieldChange('Apellidos', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">DNI/NIE</label>
                        <input
                          type="text"
                          value={editFormData['DNI'] || ''}
                          onChange={(e) => handleFieldChange('DNI', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Fecha de nacimiento</label>
                        <input
                          type="date"
                          value={editFormData['Fecha de nacimiento'] || ''}
                          onChange={(e) => handleFieldChange('Fecha de nacimiento', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Nacionalidad</label>
                        <input
                          type="text"
                          value={editFormData['Nacionalidad'] || ''}
                          onChange={(e) => handleFieldChange('Nacionalidad', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Lugar de nacimiento</label>
                        <input
                          type="text"
                          value={editFormData['LugarNacimiento'] || ''}
                          onChange={(e) => handleFieldChange('LugarNacimiento', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono</label>
                        <input
                          type="tel"
                          value={editFormData['Teléfono'] || ''}
                          onChange={(e) => handleFieldChange('Teléfono', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                        <input
                          type="email"
                          value={editFormData['Email'] || ''}
                          onChange={(e) => handleFieldChange('Email', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>

                    <div className="flex justify-end space-x-3 pt-4 border-t">
                      <button
                        onClick={handleCancelEdit}
                        disabled={saveLoading}
                        className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                      >
                        Cancelar
                      </button>
                      <button
                        onClick={handleSaveChanges}
                        disabled={saveLoading}
                        className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center"
                      >
                        {saveLoading ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Guardando...
                          </>
                        ) : (
                          <>
                            <CheckIcon className="h-4 w-4 mr-2" />
                            Guardar Cambios
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                ) : (
                  // Vista de solo lectura
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-semibold text-gray-900">Estado:</span>
                      <div className="mt-1">{getStatusBadge(selectedRequest.status)}</div>
                    </div>
                    <div>
                      <span className="font-semibold text-gray-900">Tipo:</span>
                      <p className="mt-1 text-gray-800">{getRequestTypeLabel(selectedRequest?.request_type)}</p>
                    </div>
                    <div>
                      <span className="font-semibold text-gray-900">Documento:</span>
                      <p className="mt-1 text-gray-800">{selectedRequest.document_type}: {selectedRequest.document_number}</p>
                    </div>
                    <div>
                      <span className="font-semibold text-gray-900">Fecha de Nacimiento:</span>
                      <p className="mt-1 text-gray-800">{formatDate(selectedRequest.birth_date)}</p>
                    </div>
                    <div>
                      <span className="font-semibold text-gray-900">Nombre Completo:</span>
                      <p className="mt-1 text-gray-800">
                        {selectedRequest.first_name} {selectedRequest.first_last_name} {selectedRequest.second_last_name}
                      </p>
                    </div>
                    <div>
                      <span className="font-semibold text-gray-900">Nacionalidad:</span>
                      <p className="mt-1 text-gray-800">{selectedRequest.nationality}</p>
                    </div>
                    <div>
                      <span className="font-semibold text-gray-900">Lugar de Nacimiento:</span>
                      <p className="mt-1 text-gray-800">{selectedRequest.birth_place}</p>
                    </div>
                    <div>
                      <span className="font-semibold text-gray-900">Email:</span>
                      <p className="mt-1 text-gray-800">{selectedRequest.email}</p>
                    </div>
                    <div>
                      <span className="font-semibold text-gray-900">Teléfono:</span>
                      <p className="mt-1 text-gray-800">{selectedRequest.phone}</p>
                    </div>
                    <div>
                      <span className="font-semibold text-gray-900">Creado:</span>
                      <p className="mt-1 text-gray-800">{formatDate(selectedRequest.created_at)}</p>
                    </div>
                    {selectedRequest.expires_at && (
                      <div>
                        <span className="font-semibold text-gray-900">Expira:</span>
                        <p className="mt-1 text-gray-800">{formatDate(selectedRequest.expires_at)}</p>
                      </div>
                    )}
                  </div>
                )}
                
                {selectedRequest.notes && (
                  <div>
                    <span className="font-semibold text-gray-900">Notas:</span>
                    <p className="mt-1 text-sm text-gray-800">{selectedRequest.notes}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Visualizador/Editor de PDF */}
      <PDFViewerEditor
        hpsId={viewingHpsId}
        isOpen={pdfViewerOpen}
        onClose={handlePDFViewerClose}
        onSave={handlePDFViewerSave}
      />
    </>
  );
};

export default HPSList;
