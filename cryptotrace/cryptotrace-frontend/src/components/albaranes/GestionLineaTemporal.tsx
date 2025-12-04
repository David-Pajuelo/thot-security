"use client";

import { useEffect, useState } from "react";
import { fetchProductosAgrupados, guardarTipoProducto, procesarAlbaran } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import LineaTemporalTable from "./LineaTemporalTable";

interface Producto {
  codigo_producto: string;
  descripcion: string;
  tipo: string;
  cantidad: number;
}

export default function GestionLineaTemporal() {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [tipos, setTipos] = useState<string[]>([]);
  const [tipoAlbaran, setTipoAlbaran] = useState<string>('inventario');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const cargarProductos = async () => {
      try {
        setLoading(true);
        const response = await fetchProductosAgrupados();
        setProductos(response.productos.map((prod: any) => ({
          ...prod,
          cantidad: prod.cantidad ?? 1,
          tipo: prod.tipo && prod.tipo.trim() !== '' ? prod.tipo : 'NINGUNO'
        })));
        setTipos(response.tipos_disponibles);
      } catch (error) {
        console.error("❌ Error cargando productos:", error);
        setError("Error cargando los productos");
      } finally {
        setLoading(false);
      }
    };

    cargarProductos();
  }, []);

  const handleGuardarTipo = async (codigoProducto: string, nuevoTipo: string) => {
    try {
      await guardarTipoProducto(codigoProducto, nuevoTipo);
      setMensaje("✅ Tipo asignado correctamente");

      setProductos((prevProductos) =>
        prevProductos.map((prod) =>
          prod.codigo_producto === codigoProducto ? { ...prod, tipo: nuevoTipo } : prod
        )
      );

      setTimeout(() => setMensaje(null), 2000);
    } catch (error) {
      console.error("❌ Error guardando el tipo:", error);
      setMensaje("❌ Error al guardar el tipo");
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
    // Mostrar advertencia si hay productos sin tipo, pero permitir procesar
    const productosSinTipo = productos.filter((prod) => !prod.tipo || prod.tipo === 'NINGUNO');
    if (productosSinTipo.length > 0) {
      console.warn(`⚠️ ${productosSinTipo.length} producto(s) sin tipo asignado. Se procesarán sin tipo.`);
    }

    try {
      // El backend no requiere payload, procesa todos los productos temporales del usuario
      await procesarAlbaran();
      setMensaje('✅ Albarán procesado correctamente');
      setTimeout(() => {
        router.push('/albaranes');
      }, 1000);
    } catch (error: any) {
      console.error('❌ Error procesando el albarán:', error);
      const errorMessage = error?.message || error?.detail || 'Error desconocido';
      setMensaje(`❌ Error al procesar el albarán: ${errorMessage}`);
      setTimeout(() => setMensaje(null), 5000);
    }
  };

  return (
    <div className="relative">
      {mensaje && (
        <div className="absolute top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-md shadow-md transition-opacity duration-500">
          {mensaje}
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