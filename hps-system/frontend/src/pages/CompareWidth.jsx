import React from 'react';

const CompareWidth = () => {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Comparación de Anchos</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Columna izquierda */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Vista Móvil</h2>
            <div className="bg-gray-100 p-4 rounded mb-4">
              <p className="text-sm text-gray-600 mb-2">Simulación móvil (375px)</p>
              <div className="bg-blue-200 h-8 rounded flex items-center justify-center">
                <span className="text-xs font-mono">375px</span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="bg-red-100 p-2 rounded text-sm">
                <strong>Problemas comunes:</strong>
                <ul className="mt-1 list-disc list-inside">
                  <li>Texto muy pequeño</li>
                  <li>Botones difíciles de tocar</li>
                  <li>Formularios estrechos</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Columna derecha */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Vista Desktop</h2>
            <div className="bg-gray-100 p-4 rounded mb-4">
              <p className="text-sm text-gray-600 mb-2">Simulación desktop (1200px)</p>
              <div className="bg-green-200 h-8 rounded flex items-center justify-center">
                <span className="text-xs font-mono">1200px</span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="bg-green-100 p-2 rounded text-sm">
                <strong>Ventajas:</strong>
                <ul className="mt-1 list-disc list-inside">
                  <li>Mejor legibilidad</li>
                  <li>Navegación más fácil</li>
                  <li>Más espacio para contenido</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Recomendaciones de Diseño</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded">
              <h3 className="font-semibold text-blue-800 mb-2">Mobile First</h3>
              <p className="text-sm text-blue-700">Diseña primero para móvil y luego escala hacia arriba</p>
            </div>
            <div className="bg-green-50 p-4 rounded">
              <h3 className="font-semibold text-green-800 mb-2">Responsive Design</h3>
              <p className="text-sm text-green-700">Usa breakpoints de Tailwind para adaptar el diseño</p>
            </div>
            <div className="bg-purple-50 p-4 rounded">
              <h3 className="font-semibold text-purple-800 mb-2">Testing</h3>
              <p className="text-sm text-purple-700">Prueba en diferentes dispositivos y resoluciones</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompareWidth;
