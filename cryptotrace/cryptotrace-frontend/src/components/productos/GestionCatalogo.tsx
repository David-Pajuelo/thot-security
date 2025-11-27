"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Trash2, Wand2, AlertTriangle, CheckCircle, Info, RefreshCw } from "lucide-react";
import { obtenerProductosSinTipo, limpiarProductosHuerfanos, asignarTiposAutomatico } from "@/lib/api";

interface ProductoSinTipo {
  id: number;
  codigo_producto: string;
  descripcion: string;
  ultima_actualizacion: string;
  movimientos_count: number;
  es_huerfano: boolean;
}

interface AsignacionSugerida {
  producto_id: number;
  codigo: string;
  descripcion: string;
  tipo_sugerido_id: number;
  tipo_sugerido_nombre: string;
  razon: string;
}

export default function GestionCatalogo() {
  const [productos, setProductos] = useState<ProductoSinTipo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [estadisticas, setEstadisticas] = useState({ total: 0, huerfanos: 0, con_movimientos: 0 });
  const [asignacionesSugeridas, setAsignacionesSugeridas] = useState<AsignacionSugerida[]>([]);
  const [mostrandoAsignaciones, setMostrandoAsignaciones] = useState(false);

  useEffect(() => {
    cargarProductosSinTipo();
  }, []);

  const cargarProductosSinTipo = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await obtenerProductosSinTipo();
      setProductos(response.productos);
      setEstadisticas({
        total: response.total,
        huerfanos: response.huerfanos,
        con_movimientos: response.con_movimientos
      });
    } catch (error: any) {
      console.error("Error cargando productos sin tipo:", error);
      setError("Error al cargar productos sin tipo");
    } finally {
      setLoading(false);
    }
  };

  const handleLimpiarHuerfanos = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Primera llamada para obtener confirmación
      const response = await limpiarProductosHuerfanos(false);
      
      if (response.requiere_confirmacion) {
        const confirmar = window.confirm(
          `¿Estás seguro de que quieres eliminar ${response.total} productos huérfanos del catálogo?\n\n` +
          `Estos productos no tienen tipo asignado y no tienen movimientos asociados.\n\n` +
          `Esta acción no se puede deshacer.`
        );
        
        if (confirmar) {
          // Segunda llamada con confirmación
          const resultadoFinal = await limpiarProductosHuerfanos(true);
          setMensaje(`✅ ${resultadoFinal.mensaje}`);
          cargarProductosSinTipo(); // Recargar lista
        }
      }
    } catch (error: any) {
      console.error("Error limpiando productos huérfanos:", error);
      setError("Error al limpiar productos huérfanos");
    } finally {
      setLoading(false);
    }
  };

  const handleAsignacionAutomatica = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await asignarTiposAutomatico(false);
      
      if (response.requiere_confirmacion) {
        setAsignacionesSugeridas(response.asignaciones_sugeridas);
        setMostrandoAsignaciones(true);
        setMensaje(`💡 Se encontraron ${response.total_sugerencias} asignaciones automáticas sugeridas`);
      } else {
        setMensaje("No se encontraron asignaciones automáticas posibles");
      }
    } catch (error: any) {
      console.error("Error en asignación automática:", error);
      setError("Error en asignación automática");
    } finally {
      setLoading(false);
    }
  };

  const aplicarAsignaciones = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Preparar asignaciones para aplicar
      const asignacionesParaAplicar = asignacionesSugeridas.map(asig => ({
        producto_id: asig.producto_id,
        tipo_id: asig.tipo_sugerido_id
      }));
      
      const response = await asignarTiposAutomatico(true, asignacionesParaAplicar);
      
      if (response.success) {
        setMensaje(`✅ ${response.mensaje}`);
        setMostrandoAsignaciones(false);
        setAsignacionesSugeridas([]);
        cargarProductosSinTipo(); // Recargar lista
      }
    } catch (error: any) {
      console.error("Error aplicando asignaciones:", error);
      setError("Error aplicando asignaciones automáticas");
    } finally {
      setLoading(false);
    }
  };

  const formatearFecha = (fecha: string) => {
    return new Date(fecha).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Gestión del Catálogo</h2>
        <Button 
          onClick={cargarProductosSinTipo}
          disabled={loading}
          variant="outline"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </div>

      {/* Estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <Info className="w-8 h-8 text-blue-500" />
            <div>
              <p className="text-sm text-gray-600">Total sin tipo</p>
              <p className="text-2xl font-bold">{estadisticas.total}</p>
            </div>
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="w-8 h-8 text-orange-500" />
            <div>
              <p className="text-sm text-gray-600">Huérfanos</p>
              <p className="text-2xl font-bold">{estadisticas.huerfanos}</p>
            </div>
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <CheckCircle className="w-8 h-8 text-green-500" />
            <div>
              <p className="text-sm text-gray-600">Con movimientos</p>
              <p className="text-2xl font-bold">{estadisticas.con_movimientos}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Acciones */}
      <div className="flex flex-wrap gap-4">
        <Button 
          onClick={handleLimpiarHuerfanos}
          disabled={loading || estadisticas.huerfanos === 0}
          variant="destructive"
        >
          <Trash2 className="w-4 h-4 mr-2" />
          Limpiar Productos Huérfanos ({estadisticas.huerfanos})
        </Button>
        
        <Button 
          onClick={handleAsignacionAutomatica}
          disabled={loading || estadisticas.total === 0}
          variant="default"
        >
          <Wand2 className="w-4 h-4 mr-2" />
          Asignación Automática
        </Button>
      </div>

      {/* Mensajes */}
      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-500" />
          <div className="text-red-700">{error}</div>
        </Alert>
      )}

      {mensaje && (
        <Alert className="border-blue-200 bg-blue-50">
          <Info className="h-4 w-4 text-blue-500" />
          <div className="text-blue-700">{mensaje}</div>
        </Alert>
      )}

      {/* Asignaciones sugeridas */}
      {mostrandoAsignaciones && asignacionesSugeridas.length > 0 && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Asignaciones Automáticas Sugeridas</h3>
            <div className="space-x-2">
              <Button onClick={aplicarAsignaciones} disabled={loading}>
                Aplicar Todas
              </Button>
              <Button 
                onClick={() => setMostrandoAsignaciones(false)} 
                variant="outline"
              >
                Cancelar
              </Button>
            </div>
          </div>
          
          <div className="space-y-3">
            {asignacionesSugeridas.map((asignacion, index) => (
              <div key={index} className="border rounded-lg p-4 bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="font-medium">{asignacion.codigo}</p>
                    <p className="text-sm text-gray-600">{asignacion.descripcion}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-500">→</p>
                  </div>
                  <div className="flex-1 text-right">
                    <Badge variant="outline">{asignacion.tipo_sugerido_nombre}</Badge>
                    <p className="text-xs text-gray-500 mt-1">{asignacion.razon}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Lista de productos sin tipo */}
      {productos.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Productos Sin Tipo Asignado</h3>
          <div className="space-y-3">
            {productos.map((producto) => (
              <div key={producto.id} className="border rounded-lg p-4 bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <p className="font-medium">{producto.codigo_producto}</p>
                      {producto.es_huerfano ? (
                        <Badge variant="destructive">Huérfano</Badge>
                      ) : (
                        <Badge variant="outline">{producto.movimientos_count} movimientos</Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-600">{producto.descripcion}</p>
                    <p className="text-xs text-gray-500">
                      Creado: {formatearFecha(producto.ultima_actualizacion)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {productos.length === 0 && !loading && (
        <Card className="p-8 text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">¡Excelente!</h3>
          <p className="text-gray-600">No hay productos sin tipo asignado en el catálogo.</p>
        </Card>
      )}
    </div>
  );
} 