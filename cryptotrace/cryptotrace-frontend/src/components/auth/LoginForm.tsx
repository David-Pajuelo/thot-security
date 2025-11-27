"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { jwtDecode } from "jwt-decode";

interface JWTPayload {
  user_id: number;
  username: string;
  first_name: string;
  last_name: string;
  is_superuser: boolean;
  must_change_password: boolean;
  exp: number;
}

export default function LoginForm() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/token/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error("Usuario o contraseña incorrectos");
      }

      const data = await response.json();
      localStorage.setItem("accessToken", data.access);
      localStorage.setItem("refreshToken", data.refresh);

      // 🔥 Disparar evento para que el Layout se actualice inmediatamente
      window.dispatchEvent(new Event('tokenUpdated'));

      // Decodificar el token JWT para verificar si debe cambiar contraseña
      try {
        const payload = jwtDecode<JWTPayload>(data.access);
        
        if (payload.must_change_password) {
          // Si debe cambiar contraseña, redirigir a la página de cambio obligatorio
          router.push("/cambiar-password");
        } else {
          // Si no, continuar al dashboard normal
          router.push("/productos");
        }
      } catch (jwtError) {
        console.error("Error decodificando JWT:", jwtError);
        // Si hay error decodificando, ir al dashboard (fallback)
        router.push("/productos");
      }

    } catch (error) {
      setError(error instanceof Error ? error.message : "Error al iniciar sesión");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100">
      <div className="bg-white p-6 rounded-lg shadow-md w-96">
        <h2 className="text-2xl font-bold mb-4">Iniciar Sesión</h2>
        {error && <p className="text-red-500 mb-4">{error}</p>}
        <form onSubmit={handleLogin}>
          <input
            type="text"
            placeholder="Usuario"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full p-2 mb-2 border rounded"
          />
          <input
            type="password"
            placeholder="Contraseña"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-2 mb-4 border rounded"
          />
          <button type="submit" className="w-full bg-blue-500 text-white p-2 rounded">
            Iniciar Sesión
          </button>
        </form>
      </div>
    </div>
  );
} 