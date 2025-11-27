"use client";

import { useParams } from "next/navigation";
import AlbaranDetail from "@/components/albaranes/AlbaranDetail";
import ProtectedRoute from "@/components/protectedRoute";

export default function AlbaranDetailPage() {
  const params = useParams();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;

  if (!id) return null;

  return (
    <ProtectedRoute>
      <div className="max-w-6xl mx-auto px-6 py-4">
        <AlbaranDetail id={id} />
      </div>
    </ProtectedRoute>
  );
}
