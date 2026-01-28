"use client";

interface TipoProducto {
  id: number;
  nombre: string;
}

interface Producto {
  codigo_producto: string;
  cantidad: number;
  tipo_producto_id?: number | null;
  tipo_producto_nombre?: string | null;
  tipo_catalogo_id?: number | null;
  tipo_catalogo_nombre?: string | null;
}

interface LineaTemporalTableProps {
  productos: Producto[];
  tipos: TipoProducto[];
  tipoAlbaran: string;
  onGuardarTipo: (codigoProducto: string, tipoProductoId: number | null) => void;
  onTipoAlbaranChange: (tipo: string) => void;
}

const TIPOS_ALBARAN = [
  { value: 'inventario', label: 'Entrada por inventario' },
  { value: 'transferencia', label: 'Transferencia (AC21)' },
  { value: 'entrega_mano', label: 'Entrega en mano (AC21)' }
];

export default function LineaTemporalTable({ 
  productos, 
  tipos, 
  tipoAlbaran,
  onGuardarTipo,
  onTipoAlbaranChange
}: LineaTemporalTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border border-gray-300">
        <thead>
          <tr className="bg-gray-100">
            <th className="border p-2">Código Producto<br/>(TÍTULO CORTO / EDICIÓN)</th>
            <th className="border p-2">Tipo Cryptocustodio (CC)</th>
          </tr>
        </thead>
        <tbody>
          {productos.map((producto, index) => (
            <tr key={`${producto.codigo_producto}-${index}`} className="border-b">
              <td className="border p-2">{producto.codigo_producto || '-'}</td>
              <td className="border p-2 text-center">
                <select
                  className="border p-2 w-full"
                  value={producto.tipo_producto_id || producto.tipo_catalogo_id || ''}
                  onChange={(e) => {
                    const tipoProductoId = e.target.value ? parseInt(e.target.value, 10) : null;
                    onGuardarTipo(producto.codigo_producto, tipoProductoId);
                  }}
                >
                  <option value="">NINGUNO</option>
                  {tipos.map((tipo) => (
                    <option key={tipo.id} value={tipo.id}>
                      {tipo.nombre}
                    </option>
                  ))}
                </select>
                {producto.tipo_catalogo_id && !producto.tipo_producto_id && (
                  <span className="text-xs text-gray-500 block mt-1">
                    (Cargado automáticamente desde catálogo)
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
} 