'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-react';
import { cambiarPassword } from '@/lib/api';

interface CambiarPasswordProps {
  isRequired?: boolean; // Si es cambio obligatorio o voluntario
  onSuccess?: () => void;
}

export default function CambiarPassword({ isRequired = false, onSuccess }: CambiarPasswordProps) {
  const [passwords, setPasswords] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    // Validaciones locales
    if (!passwords.current_password || !passwords.new_password || !passwords.confirm_password) {
      setError('Todos los campos son obligatorios');
      setLoading(false);
      return;
    }

    if (passwords.new_password !== passwords.confirm_password) {
      setError('Las contraseñas nuevas no coinciden');
      setLoading(false);
      return;
    }

    if (passwords.new_password.length < 8) {
      setError('La nueva contraseña debe tener al menos 8 caracteres');
      setLoading(false);
      return;
    }

    try {
      const response = await cambiarPassword(passwords);
      
      if (response.password_change_required === false || !isRequired) {
        setSuccess(response.message);
        
        if (isRequired) {
          // Si era cambio obligatorio, redirigir al dashboard después de unos segundos
          setTimeout(() => {
            router.push('/');
          }, 2000);
        } else {
          // Si es cambio voluntario, llamar callback
          setTimeout(() => {
            onSuccess?.();
          }, 1500);
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al cambiar la contraseña');
    } finally {
      setLoading(false);
    }
  };

  const toggleShowPassword = (field: 'current' | 'new' | 'confirm') => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  return (
    <div className={`min-h-screen flex items-center justify-center ${isRequired ? 'bg-gray-50' : ''}`}>
      <Card className="w-full max-w-md mx-4">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">
            {isRequired ? '🔐 Cambio de Contraseña Obligatorio' : '🔐 Cambiar Contraseña'}
          </CardTitle>
          <CardDescription>
            {isRequired 
              ? 'Debes cambiar tu contraseña temporal antes de acceder al sistema'
              : 'Actualiza tu contraseña por seguridad'
            }
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          {error && (
            <Alert className="mb-4 border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-700">{error}</AlertDescription>
            </Alert>
          )}

          {success && (
            <Alert className="mb-4 border-green-200 bg-green-50">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-700">{success}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Contraseña actual */}
            <div className="space-y-2">
              <Label htmlFor="current_password">Contraseña Actual</Label>
              <div className="relative">
                <Input
                  id="current_password"
                  type={showPasswords.current ? 'text' : 'password'}
                  value={passwords.current_password}
                  onChange={(e) => setPasswords(prev => ({ ...prev, current_password: e.target.value }))}
                  placeholder="Tu contraseña actual"
                  required
                  disabled={loading}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2"
                  onClick={() => toggleShowPassword('current')}
                  disabled={loading}
                >
                  {showPasswords.current ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            {/* Nueva contraseña */}
            <div className="space-y-2">
              <Label htmlFor="new_password">Nueva Contraseña</Label>
              <div className="relative">
                <Input
                  id="new_password"
                  type={showPasswords.new ? 'text' : 'password'}
                  value={passwords.new_password}
                  onChange={(e) => setPasswords(prev => ({ ...prev, new_password: e.target.value }))}
                  placeholder="Mínimo 8 caracteres"
                  required
                  disabled={loading}
                  minLength={8}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2"
                  onClick={() => toggleShowPassword('new')}
                  disabled={loading}
                >
                  {showPasswords.new ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            {/* Confirmar nueva contraseña */}
            <div className="space-y-2">
              <Label htmlFor="confirm_password">Confirmar Nueva Contraseña</Label>
              <div className="relative">
                <Input
                  id="confirm_password"
                  type={showPasswords.confirm ? 'text' : 'password'}
                  value={passwords.confirm_password}
                  onChange={(e) => setPasswords(prev => ({ ...prev, confirm_password: e.target.value }))}
                  placeholder="Repetir nueva contraseña"
                  required
                  disabled={loading}
                  minLength={8}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2"
                  onClick={() => toggleShowPassword('confirm')}
                  disabled={loading}
                >
                  {showPasswords.confirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Cambiando...' : isRequired ? 'Cambiar y Acceder' : 'Cambiar Contraseña'}
            </Button>
          </form>

          {isRequired && (
            <div className="mt-4 text-sm text-gray-600 text-center">
              <p>⚠️ No podrás acceder al sistema hasta cambiar tu contraseña</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 