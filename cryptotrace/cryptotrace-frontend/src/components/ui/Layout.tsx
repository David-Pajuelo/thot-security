"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Package, FileText, Database, Building, Settings, User } from "lucide-react";
import { usePathname } from "next/navigation";

export default function Layout({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isSuperuser, setIsSuperuser] = useState(false);
  const [userRole, setUserRole] = useState<string | null>(null);
  const pathname = usePathname();

  // Helper para leer cookies
  const getCookie = (name: string): string | null => {
    if (typeof document === 'undefined') return null;
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
    return null;
  };

  // 🔥 Función para actualizar estado del usuario
  const updateUserState = () => {
    // Buscar token en localStorage primero (más rápido, evita leer cookies innecesariamente)
    let token = localStorage.getItem("accessToken") || localStorage.getItem("hps_token");
    
    // Solo verificar cookies si no hay token en localStorage
    if (!token) {
      token = getCookie("accessToken");
      if (token) {
        localStorage.setItem("accessToken", token);
        const refreshToken = getCookie("refreshToken");
        if (refreshToken) {
          localStorage.setItem("refreshToken", refreshToken);
        }
        console.log('[Layout] Token encontrado en cookie, copiado a localStorage');
      }
    }
    setIsAuthenticated(!!token);
    
    // Verificar si el usuario tiene rol permitido (admin o crypto) desde HPS
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        
        // Usar el rol de HPS (admin o crypto) para determinar permisos
        const allowedRoles = ['admin', 'crypto'];
        const role = payload.role;
        setUserRole(role || null);
        
        // isSuperuser será true si el rol es admin o crypto (roles con permisos de gestión)
        const hasManagementPermissions = role && allowedRoles.includes(role);
        setIsSuperuser(hasManagementPermissions || false);
        
        // Verificar rol permitido (admin o crypto)
        // NO redirigir desde Layout si estamos en /login (evitar bucles)
        if (role && !allowedRoles.includes(role) && pathname !== '/login') {
          // Si el usuario no tiene rol permitido, limpiar tokens y redirigir
          // Solo si NO estamos ya en la página de login (evitar bucles)
          console.log('[Layout] Usuario sin rol permitido, pero estamos en:', pathname);
          // No redirigir desde Layout - dejar que ProtectedRoute maneje esto
          setIsAuthenticated(false);
          setIsSuperuser(false);
          setUserRole(null);
        }
      } catch (error) {
        console.error("Error parsing token:", error);
        setIsSuperuser(false);
        setUserRole(null);
      }
    } else {
      setIsSuperuser(false);
      setUserRole(null);
    }
  };

  useEffect(() => {
    // 🔥 Actualizar estado inicial (solo una vez al montar)
    updateUserState();
    
    // Nota: La sincronización de tokens se hace mediante iframe + postMessage
    // cuando se accede directamente a CryptoTrace. No es necesario escuchar aquí.

    // 🔥 Escuchar cambios en localStorage (para cuando se actualice el token)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "accessToken") {
        updateUserState();
      }
    };

    // 🔥 Listener personalizado para cambios internos de localStorage
    const handleTokenUpdate = () => {
      updateUserState();
    };

    // 🔥 Listener para recibir token desde HPS System mediante postMessage
    const handleMessage = (event: MessageEvent) => {
      console.log('[Layout] Mensaje recibido:', {
        origin: event.origin,
        data: event.data,
        type: event.data?.type
      });
      
      // Verificar origen para seguridad (solo aceptar desde HPS System)
      const hpsSystemUrl = process.env.NEXT_PUBLIC_HPS_SYSTEM_URL || 'http://localhost:3001';
      const allowedOrigin = new URL(hpsSystemUrl).origin;
      
      console.log('[Layout] Origen permitido:', allowedOrigin);
      console.log('[Layout] Origen del mensaje:', event.origin);
      
      if (event.origin !== allowedOrigin) {
        console.log('[Layout] Mensaje rechazado - origen no permitido. Esperado:', allowedOrigin, 'Recibido:', event.origin);
        return;
      }

      if (event.data && event.data.type === 'HPS_AUTH_TOKEN') {
        console.log('[Layout] ✅ Recibido token desde HPS System mediante postMessage');
        console.log('[Layout] Token recibido (primeros 50 chars):', event.data.accessToken ? event.data.accessToken.substring(0, 50) + '...' : 'No hay token');
        
        // Guardar tokens en localStorage y cookies
        if (event.data.accessToken) {
          localStorage.setItem('accessToken', event.data.accessToken);
          const cookieOptions = 'path=/; SameSite=Lax; max-age=28800'; // 8 horas
          document.cookie = `accessToken=${event.data.accessToken}; ${cookieOptions}`;
          console.log('[Layout] ✅ Token guardado en localStorage y cookie');
        }
        if (event.data.refreshToken) {
          localStorage.setItem('refreshToken', event.data.refreshToken);
          const cookieOptions = 'path=/; SameSite=Lax; max-age=28800'; // 8 horas
          document.cookie = `refreshToken=${event.data.refreshToken}; ${cookieOptions}`;
          console.log('[Layout] ✅ Refresh token guardado en localStorage y cookie');
        }
        
        // Actualizar estado y disparar evento
        console.log('[Layout] Actualizando estado del usuario...');
        updateUserState();
        window.dispatchEvent(new Event('tokenUpdated'));
        console.log('[Layout] ✅ Estado actualizado y evento tokenUpdated disparado');
        
        // Si estamos en la página de login, redirigir automáticamente
        if (window.location.pathname === '/login') {
          console.log('[Layout] Estamos en /login, redirigiendo a /productos...');
          // Pequeño delay para asegurar que el estado se actualice
          setTimeout(() => {
            window.location.href = '/productos';
          }, 100);
        }
      } else {
        console.log('[Layout] Mensaje recibido pero no es de tipo HPS_AUTH_TOKEN:', event.data);
      }
    };

    // Agregar listeners
    window.addEventListener("storage", handleStorageChange);
    window.addEventListener("tokenUpdated", handleTokenUpdate);
    window.addEventListener("message", handleMessage);

    // Cleanup listeners
    return () => {
      window.removeEventListener("storage", handleStorageChange);
      window.removeEventListener("tokenUpdated", handleTokenUpdate);
      window.removeEventListener("message", handleMessage);
    };
  }, []);

  // 🔥 NUEVO: Actualizar estado cuando cambia la ruta (para detectar después del login)
  useEffect(() => {
    updateUserState();
  }, [pathname]);

  const handleLogout = async () => {
    // Limpiar tokens de ambos sistemas (compartidos)
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("user");
    // También limpiar nombres antiguos de HPS por si acaso
    localStorage.removeItem("hps_token");
    localStorage.removeItem("hps_refresh_token");
    localStorage.removeItem("hps_user");
    
    // Limpiar también cookies
    document.cookie = 'accessToken=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    document.cookie = 'refreshToken=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    
    // Sincronizar logout con HPS System
    try {
      const { syncLogoutWithHPS } = await import('../../utils/tokenSync');
      await syncLogoutWithHPS();
    } catch (e) {
      console.warn('[Layout] Error sincronizando logout con HPS System:', e);
    }
    
    // 🔥 Disparar evento para actualizar el estado inmediatamente
    window.dispatchEvent(new Event('tokenUpdated'));
    
    // Pequeño delay antes de redirigir para asegurar que se actualiza el estado
    setTimeout(() => {
      window.location.href = "/login";
    }, 100);
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-100">
      <header className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <Link href="/" className="text-2xl font-bold text-gray-900">
                  CryptoTrace
                </Link>
              </div>
              <nav className="hidden sm:ml-6 sm:flex sm:space-x-8">
                {isSuperuser && (
                  <Link
                    href="/productos/gestion-catalogo"
                    className={`inline-flex items-center px-1 pt-1 hover:text-gray-900 ${pathname === "/productos/gestion-catalogo" ? "text-blue-600 font-bold border-b-2 border-blue-600" : "text-gray-700"}`}
                  >
                    <Settings className="w-5 h-5 mr-1" />
                    Gestión
                  </Link>
                )}
                <Link
                  href="/productos"
                  className={`inline-flex items-center px-1 pt-1 hover:text-gray-900 ${pathname === "/productos" ? "text-blue-600 font-bold border-b-2 border-blue-600" : "text-gray-700"}`}
                >
                  <Database className="w-5 h-5 mr-1" />
                  Catálogo
                </Link>
                <Link
                  href="/productos/inventario"
                  prefetch={false}
                  className={`inline-flex items-center px-1 pt-1 hover:text-gray-900 ${pathname === "/productos/inventario" ? "text-blue-600 font-bold border-b-2 border-blue-600" : "text-gray-700"}`}
                >
                  <Package className="w-5 h-5 mr-1" />
                  Inventario
                </Link>
                <Link
                  href="/entradas/albaranes"
                  prefetch={false}
                  className={`inline-flex items-center px-1 pt-1 hover:text-gray-900 ${pathname.startsWith("/entradas") ? "text-blue-600 font-bold border-b-2 border-blue-600" : "text-gray-700"}`}
                >
                  <FileText className="w-5 h-5 mr-1" />
                  Entradas
                </Link>
                <Link
                  href="/salidas/albaranes"
                  prefetch={false}
                  className={`inline-flex items-center px-1 pt-1 hover:text-gray-900 ${pathname.startsWith("/salidas") ? "text-blue-600 font-bold border-b-2 border-blue-600" : "text-gray-700"}`}
                >
                  <FileText className="w-5 h-5 mr-1" />
                  Salidas
                </Link>
                <Link
                  href="/empresas"
                  className={`inline-flex items-center px-1 pt-1 hover:text-gray-900 ${pathname === "/empresas" ? "text-blue-600 font-bold border-b-2 border-blue-600" : "text-gray-700"}`}
                >
                  <Building className="w-5 h-5 mr-1" />
                  Empresas
                </Link>
              </nav>
            </div>
            <div className="flex items-center space-x-4">
              {isAuthenticated && (
                <>
                  <Link
                    href="/perfil"
                    className={`inline-flex items-center px-3 py-2 hover:text-gray-900 ${pathname === "/perfil" ? "text-blue-600 font-bold" : "text-gray-700"}`}
                  >
                    <User className="w-4 h-4 mr-1" />
                    Perfil
                  </Link>
                  <button 
                    onClick={handleLogout} 
                    className="inline-flex items-center px-4 py-2 text-red-600 hover:text-red-800"
                  >
                    Cerrar sesión
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>
      <main className="flex-1 p-6">{children}</main>
      <footer className="bg-gray-200 text-center p-4 text-sm text-gray-600">
        © 2025 CryptoTrace - Gestión y trazabilidad de productos
      </footer>
    </div>
  );
}
