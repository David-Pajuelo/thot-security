"use client";

import { useEffect, useState } from "react";
import { fetchDocumentosPrincipales, deleteAlbaran } from "@/lib/api";
import { Albaran } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Link from "next/link";
import { Trash2, Eye, Send, Printer, Search, FileText, Files, Edit } from "lucide-react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";

interface AlbaranesTableProps {
  filterType?: 'ENTRADA' | 'SALIDA' | 'ALL';
}

export default function AlbaranesTable({ filterType = 'ALL' }: AlbaranesTableProps) {
  const [albaranes, setAlbaranes] = useState<Albaran[]>([]);
  const [filteredAlbaranes, setFilteredAlbaranes] = useState<Albaran[]>([]);
  const [isDeleting, setIsDeleting] = useState<number | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [albaranToDelete, setAlbaranToDelete] = useState<number | null>(null);
  
  // Estados para filtros con persistencia
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<'ALL' | 'ALBARAN' | 'AC21'>('ALL');
  const [filtersLoaded, setFiltersLoaded] = useState(false);

  // Cargar filtros desde localStorage cuando cambie filterType
  useEffect(() => {
    const storageKey = `albaranes_filter_${filterType}`;
    const savedFilters = localStorage.getItem(storageKey);
    
    if (savedFilters) {
      try {
        const { searchTerm: savedSearchTerm, typeFilter: savedTypeFilter } = JSON.parse(savedFilters);
        if (savedSearchTerm !== undefined) setSearchTerm(savedSearchTerm);
        if (savedTypeFilter !== undefined) setTypeFilter(savedTypeFilter);
      } catch (error) {
        console.log('Error loading saved filters:', error);
      }
    } else {
      // Si no hay filtros guardados, resetear a valores por defecto
      setSearchTerm('');
      setTypeFilter('ALL');
    }
    
    // Marcar que los filtros ya se cargaron
    setFiltersLoaded(true);
  }, [filterType]);

  // Guardar filtros en localStorage cuando cambien - Solo después de cargar
  useEffect(() => {
    if (!filtersLoaded) return; // No guardar hasta que se hayan cargado los filtros
    
    const storageKey = `albaranes_filter_${filterType}`;
    const filtersToSave = {
      searchTerm,
      typeFilter
    };
    localStorage.setItem(storageKey, JSON.stringify(filtersToSave));
  }, [searchTerm, typeFilter, filterType, filtersLoaded]);

  useEffect(() => {
    loadAlbaranes();
  }, []);

  useEffect(() => {
    // Filtrar albaranes cuando cambian los datos, el filtro, la búsqueda o el tipo
    let filtered = albaranes;

    // 1. Filtrar por tipo de página (ENTRADA/SALIDA/ALL)
    if (filterType === 'ENTRADA') {
      // Para ENTRADA: mostrar TODOS los albaranes de entrada (albaranes normales + AC21s de entrada)
      filtered = filtered.filter(alb => {
        // AC21s de entrada
        if (alb.empresa_origen && alb.empresa_destino && alb.direccion_transferencia === 'ENTRADA') {
          return true;
        }
        // Albaranes normales (que no son AC21s pero son entradas)
        if (!alb.empresa_origen && !alb.empresa_destino) {
          return true;
        }
        return false;
      });
    } else if (filterType === 'SALIDA') {
      // Para SALIDA: solo AC21s de salida
      filtered = filtered.filter(alb => {
        const isAC21 = alb.empresa_origen && alb.empresa_destino;
        return isAC21 && alb.direccion_transferencia === 'SALIDA';
      });
    }

    // 2. Filtrar por tipo de documento (AC21 vs Albarán normal) - Solo aplicar si NO es página de salida
    if (filterType !== 'SALIDA') {
      if (typeFilter === 'AC21') {
        filtered = filtered.filter(alb => alb.empresa_origen && alb.empresa_destino);
      } else if (typeFilter === 'ALBARAN') {
        filtered = filtered.filter(alb => !alb.empresa_origen && !alb.empresa_destino);
      }
    }

    // 3. Filtrar por término de búsqueda (número de albarán)
    if (searchTerm.trim()) {
      filtered = filtered.filter(alb => 
        alb.numero.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredAlbaranes(filtered);
  }, [albaranes, filterType, typeFilter, searchTerm]);

  const loadAlbaranes = async () => {
    try {
      const data = await fetchDocumentosPrincipales();
      setAlbaranes(data);
    } catch (error) {
      console.error("Error fetching albaranes:", error);
      toast.error("Error al cargar los albaranes");
    }
  };

  const handleDeleteClick = (id: number) => {
    setAlbaranToDelete(id);
    setShowConfirmDialog(true);
  };

  const handleDeleteConfirm = async () => {
    if (!albaranToDelete) return;

    setIsDeleting(albaranToDelete);
    try {
      await deleteAlbaran(albaranToDelete);
      toast.success("Albarán eliminado correctamente");
      loadAlbaranes(); // Recargar la tabla
    } catch (error) {
      console.error("Error deleting albaran:", error);
      toast.error("Error al eliminar el albarán");
    } finally {
      setIsDeleting(null);
      setShowConfirmDialog(false);
      setAlbaranToDelete(null);
    }
  };

  const handlePrintAC21 = async (albaranId: number) => {
    try {
      // Obtener el token de autenticación
      const token = localStorage.getItem('accessToken');
      if (!token) {
        toast.error('No hay sesión activa');
        return;
      }

      // Hacer la petición con autenticación
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/albaranes/${albaranId}/generar-ac21-html/`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        // Obtener el HTML como texto
        const htmlContent = await response.text();
        
        // Crear una nueva ventana y escribir el HTML
        const printWindow = window.open('', '_blank');
        if (printWindow) {
          printWindow.document.write(htmlContent);
          printWindow.document.close();
          
          // Enfocar la ventana
          printWindow.focus();
          

        }
      } else if (response.status === 401) {
        toast.error('Sesión expirada. Inicia sesión nuevamente.');
      } else {
        toast.error('Error al generar el documento AC21');
      }
    } catch (error) {
      console.error('Error al generar AC21:', error);
      toast.error('Error al conectar con el servidor');
    }
  };

  return (
    <>
      {/* Filtros */}
      <div className="mb-6 bg-white p-4 rounded-lg border border-gray-200">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Campo de búsqueda */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                type="text"
                placeholder="Buscar por número de albarán..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Filtro por tipo - Botones toggle - Solo mostrar si NO es página de salida */}
          {filterType !== 'SALIDA' && (
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setTypeFilter('ALL')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                  typeFilter === 'ALL'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Todos
              </button>
              <button
                onClick={() => setTypeFilter('ALBARAN')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center gap-2 ${
                  typeFilter === 'ALBARAN'
                    ? 'bg-blue-500 text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <div className={`w-2 h-2 rounded-full ${typeFilter === 'ALBARAN' ? 'bg-white' : 'bg-blue-400'}`}></div>
                Albaranes
              </button>
              <button
                onClick={() => setTypeFilter('AC21')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center gap-2 ${
                  typeFilter === 'AC21'
                    ? 'bg-purple-500 text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <div className={`w-2 h-2 rounded-full ${typeFilter === 'AC21' ? 'bg-white' : 'bg-purple-400'}`}></div>
                AC21
              </button>
            </div>
          )}
        </div>


      </div>

      {filteredAlbaranes.length > 0 && (
        <div className="overflow-x-auto">
        <table className="w-full border-collapse border border-gray-300">
          <thead>
            <tr className="bg-gray-100">
              <th className="border p-3 text-center font-bold text-base">Número</th>
              <th className="border p-3 text-center font-bold text-base">Fecha</th>
              <th className="border p-3 text-center font-bold text-base">Tipo</th>
              <th className="border p-3 text-center font-bold text-base">Páginas</th>
              <th className="border p-3 text-center font-bold text-base">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {filteredAlbaranes.map((alb) => (
              <tr key={alb.id} className="border-b hover:bg-gray-50">
                <td className="border p-3">{alb.numero}</td>
                <td className="border p-3 text-center">{new Date(alb.fecha).toLocaleString('es-ES')}</td>
                <td className="border p-3 text-center">
                  {alb.empresa_origen && alb.empresa_destino ? (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                      AC21 {alb.direccion_transferencia === 'ENTRADA' ? 'Entrada' : 'Salida'}
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Albarán Entrada
                    </span>
                  )}
                </td>
                <td className="border p-3 text-center">
                  <div className="flex items-center justify-center gap-1">
                    {alb.total_paginas > 1 ? (
                      <>
                        <Files className="h-4 w-4 text-amber-600" />
                        <span className="text-sm font-medium text-amber-700">
                          {alb.total_paginas}
                        </span>
                      </>
                    ) : (
                      <>
                        <FileText className="h-4 w-4 text-gray-500" />
                        <span className="text-sm text-gray-500">1</span>
                      </>
                    )}
                  </div>
                </td>
                <td className="border p-3 text-right">
                  <div className="flex justify-end gap-px max-w-lg ml-auto">
                    {(alb.empresa_origen && alb.empresa_destino && alb.direccion_transferencia === 'ENTRADA') && (
                      <Link href={`/albaranes/crear-ac21-salida/nuevo?from=${alb.id}`}>
                        <Button 
                          variant="outline"
                          className="bg-green-500 hover:bg-green-600 text-white h-8 px-2 text-xs whitespace-nowrap"
                        >
                          <Send className="h-3 w-3" />
                          <span className="ml-1">Dar Salida</span>
                        </Button>
                      </Link>
                    )}
                    {(alb.empresa_origen && alb.empresa_destino && alb.direccion_transferencia === 'SALIDA') && (
                      <>
                        <Button 
                          variant="outline"
                          className="bg-purple-500 hover:bg-purple-600 text-white h-8 px-2 text-xs whitespace-nowrap"
                          onClick={() => handlePrintAC21(alb.id)}
                        >
                          <Printer className="h-3 w-3" />
                          <span className="ml-1">Imprimir</span>
                        </Button>
                        <Link href={`/albaranes/${alb.id}?edit=true`}>
                          <Button 
                            variant="outline"
                            className="bg-orange-500 hover:bg-orange-600 text-white h-8 px-2 text-xs whitespace-nowrap"
                          >
                            <Edit className="h-3 w-3" />
                            <span className="ml-1">Editar</span>
                          </Button>
                        </Link>
                      </>
                    )}
                    {(alb.empresa_origen && alb.empresa_destino && alb.direccion_transferencia === 'ENTRADA') && (
                      <Link href={`/albaranes/${alb.id}?edit=true`}>
                        <Button 
                          variant="outline"
                          className="bg-orange-500 hover:bg-orange-600 text-white h-8 px-2 text-xs whitespace-nowrap"
                        >
                          <Edit className="h-3 w-3" />
                          <span className="ml-1">Editar</span>
                        </Button>
                      </Link>
                    )}
                    <Link href={`/albaranes/${alb.id}`}>
                      <Button 
                        variant="outline"
                        className="bg-blue-500 hover:bg-blue-600 text-white h-8 px-2 text-xs whitespace-nowrap"
                      >
                        <Eye className="h-3 w-3" />
                        <span className="ml-1">Ver</span>
                      </Button>
                    </Link>
                    <Button
                      variant="outline"
                      className="bg-red-500 hover:bg-red-600 text-white h-8 px-2 text-xs whitespace-nowrap"
                      onClick={() => handleDeleteClick(alb.id)}
                      disabled={isDeleting === alb.id}
                    >
                      {isDeleting === alb.id ? (
                        <div className="animate-spin rounded-full h-3 w-3 border-2 border-white" />
                      ) : (
                        <>
                          <Trash2 className="h-3 w-3" />
                          <span className="ml-1">Eliminar</span>
                        </>
                      )}
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      )}

      <ConfirmDialog
        isOpen={showConfirmDialog}
        onClose={() => {
          setShowConfirmDialog(false);
          setAlbaranToDelete(null);
        }}
        onConfirm={handleDeleteConfirm}
        title="Confirmar Eliminación"
        description={`¿Está seguro de que desea eliminar el albarán ${filteredAlbaranes.find(a => a.id === albaranToDelete)?.numero || ''}?`}
      />
    </>
  );
} 