"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { jwtDecode } from "jwt-decode";
import { getTokenFromHPS } from "../../utils/tokenSync";

interface JWTPayload {
  user_id: number;
  username: string;
  first_name: string;
  last_name: string;
  is_superuser: boolean;
  must_change_password: boolean;
  role?: string; // Rol HPS del usuario (admin, crypto, jefe_seguridad, member, etc.)
  exp: number;
}

export default function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [checkingToken, setCheckingToken] = useState(true);

  // Helper para leer cookies
  const getCookie = (name: string): string | null => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
    return null;
  };

  // Verificar si ya hay un token válido al cargar (sesión compartida con HPS)
  useEffect(() => {
    const checkExistingToken = async () => {
      try {
        // 1. Verificar token en localStorage
        let accessToken = localStorage.getItem("accessToken");
        const hpsToken = localStorage.getItem("hps_token");
        let token = accessToken || hpsToken;
        
        // 2. Si no hay token, intentar desde cookies primero (más rápido que iframe)
        if (!token) {
          const cookieToken = getCookie("accessToken");
          if (cookieToken) {
            token = cookieToken;
            localStorage.setItem("accessToken", cookieToken);
            const cookieRefresh = getCookie("refreshToken");
            if (cookieRefresh) {
              localStorage.setItem("refreshToken", cookieRefresh);
            }
            console.log("[LoginForm] Token encontrado en cookie, copiado a localStorage");
          }
        }
        
        // 3. Si aún no hay token, intentar obtenerlo desde HPS System (más lento, último recurso)
        if (!token) {
          console.log("[LoginForm] Intentando obtener token desde HPS System...");
          const hpsToken = await getTokenFromHPS();
          if (hpsToken) {
            token = hpsToken;
            localStorage.setItem("accessToken", token);
            console.log("[LoginForm] ✅ Token copiado desde HPS System a localStorage");
          }
        }
        
        // Logs solo en desarrollo para mejor rendimiento
        if (process.env.NODE_ENV === 'development') {
          console.log("[LoginForm] Verificando token existente...");
          console.log("[LoginForm] accessToken existe:", !!accessToken);
          console.log("[LoginForm] hps_token existe:", !!hpsToken);
          console.log("[LoginForm] Token a usar:", token ? "Sí" : "No");
        }
        
        if (!token) {
          console.log("[LoginForm] No hay token, mostrando formulario de login");
          setCheckingToken(false);
          return;
        }

        // Verificar si el token es válido decodificándolo
        try {
          console.log("[LoginForm] Decodificando token...");
          const payload = jwtDecode<JWTPayload>(token);
          console.log("[LoginForm] Payload decodificado:", {
            user_id: payload.user_id,
            username: payload.username,
            role: payload.role,
            exp: payload.exp,
            must_change_password: payload.must_change_password
          });
          
          // Verificar si el token ha expirado
          const currentTime = Math.floor(Date.now() / 1000);
          if (payload.exp && payload.exp < currentTime) {
            console.log("[LoginForm] Token expirado. Exp:", payload.exp, "Current:", currentTime);
            // Token expirado, limpiar y permitir login
            localStorage.removeItem("accessToken");
            localStorage.removeItem("refreshToken");
            localStorage.removeItem("hps_token");
            localStorage.removeItem("hps_refresh_token");
            setCheckingToken(false);
            return;
          }

          // Verificar rol permitido
          const allowedRoles = ['admin', 'crypto'];
          console.log("[LoginForm] Rol del usuario:", payload.role);
          console.log("[LoginForm] Roles permitidos:", allowedRoles);
          
          if (payload.role && !allowedRoles.includes(payload.role)) {
            console.log("[LoginForm] Usuario no tiene rol permitido, limpiando token y mostrando formulario");
            // Usuario no tiene permisos, limpiar token y mostrar formulario con error
            localStorage.removeItem("accessToken");
            localStorage.removeItem("refreshToken");
            localStorage.removeItem("hps_token");
            localStorage.removeItem("hps_refresh_token");
            setError("No tienes permisos para acceder a CryptoTrace. Solo usuarios con rol 'admin' o 'crypto' pueden acceder.");
            setCheckingToken(false);
            return;
          }

          // Token válido y rol permitido, redirigir al dashboard
          console.log("[LoginForm] Token válido y rol permitido, redirigiendo...");
          if (payload.must_change_password) {
            console.log("[LoginForm] Debe cambiar contraseña, redirigiendo a /cambiar-password");
            router.push("/cambiar-password");
          } else {
            console.log("[LoginForm] Redirigiendo a /productos");
            router.push("/productos");
          }
        } catch (decodeError) {
          console.error("[LoginForm] Error decodificando token existente:", decodeError);
          // Token inválido, limpiar y permitir login
          localStorage.removeItem("accessToken");
          localStorage.removeItem("refreshToken");
          localStorage.removeItem("hps_token");
          localStorage.removeItem("hps_refresh_token");
          setCheckingToken(false);
        }
      } catch (error) {
        console.error("[LoginForm] Error verificando token existente:", error);
        setCheckingToken(false);
      }
    };

    checkExistingToken();
    
    // También escuchar el evento tokenUpdated para cuando llegue el token mediante postMessage
    const handleTokenUpdate = () => {
      console.log("[LoginForm] Evento tokenUpdated recibido, verificando token...");
      const token = localStorage.getItem("accessToken") || localStorage.getItem("hps_token");
      if (token) {
        console.log("[LoginForm] Token encontrado después de tokenUpdated, verificando...");
        checkExistingToken();
      }
    };
    
    window.addEventListener('tokenUpdated', handleTokenUpdate);
    
    return () => {
      window.removeEventListener('tokenUpdated', handleTokenUpdate);
    };
  }, [router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validar formato de email
    const emailRegex = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i;
    if (!email.trim()) {
      setError("El correo electrónico es requerido");
      return;
    }
    if (!emailRegex.test(email.trim())) {
      setError("Por favor, introduce un correo electrónico válido");
      return;
    }

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/token/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // El backend acepta email o username en el campo 'username'
        body: JSON.stringify({ username: email.trim(), password }),
      });

      if (!response.ok) {
        throw new Error("Correo electrónico o contraseña incorrectos");
      }

      const data = await response.json();
      localStorage.setItem("accessToken", data.access);
      localStorage.setItem("refreshToken", data.refresh);
      
      // Guardar también en cookies para compartir con HPS System
      const cookieOptions = 'path=/; SameSite=Lax; max-age=28800'; // 8 horas
      document.cookie = `accessToken=${data.access}; ${cookieOptions}`;
      document.cookie = `refreshToken=${data.refresh}; ${cookieOptions}`;

      // 🔥 Disparar evento para que el Layout se actualice inmediatamente
      window.dispatchEvent(new Event('tokenUpdated'));

      // Decodificar el token JWT para verificar si debe cambiar contraseña y rol
      try {
        const payload = jwtDecode<JWTPayload>(data.access);
        console.log("[LoginForm] Payload después de login:", {
          role: payload.role,
          must_change_password: payload.must_change_password,
          username: payload.username
        });
        
        // Verificar que el usuario tenga un rol permitido (admin o crypto)
        const allowedRoles = ['admin', 'crypto'];
        if (!payload.role || !allowedRoles.includes(payload.role)) {
          // Usuario no tiene permisos para acceder a CryptoTrace
          // Limpiar tokens y mostrar error
          localStorage.removeItem("accessToken");
          localStorage.removeItem("refreshToken");
          setError(`No tienes permisos para acceder a CryptoTrace. Tu rol actual es: ${payload.role || 'sin rol'}. Solo usuarios con rol 'admin' o 'crypto' pueden acceder.`);
          return;
        }
        
        // Usuario tiene rol permitido, proceder con la redirección
        if (payload.must_change_password) {
          // Si debe cambiar contraseña, redirigir a la página de cambio obligatorio
          console.log("[LoginForm] Debe cambiar contraseña, redirigiendo a /cambiar-password");
          router.push("/cambiar-password");
        } else {
          // Si no, continuar al dashboard normal
          console.log("[LoginForm] Login exitoso, redirigiendo a /productos");
          router.push("/productos");
        }
      } catch (jwtError) {
        console.error("Error decodificando JWT:", jwtError);
        // Si hay error decodificando, limpiar tokens y mostrar error
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        setError("Error al verificar credenciales. Por favor, intenta de nuevo.");
      }

    } catch (error) {
      setError(error instanceof Error ? error.message : "Error al iniciar sesión");
    }
  };

  // Mostrar loading mientras se verifica el token existente
  if (checkingToken) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Verificando sesión...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100">
      <div className="bg-white p-6 rounded-lg shadow-md w-96">
        <h2 className="text-2xl font-bold mb-4">Iniciar Sesión</h2>
        {error && <p className="text-red-500 mb-4">{error}</p>}
        <form onSubmit={handleLogin}>
          <div className="mb-2">
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Correo Electrónico
            </label>
            <input
              id="email"
              type="email"
              placeholder="correo@ejemplo.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              autoComplete="email"
            />
          </div>
          <div className="mb-4">
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              placeholder="Contraseña"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              autoComplete="current-password"
            />
          </div>
          <button type="submit" className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
            Iniciar Sesión
          </button>
        </form>
      </div>
    </div>
  );
} 