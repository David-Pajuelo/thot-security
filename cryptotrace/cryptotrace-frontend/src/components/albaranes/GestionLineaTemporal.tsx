"use client";

import { useEffect, useState } from "react";
import { fetchTiposProducto, procesarAlbaranDirecto } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import LineaTemporalTable from "./LineaTemporalTable";
import { toast } from "sonner";
import DocumentoExistenteModal from "./DocumentoExistenteModal";

interface TipoProducto {
  id: number;
  nombre: string;
}

interface CodigoTipificado {
  codigo_producto: string;
  descripcion: string;
  tipo_producto_id: number | null;
  tipo_producto_nombre: string | null;
  tipo_catalogo_id?: number | null; // Para carga automática desde catálogo
  tipo_catalogo_nombre?: string | null;
}

interface GestionLineaTemporalProps {
  onClose?: () => void;
  ac21Data?: {
    cabecera: any;
    empresa_origen: any;
    empresa_destino: any;
    articulos: any[];
    accesorios: any[];
    equipos_prueba: any[];
    firmas: any;
    observaciones: string;
    imagen?: File;
  };
}

export default function GestionLineaTemporal({ onClose, ac21Data }: GestionLineaTemporalProps = {}) {
  const [codigosTipificados, setCodigosTipificados] = useState<CodigoTipificado[]>([]);
  const [tipos, setTipos] = useState<TipoProducto[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [documentoExistente, setDocumentoExistente] = useState<any>(null);
  const [showDocumentoExistenteModal, setShowDocumentoExistenteModal] = useState(false);
  const router = useRouter();

  // Cargar tipos disponibles desde API
  const cargarTipos = async () => {
    try {
      const response = await fetchTiposProducto();
      setTipos(response);
    } catch (error) {
      console.error("❌ Error cargando tipos:", error);
      setError("Error cargando los tipos de producto");
    }
  };

  // Extraer códigos únicos de los artículos y cargar tipos desde catálogo
  const extraerCodigosUnicos = async (articulos: any[], tiposDisponibles: TipoProducto[]) => {
    const codigosUnicos = new Map<string, CodigoTipificado>();
    
    // Primero extraer códigos únicos
    for (const art of articulos) {
      const codigo = art.codigo_producto || art.titulo_corto || '';
      if (!codigo || codigosUnicos.has(codigo)) continue;
      
      const descripcion = art.observaciones || art.descripcion || '';
      
      codigosUnicos.set(codigo, {
        codigo_producto: codigo,
        descripcion: descripcion,
        tipo_producto_id: null,
        tipo_producto_nombre: null,
        tipo_catalogo_id: null,
        tipo_catalogo_nombre: null
      });
    }
    
    // Luego cargar tipos desde catálogo para cada código (consultar uno por uno)
    const codigosArray = Array.from(codigosUnicos.keys());
    if (codigosArray.length > 0) {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api';
        const token = localStorage.getItem('accessToken');
        
        // Consultar cada código individualmente (Django REST Framework no soporta __in con lista separada por comas)
        console.log(`[GestionLineaTemporal] Consultando catálogo para ${codigosArray.length} códigos...`);
        for (const codigo of codigosArray) {
          try {
            const url = `${API_URL}/productos/?codigo_producto=${encodeURIComponent(codigo)}`;
            console.log(`[GestionLineaTemporal] Consultando: ${url}`);
            
            const catalogoResponse = await fetch(url, {
              headers: {
                'Authorization': `Bearer ${token}`
              }
            });
            
            if (catalogoResponse.ok) {
              const catalogoData = await catalogoResponse.json();
              const productosCatalogo = Array.isArray(catalogoData) ? catalogoData : (catalogoData.results || []);
              console.log(`[GestionLineaTemporal] Respuesta para ${codigo}:`, productosCatalogo);
              
              // Mapear tipos desde catálogo
              if (productosCatalogo.length > 0) {
                const prod = productosCatalogo[0]; // Tomar el primero
                console.log(`[GestionLineaTemporal] Producto encontrado para ${codigo}:`, prod, `tipo=${prod.tipo}, tipo_nombre=${prod.tipo_nombre}`);
                if (prod.codigo_producto && codigosUnicos.has(prod.codigo_producto)) {
                  const codigoObj = codigosUnicos.get(prod.codigo_producto)!;
                  // El campo 'tipo' es el ID del TipoProducto (ForeignKey)
                  const tipoId = prod.tipo;
                  if (tipoId) {
                    codigoObj.tipo_catalogo_id = tipoId;
                    // Buscar nombre del tipo
                    const tipoObj = tiposDisponibles.find(t => t.id === tipoId);
                    if (tipoObj) {
                      codigoObj.tipo_catalogo_nombre = tipoObj.nombre;
                      codigoObj.tipo_producto_id = tipoId; // Auto-asignar si existe en catálogo
                      codigoObj.tipo_producto_nombre = tipoObj.nombre;
                      console.log(`✅ [GestionLineaTemporal] Tipo cargado automáticamente para ${codigo}: ${tipoObj.nombre} (ID=${tipoId})`);
                    } else {
                      console.warn(`⚠️ [GestionLineaTemporal] Tipo ID ${tipoId} no encontrado en tiposDisponibles para código ${codigo}. Tipos disponibles:`, tiposDisponibles.map(t => `${t.id}:${t.nombre}`));
                    }
                  } else {
                    console.log(`ℹ️ [GestionLineaTemporal] Producto ${codigo} no tiene tipo asignado en catálogo (tipo=${tipoId})`);
                  }
                }
              } else {
                console.log(`ℹ️ [GestionLineaTemporal] Producto ${codigo} no encontrado en catálogo`);
              }
            } else if (catalogoResponse.status === 404) {
              // 404 es normal cuando el producto no existe en el catálogo (aún no se ha procesado)
              console.log(`ℹ️ [GestionLineaTemporal] Producto ${codigo} no encontrado en catálogo (404 - normal para productos nuevos)`);
            } else {
              // Otros errores (500, 401, etc.) sí son problemáticos
              console.error(`❌ [GestionLineaTemporal] Error en respuesta para ${codigo}: ${catalogoResponse.status}`);
            }
          } catch (error) {
            console.error(`❌ [GestionLineaTemporal] Error cargando tipo para código ${codigo}:`, error);
            // Continuar con el siguiente código
          }
        }
      } catch (error) {
        console.error('[GestionLineaTemporal] Error cargando tipos desde catálogo:', error);
        // Continuar sin fallar si hay error
      }
    }
    
    return Array.from(codigosUnicos.values());
  };

  useEffect(() => {
    const inicializar = async () => {
      const tiposCargados = await fetchTiposProducto();
      setTipos(tiposCargados);
      
      if (ac21Data && ac21Data.articulos) {
        // Extraer códigos únicos de los artículos y cargar tipos desde catálogo
        const codigos = await extraerCodigosUnicos(ac21Data.articulos, tiposCargados);
        setCodigosTipificados(codigos);
        console.log("[GestionLineaTemporal] Códigos únicos extraídos con tipos:", codigos);
      } else {
        // Si no hay datos desde props, mantener comportamiento antiguo (cargar desde BD)
        // Esto es para compatibilidad con otros flujos
        setError("No hay datos del AC21 para procesar");
      }
    };
    
    inicializar();
  }, [ac21Data]);

  const handleGuardarTipo = async (codigoProducto: string, tipoProductoId: number | null) => {
    // Actualizar estado en memoria primero
    const tipoSeleccionado = tipos.find(t => t.id === tipoProductoId);
    setCodigosTipificados((prev) =>
      prev.map((codigo) =>
        codigo.codigo_producto === codigoProducto
          ? {
              ...codigo,
              tipo_producto_id: tipoProductoId,
              tipo_producto_nombre: tipoSeleccionado?.nombre || null
            }
          : codigo
      )
    );
    
    // Actualizar inmediatamente en la base de datos (catálogo)
    try {
      if (tipoProductoId) {
        // Llamar a la API para actualizar el catálogo
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api'}/lineas-temporales/actualizar-cc/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
          },
          body: JSON.stringify({
            codigo_producto: codigoProducto,
            tipo_producto_id: tipoProductoId
          })
        });
        
        if (response.ok) {
          console.log(`✅ [GestionLineaTemporal] Tipo actualizado en catálogo: ${codigoProducto} → ${tipoSeleccionado?.nombre || 'NINGUNO'}`);
        } else {
          const errorData = await response.json().catch(() => ({}));
          console.error(`❌ [GestionLineaTemporal] Error actualizando tipo en catálogo:`, errorData);
        }
      } else {
        console.log(`ℹ️ [GestionLineaTemporal] Tipo NINGUNO seleccionado para ${codigoProducto} (no se actualiza catálogo)`);
      }
    } catch (error) {
      console.error(`❌ [GestionLineaTemporal] Error actualizando tipo en catálogo:`, error);
      // No mostrar error al usuario, solo log
    }
    
    console.log(`[GestionLineaTemporal] Tipo asignado: ${codigoProducto} → ${tipoSeleccionado?.nombre || 'NINGUNO'}`);
  };

  const handleProcesarAlbaran = async () => {
    if (!ac21Data) {
      setMensaje('❌ No hay datos del AC21 para procesar.');
      setTimeout(() => setMensaje(null), 3000);
      return;
    }

    // Verificar que hay códigos para procesar
    if (codigosTipificados.length === 0) {
      setMensaje('❌ No hay códigos para procesar.');
      setTimeout(() => setMensaje(null), 3000);
      return;
    }

    try {
      setLoading(true);
      setMensaje(null);

      // 1. Crear mapa de código → tipo_producto_id desde la tipificación
      const codigoATipo = new Map(
        codigosTipificados
          .filter((c) => c.tipo_producto_id !== null)
          .map((c) => [c.codigo_producto, c.tipo_producto_id!])
      );

      // 2. Construir payload completo con todos los artículos
      const payload = {
        cabecera: ac21Data.cabecera,
        empresa_origen: ac21Data.empresa_origen,
        empresa_destino: ac21Data.empresa_destino,
        articulos: ac21Data.articulos.map((art) => {
          const codigo = art.codigo_producto || art.titulo_corto || '';
          const numeroSerie = art.numero_serie_inicio || art.numero_serie_fin || art.numero_serie || '';
          
          return {
            codigo_producto: codigo,
            numero_serie: numeroSerie,
            cantidad: art.cantidad || 1,
            descripcion: art.observaciones || art.descripcion || '',
            tipo_producto_id: codigoATipo.get(codigo) || null, // Tipo asignado en modal
            observaciones: art.observaciones || '',
            cc: (art.cc && art.cc.toString().trim() !== '') ? art.cc : '' // CC del OCR - NO usar valor por defecto si está vacío
          };
        }),
        accesorios: ac21Data.accesorios || [],
        equipos_prueba: ac21Data.equipos_prueba || [],
        firmas: ac21Data.firmas || {},
        observaciones: ac21Data.observaciones || ''
      };

      console.log('🔄 [FRONTEND] Enviando payload a procesar_directo:', payload);

      // 3. Llamar a procesar_directo
      const result = await procesarAlbaranDirecto(payload, ac21Data.imagen);
      console.log('✅ [FRONTEND] Respuesta del backend:', result);

      // 4. Si existe documento, mostrar modal de decisión
      if (result.documento_existente && result.requiere_decision) {
        console.log('[GestionLineaTemporal] Documento existente detectado, mostrando modal de decisión');
        setDocumentoExistente(result.documento_existente);
        setShowDocumentoExistenteModal(true);
        setLoading(false);
        return;
      }

      // 5. Si no existe, mostrar éxito y cerrar
      toast.success(`AC21 procesado correctamente (ID: ${result.albaran_id}, Número: ${result.albaran_numero || 'N/A'})`);
      
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
      toast.error(`Error al procesar el AC21: ${errorMessage}`);
      setMensaje(`❌ Error: ${errorMessage}`);
      setTimeout(() => setMensaje(null), 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentoExistenteDecision = async (crearPaginaAdicional: boolean) => {
    if (!ac21Data || !documentoExistente) return;

    try {
      setLoading(true);
      setShowDocumentoExistenteModal(false);

      // Crear mapa de código → tipo_producto_id
      const codigoATipo = new Map(
        codigosTipificados
          .filter((c) => c.tipo_producto_id !== null)
          .map((c) => [c.codigo_producto, c.tipo_producto_id!])
      );

      // Construir payload con decisión
      const payload = {
        cabecera: ac21Data.cabecera,
        empresa_origen: ac21Data.empresa_origen,
        empresa_destino: ac21Data.empresa_destino,
        articulos: ac21Data.articulos.map((art) => {
          const codigo = art.codigo_producto || art.titulo_corto || '';
          const numeroSerie = art.numero_serie_inicio || art.numero_serie_fin || art.numero_serie || '';
          
          return {
            codigo_producto: codigo,
            numero_serie: numeroSerie,
            cantidad: art.cantidad || 1,
            descripcion: art.observaciones || art.descripcion || '',
            tipo_producto_id: codigoATipo.get(codigo) || null,
            observaciones: art.observaciones || '',
            cc: art.cc || 1
          };
        }),
        accesorios: ac21Data.accesorios || [],
        equipos_prueba: ac21Data.equipos_prueba || [],
        firmas: ac21Data.firmas || {},
        observaciones: ac21Data.observaciones || '',
        crear_pagina_adicional: crearPaginaAdicional,
        documento_existente_id: documentoExistente.id
      };

      const result = await procesarAlbaranDirecto(payload, ac21Data.imagen);
      
      toast.success(`AC21 procesado correctamente (ID: ${result.albaran_id}, Número: ${result.albaran_numero || 'N/A'})`);
      
      setTimeout(() => {
        if (onClose) {
          onClose();
        } else {
          router.push('/albaranes/upload-ac21');
        }
      }, 1000);
    } catch (error: any) {
      console.error('❌ Error procesando con decisión:', error);
      toast.error(`Error al procesar el AC21: ${error?.message || 'Error desconocido'}`);
    } finally {
      setLoading(false);
    }
  };

  // Convertir codigosTipificados a formato Producto para la tabla
  const productosParaTabla = codigosTipificados.map((codigo) => ({
    codigo_producto: codigo.codigo_producto,
    cantidad: 0, // No se muestra cantidad, pero la tabla lo requiere
    tipo_producto_id: codigo.tipo_producto_id,
    tipo_producto_nombre: codigo.tipo_producto_nombre,
    tipo_catalogo_id: codigo.tipo_catalogo_id,
    tipo_catalogo_nombre: codigo.tipo_catalogo_nombre
  }));

  return (
    <div className="relative">
      {mensaje && (
        <div className="absolute top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-md shadow-md transition-opacity duration-500 z-50">
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

      {loading && <p>Cargando...</p>}
      {error && <p className="text-red-500">{error}</p>}
      
      {!loading && !error && ac21Data && (
        <>
          <p className="mb-4 text-sm text-gray-600">
            Asigna un Tipo de Cryptocustodio (CC) a cada código único del AC21. 
            Esta asignación se guardará en el catálogo de productos.
          </p>
          
          <LineaTemporalTable 
            productos={productosParaTabla}
            tipos={tipos}
            tipoAlbaran="inventario"
            onGuardarTipo={handleGuardarTipo}
            onTipoAlbaranChange={() => {}} // No se usa en el nuevo flujo
          />

          <div className="mt-6 flex justify-center">
            <Button
              onClick={handleProcesarAlbaran}
              disabled={codigosTipificados.length === 0}
              className={`px-6 py-3 font-semibold rounded-lg transition 
                ${codigosTipificados.length > 0 
                  ? 'bg-green-500 text-white hover:bg-green-600' 
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'}
              `}
            >
              🚀 Procesar AC21
            </Button>
          </div>

          {codigosTipificados.length === 0 && (
            <p className="text-red-500 text-center mt-2">
              ⚠️ No hay códigos para procesar.
            </p>
          )}
        </>
      )}

      {/* Modal de documento existente */}
      {showDocumentoExistenteModal && documentoExistente && (
        <DocumentoExistenteModal
          isOpen={showDocumentoExistenteModal}
          onClose={() => setShowDocumentoExistenteModal(false)}
          documentoExistente={documentoExistente}
          numeroRegistro={ac21Data?.cabecera?.numero_registro_salida || ac21Data?.cabecera?.numero_registro_entrada || ''}
          onCrearNuevaPagina={() => handleDocumentoExistenteDecision(true)}
          onCrearDocumentoIndependiente={() => handleDocumentoExistenteDecision(false)}
        />
      )}
    </div>
  );
} 