import React from 'react';

const TestWidth = () => {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Test de Ancho de Pantalla</h1>
        
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Información de la Pantalla</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-100 p-4 rounded">
              <p className="text-sm text-gray-600">Ancho de ventana:</p>
              <p className="text-lg font-mono">{window.innerWidth}px</p>
            </div>
            <div className="bg-gray-100 p-4 rounded">
              <p className="text-sm text-gray-600">Alto de ventana:</p>
              <p className="text-lg font-mono">{window.innerHeight}px</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Breakpoints de Tailwind</h2>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 bg-blue-50 rounded">
              <span className="font-medium">sm:</span>
              <span className="text-sm text-gray-600">≥ 640px</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-green-50 rounded">
              <span className="font-medium">md:</span>
              <span className="text-sm text-gray-600">≥ 768px</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-yellow-50 rounded">
              <span className="font-medium">lg:</span>
              <span className="text-sm text-gray-600">≥ 1024px</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-red-50 rounded">
              <span className="font-medium">xl:</span>
              <span className="text-sm text-gray-600">≥ 1280px</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestWidth;
