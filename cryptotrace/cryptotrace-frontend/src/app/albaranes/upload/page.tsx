"use client";

import ProtectedRoute from "@/components/protectedRoute";
import UploadExcelForm from "@/components/albaranes/UploadExcelForm";

export default function UploadPage() {
  return (
    <ProtectedRoute>
      <div className="max-w-2xl mx-auto py-10">
        <UploadExcelForm />
      </div>
    </ProtectedRoute>
  );
}
