"use client";

import ProtectedRoute from "@/components/protectedRoute";
import AlbaranesTable from "@/components/albaranes/AlbaranesTable";
import AlbaranesActions from "@/components/albaranes/AlbaranesActions";

export default function AlbaranesEntradaPage() {
  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto py-10">
        <AlbaranesActions />
        <AlbaranesTable filterType="ENTRADA" />
      </div>
    </ProtectedRoute>
  );
} 