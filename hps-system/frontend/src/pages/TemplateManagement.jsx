import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeftIcon, PlusIcon } from '@heroicons/react/24/outline';
import TemplateList from '../components/TemplateList';
import TemplateForm from '../components/TemplateForm';

const TemplateManagement = () => {
  const navigate = useNavigate();
  const [showForm, setShowForm] = useState(false);
  const templateListRef = useRef(null);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Gestión de Plantillas
              </h1>
              <p className="text-sm text-gray-600">
                Administrar plantillas PDF para traspasos HPS
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowForm(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Nueva Plantilla
              </button>
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
          <TemplateList ref={templateListRef} />
        </div>
      </div>

      {/* Modal del formulario */}
      {showForm && (
        <TemplateForm
          template={null}
          onClose={() => setShowForm(false)}
          onSuccess={() => {
            // Actualizar la lista de plantillas después de crear/actualizar
            if (templateListRef.current) {
              templateListRef.current.refresh();
            }
          }}
        />
      )}
    </div>
  );
};

export default TemplateManagement;

