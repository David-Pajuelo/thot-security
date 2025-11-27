"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Upload, Building, ZoomIn, ZoomOut, MoveHorizontal, Pencil, Plus } from "lucide-react";
import ProtectedRoute from "@/components/protectedRoute";
import { processAC21Image, saveAC21Data, processAC21Companies, createEmpresa, guardarTipoProducto, apiFetch, ProductoCatalogo, fetchEmpresas, obtenerProductosDeAlbaran, verificarDocumentoExistente, crearPaginaAdicional } from "@/lib/api";
import { toast } from "sonner";
import DocumentoExistenteModal from "@/components/albaranes/DocumentoExistenteModal";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import dynamic from 'next/dynamic';

// Carga dinámica de pdfjs-dist solo en el cliente
const usePdfJs = () => {
  const [pdfjsLib, setPdfjsLib] = useState<any>(null);
  
  useEffect(() => {
    if (typeof window !== 'undefined') {
      import('pdfjs-dist').then((pdfjs) => {
        pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.js';
        setPdfjsLib(pdfjs);
      });
    }
  }, []);
  
  return pdfjsLib;
};

function UploadAC21PageContent() {
  const router = useRouter();
  const pdfjsLib = usePdfJs();
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [processedData, setProcessedData] = useState<any>({
    cabecera: {
      numero_registro_salida: null,
      fecha_transaccion: null,
      numero_registro_entrada: null,
      fecha_informe: null,
      odmc_numero: null,
    },
          empresa_origen: {
        nombre: null,
        direccion: null,
        codigo_postal: null,
        ciudad: null,
        provincia: null,
        pais: null,
        numero_odmc: null,
        nif: null,
        telefono: null,
        email: null,
      },
      empresa_destino: {
        nombre: null,
        direccion: null,
        codigo_postal: null,
        ciudad: null,
        provincia: null,
        pais: null,
        numero_odmc: null,
        nif: null,
        telefono: null,
        email: null,
      },
    articulos: [],
    accesorios: [],
    equipos_prueba: [],
    observaciones: null,
    firmas: {
      firma_a: { nombre: null, cargo: null, empleo_rango: null },
      firma_b: { nombre: null, cargo: null, empleo_rango: null },
    },
  });
  const [newCompaniesCount, setNewCompaniesCount] = useState<number>(0);
  const [selectedArticulos, setSelectedArticulos] = useState<Set<number>>(new Set());
  const [showEmpresaModal, setShowEmpresaModal] = useState(false);
  const [empresaToEdit, setEmpresaToEdit] = useState<any>(null);
  const [isSavingEmpresa, setIsSavingEmpresa] = useState(false);
  const [productosTipificados, setProductosTipificados] = useState<Map<string, { tipo: string }>>(new Map());
  const [isDragging, setIsDragging] = useState(false);
  const [isEditingEmpresaOrigen, setIsEditingEmpresaOrigen] = useState(false);
  const [isEditingEmpresaDestino, setIsEditingEmpresaDestino] = useState(false);
  const [empresas, setEmpresas] = useState<any[]>([]);

  // Añadir estado para los tipos de artículos
  const TIPOS_ARTICULO = ['C', 'CC'];
  const [articulosTipos, setArticulosTipos] = useState<{ [key: number]: string }>({});

  const [previewImages, setPreviewImages] = useState<string[]>([]);
  const [rotations, setRotations] = useState<number[]>([]);
  const [currentPage, setCurrentPage] = useState(0); // Página actual del visor

  // Función para actualizar el tipo de un artículo
  const handleTipoChange = (index: number, tipo: string) => {
    setArticulosTipos(prev => ({
      ...prev,
      [index]: tipo
    }));
    registerProductType(index, tipo);
  };

  // Función para aplicar un tipo a todos los artículos seleccionados
  const aplicarTipoASeleccionados = (tipo: string) => {
    const nuevosTipos = { ...articulosTipos };
    selectedArticulos.forEach(index => {
      nuevosTipos[index] = tipo;
    });
    setArticulosTipos(nuevosTipos);
    toast.success(`Tipo ${tipo} aplicado a ${selectedArticulos.size} artículos`);
  };

  // Verificar si todos los artículos seleccionados tienen tipo asignado
  const allSelectedHaveType = () => {
    return Array.from(selectedArticulos).every(index => articulosTipos[index]);
  };

  // Verificar si hay datos procesados y artículos válidos para confirmar
  const canConfirm = () => {
    // Debe haber artículos procesados
    return processedData.articulos && processedData.articulos.length > 0;
  };

  // Función para verificar si todos los tipos seleccionados son iguales
  const areSelectedTypesEqual = () => {
    const selectedTypes = Array.from(selectedArticulos).map(index => articulosTipos[index]);
    return new Set(selectedTypes).size === 1;
  };

  // Función para verificar si los artículos seleccionados tienen diferentes partnumbers
  const haveDifferentPartnumbers = () => {
    const selectedPartnumbers = Array.from(selectedArticulos).map(index => processedData.articulos[index].partnumber);
    return new Set(selectedPartnumbers).size > 1;
  };

  // Función para verificar si todos los productos son iguales
  const areAllProductsEqual = () => {
    const partnumbers = processedData.articulos.map((articulo: any) => articulo.partnumber);
    return new Set(partnumbers).size === 1;
  };

  // Función para normalizar códigos de producto
  const normalizaCodigo = (codigo: string) => {
    return codigo ? codigo.trim().toUpperCase().replace(/\s+/g, ' ') : '';
  };

  // Modifica fetchProductosTipificados para usar '/productos/'
  const fetchProductosTipificados = async () => {
    try {
      const productos: ProductoCatalogo[] = await apiFetch('/productos/');
      // Crear un Map con los productos del catálogo, normalizando el código
      const productosMap = new Map<string, { tipo: string }>();
      productos.forEach(producto => {
        // Prioriza el nombre del tipo (tipo_nombre) sobre el id (tipo)
        const tipoFinal = (producto as any).tipo_nombre || producto.tipo;
        if (producto.codigo_producto && tipoFinal) {
          productosMap.set(normalizaCodigo(producto.codigo_producto), { tipo: tipoFinal });
        }
      });
      setProductosTipificados(productosMap);
    } catch (error) {
      console.error('Error al obtener productos del catálogo:', error);
      setProductosTipificados(new Map());
    }
  };

  // Modifica getCodigoProducto para normalizar el código
  const getCodigoProducto = (articulo: any) => {
    return normalizaCodigo(articulo.codigo_producto || articulo.descripcion || '-');
  };

  // Modifica isProductoTipificado para usar el código normalizado
  const isProductoTipificado = (articulo: { codigo_producto?: string }) => {
    const codigo = getCodigoProducto(articulo);
    return codigo ? productosTipificados.has(codigo) : false;
  };

  // Modifica getTipoProducto para usar el código normalizado
  const getTipoProducto = (articulo: { codigo_producto?: string }) => {
    const codigo = getCodigoProducto(articulo);
    const prodTipificado = productosTipificados.get(codigo);
    return prodTipificado ? prodTipificado.tipo || '-' : '-';
  };

  // Función para saber si todos los productos no tipificados son iguales (por código)
  const areAllNonTipificadosEqual = () => {
    const noTipificados = processedData.articulos.filter((art: any) => !isProductoTipificado(art));
    if (noTipificados.length === 0) return true;
    const codigoBase = getCodigoProducto(noTipificados[0]);
    return noTipificados.every((art: any) => getCodigoProducto(art) === codigoBase);
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    // Loguear archivo seleccionado
    console.log('[AC21] Archivo seleccionado:', file);
    // Renombrar el archivo con un timestamp para evitar caché
    const uniqueName = `${Date.now()}_${file.name}`;
    const renamedFile = new File([file], uniqueName, { type: file.type });
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setSelectedFile(renamedFile);
    setPreviewUrl(null); // No usar más previewUrl, solo previewImages
    setPreviewImages([]);
    setRotations([]);
    setCurrentPage(0); // Resetear currentPage al cambiar de archivo
    // Resetear estados relacionados
    setProcessedData({
      cabecera: {
        numero_registro_salida: null,
        fecha_transaccion: null,
        numero_registro_entrada: null,
        fecha_informe: null,
        odmc_numero: null,
      },
                          empresa_origen: {
                        nombre: null,
                        direccion: null,
                        codigo_postal: null,
                        ciudad: null,
                        provincia: null,
                        pais: null,
                        codigo_odmc: null,
                        codigo_emad: null,
                        nif: null,
                        telefono: null,
                        email: null,
                      },
                      empresa_destino: {
                        nombre: null,
                        direccion: null,
                        codigo_postal: null,
                        ciudad: null,
                        provincia: null,
                        pais: null,
                        codigo_odmc: null,
                        codigo_emad: null,
                        nif: null,
                        telefono: null,
                        email: null,
                      },
      articulos: [],
      accesorios: [],
      equipos_prueba: [],
      observaciones: null,
      firmas: {
        firma_a: { nombre: null, cargo: null, empleo_rango: null },
        firma_b: { nombre: null, cargo: null, empleo_rango: null },
      },
    });
    setSelectedArticulos(new Set());
    setArticulosTipos({});
    setNewCompaniesCount(0);
    // Resetear estados de nuevos accesorios y equipos
    setNewAccesorio({
      codigo: '',
      descripcion: '',
      cantidad: '',
    });
    setNewEquipo({
      codigo: '',
      descripcion: '',
      cantidad: '',
    });
    // Si es PDF, convertir a imágenes con MÁXIMA CALIDAD
    if (file.type === 'application/pdf') {
      console.log('📄 PDF detectado, procesando con configuración optimizada...');
      
      if (!pdfjsLib) {
        toast.error('El sistema PDF está cargando, por favor espera un momento e inténtalo de nuevo.');
        return;
      }
      
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
      
      const images: string[] = [];
      const rotArr: number[] = [];
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        
        // CONFIGURACIÓN OPTIMIZADA: 1241px para la dimensión MÁS CORTA
        // Primero obtenemos las dimensiones originales
        const originalViewport = page.getViewport({ scale: 1 });
        
        // Determinamos cuál es la dimensión más corta
        const shortestDimension = Math.min(originalViewport.width, originalViewport.height);
        
        // Calculamos la escala para que la dimensión más corta sea 1241px
        const targetShortestSize = 1241;
        const scale = targetShortestSize / shortestDimension;
        
        // Aplicamos la escala calculada
        const viewport = page.getViewport({ scale: scale, rotation: -page.rotate });
        
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        await page.render({ canvasContext: context!, viewport }).promise;
        
        // Sin recorte - máxima preservación de contenido
        const finalCanvas = canvas;
        
        const shortestFinal = Math.min(finalCanvas.width, finalCanvas.height);
        console.log(`Página ${i}: ${finalCanvas.width}x${finalCanvas.height} px (dimensión más corta: ${shortestFinal}px, escala: ${scale.toFixed(2)}x)`);
        
        // Calidad JPEG máxima para OCR óptimo
        const imageDataUrl = finalCanvas.toDataURL('image/jpeg', 1.0);
        images.push(imageDataUrl);
        rotArr.push(page.rotate || 0);
      }
      console.log(`✅ ${images.length} imágenes de alta calidad generadas para OCR`);
      setPreviewImages(images);
      setRotations(rotArr);
    } else if (file.type.startsWith('image/')) {
      // Imagen suelta
      const url = URL.createObjectURL(renamedFile);
      setPreviewImages([url]);
      setRotations([0]);
    } else {
      toast.error('Formato de archivo no soportado.');
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedFile || previewImages.length === 0) {
      toast.error("Por favor, selecciona una imagen o PDF.");
      return;
    }
    setIsUploading(true);
    toast.info("Procesando imagen AC21, por favor espera...");

    try {
      // Aplicar rotación antes de enviar al OCR
      const rotation = rotations[currentPage] || 0;
      let imageBlob;

      if (rotation === 0) {
        // Sin rotación, usar imagen original
        imageBlob = await fetch(previewImages[currentPage]).then(res => res.blob());
      } else {
        // Aplicar rotación como en la función de descarga
        imageBlob = await new Promise<Blob>((resolve, reject) => {
          const img = new Image();
          img.onload = () => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            if (!ctx) {
              reject(new Error("Error al crear canvas para rotación"));
              return;
            }
            
            // Para rotaciones de 90° y 270°, intercambiar width y height
            let canvasWidth, canvasHeight;
            if (Math.abs(rotation) === 90 || Math.abs(rotation) === 270) {
              canvasWidth = img.height;
              canvasHeight = img.width;
            } else {
              canvasWidth = img.width;
              canvasHeight = img.height;
            }
            
            canvas.width = canvasWidth;
            canvas.height = canvasHeight;
            
            // Configurar transformaciones según el ángulo
            ctx.save();
            
            if (rotation === 90) {
              ctx.translate(canvasWidth, 0);
              ctx.rotate(Math.PI / 2);
            } else if (rotation === 180) {
              ctx.translate(canvasWidth, canvasHeight);
              ctx.rotate(Math.PI);
            } else if (rotation === 270 || rotation === -90) {
              ctx.translate(0, canvasHeight);
              ctx.rotate(-Math.PI / 2);
            }
            
            // Dibujar la imagen
            ctx.drawImage(img, 0, 0);
            ctx.restore();
            
            // Convertir canvas a blob
            canvas.toBlob((blob) => {
              if (blob) {
                resolve(blob);
              } else {
                reject(new Error("Error al convertir canvas a blob"));
              }
            }, 'image/jpeg', 1.0);
          };
          
          img.onerror = () => reject(new Error("Error al cargar imagen"));
          img.src = previewImages[currentPage];
        });
      }

      const formData = new FormData();
      // Usar el nombre de archivo original para el blob, agregando info de rotación
      const fileName = rotation === 0 ? selectedFile.name : `${selectedFile.name}_rotated_${rotation}deg`;
      formData.append("file", imageBlob, fileName); 
      formData.append("document_type", "ac21");

      console.log(`📤 [OCR] Enviando imagen con rotación ${rotation}° aplicada al servicio OCR`);
      const response = await processAC21Image(formData);

      if (response && response.success) {
        // Mapeo cuidadoso de la respuesta a la estructura del estado
        const responseData = response.data;
        // --- LIMPIEZA Y SINCRONIZACIÓN DE CAMPOS ---
        let tipoTransaccion = responseData.cabecera?.tipo_transaccion;
        let numeroRegistroEntrada = responseData.cabecera?.numero_registro_entrada;
        // Si el OCR devuelve 'String' literal, vacío, nulo o no existe, y hay numero_registro_salida, dejar en blanco
        if (!numeroRegistroEntrada || numeroRegistroEntrada === 'String' || numeroRegistroEntrada === tipoTransaccion) {
          if (responseData.cabecera?.numero_registro_salida) {
            numeroRegistroEntrada = '';
          }
        }
        // NO copiar tipoTransaccion a numeroRegistroEntrada bajo ninguna circunstancia
        // Función para limpiar campos con valor 'String'
        const cleanString = (val: any) => (val === 'String' ? '' : val);
        // Limpiar firmas
        const cleanFirmas = (firmas: any) => ({
          firma_a: {
            nombre: cleanString(firmas?.firma_a?.nombre),
            cargo: cleanString(firmas?.firma_a?.cargo),
            empleo_rango: cleanString(firmas?.firma_a?.empleo_rango),
            firma: cleanString(firmas?.firma_a?.firma),
          },
          firma_b: {
            nombre: cleanString(firmas?.firma_b?.nombre),
            cargo: cleanString(firmas?.firma_b?.cargo),
            empleo_rango: cleanString(firmas?.firma_b?.empleo_rango),
            firma: cleanString(firmas?.firma_b?.firma),
          },
        });
        // Limpiar cabecera
        const cleanCabecera = (cab: any) => ({
          numero_registro_salida: cleanString(cab?.numero_registro_salida),
          fecha_transaccion: cleanString(cab?.fecha_transaccion),
          numero_registro_entrada: numeroRegistroEntrada || '',
          fecha_informe: cleanString(cab?.fecha_informe),
          odmc_numero: cleanString(cab?.odmc_numero),
          tipo_transaccion: cleanString(tipoTransaccion),
        });
        // Limpiar empresas
        const cleanEmpresa = (emp: any) => ({
          nombre: cleanString(emp?.nombre),
          direccion: cleanString(emp?.direccion),
          codigo_postal: cleanString(emp?.codigo_postal),
          ciudad: cleanString(emp?.ciudad),
          provincia: cleanString(emp?.provincia),
          pais: cleanString(emp?.pais),
          numero_odmc: cleanString(emp?.numero_odmc),
          nif: cleanString(emp?.nif),
          telefono: cleanString(emp?.telefono),
          email: cleanString(emp?.email),
          id: emp?.id || undefined
        });
        const newFormData: any = {
          cabecera: cleanCabecera(responseData.cabecera || {}),
          empresa_origen: cleanEmpresa(responseData.empresa_origen || {}),
          empresa_destino: cleanEmpresa(responseData.empresa_destino || {}),
          articulos: responseData.articulos || [],
          accesorios: responseData.accesorios || [],
          equipos_prueba: responseData.equipos_prueba || [],
          observaciones: cleanString(responseData.observaciones),
          firmas: cleanFirmas(responseData.firmas || {
            firma_a: { nombre: null, cargo: null, empleo_rango: null },
            firma_b: { nombre: null, cargo: null, empleo_rango: null },
          }),
        };

        setProcessedData(newFormData);
        // Guardar la imagen rotada para su posterior uso
        setImagenParaGuardar(imageBlob);
        console.log("🖼️ [AC21] Imagen rotada guardada para posterior uso", imageBlob.size, "bytes");
        toast.success("Imagen procesada. Revisa los datos y confirma.");
      } else {
        toast.error("Error en el procesamiento del OCR. Revisa los logs del servicio.");
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
      console.error("Error al procesar la imagen:", {
        error,
        message: errorMessage,
        stack: error instanceof Error ? error.stack : undefined
      });
      toast.error(`Error procesando imagen AC21: ${errorMessage}`);
    } finally {
      setIsUploading(false);
    }
  };

  // Estado para el modal de duplicado de albarán
  const [showDuplicadoModal, setShowDuplicadoModal] = useState(false);
  const [productosYaEnAlbaran, setProductosYaEnAlbaran] = useState<any[]>([]);

  // Estados para documento multipágina
  const [showDocumentoExistenteModal, setShowDocumentoExistenteModal] = useState(false);
  const [documentoExistente, setDocumentoExistente] = useState<any>(null);
  const [numeroRegistroDetectado, setNumeroRegistroDetectado] = useState<string>('');

  // Función para crear una nueva página del documento existente
  const handleCrearNuevaPagina = async () => {
    try {
      setShowDocumentoExistenteModal(false);
      setIsUploading(true);

      // Filtrar productos seleccionados
      const articulosAInsertar = processedData.articulos
        .filter((_: any, index: number) => selectedArticulos.has(index))
        .map((art: any) => ({
          ...art,
          tipo: articulosTipos[processedData.articulos.findIndex((originalArt: any) => originalArt === art)] || art.tipo,
        }));

      // Crear payload marcando que es una página adicional
      const payload = {
        ...processedData,
        es_pagina_adicional: true,
        documento_principal_id: documentoExistente.id,
        articulos: articulosAInsertar,
      };

      console.log('📄 [AC21] Creando página adicional:', payload);
      const result = await crearPaginaAdicional(documentoExistente.id, payload);

      if (result.success) {
        toast.success(`Página ${documentoExistente.total_paginas + 1} agregada al documento AC21`);
        router.push('/albaranes/gestion-linea-temporal');
      } else {
        toast.error(result.message || "Error al crear página adicional");
      }
    } catch (error: any) {
      console.error('❌ Error creando página adicional:', error);
      toast.error(error.message || "Error al crear página adicional");
    } finally {
      setIsUploading(false);
    }
  };

  // Función para crear un documento independiente (continuar flujo normal)
  const handleCrearDocumentoIndependiente = () => {
    setShowDocumentoExistenteModal(false);
    // Continuar con el flujo normal de handleConfirm
    handleConfirmContinuado();
  };

  // Función con la lógica original de confirmación (sin verificación de documento existente)
  const handleConfirmContinuado = async () => {
    try {
      setIsUploading(true);

      // Filtrar productos seleccionados para excluir los ya existentes
      const indicesDuplicados = new Set(productosYaEnAlbaran.map((p: any) => p.index));
      const articulosAInsertar = processedData.articulos
        .filter((_: any, index: number) => selectedArticulos.has(index) && !indicesDuplicados.has(index))
        .map((art: any) => ({
          ...art,
          tipo: articulosTipos[processedData.articulos.findIndex((originalArt: any) => originalArt === art)] || art.tipo,
        }));

      if (articulosAInsertar.length === 0) {
        toast.info("No hay productos nuevos para guardar.");
        setIsUploading(false);
        return;
      }

      // Construir el payload solo con los artículos nuevos
      const payload = {
        ...processedData, // Expande todos los datos procesados
        numero: processedData.cabecera?.numero_registro_salida || '',
        numero_registro_salida: processedData.cabecera?.numero_registro_salida || '',
        tipo_documento: processedData.cabecera?.tipo_transaccion || '',
        direccion_transferencia: "ENTRADA", // Forzar ENTRADA para este flujo de AC21
        articulos: articulosAInsertar,
        // Incluir accesorios y equipos de prueba
        accesorios: processedData.accesorios || [],
        equipos_prueba: processedData.equipos_prueba || [],
      };
      
      console.log("[AC21] Payload enviado a saveAC21Data:", JSON.stringify(payload, null, 2));

      const result = await saveAC21Data(payload, imagenParaGuardar || undefined);

      if (!result.success) {
        // Si es error por número duplicado, agregar solo productos nuevos al albarán existente
        if (result.duplicate && (result as any).productos_existentes) {
          console.log("[AC21] AC21 ya existe, agregando solo productos nuevos");
          
          // Mapear productos existentes del backend con los índices locales
          const productosExistentesBackend = (result as any).productos_existentes || [];
          const duplicadosLocales = compararProductosLocalmente(
            productosExistentesBackend.map((p: any) => ({
              codigo: p.producto_codigo,
              numero_serie: p.numero_serie
            })), 
            processedData.articulos
          );
          
          // Filtrar productos que NO son duplicados
          const indicesDuplicados = new Set(duplicadosLocales.map((d: any) => d.index));
          const productosNuevos = processedData.articulos
            .filter((_: any, index: number) => selectedArticulos.has(index) && !indicesDuplicados.has(index))
            .map((art: any) => ({
              ...art,
              tipo: articulosTipos[processedData.articulos.findIndex((originalArt: any) => originalArt === art)] || art.tipo,
            }));

          if (productosNuevos.length === 0) {
            toast.info("Todos los productos seleccionados ya están en el albarán existente.");
            setIsUploading(false);
            return;
          }

          // Crear payload con modo agregar_a_existente
          const payloadExistente = {
            ...processedData,
            modo: 'agregar_a_existente',
            albaran_id: (result as any).albaran_id,
            articulos: productosNuevos,
          };
          
          console.log("[AC21] Agregando productos al albarán existente:", JSON.stringify(payloadExistente, null, 2));
          
          const resultExistente = await saveAC21Data(payloadExistente, imagenParaGuardar || undefined);
          
          if (!resultExistente.success) {
            toast.error(resultExistente.message || "Error al agregar productos al albarán existente", { duration: 5000 });
            setIsUploading(false);
            return;
          }
          
          toast.success(`${productosNuevos.length} producto(s) agregado(s) a la línea temporal para catalogación`);
          setIsUploading(false);
          router.push('/albaranes/gestion-linea-temporal');
          return;
        } else {
          toast.error(result.message || "Error al procesar el AC21", { duration: 5000 });
        }
        setIsUploading(false);
        return;
      }

      toast.success("AC21 procesado correctamente. Los artículos están listos para catalogación.");
      setIsUploading(false);
      router.push('/albaranes/gestion-linea-temporal');
      
    } catch (error: any) {
      console.error("Error en handleConfirmContinuado:", error);
      toast.error(error.message || "Error inesperado al procesar el AC21", { duration: 5000 });
      setIsUploading(false);
    }
  };

  const handleConfirm = async () => {
    if (!processedData || !selectedArticulos || selectedArticulos.size === 0) {
      toast.error("No hay artículos seleccionados para procesar");
      return;
    }

    // Verificar que hay productos válidos para procesar
    const productosSeleccionados = Array.from(selectedArticulos);
    const productosValidos = productosSeleccionados.filter(index => {
      const articulo = processedData.articulos[index];
      return articulo && (articulo.codigo_producto || articulo.descripcion);
    });

    if (productosValidos.length === 0) {
      toast.error("No hay productos válidos seleccionados para procesar");
      return;
    }

    try {
      setIsUploading(true);

      // 1. Verificar si existe un documento con el mismo número de registro
      const numeroRegistro = processedData.cabecera?.numero_registro_entrada || processedData.cabecera?.numero_registro_salida;
      
      if (numeroRegistro) {
        console.log('🔍 [AC21] Verificando documento existente con número:', numeroRegistro);
        const verificacion = await verificarDocumentoExistente(numeroRegistro);
        
        if (verificacion.existe && verificacion.documento) {
          console.log('📄 [AC21] Documento existente encontrado:', verificacion.documento);
          setDocumentoExistente(verificacion.documento);
          setNumeroRegistroDetectado(numeroRegistro);
          setShowDocumentoExistenteModal(true);
          setIsUploading(false);
          return; // Detener el proceso para mostrar el modal
        }
      }

      // Si no existe documento, continuar con el flujo normal
      await handleConfirmContinuado();
      
    } catch (error: any) {
      console.error("Error en handleConfirm:", error);
      toast.error(error.message || "Error inesperado al procesar el AC21", { duration: 5000 });
      setIsUploading(false);
    }
  };

  // Función para agregar productos a un albarán existente
  const handleAgregarAExistente = async () => {
    if (!processedData || !selectedArticulos || selectedArticulos.size === 0) {
      toast.error("No hay artículos seleccionados para agregar");
      return;
    }
    
    try {
      setIsUploading(true);
      
      // Filtrar solo los productos seleccionados y que no están ya en el albarán
      const indicesDuplicados = new Set(productosYaEnAlbaran.map((p: any) => p.index));
      
      const articulosAInsertar = processedData.articulos
        .filter((_: any, index: number) => selectedArticulos.has(index) && !indicesDuplicados.has(index))
        .map((art: any) => ({
          ...art,
          tipo: articulosTipos[processedData.articulos.findIndex((originalArt: any) => originalArt === art)] || art.tipo,
        }));

      if (articulosAInsertar.length === 0) {
        const duplicadosSeleccionados = Array.from(selectedArticulos).filter((index: number) => indicesDuplicados.has(index));
        if (duplicadosSeleccionados.length > 0) {
          toast.warning("Todos los productos seleccionados ya están en el albarán existente.");
        } else {
          toast.info("No hay productos nuevos para agregar.");
        }
        setIsUploading(false);
        return;
      }

      // Verificar que los productos a insertar tienen datos válidos
      const productosValidos = articulosAInsertar.filter((art: any) => 
        art && (art.codigo_producto || art.descripcion) && art.numero_serie
      );

      if (productosValidos.length === 0) {
        toast.error("Los productos seleccionados no tienen datos válidos (código/descripción y número de serie)");
        setIsUploading(false);
        return;
      }

      if (productosValidos.length < articulosAInsertar.length) {
        toast.warning(`Solo ${productosValidos.length} de ${articulosAInsertar.length} productos tienen datos válidos`);
      }

      // Construir payload con modo agregar_a_existente
      const payload = {
        ...processedData,
        modo: 'agregar_a_existente',
        articulos: productosValidos,
      };
      
      console.log("[AC21] Payload para agregar a existente:", JSON.stringify(payload, null, 2));
      
      const result = await saveAC21Data(payload, imagenParaGuardar || undefined);
      
      if (!result.success) {
        toast.error(result.message || "Error al agregar productos al albarán existente", { duration: 5000 });
        return;
      }
      
      toast.success(`${productosValidos.length} producto(s) agregado(s) a la línea temporal para catalogación`);
      router.push('/albaranes/gestion-linea-temporal');
    } catch (error: any) {
      console.error("Error al agregar productos al albarán existente:", error);
      toast.error(error.message || "Error al agregar productos al albarán existente", { duration: 5000 });
      setIsUploading(false);
    }
  };

  const handleSelectAllArticulos = (checked: boolean) => {
    if (checked) {
      // Seleccionar todos los artículos
      const allIndexes = processedData.articulos?.map((_: any, index: number) => index) || [];
      setSelectedArticulos(new Set(allIndexes));
    } else {
      // Deseleccionar todos
      setSelectedArticulos(new Set());
    }
  };

  const handleSelectArticulo = (index: number) => {
    const newSelected = new Set(selectedArticulos);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedArticulos(newSelected);
  };

  const areAllSelected = processedData?.articulos?.length > 0 && 
    selectedArticulos.size === processedData.articulos.length;

  const handleAltaEmpresa = async (formData: any) => {
    try {
      setIsSavingEmpresa(true);
      const nuevaEmpresa = await createEmpresa({
        ...formData,
        activa: true
      });

      // Actualizar los datos procesados con la nueva empresa
      const updatedData = { ...processedData };
      if (empresaToEdit.tipo === 'origen') {
        updatedData.empresa_origen = { ...nuevaEmpresa, es_nueva: false };
      } else {
        updatedData.empresa_destino = { ...nuevaEmpresa, es_nueva: false };
      }
      setProcessedData(updatedData);

      // Actualizar el contador de empresas nuevas
      setNewCompaniesCount(prev => Math.max(0, prev - 1));

      toast.success("Empresa creada correctamente");
      setShowEmpresaModal(false);
    } catch (error: any) {
      console.error("Error creando empresa:", error);
      toast.error(error.message || "Error al crear la empresa");
    } finally {
      setIsSavingEmpresa(false);
    }
  };

  const handleOpenEmpresaModal = (empresa: any, tipo: 'origen' | 'destino') => {
    setEmpresaToEdit({ ...empresa, tipo });
    setShowEmpresaModal(true);
  };

  // Función para registrar el tipo de producto en el catálogo
  const registerProductType = (index: number, tipo: string) => {
    console.log(`Registrando tipo ${tipo} para el producto en la fila ${index}`);
    
    // Usamos la función helper para obtener el código de producto
    const codigoProducto = getCodigoProducto(processedData.articulos[index]);
    
    guardarTipoProducto(codigoProducto, tipo)
      .then(response => {
        if (response.message) {
          console.log('Tipo registrado en el catálogo:', response.message);
          toast.success('Tipo registrado correctamente');
        } else {
          console.error('Error al registrar el tipo en el catálogo');
          toast.error('Error al registrar el tipo');
        }
      })
      .catch(error => {
        console.error('Error en la solicitud de registro:', error);
        toast.error('Error al registrar el tipo');
      });
  };

  // Llamar a fetchProductosTipificados cuando se monte el componente
  useEffect(() => {
    fetchProductosTipificados();
  }, []);

  // Función para manejar el cambio de tipo de transacción
  const handleTipoTransaccionChange = (tipo: string) => {
    setProcessedData((prev: any) => ({
      ...prev,
      cabecera: {
        ...prev.cabecera,
        numero_registro_entrada: tipo
      }
    }));
  };

  // Función para manejar el cambio de estado del material
  const handleEstadoMaterialChange = (estado: string) => {
    setProcessedData((prev: any) => ({
      ...prev,
      estado_material: estado
    }));
  };

  // Función para manejar el cambio de destinatario autorizado
  const handleDestinatarioChange = (campo: 'testigo' | 'otro', valor: boolean) => {
    setProcessedData((prev: any) => ({
      ...prev,
      [campo]: valor
    }));
  };

  // Cargar empresas al montar
  useEffect(() => {
    fetchEmpresas().then(setEmpresas);
  }, []);

  // Estado para el modal de agregar producto manual
  const [showAddProductModal, setShowAddProductModal] = useState(false);
  const [newProduct, setNewProduct] = useState({
    codigo_producto: '',
    cantidad: '',
    numero_serie: '',
    tipo: '',
    observaciones: '',
  });

  // Estados para nuevos accesorios y equipos
  const [newAccesorio, setNewAccesorio] = useState({
    codigo: '',
    descripcion: '',
    cantidad: '',
  });

  const [newEquipo, setNewEquipo] = useState({
    codigo: '',
    descripcion: '',
    cantidad: '',
  });

  // Función para agregar accesorio
  const handleAddAccesorio = () => {
    if (!newAccesorio.codigo || !newAccesorio.cantidad) {
      toast.error("El código y la cantidad son obligatorios");
      return;
    }
    setProcessedData((prev: any) => ({
      ...prev,
      accesorios: [
        ...prev.accesorios,
        {
          codigo: newAccesorio.codigo,
          descripcion: newAccesorio.descripcion,
          cantidad: newAccesorio.cantidad,
        },
      ],
    }));
    setNewAccesorio({
      codigo: '',
      descripcion: '',
      cantidad: '',
    });
    toast.success("Accesorio añadido");
  };

  // Función para agregar equipo de prueba
  const handleAddEquipo = () => {
    if (!newEquipo.codigo || !newEquipo.cantidad) {
      toast.error("El código y la cantidad son obligatorios");
      return;
    }
    setProcessedData((prev: any) => ({
      ...prev,
      equipos_prueba: [
        ...prev.equipos_prueba,
        {
          codigo: newEquipo.codigo,
          descripcion: newEquipo.descripcion,
          cantidad: newEquipo.cantidad,
        },
      ],
    }));
    setNewEquipo({
      codigo: '',
      descripcion: '',
      cantidad: '',
    });
    toast.success("Equipo de prueba añadido");
  };

  // Función para agregar producto manualmente
  const handleAddProduct = (e: React.FormEvent) => {
    e.preventDefault();
    // Validación básica
    if (!newProduct.codigo_producto || !newProduct.cantidad) {
      toast.error("El código de producto y la cantidad son obligatorios");
      return;
    }
    // Añadir el producto al array de artículos
    setProcessedData((prev: any) => ({
      ...prev,
      articulos: [
        ...prev.articulos,
        {
          codigo_producto: newProduct.codigo_producto,
          cantidad: newProduct.cantidad,
          numero_serie: newProduct.numero_serie,
          tipo: newProduct.tipo,
          observaciones: newProduct.observaciones,
          manual: true,
        },
      ],
    }));
    // Si se ha seleccionado tipo, actualizar articulosTipos
    if (newProduct.tipo) {
      setArticulosTipos(prev => ({
        ...prev,
        [processedData.articulos.length]: newProduct.tipo
      }));
    }
    setShowAddProductModal(false);
    setNewProduct({
      codigo_producto: '',
      cantidad: '',
      numero_serie: '',
      tipo: '',
      observaciones: '',
    });
    toast.success("Producto añadido manualmente");
  };

  // useEffect para mapear tipo_documento a tipo_entrada al cargar un albarán existente
  useEffect(() => {
    if (processedData && processedData.cabecera?.numero_registro_entrada) {
      setProcessedData((prev: any) => ({
        ...prev,
        cabecera: {
          ...prev.cabecera,
          numero_registro_entrada: processedData.cabecera.numero_registro_entrada
        }
      }));
    }
    // Solo ejecutar cuando processedData.cabecera.numero_registro_entrada cambie
  }, [processedData?.cabecera?.numero_registro_entrada]);

  // useEffect para inicializar estado_material desde numero_registro_entrada si viene del OCR
  useEffect(() => {
    const numeroEntrada = processedData?.cabecera?.numero_registro_entrada;
    if (
      numeroEntrada &&
      !processedData.estado_material &&
      ['RECIBIDO', 'INVENTARIADO', 'DESTRUCCION'].includes(numeroEntrada)
    ) {
      setProcessedData((prev: any) => ({
        ...prev,
        estado_material: numeroEntrada
      }));
    }
    // Solo ejecuta cuando cambia numero_registro_entrada
  }, [processedData?.cabecera?.numero_registro_entrada]);

  // useEffect para seleccionar todos los artículos detectados por defecto al recibirlos del OCR
  useEffect(() => {
    if (processedData.articulos && processedData.articulos.length > 0) {
      setSelectedArticulos(new Set(processedData.articulos.map((_: any, idx: number) => idx)));
    }
  }, [processedData.articulos]);

  // useEffect para autocompletar tipo de productos tipificados
  useEffect(() => {
    if (processedData.articulos && processedData.articulos.length > 0 && productosTipificados.size > 0) {
      setArticulosTipos((prev: any) => {
        const nuevosTipos = { ...prev };
        processedData.articulos.forEach((articulo: any, idx: number) => {
          const codigo = getCodigoProducto(articulo);
          const prodTipificado = productosTipificados.get(codigo);
          if (prodTipificado && prodTipificado.tipo) {
            nuevosTipos[idx] = prodTipificado.tipo;
          }
        });
        return nuevosTipos;
      });
    }
  }, [processedData.articulos, productosTipificados]);

  // Log de productos tipificados tras cargar el catálogo
  useEffect(() => {
    if (productosTipificados && productosTipificados.size > 0) {
      console.log('🟢 Productos tipificados cargados:', Array.from(productosTipificados.entries()));
    }
  }, [productosTipificados]);

  // Log de cada artículo detectado y su tipificación
  useEffect(() => {
    if (processedData.articulos && processedData.articulos.length > 0) {
      processedData.articulos.forEach((art: any, idx: number) => {
        console.log(`🔎 Artículo ${idx}:`, getCodigoProducto(art), 'Tipificado:', isProductoTipificado(art), 'Tipo:', getTipoProducto(art));
      });
    }
  }, [processedData.articulos, productosTipificados]);

  // Función helper para comparar productos localmente
  const compararProductosLocalmente = (productosExistentes: any[], articulosNuevos: any[]) => {
    console.log('🔍 [AC21] Comparando productos localmente');
    console.log('🔍 [AC21] Productos existentes:', productosExistentes);
    console.log('🔍 [AC21] Artículos nuevos:', articulosNuevos);

    const duplicados: any[] = [];
    
    articulosNuevos.forEach((artNuevo: any, index: number) => {
      const codigoNuevo = getCodigoProducto(artNuevo);
      const serieNueva = artNuevo.numero_serie || '';
      
      const existe = productosExistentes.some((prodExistente: any) => {
        const codigoExistente = normalizaCodigo(prodExistente.codigo);
        const serieExistente = prodExistente.numero_serie || '';
        
        const esIgual = codigoExistente === normalizaCodigo(codigoNuevo) && serieExistente === serieNueva;
        
        if (esIgual) {
          console.log('🔍 [AC21] Producto duplicado encontrado:', { codigoNuevo, serieNueva, index });
        }
        
        return esIgual;
      });
      
      if (existe) {
        duplicados.push({
          codigo: codigoNuevo,
          numero_serie: serieNueva,
          index: index
        });
      }
    });
    
    console.log('🔍 [AC21] Duplicados encontrados:', duplicados);
    return duplicados;
  };

  // useEffect para consultar productos existentes tras procesar el OCR
  useEffect(() => {
    console.log('🔍 [AC21] useEffect verificación duplicados ejecutado');
    console.log('🔍 [AC21] processedData.cabecera:', processedData?.cabecera);
    
    const numero = processedData?.cabecera?.numero_registro_entrada || processedData?.cabecera?.numero_registro_salida;
    
    console.log('🔍 [AC21] Número extraído:', numero);
    console.log('🔍 [AC21] Tiene artículos:', processedData.articulos && processedData.articulos.length > 0);
    
    if (numero && processedData.articulos && processedData.articulos.length > 0) {
      console.log('🔍 [AC21] Iniciando verificación de productos existentes para número:', numero);
      
      obtenerProductosDeAlbaran(numero).then((response) => {
        console.log('🔍 [AC21] Respuesta completa del albarán:', response);
        
        if (response.productos && response.productos.length > 0) {
          console.log('🔍 [AC21] Productos del albarán existente:', response.productos);
          
          // Comparar localmente
          const duplicados = compararProductosLocalmente(response.productos, processedData.articulos);
          
          // Actualizar estado con productos ya en albarán
          setProductosYaEnAlbaran(duplicados);
          
          // Desmarcar los duplicados
          setSelectedArticulos(prev => {
            const newSet = new Set(prev);
            duplicados.forEach((dup: any) => {
              if (dup.index !== undefined) {
                console.log('🔍 [AC21] Desmarcando producto duplicado índice:', dup.index);
                newSet.delete(dup.index);
              }
            });
            return newSet;
          });
          
          if (duplicados.length > 0) {
            console.log('🔍 [AC21] Se encontraron productos duplicados, mostrando indicadores visuales');
            toast.info(`Se encontraron ${duplicados.length} producto(s) que ya están en el albarán ${response.albaran_numero}`);
          }
        } else {
          console.log('🔍 [AC21] No se encontró albarán o no tiene productos');
          setProductosYaEnAlbaran([]);
        }
      }).catch(error => {
        console.error('❌ [AC21] Error obteniendo productos del albarán:', error);
        setProductosYaEnAlbaran([]);
      });
    } else {
      console.log('🔍 [AC21] No se ejecuta verificación - Número:', numero, 'Artículos:', processedData.articulos?.length || 0);
      setProductosYaEnAlbaran([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [processedData.articulos, processedData?.cabecera?.numero_registro_entrada, processedData?.cabecera?.numero_registro_salida]);

  // Función para rotar manualmente una imagen
  const handleRotate = (idx: number, delta: number) => {
    const newRotations = [...rotations];
    newRotations[idx] = (newRotations[idx] + delta + 360) % 360;
    setRotations(newRotations);
  };

  // Añade refs para los controles externos
  // Estado para la imagen procesada (rotada y lista para guardar)
  const [imagenParaGuardar, setImagenParaGuardar] = useState<Blob | null>(null);

  let zoomInRef: (() => void) | null = null;
  let zoomOutRef: (() => void) | null = null;
  let resetTransformRef: (() => void) | null = null;

  // FUNCIÓN PARA DESCARGAR IMAGEN GENERADA CON ROTACIÓN APLICADA
  const downloadGeneratedImage = (pageIndex: number = 0) => {
    if (previewImages.length === 0) {
      toast.error("No hay imágenes generadas para descargar");
      return;
    }
    
    const imageDataUrl = previewImages[pageIndex];
    const rotation = rotations[pageIndex] || 0;
    
    // Si no hay rotación, descargar directamente
    if (rotation === 0) {
      const link = document.createElement('a');
      link.download = `imagen_1241px_pagina_${pageIndex + 1}_rotada_${rotation}deg_${Date.now()}.jpg`;
      link.href = imageDataUrl;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast.success(`Imagen página ${pageIndex + 1} descargada sin rotación`);
      return;
    }
    
         // Aplicar rotación a la imagen antes de descargar
     const img = new Image();
     img.onload = () => {
       const canvas = document.createElement('canvas');
       const ctx = canvas.getContext('2d');
       
       if (!ctx) {
         toast.error("Error al crear canvas para rotación");
         return;
       }
       
       // Para rotaciones de 90° y 270°, intercambiar width y height
       let canvasWidth, canvasHeight;
       if (Math.abs(rotation) === 90 || Math.abs(rotation) === 270) {
         canvasWidth = img.height;
         canvasHeight = img.width;
       } else {
         canvasWidth = img.width;
         canvasHeight = img.height;
       }
       
       canvas.width = canvasWidth;
       canvas.height = canvasHeight;
       
       // Configurar transformaciones según el ángulo
       ctx.save();
       
       if (rotation === 90) {
         ctx.translate(canvasWidth, 0);
         ctx.rotate(Math.PI / 2);
       } else if (rotation === 180) {
         ctx.translate(canvasWidth, canvasHeight);
         ctx.rotate(Math.PI);
       } else if (rotation === 270 || rotation === -90) {
         ctx.translate(0, canvasHeight);
         ctx.rotate(-Math.PI / 2);
       }
       
       // Dibujar la imagen
       ctx.drawImage(img, 0, 0);
       ctx.restore();
       
       // Descargar imagen rotada
       const rotatedDataUrl = canvas.toDataURL('image/jpeg', 1.0);
       const link = document.createElement('a');
       link.download = `imagen_1241px_pagina_${pageIndex + 1}_rotada_${rotation}deg_${Date.now()}.jpg`;
       link.href = rotatedDataUrl;
       document.body.appendChild(link);
       link.click();
       document.body.removeChild(link);
       
       toast.success(`Imagen página ${pageIndex + 1} descargada con rotación ${rotation}° aplicada`);
     };
    
    img.src = imageDataUrl;
  };

  return (
    <ProtectedRoute>
      <div className="container mx-auto py-2">
        <div className="bg-white rounded-lg shadow-sm p-3">
          <div className="flex justify-between items-center mb-2">
            <h1 className="text-2xl font-bold">Subir AC21</h1>
            <Button 
              variant="outline" 
              onClick={() => router.push("/albaranes")}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" /> 
              Volver a la lista
            </Button>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-3">
            {/* Columna izquierda: Formulario */}
            <div className="space-y-3">
              <form onSubmit={handleSubmit} className="space-y-3">
                <div className="flex gap-4 h-[50px]">
                  {/* Área de drop o selección de archivo (75%) */}
                  <div
                    className={`flex-[3] border-2 border-dashed rounded-lg flex items-center justify-center transition-colors duration-200 ${
                      isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'
                    }`}
                    onDragEnter={e => { e.preventDefault(); setIsDragging(true); }}
                    onDragLeave={e => { e.preventDefault(); setIsDragging(false); }}
                    onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
                    onDrop={e => {
                      e.preventDefault();
                      setIsDragging(false);
                      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                        setSelectedFile(e.dataTransfer.files[0]);
                        const url = URL.createObjectURL(e.dataTransfer.files[0]);
                        setPreviewUrl(url);
                        setProcessedData({
                          cabecera: {
                            numero_registro_salida: null,
                            fecha_transaccion: null,
                            numero_registro_entrada: null,
                            fecha_informe: null,
                            odmc_numero: null,
                          },
                          empresa_origen: {
                            nombre: null,
                            direccion: null,
                            codigo_postal: null,
                            ciudad: null,
                            provincia: null,
                            pais: null,
                            codigo_odmc: null,
                            codigo_emad: null,
                            nif: null,
                            telefono: null,
                            email: null,
                          },
                          empresa_destino: {
                            nombre: null,
                            direccion: null,
                            codigo_postal: null,
                            ciudad: null,
                            provincia: null,
                            pais: null,
                            codigo_odmc: null,
                            codigo_emad: null,
                            nif: null,
                            telefono: null,
                            email: null,
                          },
                          articulos: [],
                          accesorios: [],
                          equipos_prueba: [],
                          observaciones: null,
                          firmas: {
                            firma_a: { nombre: null, cargo: null, empleo_rango: null },
                            firma_b: { nombre: null, cargo: null, empleo_rango: null },
                          },
                        });
                      }
                    }}
                  >
                  <input
                    type="file"
                    accept="image/*,application/pdf"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="file-upload"
                  />
                  <label
                    htmlFor="file-upload"
                      className="cursor-pointer flex items-center justify-center gap-3 w-full h-full"
                    >
                      <Upload className="w-5 h-5 text-gray-400" />
                      <span className="text-gray-600 text-sm">
                        {selectedFile ? selectedFile.name : "Selecciona AC21 o arrástralo aquí"}
                    </span>
                  </label>
                </div>

                  {/* Botón de submit (25%) */}
                <Button
                  type="submit"
                    className="flex-1 bg-purple-500 hover:bg-purple-600 text-white h-full"
                  disabled={!selectedFile || isUploading}
                >
                  {isUploading ? (
                    <span className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white"></div>
                      Procesando...
                    </span>
                  ) : (
                    "Procesar Documento"
                  )}
                </Button>
                </div>
              </form>

              {/* Preview del archivo */}
              <div className="mt-4 bg-gray-50 rounded-lg min-h-[300px] flex items-center justify-center">
                {previewImages.length > 0 ? (
                  // Barra de controles y paginador
                  <div className="w-full">
                    <div className="flex items-center justify-between mb-2 gap-2 flex-wrap">
                      {/* Paginador */}
                      <div className="flex items-center gap-2">
                        <button
                          className="px-2 py-1 rounded bg-gray-200 hover:bg-gray-300"
                          onClick={() => setCurrentPage((prev) => Math.max(0, prev - 1))}
                          disabled={currentPage === 0}
                          title="Página anterior"
                        >&#60;</button>
                        <span className="text-sm text-gray-700">
                          Página {currentPage + 1} de {previewImages.length}
                        </span>
                        <button
                          className="px-2 py-1 rounded bg-gray-200 hover:bg-gray-300"
                          onClick={() => setCurrentPage((prev) => Math.min(previewImages.length - 1, prev + 1))}
                          disabled={currentPage === previewImages.length - 1}
                          title="Página siguiente"
                        >&#62;</button>
                      </div>
                      {/* Controles de zoom y rotación */}
                      <div className="flex items-center gap-1">
                        <Button variant="outline" size="sm" className="bg-white/90 backdrop-blur-sm" onClick={() => zoomInRef?.()} title="Acercar"><ZoomIn className="h-4 w-4" /></Button>
                        <Button variant="outline" size="sm" className="bg-white/90 backdrop-blur-sm" onClick={() => zoomOutRef?.()} title="Alejar"><ZoomOut className="h-4 w-4" /></Button>
                        <Button variant="outline" size="sm" className="bg-white/90 backdrop-blur-sm" onClick={() => resetTransformRef?.()} title="Centrar y restablecer zoom">
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                            <circle cx="8" cy="8" r="1.5" fill="currentColor"/>
                          </svg>
                        </Button>
                        <Button variant="outline" size="sm" className="bg-white/90 backdrop-blur-sm" onClick={() => handleRotate(currentPage, 90)} title="Rotar 90º"><svg width="16" height="16" viewBox="0 0 16 16"><path d="M8 1v2.5A4.5 4.5 0 1 1 3.5 8H2a6 6 0 1 0 6-6z" fill="none" stroke="currentColor" strokeWidth="1.5"/></svg></Button>
                        <Button variant="outline" size="sm" className="bg-white/90 backdrop-blur-sm" onClick={() => handleRotate(currentPage, -90)} title="Rotar -90º"><svg width="16" height="16" viewBox="0 0 16 16"><path d="M8 1v2.5A4.5 4.5 0 1 0 12.5 8H14a6 6 0 1 1-6-6z" fill="none" stroke="currentColor" strokeWidth="1.5"/></svg></Button>
                        {/* Botón de descarga para depuración */}
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="bg-blue-100/90 backdrop-blur-sm border-blue-300 hover:bg-blue-200" 
                          onClick={() => downloadGeneratedImage(currentPage)} 
                          title="Descargar imagen 1241px (Depuración)"
                        >
                          💾
                        </Button>
                      </div>
                    </div>
                    {/* Visor de imagen OPTIMIZADO - ALTURA MÁXIMA */}
                    <div className="relative w-full bg-white rounded-lg border border-gray-200 mb-2 min-h-[650px]">
                      <TransformWrapper
                        initialScale={1.4}
                        minScale={0.3}
                        maxScale={8}
                        centerOnInit={true}
                        centerZoomedOut={true}
                        limitToBounds={false}
                        onZoom={ref => { zoomInRef = ref?.zoomIn; zoomOutRef = ref?.zoomOut; resetTransformRef = ref?.resetTransform; }}
                      >
                        {({ zoomIn, zoomOut, resetTransform, centerView }) => {
                          // Guardar referencias para los botones externos
                          zoomInRef = zoomIn;
                          zoomOutRef = zoomOut;
                          resetTransformRef = () => {
                            // Primero resetear el transform
                            resetTransform();
                            // Luego centrar la vista
                            setTimeout(() => {
                              centerView?.(1.4, 200);
                            }, 50);
                          };
                          return (
                            <TransformComponent 
                              wrapperClass="!w-full !h-[650px]" 
                              contentClass="!w-full !h-full flex items-center justify-center"
                            >
                              <img
                                src={previewImages[currentPage]}
                                alt={`Preview ${currentPage + 1}`}
                                className="max-w-full max-h-full object-contain"
                                style={{ transform: `rotate(${rotations[currentPage] || 0}deg)` }}
                              />
                            </TransformComponent>
                          );
                        }}
                      </TransformWrapper>
                    </div>
                  </div>
                ) : (
                  <span className="text-gray-400">No hay documento cargado</span>
                )}
              </div>
            </div>

            {/* Columna central: Datos procesados */}
            <div className="xl:col-span-2">
              <div className="bg-gray-50 rounded-lg">
                <Tabs defaultValue="datos" className="w-full">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="datos">Datos Principales</TabsTrigger>
                    <TabsTrigger value="empresas" className="flex items-center">
                      Empresas
                      {newCompaniesCount > 0 && (
                        <Badge variant="destructive" className="ml-2 bg-red-500">
                          {newCompaniesCount}
                        </Badge>
                      )}
                    </TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="datos" className="mt-2">
                    <div className="bg-white rounded-lg shadow-sm">
                      {/* Contenedor integrado: Radios arriba + Dos columnas: Empresas izquierda, Datos registro derecha */}
                      <div className="border border-gray-300 rounded overflow-hidden bg-white">
                        {/* Radios de tipo de transacción integrados */}
                        <div className="p-3 border-b-2 border-gray-300 flex flex-wrap gap-4 items-center justify-center">
                          {['TRANSFERENCIA', 'INVENTARIO', 'DESTRUCCION', 'RECIBO EN MANO', 'OTRO'].map(tipo => (
                            <label key={tipo} className="inline-flex items-center text-base font-semibold gap-2">
                              <input
                                type="radio"
                                name="tipoTransaccion"
                                value={tipo}
                                checked={processedData.cabecera?.tipo_transaccion === tipo}
                                onChange={() => setProcessedData((prev: any) => ({
                                  ...prev,
                                  cabecera: {
                                    ...prev.cabecera,
                                    tipo_transaccion: tipo
                                  }
                                }))}
                                className="form-radio w-4 h-4 text-blue-600 border-2 border-gray-400"
                              />
                              <span>{tipo}</span>
                            </label>
                          ))}
                        </div>
                        
                        {/* Cuadrantes principales */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-0 min-h-[260px]">
                        {/* Columna izquierda: Empresas DE y PARA */}
                        <div className="flex flex-col h-full border-r-2 border-gray-300">
                          {/* Empresa DE */}
                          <div className="flex-1 pb-2 grid grid-cols-[18px_1fr] gap-2 p-3 min-h-[150px]">
                            {/* Letras DE en vertical */}
                            <div className="flex flex-col items-center justify-center h-full pt-2 select-none">
                              <span className="text-lg font-bold leading-none">D</span>
                              <span className="text-lg font-bold leading-none">E</span>
                            </div>
                            <div>
                              <div className="relative w-full mb-1 flex items-center gap-2">
                                <select
                                  className="w-full border rounded-md py-1 px-2 text-sm mb-1"
                                  value={processedData.empresa_origen?.id || ''}
                                  onChange={e => {
                                    const empresaSeleccionada = empresas.find(emp => String(emp.id) === e.target.value);
                                    if (empresaSeleccionada) {
                                      setProcessedData((prev: any) => ({
                                        ...prev,
                                        empresa_origen: { ...empresaSeleccionada }
                                      }));
                                    }
                                  }}
                                >
                                  <option value="">Selecciona empresa origen...</option>
                                  {empresas.map(emp => (
                                    <option key={emp.id} value={emp.id}>{emp.nombre}</option>
                                  ))}
                                </select>
                                <Button type="button" size="sm" variant="outline" className="mb-1 px-2 py-1 min-w-0 h-auto" title="Añadir nueva empresa" onClick={() => handleOpenEmpresaModal({}, 'origen')}>
                                  +
                                </Button>
                              </div>
                              {processedData.empresa_origen?.nombre && (
                                <div className="mt-1 text-xs text-gray-700 space-y-0.5">
                                  <div>{processedData.empresa_origen?.direccion || '-'}</div>
                                  <div>
                                    {[
                                      processedData.empresa_origen?.codigo_postal,
                                      processedData.empresa_origen?.ciudad,
                                      processedData.empresa_origen?.provincia
                                    ].filter(Boolean).join(' ') || '-'}
                                  </div>
                                  <div>
                                    <div><span className="font-semibold">ODMC Nº:</span> {processedData.empresa_origen?.numero_odmc || '-'}</div>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                          {/* Línea divisoria horizontal */}
                          <div className="border-t-2 border-gray-300 my-0"></div>
                          {/* Empresa PARA */}
                          <div className="flex-1 pt-2 grid grid-cols-[18px_1fr] gap-2 p-3 min-h-[120px]">
                            {/* Letras PARA en vertical */}
                            <div className="flex flex-col items-center justify-center h-full pt-2 select-none">
                              <span className="text-lg font-bold leading-none">P</span>
                              <span className="text-lg font-bold leading-none">A</span>
                              <span className="text-lg font-bold leading-none">R</span>
                              <span className="text-lg font-bold leading-none">A</span>
                            </div>
                            <div>
                              <div className="relative w-full mb-1 flex items-center gap-2">
                                <select
                                  className="w-full border rounded-md py-1 px-2 text-sm mb-1"
                                  value={processedData.empresa_destino?.id || ''}
                                  onChange={e => {
                                    const empresaSeleccionada = empresas.find(emp => String(emp.id) === e.target.value);
                                    if (empresaSeleccionada) {
                                      setProcessedData((prev: any) => ({
                                        ...prev,
                                        empresa_destino: { ...empresaSeleccionada }
                                      }));
                                    }
                                  }}
                                >
                                  <option value="">Selecciona empresa destino...</option>
                                  {empresas.map(emp => (
                                    <option key={emp.id} value={emp.id}>{emp.nombre}</option>
                                  ))}
                                </select>
                                <Button type="button" size="sm" variant="outline" className="mb-1 px-2 py-1 min-w-0 h-auto" title="Añadir nueva empresa" onClick={() => handleOpenEmpresaModal({}, 'destino')}>
                                  +
                                </Button>
                              </div>
                              {processedData.empresa_destino?.nombre && (
                                <div className="mt-1 text-xs text-gray-700 space-y-0.5">
                                  <div>{processedData.empresa_destino?.direccion || '-'}</div>
                                  <div>
                                    {[
                                      processedData.empresa_destino?.codigo_postal,
                                      processedData.empresa_destino?.ciudad,
                                      processedData.empresa_destino?.provincia
                                    ].filter(Boolean).join(' ') || '-'}
                                  </div>
                                  <div>
                                    <div><span className="font-semibold">ODMC Nº:</span> {processedData.empresa_destino?.numero_odmc || '-'}</div>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Columna derecha: Datos de registro */}
                        <div className="p-4 flex flex-col justify-center space-y-3">
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="block text-xs font-semibold text-gray-600 mb-1">Fecha del Informe</label>
                              <input
                                type="date"
                                className="w-full border rounded p-1 text-sm"
                                value={processedData.cabecera?.fecha_informe || ''}
                                onChange={e => setProcessedData((prev: any) => ({
                                  ...prev,
                                  cabecera: {
                                    ...prev.cabecera,
                                    fecha_informe: e.target.value
                                  }
                                }))}
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-semibold text-gray-600 mb-1">Nº Registro de Salida</label>
                              <input
                                type="text"
                                className="w-full border rounded p-1 text-sm"
                                value={processedData.cabecera?.numero_registro_salida || ''}
                                onChange={e => setProcessedData((prev: any) => ({
                                  ...prev,
                                  cabecera: {
                                    ...prev.cabecera,
                                    numero_registro_salida: e.target.value
                                  }
                                }))}
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-semibold text-gray-600 mb-1">Fecha de la Transacción</label>
                              <input
                                type="date"
                                className="w-full border rounded p-1 text-sm"
                                value={processedData.cabecera?.fecha_transaccion || ''}
                                onChange={e => setProcessedData((prev: any) => ({
                                  ...prev,
                                  cabecera: {
                                    ...prev.cabecera,
                                    fecha_transaccion: e.target.value
                                  }
                                }))}
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-semibold text-gray-600 mb-1">Nº Registro de Entrada</label>
                              <input
                                type="text"
                                className="w-full border rounded p-1 text-sm"
                                value={processedData.cabecera?.numero_registro_entrada || ''}
                                onChange={e => setProcessedData((prev: any) => ({
                                  ...prev,
                                  cabecera: {
                                    ...prev.cabecera,
                                    numero_registro_entrada: e.target.value
                                  }
                                }))}
                              />
                            </div>
                          </div>
                          
                          {/* Línea divisoria horizontal */}
                          <div className="border-t-2 border-gray-300 my-2"></div>
                          
                          {/* Cuadrante inferior derecho: Códigos de Contabilidad */}
                          <div className="mt-2">
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
                    </div>
                  </TabsContent>

                  <TabsContent value="empresas" className="mt-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Empresa Origen */}
                      <div className="bg-white p-3 rounded-md shadow-sm">
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="text-sm font-medium text-gray-600">De:</h4>
                          {processedData.empresa_origen?.es_nueva && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="bg-blue-50 text-blue-600 hover:bg-blue-100 border-blue-200"
                              onClick={() => handleOpenEmpresaModal(processedData.empresa_origen, 'origen')}
                            >
                              Dar de alta
                            </Button>
                          )}
                        </div>
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-semibold text-gray-700">Nombre:</span>
                            <span className="text-sm text-gray-600">{processedData.empresa_origen?.nombre || '-'}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-semibold text-gray-700">Dirección:</span>
                            <span className="text-sm text-gray-600">{processedData.empresa_origen?.direccion || '-'}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-semibold text-gray-700">Código Postal:</span>
                            <span className="text-sm text-gray-600">{processedData.empresa_origen?.codigo_postal || '-'}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-semibold text-gray-700">Ciudad:</span>
                            <span className="text-sm text-gray-600">{processedData.empresa_origen?.ciudad || '-'}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-semibold text-gray-700">Provincia:</span>
                            <span className="text-sm text-gray-600">{processedData.empresa_origen?.provincia || '-'}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-semibold text-gray-700">País:</span>
                            <span className="text-sm text-gray-600">{processedData.empresa_origen?.pais || '-'}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-semibold text-gray-700">Número ODMC:</span>
                            <span className="text-sm text-gray-600">{processedData.empresa_origen?.numero_odmc || '-'}</span>
                          </div>
                        </div>
                      </div>

                      {/* Empresa Destino */}
                      <div className="bg-white p-3 rounded-md shadow-sm">
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="text-sm font-medium text-gray-600">Para:</h4>
                          {processedData.empresa_destino?.es_nueva && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="bg-blue-50 text-blue-600 hover:bg-blue-100 border-blue-200"
                              onClick={() => handleOpenEmpresaModal(processedData.empresa_destino, 'destino')}
                            >
                              Dar de alta
                            </Button>
                          )}
                        </div>
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-semibold text-gray-700">Nombre:</span>
                            <span className="text-sm text-gray-600">{processedData.empresa_destino?.nombre || '-'}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-semibold text-gray-700">Dirección:</span>
                            <span className="text-sm text-gray-600">{processedData.empresa_destino?.direccion || '-'}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-semibold text-gray-700">Código Postal:</span>
                            <span className="text-sm text-gray-600">{processedData.empresa_destino?.codigo_postal || '-'}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-semibold text-gray-700">Ciudad:</span>
                            <span className="text-sm text-gray-600">{processedData.empresa_destino?.ciudad || '-'}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-semibold text-gray-700">Provincia:</span>
                            <span className="text-sm text-gray-600">{processedData.empresa_destino?.provincia || '-'}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-semibold text-gray-700">País:</span>
                            <span className="text-sm text-gray-600">{processedData.empresa_destino?.pais || '-'}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-semibold text-gray-700">Número ODMC:</span>
                            <span className="text-sm text-gray-600">{processedData.empresa_destino?.numero_odmc || '-'}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </div>

              {/* Tabla de artículos pegada al bloque superior */}
              <div>
                <div className="flex justify-between items-center">
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full border border-gray-400 text-xs">
                    <thead>
                      <tr>
                        <th rowSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle w-8">#</th>
                        <th rowSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle">TÍTULO CORTO / EDICIÓN</th>
                        <th rowSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle w-16">CANTIDAD</th>
                        <th colSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle">NÚMERO DE SERIE</th>
                        <th rowSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle w-8">CC</th>
                        <th rowSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle">OBSERVACIONES</th>
                      </tr>
                      <tr>
                        <th className="border border-gray-400 px-2 py-1 text-center align-middle w-28">INICIO</th>
                        <th className="border border-gray-400 px-2 py-1 text-center align-middle w-28">FIN</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {processedData.articulos?.map((articulo: any, index: number) => {
                        const yaExiste = productosYaEnAlbaran.some((prod: any) => prod.index === index);
                        return (
                          <tr key={index} className={yaExiste ? 'bg-gray-100 opacity-70' : (index % 2 === 0 ? 'bg-white' : 'bg-gray-50')}>
                            {/* Numeración */}
                            <td className="border border-gray-400 px-2 py-1 text-center align-middle font-semibold">{index + 1}</td>
                            {/* Título corto/edición */}
                            <td className="border border-gray-400 px-2 py-1">
                              <input
                                type="text"
                                className="w-full border-none bg-transparent focus:ring-0 text-xs"
                                value={articulo.titulo || getCodigoProducto(articulo) || ''}
                                onChange={e => {
                                  const nuevos = [...processedData.articulos];
                                  nuevos[index].titulo = e.target.value;
                                  setProcessedData((prev: any) => ({ ...prev, articulos: nuevos }));
                                }}
                                disabled={yaExiste}
                              />
                            </td>
                            {/* Cantidad */}
                            <td className="border border-gray-400 px-2 py-1 text-center">
                              <input
                                type="number"
                                min="1"
                                className="w-14 border-none bg-transparent focus:ring-0 text-xs text-center"
                                value={articulo.cantidad || ''}
                                onChange={e => {
                                  const nuevos = [...processedData.articulos];
                                  nuevos[index].cantidad = e.target.value;
                                  setProcessedData((prev: any) => ({ ...prev, articulos: nuevos }));
                                }}
                                disabled={yaExiste}
                              />
                            </td>
                            {/* Nº Serie INICIO */}
                            <td className="border border-gray-400 px-2 py-1">
                              <input
                                type="text"
                                className="w-full border-none bg-transparent focus:ring-0 text-xs"
                                value={articulo.numero_serie_inicio || articulo.numero_serie || ''}
                                onChange={e => {
                                  const nuevos = [...processedData.articulos];
                                  nuevos[index].numero_serie_inicio = e.target.value;
                                  setProcessedData((prev: any) => ({ ...prev, articulos: nuevos }));
                                }}
                                disabled={yaExiste}
                              />
                            </td>
                            {/* Nº Serie FIN */}
                            <td className="border border-gray-400 px-2 py-1">
                              <input
                                type="text"
                                className="w-full border-none bg-transparent focus:ring-0 text-xs"
                                value={articulo.numero_serie_fin || articulo.numero_serie || ''}
                                onChange={e => {
                                  const nuevos = [...processedData.articulos];
                                  nuevos[index].numero_serie_fin = e.target.value;
                                  setProcessedData((prev: any) => ({ ...prev, articulos: nuevos }));
                                }}
                                disabled={yaExiste}
                              />
                            </td>
                            {/* CC */}
                            <td className="border border-gray-400 px-2 py-1 text-center">
                              <input
                                type="text"
                                className="w-10 border-none bg-transparent focus:ring-0 text-xs text-center"
                                value={articulo.cc || articulosTipos[index] || ''}
                                onChange={e => {
                                  const nuevos = [...processedData.articulos];
                                  nuevos[index].cc = e.target.value;
                                  setProcessedData((prev: any) => ({ ...prev, articulos: nuevos }));
                                }}
                                disabled={yaExiste}
                              />
                            </td>
                            {/* Observaciones */}
                            <td className="border border-gray-400 px-2 py-1">
                              <input
                                type="text"
                                className="w-full border-none bg-transparent focus:ring-0 text-xs"
                                value={articulo.observaciones || ''}
                                onChange={e => {
                                  const nuevos = [...processedData.articulos];
                                  nuevos[index].observaciones = e.target.value;
                                  setProcessedData((prev: any) => ({ ...prev, articulos: nuevos }));
                                }}
                                disabled={yaExiste}
                              />
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Tablas de Accesorios y Equipos de Prueba */}
              <div className="mt-4">
                <div className="grid grid-cols-2 gap-4">
                  {/* Accesorios - Lado izquierdo */}
                  <div className="border border-gray-300 rounded-md p-4">
                    <h3 className="text-sm font-semibold mb-3">ACCESORIOS ENTREGADOS CON CADA EQUIPO:</h3>
                    <div className="space-y-2">
                      {processedData.accesorios?.map((accesorio: any, index: number) => (
                        <div key={index} className="flex items-center gap-2">
                          <Input
                            type="text"
                            value={accesorio.descripcion || ''}
                            onChange={e => {
                              const nuevos = [...processedData.accesorios];
                              nuevos[index].descripcion = e.target.value;
                              setProcessedData((prev: any) => ({ ...prev, accesorios: nuevos }));
                            }}
                            className="text-xs flex-grow"
                            placeholder="Descripción del accesorio"
                          />
                          <Input
                            type="number"
                            value={accesorio.cantidad || ''}
                            onChange={e => {
                              const nuevos = [...processedData.accesorios];
                              nuevos[index].cantidad = e.target.value;
                              setProcessedData((prev: any) => ({ ...prev, accesorios: nuevos }));
                            }}
                            className="text-xs w-20"
                            min="1"
                            placeholder="Cant."
                          />
                        </div>
                      ))}
                      {/* Formulario para agregar accesorio */}
                      <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-200">
                        <Input
                          type="text"
                          placeholder="Nuevo accesorio..."
                          value={newAccesorio.descripcion}
                          onChange={e => setNewAccesorio(prev => ({ ...prev, descripcion: e.target.value }))}
                          className="text-xs flex-grow"
                        />
                        <Input
                          type="number"
                          placeholder="Cant."
                          value={newAccesorio.cantidad}
                          onChange={e => setNewAccesorio(prev => ({ ...prev, cantidad: e.target.value }))}
                          className="text-xs w-20"
                          min="1"
                        />
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            if (!newAccesorio.descripcion || !newAccesorio.cantidad) {
                              toast.error("La descripción y cantidad son obligatorias");
                              return;
                            }
                            setProcessedData((prev: any) => ({
                              ...prev,
                              accesorios: [
                                ...prev.accesorios,
                                {
                                  descripcion: newAccesorio.descripcion,
                                  cantidad: newAccesorio.cantidad,
                                },
                              ],
                            }));
                            setNewAccesorio({
                              codigo: '',
                              descripcion: '',
                              cantidad: '',
                            });
                            toast.success("Accesorio añadido");
                          }}
                          className="flex items-center gap-1"
                        >
                          <Plus className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Equipos de Prueba - Lado derecho */}
                  <div className="border border-gray-300 rounded-md p-4">
                    <h3 className="text-sm font-semibold mb-3">EQUIPOS PRUEBAS AICOX:</h3>
                    <div className="space-y-2">
                      {processedData.equipos_prueba?.map((equipo: any, index: number) => (
                        <div key={index} className="flex items-center gap-2">
                          <Input
                            type="text"
                            value={equipo.codigo || ''}
                            onChange={e => {
                              const nuevos = [...processedData.equipos_prueba];
                              nuevos[index].codigo = e.target.value;
                              setProcessedData((prev: any) => ({ ...prev, equipos_prueba: nuevos }));
                            }}
                            className="text-xs"
                            placeholder="Código del equipo"
                          />
                        </div>
                      ))}
                      {/* Formulario para agregar equipo de prueba */}
                      <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-200">
                        <Input
                          type="text"
                          placeholder="Nuevo código de equipo..."
                          value={newEquipo.codigo}
                          onChange={e => setNewEquipo(prev => ({ ...prev, codigo: e.target.value }))}
                          className="text-xs flex-grow"
                        />
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            if (!newEquipo.codigo) {
                              toast.error("El código es obligatorio");
                              return;
                            }
                            setProcessedData((prev: any) => ({
                              ...prev,
                              equipos_prueba: [
                                ...prev.equipos_prueba,
                                {
                                  codigo: newEquipo.codigo,
                                },
                              ],
                            }));
                            setNewEquipo({
                              codigo: '',
                              descripcion: '',
                              cantidad: '',
                            });
                            toast.success("Equipo de prueba añadido");
                          }}
                          className="flex items-center gap-1"
                        >
                          <Plus className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Botón de confirmación */}
              <div className="mt-4 flex flex-col sm:flex-row justify-between items-center bg-white rounded-lg shadow-sm p-4 gap-2">
                <div className="w-full sm:w-auto flex justify-start">
                  <Button
                    type="button"
                    variant="outline"
                    className="flex items-center gap-2 bg-blue-50 text-blue-600 hover:bg-blue-100 border-blue-200"
                    onClick={() => setShowAddProductModal(true)}
                  >
                    <Plus className="w-4 h-4" /> Agregar producto
                  </Button>
                </div>
                <Button
                  onClick={handleConfirm}
                  className="w-full sm:w-auto px-8 bg-green-500 hover:bg-green-600 text-white"
                  disabled={isUploading || !canConfirm()}
                  title={
                    !processedData.articulos || processedData.articulos.length === 0 
                      ? "Primero debe procesar un AC21" 
                      : selectedArticulos.size === 0 
                        ? "Debe seleccionar al menos un artículo"
                        : !allSelectedHaveType() 
                          ? "Todos los artículos seleccionados deben tener un tipo asignado"
                          : ""
                  }
                >
                  {isUploading ? (
                    <span className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white"></div>
                      Guardando...
                    </span>
                  ) : (
                    `Confirmar y Guardar (${selectedArticulos.size} artículos)`
                  )}
                </Button>
              </div>

              {/* Sección inferior: Estado del material, firmas y observaciones */}
              <div className="mt-4 border border-gray-300 rounded bg-white p-4">
                {/* Fila 1: El material ha sido (radios) */}
                <div className="grid grid-cols-1 md:grid-cols-4 items-center gap-x-4 gap-y-2 mb-4">
                  <div className="md:col-span-1 text-sm font-semibold text-gray-700">
                    14. EL MATERIAL HA SIDO:
                  </div>
                  <label className="flex items-center gap-2 text-sm">
                    <input type="radio" name="estado_material" value="RECIBIDO" checked={processedData.estado_material === 'RECIBIDO'} onChange={() => handleEstadoMaterialChange('RECIBIDO')} className="form-radio"/>
                    RECIBIDO
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input type="radio" name="estado_material" value="INVENTARIADO" checked={processedData.estado_material === 'INVENTARIADO'} onChange={() => handleEstadoMaterialChange('INVENTARIADO')} className="form-radio"/>
                    INVENTARIADO
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input type="radio" name="estado_material" value="DESTRUIDO" checked={processedData.estado_material === 'DESTRUIDO'} onChange={() => handleEstadoMaterialChange('DESTRUCCION')} className="form-radio"/>
                    DESTRUIDO
                  </label>
                </div>

                {/* Fila 2: Firmas */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 border-t border-gray-300 pt-4">
                  {/* Bloque Izquierdo: Destinatario */}
                  <div className="flex flex-col">
                    <div className="flex justify-between items-center mb-2">
                      <h3 className="text-sm font-semibold text-gray-700">15. DESTINATARIO AUTORIZADO DEL MATERIAL DE CIFRA</h3>
                    </div>
                    <div className="flex-grow grid grid-cols-2 gap-x-4 gap-y-2">
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">a. Firma</label>
                        <Input
                          type="text"
                          className="text-sm"
                          value={processedData.firmas?.firma_a?.firma || ''}
                          onChange={e => setProcessedData((prev: any) => ({ ...prev, firmas: { ...prev.firmas, firma_a: { ...prev.firmas.firma_a, firma: e.target.value } } }))}
                          placeholder="Firma"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">b. Empleo/Rango</label>
                        <Input
                          type="text"
                          className="text-sm"
                          value={processedData.firmas?.firma_a?.empleo_rango || ''}
                          onChange={e => setProcessedData((prev: any) => ({ ...prev, firmas: { ...prev.firmas, firma_a: { ...prev.firmas.firma_a, empleo_rango: e.target.value } } }))}
                          placeholder="Empleo/Rango"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">c. Nombre y Apellidos</label>
                        <Input
                          type="text"
                          className="text-sm"
                          value={processedData.firmas?.firma_a?.nombre || ''}
                          onChange={e => setProcessedData((prev: any) => ({ ...prev, firmas: { ...prev.firmas, firma_a: { ...prev.firmas.firma_a, nombre: e.target.value } } }))}
                          placeholder="Nombre y Apellidos"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">d. Cargo</label>
                        <Input
                          type="text"
                          className="text-sm"
                          value={processedData.firmas?.firma_a?.cargo || ''}
                          onChange={e => setProcessedData((prev: any) => ({ ...prev, firmas: { ...prev.firmas, firma_a: { ...prev.firmas.firma_a, cargo: e.target.value } } }))}
                          placeholder="Cargo"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Bloque Derecho: Testigo / Otro */}
                  <div className="flex flex-col mt-4 md:mt-0">
                     <div className="flex items-center mb-2 gap-4">
                      <h3 className="text-sm font-semibold text-gray-700">16.</h3>
                      <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" checked={processedData.testigo === true} onChange={e => handleDestinatarioChange('testigo', e.target.checked)} className="form-checkbox" />
                        TESTIGO
                      </label>
                      <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" checked={processedData.otro === true} onChange={e => handleDestinatarioChange('otro', e.target.checked)} className="form-checkbox" />
                        OTRO
                      </label>
                    </div>
                    <div className="flex-grow grid grid-cols-2 gap-x-4 gap-y-2">
                       <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">a. Firma</label>
                        <Input
                          type="text"
                          className="text-sm"
                          value={processedData.firmas?.firma_b?.firma || ''}
                          onChange={e => setProcessedData((prev: any) => ({ ...prev, firmas: { ...prev.firmas, firma_b: { ...prev.firmas.firma_b, firma: e.target.value } } }))}
                          placeholder="Firma"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">b. Empleo/Rango</label>
                        <Input
                          type="text"
                          className="text-sm"
                          value={processedData.firmas?.firma_b?.empleo_rango || ''}
                          onChange={e => setProcessedData((prev: any) => ({ ...prev, firmas: { ...prev.firmas, firma_b: { ...prev.firmas.firma_b, empleo_rango: e.target.value } } }))}
                          placeholder="Empleo/Rango"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">c. Nombre y Apellidos</label>
                        <Input
                          type="text"
                          className="text-sm"
                          value={processedData.firmas?.firma_b?.nombre || ''}
                          onChange={e => setProcessedData((prev: any) => ({ ...prev, firmas: { ...prev.firmas, firma_b: { ...prev.firmas.firma_b, nombre: e.target.value } } }))}
                          placeholder="Nombre y Apellidos"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">d. Cargo</label>
                        <Input
                          type="text"
                          className="text-sm"
                          value={processedData.firmas?.firma_b?.cargo || ''}
                          onChange={e => setProcessedData((prev: any) => ({ ...prev, firmas: { ...prev.firmas, firma_b: { ...prev.firmas.firma_b, cargo: e.target.value } } }))}
                          placeholder="Cargo"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Fila 3: Observaciones */}
                <div className="border-t border-gray-300 pt-4 mt-4">
                  <label className="block text-sm font-semibold text-gray-700 mb-1">17. OBSERVACIONES DEL ODMC REMITENTE</label>
                  <textarea
                    className="w-full border rounded p-2 text-sm"
                    rows={2}
                    value={processedData.observaciones || ''}
                    onChange={e => setProcessedData((prev: any) => ({ ...prev, observaciones: e.target.value }))}
                    placeholder="Observaciones..."
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Modal de Alta de Empresa */}
        <Dialog open={showEmpresaModal} onOpenChange={setShowEmpresaModal}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Alta de Empresa {empresaToEdit?.tipo === 'origen' ? 'Origen' : 'Destino'}</DialogTitle>
              <DialogDescription>
                Completa los datos para dar de alta la nueva empresa en el sistema.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={(e) => {
              e.preventDefault();
              const formData = new FormData(e.currentTarget);
              const data = Object.fromEntries(formData.entries());
              handleAltaEmpresa(data);
            }} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <Label htmlFor="nombre">Nombre</Label>
                  <Input id="nombre" name="nombre" defaultValue={empresaToEdit?.nombre} required />
                </div>
                <div className="col-span-2">
                  <Label htmlFor="direccion">Dirección</Label>
                  <Input id="direccion" name="direccion" defaultValue={empresaToEdit?.direccion} required />
                </div>
                <div>
                  <Label htmlFor="codigo_postal">Código Postal</Label>
                  <Input id="codigo_postal" name="codigo_postal" defaultValue={empresaToEdit?.codigo_postal} required />
                </div>
                <div>
                  <Label htmlFor="ciudad">Ciudad</Label>
                  <Input id="ciudad" name="ciudad" defaultValue={empresaToEdit?.ciudad} required />
                </div>
                <div>
                  <Label htmlFor="provincia">Provincia</Label>
                  <Input id="provincia" name="provincia" defaultValue={empresaToEdit?.provincia} required />
                </div>
                <div>
                  <Label htmlFor="pais">País</Label>
                  <Input id="pais" name="pais" defaultValue={empresaToEdit?.pais} required />
                </div>
                <div>
                  <Label htmlFor="numero_odmc">Número ODMC</Label>
                  <Input id="numero_odmc" name="numero_odmc" defaultValue={empresaToEdit?.numero_odmc} />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setShowEmpresaModal(false)}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={isSavingEmpresa}>
                  {isSavingEmpresa ? "Guardando..." : "Guardar"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Modal para agregar producto manualmente */}
        <Dialog open={showAddProductModal} onOpenChange={setShowAddProductModal}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Agregar producto manualmente</DialogTitle>
              <DialogDescription>
                Introduce los datos del producto a añadir manualmente.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleAddProduct} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <Label htmlFor="codigo_producto">Código de producto</Label>
                  <Input id="codigo_producto" name="codigo_producto" value={newProduct.codigo_producto} onChange={e => setNewProduct(p => ({ ...p, codigo_producto: e.target.value }))} required />
                </div>
                <div>
                  <Label htmlFor="cantidad">Cantidad</Label>
                  <Input id="cantidad" name="cantidad" type="number" min="1" value={newProduct.cantidad} onChange={e => setNewProduct(p => ({ ...p, cantidad: e.target.value }))} required />
                </div>
                <div>
                  <Label htmlFor="numero_serie">Nº Serie</Label>
                  <Input id="numero_serie" name="numero_serie" value={newProduct.numero_serie} onChange={e => setNewProduct(p => ({ ...p, numero_serie: e.target.value }))} />
                </div>
                <div>
                  <Label htmlFor="tipo">Tipo</Label>
                  <select id="tipo" name="tipo" className="border rounded px-2 py-1 w-full" value={newProduct.tipo} onChange={e => setNewProduct(p => ({ ...p, tipo: e.target.value }))}>
                    <option value="">Seleccionar tipo</option>
                    {TIPOS_ARTICULO.map(tipo => (
                      <option key={tipo} value={tipo}>{tipo}</option>
                    ))}
                  </select>
                </div>
                <div className="col-span-2">
                  <Label htmlFor="observaciones">Observaciones</Label>
                  <Input id="observaciones" name="observaciones" value={newProduct.observaciones} onChange={e => setNewProduct(p => ({ ...p, observaciones: e.target.value }))} />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setShowAddProductModal(false)}>
                  Cancelar
                </Button>
                <Button type="submit">
                  Guardar
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Modal para duplicado de albarán */}
        <Dialog open={showDuplicadoModal} onOpenChange={setShowDuplicadoModal}>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>Albarán AC21 existente</DialogTitle>
              <DialogDescription>
                Ya existe un albarán con el número de registro "{processedData?.cabecera?.numero_registro_entrada || processedData?.cabecera?.numero_registro_salida}". 
                <br /><br />
                Esto es normal cuando diferentes páginas del mismo AC21 contienen productos distintos.
                <br /><br />
                ¿Deseas agregar los productos seleccionados de esta página al albarán existente?
                <br />
                <small className="text-gray-500">Los productos que ya están en el albarán se omitirán automáticamente.</small>
              </DialogDescription>
            </DialogHeader>
            
            {/* Mostrar resumen de productos a agregar */}
            {selectedArticulos.size > 0 && (
              <div className="mt-4 p-3 bg-gray-50 rounded">
                <h4 className="font-medium text-sm mb-2">Productos seleccionados para agregar:</h4>
                <div className="text-sm text-gray-600">
                  {Array.from(selectedArticulos).map(index => {
                    const articulo = processedData.articulos[index];
                    const yaExiste = productosYaEnAlbaran.some(
                      (prod: any) => prod.index === index
                    );
                    return (
                      <div key={index} className={`flex justify-between ${yaExiste ? 'line-through text-gray-400' : ''}`}>
                        <span>{getCodigoProducto(articulo)}</span>
                        <span>{articulo.numero_serie || 'Sin N/S'}</span>
                        {yaExiste && <span className="text-red-500 text-xs">Ya existe</span>}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
            
            <div className="flex justify-end gap-2 mt-4">
              <Button type="button" variant="outline" onClick={() => setShowDuplicadoModal(false)}>
                Cancelar
              </Button>
              <Button 
                type="button" 
                onClick={handleAgregarAExistente}
                disabled={!allSelectedHaveType()}
                title={!allSelectedHaveType() ? "Todos los artículos seleccionados deben tener un tipo asignado" : ""}
              >
                Agregar productos al albarán existente ({selectedArticulos.size} productos)
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Modal para documento existente (multipágina) */}
        {documentoExistente && (
          <DocumentoExistenteModal
            isOpen={showDocumentoExistenteModal}
            onClose={() => setShowDocumentoExistenteModal(false)}
            documentoExistente={documentoExistente}
            numeroRegistro={numeroRegistroDetectado}
            onCrearNuevaPagina={handleCrearNuevaPagina}
            onCrearDocumentoIndependiente={handleCrearDocumentoIndependiente}
          />
        )}
      </div>
    </ProtectedRoute>
  );
} 

// Añadir función utilitaria mejorada para recortar bordes blancos de un canvas
function cropWhiteBordersImproved(canvas: HTMLCanvasElement): HTMLCanvasElement {
  const ctx = canvas.getContext('2d');
  if (!ctx) return canvas;
  
  const w = canvas.width;
  const h = canvas.height;
  const imageData = ctx.getImageData(0, 0, w, h);
  const data = imageData.data;
  
  let top = 0, bottom = h, left = 0, right = w;
  
  // Buscar top - menos estricto para preservar contenido
  outer: for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const idx = (y * w + x) * 4;
      if (!isWhiteImproved(data, idx)) { 
        top = y; 
        break outer; 
      }
    }
  }
  
  // Buscar bottom
  outer: for (let y = h - 1; y >= 0; y--) {
    for (let x = 0; x < w; x++) {
      const idx = (y * w + x) * 4;
      if (!isWhiteImproved(data, idx)) { 
        bottom = y + 1; 
        break outer; 
      }
    }
  }
  
  // Buscar left
  outer: for (let x = 0; x < w; x++) {
    for (let y = top; y < bottom; y++) {
      const idx = (y * w + x) * 4;
      if (!isWhiteImproved(data, idx)) { 
        left = x; 
        break outer; 
      }
    }
  }
  
  // Buscar right
  outer: for (let x = w - 1; x >= 0; x--) {
    for (let y = top; y < bottom; y++) {
      const idx = (y * w + x) * 4;
      if (!isWhiteImproved(data, idx)) { 
        right = x + 1; 
        break outer; 
      }
    }
  }
  
  // Margen de seguridad más amplio: 25px en lugar de 10px
  // Esto preserva más contenido potencialmente importante
  const margin = 25;
  top = Math.max(0, top - margin);
  bottom = Math.min(h, bottom + margin);
  left = Math.max(0, left - margin);
  right = Math.min(w, right + margin);
  
  // Crear canvas recortado
  const croppedW = right - left;
  const croppedH = bottom - top;
  const croppedCanvas = document.createElement('canvas');
  croppedCanvas.width = croppedW;
  croppedCanvas.height = croppedH;
  const croppedCtx = croppedCanvas.getContext('2d');
  
  if (croppedCtx) {
    croppedCtx.drawImage(canvas, left, top, croppedW, croppedH, 0, 0, croppedW, croppedH);
  }
  
  return croppedCanvas;
}

function isWhiteImproved(data: Uint8ClampedArray, idx: number): boolean {
  // Criterio menos estricto para considerar un pixel como blanco
  // RGB > 240 en lugar de 220 - esto preserva más contenido de bajo contraste
  return data[idx] > 240 && data[idx+1] > 240 && data[idx+2] > 240;
}

// Añadir función utilitaria para recortar bordes blancos de un canvas
function cropWhiteBorders(canvas: HTMLCanvasElement): HTMLCanvasElement {
  const ctx = canvas.getContext('2d');
  if (!ctx) return canvas;
  const w = canvas.width;
  const h = canvas.height;
  const imageData = ctx.getImageData(0, 0, w, h);
  const data = imageData.data;
  let top = 0, bottom = h, left = 0, right = w;
  // Buscar top
  outer: for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const idx = (y * w + x) * 4;
      if (!isWhite(data, idx)) { top = y; break outer; }
    }
  }
  // Buscar bottom
  outer: for (let y = h - 1; y >= 0; y--) {
    for (let x = 0; x < w; x++) {
      const idx = (y * w + x) * 4;
      if (!isWhite(data, idx)) { bottom = y + 1; break outer; }
    }
  }
  // Buscar left
  outer: for (let x = 0; x < w; x++) {
    for (let y = top; y < bottom; y++) {
      const idx = (y * w + x) * 4;
      if (!isWhite(data, idx)) { left = x; break outer; }
    }
  }
  // Buscar right
  outer: for (let x = w - 1; x >= 0; x--) {
    for (let y = top; y < bottom; y++) {
      const idx = (y * w + x) * 4;
      if (!isWhite(data, idx)) { right = x + 1; break outer; }
    }
  }
  // Añadir margen de seguridad de 10px
  const margin = 10;
  top = Math.max(0, top - margin);
  bottom = Math.min(h, bottom + margin);
  left = Math.max(0, left - margin);
  right = Math.min(w, right + margin);
  // Crear canvas recortado
  const croppedW = right - left;
  const croppedH = bottom - top;
  const croppedCanvas = document.createElement('canvas');
  croppedCanvas.width = croppedW;
  croppedCanvas.height = croppedH;
  const croppedCtx = croppedCanvas.getContext('2d');
  if (croppedCtx) {
    croppedCtx.drawImage(canvas, left, top, croppedW, croppedH, 0, 0, croppedW, croppedH);
  }
  return croppedCanvas;
}

function isWhite(data: Uint8ClampedArray, idx: number): boolean {
  // Considera blanco si RGB > 220 (más agresivo)
  return data[idx] > 220 && data[idx+1] > 220 && data[idx+2] > 220;
}

// Export con dynamic import para evitar problemas de SSR
const UploadAC21Page = dynamic(() => Promise.resolve(UploadAC21PageContent), {
  ssr: false,
  loading: () => (
    <div className="flex justify-center items-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
        <p>Cargando sistema de procesamiento de documentos...</p>
      </div>
    </div>
  ),
});

export default UploadAC21Page;