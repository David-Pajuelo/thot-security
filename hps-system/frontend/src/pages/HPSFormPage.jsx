/**
 * Página independiente para el formulario HPS
 * Accesible vía URL con email prellenado
 */
import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import HPSForm from '../components/HPSForm';

const HPSFormPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [prefilledEmail, setPrefilledEmail] = useState('');
  const [token, setToken] = useState('');
  const [hpsType, setHpsType] = useState('nueva');

  useEffect(() => {
    // Obtener email, token y tipo del query parameter
    const email = searchParams.get('email');
    const tokenParam = searchParams.get('token');
    const typeParam = searchParams.get('type');
    
    if (email) {
      // Decodificar email en caso de que esté encoded
      setPrefilledEmail(decodeURIComponent(email));
    }
    
    if (tokenParam) {
      setToken(tokenParam);
    }
    
    if (typeParam) {
      setHpsType(typeParam);
    }
  }, [searchParams]);

  const handleFormSuccess = () => {
    // Mostrar mensaje de éxito y redirigir después de unos segundos
    setTimeout(() => {
      navigate('/');
    }, 3000);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900">
            {hpsType === 'traslado' 
              ? 'Traspaso de Habilitación Personal de Seguridad (HPS)'
              : hpsType === 'renovacion'
              ? 'Renovación de Habilitación Personal de Seguridad (HPS)'
              : hpsType === 'nueva'
              ? 'Nueva Habilitación Personal de Seguridad (HPS)'
              : 'Solicitud de Habilitación Personal de Seguridad (HPS)'
            }
          </h1>
          {hpsType === 'traslado' && (
            <p className="mt-2 text-lg text-blue-600 font-medium">
              📋 Formulario de Traspaso HPS
            </p>
          )}
          {hpsType === 'renovacion' && (
            <p className="mt-2 text-lg text-green-600 font-medium">
              🔄 Formulario de Renovación HPS
            </p>
          )}
          {hpsType === 'nueva' && (
            <p className="mt-2 text-lg text-purple-600 font-medium">
              ✨ Formulario de Nueva HPS
            </p>
          )}
        </div>



        {/* Formulario HPS */}
        <div className="bg-white shadow-lg rounded-lg overflow-hidden">
          <div className="p-6">
            <HPSForm 
              onSuccess={handleFormSuccess} 
              prefilledEmail={prefilledEmail}
              token={token}
              hpsType={hpsType}
            />
          </div>
        </div>

        {/* Footer informativo */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>
            Este formulario utiliza conexión segura (HTTPS) para proteger sus datos personales.
          </p>
        </div>
      </div>
    </div>
  );
};

export default HPSFormPage;
