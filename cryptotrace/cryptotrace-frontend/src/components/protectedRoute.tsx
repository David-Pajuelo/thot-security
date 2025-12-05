"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface JWTPayload {
  role?: string;
  exp: number;
}

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [unauthorized, setUnauthorized] = useState(false);

  // Helper para leer cookies
  const getCookie = (name: string): string | null => {
    if (typeof document === 'undefined') return null;
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
    return null;
  };

  useEffect(() => {
    // Asegurarse de que estamos en el cliente (no SSR)
    if (typeof window === 'undefined') {
      return;
    }

    // Buscar token en localStorage primero (más rápido)
    let accessToken = localStorage.getItem("accessToken");
    const hpsToken = localStorage.getItem("hps_token");
    let token = accessToken || hpsToken;
    
    // Solo verificar cookies si no hay token en localStorage (evitar verificaciones redundantes)
    if (!token) {
      accessToken = getCookie("accessToken");
      if (accessToken) {
        token = accessToken;
        localStorage.setItem("accessToken", accessToken);
        const refreshToken = getCookie("refreshToken");
        if (refreshToken) {
          localStorage.setItem("refreshToken", refreshToken);
        }
        console.log("[ProtectedRoute] Token encontrado en cookie, copiado a localStorage");
      }
    }
    
    // Logs solo en desarrollo para mejor rendimiento
    if (process.env.NODE_ENV === 'development') {
      console.log("[ProtectedRoute] Verificando token...");
      console.log("[ProtectedRoute] accessToken existe:", !!accessToken);
      console.log("[ProtectedRoute] hps_token existe:", !!hpsToken);
      console.log("[ProtectedRoute] Token completo (primeros 50 chars):", token ? token.substring(0, 50) + "..." : "No hay token");
    }
    
    if (!token) {
      console.log("[ProtectedRoute] No hay token, redirigiendo a /login");
      router.push("/login"); // Redirigir si no hay token
      return;
    }

    // Verificar rol del usuario desde el token JWT
    try {
      const payload = JSON.parse(atob(token.split('.')[1])) as JWTPayload;
      console.log("[ProtectedRoute] Payload decodificado:", {
        role: payload.role,
        exp: payload.exp
      });
      
      const allowedRoles = ['admin', 'crypto'];
      
      // Si el token no tiene rol o el rol no está permitido, denegar acceso
      // PERO mantener la sesión activa para permitir navegación a HPS
      if (!payload.role || !allowedRoles.includes(payload.role)) {
        console.log("[ProtectedRoute] Usuario no tiene rol permitido:", payload.role);
        setUnauthorized(true);
        setLoading(false);
        // NO limpiar tokens - mantener sesión activa para HPS
        return;
      }

      // Verificar si el token ha expirado
      const currentTime = Math.floor(Date.now() / 1000);
      if (payload.exp && payload.exp < currentTime) {
        console.log("[ProtectedRoute] Token expirado. Exp:", payload.exp, "Current:", currentTime);
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        localStorage.removeItem("hps_token");
        localStorage.removeItem("hps_refresh_token");
        router.push("/login");
        return;
      }

      // Usuario autorizado
      console.log("[ProtectedRoute] Usuario autorizado, mostrando contenido");
      setLoading(false);
    } catch (error) {
      console.error("[ProtectedRoute] Error verificando token:", error);
      // Si hay error decodificando, por seguridad, no permitir acceso
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("hps_token");
      localStorage.removeItem("hps_refresh_token");
      router.push("/login");
    }
  }, [router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Verificando permisos...</p>
        </div>
      </div>
    );
  }

  if (unauthorized) {
    const hpsSystemUrlEnv = process.env.NEXT_PUBLIC_HPS_SYSTEM_URL;
    if (!hpsSystemUrlEnv) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ NEXT_PUBLIC_HPS_SYSTEM_URL no definida, usando localhost (solo en desarrollo)');
      } else {
        console.error('❌ NEXT_PUBLIC_HPS_SYSTEM_URL debe estar definida en producción');
      }
    }
    const hpsSystemUrl = hpsSystemUrlEnv || 'http://localhost:3001';  // Fallback solo en desarrollo
    
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md text-center">
          <div className="text-6xl mb-4">🚫</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Acceso Denegado</h2>
          <p className="text-gray-600 mb-6">
            No tienes permisos para acceder a CryptoTrace. Solo usuarios con rol <strong>admin</strong> o <strong>crypto</strong> pueden acceder a esta plataforma.
          </p>
          <p className="text-sm text-gray-500 mb-6">
            Sin embargo, puedes acceder a la plataforma HPS System con tu sesión actual.
          </p>
          <div className="flex flex-col gap-3">
            <a
              href={hpsSystemUrl}
              target="_self"
              className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-md transition-colors inline-block"
            >
              Ir a HPS System
            </a>
            <button
              onClick={() => {
                localStorage.removeItem("accessToken");
                localStorage.removeItem("refreshToken");
                router.push("/login");
              }}
              className="bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-md transition-colors"
            >
              Cerrar Sesión
            </button>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
