import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import { 
  DocumentTextIcon, 
  TrashIcon,
  ArrowDownTrayIcon,
  PencilIcon,
  DocumentTextIcon as EditPDFIcon
} from '@heroicons/react/24/outline';
import templateService from '../services/templateService';
import pdfService from '../services/pdfService';
import TemplatePDFEditor from './TemplatePDFEditor';

const TemplateList = forwardRef((props, ref) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [editFormData, setEditFormData] = useState({
    name: '',
    template_type: 'jefe_seguridad',
    template_pdf: null
  });
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 10,
    total: 0
  });
  const [editingPDFTemplateId, setEditingPDFTemplateId] = useState(null);

  useEffect(() => {
    loadTemplates();
  }, [pagination.page]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const result = await templateService.getTemplates({
        page: pagination.page,
        per_page: pagination.per_page
      });

      if (result.success) {
        setTemplates(result.data.templates || []);
        setPagination(prev => ({
          ...prev,
          total: result.data.total || 0
        }));
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Error al cargar las plantillas');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Estás seguro de que quieres eliminar esta plantilla?')) {
      return;
    }

    try {
      console.log('Eliminando plantilla con ID:', id);
      const result = await templateService.deleteTemplate(id);
      console.log('Resultado eliminación:', result);
      if (result.success) {
        setError(null); // Limpiar errores previos
        loadTemplates();
      } else {
        setError(result.error);
      }
    } catch (err) {
      console.error('Error eliminando plantilla:', err);
      setError('Error al eliminar la plantilla');
    }
  };


  const handleDownload = async (id, name) => {
    try {
      const url = `/api/hps/templates/${id}/pdf/`;
      const result = await pdfService.downloadPDFAsFile(url, `${name}.pdf`);
      if (!result.success) {
        setError(result.error);
      }
    } catch (err) {
      setError('Error al descargar la plantilla');
    }
  };

  const handleEdit = (template) => {
    setEditingTemplate(template);
    setEditFormData({
      name: template.name,
      template_type: template.template_type || 'jefe_seguridad',
      template_pdf: null
    });
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      const result = await templateService.updateTemplate(editingTemplate.id, editFormData);
      if (result.success) {
        setEditingTemplate(null);
        setEditFormData({
          name: '',
          template_type: 'jefe_seguridad',
          template_pdf: null
        });
        loadTemplates();
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Error al actualizar la plantilla');
    }
  };

  const handleEditCancel = () => {
    setEditingTemplate(null);
    setEditFormData({
      name: '',
      template_type: 'jefe_seguridad',
      template_pdf: null
    });
  };

  const handleEditInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setEditFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleEditFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      setEditFormData(prev => ({
        ...prev,
        template_pdf: file
      }));
    } else {
      setError('Solo se permiten archivos PDF');
    }
  };



  const getTemplateTypeBadge = (templateType) => {
    const typeLabels = {
      'jefe_seguridad': 'Jefe Seguridad',
      'jefe_seguridad_suplente': 'Jefe Seguridad Suplente'
    };
    const typeColors = {
      'jefe_seguridad': 'bg-orange-100 text-orange-800',
      'jefe_seguridad_suplente': 'bg-orange-100 text-orange-800'
    };
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${typeColors[templateType] || 'bg-gray-100 text-gray-800'}`}>
        {typeLabels[templateType] || templateType}
      </span>
    );
  };

  const handleEditPDF = (templateId) => {
    setEditingPDFTemplateId(templateId);
  };

  const handlePDFEditorClose = () => {
    setEditingPDFTemplateId(null);
  };

  const handlePDFEditorSave = () => {
    loadTemplates();
  };

  // Exponer loadTemplates para que pueda ser llamado desde el componente padre
  useImperativeHandle(ref, () => ({
    refresh: loadTemplates
  }));

  // Separar plantillas por tipo (manejar plantillas sin template_type asignándoles 'jefe_seguridad' por defecto)
  const templatesByType = {
    jefe_seguridad: templates.filter(t => !t.template_type || t.template_type === 'jefe_seguridad'),
    jefe_seguridad_suplente: templates.filter(t => t.template_type === 'jefe_seguridad_suplente')
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* Templates List by Type */}
      {templates.length === 0 ? (
        <div className="text-center py-12">
          <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No hay plantillas</h3>
          <p className="mt-1 text-sm text-gray-500">Comienza creando tu primera plantilla usando el botón "Nueva Plantilla" en el header.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Plantilla Jefe Seguridad Section */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <span className="h-3 w-3 bg-orange-500 rounded-full mr-2"></span>
              Plantilla Jefe Seguridad
            </h3>
            {templatesByType.jefe_seguridad.length === 0 ? (
              <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-500">No hay plantillas de tipo Jefe Seguridad</p>
              </div>
            ) : (
              <div className="bg-white shadow overflow-hidden sm:rounded-md">
                <ul className="divide-y divide-gray-200">
                  {templatesByType.jefe_seguridad.map((template) => (
                    <li key={template.id}>
                      <div className="px-4 py-4 flex items-center justify-between">
                        <div className="flex items-center">
                          <div className="flex-shrink-0">
                            <DocumentTextIcon className="h-8 w-8 text-gray-400" />
                          </div>
                          <div className="ml-4">
                            <div className="flex items-center">
                              <p className="text-sm font-medium text-gray-900">{template.name}</p>
                              <div className="ml-2">
                                {getTemplateTypeBadge(template.template_type || 'jefe_seguridad')}
                              </div>
                            </div>
                            <div className="mt-1 text-xs text-gray-400">
                              Creado {new Date(template.created_at).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleEditPDF(template.id)}
                            className="text-gray-400 hover:text-purple-600"
                            title="Editar PDF"
                          >
                            <EditPDFIcon className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => handleDownload(template.id, template.name)}
                            className="text-gray-400 hover:text-gray-600"
                            title="Descargar PDF"
                          >
                            <ArrowDownTrayIcon className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => handleEdit(template)}
                            className="text-gray-400 hover:text-yellow-600"
                            title="Editar plantilla"
                          >
                            <PencilIcon className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => handleDelete(template.id)}
                            className="text-gray-400 hover:text-red-600"
                            title="Eliminar"
                          >
                            <TrashIcon className="h-5 w-5" />
                          </button>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Plantilla Jefe Seguridad Suplente Section */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <span className="h-3 w-3 bg-orange-500 rounded-full mr-2"></span>
              Plantilla Jefe Seguridad Suplente
            </h3>
            {templatesByType.jefe_seguridad_suplente.length === 0 ? (
              <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-500">No hay plantillas de tipo Jefe Seguridad Suplente</p>
              </div>
            ) : (
              <div className="bg-white shadow overflow-hidden sm:rounded-md">
                <ul className="divide-y divide-gray-200">
                  {templatesByType.jefe_seguridad_suplente.map((template) => (
                    <li key={template.id}>
                      <div className="px-4 py-4 flex items-center justify-between">
                        <div className="flex items-center">
                          <div className="flex-shrink-0">
                            <DocumentTextIcon className="h-8 w-8 text-gray-400" />
                          </div>
                          <div className="ml-4">
                            <div className="flex items-center">
                              <p className="text-sm font-medium text-gray-900">{template.name}</p>
                              <div className="ml-2">
                                {getTemplateTypeBadge(template.template_type || 'jefe_seguridad_suplente')}
                              </div>
                            </div>
                            <div className="mt-1 text-xs text-gray-400">
                              Creado {new Date(template.created_at).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleEditPDF(template.id)}
                            className="text-gray-400 hover:text-purple-600"
                            title="Editar PDF"
                          >
                            <EditPDFIcon className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => handleDownload(template.id, template.name)}
                            className="text-gray-400 hover:text-gray-600"
                            title="Descargar PDF"
                          >
                            <ArrowDownTrayIcon className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => handleEdit(template)}
                            className="text-gray-400 hover:text-yellow-600"
                            title="Editar plantilla"
                          >
                            <PencilIcon className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => handleDelete(template.id)}
                            className="text-gray-400 hover:text-red-600"
                            title="Eliminar"
                          >
                            <TrashIcon className="h-5 w-5" />
                          </button>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Pagination */}
      {pagination.total > pagination.per_page && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Mostrando {((pagination.page - 1) * pagination.per_page) + 1} a {Math.min(pagination.page * pagination.per_page, pagination.total)} de {pagination.total} plantillas
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
              disabled={pagination.page === 1}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Anterior
            </button>
            <button
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
              disabled={pagination.page * pagination.per_page >= pagination.total}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}

      {/* PDF Editor Modal */}
      {editingPDFTemplateId && (
        <TemplatePDFEditor
          templateId={editingPDFTemplateId}
          isOpen={true}
          onClose={handlePDFEditorClose}
          onSave={handlePDFEditorSave}
        />
      )}

      {/* Modal de Edición */}
      {editingTemplate && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Editar Plantilla: {editingTemplate.name}
              </h3>
              
              <form onSubmit={handleEditSubmit} className="space-y-4">
                <div>
                  <label htmlFor="edit_name" className="block text-sm font-medium text-gray-700">
                    Nombre *
                  </label>
                  <input
                    type="text"
                    id="edit_name"
                    name="name"
                    value={editFormData.name}
                    onChange={handleEditInputChange}
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label htmlFor="edit_template_type" className="block text-sm font-medium text-gray-700">
                    Tipo de Plantilla *
                  </label>
                  <select
                    id="edit_template_type"
                    name="template_type"
                    value={editFormData.template_type}
                    onChange={handleEditInputChange}
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="jefe_seguridad">Jefe Seguridad</option>
                    <option value="jefe_seguridad_suplente">Jefe Seguridad Suplente</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="edit_pdf" className="block text-sm font-medium text-gray-700">
                    Nuevo PDF (opcional)
                  </label>
                  <input
                    type="file"
                    id="edit_pdf"
                    accept=".pdf"
                    onChange={handleEditFileChange}
                    className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Si no seleccionas un archivo, se mantendrá el PDF actual
                  </p>
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={handleEditCancel}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
                  >
                    Guardar Cambios
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

    </div>
  );
});

TemplateList.displayName = 'TemplateList';

export default TemplateList;
