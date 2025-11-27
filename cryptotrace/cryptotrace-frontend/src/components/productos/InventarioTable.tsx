"use client";

import { useEffect, useState, useCallback } from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { fetchInventario, fetchInventarioResumen } from "@/lib/api";
import debounce from 'lodash/debounce';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface InventarioProducto {
  id: number;
  codigo_producto: string;
  numero_serie: string;
  descripcion: string;
  tipo_nombre: string;
  estado: string;
  estado_display: string;
  ubicacion: string;
  ultima_actualizacion: string;
  ultimo_movimiento_info: {
    tipo_movimiento: string;
    tipo_movimiento_display: string;
    albaran_numero: string;
    albaran_id: string;
    fecha: string;
  } | null;
  notas: string;
}

interface ResumenInventario {
  total: number;
  en_custodia: number;
  fuera_custodia: number;
}

export default function InventarioTable() {
  const [data, setData] = useState<InventarioProducto[]>([]);
  const [filteredData, setFilteredData] = useState<InventarioProducto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [estadoFilter, setEstadoFilter] = useState("");
  const [summary, setSummary] = useState<ResumenInventario>({
    total: 0,
    en_custodia: 0,
    fuera_custodia: 0,
  });
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const router = useRouter();

  // Función de filtrado
  const filterData = useCallback((term: string, estado: string, items: InventarioProducto[]) => {
    return items.filter(item => {
      const lowerTerm = term.toLowerCase();
      const matchesSearch = !term || [
        item.codigo_producto,
        item.numero_serie,
        item.descripcion,
        item.tipo_nombre,
        item.ubicacion,
        item.estado_display,
        item.notas,
        item.ultimo_movimiento_info?.albaran_numero,
        item.ultimo_movimiento_info?.tipo_movimiento_display,
        item.ultimo_movimiento_info?.fecha ? new Date(item.ultimo_movimiento_info.fecha).toLocaleString('es-ES') : ''
      ].some(field => (field?.toLowerCase() || '').includes(lowerTerm));

      const matchesEstado = !estado || (
        estado === 'en_custodia' ? item.estado === 'activo' : item.estado === 'inactivo'
      );

      return matchesSearch && matchesEstado;
    });
  }, []);

  // Debounced search handler con dependencias explícitas
  const debouncedSearch = useCallback(
    debounce((term: string) => {
      setSearchTerm(term);
      setFilteredData(prevData => filterData(term, estadoFilter, data));
    }, 300),
    [estadoFilter, data, filterData]
  );

  // Selección individual
  const handleSelect = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((sid) => sid !== id) : [...prev, id]
    );
  };

  // Selección general
  const handleSelectAll = () => {
    if (selectedIds.length === filteredData.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredData.map((item) => item.id));
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [inventarioData, resumenData] = await Promise.all([
          fetchInventario(),
          fetchInventarioResumen()
        ]);
        
        console.log('Datos del inventario:', inventarioData);
        setData(inventarioData);
        setFilteredData(inventarioData);
        setSummary(resumenData);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching data:", error);
        setError(error instanceof Error ? error.message : "Error al cargar el inventario");
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Efecto para el filtro de estado
  useEffect(() => {
    setFilteredData(filterData(searchTerm, estadoFilter, data));
  }, [estadoFilter, data, filterData, searchTerm]);

  if (loading) return <p className="text-center text-gray-500">Cargando inventario...</p>;
  if (error) return <p className="text-center text-red-500">{error}</p>;

  return (
    <div className="max-w-7xl mx-auto p-4">
      <h1 className="text-4xl font-bold text-center mb-6">Inventario de Productos</h1>

      {/* Botón para crear AC21 */}
      <div className="mb-4 flex justify-end">
        <button
          className={`px-4 py-2 rounded bg-blue-600 text-white font-semibold shadow transition disabled:bg-gray-300 disabled:cursor-not-allowed`}
          disabled={selectedIds.length === 0}
          onClick={() => {
            if (selectedIds.length > 0) {
              const query = selectedIds.join(',');
              router.push(`/albaranes/crear-ac21-salida/nuevo/?productos=${query}`);
            }
          }}
        >
          Crear AC21 ({selectedIds.length})
        </button>
      </div>

      {/* Resumen Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="font-semibold">Total Productos</h3>
          <p className="text-2xl">{summary.total}</p>
          <p className="text-sm text-gray-500">Productos únicos por número de serie</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="font-semibold">En Custodia</h3>
          <p className="text-2xl text-green-600">{summary.en_custodia}</p>
          <p className="text-sm text-gray-500">Productos físicamente en Aicox</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="font-semibold">Fuera de Custodia</h3>
          <p className="text-2xl text-red-600">{summary.fuera_custodia}</p>
          <p className="text-sm text-gray-500">Productos entregados o en tránsito</p>
        </div>
      </div>

      {/* Filtros */}
      <div className="mb-6 bg-white p-4 rounded-lg border border-gray-200">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Campo de búsqueda */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                type="text"
                placeholder="Buscar por código, número de serie, descripción..."
                className="pl-10"
                onChange={(e) => debouncedSearch(e.target.value)}
              />
            </div>
          </div>

          {/* Filtro por estado - Botones toggle */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setEstadoFilter('')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                estadoFilter === ''
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Todos
            </button>
            <button
              onClick={() => setEstadoFilter('en_custodia')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center gap-2 ${
                estadoFilter === 'en_custodia'
                  ? 'bg-green-500 text-white shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <div className={`w-2 h-2 rounded-full ${estadoFilter === 'en_custodia' ? 'bg-white' : 'bg-green-400'}`}></div>
              En Custodia
            </button>
            <button
              onClick={() => setEstadoFilter('fuera_custodia')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center gap-2 ${
                estadoFilter === 'fuera_custodia'
                  ? 'bg-red-500 text-white shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <div className={`w-2 h-2 rounded-full ${estadoFilter === 'fuera_custodia' ? 'bg-white' : 'bg-red-400'}`}></div>
              Fuera de Custodia
            </button>
          </div>
        </div>
      </div>

      {/* Tabla de Inventario */}
      <div className="overflow-x-auto">
        <Table className="w-full border border-gray-300">
          <TableHeader>
            <TableRow className="bg-gray-100">
              <TableHead className="px-2 py-2 w-8 text-center">
                <input
                  type="checkbox"
                  checked={filteredData.length > 0 && selectedIds.length === filteredData.length}
                  ref={el => {
                    if (el) el.indeterminate = selectedIds.length > 0 && selectedIds.length < filteredData.length;
                  }}
                  onChange={handleSelectAll}
                  aria-label="Seleccionar todos"
                />
              </TableHead>
              <TableHead className="px-4 py-2">Código</TableHead>
              <TableHead className="px-4 py-2">Nº Serie</TableHead>
              <TableHead className="px-4 py-2">Descripción</TableHead>
              <TableHead className="px-4 py-2">Tipo</TableHead>
              <TableHead className="px-4 py-2">Estado</TableHead>
              <TableHead className="px-4 py-2">Último Movimiento</TableHead>
              <TableHead className="px-4 py-2">Ubicación</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredData.length > 0 ? (
              filteredData.map((item) => (
                <TableRow key={item.id} className="border-t">
                  <TableCell className="px-2 py-2 w-8 text-center">
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(item.id)}
                      onChange={() => handleSelect(item.id)}
                      aria-label={`Seleccionar producto ${item.codigo_producto}`}
                    />
                  </TableCell>
                  <TableCell className="px-4 py-2">{item.codigo_producto}</TableCell>
                  <TableCell className="px-4 py-2 font-mono">{item.numero_serie}</TableCell>
                  <TableCell className="px-4 py-2">{item.descripcion}</TableCell>
                  <TableCell className="px-4 py-2">{item.tipo_nombre}</TableCell>
                  <TableCell className="px-4 py-2">
                    <span className={`px-2 py-1 rounded-full text-sm ${
                      item.estado === 'activo' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {item.estado_display}
                    </span>
                  </TableCell>
                  <TableCell className="px-4 py-2">
                    <div className="text-sm">
                      {item.ultimo_movimiento_info ? (
                        <>
                          <p>Albarán: <Link href={`/albaranes/${item.ultimo_movimiento_info.albaran_id || item.ultimo_movimiento_info.albaran_numero}`} className="text-blue-600 hover:underline">{item.ultimo_movimiento_info.albaran_numero}</Link></p>
                          <p>Tipo: {item.ultimo_movimiento_info.tipo_movimiento_display}</p>
                          <p className="text-gray-500">{new Date(item.ultimo_movimiento_info.fecha).toLocaleString('es-ES')}</p>
                        </>
                      ) : (
                        <p className="text-gray-500">Sin movimientos registrados</p>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="px-4 py-2">{item.ubicacion || '-'}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={8} className="text-center text-gray-500 py-4">
                  No se encontraron productos en el inventario.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
} 