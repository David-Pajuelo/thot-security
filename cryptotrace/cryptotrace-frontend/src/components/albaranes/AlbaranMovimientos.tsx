"use client";

import { useEffect, useState } from "react";
import { Package, ArrowRightLeft } from "lucide-react";
import { fetchMovimientosAlbaran } from "@/lib/api";

interface Movimiento {
  id: number;
  producto_codigo: string;
  producto_descripcion: string;
  tipo_movimiento: string;
  tipo_movimiento_display: string;
  fecha: string;
  estado_anterior: string;
  estado_nuevo: string;
  numero_serie: string;
}

interface AlbaranMovimientosProps {
  albaranId: string;
  showAsTable?: boolean;
}

export default function AlbaranMovimientos({ albaranId, showAsTable = false }: AlbaranMovimientosProps) {
  const [movimientos, setMovimientos] = useState<Movimiento[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const formatearFecha = (fecha: string) => {
    const date = new Date(fecha);
    return date.toLocaleString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const traducirEstado = (estado: string) => {
    return estado === 'activo' ? 'En custodia' : 'Fuera de custodia';
  };

  useEffect(() => {
    const cargarMovimientos = async () => {
      try {
        setLoading(true);
        const data = await fetchMovimientosAlbaran(albaranId);
        setMovimientos(data);
      } catch (error) {
        console.error("❌ Error cargando movimientos:", error);
        setError("Error al cargar los movimientos");
      } finally {
        setLoading(false);
      }
    };

    cargarMovimientos();
  }, [albaranId]);

  if (loading) return showAsTable ? null : <p className="text-gray-500 text-center py-4">Cargando movimientos...</p>;
  if (error) return showAsTable ? null : <p className="text-red-500 text-center py-4">{error}</p>;
  if (movimientos.length === 0) {
    return showAsTable ? null : (
      <div className="text-center py-8">
        <ArrowRightLeft className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-500">No hay movimientos registrados para este albarán.</p>
      </div>
    );
  }

  // Si showAsTable es true, renderizar como filas de tabla para AC21
  if (showAsTable) {
    return (
      <>
        {movimientos.map((movimiento) => (
          <tr key={movimiento.id} className="hover:bg-gray-50">
            <td className="px-4 py-3 border-r border-gray-300">
              <div className="text-sm font-medium text-gray-900">
                {movimiento.producto_codigo}
              </div>
              <div className="text-sm text-gray-500">
                {movimiento.producto_descripcion}
              </div>
            </td>
            <td className="px-4 py-3 text-sm text-gray-900 border-r border-gray-300">
              1
            </td>
            <td className="px-4 py-3 text-sm text-gray-900 border-r border-gray-300">
              {movimiento.numero_serie || '-'}
            </td>
            <td className="px-4 py-3 text-sm text-gray-900">
              -
            </td>
          </tr>
        ))}
      </>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-gray-50">
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Producto</th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Número de Serie</th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Fecha</th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Estado Anterior</th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Estado Nuevo</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {movimientos.map((mov) => (
            <tr key={mov.id} className="hover:bg-gray-50">
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <Package className="w-4 h-4 text-gray-400" />
                  <div>
                    <p className="font-medium text-gray-900">{mov.producto_codigo}</p>
                    <p className="text-sm text-gray-500">{mov.producto_descripcion}</p>
                  </div>
                </div>
              </td>
              <td className="px-4 py-3">
                <div>
                  <p className="text-gray-900">{mov.numero_serie || '-'}</p>
                </div>
              </td>
              <td className="px-4 py-3 text-gray-900">{formatearFecha(mov.fecha)}</td>
              <td className="px-4 py-3">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  mov.estado_anterior === 'activo' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {traducirEstado(mov.estado_anterior)}
                </span>
              </td>
              <td className="px-4 py-3">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  mov.estado_nuevo === 'activo' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {traducirEstado(mov.estado_nuevo)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
} 