"use client";

import { useEffect, useState } from "react";
import { fetchProductosAgrupados, guardarTipoCryptocustodio, procesarAlbaran } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import LineaTemporalTable from "./LineaTemporalTable";

interface Producto {
  codigo_producto: string;
  cantidad: number;
  tipo_cryptocustodio?: string; // Tipo de cryptocustodio ('c', 'CC' o 'Ninguno') - DIFERENTE del cc del AC21
}

interface GestionLineaTemporalProps {
  onClose?: () => void;
}

export default function GestionLineaTemporal({ onClose }: GestionLineaTemporalProps = {}) {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [tipos, setTipos] = useState<string[]>([]);
  const [tipoAlbaran, setTipoAlbaran] = useState<string>('inventario');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const router = useRouter();

  const cargarProductos = async () => {
    try {
      setLoading(true);
      const response = await fetchProductosAgrupados();
      setProductos(response.productos.map((prod: any) => ({
        codigo_producto: prod.codigo_producto,
        cantidad: prod.cantidad ?? 1,
        tipo_cryptocustodio: prod.tipo_cryptocustodio ?? 'Ninguno' // Por defecto 'Ninguno'
      })));
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

  const handleGuardarTipo = async (codigoProducto: string, nuevoTipoCryptocustodio: string) => {
    try {
      // nuevoTipoCryptocustodio viene directamente como 'c', 'CC' o 'Ninguno' desde el select
      await guardarTipoCryptocustodio(codigoProducto, nuevoTipoCryptocustodio);
      setMensaje("✅ Tipo de cryptocustodio asignado correctamente");

      setProductos((prevProductos) =>
        prevProductos.map((prod) =>
          prod.codigo_producto === codigoProducto ? { ...prod, tipo_cryptocustodio: nuevoTipoCryptocustodio } : prod
        )
      );

      setTimeout(() => setMensaje(null), 2000);
    } catch (error) {
      console.error("❌ Error guardando el tipo de cryptocustodio:", error);
      setMensaje("❌ Error al guardar el tipo de cryptocustodio");
      setTimeout(() => setMensaje(null), 3000);
    }
  };

  const todosTipificados = productos.every((prod) => prod.tipo);

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
      const result = await procesarAlbaran();
      setMensaje('✅ Albarán procesado correctamente');
      
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