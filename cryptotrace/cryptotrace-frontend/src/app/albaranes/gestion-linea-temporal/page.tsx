"use client";

import ProtectedRoute from "@/components/protectedRoute";
import GestionLineaTemporal from "@/components/albaranes/GestionLineaTemporal";

export default function GestionLineaTemporalPage() {
  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto py-10">
        <h1 className="text-2xl font-bold mb-6">Gestión de Línea Temporal</h1>
        <GestionLineaTemporal />
      </div>
    </ProtectedRoute>
  );
}
