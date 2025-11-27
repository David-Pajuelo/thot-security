"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from "@/components/ui/button";
import { fetchEmpresas, fetchProductos, fetchInventario, apiFetch, obtenerSiguienteNumeroRegistroSalida } from "@/lib/api";
import { Empresa, Producto } from "@/lib/types";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import EmpresaForm from "@/components/empresas/EmpresaForm";
import { Send } from "lucide-react";

// Definición de tipo para una línea de producto
interface LineaProductoAC21 {
  producto: string;
  cantidad: number;
  numeroSerie: string[];
  inputSerie: string;
  observaciones: string;
  paginaOrigen?: number; // Para trackear de qué página viene el producto
  paginaId?: number; // ID de la página origen
}

function CrearAC21SalidaFormPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [empresaOrigen, setEmpresaOrigen] = useState("");
  const [empresaDestino, setEmpresaDestino] = useState("");
  const [tipoTransaccion, setTipoTransaccion] = useState("");
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [sugerenciasOrigen, setSugerenciasOrigen] = useState<Empresa[]>([]);
  const [sugerenciasDestino, setSugerenciasDestino] = useState<Empresa[]>([]);
  const [lineas, setLineas] = useState<LineaProductoAC21[]>([
    { producto: "", cantidad: 1, numeroSerie: [], inputSerie: "", observaciones: "" }
  ]);
  const [productosCatalogo, setProductosCatalogo] = useState<Producto[]>([]);
  const [sugerenciasProducto, setSugerenciasProducto] = useState<{codigo: string}[][]>([]);
  const [inventario, setInventario] = useState<any[]>([]);
  const [sugerenciasSerie, setSugerenciasSerie] = useState<string[][]>([]);
  const tiposTransaccion = [
    "Transferencia",
    "Inventario",
    "Destrucción",
    "Recibo en Mano",
    "Otro"
  ];

  // Añade un array de refs para los inputs de número de serie
  const inputSerieRefs = useRef<(HTMLInputElement | null)[]>([]);
  const [dropdownDirection, setDropdownDirection] = useState<string[]>([]);
  // Añade estado para controlar la visibilidad del dropdown por línea
  const [dropdownVisible, setDropdownVisible] = useState<boolean[]>(lineas.map(() => false));
  const [productoDropdownVisible, setProductoDropdownVisible] = useState<boolean[]>(lineas.map(() => false));
  const [showEmpresaModal, setShowEmpresaModal] = useState(false);
  const [empresaModalTipo, setEmpresaModalTipo] = useState<'origen' | 'destino' | null>(null);

  // Nuevos estados para los campos del formulario
  const [fechaInforme, setFechaInforme] = useState("");
  const [numeroRegistroSalida, setNumeroRegistroSalida] = useState("");
  const [fechaTransaccionDMA, setFechaTransaccionDMA] = useState("");
  const [numeroRegistroEntrada, setNumeroRegistroEntrada] = useState("");
  
  const [materialHaSido, setMaterialHaSido] = useState(""); // Para radios: RECIBIDO, INVENTARIADO, DESTRUIDO
  const [destinatarioAutorizadoTestigo, setDestinatarioAutorizadoTestigo] = useState(false);
  const [destinatarioAutorizadoOtro, setDestinatarioAutorizadoOtro] = useState(false);
  const [destinatarioAutorizadoOtroTexto, setDestinatarioAutorizadoOtroTexto] = useState("");

  const [firmaEntregaNombre, setFirmaEntregaNombre] = useState("");
  const [firmaEntregaCargo, setFirmaEntregaCargo] = useState("");
  const [firmaEntregaEmpleo, setFirmaEntregaEmpleo] = useState("");
  const [firmaEntregaFirma, setFirmaEntregaFirma] = useState(""); // O la representación de la firma

  const [firmaRecibeNombre, setFirmaRecibeNombre] = useState("");
  const [firmaRecibeCargo, setFirmaRecibeCargo] = useState("");
  const [firmaRecibeEmpleo, setFirmaRecibeEmpleo] = useState("");
  const [firmaRecibeFirma, setFirmaRecibeFirma] = useState("");

  const [observacionesODMC, setObservacionesODMC] = useState("");

  // Estados para accesorios y equipos de prueba
  const [accesorios, setAccesorios] = useState<any[]>([]);
  const [equiposPrueba, setEquiposPrueba] = useState<any[]>([]);

  // Estados para el envío
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Estados para tracking multipágina
  const [esOrigenMultipagina, setEsOrigenMultipagina] = useState(false);
  const [totalPaginasOrigen, setTotalPaginasOrigen] = useState(1);
  const [estructuraPaginas, setEstructuraPaginas] = useState<{[pagina: number]: LineaProductoAC21[]}>({});

  // Función para cargar datos de un AC21 de entrada
  const cargarDatosAC21Entrada = async (albaranId: string) => {
    try {
      const response = await apiFetch(`/albaranes/${albaranId}/`);
      const albaran = response;
      
      console.log('📥 Cargando datos del AC21 de entrada:', albaran);
      
      // Verificar si es un documento multipágina
      let todasLasPaginas = [albaran];
      let esMultipagina = false;
      
      if (albaran.total_paginas > 1) {
        console.log('📄 Documento multipágina detectado, cargando todas las páginas...');
        esMultipagina = true;
        
        // Obtener el documento principal si estamos en una página secundaria
        let documentoPrincipalId = albaran.documento_principal || albaran.id;
        
        // Cargar todas las páginas del documento
        try {
          const paginasResponse = await apiFetch(`/albaranes/${documentoPrincipalId}/paginas/`);
          todasLasPaginas = paginasResponse;
          console.log('📄 Todas las páginas cargadas:', todasLasPaginas);
        } catch (error) {
          console.error('❌ Error cargando páginas del documento:', error);
          // Fallback: usar solo la página actual
          todasLasPaginas = [albaran];
        }
      }
      
      // Usar la primera página para datos generales (empresas, fechas, etc.)
      const paginaPrincipal = todasLasPaginas[0];
      
      // Invertir origen y destino para la salida
      if (paginaPrincipal.empresa_destino_info) {
        setEmpresaOrigen(paginaPrincipal.empresa_destino_info.nombre);
      }
      if (paginaPrincipal.empresa_origen_info) {
        setEmpresaDestino(paginaPrincipal.empresa_origen_info.nombre);
      }
      
      // Prellenar algunos campos relacionados
      setTipoTransaccion("Transferencia"); // Por defecto para salidas
      
      // Cargar productos de TODAS las páginas del AC21 de entrada
      let todosLosMovimientos: any[] = [];
      
      for (const pagina of todasLasPaginas) {
        try {
          const movimientosResponse = await apiFetch(`/albaranes/${pagina.id}/movimientos/`);
          console.log(`📦 Movimientos de página ${pagina.pagina_numero}:`, movimientosResponse);
      
      if (movimientosResponse && movimientosResponse.length > 0) {
            // Marcar a qué página pertenece cada movimiento para mantener la estructura
            const movimientosConPagina = movimientosResponse.map((mov: any) => ({
              ...mov,
              pagina_origen: pagina.pagina_numero,
              pagina_id: pagina.id
            }));
            todosLosMovimientos = [...todosLosMovimientos, ...movimientosConPagina];
          }
        } catch (error) {
          console.error(`❌ Error cargando movimientos de página ${pagina.id}:`, error);
        }
      }
      
      console.log('📦 Todos los movimientos combinados:', todosLosMovimientos);
      
      // Definir lineasMapeadas fuera del if para que esté disponible en toda la función
      let lineasMapeadas: LineaProductoAC21[] = [];
      
      if (todosLosMovimientos.length > 0) {
        lineasMapeadas = todosLosMovimientos.map((mov: any): LineaProductoAC21 => {
          // Usar los campos correctos del serializer
          const codigoProducto = mov.producto_codigo || '';
          const numeroSerie = mov.numero_serie || '';
          const observaciones = mov.observaciones || '';
          
          return {
            producto: codigoProducto,
            cantidad: 1,
            numeroSerie: numeroSerie ? [numeroSerie] : [],
            inputSerie: "",
            observaciones: observaciones,
            paginaOrigen: mov.pagina_origen,
            paginaId: mov.pagina_id
          };
        });
        
        const lineasPrellenadas = lineasMapeadas.filter(linea => linea.producto); // Filtrar líneas sin producto
        
        if (lineasPrellenadas.length > 0) {
          setLineas(lineasPrellenadas);
        }
      }
      
      // Cargar accesorios (de la página principal)
      try {
        const accesoriosData = typeof paginaPrincipal.accesorios === 'string' 
          ? JSON.parse(paginaPrincipal.accesorios) 
          : paginaPrincipal.accesorios;
        
        if (Array.isArray(accesoriosData) && accesoriosData.length > 0) {
          setAccesorios(accesoriosData);
        }
      } catch (error) {
        console.log('ℹ️ No se pudieron cargar accesorios:', error);
      }
      
      // Cargar equipos de prueba (de la página principal)
      try {
        const equiposData = typeof paginaPrincipal.equipos_prueba === 'string' 
          ? JSON.parse(paginaPrincipal.equipos_prueba) 
          : paginaPrincipal.equipos_prueba;
        
        if (Array.isArray(equiposData) && equiposData.length > 0) {
          setEquiposPrueba(equiposData);
        }
      } catch (error) {
        console.log('ℹ️ No se pudieron cargar equipos de prueba:', error);
      }
      
      // Cargar checkboxes y observaciones (de la página principal)
      if (typeof paginaPrincipal.destinatario_autorizado_testigo === 'boolean') {
        setDestinatarioAutorizadoTestigo(paginaPrincipal.destinatario_autorizado_testigo);
      } else if (typeof paginaPrincipal.requiere_testigo === 'boolean') {
        setDestinatarioAutorizadoTestigo(paginaPrincipal.requiere_testigo === true);
      }
      
      if (typeof paginaPrincipal.destinatario_autorizado_otro === 'boolean') {
        setDestinatarioAutorizadoOtro(paginaPrincipal.destinatario_autorizado_otro);
      } else if (typeof paginaPrincipal.requiere_testigo === 'boolean') {
        setDestinatarioAutorizadoOtro(paginaPrincipal.requiere_testigo === false);
      }
      
      if (paginaPrincipal.destinatario_autorizado_otro_especificar) {
        setDestinatarioAutorizadoOtroTexto(paginaPrincipal.destinatario_autorizado_otro_especificar);
      }
      
      if (paginaPrincipal.observaciones_odmc) {
        setObservacionesODMC(paginaPrincipal.observaciones_odmc);
      }
      
      if (paginaPrincipal.estado_material && ['RECIBIDO', 'INVENTARIADO', 'DESTRUIDO'].includes(paginaPrincipal.estado_material)) {
        setMaterialHaSido(paginaPrincipal.estado_material);
      }
      
      // Mostrar información sobre la estructura multipágina
      if (esMultipagina) {
        console.log(`📄 AC21 multipágina detectado: ${todasLasPaginas.length} páginas, ${todosLosMovimientos.length} productos totales`);
        
        // Configurar estados multipágina
        setEsOrigenMultipagina(true);
        setTotalPaginasOrigen(todasLasPaginas.length);
        
        // Organizar productos por página para mantener la estructura
        const estructuraPorPagina: {[pagina: number]: LineaProductoAC21[]} = {};
        
        console.log('📄 DEBUG: lineasMapeadas antes de organizar:', lineasMapeadas);
        
        lineasMapeadas.forEach(linea => {
          const pagina = linea.paginaOrigen || 1;
          console.log(`📄 DEBUG: Producto "${linea.producto}" asignado a página ${pagina}`);
          if (!estructuraPorPagina[pagina]) {
            estructuraPorPagina[pagina] = [];
          }
          estructuraPorPagina[pagina].push(linea);
        });
        
        setEstructuraPaginas(estructuraPorPagina);
        console.log('📄 Estructura de páginas organizada:', estructuraPorPagina);
        console.log('📄 Número de páginas con productos:', Object.keys(estructuraPorPagina).length);
      } else {
        // Documento de página única
        setEsOrigenMultipagina(false);
        setTotalPaginasOrigen(1);
        setEstructuraPaginas({});
      }
      
    } catch (error) {
      console.error('❌ Error cargando datos del AC21 de entrada:', error);
      // No mostrar error, simplemente no prellenar
    }
  };

  // Cargar empresas y recuperar selección previa
  useEffect(() => {
    fetchEmpresas().then(setEmpresas);
    
    // Prellenar fechas con la fecha actual (siempre)
    const fechaActual = new Date().toISOString().split('T')[0]; // Formato YYYY-MM-DD
    setFechaInforme(fechaActual);
    setFechaTransaccionDMA(fechaActual);
    
    // Generar automáticamente el siguiente número de registro de salida
    const cargarSiguienteNumero = async () => {
      try {
        const siguienteNumero = await obtenerSiguienteNumeroRegistroSalida();
        setNumeroRegistroSalida(siguienteNumero);
      } catch (error) {
        console.error('❌ Error obteniendo siguiente número de registro:', error);
        // Fallback: generar uno básico basado en la fecha
        const año = new Date().getFullYear();
        setNumeroRegistroSalida(`S${año}-0001`);
      }
    };
    cargarSiguienteNumero();
    
    // Si hay parámetro 'from', cargar datos del AC21 de entrada
    const fromAlbaranId = searchParams.get('from');
    if (fromAlbaranId) {
      cargarDatosAC21Entrada(fromAlbaranId);
    } else {
      // Si hay parámetro 'productos', precargar productos seleccionados del inventario
      const productosParam = searchParams.get('productos');
      if (productosParam) {
        const ids = productosParam.split(',').map(id => id.trim()).filter(Boolean);
        if (ids.length > 0) {
          // Obtener inventario y filtrar por los IDs seleccionados
          fetchInventario().then(inventarioData => {
            const productosSeleccionados = inventarioData.filter((item: any) => ids.includes(item.id.toString()));
            if (productosSeleccionados.length > 0) {
              const nuevasLineas = productosSeleccionados.map((item: any) => ({
                producto: item.codigo_producto,
                cantidad: 1,
                numeroSerie: item.numero_serie ? [item.numero_serie] : [],
                inputSerie: "",
                observaciones: item.descripcion || ""
              }));
              setLineas(nuevasLineas);
            }
          });
        }
      } else {
        // Solo usar localStorage si no hay parámetro 'from' ni 'productos'
        const lastOrigen = localStorage.getItem("ac21_empresa_origen");
        const lastDestino = localStorage.getItem("ac21_empresa_destino");
        if (lastOrigen) setEmpresaOrigen(lastOrigen);
        if (lastDestino) setEmpresaDestino(lastDestino);
      }
    }
  }, [searchParams]);

  // Guardar selección en localStorage
  useEffect(() => {
    if (empresaOrigen) localStorage.setItem("ac21_empresa_origen", empresaOrigen);
  }, [empresaOrigen]);
  useEffect(() => {
    if (empresaDestino) localStorage.setItem("ac21_empresa_destino", empresaDestino);
  }, [empresaDestino]);

  // Filtrar sugerencias
  useEffect(() => {
    setSugerenciasOrigen(
      empresaOrigen.length > 0
        ? empresas.filter(e => e.nombre.toLowerCase().includes(empresaOrigen.toLowerCase()))
        : []
    );
  }, [empresaOrigen, empresas]);
  useEffect(() => {
    setSugerenciasDestino(
      empresaDestino.length > 0
        ? empresas.filter(e => e.nombre.toLowerCase().includes(empresaDestino.toLowerCase()))
        : []
    );
  }, [empresaDestino, empresas]);

  // Cargar productos catálogo
  useEffect(() => {
    fetchProductos().then(setProductosCatalogo);
  }, []);

  // Autocompletado por línea
  useEffect(() => {
    const nuevasSugerencias = lineas.map((linea, i) => {
      const userInput = linea.producto.trim().toLowerCase();
      if (userInput.length > 0) {
        // Filtrar si hay texto, comparando solo con codigo_producto
        return productosCatalogo
          .filter(p =>
            p.codigo_producto.toLowerCase().includes(userInput)
          )
          .map(p => ({ codigo: p.codigo_producto })); // Mapear solo el código
      } else if (productoDropdownVisible[i]) {
        // Si no hay texto PERO el dropdown está visible, mostrar todos los códigos
        return productosCatalogo.map(p => ({ codigo: p.codigo_producto })); // Mapear solo el código
      }
      // Si no hay texto y el dropdown no está visible, no mostrar sugerencias
      return [];
    });
    setSugerenciasProducto(nuevasSugerencias);
  }, [lineas, productosCatalogo, productoDropdownVisible]);

  // Cargar inventario
  useEffect(() => {
    fetchInventario().then(setInventario);
  }, []);

  // Autocompletado de número de serie por línea
  useEffect(() => {
    // 1. Recolectar todos los números de serie ya utilizados en CUALQUIER línea de este AC21.
    const todosLosNumerosDeSerieGlobalmenteUsados = new Set<string>();
    lineas.forEach(l => {
      l.numeroSerie.forEach(serie => todosLosNumerosDeSerieGlobalmenteUsados.add(serie));
    });

    setSugerenciasSerie(
      lineas.map(linea =>
        linea.producto.length > 0
          ? inventario
              .filter(item =>
                item.codigo_producto === linea.producto &&
                item.estado === "activo" &&
                item.numero_serie && // Asegurarse que el item de inventario tiene un numero_serie
                // Condición 1: No debe estar ya seleccionado como chip en la línea actual
                !linea.numeroSerie.includes(item.numero_serie) &&
                // Condición 2: No debe estar seleccionado en NINGUNA línea de este AC21.
                !todosLosNumerosDeSerieGlobalmenteUsados.has(item.numero_serie) &&
                item.numero_serie.toLowerCase().includes((linea.inputSerie || "").toLowerCase())
              )
              .map(item => item.numero_serie)
          : []
      )
    );
  }, [lineas, inventario]);

  // Efecto para calcular la dirección del dropdown en cada línea
  useEffect(() => {
    setDropdownDirection(
      lineas.map((_, idx) => {
        const ref = inputSerieRefs.current[idx];
        if (!ref) return "down";
        const rect = ref.getBoundingClientRect();
        const spaceBelow = window.innerHeight - rect.bottom;
        const spaceAbove = rect.top;
        // Si hay menos de 250px abajo y más arriba, abre hacia arriba
        if (spaceBelow < 250 && spaceAbove > spaceBelow) return "up";
        return "down";
      })
    );
  }, [lineas, sugerenciasSerie]);

  // Actualiza el estado cuando cambian las líneas
  useEffect(() => {
    setDropdownVisible(lineas.map(() => false));
    setProductoDropdownVisible(lineas.map(() => false));
  }, [lineas.length]);

  const handleLineaChange = (idx: number, field: string, value: string | number) => {
    setLineas(prev => prev.map((l, i) => i === idx ? { ...l, [field]: value } : l));
  };
  const handleSelectProducto = (idx: number, codigo: string) => {
    setLineas(prev => prev.map((l, i) => i === idx ? { ...l, producto: codigo } : l));
  };
  const handleAddLinea = () => {
    setLineas(prev => [...prev, { producto: "", cantidad: 1, numeroSerie: [], inputSerie: "", observaciones: "" }]);
  };
  const handleRemoveLinea = (idx: number) => {
    setLineas(prev => prev.filter((_, i) => i !== idx));
    setSugerenciasProducto(prev => prev.filter((_, i) => i !== idx));
  };
  const handleInputSerieChange = (idx: number, value: string) => {
    setLineas(prev => prev.map((l, i) => i === idx ? { ...l, inputSerie: value } : l));
  };
  const handleAddSerie = (idx: number, serie: string) => {
    setLineas(prev => prev.map((l, i) =>
      i === idx
        ? {
            ...l,
            numeroSerie: [...l.numeroSerie, serie],
            inputSerie: "",
            cantidad: l.numeroSerie.length + 1
          }
        : l
    ));
    setSugerenciasSerie(prev => prev.map((s, i) => i === idx ? [] : s));
  };
  const handleRemoveSerie = (idx: number, serie: string) => {
    setLineas(prev => prev.map((l, i) =>
      i === idx
        ? {
            ...l,
            numeroSerie: l.numeroSerie.filter(s => s !== serie),
            cantidad: l.numeroSerie.length - 1 > 0 ? l.numeroSerie.length - 1 : 1
          }
        : l
    ));
  };

  // Funciones para manejar accesorios
  const handleAddAccesorio = () => {
    setAccesorios(prev => [...prev, { descripcion: '', cantidad: 1 }]);
  };

  const handleRemoveAccesorio = (index: number) => {
    setAccesorios(prev => prev.filter((_, i) => i !== index));
  };

  const handleAccesorioChange = (index: number, field: 'descripcion' | 'cantidad', value: string | number) => {
    setAccesorios(prev => prev.map((acc, i) => 
      i === index ? { ...acc, [field]: value } : acc
    ));
  };

  // Funciones para manejar equipos de prueba
  const handleAddEquipoPrueba = () => {
    setEquiposPrueba(prev => [...prev, { codigo: '', comentario: '' }]);
  };

  const handleRemoveEquipoPrueba = (index: number) => {
    setEquiposPrueba(prev => prev.filter((_, i) => i !== index));
  };

  const handleEquipoPruebaChange = (index: number, field: 'codigo' | 'comentario', value: string) => {
    setEquiposPrueba(prev => prev.map((equipo, i) => 
      i === index ? { ...equipo, [field]: value } : equipo
    ));
  };

  const puedeAvanzar = lineas.some(l => l.producto && l.cantidad > 0) && empresaOrigen && empresaDestino && tipoTransaccion &&
                       fechaInforme && numeroRegistroSalida && fechaTransaccionDMA;

  // Función para abrir el modal y saber si es para origen o destino
  const handleOpenEmpresaModal = (tipo: 'origen' | 'destino') => {
    setEmpresaModalTipo(tipo);
    setShowEmpresaModal(true);
  };

  // Función para refrescar empresas y seleccionar la nueva
  const handleEmpresaCreada = async () => {
    setShowEmpresaModal(false);
    // Refrescar empresas
    const nuevasEmpresas = await fetchEmpresas();
    setEmpresas(nuevasEmpresas);
    // Seleccionar la última empresa añadida (por nombre, asumiendo que es la última alfabéticamente)
    const ultima = nuevasEmpresas[nuevasEmpresas.length - 1];
    if (empresaModalTipo === 'origen') setEmpresaOrigen(ultima.nombre);
    if (empresaModalTipo === 'destino') setEmpresaDestino(ultima.nombre);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!puedeAvanzar) {
      const camposFaltantes = [];
      if (!lineas.some(l => l.producto && l.cantidad > 0)) camposFaltantes.push("al menos una línea de producto completa");
      if (!empresaOrigen) camposFaltantes.push("empresa de origen");
      if (!empresaDestino) camposFaltantes.push("empresa de destino");
      if (!tipoTransaccion) camposFaltantes.push("tipo de transacción");
      if (!fechaInforme) camposFaltantes.push("fecha del informe");
      if (!numeroRegistroSalida) camposFaltantes.push("Nº de registro de salida");
      if (!fechaTransaccionDMA) camposFaltantes.push("fecha de la transacción");

      setSubmitError(`Por favor, completa los siguientes campos obligatorios: ${camposFaltantes.join(', ')}.`);
      return;
    }
    setIsSubmitting(true);
    setSubmitError(null);

    const empresaOrigenSeleccionada = empresas.find(e => e.nombre === empresaOrigen);
    const empresaDestinoSeleccionada = empresas.find(e => e.nombre === empresaDestino);

    let tipoDocumentoBackend = tipoTransaccion.toUpperCase();
    if (tipoTransaccion === "Recibo en Mano") {
      tipoDocumentoBackend = "RECIBO_MANO";
    }

    // Datos comunes para todas las páginas
    const datosComunes = {
      fecha: new Date().toISOString(),
      numero_registro_salida: numeroRegistroSalida,
      fecha_informe: fechaInforme,
      fecha_transaccion: fechaTransaccionDMA,
      numero_registro_entrada: numeroRegistroEntrada || "",
      empresa_origen: empresaOrigenSeleccionada ? empresaOrigenSeleccionada.id : null,
      empresa_destino: empresaDestinoSeleccionada ? empresaDestinoSeleccionada.id : null,
      tipo_documento: tipoDocumentoBackend,
      direccion_transferencia: "SALIDA",
      accesorios: accesorios,
      equipos_prueba: equiposPrueba,
      destinatario_autorizado_testigo: destinatarioAutorizadoTestigo,
      destinatario_autorizado_otro: destinatarioAutorizadoOtro,
      destinatario_autorizado_otro_especificar: destinatarioAutorizadoOtroTexto.trim() || null,
      firma_a_nombre_apellidos: firmaEntregaNombre,
      firma_a_cargo: firmaEntregaCargo,
      firma_a_empleo_rango: firmaEntregaEmpleo,
      firma_a: firmaEntregaFirma,
      firma_b_nombre_apellidos: firmaRecibeNombre,
      firma_b_cargo: firmaRecibeCargo,
      firma_b_empleo_rango: firmaRecibeEmpleo,
      firma_b: firmaRecibeFirma,
      observaciones_odmc: observacionesODMC,
    };

    // Agregar estado_material si se ha seleccionado
    if (materialHaSido && ['RECIBIDO', 'INVENTARIADO', 'DESTRUIDO'].includes(materialHaSido.toUpperCase())) {
      datosComunes.estado_material = materialHaSido.toUpperCase();
    }

    try {
      if (esOrigenMultipagina && Object.keys(estructuraPaginas).length > 1) {
        console.log('📄 Creando AC21 de salida multipágina...');
        console.log('📄 esOrigenMultipagina:', esOrigenMultipagina);
        console.log('📄 estructuraPaginas:', estructuraPaginas);
        console.log('📄 Object.keys(estructuraPaginas).length:', Object.keys(estructuraPaginas).length);
        
        // Crear página principal primero
        const paginasPorCrear = Object.keys(estructuraPaginas).sort((a, b) => parseInt(a) - parseInt(b));
        let documentoPrincipalId = null;
        
        for (let i = 0; i < paginasPorCrear.length; i++) {
          const numeroPagina = parseInt(paginasPorCrear[i]);
          const productosDeEstaPagina = estructuraPaginas[numeroPagina];
          
          // Convertir productos a formato API
          const lineasProductoParaApi: any[] = [];
          productosDeEstaPagina.forEach(lineaForm => {
            if (lineaForm.numeroSerie && lineaForm.numeroSerie.length > 0) {
              lineaForm.numeroSerie.forEach(serie => {
                lineasProductoParaApi.push({
                  codigo: lineaForm.producto,
                  cantidad: 1,
                  numero_serie: serie,
                  observaciones: lineaForm.observaciones,
                });
              });
            } else {
              lineasProductoParaApi.push({
                codigo: lineaForm.producto,
                cantidad: lineaForm.cantidad,
                observaciones: lineaForm.observaciones,
              });
            }
          });
          
          const datosPagina = {
            ...datosComunes,
            articulos: lineasProductoParaApi,
            numero: i === 0 ? numeroRegistroSalida : `${numeroRegistroSalida}-P${numeroPagina}`,
            pagina_numero: numeroPagina,
            total_paginas: paginasPorCrear.length,
          };
          
          // Si no es la primera página, agregar referencia al documento principal
          if (documentoPrincipalId) {
            datosPagina.documento_principal_id = documentoPrincipalId;
            datosPagina.es_pagina_adicional = true;
          }
          
          console.log(`📄 Creando página ${numeroPagina}:`, datosPagina);
          
          const responseData = await apiFetch("/albaranes/", {
            method: 'POST',
            body: JSON.stringify(datosPagina),
          });
          
          // Guardar el ID del documento principal
          if (i === 0) {
            documentoPrincipalId = responseData.id;
            console.log(`📄 Documento principal creado con ID: ${documentoPrincipalId}`);
          }
          
          if (responseData && responseData.error) {
            throw new Error(`Error en página ${numeroPagina}: ${responseData.error}`);
          }
        }
        
        console.log('📄 AC21 multipágina creado exitosamente');
        router.push('/salidas/albaranes');
        
      } else {
        // Crear AC21 de página única (comportamiento original)
        console.log('📄 Creando AC21 de salida página única...');
        
        const lineasProductoParaApi: any[] = [];
        lineas.forEach(lineaForm => {
          if (lineaForm.numeroSerie && lineaForm.numeroSerie.length > 0) {
            lineaForm.numeroSerie.forEach(serie => {
              lineasProductoParaApi.push({
                codigo: lineaForm.producto,
                cantidad: 1,
                numero_serie: serie,
                observaciones: lineaForm.observaciones,
              });
            });
          } else {
            lineasProductoParaApi.push({
              codigo: lineaForm.producto,
              cantidad: lineaForm.cantidad,
              observaciones: lineaForm.observaciones,
            });
          }
        });

        const datosParaBackend = {
          ...datosComunes,
          numero: numeroRegistroSalida,
          articulos: lineasProductoParaApi,
        };

        console.log("📄 Enviando AC21 página única:", JSON.stringify(datosParaBackend, null, 2));

      const responseData = await apiFetch("/albaranes/", {
        method: 'POST',
        body: JSON.stringify(datosParaBackend),
      });

      if (responseData && responseData.error) {
        if (responseData.error === 'DUPLICATE_ALBARAN') {
          setSubmitError("Error: Ya existe un albarán con ese número.");
        } else {
          setSubmitError(`Error del backend: ${responseData.error}`);
        }
      } else {
        router.push('/salidas/albaranes');
        }
      }

    } catch (error: any) {
      console.error("Error al guardar AC21 de salida:", error);
      let errorMessage = "No se pudo crear el albarán.";
      if (error && error.message) {
        const match = error.message.match(/Error \d+: (\{.*\})/);
        if (match && match[1]) {
          try {
            const parsedError = JSON.parse(match[1]);
            errorMessage = Object.entries(parsedError).map(([key, value]) => {
                if (Array.isArray(value)) return `${key}: ${value.join(', ')}`;
                return `${key}: ${value}`;
            }).join('; ');
          } catch (e) { errorMessage = match[1]; }
        } else {
          errorMessage = error.message;
        }
      } else if (typeof error === 'string') {
        errorMessage = error;
      }
      setSubmitError(`Error: ${errorMessage}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full flex flex-col gap-4 py-6 px-0 min-h-screen">
      <div className="bg-white rounded-lg shadow-sm p-6 w-full max-w-5xl mx-auto flex flex-col gap-4">
        <form className="space-y-6" onSubmit={handleSubmit}>
          {/* Formulario AC21 compacto */}
          <div className="border border-gray-300 rounded overflow-hidden bg-white">
            {/* Radios de tipo de transacción */}
            <div className="p-3 border-b-2 border-gray-300 bg-gray-50 flex flex-wrap gap-4 items-center justify-center">
            {tiposTransaccion.map((tipo) => (
              <label key={tipo} className="inline-flex items-center text-base font-semibold gap-2">
                <input
                  type="radio"
                  name="tipoTransaccion"
                  value={tipo}
                  checked={tipoTransaccion === tipo}
                  onChange={(e) => setTipoTransaccion(e.target.value)}
                  className="form-radio w-4 h-4 text-blue-600 border-2 border-gray-400"
                  required
                />
                  <span>{tipo === "Recibo en Mano" ? "RECIBO EN MANO" : tipo.toUpperCase()}</span>
              </label>
            ))}
          </div>
            
            {/* Banner informativo combinado */}
            {searchParams.get('from') && (
              <div className="bg-blue-50 border-l-4 border-blue-400 p-3 border-b border-gray-300">
                <div className="flex items-center justify-center gap-3 flex-wrap">
                  <span className="text-sm text-blue-800 font-medium">
                    📋 AC21 de salida basado en entrada (ID: {searchParams.get('from')})
                  </span>
                  <span className="text-sm text-blue-600">•</span>
                  <span className="text-sm text-blue-700">
                    🔄 Empresas intercambiadas automáticamente
                  </span>
                  {esOrigenMultipagina && (
                    <>
                      <span className="text-sm text-blue-600">•</span>
                      <span className="text-sm text-amber-700 bg-amber-100 px-2 py-1 rounded font-medium">
                        📄 Se crearán {totalPaginasOrigen} páginas automáticamente
                      </span>
                    </>
                  )}
                </div>
              </div>
            )}
            
            {/* Cuadrantes principales */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-0 min-h-[280px]">
              {/* Columna izquierda: Empresas DE y PARA */}
              <div className="flex flex-col h-full border-r-2 border-gray-300">
                {/* Empresa DE */}
                <div className="flex-1 pb-2 grid grid-cols-[28px_1fr] gap-2 p-3 min-h-[130px]">
                  <div className="flex flex-col items-center justify-center h-full pt-2 select-none">
                    <span className="text-lg font-bold leading-none">D</span>
                    <span className="text-lg font-bold leading-none">E</span>
                  </div>
                  <div>
                    <div className="relative w-full mb-1 flex items-center gap-2">
                      <input
                        type="text"
                        className="w-full border rounded-md py-1 px-2 text-sm mb-1"
                        placeholder="Buscar o seleccionar empresa de origen..."
                        value={empresaOrigen}
                        onChange={e => setEmpresaOrigen(e.target.value.replace(/\s+/g, ' ').replace(/\n/g, '').trim())}
                        autoComplete="off"
                        onFocus={() => {
                          if (empresaOrigen.trim() === "") setSugerenciasOrigen(empresas);
                        }}
                        required
                      />
                      <Button type="button" size="icon" variant="outline" className="mb-1 px-2 py-1 min-w-0 h-auto" title="Añadir nueva empresa" onClick={() => handleOpenEmpresaModal('origen')}>
                        +
                      </Button>
                    </div>
                    {sugerenciasOrigen.length > 0 &&
                      !sugerenciasOrigen.some(e => e.nombre.trim().toLowerCase() === empresaOrigen.trim().toLowerCase()) && (
                      <ul className="absolute z-10 bg-white border rounded shadow w-full mt-1 max-h-48 overflow-y-auto">
                        {sugerenciasOrigen.map(e => (
                          <li
                            key={e.id}
                            className="px-3 py-2 hover:bg-gray-100 cursor-pointer"
                            onClick={() => {
                              setEmpresaOrigen(e.nombre.replace(/\s+/g, ' ').replace(/\n/g, '').trim());
                              setSugerenciasOrigen([]);
                            }}
                          >
                            {e.nombre}
                          </li>
                        ))}
                      </ul>
                    )}
                    {empresas.find(e => e.nombre === empresaOrigen) && (
                      <div className="mt-1 text-xs text-gray-700 space-y-0.5">
                        <div>{empresas.find(e => e.nombre === empresaOrigen)?.direccion || '-'}</div>
                        <div>
                          {[
                            empresas.find(e => e.nombre === empresaOrigen)?.codigo_postal,
                            empresas.find(e => e.nombre === empresaOrigen)?.ciudad,
                            empresas.find(e => e.nombre === empresaOrigen)?.provincia
                          ].filter(Boolean).join(' ') || '-'}
                        </div>
                        <div>
                          <div><span className="font-semibold">ODMC Nº:</span> {empresas.find(e => e.nombre === empresaOrigen)?.numero_odmc || '-'}</div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                <div className="border-t-2 border-gray-300"></div>
                {/* Empresa PARA */}
                <div className="flex-1 pt-2 grid grid-cols-[28px_1fr] gap-2 p-3 min-h-[130px]">
                  <div className="flex flex-col items-center justify-center h-full pt-2 select-none">
                    <span className="text-lg font-bold leading-none">P</span>
                    <span className="text-lg font-bold leading-none">A</span>
                    <span className="text-lg font-bold leading-none">R</span>
                    <span className="text-lg font-bold leading-none">A</span>
                  </div>
                  <div>
                    <div className="relative w-full mb-1 flex items-center gap-2">
                      <input
                        type="text"
                        className="w-full border rounded-md py-1 px-2 text-sm mb-1"
                        placeholder="Buscar o seleccionar empresa de destino..."
                        value={empresaDestino}
                        onChange={e => setEmpresaDestino(e.target.value.replace(/\s+/g, ' ').replace(/\n/g, '').trim())}
                        autoComplete="off"
                        onFocus={() => {
                          if (empresaDestino.trim() === "") setSugerenciasDestino(empresas);
                        }}
                        required
                      />
                      <Button type="button" size="icon" variant="outline" className="mb-1 px-2 py-1 min-w-0 h-auto" title="Añadir nueva empresa" onClick={() => handleOpenEmpresaModal('destino')}>
                        +
                      </Button>
                    </div>
                    {sugerenciasDestino.length > 0 &&
                      !sugerenciasDestino.some(e => e.nombre.trim().toLowerCase() === empresaDestino.trim().toLowerCase()) && (
                      <ul className="absolute z-10 bg-white border rounded shadow w-full mt-1 max-h-48 overflow-y-auto">
                        {sugerenciasDestino.map(e => (
                          <li
                            key={e.id}
                            className="px-3 py-2 hover:bg-gray-100 cursor-pointer"
                            onClick={() => {
                              setEmpresaDestino(e.nombre.replace(/\s+/g, ' ').replace(/\n/g, '').trim());
                              setSugerenciasDestino([]);
                            }}
                          >
                            {e.nombre}
                          </li>
                        ))}
                      </ul>
                    )}
                    {empresas.find(e => e.nombre === empresaDestino) && (
                      <div className="mt-1 text-xs text-gray-700 space-y-0.5">
                        <div>{empresas.find(e => e.nombre === empresaDestino)?.direccion || '-'}</div>
                        <div>
                          {[
                            empresas.find(e => e.nombre === empresaDestino)?.codigo_postal,
                            empresas.find(e => e.nombre === empresaDestino)?.ciudad,
                            empresas.find(e => e.nombre === empresaDestino)?.provincia
                          ].filter(Boolean).join(' ') || '-'}
                        </div>
                        <div>
                          <div><span className="font-semibold">ODMC Nº:</span> {empresas.find(e => e.nombre === empresaDestino)?.numero_odmc || '-'}</div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              {/* Columna derecha: Datos de registro y CC */}
              <div className="flex flex-col h-full">
                <div className="flex-1 p-3 flex flex-col justify-center min-h-[130px]">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-gray-600 mb-1">Fecha del Informe</label>
                      <input type="date" className="w-full border rounded p-1 text-sm bg-gray-50" value={fechaInforme} onChange={e => setFechaInforme(e.target.value)} required />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-600 mb-1">Nº Registro de Salida</label>
                      <input type="text" className="w-full border rounded p-1 text-sm bg-gray-50" value={numeroRegistroSalida} onChange={e => setNumeroRegistroSalida(e.target.value)} required />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-600 mb-1">Fecha de la Transacción</label>
                      <input type="date" className="w-full border rounded p-1 text-sm bg-gray-50" value={fechaTransaccionDMA} onChange={e => setFechaTransaccionDMA(e.target.value)} required />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-600 mb-1">Nº Registro de Entrada</label>
                      <input type="text" className="w-full border rounded p-1 text-sm bg-gray-50" value={numeroRegistroEntrada} onChange={e => setNumeroRegistroEntrada(e.target.value)} />
                    </div>
                  </div>
                </div>
                <div className="border-t-2 border-gray-300"></div>
                <div className="flex-1 p-3 flex flex-col justify-center min-h-[130px]">
                  <div className="text-xs font-bold text-center mb-2">CÓDIGOS DE CONTABILIDAD (CC)</div>
                  <div className="text-xs text-gray-700 space-y-1">
                    <div>1. Contabilizable por número de serie.</div>
                    <div>2. Contabilizable por cantidad.</div>
                    <div>3. Acuse de recibo inicial. Puede ser controlado según instrucciones particulares del órgano correspondiente.</div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Tabla de artículos con el diseño AC21 */}
            <div className="mt-0">
              <div className="overflow-x-auto">
                <table className="min-w-full border border-gray-400 text-xs">
              <thead>
                <tr>
                  <th rowSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle w-8 bg-gray-50">#</th>
                  <th rowSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle bg-gray-50">TÍTULO CORTO / EDICIÓN</th>
                  <th rowSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle w-16 bg-gray-50">CANTIDAD</th>
                  <th colSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle bg-gray-50">NÚMERO DE SERIE</th>
                  <th rowSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle w-8 bg-gray-50">CC</th>
                  <th rowSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle bg-gray-50">OBSERVACIONES</th>
                  <th rowSpan={2} className="border-l border-r border-b border-gray-400 px-2 py-1 text-center align-middle w-12 bg-gray-50">ACCIÓN</th>
                </tr>
                <tr>
                  <th className="border border-gray-400 px-2 py-1 text-center align-middle w-28 bg-gray-50">INICIO</th>
                  <th className="border border-gray-400 px-2 py-1 text-center align-middle w-28 bg-gray-50">FIN</th>
                </tr>
              </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {lineas.map((linea, idx) => (
                    <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="border border-gray-400 px-2 py-1 text-center align-middle font-semibold">{idx + 1}</td>
                      
                      {/* Producto */}
                      <td className="border border-gray-400 px-2 py-1">
                        <div className="relative">
                          <input
                            type="text"
                            className="w-full border-0 bg-transparent text-xs focus:ring-1 focus:ring-blue-500 rounded"
                            placeholder="Buscar producto..."
                            value={linea.producto}
                            onChange={e => handleLineaChange(idx, "producto", e.target.value)}
                            onFocus={() => {
                              setProductoDropdownVisible(prev => prev.map((_, i) => i === idx ? true : false));
                              if (linea.producto.trim() === "") {
                                setSugerenciasProducto(prev => prev.map((_, i) => 
                                  i === idx ? productosCatalogo.map(p => ({ codigo: p.codigo_producto })) : []
                                ));
                              }
                            }}
                            onBlur={() => {
                              setTimeout(() => {
                                setProductoDropdownVisible(prev => prev.map((_, i) => i === idx ? false : prev[i]));
                              }, 200);
                            }}
                          />
                          {productoDropdownVisible[idx] && sugerenciasProducto[idx]?.length > 0 && (
                            <ul className="absolute z-10 bg-white border rounded shadow w-full mt-1 max-h-48 overflow-y-auto">
                              {sugerenciasProducto[idx].map((sugerencia, i) => (
                                <li
                                  key={i}
                                  className="px-3 py-2 hover:bg-gray-100 cursor-pointer text-xs"
                                  onClick={() => {
                                    handleSelectProducto(idx, sugerencia.codigo);
                                    setProductoDropdownVisible(prev => prev.map((_, j) => j === idx ? false : prev[j]));
                                  }}
                                >
                                  {sugerencia.codigo}
                                </li>
                              ))}
                            </ul>
                          )}
          </div>
                      </td>
                      
                      {/* Cantidad */}
                      <td className="border border-gray-400 px-2 py-1 text-center">
                        <input
                          type="number"
                          min="1"
                          className="w-full border-0 bg-transparent text-center text-xs focus:ring-1 focus:ring-blue-500 rounded"
                          value={linea.cantidad}
                          onChange={e => handleLineaChange(idx, "cantidad", parseInt(e.target.value) || 1)}
                        />
                      </td>
                      
                      {/* Número de Serie INICIO */}
                      <td className="border border-gray-400 px-2 py-1 text-center">
                        <div className="space-y-1">
                                                    {/* Números de serie editables */}
                          {linea.numeroSerie.map((serie, serieIdx) => (
                            <input
                              key={serieIdx}
                              type="text"
                              className="w-full border-0 bg-transparent text-xs focus:ring-1 focus:ring-blue-500 rounded mb-1"
                              value={serie}
                              onChange={e => {
                                const newNumeroSerie = [...linea.numeroSerie];
                                newNumeroSerie[serieIdx] = e.target.value;
                                setLineas(prev => prev.map((l, i) => i === idx ? { ...l, numeroSerie: newNumeroSerie } : l));
                              }}
                              placeholder="Número de serie..."
                            />
                          ))}
                        </div>
                      </td>
                      
                      {/* Número de Serie FIN */}
                      <td className="border border-gray-400 px-2 py-1 text-center">
                        <input
                          type="text"
                          className="w-full border-0 bg-transparent text-center text-xs focus:ring-1 focus:ring-blue-500 rounded"
                          value={linea.numeroSerie.length > 0 ? linea.numeroSerie[linea.numeroSerie.length - 1] : ''}
                          onChange={e => {
                            if (linea.numeroSerie.length > 0) {
                              const newNumeroSerie = [...linea.numeroSerie];
                              newNumeroSerie[newNumeroSerie.length - 1] = e.target.value;
                              setLineas(prev => prev.map((l, i) => i === idx ? { ...l, numeroSerie: newNumeroSerie } : l));
                            }
                          }}
                          placeholder="Nº serie fin..."
                        />
                      </td>
                      
                      {/* CC */}
                      <td className="border border-gray-400 px-2 py-1 text-center">
                        <span className="text-xs">1</span>
                      </td>
                      
                      {/* Observaciones */}
                      <td className="border border-gray-400 px-2 py-1">
                        <textarea
                          className="w-full border-0 bg-transparent text-xs resize-none focus:ring-1 focus:ring-blue-500 rounded"
                          rows={1}
                          placeholder="Observaciones..."
                          value={linea.observaciones}
                          onChange={e => handleLineaChange(idx, "observaciones", e.target.value)}
                        />
                      </td>
                      
                      {/* Acción - Eliminar */}
                      <td className="border border-gray-400 px-1 py-1 text-center">
                        {lineas.length > 1 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveLinea(idx)}
                            className="text-red-600 hover:text-red-800 hover:bg-red-50 rounded p-1 transition-colors"
                            title="Eliminar línea"
                          >
                            ✕
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* Botón de acción para añadir líneas */}
            {lineas.length < 18 && (
              <div className="flex gap-2 mt-6 mb-4 justify-center">
                <Button
                  type="button"
                  variant="outline"
                  size="lg"
                  onClick={handleAddLinea}
                  className="bg-green-50 hover:bg-green-100 text-green-700 border-green-300 font-semibold px-6 py-3 shadow-md hover:shadow-lg transition-shadow"
                >
                  ➕ Añadir Nueva Línea de Producto
                </Button>
              </div>
            )}
          </div>

          {/* Línea ULTIMA LINEA */}
          <div className="mt-2 text-center">
            <div className="flex items-center justify-center gap-2">
              <span className="text-gray-400 text-lg font-mono select-none">
                ///////////////////
              </span>
              <span className="text-xs font-bold">ULTIMA LINEA</span>
              <span className="text-gray-400 text-lg font-mono select-none">
                ///////////////////
              </span>
            </div>
          </div>

          {/* Sección Accesorios y Equipos de Prueba */}
          <div className="mt-6">
            <div className="p-4">
              <div className="grid grid-cols-2 min-h-[200px]">
                
                {/* Cuadrante izquierdo: Accesorios */}
                <div className="px-4 pr-8">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xs font-bold">ACCESORIOS ENTREGADOS CON CADA EQUIPO:</h3>
                    <button
                      type="button"
                      onClick={handleAddAccesorio}
                      className="text-green-600 hover:text-green-800 text-xs font-medium px-2 py-1 hover:bg-green-50 rounded transition-colors"
                      title="Añadir accesorio"
                    >
                      + Añadir
                    </button>
                  </div>
                  <table className="w-full text-xs">
                    <tbody>
                      {accesorios.length > 0 ? accesorios.map((accesorio: any, index: number) => (
                        <tr key={index}>
                          <td className="w-4 text-center">
                            {accesorios.length > 1 && (
                              <button
                                type="button"
                                onClick={() => handleRemoveAccesorio(index)}
                                className="text-red-600 hover:text-red-800 hover:bg-red-50 rounded p-1 transition-colors text-xs"
                                title="Eliminar accesorio"
                              >
                                ✕
                              </button>
                            )}
                          </td>
                          <td className="pl-2 py-0.5">
                            <input
                              type="text"
                              className="w-full border-0 bg-transparent text-xs focus:ring-1 focus:ring-blue-500 rounded"
                              placeholder="Descripción del accesorio..."
                              value={accesorio.descripcion || ''}
                              onChange={e => handleAccesorioChange(index, 'descripcion', e.target.value)}
                            />
                          </td>
                          <td className="text-right w-12">
                            <input
                              type="number"
                              min="1"
                              className="w-full border-0 bg-transparent text-xs text-right focus:ring-1 focus:ring-blue-500 rounded"
                              value={accesorio.cantidad || 1}
                              onChange={e => handleAccesorioChange(index, 'cantidad', parseInt(e.target.value) || 1)}
                            />
                          </td>
                          <td className="w-12"></td>
                        </tr>
                      )) : (
                        <tr>
                          <td colSpan={4} className="text-gray-500 pl-4 py-2 text-center text-xs">
                            <em>No hay accesorios especificados</em>
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Cuadrante derecho: Equipos de Prueba */}
                <div className="pl-8">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xs font-bold">EQUIPOS DE PRUEBA AICOX:</h3>
                    <button
                      type="button"
                      onClick={handleAddEquipoPrueba}
                      className="text-green-600 hover:text-green-800 text-xs font-medium px-2 py-1 hover:bg-green-50 rounded transition-colors"
                      title="Añadir equipo de prueba"
                    >
                      + Añadir
                    </button>
                  </div>
                  <table className="w-full text-xs">
                    <tbody>
                      {equiposPrueba.length > 0 ? equiposPrueba.map((equipo: any, index: number) => (
                        <tr key={index}>
                          <td className="w-4 text-center">
                            {equiposPrueba.length > 1 && (
                              <button
                                type="button"
                                onClick={() => handleRemoveEquipoPrueba(index)}
                                className="text-red-600 hover:text-red-800 hover:bg-red-50 rounded p-1 transition-colors text-xs"
                                title="Eliminar equipo de prueba"
                              >
                                ✕
                              </button>
                            )}
                          </td>
                          <td className="pl-2 py-0.5 w-20">
                            <input
                              type="text"
                              className="w-full border-0 bg-transparent text-xs focus:ring-1 focus:ring-blue-500 rounded"
                              placeholder="Código..."
                              value={equipo.codigo || ''}
                              onChange={e => handleEquipoPruebaChange(index, 'codigo', e.target.value)}
                            />
                          </td>
                          <td className="pl-2 py-0.5">
                            <input
                              type="text"
                              className="w-full border-0 bg-transparent text-xs focus:ring-1 focus:ring-blue-500 rounded"
                              placeholder="Comentario..."
                              value={equipo.comentario || ''}
                              onChange={e => handleEquipoPruebaChange(index, 'comentario', e.target.value)}
                            />
                          </td>
                        </tr>
                      )) : (
                        <tr>
                          <td colSpan={3} className="text-gray-500 pl-4 py-2 text-center text-xs">
                            <em>No hay equipos de prueba especificados</em>
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          {/* Material ha sido - Radio buttons */}
          <div className="mt-6 p-4 border-t border-gray-400 bg-gray-50">
            <div className="flex items-center gap-6">
              <label className="text-sm font-semibold text-gray-700">El material ha sido:</label>
              {['RECIBIDO', 'INVENTARIADO', 'DESTRUIDO'].map(estado => (
                <label key={estado} className="inline-flex items-center gap-2">
                  <input
                    type="radio"
                    name="materialHaSido"
                    value={estado}
                    checked={materialHaSido === estado}
                    onChange={e => setMaterialHaSido(e.target.value)}
                    className="w-4 h-4 text-blue-600 border-2 border-gray-400 rounded-sm focus:ring-blue-500 focus:ring-2 appearance-none checked:bg-blue-600 checked:border-blue-600 relative checked:after:content-['✓'] checked:after:text-white checked:after:text-xs checked:after:absolute checked:after:inset-0 checked:after:flex checked:after:items-center checked:after:justify-center"
                  />
                  <span className="text-sm font-medium">{estado}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Firmas y Observaciones */}
          <div className="border-t border-gray-400 mt-6">
            <table className="w-full text-[11px] border-collapse">
              <thead>
                <tr>
                  <th className="font-bold px-2 py-1 border-b border-r border-gray-400 text-left" colSpan={2}>
                    15. DESTINATARIO AUTORIZADO DEL MATERIAL DE CIFRA
                  </th>
                  <th className="font-bold px-2 py-1 border-b border-gray-400 text-left" colSpan={2}>
                    16. (marcar X) ⇒
                    <label className="inline-flex items-center gap-1 ml-2">
                      <input 
                        type="checkbox" 
                        className="accent-black" 
                        checked={destinatarioAutorizadoTestigo}
                        onChange={e => setDestinatarioAutorizadoTestigo(e.target.checked)}
                      /> TESTIGO
                    </label>
                    <label className="inline-flex items-center gap-1 ml-4">
                      <input 
                        type="checkbox" 
                        className="accent-black" 
                        checked={destinatarioAutorizadoOtro}
                        onChange={e => setDestinatarioAutorizadoOtro(e.target.checked)}
                      /> OTRO
                    </label>
                    {destinatarioAutorizadoOtro && (
                      <div className="mt-1">
                        <input
                          type="text"
                          className="w-32 text-xs border border-gray-300 rounded px-2 py-1 focus:ring-1 focus:ring-blue-500"
                          placeholder="Especificar..."
                          value={destinatarioAutorizadoOtroTexto}
                          onChange={e => setDestinatarioAutorizadoOtroTexto(e.target.value)}
                        />
                      </div>
                    )}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="border-b border-r border-gray-400 px-2 py-1 align-top">
                    a. Firma
                    <div className="h-8">
                      <input
                        type="text"
                        className="w-full border-0 bg-transparent text-xs focus:ring-1 focus:ring-blue-500 rounded"
                        placeholder="Firma entrega..."
                        value={firmaEntregaFirma}
                        onChange={e => setFirmaEntregaFirma(e.target.value)}
                      />
                    </div>
                  </td>
                  <td className="border-b border-r border-gray-400 px-2 py-1 align-top">
                    b. Empleo/Rango
                    <div className="h-8">
                      <input
                        type="text"
                        className="w-full border-0 bg-transparent text-xs font-bold focus:ring-1 focus:ring-blue-500 rounded"
                        placeholder="Empleo/Rango..."
                        value={firmaEntregaEmpleo}
                        onChange={e => setFirmaEntregaEmpleo(e.target.value)}
                      />
                    </div>
                  </td>
                  <td className="border-b border-r border-gray-400 px-2 py-1 align-top">
                    a. Firma
                    <div className="h-8">
                      <input
                        type="text"
                        className="w-full border-0 bg-transparent text-xs focus:ring-1 focus:ring-blue-500 rounded"
                        placeholder="Firma recibe..."
                        value={firmaRecibeFirma}
                        onChange={e => setFirmaRecibeFirma(e.target.value)}
                      />
                    </div>
                  </td>
                  <td className="border-b border-gray-400 px-2 py-1 align-top">
                    b. Empleo/Rango
                    <div className="h-8">
                      <input
                        type="text"
                        className="w-full border-0 bg-transparent text-xs font-bold focus:ring-1 focus:ring-blue-500 rounded"
                        placeholder="Empleo/Rango..."
                        value={firmaRecibeEmpleo}
                        onChange={e => setFirmaRecibeEmpleo(e.target.value)}
                      />
                    </div>
                  </td>
                </tr>
                <tr>
                  <td className="border-r border-gray-400 px-2 py-1 align-top">
                    c. Nombre y Apellidos
                    <div className="h-8">
                      <input
                        type="text"
                        className="w-full border-0 bg-transparent text-xs font-bold focus:ring-1 focus:ring-blue-500 rounded"
                        placeholder="Nombre y apellidos..."
                        value={firmaEntregaNombre}
                        onChange={e => setFirmaEntregaNombre(e.target.value)}
                      />
                    </div>
                  </td>
                  <td className="border-r border-gray-400 px-2 py-1 align-top">
                    d. Cargo
                    <div className="h-8">
                      <input
                        type="text"
                        className="w-full border-0 bg-transparent text-xs font-bold focus:ring-1 focus:ring-blue-500 rounded"
                        placeholder="Cargo..."
                        value={firmaEntregaCargo}
                        onChange={e => setFirmaEntregaCargo(e.target.value)}
                      />
                    </div>
                  </td>
                  <td className="border-r border-gray-400 px-2 py-1 align-top">
                    c. Nombre y Apellidos
                    <div className="h-8">
                      <input
                        type="text"
                        className="w-full border-0 bg-transparent text-xs font-bold focus:ring-1 focus:ring-blue-500 rounded"
                        placeholder="Nombre y apellidos..."
                        value={firmaRecibeNombre}
                        onChange={e => setFirmaRecibeNombre(e.target.value)}
                      />
                    </div>
                  </td>
                  <td className="px-2 py-1 align-top">
                    d. Cargo
                    <div className="h-8">
                      <input
                        type="text"
                        className="w-full border-0 bg-transparent text-xs font-bold focus:ring-1 focus:ring-blue-500 rounded"
                        placeholder="Cargo..."
                        value={firmaRecibeCargo}
                        onChange={e => setFirmaRecibeCargo(e.target.value)}
                      />
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
            
            {/* Observaciones ODMC */}
            <div className="border-t border-gray-400 px-4 py-2 bg-gray-50">
              <div className="font-bold mb-1">17. OBSERVACIONES DEL ODMC REMITENTE</div>
              <textarea
                className="w-full border border-gray-300 rounded px-3 py-2 text-xs bg-white resize-none focus:ring-1 focus:ring-blue-500"
                rows={3}
                placeholder="Observaciones del ODMC remitente..."
                value={observacionesODMC}
                onChange={e => setObservacionesODMC(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Botones de acción */}
          <div className="flex gap-4 justify-end mt-8 pt-6 border-t border-gray-200">
            <Button
              type="button"
              variant="outline"
              onClick={() => router.push('/salidas/albaranes')}
              disabled={isSubmitting}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={!puedeAvanzar || isSubmitting}
              className="bg-purple-600 hover:bg-purple-700 text-white"
            >
              {isSubmitting ? 'Guardando...' : 'Crear AC21 de Salida'}
            </Button>
          </div>

          {/* Mostrar errores */}
          {submitError && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">{submitError}</p>
            </div>
          )}
        </form>
      </div>
      {/* Modal de alta de empresa */}
      <Dialog open={showEmpresaModal} onOpenChange={setShowEmpresaModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Alta de Empresa {empresaModalTipo === 'origen' ? 'Origen' : empresaModalTipo === 'destino' ? 'Destino' : ''}</DialogTitle>
            <DialogDescription>
              Completa los datos para dar de alta la nueva empresa en el sistema.
            </DialogDescription>
          </DialogHeader>
          <EmpresaForm
            onSuccess={handleEmpresaCreada}
            onCancel={() => setShowEmpresaModal(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Wrapper del componente con Suspense para manejar useSearchParams
export default function CrearAC21SalidaFormPageWrapper() {
  return (
    <Suspense fallback={<div className="flex justify-center items-center min-h-screen">Cargando formulario...</div>}>
      <CrearAC21SalidaFormPage />
    </Suspense>
  );
} 