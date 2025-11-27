/**
 * Formulario para crear solicitudes HPS
 */
import React, { useState, useEffect } from 'react';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import hpsService from '../services/hpsService';
import useAuthStore from '../store/authStore';
import { NATIONALITY_OPTIONS, DOCUMENT_TYPE_OPTIONS, REQUEST_TYPE_OPTIONS } from '../constants/hpsOptions';
import { formatErrorForDisplay } from '../utils/errorHandler';

const HPSForm = ({ onSuccess, prefilledEmail, token, hpsType = 'nueva' }) => {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [tokenInfo, setTokenInfo] = useState(null);

  // Estado del formulario con los 11 campos obligatorios
  const [formData, setFormData] = useState({
    request_type: hpsType === 'traslado' ? 'transfer' : (hpsType === 'renovacion' ? 'renewal' : 'new'),
    document_type: 'DNI / NIF', // Valor legible por defecto
    document_number: '',
    birth_date: '',
    first_name: '',
    first_last_name: '',
    second_last_name: '',
    nationality: 'ESPAÑA', // Valor legible por defecto
    birth_place: '',
    email: '',
    phone: ''
  });

  const [errors, setErrors] = useState({});

  // Efecto para prellenar email si se proporciona
  useEffect(() => {
    if (prefilledEmail && prefilledEmail.trim()) {
      setFormData(prev => ({
        ...prev,
        email: prefilledEmail.trim()
      }));
    }
  }, [prefilledEmail]);

  // Efecto para validar token si se proporciona
  useEffect(() => {
    const validateTokenIfProvided = async () => {
      if (token) {
        setLoading(true);
        try {
          const result = await hpsService.validateToken(token, prefilledEmail);
          if (result.success) {
            setTokenInfo(result.data);
            // Si el token es válido y tiene email, usarlo
            if (result.data.email && !prefilledEmail) {
              setFormData(prev => ({
                ...prev,
                email: result.data.email
              }));
            }
          } else {
            setError('Token inválido o expirado. No se puede acceder al formulario.');
          }
        } catch (err) {
          setError('Error al validar el token de acceso.');
        } finally {
          setLoading(false);
        }
      }
    };

    validateTokenIfProvided();
  }, [token, prefilledEmail]);

  // Validaciones del formulario
  const validateForm = () => {
    const newErrors = {};

    // Campos obligatorios
    if (!formData.document_number.trim()) {
      newErrors.document_number = 'El número de documento es obligatorio';
    }

    if (!formData.birth_date) {
      newErrors.birth_date = 'La fecha de nacimiento es obligatoria';
    }

    if (!formData.first_name.trim()) {
      newErrors.first_name = 'El nombre es obligatorio';
    }

    if (!formData.first_last_name.trim()) {
      newErrors.first_last_name = 'El primer apellido es obligatorio';
    }

    if (!formData.nationality.trim()) {
      newErrors.nationality = 'La nacionalidad es obligatoria';
    }

    if (!formData.birth_place.trim()) {
      newErrors.birth_place = 'El lugar de nacimiento es obligatorio';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'El email es obligatorio';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'El formato del email no es válido';
    }

    if (!formData.phone.trim()) {
      newErrors.phone = 'El teléfono es obligatorio';
    } else if (!/^[\+]?[0-9\s\-\(\)]{9,15}$/.test(formData.phone.replace(/\s/g, ''))) {
      newErrors.phone = 'El formato del teléfono no es válido';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Limpiar error del campo cuando el usuario comience a escribir
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Preparar datos para el backend
      const requestData = {
        ...formData,
        // Usar el ID del usuario actual si está autenticado (solo para formularios sin token)
        ...(!token && user?.id && { user_id: user.id })
      };
      
      console.log('🔍 DEBUG FRONTEND: requestData.request_type:', requestData.request_type);
      console.log('🔍 DEBUG FRONTEND: hpsType:', hpsType);

      // Usar endpoint apropiado según si hay token o no
      const result = token 
        ? await hpsService.createRequestWithToken(requestData, token, hpsType)
        : await hpsService.createRequest(requestData);

      if (result.success) {
        setSuccess('Solicitud HPS creada exitosamente');
        
        // Resetear formulario
        setFormData({
          request_type: 'new',
          document_type: '206', // DNI / NIF por defecto
          document_number: '',
          birth_date: '',
          first_name: '',
          first_last_name: '',
          second_last_name: '',
          nationality: '1', // España por defecto
          birth_place: '',
          email: '',
          phone: ''
        });

        // Notificar al componente padre
        if (onSuccess) {
          setTimeout(() => {
            onSuccess();
          }, 2000);
        }
      } else {
        setError(formatErrorForDisplay(result.error));
      }
    } catch (err) {
      setError(formatErrorForDisplay(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Información del token si está disponible */}
      {tokenInfo && tokenInfo.is_valid && (
        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <h4 className="text-sm font-medium text-blue-800">Formulario Autorizado</h4>
              <div className="mt-2 text-sm text-blue-700">
                <p>• Solicitado por: {tokenInfo.requested_by_name}</p>
                {tokenInfo.purpose && <p>• Motivo: {tokenInfo.purpose}</p>}
                <p>• Válido hasta: {new Date(tokenInfo.expires_at).toLocaleString()}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mensajes de estado */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <XCircleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex">
            <CheckCircleIcon className="h-5 w-5 text-green-400" />
            <div className="ml-3">
              <p className="text-green-800">{success}</p>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Tipo de solicitud */}
        <div className="grid grid-cols-1 gap-6">
          <div>
            <label htmlFor="request_type" className="block text-sm font-medium text-gray-700">
              Tipo de Solicitud *
            </label>
            {hpsType === 'traslado' ? (
              <div className="mt-1">
                <div className="block w-full rounded-md border-gray-300 shadow-sm bg-gray-100 text-gray-500 px-3 py-2">
                  📋 Traspaso
                </div>
                <input
                  type="hidden"
                  name="request_type"
                  value="transfer"
                />
              </div>
            ) : hpsType === 'renovacion' ? (
              <div className="mt-1">
                <div className="block w-full rounded-md border-gray-300 shadow-sm bg-gray-100 text-gray-500 px-3 py-2">
                  🔄 Renovación
                </div>
                <input
                  type="hidden"
                  name="request_type"
                  value="renewal"
                />
              </div>
            ) : hpsType === 'nueva' ? (
              <div className="mt-1">
                <div className="block w-full rounded-md border-gray-300 shadow-sm bg-gray-100 text-gray-500 px-3 py-2">
                  ✨ Nueva HPS
                </div>
                <input
                  type="hidden"
                  name="request_type"
                  value="new"
                />
              </div>
            ) : (
              <select
                id="request_type"
                name="request_type"
                value={formData.request_type}
                onChange={handleInputChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-gray-900"
              >
                {REQUEST_TYPE_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div>
            <label htmlFor="document_type" className="block text-sm font-medium text-gray-700">
              Tipo de Documento *
            </label>
            <select
              id="document_type"
              name="document_type"
              value={formData.document_type}
              onChange={handleInputChange}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-gray-900"
            >
              {DOCUMENT_TYPE_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Documento y fecha de nacimiento */}
        <div className="grid grid-cols-1 gap-6">
          <div>
            <label htmlFor="document_number" className="block text-sm font-medium text-gray-700">
              Número de Documento *
            </label>
            <input
              type="text"
              id="document_number"
              name="document_number"
              value={formData.document_number}
              onChange={handleInputChange}
              className={`mt-1 block w-full rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 ${
                errors.document_number ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="Ej: 12345678A"
            />
            {errors.document_number && (
              <p className="mt-1 text-sm text-red-600">{errors.document_number}</p>
            )}
          </div>

          <div>
            <label htmlFor="birth_date" className="block text-sm font-medium text-gray-700">
              Fecha de Nacimiento *
            </label>
            <input
              type="date"
              id="birth_date"
              name="birth_date"
              value={formData.birth_date}
              onChange={handleInputChange}
              className={`mt-1 block w-full rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 ${
                errors.birth_date ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {errors.birth_date && (
              <p className="mt-1 text-sm text-red-600">{errors.birth_date}</p>
            )}
          </div>
        </div>

        {/* Nombres */}
        <div className="grid grid-cols-1 gap-6">
          <div>
            <label htmlFor="first_name" className="block text-sm font-medium text-gray-700">
              Nombre *
            </label>
            <input
              type="text"
              id="first_name"
              name="first_name"
              value={formData.first_name}
              onChange={handleInputChange}
              className={`mt-1 block w-full rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 ${
                errors.first_name ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="Nombre"
            />
            {errors.first_name && (
              <p className="mt-1 text-sm text-red-600">{errors.first_name}</p>
            )}
          </div>

          <div>
            <label htmlFor="first_last_name" className="block text-sm font-medium text-gray-700">
              Primer Apellido *
            </label>
            <input
              type="text"
              id="first_last_name"
              name="first_last_name"
              value={formData.first_last_name}
              onChange={handleInputChange}
              className={`mt-1 block w-full rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 ${
                errors.first_last_name ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="Primer apellido"
            />
            {errors.first_last_name && (
              <p className="mt-1 text-sm text-red-600">{errors.first_last_name}</p>
            )}
          </div>

          <div>
            <label htmlFor="second_last_name" className="block text-sm font-medium text-gray-700">
              Segundo Apellido
            </label>
            <input
              type="text"
              id="second_last_name"
              name="second_last_name"
              value={formData.second_last_name}
              onChange={handleInputChange}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900"
              placeholder="Segundo apellido (opcional)"
            />
          </div>
        </div>

        {/* Nacionalidad y lugar de nacimiento */}
        <div className="grid grid-cols-1 gap-6">
          <div>
            <label htmlFor="nationality" className="block text-sm font-medium text-gray-700">
              Nacionalidad *
            </label>
            <select
              id="nationality"
              name="nationality"
              value={formData.nationality}
              onChange={handleInputChange}
              className={`mt-1 block w-full rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 ${
                errors.nationality ? 'border-red-300' : 'border-gray-300'
              }`}
            >
              {NATIONALITY_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {errors.nationality && (
              <p className="mt-1 text-sm text-red-600">{errors.nationality}</p>
            )}
          </div>

          <div>
            <label htmlFor="birth_place" className="block text-sm font-medium text-gray-700">
              Lugar de Nacimiento *
            </label>
            <input
              type="text"
              id="birth_place"
              name="birth_place"
              value={formData.birth_place}
              onChange={handleInputChange}
              className={`mt-1 block w-full rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 ${
                errors.birth_place ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="Ej: Madrid, España"
            />
            {errors.birth_place && (
              <p className="mt-1 text-sm text-red-600">{errors.birth_place}</p>
            )}
          </div>
        </div>

        {/* Email y teléfono */}
        <div className="grid grid-cols-1 gap-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Correo Electrónico *
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email || 'Email no proporcionado'}
              disabled={true}
              className="mt-1 block w-full rounded-md shadow-sm bg-gray-100 text-gray-600 border-gray-300 cursor-not-allowed"
              placeholder="Se rellenará automáticamente desde la URL"
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-600">{errors.email}</p>
            )}
          </div>

          <div>
            <label htmlFor="phone" className="block text-sm font-medium text-gray-700">
              Teléfono *
            </label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              className={`mt-1 block w-full rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 ${
                errors.phone ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="+34 600 123 456"
            />
            {errors.phone && (
              <p className="mt-1 text-sm text-red-600">{errors.phone}</p>
            )}
          </div>
        </div>



        {/* Botones */}
        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => {
              setFormData({
                request_type: 'new',
                document_type: '206', // DNI / NIF por defecto
                document_number: '',
                birth_date: '',
                first_name: '',
                first_last_name: '',
                second_last_name: '',
                nationality: '1', // España por defecto
                birth_place: '',
                email: '',
                phone: ''
              });
              setErrors({});
              setError('');
              setSuccess('');
            }}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Limpiar
          </button>
          
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Creando...' : 'Crear Solicitud HPS'}
          </button>
        </div>
      </form>
    </>
  );
};

export default HPSForm;
