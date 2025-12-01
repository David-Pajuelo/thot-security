import React, { useState } from 'react';
import { ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline';

const PermanentDeleteModal = ({ 
  isOpen, 
  onClose, 
  onConfirm, 
  userEmail, 
  hpsRequestsCount = 0,
  loading = false 
}) => {
  const [confirmText, setConfirmText] = useState('');
  const [step, setStep] = useState(1); // 1: Advertencia, 2: Confirmación final

  const isConfirmValid = confirmText.toLowerCase() === 'eliminar';

  const handleConfirm = () => {
    if (step === 1) {
      setStep(2);
    } else if (step === 2 && isConfirmValid) {
      onConfirm();
    }
  };

  const handleClose = () => {
    setStep(1);
    setConfirmText('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <ExclamationTriangleIcon className="h-8 w-8 text-red-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900">
              {step === 1 ? 'Eliminación Definitiva' : 'Confirmación Final'}
            </h2>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600"
            disabled={loading}
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {step === 1 ? (
            // Paso 1: Advertencia
            <div className="space-y-4">
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800">
                  <strong>⚠️ ADVERTENCIA CRÍTICA:</strong>
                </p>
                <ul className="mt-2 text-sm text-red-700 space-y-1">
                  <li>• Esta acción es <strong>IRREVERSIBLE</strong></li>
                  <li>• El usuario <strong>{userEmail}</strong> será eliminado permanentemente</li>
                  <li>• Se eliminarán TODOS sus datos: solicitudes HPS, tokens, conversaciones, etc.</li>
                  <li>• Esta acción NO se puede deshacer</li>
                </ul>
              </div>
              
              {hpsRequestsCount > 0 && (
                <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                  <p className="text-sm text-orange-800 font-semibold mb-2">
                    ⚠️ Solicitudes HPS asociadas:
                  </p>
                  <p className="text-sm text-orange-700">
                    Este usuario tiene <strong>{hpsRequestsCount} solicitud{hpsRequestsCount !== 1 ? 'es' : ''} HPS</strong> asociada{hpsRequestsCount !== 1 ? 's' : ''}. 
                    Al eliminar el usuario, estas solicitudes quedarán sin usuario asociado (el campo usuario se establecerá en NULL).
                  </p>
                </div>
              )}
              
              <p className="text-gray-600">
                ¿Estás seguro de que quieres continuar con la eliminación definitiva?
              </p>
            </div>
          ) : (
            // Paso 2: Confirmación final
            <div className="space-y-4">
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800 font-semibold">
                  ÚLTIMA CONFIRMACIÓN REQUERIDA
                </p>
                <p className="text-sm text-red-700 mt-1">
                  Para confirmar la eliminación definitiva de <strong>{userEmail}</strong>, 
                  escribe <strong>"ELIMINAR"</strong> en el campo de abajo:
                </p>
              </div>
              
              <div>
                <label htmlFor="confirmText" className="block text-sm font-medium text-gray-700 mb-1">
                  Escribe "ELIMINAR" para confirmar:
                </label>
                <input
                  type="text"
                  id="confirmText"
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  placeholder="Escribe ELIMINAR aquí"
                  disabled={loading}
                />
              </div>
            </div>
          )}

          {/* Botones */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleConfirm}
              disabled={loading || (step === 2 && !isConfirmValid)}
              className="flex-1 px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                'Eliminando...'
              ) : step === 1 ? (
                'Continuar'
              ) : (
                'ELIMINAR DEFINITIVAMENTE'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PermanentDeleteModal;
