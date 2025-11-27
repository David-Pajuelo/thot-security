"use client";

import ProtectedRoute from "@/components/protectedRoute";
import AlbaranesTable from "@/components/albaranes/AlbaranesTable";

export default function AlbaranesSalidaPage() {
  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto py-10">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Salidas de Material</h1>
          <p className="text-gray-600 mt-2">Gestión de AC21s de salida de material</p>
        </div>
        {/* No mostramos AlbaranesActions aquí porque las salidas se crean desde las entradas */}
        <AlbaranesTable filterType="SALIDA" />
      </div>
    </ProtectedRoute>
  );
} 