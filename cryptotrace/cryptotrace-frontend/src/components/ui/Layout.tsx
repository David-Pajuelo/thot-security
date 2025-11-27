"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Package, FileText, Database, Building, Settings, User } from "lucide-react";
import { usePathname } from "next/navigation";

export default function Layout({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isSuperuser, setIsSuperuser] = useState(false);
  const pathname = usePathname();

  // 🔥 Función para actualizar estado del usuario
  const updateUserState = () => {
    const token = localStorage.getItem("accessToken");
    setIsAuthenticated(!!token);
    
    // Verificar si el usuario es superusuario
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setIsSuperuser(payload.is_superuser || false);
      } catch (error) {
        console.error("Error parsing token:", error);
        setIsSuperuser(false);
      }
    } else {
      setIsSuperuser(false);
    }
  };

  useEffect(() => {
    // 🔥 Actualizar estado inicial
    updateUserState();

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

    // Agregar listeners
    window.addEventListener("storage", handleStorageChange);
    window.addEventListener("tokenUpdated", handleTokenUpdate);

    // Cleanup listeners
    return () => {
      window.removeEventListener("storage", handleStorageChange);
      window.removeEventListener("tokenUpdated", handleTokenUpdate);
    };
  }, []);

  // 🔥 NUEVO: Actualizar estado cuando cambia la ruta (para detectar después del login)
  useEffect(() => {
    updateUserState();
  }, [pathname]);

  const handleLogout = () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    
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
