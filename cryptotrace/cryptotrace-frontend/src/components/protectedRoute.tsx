"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("accessToken");
    if (!token) {
      router.push("/login"); // Redirigir si no hay token
    } else {
      setLoading(false);
    }
  }, [router]);

  if (loading) return <div>Cargando...</div>; // Muestra un loader mientras verifica

  return <>{children}</>;
}
