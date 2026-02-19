"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ArrowLeft, FileText, Printer, ArrowUpRight, ChevronLeft, ChevronRight, Files, Edit, Save, X, Image, Download } from "lucide-react";
import { Albaran, Empresa } from "@/lib/types";
import AlbaranMovimientos from "./AlbaranMovimientos";
import { toast } from "sonner";
import { obtenerPaginasDocumento, fetchEmpresas, fetchCryptocustodios } from "@/lib/api";

// Modal para mostrar la imagen del documento con autenticación
interface ModalImagenDocumentoProps {
  albaranId: number;
  numero: string;
  isOpen: boolean;
  onClose: () => void;
}

function ModalImagenDocumento({ albaranId, numero, isOpen, onClose }: ModalImagenDocumentoProps) {
  const [imagenSrc, setImagenSrc] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    const cargarImagen = async () => {
      try {
        setCargando(true);
        setError(null);
        
        const token = localStorage.getItem('accessToken');
        if (!token) {
          throw new Error('No hay token de autenticación');
        }

        const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api';
        const response = await fetch(`${apiBase}/albaranes/${albaranId}/imagen-documento/`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          let msg = `Error del servidor: ${response.status}`;
          try {
            const data = await response.json();
            if (data?.detail) msg = typeof data.detail === 'string' ? data.detail : String(data.detail);
          } catch (_) {}
          if (response.status === 401) msg = 'No autorizado - inicia sesión nuevamente';
          else if (response.status === 404) msg = msg || 'Imagen no encontrada';
          throw new Error(msg);
        }

        const blob = await response.blob();
        if (!blob.size || !(blob.type.startsWith('image/'))) {
          throw new Error(blob.size ? 'La respuesta no es una imagen válida.' : 'El documento no tiene imagen asociada.');
        }
        const imageUrl = URL.createObjectURL(blob);
        setImagenSrc(imageUrl);
      } catch (err: any) {
        console.error('Error cargando imagen:', err);
        setError(err.message || 'Error al cargar la imagen');
      } finally {
        setCargando(false);
      }
    };

    cargarImagen();

    // Cleanup: revocar la URL del blob cuando se cierre el modal
    return () => {
      if (imagenSrc) {
        URL.revokeObjectURL(imagenSrc);
      }
    };
  }, [albaranId, isOpen]);

  const handleDescargar = () => {
    if (imagenSrc) {
      const link = document.createElement('a');
      link.href = imagenSrc;
      link.download = `AC21_${numero}_documento_original.jpg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast.success('Imagen descargada');
    }
  };

  const handleImprimir = () => {
    if (imagenSrc) {
      const printWindow = window.open('', '_blank');
      if (printWindow) {
        printWindow.document.write(`
          <html>
            <head>
              <title>AC21 ${numero} - Documento Original</title>
              <style>
                body { margin: 0; padding: 20px; text-align: center; }
                img { max-width: 100%; height: auto; }
                h3 { margin-bottom: 20px; }
              </style>
            </head>
            <body>
              <h3>AC21 ${numero} - Documento Original</h3>
              <img src="${imagenSrc}" alt="Documento AC21 ${numero}" />
            </body>
          </html>
        `);
        printWindow.document.close();
        printWindow.focus();
        printWindow.print();
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl max-w-4xl max-h-[90vh] w-full mx-4 flex flex-col" onClick={(e) => e.stopPropagation()}>
        {/* Header del modal */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-500" />
            AC21 {numero} - Documento Original
          </h3>
          <div className="flex items-center gap-2">
            {imagenSrc && !cargando && !error && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDescargar}
                  className="flex items-center gap-1"
                >
                  <Download className="w-4 h-4" />
                  Descargar
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleImprimir}
                  className="flex items-center gap-1"
                >
                  <Printer className="w-4 h-4" />
                  Imprimir
                </Button>
              </>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
              className="flex items-center gap-1"
            >
              <X className="w-4 h-4" />
              Cerrar
            </Button>
          </div>
        </div>

        {/* Contenido del modal */}
        <div className="flex-1 overflow-auto p-4">
          {cargando && (
            <div className="text-center text-gray-500 py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
              <p>Cargando imagen...</p>
            </div>
          )}
          
          {error && (
            <div className="text-center text-red-500 py-8">
              <p>Error al cargar la imagen del documento</p>
              <p className="text-sm text-gray-600 mt-1">{error}</p>
            </div>
          )}
          
          {imagenSrc && !cargando && !error && (
            <div className="text-center">
              <img
                src={imagenSrc}
                alt={`Imagen del documento AC21 - ${numero}`}
                className="max-w-full h-auto border border-gray-300 rounded-lg shadow-sm mx-auto"
                style={{ maxHeight: 'calc(90vh - 200px)' }}
                onError={() => {
                  setError('Error al mostrar la imagen');
                }}
              />
            </div>
          )}
        </div>

        {/* Footer del modal */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <p className="text-sm text-gray-600 text-center">
            <strong>Nota:</strong> Esta imagen corresponde al documento AC21 original procesado por OCR.
          </p>
        </div>
      </div>
    </div>
  );
}

// Función para formatear la fecha
const formatearFecha = (fecha: string) => {
  if (!fecha) return '';
  const date = new Date(fecha);
  return date.toISOString().split('T')[0]; // Formato YYYY-MM-DD
};

// Función utilitaria para mostrar un guion o línea si el valor es null o vacío
const displayOrLine = (value: string | null | undefined) => {
  return value && value.trim() !== '' ? value : '____________________';
};

interface AC21DetailProps {
  albaran: Albaran;
  onBack: () => void;
}

export default function AC21Detail({ albaran, onBack }: AC21DetailProps) {
  const router = useRouter();
  // Estado local del albarán principal (se actualiza después de guardar)
  const [albaranLocal, setAlbaranLocal] = useState<Albaran>(albaran);
  const [movimientos, setMovimientos] = useState<any[]>([]);
  const [paginas, setPaginas] = useState<Albaran[]>([]);
  const [paginaActual, setPaginaActual] = useState(0);
  const [cargandoPaginas, setCargandoPaginas] = useState(false);
  
  // Estados para modo edición
  const [modoEdicion, setModoEdicion] = useState(false);
  const [datosEditables, setDatosEditables] = useState<any>({});
  const [guardando, setGuardando] = useState(false);
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [cryptocustodiosDestino, setCryptocustodiosDestino] = useState<any[]>([]);
  const [selectedCryptocustodioIdFirmaA, setSelectedCryptocustodioIdFirmaA] = useState<string>('');
  const [selectedCryptocustodioIdFirmaB, setSelectedCryptocustodioIdFirmaB] = useState<string>('');
  
  // Estado para el modal de imagen
  const [modalImagenAbierto, setModalImagenAbierto] = useState(false);

  // Obtener albarán actual (puede ser la página principal o una página específica)
  const albaranActual = (paginas.length > 0 && paginas[paginaActual]) ? paginas[paginaActual] : albaranLocal;
  
  // Actualizar albaranLocal cuando cambie el prop albaran
  useEffect(() => {
    setAlbaranLocal(albaran);
  }, [albaran]);

  // Función para recargar todos los datos del albarán desde el servidor
  const recargarDatos = async (albaranGuardadoId?: number) => {
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        console.error('No hay token de autenticación');
        return;
      }

      // Determinar qué albarán recargar (el guardado o el principal)
      const idAlbaranARecargar = albaranGuardadoId || albaranLocal.id;

      // 1. Recargar el albarán principal
      const albaranResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/albaranes/${albaranLocal.id}/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (albaranResponse.ok) {
        const albaranData = await albaranResponse.json();
        setAlbaranLocal(albaranData);
        console.log('✅ Albarán recargado:', albaranData);
      }

      // 2. Recargar movimientos del albarán que se guardó (o el principal si no se especifica)
      const movimientosResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/albaranes/${idAlbaranARecargar}/movimientos/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (movimientosResponse.ok) {
        const movimientosData = await movimientosResponse.json();
        setMovimientos(movimientosData);
        console.log('✅ Movimientos recargados:', movimientosData.length);
      }

      // 3. Recargar páginas si es multipágina
      if (albaranLocal.total_paginas && albaranLocal.total_paginas > 1) {
        try {
          const paginasDocumento = await obtenerPaginasDocumento(albaranLocal.id);
          setPaginas(paginasDocumento);
          console.log('✅ Páginas recargadas:', paginasDocumento.length);
        } catch (error) {
          console.error('Error recargando páginas:', error);
        }
      }
    } catch (error) {
      console.error('❌ Error recargando datos:', error);
    }
  };

  // Cargar páginas del documento si es multipágina
  useEffect(() => {
    const cargarPaginas = async () => {
      if (albaranLocal.total_paginas && albaranLocal.total_paginas > 1) {
        setCargandoPaginas(true);
        try {
          const paginasDocumento = await obtenerPaginasDocumento(albaranLocal.id);
          setPaginas(paginasDocumento);
        } catch (error) {
          console.error('Error cargando páginas:', error);
          toast.error('Error al cargar las páginas del documento');
        } finally {
          setCargandoPaginas(false);
        }
      }
    };

    cargarPaginas();
  }, [albaranLocal.id, albaranLocal.total_paginas]);

  // Cargar empresas disponibles
  useEffect(() => {
    const cargarEmpresas = async () => {
      try {
        const empresasData = await fetchEmpresas();
        setEmpresas(empresasData);
      } catch (error) {
        console.error('Error cargando empresas:', error);
      }
    };

    cargarEmpresas();
  }, []);

  // Cargar cryptocustodios de la empresa destino (para rellenar firmas en edición)
  const empresaDestinoIdRaw = modoEdicion
    ? (datosEditables.empresa_destino_id ?? albaranActual.empresa_destino)
    : albaranActual.empresa_destino;
  const empresaDestinoIdNum = typeof empresaDestinoIdRaw === 'object' && empresaDestinoIdRaw !== null
    ? (empresaDestinoIdRaw as any)?.id
    : empresaDestinoIdRaw;
  useEffect(() => {
    if (!empresaDestinoIdNum) {
      setCryptocustodiosDestino([]);
      setSelectedCryptocustodioIdFirmaA('');
      setSelectedCryptocustodioIdFirmaB('');
      return;
    }
    setSelectedCryptocustodioIdFirmaA('');
    setSelectedCryptocustodioIdFirmaB('');
    fetchCryptocustodios(Number(empresaDestinoIdNum))
      .then((data) => setCryptocustodiosDestino(Array.isArray(data) ? data : []))
      .catch(() => setCryptocustodiosDestino([]));
  }, [empresaDestinoIdNum]);

  // Funciones de navegación
  const irPaginaAnterior = () => {
    if (paginaActual > 0) {
      setPaginaActual(paginaActual - 1);
    }
  };

  const irPaginaSiguiente = () => {
    if (paginaActual < paginas.length - 1) {
      setPaginaActual(paginaActual + 1);
    }
  };

  const tienePaginaAnterior = paginaActual > 0;
  const tienePaginaSiguiente = paginaActual < paginas.length - 1;

  // Id del albarán que tiene la imagen (página actual o primera página del documento que la tenga)
  const imagenAlbaranId: number | null = albaranActual?.tiene_imagen_documento
    ? albaranActual.id
    : (paginas.find((p: Albaran & { tiene_imagen_documento?: boolean }) => p.tiene_imagen_documento)?.id ?? null);

  useEffect(() => {
    // Cargar movimientos del albarán
    const loadMovimientos = async () => {
      try {
        const token = localStorage.getItem('accessToken');
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/albaranes/${albaranActual.id}/movimientos/`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        if (response.ok) {
          const data = await response.json();
          setMovimientos(data);
        }
      } catch (error) {
        console.error('Error cargando movimientos:', error);
      }
    };

    loadMovimientos();
  }, [albaranActual.id]);

  // Detectar si debe iniciar en modo edición desde URL
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const editMode = urlParams.get('edit') === 'true';
    
    // Verificar si es un AC21 usando múltiples criterios (no solo empresas)
    const esAC21 = albaranActual.direccion_transferencia === 'ENTRADA' || 
                   albaranActual.direccion_transferencia === 'SALIDA' ||
                   albaranActual.tipo_documento === 'TRANSFERENCIA';
    
    // Solo activar si:
    // 1. Hay parámetro ?edit=true en la URL
    // 2. Es un AC21
    // 3. No está ya en modo edición
    // 4. Los movimientos se han cargado (para evitar activación prematura)
    if (editMode && esAC21 && !modoEdicion && movimientos.length >= 0) {
      // Activar edición para cualquier AC21 (entrada o salida) una vez que se cargaron los datos
      setTimeout(() => {
        iniciarEdicion();
        // Limpiar el parámetro de la URL para que no se active cada vez
        const newUrl = window.location.pathname;
        window.history.replaceState({}, '', newUrl);
      }, 100); // Pequeño delay para que se carguen los datos primero
    }
  }, [albaranActual.direccion_transferencia, albaranActual.tipo_documento, modoEdicion, movimientos.length]);

  const handlePrintAC21 = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        toast.error('No hay sesión activa');
        return;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/albaranes/${albaranActual.id}/generar-ac21-html/`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const htmlContent = await response.text();
        const printWindow = window.open('', '_blank');
        if (printWindow) {
          printWindow.document.write(htmlContent);
          printWindow.document.close();
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

  const handleDarSalida = () => {
    // Siempre usar el documento principal para "Dar Salida", no la página actual
    const documentoPrincipalId = albaran.documento_principal ? albaran.documento_principal : albaran.id;
    router.push(`/albaranes/crear-ac21-salida/nuevo?from=${documentoPrincipalId}`);
  };

  // Funciones para modo edición
  const iniciarEdicion = () => {
    setDatosEditables({
      numero_registro_salida: albaranActual.numero_registro_salida || '',
      numero_registro_entrada: albaranActual.numero_registro_entrada || '',
      fecha_informe: albaranActual.fecha_informe || '',
      fecha_transaccion: albaranActual.fecha_transaccion || '',
      tipo_documento: albaranActual.tipo_documento || '',
      codigo_contabilidad: albaranActual.codigo_contabilidad || '',
      observaciones_odmc: albaranActual.observaciones_odmc || '',
      estado_material: albaranActual.estado_material || '',
      // IDs de empresas para seleccionar del catálogo
      empresa_origen_id: albaranActual.empresa_origen || '',
      empresa_destino_id: albaranActual.empresa_destino || '',
      // Datos de firmas
      firma_a_nombre_apellidos: albaranActual.firma_a_nombre_apellidos || '',
      firma_a_cargo: albaranActual.firma_a_cargo || '',
      firma_a_empleo_rango: albaranActual.firma_a_empleo_rango || '',
      firma_b_nombre_apellidos: albaranActual.firma_b_nombre_apellidos || '',
      firma_b_cargo: albaranActual.firma_b_cargo || '',
      firma_b_empleo_rango: albaranActual.firma_b_empleo_rango || '',
      // Destinatario autorizado
      destinatario_autorizado_testigo: albaranActual.destinatario_autorizado_testigo || false,
      destinatario_autorizado_otro: albaranActual.destinatario_autorizado_otro || false,
      destinatario_autorizado_otro_especificar: albaranActual.destinatario_autorizado_otro_especificar || '',
      // Movimientos/productos editables
      movimientos: movimientos.map(mov => ({
        id: mov.id,
        producto_codigo: mov.producto_codigo || mov.descripcion || '',
        descripcion: mov.descripcion || '',
        cantidad: mov.cantidad || 1,
        numero_serie: mov.numero_serie || '',
        cc: (mov.cc && mov.cc.toString().trim() !== '' && mov.cc !== 1) ? mov.cc : '', // CC puede estar vacío - solo mostrar si tiene valor real
        observaciones: mov.observaciones || ''
      })),
      // Accesorios y equipos de prueba editables
      accesorios: (() => {
        try {
          const accesorios = typeof albaranActual.accesorios === 'string' 
            ? JSON.parse(albaranActual.accesorios) 
            : albaranActual.accesorios;
          return Array.isArray(accesorios) ? accesorios : [];
        } catch {
          return [];
        }
      })(),
      equipos_prueba: (() => {
        try {
          const equipos = typeof albaranActual.equipos_prueba === 'string' 
            ? JSON.parse(albaranActual.equipos_prueba) 
            : albaranActual.equipos_prueba;
          return Array.isArray(equipos) ? equipos : [];
        } catch {
          return [];
        }
      })(),
    });
    setModoEdicion(true);
  };

  const cancelarEdicion = () => {
    setModoEdicion(false);
    setDatosEditables({});
  };

  const guardarCambios = async () => {
    try {
      setGuardando(true);
      
      // Función auxiliar para intentar la petición con manejo de token
      const intentarPeticion = async (token: string) => {
        const payload = {
          numero_registro_salida: datosEditables.numero_registro_salida,
          numero_registro_entrada: datosEditables.numero_registro_entrada,
          fecha_informe: datosEditables.fecha_informe,
          fecha_transaccion: datosEditables.fecha_transaccion,
          tipo_documento: datosEditables.tipo_documento,
          codigo_contabilidad: datosEditables.codigo_contabilidad,
          observaciones_odmc: datosEditables.observaciones_odmc,
          estado_material: datosEditables.estado_material,
          // IDs de empresas
          empresa_origen: datosEditables.empresa_origen_id,
          empresa_destino: datosEditables.empresa_destino_id,
          // Datos de firmas
          firma_a_nombre_apellidos: datosEditables.firma_a_nombre_apellidos,
          firma_a_cargo: datosEditables.firma_a_cargo,
          firma_a_empleo_rango: datosEditables.firma_a_empleo_rango,
          firma_b_nombre_apellidos: datosEditables.firma_b_nombre_apellidos,
          firma_b_cargo: datosEditables.firma_b_cargo,
          firma_b_empleo_rango: datosEditables.firma_b_empleo_rango,
          // Destinatario autorizado
          destinatario_autorizado_testigo: datosEditables.destinatario_autorizado_testigo,
          destinatario_autorizado_otro: datosEditables.destinatario_autorizado_otro,
          destinatario_autorizado_otro_especificar: datosEditables.destinatario_autorizado_otro_especificar,
          // Movimientos editados
          movimientos: datosEditables.movimientos,
          // Accesorios y equipos de prueba
          accesorios: JSON.stringify(datosEditables.accesorios || []),
          equipos_prueba: JSON.stringify(datosEditables.equipos_prueba || []),
        };

        console.log('💾 Guardando cambios con payload:', payload);

        return await fetch(`${process.env.NEXT_PUBLIC_API_URL}/albaranes/${albaranActual.id}/`, {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        });
      };

      let token = localStorage.getItem('accessToken');
      
      if (!token) {
        throw new Error('No hay token de autenticación. Por favor, inicia sesión nuevamente.');
      }

      let response = await intentarPeticion(token);

      // Si recibimos 401, intentar renovar el token
      if (response.status === 401) {
        console.log('🔄 Token expirado, intentando renovar...');
        
        const refreshTokenValue = localStorage.getItem('refreshToken');
        if (!refreshTokenValue) {
          console.error('❌ No hay refresh token disponible');
          localStorage.removeItem('accessToken');
          throw new Error('Sesión expirada. Por favor, inicia sesión nuevamente.');
        }

        // Intentar renovar el token usando el endpoint correcto
        // El API_URL ya incluye /api, así que usamos /token/refresh/
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api';
        let refreshResponse: Response | null = null;
        let refreshData: any = null;
        let refreshError: Error | null = null;
        
        try {
          console.log(`🔄 Intentando refresh token en: ${API_URL}/token/refresh/`);
          refreshResponse = await fetch(`${API_URL}/token/refresh/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              refresh: refreshTokenValue
            }),
          });
          
          if (refreshResponse.ok) {
            refreshData = await refreshResponse.json();
            console.log('✅ Refresh token exitoso');
          } else {
            const errorText = await refreshResponse.text();
            console.error(`❌ Error en refresh token (${refreshResponse.status}):`, errorText);
            refreshError = new Error(`Error al renovar token: ${refreshResponse.status}`);
          }
        } catch (error: any) {
          console.error('❌ Error de red al renovar token:', error);
          refreshError = error instanceof Error ? error : new Error('Error de red al renovar la sesión');
        }

        // Si el refresh fue exitoso, usar el nuevo token
        if (refreshResponse && refreshResponse.ok && refreshData && refreshData.access) {
          const newToken = refreshData.access;
          localStorage.setItem('accessToken', newToken);
          console.log('✅ Token renovado exitosamente, reintentando petición original...');
          
          // Reintentar la petición original con el nuevo token
          response = await intentarPeticion(newToken);
        } else {
          // Si el refresh falló, limpiar tokens y lanzar error
          console.error('❌ No se pudo renovar el token. Refresh token expirado o inválido.');
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          
          if (refreshError) {
            throw new Error(`Error al renovar la sesión: ${refreshError.message}. Por favor, inicia sesión nuevamente.`);
          } else if (refreshResponse && refreshResponse.status === 401) {
            throw new Error('Sesión expirada. Por favor, inicia sesión nuevamente.');
          } else {
            throw new Error('Error al renovar la sesión. Por favor, inicia sesión nuevamente.');
          }
        }
      }

      // Clonar la respuesta para poder leerla múltiples veces si es necesario
      const responseClone = response.clone();
      
      // Verificar si la respuesta es exitosa (200-299)
      if (response.ok) {
        let responseData;
        try {
          responseData = await response.json();
        } catch (jsonError) {
          // Si no se puede parsear como JSON, intentar leer como texto desde el clon
          try {
            const textData = await responseClone.text();
            console.warn('⚠️ Respuesta no es JSON válido:', textData);
            // Si el status es 200 pero no es JSON, considerar éxito pero con advertencia
            if (response.status >= 200 && response.status < 300) {
              toast.success('Cambios guardados correctamente (respuesta no válida del servidor)');
              setModoEdicion(false);
              setDatosEditables({});
              // Recargar todos los datos desde el servidor
              await recargarDatos(albaranActual.id);
              router.refresh();
              return;
            }
            throw new Error(`Respuesta inválida del servidor: ${textData}`);
          } catch (textError) {
            console.error('❌ Error leyendo respuesta como texto:', textError);
            throw new Error('Error al procesar la respuesta del servidor');
          }
        }
        
        console.log('✅ Cambios guardados exitosamente:', responseData);
        toast.success('Cambios guardados correctamente');
        setModoEdicion(false);
        
        // Limpiar datos editables
        setDatosEditables({});
        
        // Recargar todos los datos desde el servidor para reflejar los cambios
        // Usar el ID del albarán guardado (puede ser una página o el principal)
        const albaranGuardadoId = responseData?.id || albaranActual.id;
        await recargarDatos(albaranGuardadoId);
        
        // Refrescar la página para actualizar el listado de Entradas
        router.refresh();
      } else {
        // Manejar errores del servidor - leer el body solo una vez
        let errorData;
        const contentType = response.headers.get('content-type');
        
        try {
          if (contentType && contentType.includes('application/json')) {
            errorData = await response.json();
          } else {
            errorData = await response.text();
          }
        } catch (readError) {
          console.error('❌ Error leyendo respuesta de error:', readError);
          errorData = `Error ${response.status}: ${response.statusText}`;
        }
        
        console.error('❌ Error del servidor:', {
          status: response.status,
          statusText: response.statusText,
          data: errorData
        });
        
        // Si el error es 400 (Bad Request), mostrar detalles de validación
        if (response.status === 400 && typeof errorData === 'object') {
          const validationErrors = Object.entries(errorData)
            .map(([field, errors]: [string, any]) => {
              if (Array.isArray(errors)) {
                return `${field}: ${errors.join(', ')}`;
              }
              return `${field}: ${errors}`;
            })
            .join('; ');
          throw new Error(`Error de validación: ${validationErrors}`);
        }
        
        throw new Error(`Error del servidor (${response.status}): ${typeof errorData === 'object' ? JSON.stringify(errorData) : errorData}`);
      }
    } catch (error) {
      console.error('❌ Error guardando cambios:', error);
      
      // Mostrar error más específico al usuario
      if (error instanceof Error) {
        if (error.message.includes('token') || error.message.includes('autenticación')) {
          toast.error('Sesión expirada. Por favor, inicia sesión nuevamente.');
          // Opcional: redirigir al login
          // window.location.href = '/login';
        } else {
          toast.error(`Error al guardar: ${error.message}`);
        }
      } else {
        toast.error('Error al guardar los cambios');
      }
    } finally {
      setGuardando(false);
    }
  };

  const actualizarDatoEditable = (campo: string, valor: any) => {
    setDatosEditables((prev: any) => ({
      ...prev,
      [campo]: valor
    }));
  };

  const actualizarMovimiento = (index: number, campo: string, valor: any) => {
    setDatosEditables((prev: any) => ({
      ...prev,
      movimientos: prev.movimientos.map((mov: any, i: number) => 
        i === index ? { ...mov, [campo]: valor } : mov
      )
    }));
  };

  const agregarMovimiento = () => {
    setDatosEditables((prev: any) => ({
      ...prev,
      movimientos: [
        ...prev.movimientos,
        {
          id: null, // null para nuevos movimientos
          producto_codigo: '',
          descripcion: '',
          cantidad: 1,
          numero_serie: '',
          cc: 1,
          observaciones: ''
        }
      ]
    }));
  };

  const eliminarMovimiento = (index: number) => {
    setDatosEditables((prev: any) => ({
      ...prev,
      movimientos: prev.movimientos.filter((_: any, i: number) => i !== index)
    }));
  };

  // Funciones para manejar accesorios
  const agregarAccesorio = () => {
    const nuevosAccesorios = [...(datosEditables.accesorios || [])];
    nuevosAccesorios.push({ descripcion: '', cantidad: 1 });
    actualizarDatoEditable('accesorios', nuevosAccesorios);
  };

  const actualizarAccesorio = (index: number, campo: string, valor: any) => {
    const nuevosAccesorios = [...(datosEditables.accesorios || [])];
    nuevosAccesorios[index] = { ...nuevosAccesorios[index], [campo]: valor };
    actualizarDatoEditable('accesorios', nuevosAccesorios);
  };

  const eliminarAccesorio = (index: number) => {
    const nuevosAccesorios = [...(datosEditables.accesorios || [])];
    nuevosAccesorios.splice(index, 1);
    actualizarDatoEditable('accesorios', nuevosAccesorios);
  };

  // Funciones para manejar equipos de prueba
  const agregarEquipoPrueba = () => {
    const nuevosEquipos = [...(datosEditables.equipos_prueba || [])];
    nuevosEquipos.push({ codigo: '', comentario: '' });
    actualizarDatoEditable('equipos_prueba', nuevosEquipos);
  };

  const actualizarEquipoPrueba = (index: number, campo: string, valor: any) => {
    const nuevosEquipos = [...(datosEditables.equipos_prueba || [])];
    nuevosEquipos[index] = { ...nuevosEquipos[index], [campo]: valor };
    actualizarDatoEditable('equipos_prueba', nuevosEquipos);
  };

  const eliminarEquipoPrueba = (index: number) => {
    const nuevosEquipos = [...(datosEditables.equipos_prueba || [])];
    nuevosEquipos.splice(index, 1);
    actualizarDatoEditable('equipos_prueba', nuevosEquipos);
  };

  return (
    <div className="w-full">
      {/* Formulario AC21 unificado con header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="overflow-hidden bg-white">
          {/* Header integrado con radios de tipo de transacción */}
          <div className="px-4 py-3 border-b-2 border-gray-300 bg-gray-50">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <FileText className="w-6 h-6 text-purple-500" />
                <h1 className={`font-bold transition-all duration-200 ${
                  albaranActual.numero.length > 15 
                    ? 'text-base sm:text-lg' 
                    : albaranActual.numero.length > 10 
                      ? 'text-lg sm:text-xl' 
                      : 'text-xl sm:text-2xl'
                } break-words max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg`}>
                  AC21 - {albaranActual.numero}
                </h1>
              </div>
              <div className="flex items-center gap-4">
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                  {albaranActual.direccion_transferencia === 'ENTRADA' ? 'Entrada' : 'Salida'}
                </span>
                {/* Navegación de páginas */}
                {albaran.total_paginas && albaran.total_paginas > 1 && (
                  <div className="flex items-center gap-2">
                    <Files className="w-4 h-4 text-amber-600" />
                    <span className="text-sm font-medium text-amber-700">
                      {paginaActual + 1} de {albaran.total_paginas}
                    </span>
                    <div className="flex items-center gap-1 ml-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={irPaginaAnterior}
                        disabled={!tienePaginaAnterior || cargandoPaginas}
                        className="h-8 w-8 p-0"
                      >
                        <ChevronLeft className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={irPaginaSiguiente}
                        disabled={!tienePaginaSiguiente || cargandoPaginas}
                        className="h-8 w-8 p-0"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                )}
                {(albaranActual.empresa_origen && albaranActual.empresa_destino && albaranActual.direccion_transferencia === 'ENTRADA') && (
                  <Button 
                    variant="outline"
                    onClick={handleDarSalida}
                    className="bg-green-500 hover:bg-green-600 text-white flex items-center gap-1 text-sm px-3 py-2"
                    disabled={modoEdicion}
                  >
                    <ArrowUpRight className="w-3 h-3" />
                    Dar Salida
                  </Button>
                )}
                
                {/* Botones de edición */}
                {/* Mostrar botón de editar si es un AC21 (tiene direccion_transferencia o tipo_documento = TRANSFERENCIA) */}
                {(albaranActual.direccion_transferencia === 'ENTRADA' || 
                  albaranActual.direccion_transferencia === 'SALIDA' ||
                  albaranActual.tipo_documento === 'TRANSFERENCIA') && 
                  !modoEdicion && (
                  <Button 
                    variant="outline"
                    onClick={iniciarEdicion}
                    className="bg-blue-500 hover:bg-blue-600 text-white flex items-center gap-1 text-sm px-3 py-2"
                  >
                    <Edit className="w-3 h-3" />
                    Editar
                  </Button>
                )}
                
                {modoEdicion && (
                  <>
                    <Button 
                      variant="outline"
                      onClick={guardarCambios}
                      disabled={guardando}
                      className="bg-green-500 hover:bg-green-600 text-white flex items-center gap-1 text-sm px-3 py-2"
                    >
                      <Save className="w-3 h-3" />
                      {guardando ? 'Guardando...' : 'Guardar'}
                    </Button>
                    <Button 
                      variant="outline"
                      onClick={cancelarEdicion}
                      disabled={guardando}
                      className="bg-red-500 hover:bg-red-600 text-white flex items-center gap-1 text-sm px-3 py-2"
                    >
                      <X className="w-3 h-3" />
                      Cancelar
                    </Button>
                  </>
                )}
                
                <Button 
                  variant="outline"
                  onClick={handlePrintAC21}
                  className="bg-purple-500 hover:bg-purple-600 text-white flex items-center gap-1 text-sm px-3 py-2"
                  disabled={modoEdicion}
                >
                  <Printer className="w-3 h-3" />
                  Imprimir AC21
                </Button>
                
                {/* Botón para ver imagen del documento (puede estar en la página actual o en otra página del mismo documento) */}
                {imagenAlbaranId != null && (
                  <Button 
                    variant="outline"
                    onClick={() => setModalImagenAbierto(true)}
                    className="bg-indigo-500 hover:bg-indigo-600 text-white flex items-center gap-1 text-sm px-3 py-2"
                    disabled={modoEdicion}
                  >
                    <Image className="w-3 h-3" />
                    Original
                  </Button>
                )}
                <Button 
                  variant="outline" 
                  onClick={onBack}
                  className="flex items-center gap-1 text-sm px-3 py-2"
                  disabled={modoEdicion}
                >
                  <ArrowLeft className="w-3 h-3" /> 
                  Volver
                </Button>
              </div>
            </div>
            <div className="border-t border-gray-300 mt-3 pt-3 flex flex-wrap gap-4 items-center justify-center">
              {['TRANSFERENCIA', 'INVENTARIO', 'DESTRUCCION', 'RECIBO_MANO', 'OTRO'].map(tipo => (
                <label key={tipo} className="inline-flex items-center text-base font-semibold gap-2">
                  <input
                    type="radio"
                    name="tipoTransaccion"
                    value={tipo}
                    checked={modoEdicion ? (datosEditables.tipo_documento === tipo) : (albaranActual.tipo_documento === tipo)}
                    disabled={!modoEdicion}
                    onChange={(e) => modoEdicion && actualizarDatoEditable('tipo_documento', e.target.value)}
                    className="form-radio w-4 h-4 text-blue-600 border-2 border-gray-400"
                  />
                  <span>{tipo === 'RECIBO_MANO' ? 'RECIBO EN MANO' : tipo}</span>
                </label>
              ))}
            </div>
          </div>
          
          {/* Cuadrantes principales */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-0 min-h-[280px]">
            {/* Columna izquierda: Empresas DE y PARA */}
            <div className="flex flex-col h-full border-r-2 border-gray-300">
              {/* Empresa DE */}
              <div className="flex-1 pb-2 grid grid-cols-[18px_1fr] gap-3 px-4 py-3 min-h-[140px]">
                {/* Letras DE en vertical */}
                <div className="flex flex-col items-center justify-center h-full pt-2 select-none">
                  <span className="text-lg font-bold leading-none">D</span>
                  <span className="text-lg font-bold leading-none">E</span>
                </div>
                <div>
                  <div className="w-full mb-1">
                    {modoEdicion ? (
                      <select
                        className="w-full border rounded-md py-1 px-2 text-sm mb-1 bg-white font-semibold"
                        value={datosEditables.empresa_origen_id || ''}
                        onChange={(e) => actualizarDatoEditable('empresa_origen_id', e.target.value)}
                      >
                        <option value="">Seleccionar empresa origen...</option>
                        {empresas.map(empresa => (
                          <option key={empresa.id} value={empresa.id}>
                            {empresa.nombre}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <div className="w-full border rounded-md py-1 px-2 text-sm mb-1 bg-gray-50 font-semibold">
                        {albaranActual.empresa_origen_info?.nombre || '-'}
                      </div>
                    )}
                  </div>
                  <div className="mt-1 text-xs text-gray-700 space-y-0.5">
                    {modoEdicion ? (
                      (() => {
                        const empresaSeleccionada = empresas.find(e => e.id.toString() === datosEditables.empresa_origen_id?.toString());
                        return empresaSeleccionada ? (
                          <>
                            <div className="bg-blue-50 border border-blue-200 rounded px-2 py-1">
                              <div><strong>Datos de la empresa seleccionada:</strong></div>
                              <div>{empresaSeleccionada.direccion}</div>
                              <div>
                                {[
                                  empresaSeleccionada.codigo_postal,
                                  empresaSeleccionada.ciudad,
                                  empresaSeleccionada.provincia
                                ].filter(Boolean).join(' ')}
                              </div>
                              <div><span className="font-semibold">ODMC Nº:</span> {empresaSeleccionada.numero_odmc || '-'}</div>
                            </div>
                          </>
                        ) : (
                          <div className="text-gray-400 text-center py-2">
                            Selecciona una empresa para ver sus datos
                          </div>
                        );
                      })()
                    ) : (
                      <>
                        <div>{albaranActual.empresa_origen_info?.direccion || '-'}</div>
                        <div>
                          {[
                            albaranActual.empresa_origen_info?.codigo_postal,
                            albaranActual.empresa_origen_info?.ciudad,
                            albaranActual.empresa_origen_info?.provincia
                          ].filter(Boolean).join(' ') || '-'}
                        </div>
                        <div>
                          <div><span className="font-semibold">ODMC Nº:</span> {albaranActual.empresa_origen_info?.numero_odmc || '-'}</div>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Línea divisoria horizontal */}
              <div className="border-t-2 border-gray-300"></div>
              
              {/* Empresa PARA */}
              <div className="flex-1 pt-2 grid grid-cols-[28px_1fr] gap-3 px-4 py-3 min-h-[140px]">
                {/* Letras PARA en vertical */}
                <div className="flex flex-col items-center justify-center h-full select-none">
                  <span className="text-lg font-bold leading-none">P</span>
                  <span className="text-lg font-bold leading-none">A</span>
                  <span className="text-lg font-bold leading-none">R</span>
                  <span className="text-lg font-bold leading-none">A</span>
                </div>
                <div>
                  <div className="w-full mb-1">
                    {modoEdicion ? (
                      <select
                        className="w-full border rounded-md py-1 px-2 text-sm mb-1 bg-white font-semibold"
                        value={datosEditables.empresa_destino_id || ''}
                        onChange={(e) => actualizarDatoEditable('empresa_destino_id', e.target.value)}
                      >
                        <option value="">Seleccionar empresa destino...</option>
                        {empresas.map(empresa => (
                          <option key={empresa.id} value={empresa.id}>
                            {empresa.nombre}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <div className="w-full border rounded-md py-1 px-2 text-sm mb-1 bg-gray-50 font-semibold">
                        {albaranActual.empresa_destino_info?.nombre || '-'}
                      </div>
                    )}
                  </div>
                  <div className="mt-1 text-xs text-gray-700 space-y-0.5">
                    {modoEdicion ? (
                      (() => {
                        const empresaSeleccionada = empresas.find(e => e.id.toString() === datosEditables.empresa_destino_id?.toString());
                        return empresaSeleccionada ? (
                          <>
                            <div className="bg-green-50 border border-green-200 rounded px-2 py-1">
                              <div><strong>Datos de la empresa seleccionada:</strong></div>
                              <div>{empresaSeleccionada.direccion}</div>
                              <div>
                                {[
                                  empresaSeleccionada.codigo_postal,
                                  empresaSeleccionada.ciudad,
                                  empresaSeleccionada.provincia
                                ].filter(Boolean).join(' ')}
                              </div>
                              <div><span className="font-semibold">ODMC Nº:</span> {empresaSeleccionada.numero_odmc || '-'}</div>
                            </div>
                          </>
                        ) : (
                          <div className="text-gray-400 text-center py-2">
                            Selecciona una empresa para ver sus datos
                          </div>
                        );
                      })()
                    ) : (
                      <>
                        <div>{albaranActual.empresa_destino_info?.direccion || '-'}</div>
                        <div>
                          {[
                            albaranActual.empresa_destino_info?.codigo_postal,
                            albaranActual.empresa_destino_info?.ciudad,
                            albaranActual.empresa_destino_info?.provincia
                          ].filter(Boolean).join(' ') || '-'}
                        </div>
                        <div>
                          <div><span className="font-semibold">ODMC Nº:</span> {albaranActual.empresa_destino_info?.numero_odmc || '-'}</div>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>

                         {/* Columna derecha: Datos de registro */}
             <div className="flex flex-col h-full">
               {/* Cuadrante superior derecho: Datos de registro */}
               <div className="flex-1 px-4 py-3 flex flex-col justify-center">
                 <div className="grid grid-cols-2 gap-4">
                   <div>
                     <label className="block text-xs font-semibold text-gray-600 mb-1">Fecha del Informe</label>
                     <input
                       type="date"
                       className={`w-full border rounded p-1 text-sm ${modoEdicion ? 'bg-white' : 'bg-gray-50'}`}
                       value={modoEdicion ? formatearFecha(datosEditables.fecha_informe || '') : formatearFecha(albaranActual.fecha_informe || '')}
                       disabled={!modoEdicion}
                       onChange={(e) => modoEdicion && actualizarDatoEditable('fecha_informe', e.target.value)}
                     />
                   </div>
                   <div>
                     <label className="block text-xs font-semibold text-gray-600 mb-1">Nº Registro de Salida</label>
                     <input
                       type="text"
                       className={`w-full border rounded p-1 text-sm ${modoEdicion ? 'bg-white' : 'bg-gray-50'}`}
                       value={modoEdicion ? (datosEditables.numero_registro_salida || '') : (albaranActual.numero_registro_salida || '')}
                       disabled={!modoEdicion}
                       onChange={(e) => modoEdicion && actualizarDatoEditable('numero_registro_salida', e.target.value)}
                     />
                   </div>
                   <div>
                     <label className="block text-xs font-semibold text-gray-600 mb-1">Fecha de la Transacción</label>
                     <input
                       type="date"
                       className={`w-full border rounded p-1 text-sm ${modoEdicion ? 'bg-white' : 'bg-gray-50'}`}
                       value={modoEdicion ? formatearFecha(datosEditables.fecha_transaccion || '') : formatearFecha(albaranActual.fecha_transaccion || '')}
                       disabled={!modoEdicion}
                       onChange={(e) => modoEdicion && actualizarDatoEditable('fecha_transaccion', e.target.value)}
                     />
                   </div>
                   <div>
                     <label className="block text-xs font-semibold text-gray-600 mb-1">Nº Registro de Entrada</label>
                     <input
                       type="text"
                       className={`w-full border rounded p-1 text-sm ${modoEdicion ? 'bg-white' : 'bg-gray-50'}`}
                       value={modoEdicion ? (datosEditables.numero_registro_entrada || '') : (albaranActual.numero_registro_entrada || '')}
                       disabled={!modoEdicion}
                       onChange={(e) => modoEdicion && actualizarDatoEditable('numero_registro_entrada', e.target.value)}
                     />
                   </div>
                 </div>
               </div>
               
               {/* Línea divisoria horizontal */}
               <div className="border-t-2 border-gray-300"></div>
               
               {/* Cuadrante inferior derecho: Códigos de Contabilidad */}
               <div className="flex-1 p-3 flex flex-col justify-center">
                 <div className="text-xs font-bold text-center mb-2">CÓDIGOS DE CONTABILIDAD (CC)</div>
                 <div className="text-xs text-gray-700 space-y-1">
                   <div>1. Contabilizable por número de serie.</div>
                   <div>2. Contabilizable por cantidad.</div>
                   <div>3. Acuse de recibo inicial. Puede ser controlado según instrucciones particulares del órgano correspondiente.</div>
                 </div>
               </div>
             </div>
          </div>
        </div>

        {/* Tabla de artículos con el mismo diseño */}
        <div className="px-4 py-4">
          {modoEdicion && (
            <div className="mb-3 flex justify-end">
              <button
                onClick={agregarMovimiento}
                className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-xs flex items-center gap-1"
              >
                + Agregar Producto
              </button>
            </div>
          )}
          <div className="overflow-x-auto">
            <table className="min-w-full border border-gray-400 text-xs">
              <thead>
                <tr>
                  <th rowSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle w-12 bg-gray-50">#</th>
                  <th rowSpan={2} className="border-l border-r border-b border-gray-400 px-3 py-1 text-center align-middle bg-gray-50 min-w-[200px]">TÍTULO CORTO / EDICIÓN</th>
                  <th rowSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle w-20 bg-gray-50">CANTIDAD</th>
                  <th colSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle bg-gray-50">NÚMERO DE SERIE</th>
                  <th rowSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle w-12 bg-gray-50">CC</th>
                  <th rowSpan={2} className="border-l border-r border-b border-gray-400 px-3 py-1 text-center align-middle bg-gray-50 min-w-[150px]">OBSERVACIONES</th>
                  {modoEdicion && (
                    <th rowSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle w-16 bg-red-50">ACCIONES</th>
                  )}
                </tr>
                <tr>
                  <th className="border border-gray-400 px-2 py-1 text-center align-middle w-36 bg-gray-50">INICIO</th>
                  <th className="border border-gray-400 px-2 py-1 text-center align-middle w-36 bg-gray-50">FIN</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {(modoEdicion ? datosEditables.movimientos : movimientos).length > 0 ? 
                  (modoEdicion ? datosEditables.movimientos : movimientos).map((movimiento: any, index: number) => (
                  <tr key={modoEdicion ? index : movimiento.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="border border-gray-400 px-2 py-1 text-center align-middle font-semibold">{index + 1}</td>
                    <td className="border border-gray-400 px-3 py-1">
                      {modoEdicion ? (
                        <input
                          type="text"
                          className="w-full text-xs border-0 bg-transparent focus:bg-white focus:border focus:border-blue-300 rounded px-1 py-0.5"
                          value={movimiento.producto_codigo || ''}
                          onChange={(e) => actualizarMovimiento(index, 'producto_codigo', e.target.value)}
                          placeholder="Código/Descripción del producto"
                        />
                      ) : (
                        movimiento.producto_codigo || movimiento.descripcion || '-'
                      )}
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-center">
                      {modoEdicion ? (
                        <input
                          type="number"
                          min="1"
                          className="w-full text-xs border-0 bg-transparent focus:bg-white focus:border focus:border-blue-300 rounded px-1 py-0.5 text-center"
                          value={movimiento.cantidad || 1}
                          onChange={(e) => actualizarMovimiento(index, 'cantidad', parseInt(e.target.value) || 1)}
                        />
                      ) : (
                        movimiento.cantidad || 1
                      )}
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-center">
                      {modoEdicion ? (
                        <input
                          type="text"
                          className="w-full text-xs border-0 bg-transparent focus:bg-white focus:border focus:border-blue-300 rounded px-1 py-0.5 text-center"
                          value={movimiento.numero_serie || ''}
                          onChange={(e) => actualizarMovimiento(index, 'numero_serie', e.target.value)}
                          placeholder="Nº Serie"
                        />
                      ) : (
                        movimiento.numero_serie || '-'
                      )}
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-center">
                      {modoEdicion ? (
                        <input
                          type="text"
                          className="w-full text-xs border-0 bg-transparent focus:bg-white focus:border focus:border-blue-300 rounded px-1 py-0.5 text-center"
                          value={movimiento.numero_serie || ''}
                          onChange={(e) => actualizarMovimiento(index, 'numero_serie', e.target.value)}
                          placeholder="Nº Serie"
                        />
                      ) : (
                        movimiento.numero_serie || '-'
                      )}
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-center">
                      {modoEdicion ? (
                        <select
                          className="w-full text-xs border-0 bg-transparent focus:bg-white focus:border focus:border-blue-300 rounded px-1 py-0.5 text-center"
                          value={movimiento.cc || ''}
                          onChange={(e) => actualizarMovimiento(index, 'cc', e.target.value ? parseInt(e.target.value) : null)}
                        >
                          <option value="">-</option>
                          <option value={1}>1</option>
                          <option value={2}>2</option>
                          <option value={3}>3</option>
                        </select>
                      ) : (
                        movimiento.cc || '-'
                      )}
                    </td>
                    <td className="border border-gray-400 px-3 py-1">
                      {modoEdicion ? (
                        <input
                          type="text"
                          className="w-full text-xs border-0 bg-transparent focus:bg-white focus:border focus:border-blue-300 rounded px-1 py-0.5"
                          value={movimiento.observaciones || ''}
                          onChange={(e) => actualizarMovimiento(index, 'observaciones', e.target.value)}
                          placeholder="Observaciones"
                        />
                      ) : (
                        movimiento.observaciones || '-'
                      )}
                    </td>
                    {modoEdicion && (
                      <td className="border border-gray-400 px-2 py-1 text-center">
                        <button
                          onClick={() => eliminarMovimiento(index)}
                          className="text-red-500 hover:text-red-700 p-1 rounded hover:bg-red-50"
                          title="Eliminar producto"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </td>
                    )}
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={modoEdicion ? 8 : 7} className="border border-gray-400 px-2 py-4 text-center text-gray-500">
                      {modoEdicion ? 
                        'No hay productos. Haz clic en "Agregar Producto" para añadir uno.' : 
                        'No hay artículos registrados en este AC21'
                      }
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Línea ULTIMA LINEA */}
        <div className="mt-2 text-center">
          <div className="border-t border-gray-400 mx-8 relative">
            <div className="absolute inset-x-0 -top-2 flex justify-center">
              <span className="bg-white px-4 text-xs font-bold">ULTIMA LINEA</span>
            </div>
          </div>
        </div>

                {/* Sección Accesorios y Equipos de Prueba - Editable */}
        <div className="mt-6 border-t border-gray-400">
          <div className="p-4">
            {/* Zona horizontal dividida en 2 cuadrantes */}
            <div className="grid grid-cols-2 gap-8 min-h-[200px]">
              
              {/* Cuadrante izquierdo: Accesorios */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-bold">ACCESORIOS ENTREGADOS CON CADA EQUIPO:</h3>
                  {modoEdicion && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={agregarAccesorio}
                      className="text-xs px-2 py-1 h-6"
                    >
                      + Agregar
                    </Button>
                  )}
                </div>
                <div className="space-y-2">
                  {modoEdicion ? (
                    (datosEditables.accesorios || []).length > 0 ? (
                      (datosEditables.accesorios || []).map((accesorio: any, index: number) => (
                        <div key={index} className="flex items-center gap-2 bg-gray-50 p-2 rounded">
                          <input
                            type="text"
                            placeholder="Descripción del accesorio"
                            value={accesorio.descripcion || ''}
                            onChange={(e) => actualizarAccesorio(index, 'descripcion', e.target.value)}
                            className="flex-1 text-xs border rounded px-2 py-1"
                          />
                          <input
                            type="number"
                            placeholder="Cant."
                            min="1"
                            value={accesorio.cantidad || 1}
                            onChange={(e) => actualizarAccesorio(index, 'cantidad', parseInt(e.target.value) || 1)}
                            className="w-16 text-xs border rounded px-2 py-1"
                          />
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => eliminarAccesorio(index)}
                            className="text-red-500 hover:bg-red-50 p-1 h-6 w-6"
                          >
                            <X className="w-3 h-3" />
                          </Button>
                        </div>
                      ))
                    ) : (
                      <div className="text-gray-500 text-xs text-center py-4">
                        No hay accesorios. Haz clic en "Agregar" para añadir uno.
                      </div>
                    )
                  ) : (
                    (() => {
                      try {
                        const accesorios = typeof albaranActual.accesorios === 'string' 
                          ? JSON.parse(albaranActual.accesorios) 
                          : albaranActual.accesorios;
                        
                        if (Array.isArray(accesorios) && accesorios.length > 0) {
                          return (
                            <table className="w-full text-xs">
                              <tbody>
                                {accesorios.map((accesorio: any, index: number) => (
                                  <tr key={index}>
                                    <td className="w-12"></td>
                                    <td className="pl-4 py-0.5">{accesorio.descripcion || '-'}</td>
                                    <td className="text-right w-8">{accesorio.cantidad || 1}</td>
                                    <td className="w-24"></td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          );
                        } else {
                          return (
                            <div className="text-gray-500 text-xs pl-4">No hay accesorios especificados</div>
                          );
                        }
                      } catch (error) {
                        return (
                          <div className="text-gray-500 text-xs pl-4">Error al procesar accesorios</div>
                        );
                      }
                    })()
                  )}
                </div>
              </div>

              {/* Cuadrante derecho: Equipos de Prueba */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-bold">EQUIPOS DE PRUEBA AICOX:</h3>
                  {modoEdicion && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={agregarEquipoPrueba}
                      className="text-xs px-2 py-1 h-6"
                    >
                      + Agregar
                    </Button>
                  )}
                </div>
                <div className="space-y-2">
                  {modoEdicion ? (
                    (datosEditables.equipos_prueba || []).length > 0 ? (
                      (datosEditables.equipos_prueba || []).map((equipo: any, index: number) => (
                        <div key={index} className="flex items-center gap-2 bg-gray-50 p-2 rounded">
                          <input
                            type="text"
                            placeholder="Código del equipo"
                            value={equipo.codigo || ''}
                            onChange={(e) => actualizarEquipoPrueba(index, 'codigo', e.target.value)}
                            className="w-24 text-xs border rounded px-2 py-1"
                          />
                          <input
                            type="text"
                            placeholder="Comentario"
                            value={equipo.comentario || ''}
                            onChange={(e) => actualizarEquipoPrueba(index, 'comentario', e.target.value)}
                            className="flex-1 text-xs border rounded px-2 py-1"
                          />
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => eliminarEquipoPrueba(index)}
                            className="text-red-500 hover:bg-red-50 p-1 h-6 w-6"
                          >
                            <X className="w-3 h-3" />
                          </Button>
                        </div>
                      ))
                    ) : (
                      <div className="text-gray-500 text-xs text-center py-4">
                        No hay equipos de prueba. Haz clic en "Agregar" para añadir uno.
                      </div>
                    )
                  ) : (
                    (() => {
                      try {
                        const equipos = typeof albaranActual.equipos_prueba === 'string' 
                          ? JSON.parse(albaranActual.equipos_prueba) 
                          : albaranActual.equipos_prueba;
                        
                        if (Array.isArray(equipos) && equipos.length > 0) {
                          return (
                            <table className="w-full text-xs">
                              <tbody>
                                {equipos.map((equipo: any, index: number) => (
                                  <tr key={index}>
                                    <td className="w-16"></td>
                                    <td className="pl-4 py-0.5">{equipo.codigo || equipo.descripcion || '-'}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          );
                        } else {
                          return (
                            <div className="text-gray-500 text-xs pl-4">No hay equipos de prueba especificados</div>
                          );
                        }
                      } catch (error) {
                        return (
                          <div className="text-gray-500 text-xs pl-4">Error al procesar equipos de prueba</div>
                        );
                      }
                    })()
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

                                {/* Sección 14 - Material ha sido */}
        <div className="mt-6 p-4 border-t border-gray-400 bg-gray-50">
          <div className="flex items-center gap-6">
            <span className="font-bold text-xs">14. EL MATERIAL HA SIDO:</span>
            {['RECIBIDO', 'INVENTARIADO', 'DESTRUIDO'].map(estado => (
              <label key={estado} className="inline-flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={modoEdicion ? (datosEditables.estado_material === estado) : (albaranActual.estado_material === estado)}
                  disabled={!modoEdicion}
                  onChange={(e) => {
                    if (modoEdicion) {
                      if (e.target.checked) {
                        // Si se marca, seleccionar este y desmarcar los otros
                        actualizarDatoEditable('estado_material', estado);
                      } else {
                        // Si se desmarca, limpiar selección
                        actualizarDatoEditable('estado_material', '');
                      }
                    }
                  }}
                  className="appearance-none w-4 h-4 border-2 border-gray-400 checked:bg-black checked:border-black disabled:opacity-50 checked:after:content-['✓'] checked:after:text-white checked:after:text-xs checked:after:flex checked:after:items-center checked:after:justify-center checked:after:h-full"
                />
                <span className="text-sm font-medium">{estado}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Firmas y Observaciones - Layout compacto en una fila */}
        <div className="border-t border-gray-400">
          {/* Títulos y checkboxes en una sola línea horizontal - Grid 2 columnas */}
          <div className="grid grid-cols-2 items-center p-3 border-b border-gray-400 bg-gray-50">
            <div className="font-bold text-xs">15. DESTINATARIO AUTORIZADO DEL MATERIAL DE CIFRA</div>
            <div className="flex items-center gap-4">
              <span className="font-bold text-xs">16. (marcar X) ⇒</span>
              <label className="inline-flex items-center gap-1">
                <input 
                  type="checkbox" 
                  disabled={!modoEdicion}
                  className="appearance-none w-4 h-4 border-2 border-gray-400 checked:bg-black checked:border-black disabled:opacity-50 checked:after:content-['✓'] checked:after:text-white checked:after:text-xs checked:after:flex checked:after:items-center checked:after:justify-center checked:after:h-full" 
                  checked={modoEdicion ? 
                    (datosEditables.destinatario_autorizado_testigo === true) : 
                    (albaranActual.destinatario_autorizado_testigo === true || (albaranActual.requiere_testigo === true && !albaranActual.destinatario_autorizado_testigo))} 
                  onChange={(e) => {
                    if (modoEdicion) {
                      if (e.target.checked) {
                        // Si se marca TESTIGO, desmarcar OTRO
                        actualizarDatoEditable('destinatario_autorizado_testigo', true);
                        actualizarDatoEditable('destinatario_autorizado_otro', false);
                      } else {
                        // Si se desmarca TESTIGO
                        actualizarDatoEditable('destinatario_autorizado_testigo', false);
                      }
                    }
                  }}
                /> TESTIGO
              </label>
              <label className="inline-flex items-center gap-1">
                <input 
                  type="checkbox" 
                  disabled={!modoEdicion}
                  className="appearance-none w-4 h-4 border-2 border-gray-400 checked:bg-black checked:border-black disabled:opacity-50 checked:after:content-['✓'] checked:after:text-white checked:after:text-xs checked:after:flex checked:after:items-center checked:after:justify-center checked:after:h-full" 
                  checked={modoEdicion ? 
                    (datosEditables.destinatario_autorizado_otro === true) : 
                    (albaranActual.destinatario_autorizado_otro === true || (albaranActual.requiere_testigo === false && !albaranActual.destinatario_autorizado_otro))} 
                  onChange={(e) => {
                    if (modoEdicion) {
                      if (e.target.checked) {
                        // Si se marca OTRO, desmarcar TESTIGO
                        actualizarDatoEditable('destinatario_autorizado_testigo', false);
                        actualizarDatoEditable('destinatario_autorizado_otro', true);
                      } else {
                        // Si se desmarca OTRO
                        actualizarDatoEditable('destinatario_autorizado_otro', false);
                      }
                    }
                  }}
                /> OTRO
              </label>
              {(modoEdicion && datosEditables.destinatario_autorizado_otro === true) ? (
                <input
                  type="text"
                  className="text-xs border rounded px-1 py-0.5 w-32"
                  value={datosEditables.destinatario_autorizado_otro_especificar || ''}
                  onChange={(e) => actualizarDatoEditable('destinatario_autorizado_otro_especificar', e.target.value)}
                  placeholder="Especificar..."
                />
              ) : (
                (!modoEdicion && albaranActual.destinatario_autorizado_otro_especificar && (
                  <span className="text-xs">({albaranActual.destinatario_autorizado_otro_especificar})</span>
                ))
              )}
            </div>
          </div>

          {/* Rellenar firmas desde cryptocustodio (visible en edición; desplegables si hay empresa destino y cryptocustodios) */}
          {modoEdicion && (
            <div className="px-4 pb-2 flex flex-wrap items-center gap-2 text-xs">
              <span className="font-medium">Rellenar desde cryptocustodio:</span>
              {cryptocustodiosDestino.length > 0 ? (
                <>
                  <select
                    className="border rounded px-2 py-1 text-xs bg-white"
                    value={selectedCryptocustodioIdFirmaA}
                    onChange={(e) => {
                      const id = e.target.value;
                      setSelectedCryptocustodioIdFirmaA(id);
                      if (!id) return;
                      const cc = cryptocustodiosDestino.find((c: any) => String(c.id) === id);
                      if (cc) {
                        setDatosEditables((prev: any) => ({
                          ...prev,
                          firma_a_empleo_rango: cc.empleo_rango ?? '',
                          firma_a_nombre_apellidos: cc.nombre_apellidos ?? '',
                          firma_a_cargo: cc.cargo ?? '',
                        }));
                      }
                    }}
                  >
                    <option value="">— Firma A —</option>
                    {cryptocustodiosDestino.map((cc: any) => (
                      <option key={cc.id} value={cc.id}>{cc.nombre_apellidos}</option>
                    ))}
                  </select>
                  <select
                    className="border rounded px-2 py-1 text-xs bg-white"
                    value={selectedCryptocustodioIdFirmaB}
                    onChange={(e) => {
                      const id = e.target.value;
                      setSelectedCryptocustodioIdFirmaB(id);
                      if (!id) return;
                      const cc = cryptocustodiosDestino.find((c: any) => String(c.id) === id);
                      if (cc) {
                        setDatosEditables((prev: any) => ({
                          ...prev,
                          firma_b_empleo_rango: cc.empleo_rango ?? '',
                          firma_b_nombre_apellidos: cc.nombre_apellidos ?? '',
                          firma_b_cargo: cc.cargo ?? '',
                        }));
                      }
                    }}
                  >
                    <option value="">— Firma B —</option>
                    {cryptocustodiosDestino.map((cc: any) => (
                      <option key={cc.id} value={cc.id}>{cc.nombre_apellidos}</option>
                    ))}
                  </select>
                </>
              ) : (
                <span className="text-amber-700">Empresa destino sin cryptocustodios o no seleccionada.</span>
              )}
            </div>
          )}

          {/* Campos de firma en dos columnas */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4">
            {/* Sección 15: Primera firma */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <div className="font-semibold mb-1">a. Firma</div>
                <div className="h-8 border-b border-gray-300"></div>
              </div>
              <div>
                <div className="font-semibold mb-1">b. Empleo/Rango</div>
                {modoEdicion ? (
                  <input
                    type="text"
                    className="w-full text-xs border rounded px-1 py-0.5"
                    value={datosEditables.firma_a_empleo_rango || ''}
                    onChange={(e) => actualizarDatoEditable('firma_a_empleo_rango', e.target.value)}
                    placeholder="Empleo/Rango"
                  />
                ) : (
                  <div className="h-6 font-bold">{albaranActual.firma_a_empleo_rango || ''}</div>
                )}
              </div>
              <div>
                <div className="font-semibold mb-1">c. Nombre y Apellidos</div>
                {modoEdicion ? (
                  <input
                    type="text"
                    className="w-full text-xs border rounded px-1 py-0.5"
                    value={datosEditables.firma_a_nombre_apellidos || ''}
                    onChange={(e) => actualizarDatoEditable('firma_a_nombre_apellidos', e.target.value)}
                    placeholder="Nombre y Apellidos"
                  />
                ) : (
                  <div className="h-6 font-bold">{albaranActual.firma_a_nombre_apellidos || ''}</div>
                )}
              </div>
              <div>
                <div className="font-semibold mb-1">d. Cargo</div>
                {modoEdicion ? (
                  <input
                    type="text"
                    className="w-full text-xs border rounded px-1 py-0.5"
                    value={datosEditables.firma_a_cargo || ''}
                    onChange={(e) => actualizarDatoEditable('firma_a_cargo', e.target.value)}
                    placeholder="Cargo"
                  />
                ) : (
                  <div className="h-6 font-bold">{albaranActual.firma_a_cargo || ''}</div>
                )}
              </div>
            </div>

            {/* Sección 16: Segunda firma */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <div className="font-semibold mb-1">a. Firma</div>
                <div className="h-8 border-b border-gray-300"></div>
              </div>
              <div>
                <div className="font-semibold mb-1">b. Empleo/Rango</div>
                {modoEdicion ? (
                  <input
                    type="text"
                    className="w-full text-xs border rounded px-1 py-0.5"
                    value={datosEditables.firma_b_empleo_rango || ''}
                    onChange={(e) => actualizarDatoEditable('firma_b_empleo_rango', e.target.value)}
                    placeholder="Empleo/Rango"
                  />
                ) : (
                  <div className="h-6 font-bold">{albaranActual.firma_b_empleo_rango || ''}</div>
                )}
              </div>
              <div>
                <div className="font-semibold mb-1">c. Nombre y Apellidos</div>
                {modoEdicion ? (
                  <input
                    type="text"
                    className="w-full text-xs border rounded px-1 py-0.5"
                    value={datosEditables.firma_b_nombre_apellidos || ''}
                    onChange={(e) => actualizarDatoEditable('firma_b_nombre_apellidos', e.target.value)}
                    placeholder="Nombre y Apellidos"
                  />
                ) : (
                  <div className="h-6 font-bold">{albaranActual.firma_b_nombre_apellidos || ''}</div>
                )}
              </div>
              <div>
                <div className="font-semibold mb-1">d. Cargo</div>
                {modoEdicion ? (
                  <input
                    type="text"
                    className="w-full text-xs border rounded px-1 py-0.5"
                    value={datosEditables.firma_b_cargo || ''}
                    onChange={(e) => actualizarDatoEditable('firma_b_cargo', e.target.value)}
                    placeholder="Cargo"
                  />
                ) : (
                  <div className="h-6 font-bold">{albaranActual.firma_b_cargo || ''}</div>
                )}
              </div>
            </div>
          </div>

          {/* Observaciones */}
          <div className="px-4 py-3 bg-gray-50">
            <div className="font-bold text-sm mb-2">17. OBSERVACIONES DEL ODMC REMITENTE</div>
            {modoEdicion ? (
              <textarea
                className="w-full text-xs text-gray-700 min-h-[60px] p-2 border rounded resize-none"
                value={datosEditables.observaciones_odmc || ''}
                onChange={(e) => actualizarDatoEditable('observaciones_odmc', e.target.value)}
                placeholder="Escriba las observaciones del ODMC remitente..."
              />
            ) : (
              <div className="text-xs text-gray-700 min-h-[24px]">
                {albaranActual.observaciones_odmc || <span className="text-gray-400 italic">Sin observaciones</span>}
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Modal de imagen del documento */}
      <ModalImagenDocumento 
        albaranId={imagenAlbaranId ?? albaranActual?.id ?? albaranLocal.id} 
        numero={albaranActual?.numero ?? albaranLocal.numero} 
        isOpen={modalImagenAbierto}
        onClose={() => setModalImagenAbierto(false)}
      />
    </div>
  );
}