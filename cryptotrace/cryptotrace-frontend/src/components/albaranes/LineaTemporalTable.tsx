"use client";

interface Producto {
  codigo_producto: string;
  cantidad: number;
  tipo_cryptocustodio?: string; // Tipo de cryptocustodio ('c', 'CC' o 'Ninguno') - DIFERENTE del cc del AC21
}

interface LineaTemporalTableProps {
  productos: Producto[];
  tipos: string[];
  tipoAlbaran: string;
  onGuardarTipo: (codigoProducto: string, nuevoTipo: string) => void;
  onTipoAlbaranChange: (tipo: string) => void;
}

const TIPOS_ALBARAN = [
  { value: 'inventario', label: 'Entrada por inventario' },
  { value: 'transferencia', label: 'Transferencia (AC21)' },
  { value: 'entrega_mano', label: 'Entrega en mano (AC21)' }
];

// Ya no necesitamos mapear, el valor viene directamente como texto

export default function LineaTemporalTable({ 
  productos, 
  tipos, 
  tipoAlbaran,
  onGuardarTipo,
  onTipoAlbaranChange
}: LineaTemporalTableProps) {
  // Tipos de cryptocustodio disponibles
  const tiposCryptocustodio = ['c', 'CC', 'Ninguno'];

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border border-gray-300">
        <thead>
          <tr className="bg-gray-100">
            <th className="border p-2">Código Producto<br/>(TÍTULO CORTO / EDICIÓN)</th>
            <th className="border p-2">Cantidad</th>
            <th className="border p-2">Tipo Cryptocustodio</th>
          </tr>
        </thead>
        <tbody>
          {productos.map((producto, index) => (
            <tr key={`${producto.codigo_producto}-${index}`} className="border-b">
              <td className="border p-2">{producto.codigo_producto || '-'}</td>
              <td className="border p-2 text-center">{producto.cantidad || 1}</td>
              <td className="border p-2 text-center">
                <select
                  className="border p-2 w-full"
                  value={producto.tipo_cryptocustodio || 'Ninguno'}
                  onChange={(e) => {
                    // El valor viene directamente como 'c', 'CC' o 'Ninguno'
                    onGuardarTipo(producto.codigo_producto, e.target.value);
                  }}
                >
                  {tiposCryptocustodio.map((tipo) => (
                    <option key={tipo} value={tipo}>
                      {tipo}
                    </option>
                  ))}
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
} 