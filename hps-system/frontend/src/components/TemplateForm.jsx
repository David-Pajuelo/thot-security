import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import templateService from '../services/templateService';

const TemplateForm = ({ template, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    template_type: 'jefe_seguridad',
    template_pdf: null
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (template) {
      setFormData({
        name: template.name || '',
        template_type: template.template_type || 'jefe_seguridad',
        template_pdf: null
      });
    }
  }, [template]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        setError('Solo se permiten archivos PDF');
        return;
      }
      if (file.size > 10 * 1024 * 1024) { // 10MB
        setError('El archivo no puede ser mayor a 10MB');
        return;
      }
      setFormData(prev => ({
        ...prev,
        template_pdf: file
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      let result;
      if (template) {
        // Actualizar plantilla existente
        result = await templateService.updateTemplate(template.id, formData);
      } else {
        // Crear nueva plantilla
        if (!formData.template_pdf) {
          setError('Debes seleccionar un archivo PDF');
          setLoading(false);
          return;
        }
        result = await templateService.createTemplate(formData);
      }

      if (result.success) {
        // Llamar callback de éxito si existe (para actualizar la lista)
        if (onSuccess) {
          onSuccess();
        }
        onClose();
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Error al procesar la plantilla');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white my-8">
        <div className="mt-3">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              {template ? 'Editar Plantilla' : 'Nueva Plantilla'}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Nombre */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                Nombre *
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                required
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ej: Plantilla Traspaso HPS 2024"
              />
            </div>

            {/* Tipo de Plantilla */}
            <div>
              <label htmlFor="template_type" className="block text-sm font-medium text-gray-700">
                Tipo de Plantilla *
              </label>
              <select
                id="template_type"
                name="template_type"
                value={formData.template_type}
                onChange={handleInputChange}
                required
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="jefe_seguridad">Jefe Seguridad</option>
                <option value="jefe_seguridad_suplente">Jefe Seguridad Suplente</option>
              </select>
            </div>

            {/* Archivo PDF */}
            <div>
              <label htmlFor="template_pdf" className="block text-sm font-medium text-gray-700">
                Archivo PDF {!template && '*'}
              </label>
              <div className="mt-1">
                <input
                  type="file"
                  id="template_pdf"
                  name="template_pdf"
                  accept=".pdf"
                  onChange={handleFileChange}
                  required={!template}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-3 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 file:cursor-pointer cursor-pointer"
                />
                {formData.template_pdf && (
                  <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded-md">
                    <p className="text-sm text-green-800 font-medium">
                      ✓ Archivo seleccionado: {formData.template_pdf.name}
                    </p>
                    <p className="text-xs text-green-600">
                      Tamaño: {(formData.template_pdf.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Botones */}
            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {loading ? 'Guardando...' : (template ? 'Actualizar' : 'Crear')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default TemplateForm;
