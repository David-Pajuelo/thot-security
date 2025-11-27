'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { User, Mail, Calendar, Shield, Lock } from 'lucide-react';
import { obtenerPerfilUsuario } from '@/lib/api';
import CambiarPassword from '@/components/auth/CambiarPassword';
import ProtectedRoute from '@/components/protectedRoute';

interface PerfilUsuario {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  must_change_password: boolean;
  created_at: string;
}

export default function PerfilPage() {
  const [perfil, setPerfil] = useState<PerfilUsuario | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCambiarPassword, setShowCambiarPassword] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    cargarPerfil();
  }, []);

  const cargarPerfil = async () => {
    try {
      setLoading(true);
      const data = await obtenerPerfilUsuario();
      setPerfil(data);
    } catch (error) {
      console.error('Error cargando perfil:', error);
      setError('Error al cargar el perfil');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChangeSuccess = () => {
    setShowCambiarPassword(false);
    // Recargar perfil para actualizar datos
    cargarPerfil();
  };

  if (showCambiarPassword) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50">
          <div className="p-4">
            <Button 
              onClick={() => setShowCambiarPassword(false)}
              variant="outline"
              className="mb-4"
            >
              ← Volver al perfil
            </Button>
          </div>
          <CambiarPassword 
            isRequired={false} 
            onSuccess={handlePasswordChangeSuccess}
          />
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="container mx-auto p-4 max-w-4xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">Mi Perfil</h1>
          <p className="text-gray-600">Gestiona tu información personal y configuración</p>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
              </div>
            </CardContent>
          </Card>
        ) : perfil ? (
          <div className="grid gap-6 md:grid-cols-2">
            {/* Información Personal */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Información Personal
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-600">Usuario</label>
                  <p className="text-lg font-semibold">{perfil.username}</p>
                </div>

                {perfil.first_name && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-600">Nombre</label>
                    <p className="text-lg">{perfil.first_name}</p>
                  </div>
                )}

                {perfil.last_name && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-600">Apellidos</label>
                    <p className="text-lg">{perfil.last_name}</p>
                  </div>
                )}

                {perfil.email && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-600 flex items-center gap-1">
                      <Mail className="h-4 w-4" />
                      Email
                    </label>
                    <p className="text-lg">{perfil.email}</p>
                  </div>
                )}

                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-600 flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    Cuenta creada
                  </label>
                  <p className="text-lg">
                    {new Date(perfil.created_at).toLocaleDateString('es-ES', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Seguridad */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Seguridad
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-600">Estado de la contraseña</label>
                  <div>
                    {perfil.must_change_password ? (
                      <Badge variant="destructive" className="flex items-center gap-1 w-fit">
                        <Lock className="h-3 w-3" />
                        Cambio obligatorio pendiente
                      </Badge>
                    ) : (
                      <Badge variant="default" className="flex items-center gap-1 w-fit bg-green-100 text-green-800">
                        <Lock className="h-3 w-3" />
                        Contraseña actualizada
                      </Badge>
                    )}
                  </div>
                </div>

                <div className="pt-4">
                  <Button 
                    onClick={() => setShowCambiarPassword(true)}
                    className="w-full"
                    variant={perfil.must_change_password ? "destructive" : "outline"}
                  >
                    <Lock className="h-4 w-4 mr-2" />
                    {perfil.must_change_password ? 'Cambiar contraseña ahora' : 'Cambiar contraseña'}
                  </Button>
                </div>

                {perfil.must_change_password && (
                  <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                    <p className="text-sm text-orange-700">
                      ⚠️ Debes cambiar tu contraseña temporal antes de continuar usando el sistema.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        ) : (
          <Card>
            <CardContent className="p-6 text-center">
              <p className="text-gray-600">No se pudo cargar la información del perfil</p>
            </CardContent>
          </Card>
        )}
      </div>
    </ProtectedRoute>
  );
} 