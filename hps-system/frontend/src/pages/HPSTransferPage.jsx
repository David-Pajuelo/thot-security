import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { DocumentArrowDownIcon, DocumentArrowUpIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const HPSTransferPage = () => {
  const { transferId } = useParams();
  const [searchParams] = useSearchParams();
  const email = searchParams.get('email');
  
  const [transferData, setTransferData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  useEffect(() => {
    if (transferId) {
      fetchTransferData();
    }
  }, [transferId]);

  const fetchTransferData = async () => {
    try {
      const response = await fetch(`/api/hps/requests/${transferId}/`);
      if (response.ok) {
        const data = await response.json();
        setTransferData(data);
      } else {
        setError('No se pudo cargar la información del traspaso');
      }
    } catch (err) {
      setError('Error de conexión');
    } finally {
      setLoading(false);
    }
  };

  const downloadTemplate = async () => {
    try {
      const response = await fetch(`/api/hps/templates/${transferData.template_id}/pdf/`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `plantilla-traspaso-hps-${email}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        setError('No se pudo descargar la plantilla');
      }
    } catch (err) {
      setError('Error descargando la plantilla');
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      setError('Solo se permiten archivos PDF');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('filled_pdf', file);

      const response = await fetch(`/api/hps/requests/${transferId}/upload-filled-pdf/`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        setUploadSuccess(true);
        setTransferData(prev => ({ ...prev, filled_pdf: true }));
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Error subiendo el archivo');
      }
    } catch (err) {
      setError('Error de conexión al subir el archivo');
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando información del traspaso...</p>
        </div>
      </div>
    );
  }

  if (error && !transferData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Error</h1>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Traspaso HPS
          </h1>
          <p className="text-gray-600">
            Proceso de traspaso para {email}
          </p>
        </div>

        {/* Status Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Estado del Traspaso</h2>
              <p className="text-gray-600">
                {transferData?.status === 'pending' ? 'Pendiente de PDF' : 
                 transferData?.status === 'submitted' ? 'PDF Subido' : 
                 transferData?.status === 'approved' ? 'Aprobado' : 
                 transferData?.status === 'rejected' ? 'Rechazado' : 'Desconocido'}
              </p>
            </div>
            <div className="text-right">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                transferData?.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                transferData?.status === 'submitted' ? 'bg-blue-100 text-blue-800' :
                transferData?.status === 'approved' ? 'bg-green-100 text-green-800' :
                transferData?.status === 'rejected' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {transferData?.status === 'pending' ? 'Pendiente' :
                 transferData?.status === 'submitted' ? 'Enviado' :
                 transferData?.status === 'approved' ? 'Aprobado' :
                 transferData?.status === 'rejected' ? 'Rechazado' : 'Desconocido'}
              </span>
            </div>
          </div>
        </div>

        {/* Steps */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">Pasos del Traspaso</h2>
          
          <div className="space-y-6">
            {/* Step 1: Download Template */}
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  transferData?.template_id ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'
                }`}>
                  <DocumentArrowDownIcon className="w-5 h-5" />
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-medium text-gray-900">1. Descargar Plantilla PDF</h3>
                <p className="text-gray-600 mb-4">
                  Descarga la plantilla oficial del gobierno para el traspaso HPS.
                </p>
                <button
                  onClick={downloadTemplate}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <DocumentArrowDownIcon className="w-4 h-4 mr-2" />
                  Descargar Plantilla PDF
                </button>
              </div>
            </div>

            {/* Step 2: Fill and Upload */}
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  transferData?.filled_pdf ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'
                }`}>
                  <DocumentArrowUpIcon className="w-5 h-5" />
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-medium text-gray-900">2. Rellenar y Subir PDF</h3>
                <p className="text-gray-600 mb-4">
                  Rellena la plantilla con tus datos y súbela aquí.
                </p>
                
                {uploadSuccess && (
                  <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
                    <div className="flex">
                      <CheckCircleIcon className="w-5 h-5 text-green-400 mr-2" />
                      <p className="text-green-800">PDF subido correctamente</p>
                    </div>
                  </div>
                )}

                {error && (
                  <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-red-800">{error}</p>
                  </div>
                )}

                <div className="flex items-center space-x-4">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileUpload}
                    disabled={uploading || uploadSuccess}
                    className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  />
                  {uploading && (
                    <div className="flex items-center text-blue-600">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                      Subiendo...
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Step 3: Processing */}
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  transferData?.status === 'approved' ? 'bg-green-100 text-green-600' : 
                  transferData?.status === 'rejected' ? 'bg-red-100 text-red-600' :
                  'bg-gray-100 text-gray-400'
                }`}>
                  <CheckCircleIcon className="w-5 h-5" />
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-medium text-gray-900">3. Procesamiento</h3>
                <p className="text-gray-600">
                  El jefe de seguridad procesará tu solicitud de traspaso.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-2">Instrucciones</h3>
          <ul className="text-blue-800 space-y-2">
            <li>• Descarga la plantilla PDF oficial</li>
            <li>• Rellena todos los campos requeridos</li>
            <li>• Guarda el PDF rellenado</li>
            <li>• Sube el PDF completado en esta página</li>
            <li>• Espera la respuesta del jefe de seguridad</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default HPSTransferPage;
