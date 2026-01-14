"use client";

interface Producto {
  codigo_producto: string;
  descripcion: string;
  tipo: string;
  cantidad: number;
  numero_serie_inicio?: string;
  numero_serie_fin?: string;
  rango_serie?: string;
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

export default function LineaTemporalTable({ 
  productos, 
  tipos, 
  tipoAlbaran,
  onGuardarTipo,
  onTipoAlbaranChange
}: LineaTemporalTableProps) {
  // Antes de renderizar la tabla, crea un array de tipos con 'NINGUNO' al principio y sin duplicados
  const tiposConNinguno = ['NINGUNO', ...tipos.filter(t => t !== 'NINGUNO')];

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border border-gray-300">
        <thead>
          <tr className="bg-gray-100">
            <th className="border p-2">Código Producto<br/>(TÍTULO CORTO / EDICIÓN)</th>
            <th className="border p-2">Descripción<br/>(OBSERVACIONES)</th>
            <th className="border p-2">Cantidad</th>
            <th className="border p-2">Números de Serie<br/>(Inicio - Fin)</th>
            <th className="border p-2">Tipo</th>
          </tr>
        </thead>
        <tbody>
          {productos.map((producto) => (
            <tr key={producto.codigo_producto} className="border-b">
              <td className="border p-2">{producto.codigo_producto || '-'}</td>
              <td className="border p-2">{producto.descripcion || '-'}</td>
              <td className="border p-2 text-center">{producto.cantidad || 1}</td>
              <td className="border p-2 text-center text-sm">
                {(() => {
                  // Priorizar rango_serie del backend (ya formateado)
                  if (producto.rango_serie) {
                    return producto.rango_serie;
                  }
                  // Si hay inicio Y fin
                  if (producto.numero_serie_inicio && producto.numero_serie_fin) {
                    // Si son iguales, mostrar solo uno (una sola unidad)
                    if (producto.numero_serie_inicio === producto.numero_serie_fin) {
                      return producto.numero_serie_inicio;
                    }
                    // Si son diferentes, mostrar rango "inicio - fin"
                    return `${producto.numero_serie_inicio} - ${producto.numero_serie_fin}`;
                  }
                  // Si solo hay uno, mostrarlo
                  if (producto.numero_serie_inicio) {
                    return producto.numero_serie_inicio;
                  }
                  if (producto.numero_serie_fin) {
                    return producto.numero_serie_fin;
                  }
                  // Si no hay ninguno, mostrar guion
                  return '-';
                })()}
              </td>
              <td className="border p-2 text-center">
                <select
                  className="border p-2 w-full"
                  value={producto.tipo || (tiposConNinguno.includes('NINGUNO') ? 'NINGUNO' : '')}
                  onChange={(e) => onGuardarTipo(producto.codigo_producto, e.target.value)}
                >
                  {tiposConNinguno.map((tipo) => (
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