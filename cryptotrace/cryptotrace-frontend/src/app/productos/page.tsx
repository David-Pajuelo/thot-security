"use client";

import ProtectedRoute from "@/components/protectedRoute";
import ProductosTable from "@/components/productos/ProductosTable";

export default function ProductosPage() {
  return (
    <ProtectedRoute>
      <div className="py-10">
        <ProductosTable />
      </div>
    </ProtectedRoute>
  );
}
