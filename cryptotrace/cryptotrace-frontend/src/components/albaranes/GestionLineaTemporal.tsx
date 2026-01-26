"use client";

import { useEffect, useState } from "react";
import { fetchProductosAgrupados, guardarTipoCryptocustodio, procesarAlbaran } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import LineaTemporalTable from "./LineaTemporalTable";

interface TipoProducto {
  id: number;
  nombre: string;
}

interface Producto {
  codigo_producto: string;
  cantidad: number;
  tipo_producto_id?: number | null; // ID del TipoProducto asignado
  tipo_producto_nombre?: string | null; // Nombre del TipoProducto asignado
  tipo_catalogo_id?: number | null; // ID del tipo desde CatalogoProducto (para carga automática)
  tipo_catalogo_nombre?: string | null; // Nombre del tipo desde CatalogoProducto
}

interface GestionLineaTemporalProps {
  onClose?: () => void;
}

export default function GestionLineaTemporal({ onClose }: GestionLineaTemporalProps = {}) {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [tipos, setTipos] = useState<TipoProducto[]>([]);
  const [tipoAlbaran, setTipoAlbaran] = useState<string>('inventario');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const router = useRouter();

  const cargarProductos = async () => {
    try {
      setLoading(true);
      const response = await fetchProductosAgrupados();
      
      // Buscar el tipo "NINGUNO" para usarlo como valor por defecto
      const tipoNinguno = response.tipos_disponibles.find((t: TipoProducto) => t.nombre === 'NINGUNO');
      const tipoNingunoId = tipoNinguno?.id || null;
      
      setProductos(response.productos.map((prod: any) => {
        // Si hay tipo_producto_id, usarlo; si no, usar tipo_catalogo_id; si no, usar NINGUNO
        let tipoProductoId = prod.tipo_producto_id;
        let tipoProductoNombre = prod.tipo_producto_nombre;
        
        if (!tipoProductoId && prod.tipo_catalogo_id) {
          // Carga automática desde CatalogoProducto
          tipoProductoId = prod.tipo_catalogo_id;
          tipoProductoNombre = prod.tipo_catalogo_nombre;
        } else if (!tipoProductoId) {
          // Valor por defecto: NINGUNO
          tipoProductoId = tipoNingunoId;
          tipoProductoNombre = tipoNinguno?.nombre || null;
        }
        
        return {
          codigo_producto: prod.codigo_producto,
          cantidad: prod.cantidad ?? 1,
          tipo_producto_id: tipoProductoId,
          tipo_producto_nombre: tipoProductoNombre,
          tipo_catalogo_id: prod.tipo_catalogo_id,
          tipo_catalogo_nombre: prod.tipo_catalogo_nombre
        };
      }));
      setTipos(response.tipos_disponibles);
    } catch (error) {
      console.error("❌ Error cargando productos:", error);
      setError("Error cargando los productos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargarProductos();
  }, []);

  // Recargar productos cuando la ventana recibe foco (por si se procesó un nuevo AC21 en otra pestaña)
  useEffect(() => {
    const handleFocus = () => {
      cargarProductos();
    };
    
    window.addEventListener('focus', handleFocus);
    return () => {
      window.removeEventListener('focus', handleFocus);
    };
  }, []);

  const handleGuardarTipo = async (codigoProducto: string, tipoProductoId: number | null) => {
    try {
      if (!tipoProductoId) {
        setMensaje("❌ Debe seleccionar un tipo de cryptocustodio");
        setTimeout(() => setMensaje(null), 3000);
        return;
      }
      
      await guardarTipoCryptocustodio(codigoProducto, tipoProductoId);
      setMensaje("✅ Tipo de cryptocustodio asignado correctamente");

      // Actualizar el producto con el nuevo tipo
      const tipoSeleccionado = tipos.find(t => t.id === tipoProductoId);
      setProductos((prevProductos) =>
        prevProductos.map((prod) =>
          prod.codigo_producto === codigoProducto 
            ? { 
                ...prod, 
                tipo_producto_id: tipoProductoId,
                tipo_producto_nombre: tipoSeleccionado?.nombre || null
              } 
            : prod
        )
      );

      setTimeout(() => setMensaje(null), 2000);
    } catch (error) {
      console.error("❌ Error guardando el tipo de cryptocustodio:", error);
      setMensaje("❌ Error al guardar el tipo de cryptocustodio");
      setTimeout(() => setMensaje(null), 3000);
    }
  };

  const handleProcesarAlbaran = async () => {
    // Verificar que hay productos para procesar
    if (productos.length === 0) {
      setMensaje('❌ No hay productos para procesar.');
      setTimeout(() => setMensaje(null), 3000);
      return;
    }

    // El backend procesa todos los productos temporales no procesados del usuario,
    // no necesita que se envíen en el payload. Solo verificamos que existan productos.
    // Todos los productos tienen un tipo de cryptocustodio (cc), así que no hay advertencia necesaria

    try {
      // El backend procesa todos los productos temporales del mismo documento (numero_albaran)
      console.log('🔄 [FRONTEND] Iniciando procesamiento de albarán...');
      const result = await procesarAlbaran();
      console.log('✅ [FRONTEND] Respuesta del backend:', result);
      
      if (result && result.albaran_id) {
        setMensaje(`✅ Albarán procesado correctamente (ID: ${result.albaran_id}, Número: ${result.albaran_numero || 'N/A'})`);
      } else {
        setMensaje('✅ Albarán procesado correctamente');
      }
      
      // Recargar productos para reflejar los cambios (aunque luego se redirija)
      await cargarProductos();
      
      // Si hay callback onClose (modal), cerrar el modal
      // Si no, redirigir a upload AC21
      setTimeout(() => {
        if (onClose) {
          onClose();
        } else {
          router.push('/albaranes/upload-ac21');
        }
      }, 1000);
    } catch (error: any) {
      console.error('❌ Error procesando el albarán:', error);
      const errorMessage = error?.message || error?.detail || 'Error desconocido';
      setMensaje(`❌ Error al procesar el albarán: ${errorMessage}`);
      setTimeout(() => setMensaje(null), 5000);
      
      // Recargar productos incluso si hubo error, por si se procesó parcialmente
      cargarProductos();
    }
  };

  return (
    <div className="relative">
      {mensaje && (
        <div className="absolute top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-md shadow-md transition-opacity duration-500">
          {mensaje}
        </div>
      )}

      {/* Botón Volver - Solo mostrar si no está en modal (no hay onClose) */}
      {!onClose && (
        <div className="mb-4">
          <Button
            onClick={() => router.push('/albaranes/upload-ac21')}
            variant="outline"
            className="flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Volver al procesamiento de AC21
          </Button>
        </div>
      )}

      {loading && <p>Cargando productos...</p>}
      {error && <p className="text-red-500">{error}</p>}
      
      {!loading && !error && (
        <>
          <LineaTemporalTable 
            productos={productos}
            tipos={tipos}
            tipoAlbaran={tipoAlbaran}
            onGuardarTipo={handleGuardarTipo}
            onTipoAlbaranChange={setTipoAlbaran}
          />

          <div className="mt-6 flex justify-center">
            <Button
              onClick={handleProcesarAlbaran}
              disabled={productos.length === 0}
              className={`px-6 py-3 font-semibold rounded-lg transition 
                ${productos.length > 0 
                  ? 'bg-green-500 text-white hover:bg-green-600' 
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'}
              `}
            >
              🚀 Procesar Albarán
            </Button>
          </div>

          {productos.length === 0 && (
            <p className="text-red-500 text-center mt-2">
              ⚠️ No hay productos en la línea temporal para procesar.
            </p>
          )}
        </>
      )}
    </div>
  );
} 