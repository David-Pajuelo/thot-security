"use client";

import ProtectedRoute from "@/components/protectedRoute";
import GestionCatalogo from "@/components/productos/GestionCatalogo";

export default function GestionCatalogoPage() {
  return (
    <ProtectedRoute>
      <div className="max-w-6xl mx-auto px-6 py-4">
        <GestionCatalogo />
      </div>
    </ProtectedRoute>
  );
} 