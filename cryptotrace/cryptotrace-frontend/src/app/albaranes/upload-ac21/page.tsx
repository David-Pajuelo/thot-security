"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Upload, Building, ZoomIn, ZoomOut, MoveHorizontal, Pencil, Plus } from "lucide-react";
import ProtectedRoute from "@/components/protectedRoute";
import { processAC21Image, saveAC21Data, processAC21Companies, createEmpresa, guardarTipoProducto, apiFetch, ProductoCatalogo, fetchEmpresas, obtenerProductosDeAlbaran, verificarDocumentoExistente, crearPaginaAdicional, guardarEnLineaTemporal } from "@/lib/api";
import { toast } from "sonner";
import DocumentoExistenteModal from "@/components/albaranes/DocumentoExistenteModal";
import AC21EntradaModal from "@/components/albaranes/AC21EntradaModal";
import LineaTemporalModal from "@/components/albaranes/LineaTemporalModal";
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
        // Detectar el entorno y basePath dinámicamente desde la URL actual
        // Esto funciona tanto en desarrollo (localhost) como en producción (seguridad.idiaicox.com)
        const pathname = window.location.pathname;
        const origin = window.location.origin;
        
        // Detectar si estamos en /cryptotrace (producción) o en la raíz (desarrollo)
        const isCryptotracePath = pathname.startsWith('/cryptotrace');
        const basePath = isCryptotracePath ? '/cryptotrace' : '';
        
        // Construir la URL completa del worker
        // En desarrollo: http://localhost:3000/pdf.worker.min.js
        // En producción: https://seguridad.idiaicox.com/cryptotrace/pdf.worker.min.js
        const workerPath = `${basePath}/pdf.worker.min.js`;
        const fullWorkerUrl = `${origin}${workerPath}`;
        
        // Configurar el worker con URL absoluta
        pdfjs.GlobalWorkerOptions.workerSrc = fullWorkerUrl;
        
        console.log('📄 PDF.js worker configurado:', {
          pathname,
          origin,
          basePath,
          workerPath,
          fullWorkerUrl,
          configured: pdfjs.GlobalWorkerOptions.workerSrc
        });
        
        setPdfjsLib(pdfjs);
      }).catch((error) => {
        console.error('❌ Error cargando pdfjs-dist:', error);
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
      tipo_transaccion: {
        transferencia: true,  // Por defecto transferencia
        inventario: false,
        destruccion: false,
        recibo_en_mano: false,
        otro: false
      }
    },
          empresa_origen: {
        nombre: null,
        direccion: null,
        codigo_postal: null,
        ciudad: null,
        provincia: null,
        numero_odmc: null,
      },
      empresa_destino: {
        nombre: null,
        direccion: null,
        codigo_postal: null,
        ciudad: null,
        provincia: null,
        numero_odmc: null,
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
  const [usarRecorte, setUsarRecorte] = useState(false); // Recorte opcional para tabla de artículos
  // Estado de recorte manual (porcentaje 0..1 relativo a la imagen)
  const [cropTop, setCropTop] = useState(0.25);
  const [cropBottom, setCropBottom] = useState(0.98);
  const [cropLeft, setCropLeft] = useState(0.0); // Cambiar a 0 para cubrir desde el borde izquierdo
  const [cropRight, setCropRight] = useState(1.0); // Cambiar a 1.0 para cubrir hasta el borde derecho

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
  // Prioriza codigo_producto (TÍTULO CORTO / EDICIÓN) sobre descripcion
  // y tolera artículos nulos/indefinidos para evitar errores en mapas de selección
  const getCodigoProducto = (articulo: any) => {
    if (!articulo) {
      return '-';
    }
    return normalizaCodigo(
      articulo.codigo_producto ||
      articulo.titulo ||
      '-'
    );
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

  // Función compartida para procesar archivos (usada tanto por handleFileSelect como por onDrop)
  const processFile = async (file: File) => {
    if (!file) return;
    
    // Loguear archivo seleccionado
    console.log('[AC21] Archivo seleccionado:', file, 'Tipo:', file.type, 'Nombre:', file.name);
    
    // Detectar tipo de archivo: primero por MIME type, luego por extensión
    const isPdfByType = file.type === 'application/pdf';
    const isPdfByExtension = file.name.toLowerCase().endsWith('.pdf');
    const isPdf = isPdfByType || isPdfByExtension;
    
    // Detectar si es imagen
    const isImageByType = file.type.startsWith('image/');
    const isImageByExtension = /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(file.name);
    const isImage = isImageByType || isImageByExtension;
    
    console.log('[AC21] Detección de tipo:', { isPdfByType, isPdfByExtension, isPdf, isImageByType, isImageByExtension, isImage });
    
    // Renombrar el archivo con un timestamp para evitar caché
    const uniqueName = `${Date.now()}_${file.name}`;
    // Asegurar que el tipo MIME esté correcto si no estaba definido
    let fileType = file.type;
    if (!fileType) {
      if (isPdf) fileType = 'application/pdf';
      else if (isImage) {
        // Intentar detectar el tipo de imagen por extensión
        const ext = file.name.toLowerCase().split('.').pop();
        const imageTypes: { [key: string]: string } = {
          'jpg': 'image/jpeg',
          'jpeg': 'image/jpeg',
          'png': 'image/png',
          'gif': 'image/gif',
          'bmp': 'image/bmp',
          'webp': 'image/webp'
        };
        fileType = imageTypes[ext || ''] || 'image/jpeg';
      }
    }
    const renamedFile = new File([file], uniqueName, { type: fileType });
    
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
      },
      empresa_origen: {
        nombre: null,
        direccion: null,
        codigo_postal: null,
        ciudad: null,
        provincia: null,
        numero_odmc: null,
      },
      empresa_destino: {
        nombre: null,
        direccion: null,
        codigo_postal: null,
        ciudad: null,
        provincia: null,
        numero_odmc: null,
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
    if (isPdf) {
      console.log('📄 PDF detectado, procesando con configuración optimizada...');
      
      if (!pdfjsLib) {
        toast.error('El sistema PDF está cargando, por favor espera un momento e inténtalo de nuevo.');
        return;
      }
      
      try {
        const arrayBuffer = await file.arrayBuffer();
        const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
        
        const images: string[] = [];
        const rotArr: number[] = [];
        
        console.log(`📄 PDF cargado: ${pdf.numPages} página(s)`);
        
        for (let i = 1; i <= pdf.numPages; i++) {
          try {
            const page = await pdf.getPage(i);
            
            // CONFIGURACIÓN OPTIMIZADA: alta resolución para la dimensión MÁS CORTA
            // Primero obtenemos las dimensiones originales
            const originalViewport = page.getViewport({ scale: 1 });
            
            // Determinamos cuál es la dimensión más corta
            const shortestDimension = Math.min(originalViewport.width, originalViewport.height);
            
            // Calculamos la escala SOLO si la página es pequeña.
            // Si la dimensión corta ya es grande, no reducimos resolución para no perder nitidez.
            // Objetivo: dimensión corta ~2200px cuando sea necesario (mejor legibilidad de texto y números de serie).
            const targetShortestSize = 2200;
            const scale = shortestDimension < targetShortestSize
              ? targetShortestSize / shortestDimension
              : 1;
            
            // Aplicamos la escala calculada
            const viewport = page.getViewport({ scale: scale, rotation: -page.rotate });
            
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            
            if (!context) {
              throw new Error(`No se pudo obtener contexto 2D del canvas para la página ${i}`);
            }
            
            canvas.width = viewport.width;
            canvas.height = viewport.height;
            await page.render({ canvasContext: context, viewport }).promise;
            
            // Sin recorte - máxima preservación de contenido
            const finalCanvas = canvas;
            
            const shortestFinal = Math.min(finalCanvas.width, finalCanvas.height);
            console.log(`Página ${i}: ${finalCanvas.width}x${finalCanvas.height} px (dimensión más corta: ${shortestFinal}px, escala: ${scale.toFixed(2)}x)`);
            
            // Usar PNG (sin pérdidas) para maximizar la nitidez del texto y números de serie
            const imageDataUrl = finalCanvas.toDataURL('image/png');
            images.push(imageDataUrl);
            rotArr.push(page.rotate || 0);
          } catch (pageError) {
            console.error(`❌ Error procesando página ${i} del PDF:`, pageError);
            toast.error(`Error procesando página ${i} del PDF: ${pageError instanceof Error ? pageError.message : 'Error desconocido'}`);
            // Continuar con las siguientes páginas
          }
        }
        
        if (images.length === 0) {
          throw new Error('No se pudo convertir ninguna página del PDF a imagen');
        }
        
        console.log(`✅ ${images.length} imágenes de alta calidad generadas para OCR`);
        setPreviewImages(images);
        setRotations(rotArr);
        toast.success(`PDF convertido: ${images.length} página(s) lista(s) para procesar`);
      } catch (error) {
        console.error('❌ Error procesando PDF:', error);
        const errorMessage = error instanceof Error ? error.message : 'Error desconocido al procesar el PDF';
        toast.error(`Error al procesar PDF: ${errorMessage}`);
        // Limpiar estados en caso de error
        setPreviewImages([]);
        setRotations([]);
        setSelectedFile(null);
      }
    } else if (isImage) {
      // Imagen suelta
      const url = URL.createObjectURL(renamedFile);
      setPreviewImages([url]);
      setRotations([0]);
    } else {
      toast.error('Formato de archivo no soportado. Por favor, sube un PDF o una imagen.');
    }
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    await processFile(file);
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
            
             // Convertir canvas a blob (PNG sin pérdidas para mantener máxima calidad)
            canvas.toBlob((blob) => {
              if (blob) {
                resolve(blob);
              } else {
                reject(new Error("Error al convertir canvas a blob"));
               }
             }, 'image/png');
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
      // Enviar parámetros de recorte (porcentaje 0..1) SOLO si el usuario ha activado el recorte
      if (usarRecorte) {
        formData.append("crop_top", String(cropTop));
        formData.append("crop_bottom", String(cropBottom));
        formData.append("crop_left", String(cropLeft));
        formData.append("crop_right", String(cropRight));
      }

      console.log(`📤 [OCR] Enviando imagen con rotación ${rotation}° aplicada al servicio OCR`);
      const response = await processAC21Image(formData);

      // El OCR devuelve los datos directamente, no en formato { success, data }
      if (response) {
        // Mapeo cuidadoso de la respuesta a la estructura del estado
        // Si viene en formato { success, data }, usar response.data, sino usar response directamente
        const responseData = response.data || response;
        
        // Log de respuesta del OCR para ver qué datos extrae
        console.log('📋 [AC21] Respuesta completa del OCR:', JSON.stringify(responseData, null, 2));
        
        // Log de información de debug del backend
        if (responseData._debug) {
          console.log('🔍 [DEBUG BACKEND] Información de debug del OCR:');
          console.log('   📥 RAW OCR - Empresa Origen:', JSON.stringify(responseData._debug.empresa_origen_raw_ocr, null, 2));
          console.log('   📥 RAW OCR - Empresa Destino:', JSON.stringify(responseData._debug.empresa_destino_raw_ocr, null, 2));
          console.log('   📤 FINAL - Empresa Origen:', JSON.stringify(responseData._debug.empresa_origen_final, null, 2));
          console.log('   📤 FINAL - Empresa Destino:', JSON.stringify(responseData._debug.empresa_destino_final, null, 2));
        }
        // --- LIMPIEZA Y SINCRONIZACIÓN DE CAMPOS ---
        // Procesar tipo_transaccion: puede venir como string (nuevo formato) o como objeto (legacy)
        let tipoTransaccionObj = responseData.cabecera?.tipo_transaccion;
        if (typeof tipoTransaccionObj === 'string') {
          // Formato nuevo: convertir string a objeto con un solo true
          const tipoStr = tipoTransaccionObj.toLowerCase().trim();
          // Mapear valores posibles
          const tipoMap: { [key: string]: string } = {
            'transferencia': 'transferencia',
            'transfer': 'transferencia',
            'inventario': 'inventario',
            'inventory': 'inventario',
            'destruccion': 'destruccion',
            'destruction': 'destruccion',
            'recibo_en_mano': 'recibo_en_mano',
            'recibo': 'recibo_en_mano',
            'hand receipt': 'recibo_en_mano',
            'otro': 'otro',
            'other': 'otro'
          };
          const tipoSeleccionado = tipoMap[tipoStr] || 'transferencia'; // Por defecto transferencia
          tipoTransaccionObj = {
            transferencia: tipoSeleccionado === 'transferencia',
            inventario: tipoSeleccionado === 'inventario',
            destruccion: tipoSeleccionado === 'destruccion',
            recibo_en_mano: tipoSeleccionado === 'recibo_en_mano',
            otro: tipoSeleccionado === 'otro'
          };
        } else if (tipoTransaccionObj && typeof tipoTransaccionObj === 'object') {
          // Formato legacy: ya viene como objeto, mantenerlo
          // Asegurar que todos los campos existan
          tipoTransaccionObj = {
            transferencia: tipoTransaccionObj.transferencia || false,
            inventario: tipoTransaccionObj.inventario || false,
            destruccion: tipoTransaccionObj.destruccion || false,
            recibo_en_mano: tipoTransaccionObj.recibo_en_mano || false,
            otro: tipoTransaccionObj.otro || false
          };
        } else {
          // Si no viene o no es válido, usar transferencia por defecto
          tipoTransaccionObj = {
            transferencia: true,
            inventario: false,
            destruccion: false,
            recibo_en_mano: false,
            otro: false
          };
        }
        let tipoTransaccion = tipoTransaccionObj; // Mantener para compatibilidad con código existente
        let numeroRegistroEntrada = responseData.cabecera?.numero_registro_entrada;
        // Si el OCR devuelve 'String' literal, vacío, nulo o no existe, y hay numero_registro_salida, dejar en blanco
        if (!numeroRegistroEntrada || numeroRegistroEntrada === 'String' || numeroRegistroEntrada === tipoTransaccion) {
          if (responseData.cabecera?.numero_registro_salida) {
            numeroRegistroEntrada = '';
          }
        }
        // NO copiar tipoTransaccion a numeroRegistroEntrada bajo ninguna circunstancia
        // Función para limpiar campos: convierte null, undefined, 'String' literal y cadenas vacías a ''
        const cleanString = (val: any) => {
          if (val === 'String' || val === null || val === undefined || val === '') {
            return '';
          }
          return val;
        };
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
        // IMPORTANTE: No copiar valores de fecha_informe a fecha_transaccion ni de numero_registro_salida a numero_registro_entrada
        // Si están vacíos, deben quedarse vacíos
        const cleanCabecera = (cab: any) => {
          // numero_registro_entrada: limpieza y validación - NO debe ser una fecha
          let numRegEntrada = cleanString(numeroRegistroEntrada);
          
          // Validar que NO sea una fecha
          if (numRegEntrada) {
            const isDate = /^\d{4}-\d{2}-\d{2}$/.test(numRegEntrada) || 
                          /^\d{2}[\/\-]\d{2}[\/\-]\d{4}$/.test(numRegEntrada) ||
                          /^\d{4}\/\d{2}\/\d{2}$/.test(numRegEntrada);
            if (isDate) {
              console.warn('⚠️ [AC21] numero_registro_entrada contiene una fecha, limpiando:', numRegEntrada);
              numRegEntrada = '';
            }
          }
          
          // Función para validar si un string es una fecha válida (formato YYYY-MM-DD o DD/MM/YYYY)
          const isValidDate = (str: string): boolean => {
            if (!str || str.length < 8) return false;
            // Patrón para YYYY-MM-DD
            const pattern1 = /^\d{4}-\d{2}-\d{2}$/;
            // Patrón para DD/MM/YYYY o DD-MM-YYYY
            const pattern2 = /^\d{2}[\/\-]\d{2}[\/\-]\d{4}$/;
            return pattern1.test(str) || pattern2.test(str);
          };

          // Función para detectar si un string NO es una fecha (es un código, número ODMC, etc.)
          const isNotADate = (str: string): boolean => {
            if (!str) return false;
            const strTrimmed = str.trim();
            const strLower = strTrimmed.toLowerCase();
            
            // Si contiene "odmc" explícitamente, NO es una fecha
            if (strLower.includes('odmc')) return true;
            
            // Si es solo números y tiene menos de 8 caracteres, probablemente NO es una fecha
            if (/^\d+$/.test(strTrimmed) && strTrimmed.length < 8) return true;
            
            // Si contiene letras y números mezclados (código alfanumérico), NO es una fecha
            if (/[A-Za-z]/.test(strTrimmed) && /\d/.test(strTrimmed)) return true;
            
            // Si contiene solo números pero no tiene el formato de fecha (YYYY-MM-DD o DD/MM/YYYY), NO es una fecha
            if (/^\d+$/.test(strTrimmed) && !isValidDate(strTrimmed)) return true;
            
            // Si tiene formato de fecha pero los valores no son válidos (mes > 12, día > 31, etc.)
            if (isValidDate(strTrimmed)) {
              const match1 = strTrimmed.match(/^(\d{4})-(\d{2})-(\d{2})$/);
              const match2 = strTrimmed.match(/^(\d{2})[\/\-](\d{2})[\/\-](\d{4})$/);
              
              if (match1) {
                const [, year, month, day] = match1;
                const m = parseInt(month, 10);
                const d = parseInt(day, 10);
                if (m > 12 || d > 31 || m === 0 || d === 0) return true;
              } else if (match2) {
                const [, day, month, year] = match2;
                const m = parseInt(month, 10);
                const d = parseInt(day, 10);
                if (m > 12 || d > 31 || m === 0 || d === 0) return true;
              }
            }
            
            return false;
          };

          // Limpiar fechas - validación más estricta
          let fechaInforme = cleanString(cab?.fecha_informe);
          let fechaTransaccion = cleanString(cab?.fecha_transaccion);
          

          // Si fecha_informe existe pero NO es una fecha válida, limpiarla
          if (fechaInforme) {
            if (!isValidDate(fechaInforme) || isNotADate(fechaInforme)) {
              console.warn('⚠️ [AC21] fecha_informe no es una fecha válida, limpiando:', fechaInforme);
              fechaInforme = '';
            }
          }

          // Si fecha_transaccion existe pero NO es una fecha válida, limpiarla
          if (fechaTransaccion) {
            if (!isValidDate(fechaTransaccion) || isNotADate(fechaTransaccion)) {
              console.warn('⚠️ [AC21] fecha_transaccion no es una fecha válida, limpiando:', fechaTransaccion);
              fechaTransaccion = '';
            }
          }

          // Heurística: si el OCR ha rellenado fecha_transaccion con el MISMO valor que fecha_informe,
          // SOLO limpiar si fecha_transaccion estaba originalmente vacío en el documento.
          // Si ambas fechas son iguales PERO ambas son válidas y diferentes de fecha_informe original,
          // mantener fecha_transaccion (puede ser que realmente sean la misma fecha).
          // NOTA: Esta heurística puede ser demasiado agresiva. Si ambas fechas son iguales y válidas,
          // podría ser que realmente sean la misma fecha en el documento. Solo limpiar si parece ser un error del OCR.
          if (fechaTransaccion && fechaInforme && fechaTransaccion === fechaInforme) {
            // Solo limpiar si fecha_transaccion parece ser una copia incorrecta (mismo formato exacto)
            // Si ambas son fechas válidas y diferentes, mantenerlas
            // NO limpiar automáticamente - dejar que el usuario decida si son realmente iguales
            // fechaTransaccion = '';
          }
          
          // numero_registro_salida: limpieza y validación - NO debe ser una fecha
          let numRegSalida = cleanString(cab?.numero_registro_salida);
          
          // Validar que NO sea una fecha
          if (numRegSalida) {
            const isDate = /^\d{4}-\d{2}-\d{2}$/.test(numRegSalida) || 
                          /^\d{2}[\/\-]\d{2}[\/\-]\d{4}$/.test(numRegSalida) ||
                          /^\d{4}\/\d{2}\/\d{2}$/.test(numRegSalida);
            if (isDate) {
              console.warn('⚠️ [AC21] numero_registro_salida contiene una fecha, limpiando:', numRegSalida);
              numRegSalida = '';
            }
          }
          
          // Extraer y limpiar ODMC
          // odmc_numero ya no existe en la cabecera, se extrae de las empresas
          
          // Validación cruzada: si encontramos un número ODMC en las fechas, limpiarlo (ya no hay odmc_numero en cabecera)
          // y limpiar las fechas
          const extractODMCFromString = (str: string): string | null => {
            if (!str) return null;
            const strLower = str.toLowerCase();
            const strTrimmed = str.trim();
            
            // Si contiene "odmc" explícitamente, extraer el número (puede incluir guiones o puntos)
            if (strLower.includes('odmc')) {
              // Buscar números/códigos cerca de "odmc" (pueden incluir guiones, puntos como "02.01.06.21", o alfanuméricos)
              const match = str.match(/odmc[:\s]*([A-Za-z0-9.\-]+)/i);
              if (match && match[1]) return match[1].trim();
              // Si no hay número después, buscar antes
              const match2 = str.match(/([A-Za-z0-9.\-]+)[\s]*odmc/i);
              if (match2 && match2[1]) return match2[1].trim();
            }
            
            // Si contiene "emad" explícitamente, extraer el código completo
            // Formatos: "EMAD-004-E08", "EMAD - 004", "EMAD004", etc.
            if (strLower.includes('emad')) {
              // Formato con guiones: "EMAD-004-E08" o "EMAD - 004"
              const match1 = str.match(/([A-Za-z]+[\s\-]+\d+[\s\-]*[A-Za-z0-9]*)/i);
              if (match1 && match1[1]) {
                // Limpiar espacios alrededor de guiones
                return match1[1].replace(/\s*-\s*/g, '-').replace(/\s+/g, '').trim();
              }
              // Formato sin guiones: "EMAD004"
              const match2 = str.match(/([A-Za-z]+\d+[A-Za-z0-9]*)/i);
              if (match2 && match2[1]) return match2[1].trim();
            }
            
            // Si contiene "acct" (Account Number), extraer el código (puede incluir puntos como "02.01.06.21")
            if (strLower.includes('acct')) {
              const match = str.match(/acct[.\s]*no[:\s]*([A-Za-z0-9.\-]+)/i);
              if (match && match[1]) return match[1].trim();
            }
            
            // Si es un código con puntos (formato como "02.01.06.21", "12.34.56.78")
            if (/^\d{2}\.\d{2}\.\d{2}\.\d{2}$/.test(strTrimmed)) {
              return strTrimmed;
            }
            
            // Si es un código alfanumérico con guiones (formato ODMC típico como "EMAD-004-E08" o "EMAD - 004")
            // Limpiar espacios alrededor de guiones primero
            const cleaned = strTrimmed.replace(/\s*-\s*/g, '-').replace(/\s+/g, '');
            if (/^[A-Za-z]+-\d+-[A-Za-z0-9]+$/.test(cleaned)) {
              return cleaned;
            }
            
            // Formato más simple: "EMAD - 004" o "EMAD-004"
            if (/^[A-Za-z]+[\s\-]+\d+$/.test(strTrimmed)) {
              return cleaned;
            }
            
            // Si es solo números (formato como "000303", "123456") y no es una fecha válida
            if (/^\d{4,10}$/.test(strTrimmed) && !isValidDate(strTrimmed)) {
              return strTrimmed;
            }
            
            // Si es un código alfanumérico con o sin guiones/puntos (probablemente ODMC)
            // Acepta: "EMAD-004", "EMAD004", "ABC123", "ODMC-123", "02.01.06.21", etc.
            if (/^[A-Za-z0-9.\-]{1,20}$/.test(strTrimmed) && 
                (/\d/.test(strTrimmed) || /[A-Za-z]/.test(strTrimmed)) && 
                !isValidDate(strTrimmed)) {
              return cleaned;
            }
            
            return null;
          };
          
          // Si fecha_informe contiene ODMC, limpiar la fecha (odmc_numero ya no existe en cabecera)
          if (fechaInforme && isNotADate(fechaInforme)) {
            const odmcFromFecha = extractODMCFromString(fechaInforme);
            if (odmcFromFecha) {
              console.log('⚠️ [AC21] fecha_informe contiene ODMC, limpiando fecha:', fechaInforme);
              fechaInforme = '';
            }
          }
          
          // Si fecha_transaccion contiene ODMC, limpiar la fecha (odmc_numero ya no existe en cabecera)
          if (fechaTransaccion && isNotADate(fechaTransaccion)) {
            const odmcFromFecha = extractODMCFromString(fechaTransaccion);
            if (odmcFromFecha) {
              console.log('⚠️ [AC21] fecha_transaccion contiene ODMC, limpiando fecha:', fechaTransaccion);
              fechaTransaccion = '';
            }
          }
          
          const cabeceraResult = {
            numero_registro_salida: numRegSalida,
            fecha_transaccion: fechaTransaccion, // Mantener vacío si viene vacío (o sospechosamente copiado) del OCR
            numero_registro_entrada: numRegEntrada, // Mantener vacío si viene vacío del OCR
            fecha_informe: fechaInforme,
            tipo_transaccion: tipoTransaccionObj,
          };
          
          return cabeceraResult;
        };
        // Limpiar empresas
        const extractPostalCityProvince = (direccion: string): { codigo_postal: string, ciudad: string, provincia: string } => {
          const result = { codigo_postal: '', ciudad: '', provincia: '' };
          if (!direccion) return result;

          // Patrón 1: "28300-ARANJUEZ (MADRID)" o "28703-SAN SEBASTIAN DE LOS REYES (MADRID)"
          const pattern1 = /(\d{5})-([A-ZÁÉÍÓÚÑ\s]+)\s*\(([A-ZÁÉÍÓÚÑ\s]+)\)/i;
          const match1 = direccion.match(pattern1);
          if (match1) {
            result.codigo_postal = match1[1];
            result.ciudad = match1[2].trim();
            result.provincia = match1[3].trim();
            console.log(`✅ [EXTRACT] Patrón 1 encontrado en dirección: CP=${result.codigo_postal}, Ciudad=${result.ciudad}, Provincia=${result.provincia}`);
            return result;
          }

          // Patrón 2: "28071 – Madrid" o "28071 Madrid"
          const pattern2 = /(\d{5})\s*[–-]?\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+)/i;
          const match2 = direccion.match(pattern2);
          if (match2) {
            result.codigo_postal = match2[1];
            result.ciudad = match2[2].trim();
            // Si la ciudad es una capital común, la provincia es la misma
            const capitales = ['Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Bilbao', 'Zaragoza'];
            if (capitales.includes(result.ciudad)) {
              result.provincia = result.ciudad;
            }
            console.log(`✅ [EXTRACT] Patrón 2 encontrado en dirección: CP=${result.codigo_postal}, Ciudad=${result.ciudad}, Provincia=${result.provincia}`);
            return result;
          }

          // Buscar código postal de 5 dígitos al final
          const pattern3 = /(\d{5})\s*$/;
          const match3 = direccion.match(pattern3);
          if (match3) {
            result.codigo_postal = match3[1];
            console.log(`⚠️ [EXTRACT] Solo código postal encontrado: ${result.codigo_postal}`);
          }

          return result;
        };

        const cleanEmpresa = (emp: any) => {
          // El OCR puede devolver codigo_odmc o numero_odmc (normalizamos a numero_odmc)
          const odmc = cleanString(emp?.numero_odmc || emp?.codigo_odmc || '');
          let direccion = cleanString(emp?.direccion);
          let codigo_postal = cleanString(emp?.codigo_postal);
          let ciudad = cleanString(emp?.ciudad);
          let provincia = cleanString(emp?.provincia);

          // Si faltan campos, intentar extraerlos de la dirección
          // Intentar extraer si falta al menos uno de los campos
          if (direccion && ((!codigo_postal || codigo_postal.trim() === '') || 
                            (!ciudad || ciudad.trim() === '') || 
                            (!provincia || provincia.trim() === ''))) {
            console.log(`🔍 [CLEAN EMPRESA] Analizando dirección para extraer campos faltantes: "${direccion}"`);
            console.log(`   CP actual: "${codigo_postal}", Ciudad actual: "${ciudad}", Provincia actual: "${provincia}"`);
            
            const extracted = extractPostalCityProvince(direccion);
            
            if (extracted.codigo_postal && (!codigo_postal || codigo_postal.trim() === '')) {
              codigo_postal = extracted.codigo_postal;
              console.log(`   ✅ CP extraído: "${codigo_postal}"`);
            }
            if (extracted.ciudad && (!ciudad || ciudad.trim() === '')) {
              ciudad = extracted.ciudad;
              console.log(`   ✅ Ciudad extraída: "${ciudad}"`);
            }
            if (extracted.provincia && (!provincia || provincia.trim() === '')) {
              provincia = extracted.provincia;
              console.log(`   ✅ Provincia extraída: "${provincia}"`);
            }
          }
          
          return {
            nombre: cleanString(emp?.nombre),
            direccion: direccion,
            codigo_postal: codigo_postal,
            ciudad: ciudad,
            provincia: provincia,
            numero_odmc: odmc,
            id: emp?.id || undefined
          };
        };

        // Limpiar estado del material: convertir booleanos del OCR a valores string del frontend
        const cleanEstadoMaterial = (estado: any): string | null => {
          if (!estado || typeof estado !== 'object') return null;
          
          // El OCR devuelve: { recibido: true/false, inventariado: true/false, destruido: true/false }
          // El frontend espera: 'RECIBIDO', 'INVENTARIADO', 'DESTRUIDO' o null
          
          if (estado.destruido === true) {
            return 'DESTRUIDO';
          } else if (estado.inventariado === true) {
            return 'INVENTARIADO';
          } else if (estado.recibido === true) {
            return 'RECIBIDO';
          }
          
          return null;
        };

        // Limpiar checks de TESTIGO y OTRO: convertir booleanos del OCR
        const cleanTestigoOtro = (data: any) => {
          return {
            testigo: data?.testigo === true || false,
            otro: data?.otro === true || false,
          };
        };
        // Construir nuevo objeto de datos, asegurando que sobrescriba completamente el estado anterior
        // IMPORTANTE: Esto evita que valores previos persistan cuando el OCR devuelve campos vacíos
        const testigoOtro = cleanTestigoOtro(responseData);
        const cabeceraLimpia = cleanCabecera(responseData.cabecera || {});
        
        // Log detallado de empresas antes de limpiar
        console.log('🔍 [AC21] Empresa origen RAW del OCR:', JSON.stringify(responseData.empresa_origen, null, 2));
        console.log('🔍 [AC21] Empresa destino RAW del OCR:', JSON.stringify(responseData.empresa_destino, null, 2));
        
        // Si usarRecorte está activado, solo actualizar artículos (inventario)
        // Mantener el resto de campos (cabecera, empresas, firmas) sin cambios
        if (usarRecorte) {
          console.log('✂️ [RECORTE] Modo recorte activado: solo actualizando artículos (inventario)');
          setProcessedData((prev: any) => ({
            ...prev, // Mantener todo el estado anterior
            articulos: responseData.articulos || [], // Solo actualizar artículos
            accesorios: responseData.accesorios || [], // También actualizar accesorios y equipos
            equipos_prueba: responseData.equipos_prueba || [],
          }));
        } else {
          // Comportamiento normal: actualizar todos los campos
          const newFormData: any = {
            cabecera: cabeceraLimpia,
            empresa_origen: cleanEmpresa(responseData.empresa_origen || {}),
            empresa_destino: cleanEmpresa(responseData.empresa_destino || {}),
            articulos: responseData.articulos || [],
            accesorios: responseData.accesorios || [],
            equipos_prueba: responseData.equipos_prueba || [],
            observaciones: cleanString(responseData.observaciones),
            estado_material: cleanEstadoMaterial(responseData.estado_material),
            testigo: testigoOtro.testigo,
            otro: testigoOtro.otro,
            firmas: cleanFirmas(responseData.firmas || {
              firma_a: { nombre: null, cargo: null, empleo_rango: null },
              firma_b: { nombre: null, cargo: null, empleo_rango: null },
            }),
          };
          setProcessedData(newFormData);
        }
        
        // Intentar auto-match de empresas después de procesar el OCR
        // Esperar un tick para asegurar que las empresas están cargadas
        setTimeout(() => {
          fetchEmpresas().then((empresasList) => {
            if (empresasList.length > 0) {
              setProcessedData((prev: any) => {
                let updated = { ...prev };
                let hasChanges = false;

                // Intentar match para empresa_origen
                if (prev.empresa_origen?.nombre && !prev.empresa_origen?.id) {
                  const match = matchEmpresa(prev.empresa_origen, empresasList);
                  if (match) {
                    updated.empresa_origen = {
                      ...prev.empresa_origen,
                      ...match,
                      id: match.id
                    };
                    hasChanges = true;
                  }
                }

                // Intentar match para empresa_destino
                if (prev.empresa_destino?.nombre && !prev.empresa_destino?.id) {
                  const match = matchEmpresa(prev.empresa_destino, empresasList);
                  if (match) {
                    updated.empresa_destino = {
                      ...prev.empresa_destino,
                      ...match,
                      id: match.id
                    };
                    hasChanges = true;
                  }
                }

                if (hasChanges) {
                  console.log('🔄 [AC21] Auto-match de empresas aplicado después del OCR');
                  toast.success("Empresas encontradas y seleccionadas automáticamente");
                }

                return hasChanges ? updated : prev;
              });
            }
          });
        }, 100);
        
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
  const [showAC21EntradaModal, setShowAC21EntradaModal] = useState(false);
  const [showLineaTemporalModal, setShowLineaTemporalModal] = useState(false);

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
        setShowLineaTemporalModal(true);
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

  // Crea una línea vacía de artículo (para inserciones manuales)
  const crearLineaVacia = () => ({
    codigo_producto: '',
    titulo: '',
    descripcion: '',
    observaciones: '',
    cantidad: 1,
    numero_serie: '',
    numero_serie_inicio: '',
    numero_serie_fin: '',
    cc: '',
    tipo: '',
  });

  // Insertar una nueva línea en una posición concreta, empujando el resto hacia abajo
  const handleInsertLineaAt = (insertIndex: number) => {
    const nuevaLinea = crearLineaVacia();

    setProcessedData((prev: any) => {
      const articulosPrev = prev.articulos || [];
      const nuevosArticulos = [...articulosPrev];
      // Insertar en la posición indicada (por ejemplo, encima de la fila actual)
      nuevosArticulos.splice(insertIndex, 0, nuevaLinea);
      
      // Actualizar todos los indice_fila para que vayan en orden secuencial (1, 2, 3, ...)
      nuevosArticulos.forEach((articulo: any, index: number) => {
        articulo.indice_fila = index + 1;
      });
      
      return {
        ...prev,
        articulos: nuevosArticulos,
      };
    });

    // Actualizar selección: desplazar índices >= insertIndex y seleccionar la nueva línea
    setSelectedArticulos((prev: Set<number>) => {
      const updated = new Set<number>();
      prev.forEach(i => {
        if (i >= insertIndex) {
          updated.add(i + 1);
        } else {
          updated.add(i);
        }
      });
      updated.add(insertIndex);
      return updated;
    });

    toast.success('Nueva línea insertada');
  };

  // Agregar una nueva línea al final de la tabla
  const handleAgregarLineaAbajo = () => {
    const articulosLength = processedData.articulos?.length || 0;
    handleInsertLineaAt(articulosLength);
  };

  // Función para guardar en línea temporal y redirigir
  const handleIrALineaTemporal = async () => {
    try {
      // Validar que el número de registro de salida esté rellenado ANTES de hacer cualquier acción
      const numeroRegistroSalida = processedData.cabecera?.numero_registro_salida;
      if (!numeroRegistroSalida || numeroRegistroSalida.trim() === '') {
        toast.error("Para continuar, debes rellenar el campo 'Número de Registro de Salida' en la cabecera del documento.", { duration: 6000 });
        return; // No cerrar el modal, no hacer nada
      }
      
      // Solo cerrar el modal si la validación pasa
      setShowAC21EntradaModal(false);
      
      setIsUploading(true);

      // Filtrar productos seleccionados
      const indicesDuplicados = new Set(productosYaEnAlbaran.map((p: any) => p.index));
      const articulosAInsertar = processedData.articulos
        .filter((_: any, index: number) => selectedArticulos.has(index) && !indicesDuplicados.has(index))
        .map((art: any) => {
          // Mapeo correcto:
          // - codigo_producto viene del OCR (TÍTULO CORTO / EDICIÓN)
          // - observaciones viene del OCR (OBSERVACIONES/REMARKS)
          // - codigo_producto viene del OCR (TÍTULO CORTO/EDICIÓN)
          const codigo = art.codigo_producto || art.titulo_corto || '';
          const observaciones = art.observaciones || art.descripcion || ''; // Mantener descripcion por compatibilidad temporal
          
          // Asegurar que cantidad sea un número válido
          let cantidad = art.cantidad;
          if (cantidad === null || cantidad === undefined || cantidad === '') {
            cantidad = 1;
          } else {
            cantidad = parseInt(String(cantidad), 10) || 1;
            cantidad = Math.max(1, cantidad); // Mínimo 1
          }
          
          return {
            ...art,
            codigo_producto: codigo, // TÍTULO CORTO / EDICIÓN
            observaciones: observaciones, // OBSERVACIONES/REMARKS del OCR (se mapeará a descripcion en BD)
            cantidad: cantidad, // Asegurar que cantidad sea un número válido
            numero_serie_inicio: art.numero_serie_inicio || art.numero_serie || '', // Preservar números de serie
            numero_serie_fin: art.numero_serie_fin || art.numero_serie || '',
            tipo: articulosTipos[processedData.articulos.findIndex((originalArt: any) => originalArt === art)] || art.tipo,
          };
        });

      if (articulosAInsertar.length === 0) {
        toast.info("No hay productos nuevos para guardar.");
        setIsUploading(false);
        return;
      }

      // Construir el payload para guardar en línea temporal
      const payload = {
        ...processedData,
        articulos: articulosAInsertar,
        // Incluir accesorios y equipos de prueba
        accesorios: processedData.accesorios || [],
        equipos_prueba: processedData.equipos_prueba || [],
      };

      console.log("[AC21] Guardando en línea temporal:", JSON.stringify(payload, null, 2));

      const result = await guardarEnLineaTemporal(payload, imagenParaGuardar || undefined);

      if (result && result.message) {
        toast.success(result.message || "Productos guardados en línea temporal");
        setShowLineaTemporalModal(true);
      } else {
        toast.error("Error al guardar en línea temporal");
      }
    } catch (error: any) {
      console.error("Error guardando en línea temporal:", error);
      toast.error(error.message || "Error al guardar en línea temporal", { duration: 5000 });
    } finally {
      setIsUploading(false);
    }
  };

  // Función con la lógica original de confirmación (sin verificación de documento existente)
  const handleConfirmContinuado = async () => {
    try {
      // Validar que el número de registro de salida esté rellenado ANTES de hacer cualquier acción
      const numeroRegistroSalida = processedData.cabecera?.numero_registro_salida;
      if (!numeroRegistroSalida || numeroRegistroSalida.trim() === '') {
        toast.error("Para continuar, debes rellenar el campo 'Número de Registro de Salida' en la cabecera del documento.", { duration: 6000 });
        setIsUploading(false);
        return; // No procesar, no abrir nada
      }
      
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
        tipo_documento: (() => {
          const tipo = processedData.cabecera?.tipo_transaccion;
          if (!tipo) return '';
          if (typeof tipo === 'string') return tipo; // Legacy format
          // Convertir objeto a string: obtener el primer tipo marcado
          const tipos = [];
          if (tipo.transferencia) tipos.push('TRANSFERENCIA');
          if (tipo.inventario) tipos.push('INVENTARIO');
          if (tipo.destruccion) tipos.push('DESTRUCCION');
          if (tipo.recibo_en_mano) tipos.push('RECIBO EN MANO');
          if (tipo.otro) tipos.push('OTRO');
          return tipos.join(', ') || '';
        })(),
        direccion_transferencia: "ENTRADA", // Forzar ENTRADA para este flujo de AC21
        articulos: articulosAInsertar,
        // Incluir accesorios y equipos de prueba
        accesorios: processedData.accesorios || [],
        equipos_prueba: processedData.equipos_prueba || [],
      };
      
      console.log("[AC21] Payload enviado a guardarEnLineaTemporal:", JSON.stringify(payload, null, 2));

      // Para AC21s de ENTRADA, usar el flujo de línea temporal en lugar de crear albarán directamente
      const result = await guardarEnLineaTemporal(payload, imagenParaGuardar || undefined);

      // El backend devuelve success: true cuando se crean líneas temporales correctamente
      if (result && result.success !== false && result.message) {
        // Éxito: mostrar mensaje y redirigir
        toast.success(result.message || "Productos guardados en línea temporal");
        setIsUploading(false);
        setShowLineaTemporalModal(true);
        return;
      }
      
      if (!result || result.success === false) {
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
          
          // Para modo 'agregar_a_existente', usar saveAC21Data (el backend lo maneja directamente)
          const resultExistente = await saveAC21Data(payloadExistente, imagenParaGuardar || undefined);
          
          if (!resultExistente.success) {
            toast.error(resultExistente.message || "Error al agregar productos al albarán existente", { duration: 5000 });
            setIsUploading(false);
            return;
          }
          
          toast.success(`${productosNuevos.length} producto(s) agregado(s) a la línea temporal para catalogación`);
          setIsUploading(false);
          setShowLineaTemporalModal(true);
          return;
        } else {
          toast.error(result.message || "Error al procesar el AC21", { duration: 5000 });
        }
        setIsUploading(false);
        return;
      }
      
    } catch (error: any) {
      console.error("Error en handleConfirmContinuado:", error);
      toast.error(error.message || "Error inesperado al procesar el AC21", { duration: 5000 });
      setIsUploading(false);
    }
  };

  const handleConfirm = async () => {
    // Verificar primero si hay artículos procesados
    if (!processedData || !processedData.articulos || processedData.articulos.length === 0) {
      toast.error("No hay artículos para procesar. Asegúrate de que el OCR haya detectado artículos en el documento.");
      return;
    }
    
    // Verificar si hay artículos seleccionados
    if (!selectedArticulos || selectedArticulos.size === 0) {
      toast.error(
        "No hay artículos seleccionados para procesar. " +
        "Selecciona al menos un artículo de la lista o usa 'Seleccionar todos'.",
        { duration: 5000 }
      );
      return;
    }

    // Verificar que hay productos válidos para procesar
    const productosSeleccionados = Array.from(selectedArticulos);
    const productosValidos = productosSeleccionados.filter(index => {
      const articulo = processedData.articulos[index];
      return articulo && (articulo.codigo_producto || articulo.observaciones);
    });

    if (productosValidos.length === 0) {
      toast.error("No hay productos válidos seleccionados para procesar");
      return;
    }

    try {
      setIsUploading(true);

      // 1. VALIDACIÓN CRÍTICA: Verificar que al menos uno de los números de registro esté presente
      const numeroRegistroSalida = processedData.cabecera?.numero_registro_salida;
      const numeroRegistroEntrada = processedData.cabecera?.numero_registro_entrada;
      const tieneNumeroRegistroSalida = numeroRegistroSalida && numeroRegistroSalida.trim() !== '';
      const tieneNumeroRegistroEntrada = numeroRegistroEntrada && numeroRegistroEntrada.trim() !== '';
      
      if (!tieneNumeroRegistroSalida && !tieneNumeroRegistroEntrada) {
        toast.error(
          "Debes introducir al menos un número de registro: 'Número de Registro de Salida' o 'Número de Registro de Entrada' en la cabecera del documento.",
          { duration: 7000 }
        );
        setIsUploading(false);
        return; // Cancelar todo el proceso
      }

      // 2. Verificar si es un AC21 de ENTRADA que requiere tipificación (ANTES de verificar documento existente)
      const tipoDocumento = (() => {
        const tipo = processedData.cabecera?.tipo_transaccion;
        if (!tipo) return '';
        if (typeof tipo === 'string') return tipo; // Legacy format
        // Convertir objeto a string: obtener el primer tipo marcado
        const tipos = [];
        if (tipo.transferencia) tipos.push('TRANSFERENCIA');
        if (tipo.inventario) tipos.push('INVENTARIO');
        if (tipo.destruccion) tipos.push('DESTRUCCION');
        if (tipo.recibo_en_mano) tipos.push('RECIBO EN MANO');
        if (tipo.otro) tipos.push('OTRO');
        return tipos.join(', ') || '';
      })();
      const tipoDocumentoUpper = tipoDocumento.toUpperCase();
      const esAC21Entrada = tipoDocumentoUpper && 
        ['TRANSFERENCIA', 'RECIBO_MANO', 'DESTRUCCION', 'OTRO'].includes(tipoDocumentoUpper);
      
      if (esAC21Entrada) {
        // Validar que el número de registro de salida esté rellenado ANTES de abrir el modal
        if (!tieneNumeroRegistroSalida) {
          toast.error("Para continuar, debes rellenar el campo 'Número de Registro de Salida' en la cabecera del documento.", { duration: 6000 });
          setIsUploading(false);
          return; // No abrir el modal, mostrar error
        }
        
        console.log('📋 [AC21] AC21 de ENTRADA detectado, requiere tipificación');
        setShowAC21EntradaModal(true);
        setIsUploading(false);
        return; // Detener el proceso para mostrar el modal
      }

      // 3. Verificar si existe un documento con el mismo número de registro (DESPUÉS de detectar AC21 de ENTRADA)
      const numeroRegistro = numeroRegistroEntrada || numeroRegistroSalida;
      
      if (numeroRegistro) {
        console.log('🔍 [AC21] Verificando documento existente con número:', numeroRegistro);
        const verificacion = await verificarDocumentoExistente(numeroRegistro);
        
        // Verificar que verificacion no sea null y tenga la propiedad existe
        if (verificacion && verificacion.existe && verificacion.documento) {
          console.log('📄 [AC21] Documento existente encontrado:', verificacion.documento);
          setDocumentoExistente(verificacion.documento);
          setNumeroRegistroDetectado(numeroRegistro);
          setShowDocumentoExistenteModal(true);
          setIsUploading(false);
          return; // Detener el proceso para mostrar el modal
        }
      }

      // Si no es AC21 de ENTRADA y no hay documento existente, continuar con el flujo normal
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
      
      // Para modo 'agregar_a_existente', usar saveAC21Data (el backend lo maneja directamente)
      const result = await saveAC21Data(payload, imagenParaGuardar || undefined);
      
      if (!result.success) {
        toast.error(result.message || "Error al agregar productos al albarán existente", { duration: 5000 });
        return;
      }
      
      toast.success(`${productosValidos.length} producto(s) agregado(s) a la línea temporal para catalogación`);
      setShowLineaTemporalModal(true);
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
      // Validar que todos los campos requeridos estén presentes
      const requiredFields = ['nombre', 'direccion', 'ciudad', 'codigo_postal', 'provincia'];
      const missingFields = requiredFields.filter(field => !formData[field] || formData[field].trim() === '');
      
      if (missingFields.length > 0) {
        toast.error(`Faltan campos requeridos: ${missingFields.join(', ')}`);
        return;
      }
      
      // Filtrar solo los campos que acepta el backend y limpiar valores
      const empresaData: any = {
        nombre: (formData.nombre || '').trim(),
        direccion: (formData.direccion || '').trim(),
        ciudad: (formData.ciudad || '').trim(),
        codigo_postal: (formData.codigo_postal || '').trim(),
        provincia: (formData.provincia || '').trim(),
        activa: true
      };
      // Solo incluir numero_odmc si existe y no está vacío
      if (formData.numero_odmc && formData.numero_odmc.trim() !== '') {
        empresaData.numero_odmc = formData.numero_odmc.trim();
      }
      console.log('📤 Enviando datos de empresa:', empresaData);
      const nuevaEmpresa = await createEmpresa(empresaData);

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
      
      // Recargar la lista de empresas para que aparezca en el desplegable
      const empresasActualizadas = await fetchEmpresas();
      setEmpresas(empresasActualizadas);
    } catch (error: any) {
      console.error("Error creando empresa:", error);
      console.error("Error data:", error.data);
      const errorMessage = error.data ? JSON.stringify(error.data, null, 2) : error.message;
      toast.error(errorMessage || "Error al crear la empresa");
    } finally {
      setIsSavingEmpresa(false);
    }
  };

  // Función para parsear y separar una dirección completa en sus componentes
  const parseDireccion = (direccionCompleta: string, ocrData: any) => {
    if (!direccionCompleta) return { direccion: '', codigo_postal: '', ciudad: '', provincia: '' };

    let direccion = direccionCompleta.trim();
    let codigo_postal = ocrData?.codigo_postal || '';
    let ciudad = ocrData?.ciudad || '';
    let provincia = ocrData?.provincia || '';

    // Si ya tenemos código postal, ciudad y provincia separados, usarlos
    if (codigo_postal && ciudad && provincia) {
      return { direccion, codigo_postal, ciudad, provincia };
    }

    // Patrón para código postal español (5 dígitos)
    const codigoPostalPattern = /\b(\d{5})\b/g;
    const codigoPostalMatch = direccion.match(codigoPostalPattern);
    
    if (codigoPostalMatch && !codigo_postal) {
      // Tomar el último código postal encontrado (por si hay varios)
      codigo_postal = codigoPostalMatch[codigoPostalMatch.length - 1];
      // Eliminar el código postal de la dirección
      direccion = direccion.replace(new RegExp(`\\b${codigo_postal}\\b`, 'g'), '').trim();
    }

    // Intentar extraer ciudad y provincia
    // Patrones comunes: "Ciudad, Provincia" o "Ciudad Provincia" o "Ciudad (Provincia)"
    const ciudadProvinciaPatterns = [
      /([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]+?)\s*,\s*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]+?)(?:\s|$)/, // "Ciudad, Provincia"
      /([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]+?)\s*\(([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]+?)\)/, // "Ciudad (Provincia)"
      /([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,})\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,})(?:\s|$)/, // "Ciudad Provincia"
    ];

    // Si no tenemos ciudad y provincia, intentar extraerlas de la dirección
    if (!ciudad || !provincia) {
      for (const pattern of ciudadProvinciaPatterns) {
        const match = direccion.match(pattern);
        if (match && match[1] && match[2]) {
          const posibleCiudad = match[1].trim();
          const posibleProvincia = match[2].trim();
          
          // Validar que no sean parte de la dirección (calle, número, etc.)
          const palabrasDireccion = ['calle', 'avenida', 'plaza', 'paseo', 'carretera', 'km', 'número', 'nº', 'n°', 'cp', 'código'];
          const esParteDireccion = palabrasDireccion.some(palabra => 
            posibleCiudad.toLowerCase().includes(palabra) || posibleProvincia.toLowerCase().includes(palabra)
          );

          if (!esParteDireccion && posibleCiudad.length > 2 && posibleProvincia.length > 2) {
            if (!ciudad) ciudad = posibleCiudad;
            if (!provincia) provincia = posibleProvincia;
            // Eliminar ciudad y provincia de la dirección
            direccion = direccion.replace(pattern, '').trim();
            break;
          }
        }
      }
    }

    // Si aún no tenemos ciudad/provincia, intentar extraer la última palabra como provincia
    // y la penúltima como ciudad (patrón común en direcciones españolas)
    if (!ciudad || !provincia) {
      const partes = direccion.split(/\s+/).filter(p => p.length > 0);
      if (partes.length >= 2) {
        const ultimaParte = partes[partes.length - 1];
        const penultimaParte = partes[partes.length - 2];
        
        // Si la última parte parece una provincia (palabra capitalizada, no es número, no es código postal)
        if (!provincia && /^[A-ZÁÉÍÓÚÑ]/.test(ultimaParte) && !/^\d+$/.test(ultimaParte) && ultimaParte.length > 2) {
          provincia = ultimaParte;
          direccion = direccion.replace(new RegExp(`\\b${ultimaParte}\\b$`, 'i'), '').trim();
        }
        
        // Si la penúltima parte parece una ciudad
        if (!ciudad && /^[A-ZÁÉÍÓÚÑ]/.test(penultimaParte) && !/^\d+$/.test(penultimaParte) && penultimaParte.length > 2) {
          ciudad = penultimaParte;
          direccion = direccion.replace(new RegExp(`\\b${penultimaParte}\\b$`, 'i'), '').trim();
        }
      }
    }

    // Limpiar la dirección de comas y espacios múltiples
    direccion = direccion.replace(/,\s*,/g, ',').replace(/\s+/g, ' ').replace(/^,\s*|\s*,$/g, '').trim();

    return {
      direccion: direccion || ocrData?.direccion || '',
      codigo_postal: codigo_postal || ocrData?.codigo_postal || '',
      ciudad: ciudad || ocrData?.ciudad || '',
      provincia: provincia || ocrData?.provincia || '',
    };
  };

  const handleOpenEmpresaModal = (empresa: any, tipo: 'origen' | 'destino') => {
    // Si se pasa un objeto vacío, usar los datos del OCR si están disponibles
    if (!empresa || Object.keys(empresa).length === 0) {
      const ocrData = tipo === 'origen' ? processedData.empresa_origen : processedData.empresa_destino;
      if (ocrData) {
        // Si la dirección viene completa pero faltan campos separados, intentar parsearla
        const direccionCompleta = ocrData.direccion || '';
        const tieneDireccionCompleta = direccionCompleta && direccionCompleta.length > 10;
        const faltanCampos = !ocrData.codigo_postal || !ocrData.ciudad || !ocrData.provincia;
        
        let direccionParsed = { direccion: direccionCompleta, codigo_postal: '', ciudad: '', provincia: '' };
        
        if (tieneDireccionCompleta && faltanCampos) {
          console.log('🔍 [AC21] Parseando dirección completa:', direccionCompleta);
          direccionParsed = parseDireccion(direccionCompleta, ocrData);
          console.log('✅ [AC21] Dirección parseada:', direccionParsed);
        }

        // Mapear los datos del OCR al formato del formulario
        empresa = {
          nombre: ocrData.nombre || '',
          direccion: direccionParsed.direccion || ocrData.direccion || '',
          codigo_postal: direccionParsed.codigo_postal || ocrData.codigo_postal || '',
          ciudad: direccionParsed.ciudad || ocrData.ciudad || '',
          provincia: direccionParsed.provincia || ocrData.provincia || '',
          numero_odmc: ocrData.numero_odmc || ocrData.codigo_odmc || '',
        };
      }
    }
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
  const handleEstadoMaterialChange = (estado: string | null) => {
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

  // Función para normalizar nombres de empresas para comparación
  const normalizeCompanyName = (name: string): string => {
    if (!name) return '';
    return name
      .toLowerCase()
      .trim()
      .replace(/\s+/g, ' ') // Normalizar espacios múltiples a uno solo
      .replace(/[.,\-_]/g, '') // Eliminar puntuación común
      .normalize('NFD') // Normalizar caracteres acentuados
      .replace(/[\u0300-\u036f]/g, ''); // Eliminar diacríticos
  };

  // Función para hacer match de empresa del OCR con empresas existentes
  const matchEmpresa = (ocrEmpresa: any, empresasList: any[]): any | null => {
    if (!ocrEmpresa?.nombre || empresasList.length === 0) return null;

    const ocrNombreNormalizado = normalizeCompanyName(ocrEmpresa.nombre);
    
    // Buscar match exacto por nombre normalizado
    const matchExacto = empresasList.find(emp => {
      const empNombreNormalizado = normalizeCompanyName(emp.nombre);
      return empNombreNormalizado === ocrNombreNormalizado;
    });

    if (matchExacto) {
      console.log(`✅ [AC21] Match encontrado para empresa "${ocrEmpresa.nombre}" → "${matchExacto.nombre}" (ID: ${matchExacto.id})`);
      return matchExacto;
    }

    // Si no hay match exacto, intentar match parcial (el nombre del OCR contiene el de la BD o viceversa)
    const matchParcial = empresasList.find(emp => {
      const empNombreNormalizado = normalizeCompanyName(emp.nombre);
      return ocrNombreNormalizado.includes(empNombreNormalizado) || 
             empNombreNormalizado.includes(ocrNombreNormalizado);
    });

    if (matchParcial) {
      console.log(`✅ [AC21] Match parcial encontrado para empresa "${ocrEmpresa.nombre}" → "${matchParcial.nombre}" (ID: ${matchParcial.id})`);
      return matchParcial;
    }

    return null;
  };

  // Auto-match de empresas cuando se procesan datos del OCR o se cargan empresas
  useEffect(() => {
    if (empresas.length === 0) return; // Esperar a que se carguen las empresas

    setProcessedData((prev: any) => {
      let updated = { ...prev };
      let hasChanges = false;

      // Intentar match para empresa_origen
      if (prev.empresa_origen?.nombre && !prev.empresa_origen?.id) {
        const match = matchEmpresa(prev.empresa_origen, empresas);
        if (match) {
          updated.empresa_origen = {
            ...prev.empresa_origen,
            ...match, // Incluir todos los datos de la empresa encontrada
            id: match.id
          };
          hasChanges = true;
        }
      }

      // Intentar match para empresa_destino
      if (prev.empresa_destino?.nombre && !prev.empresa_destino?.id) {
        const match = matchEmpresa(prev.empresa_destino, empresas);
        if (match) {
          updated.empresa_destino = {
            ...prev.empresa_destino,
            ...match, // Incluir todos los datos de la empresa encontrada
            id: match.id
          };
          hasChanges = true;
        }
      }

      if (hasChanges) {
        console.log('🔄 [AC21] Auto-match de empresas aplicado');
      }

      return hasChanges ? updated : prev;
    });
  }, [empresas, processedData.empresa_origen?.nombre, processedData.empresa_destino?.nombre]);

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

  // Calcular información sobre índices de fila detectados y filas faltantes
  const filaIndices: number[] = (processedData?.articulos || []).map(
    (art: any, idx: number) =>
      (typeof art?.indice_fila === 'number' && !Number.isNaN(art.indice_fila))
        ? art.indice_fila
        : idx + 1
  );

  const maxFilaIndex = filaIndices.length > 0 ? Math.max(...filaIndices) : 0;
  const filasPresentes = new Set(filaIndices);
  const filasFaltantes: number[] = [];
  for (let i = 1; i <= maxFilaIndex; i++) {
    if (!filasPresentes.has(i)) {
      filasFaltantes.push(i);
    }
  }

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
  // Solo selecciona si no hay artículos ya seleccionados (para evitar sobrescribir selecciones manuales)
  useEffect(() => {
    if (processedData.articulos && processedData.articulos.length > 0) {
      // Solo seleccionar automáticamente si no hay artículos seleccionados previamente
      // o si el número de artículos cambió (nuevo procesamiento)
      setSelectedArticulos(prev => {
        // Si no hay selección previa o el tamaño cambió, seleccionar todos
        if (prev.size === 0 || prev.size !== processedData.articulos.length) {
          return new Set(processedData.articulos.map((_: any, idx: number) => idx));
        }
        // Mantener la selección actual
        return prev;
      });
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
            
            // Si después de deseleccionar duplicados no quedan artículos seleccionados,
            // mostrar un mensaje más claro
            if (newSet.size === 0 && processedData.articulos && processedData.articulos.length > 0) {
              console.warn('⚠️ [AC21] Todos los artículos son duplicados');
              toast.warning(
                `Todos los artículos de este AC21 ya están en el albarán ${response.albaran_numero}. ` +
                `Puedes seleccionarlos manualmente si deseas agregarlos de nuevo.`,
                { duration: 5000 }
              );
            }
            
            return newSet;
          });
          
          if (duplicados.length > 0) {
            console.log('🔍 [AC21] Se encontraron productos duplicados, mostrando indicadores visuales');
            const mensaje = duplicados.length === processedData.articulos?.length
              ? `Todos los ${duplicados.length} producto(s) ya están en el albarán ${response.albaran_numero}`
              : `Se encontraron ${duplicados.length} producto(s) que ya están en el albarán ${response.albaran_numero}`;
            toast.info(mensaje, { duration: 5000 });
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
       
        // Descargar imagen rotada (PNG sin pérdidas para depuración)
        const rotatedDataUrl = canvas.toDataURL('image/png');
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
                    onDrop={async e => {
                      e.preventDefault();
                      setIsDragging(false);
                      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                        await processFile(e.dataTransfer.files[0]);
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
               <div className="mt-4 bg-gray-50 rounded-lg min-h-[300px] flex flex-col items-stretch justify-start">
                {previewImages.length > 0 ? (
                   // Barra de controles, paginador y recorte
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
                       {/* Controles de zoom, rotación y recorte */}
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
                     {/* Controles sencillos de recorte vertical (solo afectan a la extracción de tabla) */}
                     <div className="mt-2 flex flex-col gap-1 text-xs text-gray-700 bg-white/70 rounded px-2 py-1 border border-gray-200">
                       <div className="flex items-center justify-between">
                         <span className="font-semibold">Zona de tabla para OCR (recorte vertical)</span>
                         <label className="flex items-center gap-1 text-[11px] cursor-pointer">
                           <input
                             type="checkbox"
                             className="cursor-pointer"
                             checked={usarRecorte}
                             onChange={(e) => setUsarRecorte(e.target.checked)}
                           />
                           <span>Aplicar recorte</span>
                         </label>
                       </div>
                       <div className="flex items-center gap-2">
                         <span>Arriba</span>
                         <input
                           type="range"
                           min={0}
                           max={80}
                           value={Math.round(cropTop * 100)}
                           onChange={(e) => {
                             const val = Number(e.target.value) / 100;
                             // Mantener al menos un 5% de separación con bottom
                             const safeVal = Math.min(val, cropBottom - 0.05);
                             setCropTop(safeVal);
                           }}
                           className="flex-1"
                           disabled={!usarRecorte}
                         />
                         <span>{Math.round(cropTop * 100)}%</span>
                       </div>
                       <div className="flex items-center gap-2">
                         <span>Abajo</span>
                         <input
                           type="range"
                           min={20}
                           max={100}
                           value={Math.round(cropBottom * 100)}
                           onChange={(e) => {
                             const val = Number(e.target.value) / 100;
                             const safeVal = Math.max(val, cropTop + 0.05);
                             setCropBottom(safeVal);
                           }}
                           className="flex-1"
                           disabled={!usarRecorte}
                         />
                         <span>{Math.round(cropBottom * 100)}%</span>
                       </div>
                       <span className="text-[10px] text-gray-500">
                         Estos controles no afectan a la imagen mostrada, solo a qué parte se usa para leer la tabla de inventario. Si no marcas "Aplicar recorte", se usará la página completa.
                       </span>
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
                              <div 
                                className="relative" 
                                style={{ display: 'inline-block' }}
                                ref={(el) => {
                                  // Asegurar que el contenedor tenga el tamaño de la imagen
                                  if (el) {
                                    const img = el.querySelector('img');
                                    if (img && img.complete && img.naturalWidth > 0) {
                                      // Esperar un frame para que el layout se estabilice
                                      requestAnimationFrame(() => {
                                        el.style.width = `${img.offsetWidth}px`;
                                        el.style.height = `${img.offsetHeight}px`;
                                      });
                                    }
                                  }
                                }}
                              >
                                <img
                                  src={previewImages[currentPage]}
                                  alt={`Preview ${currentPage + 1}`}
                                  className="max-w-full max-h-full object-contain"
                                  style={{ transform: `rotate(${rotations[currentPage] || 0}deg)`, display: 'block' }}
                                  onLoad={(e) => {
                                    // Asegurar que el contenedor tenga exactamente el tamaño de la imagen
                                    const img = e.currentTarget;
                                    const container = img.parentElement;
                                    if (container && img.offsetWidth > 0 && img.offsetHeight > 0) {
                                      // El contenedor debe tener el tamaño exacto de la imagen para que el recuadro se posicione correctamente
                                      requestAnimationFrame(() => {
                                        container.style.width = `${img.offsetWidth}px`;
                                        container.style.height = `${img.offsetHeight}px`;
                                      });
                                    }
                                  }}
                                />
                                {/* Recuadro visual de recorte (dentro del TransformComponent para que se mueva con la imagen) */}
                                {usarRecorte && (
                                  <div
                                    className="pointer-events-none absolute border-2 border-red-500/80 bg-red-500/10"
                                    style={{
                                      // Posicionar el recuadro respecto a la imagen usando porcentajes
                                      // El contenedor tiene el tamaño exacto de la imagen
                                      top: `${cropTop * 100}%`,
                                      left: `${cropLeft * 100}%`,
                                      width: `${(cropRight - cropLeft) * 100}%`,
                                      height: `${(cropBottom - cropTop) * 100}%`,
                                      boxSizing: 'border-box',
                                    }}
                                  />
                                )}
                              </div>
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
                          {[
                            { key: 'transferencia', label: 'TRANSFERENCIA' },
                            { key: 'inventario', label: 'INVENTARIO' },
                            { key: 'destruccion', label: 'DESTRUCCION' },
                            { key: 'recibo_en_mano', label: 'RECIBO EN MANO' },
                            { key: 'otro', label: 'OTRO' }
                          ].map(tipo => (
                            <label key={tipo.key} className="inline-flex items-center text-base font-semibold gap-2">
                              <input
                                type="radio"
                                name="tipoTransaccion"
                                value={tipo.key}
                                checked={processedData.cabecera?.tipo_transaccion?.[tipo.key] || false}
                                onChange={() => setProcessedData((prev: any) => ({
                                  ...prev,
                                  cabecera: {
                                    ...prev.cabecera,
                                    tipo_transaccion: {
                                      transferencia: tipo.key === 'transferencia',
                                      inventario: tipo.key === 'inventario',
                                      destruccion: tipo.key === 'destruccion',
                                      recibo_en_mano: tipo.key === 'recibo_en_mano',
                                      otro: tipo.key === 'otro'
                                    }
                                  }
                                }))}
                                className="form-radio w-4 h-4 text-blue-600 border-2 border-gray-400"
                              />
                              <span>{tipo.label}</span>
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
                                        empresa_origen: { 
                                          ...empresaSeleccionada,
                                          numero_odmc: empresaSeleccionada.numero_odmc || ''
                                        }
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
                                        empresa_destino: { 
                                          ...empresaSeleccionada,
                                          numero_odmc: empresaSeleccionada.numero_odmc || ''
                                        }
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
                          <Button
                            variant="default"
                            size="sm"
                            className="bg-green-600 hover:bg-green-700 text-white"
                            onClick={async () => {
                              const empresaData = processedData.empresa_origen;
                              if (!empresaData) return;
                              
                              try {
                                setIsSavingEmpresa(true);
                                const requiredFields = ['nombre', 'direccion', 'ciudad', 'codigo_postal', 'provincia'];
                                const missingFields = requiredFields.filter(field => !empresaData[field] || empresaData[field].trim() === '');
                                
                                if (missingFields.length > 0) {
                                  toast.error(`Faltan campos requeridos: ${missingFields.join(', ')}`);
                                  return;
                                }
                                
                                const dataToSave: any = {
                                  nombre: (empresaData.nombre || '').trim(),
                                  direccion: (empresaData.direccion || '').trim(),
                                  ciudad: (empresaData.ciudad || '').trim(),
                                  codigo_postal: (empresaData.codigo_postal || '').trim(),
                                  provincia: (empresaData.provincia || '').trim(),
                                  activa: true
                                };
                                
                                // Incluir numero_odmc si existe
                                if (empresaData.numero_odmc && empresaData.numero_odmc.trim() !== '') {
                                  dataToSave.numero_odmc = empresaData.numero_odmc.trim();
                                }
                                
                                const nuevaEmpresa = await createEmpresa(dataToSave);
                                setProcessedData((prev: any) => ({
                                  ...prev,
                                  empresa_origen: { ...nuevaEmpresa, es_nueva: false }
                                }));
                                setNewCompaniesCount(prev => Math.max(0, prev - 1));
                                toast.success("Empresa guardada correctamente");
                                const empresasActualizadas = await fetchEmpresas();
                                setEmpresas(empresasActualizadas);
                              } catch (error: any) {
                                console.error("Error guardando empresa:", error);
                                toast.error(error.message || "Error al guardar la empresa");
                              } finally {
                                setIsSavingEmpresa(false);
                              }
                            }}
                            disabled={isSavingEmpresa}
                          >
                            {isSavingEmpresa ? 'Guardando...' : 'Guardar'}
                          </Button>
                        </div>
                        <div className="space-y-2">
                          <div>
                            <Label className="text-xs font-semibold text-gray-700">Número ODMC:</Label>
                            <Input
                              className="text-sm h-8"
                              value={processedData.empresa_origen?.numero_odmc || ''}
                              onChange={e => setProcessedData((prev: any) => ({
                                ...prev,
                                empresa_origen: { ...prev.empresa_origen, numero_odmc: e.target.value }
                              }))}
                            />
                          </div>
                          <div>
                            <Label className="text-xs font-semibold text-gray-700">Nombre:</Label>
                            <Input
                              className="text-sm h-8"
                              value={processedData.empresa_origen?.nombre || ''}
                              onChange={e => setProcessedData((prev: any) => ({
                                ...prev,
                                empresa_origen: { ...prev.empresa_origen, nombre: e.target.value }
                              }))}
                            />
                          </div>
                          <div>
                            <Label className="text-xs font-semibold text-gray-700">Dirección:</Label>
                            <Input
                              className="text-sm h-8"
                              value={processedData.empresa_origen?.direccion || ''}
                              onChange={e => setProcessedData((prev: any) => ({
                                ...prev,
                                empresa_origen: { ...prev.empresa_origen, direccion: e.target.value }
                              }))}
                            />
                          </div>
                          <div>
                            <Label className="text-xs font-semibold text-gray-700">Código Postal:</Label>
                            <Input
                              className="text-sm h-8"
                              value={processedData.empresa_origen?.codigo_postal || ''}
                              onChange={e => setProcessedData((prev: any) => ({
                                ...prev,
                                empresa_origen: { ...prev.empresa_origen, codigo_postal: e.target.value }
                              }))}
                            />
                          </div>
                          <div>
                            <Label className="text-xs font-semibold text-gray-700">Ciudad:</Label>
                            <Input
                              className="text-sm h-8"
                              value={processedData.empresa_origen?.ciudad || ''}
                              onChange={e => setProcessedData((prev: any) => ({
                                ...prev,
                                empresa_origen: { ...prev.empresa_origen, ciudad: e.target.value }
                              }))}
                            />
                          </div>
                          <div>
                            <Label className="text-xs font-semibold text-gray-700">Provincia:</Label>
                            <Input
                              className="text-sm h-8"
                              value={processedData.empresa_origen?.provincia || ''}
                              onChange={e => setProcessedData((prev: any) => ({
                                ...prev,
                                empresa_origen: { ...prev.empresa_origen, provincia: e.target.value }
                              }))}
                            />
                          </div>
                        </div>
                      </div>

                      {/* Empresa Destino */}
                      <div className="bg-white p-3 rounded-md shadow-sm">
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="text-sm font-medium text-gray-600">Para:</h4>
                          <Button
                            variant="default"
                            size="sm"
                            className="bg-green-600 hover:bg-green-700 text-white"
                            onClick={async () => {
                              const empresaData = processedData.empresa_destino;
                              if (!empresaData) return;
                              
                              try {
                                setIsSavingEmpresa(true);
                                const requiredFields = ['nombre', 'direccion', 'ciudad', 'codigo_postal', 'provincia'];
                                const missingFields = requiredFields.filter(field => !empresaData[field] || empresaData[field].trim() === '');
                                
                                if (missingFields.length > 0) {
                                  toast.error(`Faltan campos requeridos: ${missingFields.join(', ')}`);
                                  return;
                                }
                                
                                const dataToSave: any = {
                                  nombre: (empresaData.nombre || '').trim(),
                                  direccion: (empresaData.direccion || '').trim(),
                                  ciudad: (empresaData.ciudad || '').trim(),
                                  codigo_postal: (empresaData.codigo_postal || '').trim(),
                                  provincia: (empresaData.provincia || '').trim(),
                                  activa: true
                                };
                                
                                // Incluir numero_odmc si existe
                                if (empresaData.numero_odmc && empresaData.numero_odmc.trim() !== '') {
                                  dataToSave.numero_odmc = empresaData.numero_odmc.trim();
                                }
                                
                                const nuevaEmpresa = await createEmpresa(dataToSave);
                                setProcessedData((prev: any) => ({
                                  ...prev,
                                  empresa_destino: { ...nuevaEmpresa, es_nueva: false }
                                }));
                                setNewCompaniesCount(prev => Math.max(0, prev - 1));
                                toast.success("Empresa guardada correctamente");
                                const empresasActualizadas = await fetchEmpresas();
                                setEmpresas(empresasActualizadas);
                              } catch (error: any) {
                                console.error("Error guardando empresa:", error);
                                toast.error(error.message || "Error al guardar la empresa");
                              } finally {
                                setIsSavingEmpresa(false);
                              }
                            }}
                            disabled={isSavingEmpresa}
                          >
                            {isSavingEmpresa ? 'Guardando...' : 'Guardar'}
                          </Button>
                        </div>
                        <div className="space-y-2">
                          <div>
                            <Label className="text-xs font-semibold text-gray-700">Número ODMC:</Label>
                            <Input
                              className="text-sm h-8"
                              value={processedData.empresa_destino?.numero_odmc || ''}
                              onChange={e => setProcessedData((prev: any) => ({
                                ...prev,
                                empresa_destino: { ...prev.empresa_destino, numero_odmc: e.target.value }
                              }))}
                            />
                          </div>
                          <div>
                            <Label className="text-xs font-semibold text-gray-700">Nombre:</Label>
                            <Input
                              className="text-sm h-8"
                              value={processedData.empresa_destino?.nombre || ''}
                              onChange={e => setProcessedData((prev: any) => ({
                                ...prev,
                                empresa_destino: { ...prev.empresa_destino, nombre: e.target.value }
                              }))}
                            />
                          </div>
                          <div>
                            <Label className="text-xs font-semibold text-gray-700">Dirección:</Label>
                            <Input
                              className="text-sm h-8"
                              value={processedData.empresa_destino?.direccion || ''}
                              onChange={e => setProcessedData((prev: any) => ({
                                ...prev,
                                empresa_destino: { ...prev.empresa_destino, direccion: e.target.value }
                              }))}
                            />
                          </div>
                          <div>
                            <Label className="text-xs font-semibold text-gray-700">Código Postal:</Label>
                            <Input
                              className="text-sm h-8"
                              value={processedData.empresa_destino?.codigo_postal || ''}
                              onChange={e => setProcessedData((prev: any) => ({
                                ...prev,
                                empresa_destino: { ...prev.empresa_destino, codigo_postal: e.target.value }
                              }))}
                            />
                          </div>
                          <div>
                            <Label className="text-xs font-semibold text-gray-700">Ciudad:</Label>
                            <Input
                              className="text-sm h-8"
                              value={processedData.empresa_destino?.ciudad || ''}
                              onChange={e => setProcessedData((prev: any) => ({
                                ...prev,
                                empresa_destino: { ...prev.empresa_destino, ciudad: e.target.value }
                              }))}
                            />
                          </div>
                          <div>
                            <Label className="text-xs font-semibold text-gray-700">Provincia:</Label>
                            <Input
                              className="text-sm h-8"
                              value={processedData.empresa_destino?.provincia || ''}
                              onChange={e => setProcessedData((prev: any) => ({
                                ...prev,
                                empresa_destino: { ...prev.empresa_destino, provincia: e.target.value }
                              }))}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </div>

               {/* Tabla de artículos pegada al bloque superior */}
               <div>
                 {/* Aviso si faltan filas según los índices detectados por el OCR */}
                 {filasFaltantes.length > 0 && (
                   <div className="mb-2 text-xs text-yellow-900 bg-yellow-50 border border-yellow-200 rounded px-2 py-1">
                     Faltan filas en la tabla del AC21:{" "}
                     <span className="font-semibold">
                       {filasFaltantes.join(", ")}
                     </span>
                     . Revisa que no se haya omitido ninguna línea del documento original.
                   </div>
                 )}
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
                         const rowNumber = (typeof articulo?.indice_fila === 'number' && !Number.isNaN(articulo.indice_fila))
                           ? articulo.indice_fila
                           : index + 1;
                        return (
                          <tr
                            key={index}
                            className={`group ${yaExiste ? 'bg-gray-100 opacity-70' : (index % 2 === 0 ? 'bg-white' : 'bg-gray-50')}`}
                          >
                            {/* Numeración + botón de inserción de línea */}
                             <td className="border border-gray-400 px-2 py-1 text-center align-middle font-semibold relative">
                              {/* Botón flotante para insertar una línea encima de la actual */}
                              <button
                                type="button"
                                onClick={() => handleInsertLineaAt(index)}
                                className="absolute -left-3 top-1/2 -translate-y-1/2 h-4 w-4 rounded-full border border-gray-400 bg-white text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                                title="Insertar línea encima"
                               >
                                 +
                               </button>
                               {rowNumber}
                            </td>
                            {/* Título corto/edición (codigo_producto) */}
                            <td className="border border-gray-400 px-2 py-1">
                              <input
                                type="text"
                                className="w-full border-none bg-transparent focus:ring-0 text-xs"
                                value={articulo.codigo_producto || articulo.titulo || getCodigoProducto(articulo) || ''}
                                onChange={e => {
                                  const nuevos = [...processedData.articulos];
                                  nuevos[index].codigo_producto = e.target.value;
                                  nuevos[index].titulo = e.target.value; // Mantener compatibilidad
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
                                value={articulo.cc || ''}
                                onChange={e => {
                                  const nuevos = [...processedData.articulos];
                                  nuevos[index].cc = e.target.value;
                                  setProcessedData((prev: any) => ({ ...prev, articulos: nuevos }));
                                }}
                                disabled={yaExiste}
                                placeholder="-"
                              />
                            </td>
                            {/* Observaciones */}
                            <td className="border border-gray-400 px-2 py-1">
                              <input
                                type="text"
                                className="w-full border-none bg-transparent focus:ring-0 text-xs"
                                value={articulo.observaciones || articulo.descripcion || ''}
                                onChange={e => {
                                  const nuevos = [...processedData.articulos];
                                  nuevos[index].observaciones = e.target.value; // Se mapeará a descripcion en BD
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
                {/* Botón para añadir una línea nueva al final de la tabla */}
                <div className="mt-2 flex justify-end">
                  <Button
                    type="button"
                    onClick={handleAgregarLineaAbajo}
                    variant="outline"
                    size="sm"
                    className="text-xs"
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    Añadir línea
                  </Button>
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
                {/* Fila 1: El material ha sido (checkboxes) */}
                <div className="grid grid-cols-1 md:grid-cols-4 items-center gap-x-4 gap-y-2 mb-4">
                  <div className="md:col-span-1 text-sm font-semibold text-gray-700">
                    14. EL MATERIAL HA SIDO:
                  </div>
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={processedData.estado_material === 'RECIBIDO'} 
                      onChange={(e) => {
                        if (e.target.checked) {
                          handleEstadoMaterialChange('RECIBIDO');
                        } else {
                          handleEstadoMaterialChange(null);
                        }
                      }} 
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    RECIBIDO
                  </label>
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={processedData.estado_material === 'INVENTARIADO'} 
                      onChange={(e) => {
                        if (e.target.checked) {
                          handleEstadoMaterialChange('INVENTARIADO');
                        } else {
                          handleEstadoMaterialChange(null);
                        }
                      }} 
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    INVENTARIADO
                  </label>
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={processedData.estado_material === 'DESTRUIDO'} 
                      onChange={(e) => {
                        if (e.target.checked) {
                          handleEstadoMaterialChange('DESTRUIDO');
                        } else {
                          handleEstadoMaterialChange(null);
                        }
                      }} 
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
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
                    const articulo = processedData.articulos?.[index];
                    if (!articulo) {
                      // Si por cualquier motivo el índice está desfasado, no renderizamos nada para evitar errores
                      return null;
                    }
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

        {/* Modal para AC21 de ENTRADA que requiere tipificación */}
        <AC21EntradaModal
          isOpen={showAC21EntradaModal}
          onClose={() => setShowAC21EntradaModal(false)}
          onIrALineaTemporal={handleIrALineaTemporal}
        />

        {/* Modal para Línea Temporal */}
        <LineaTemporalModal
          isOpen={showLineaTemporalModal}
          onClose={() => setShowLineaTemporalModal(false)}
        />
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