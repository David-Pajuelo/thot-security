import React, { useState, useEffect, useRef } from 'react';
import { PDFDocument, rgb, StandardFonts } from 'pdf-lib';
import { PencilIcon, CheckIcon, XMarkIcon, DocumentArrowDownIcon } from '@heroicons/react/24/outline';
import hpsService from '../services/hpsService';
import { formatErrorForDisplay } from '../utils/errorHandler';

const PDFViewerEditor = ({ hpsId, isOpen, onClose, onSave }) => {
  const [pdfBytes, setPdfBytes] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState('');
  const [pdfUrl, setPdfUrl] = useState('');
  const canvasRef = useRef(null);
  const [annotations, setAnnotations] = useState([]);
  const [currentAnnotation, setCurrentAnnotation] = useState(null);

  // Campos editables del PDF
  const editableFields = [
    { key: 'Nombre', label: 'Nombre', x: 100, y: 700, width: 200, height: 20 },
    { key: 'Apellidos', label: 'Apellidos', x: 100, y: 670, width: 200, height: 20 },
    { key: 'DNI', label: 'DNI/NIE', x: 100, y: 640, width: 150, height: 20 },
    { key: 'Fecha de nacimiento', label: 'Fecha de nacimiento', x: 100, y: 610, width: 150, height: 20 },
    { key: 'Nacionalidad', label: 'Nacionalidad', x: 100, y: 580, width: 150, height: 20 },
    { key: 'LugarNacimiento', label: 'Lugar de nacimiento', x: 100, y: 550, width: 200, height: 20 },
    { key: 'Teléfono', label: 'Teléfono', x: 100, y: 520, width: 150, height: 20 },
    { key: 'Email', label: 'Email', x: 100, y: 490, width: 200, height: 20 },
    { key: 'Otros datos', label: 'Otros datos', x: 100, y: 460, width: 200, height: 20 },
    { key: 'Motivo de la solicitudRow1', label: 'Motivo de la solicitud', x: 100, y: 430, width: 200, height: 20 }
  ];

  useEffect(() => {
    if (isOpen && hpsId) {
      loadPDF();
    } else if (!isOpen && pdfUrl) {
      // Limpiar blob URL cuando se cierra el componente
      URL.revokeObjectURL(pdfUrl);
      setPdfUrl('');
      setPdfBytes(null);
    }
  }, [isOpen, hpsId]);

  const loadPDF = async () => {
    setLoading(true);
    setError('');

    try {
      // Siempre usar el endpoint filled-pdf para obtener los bytes
      // Esto asegura que la autenticación funcione correctamente
      const result = await hpsService.getFilledPDFBytes(hpsId);
      if (result.success) {
        // Crear blob URL para el iframe (los iframes no pueden pasar headers de autenticación)
        const blob = new Blob([result.data], { type: 'application/pdf' });
        const url = URL.createObjectURL(blob);
        setPdfUrl(url);
        setPdfBytes(result.data);
      } else {
        // Si no hay PDF, verificar si la solicitud existe
        const requestResult = await hpsService.getRequest(hpsId);
        if (requestResult.success && !requestResult.data.filled_pdf) {
          setError('No hay PDF rellenado disponible para esta solicitud');
        } else {
          setError(String(result.error) || 'Error al cargar el PDF');
        }
      }
    } catch (err) {
      console.error('Error cargando PDF:', err);
      setError('Error al cargar el PDF: ' + (err.message || 'Error desconocido'));
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = async () => {
    console.log('Iniciando modo edición...');
    setIsEditing(true);
    setExtracting(true);
    setError('');
    
    // Añadir un pequeño delay para asegurar que el estado se actualice
    setTimeout(async () => {
      // Extraer valores del PDF y pre-rellenar el formulario
      await extractTextFromPDF();
    }, 100);
  };

  const extractTextFromPDF = async () => {
    if (!pdfBytes) {
      console.warn('No hay PDF cargado, esperando...');
      // Reintentar después de un delay si no hay PDF
      setTimeout(() => extractTextFromPDF(), 200);
      return;
    }

    try {
      console.log('Iniciando extracción de campos del PDF...');
      
      // Llamar al backend para extraer los valores usando PyMuPDF
      const result = await hpsService.extractPDFFields(hpsId);
      
      // Si el endpoint no existe, usar extracción local directamente
      if (!result.success && result.error && result.error.includes('404')) {
        console.log('Endpoint de extracción no disponible, usando extracción local...');
        await extractTextFromPage();
        return;
      }
      
      if (result.success && result.data) {
        console.log('Valores extraídos del backend:', result.data);
        
        // Verificar que tenemos datos válidos
        if (Object.keys(result.data).length === 0) {
          console.warn('Backend devolvió datos vacíos, reintentando...');
          setTimeout(() => extractTextFromPDF(), 500);
          return;
        }
        
        // Crear anotaciones con los valores extraídos
        const initialAnnotations = [];
        const processedFields = new Set(); // Para evitar duplicados
        
        Object.entries(result.data).forEach(([field, value]) => {
          console.log(`Procesando campo: "${field}" = "${value}"`);
          
          // Filtrar campos duplicados - solo tomar el primero
          if (field.toLowerCase().includes('teléfono') || field.toLowerCase().includes('telefono')) {
            if (processedFields.has('Teléfono')) {
              console.log(`Ignorando campo duplicado de teléfono: "${field}"`);
              return;
            }
            processedFields.add('Teléfono');
          }
          
          // Mapear nombres de campos del PDF a nuestros campos editables
          let editableField = editableFields.find(f => f.key === field);
          
          // Si no hay coincidencia exacta, buscar coincidencia parcial
          if (!editableField) {
            editableField = editableFields.find(f => 
              field.toLowerCase().includes(f.key.toLowerCase()) ||
              f.key.toLowerCase().includes(field.toLowerCase())
            );
          }
          
          if (editableField) {
            console.log(`Mapeado "${field}" a campo editable "${editableField.key}"`);
            
            // Convertir a mayúsculas todos los campos excepto el correo
            let processedValue = String(value).trim();
            if (editableField.key.toLowerCase() !== 'email' && editableField.key.toLowerCase() !== 'correo') {
              processedValue = processedValue.toUpperCase();
            }
            
            initialAnnotations.push({
              id: Date.now() + Math.random(),
              field: editableField.key, // Usar el key del campo editable
              text: processedValue,
              x: editableField.x,
              y: editableField.y
            });
          } else {
            console.log(`No se encontró campo editable para "${field}"`);
          }
        });
        
        console.log('Anotaciones creadas:', initialAnnotations);
        
        // Verificar que se crearon anotaciones
        if (initialAnnotations.length === 0) {
          console.warn('No se pudieron mapear campos, reintentando...');
          setTimeout(() => extractTextFromPDF(), 500);
          return;
        }
        
        setAnnotations(initialAnnotations);
      } else {
        console.log('No se pudieron extraer valores del backend, intentando extracción local...');
        await extractTextFromPage();
      }
    } catch (err) {
      console.warn('Error extrayendo valores del backend:', err);
      // Fallback a extracción local
      try {
        await extractTextFromPage();
      } catch (fallbackErr) {
        console.error('Error en fallback también:', fallbackErr);
        setError('Error al extraer campos del PDF');
      }
    } finally {
      setExtracting(false);
    }
  };

  const extractTextFromPage = async (page) => {
    try {
      // Intentar extraer texto usando el método correcto de PDF-lib
      const textContent = await page.getTextContent();
      const fullText = textContent.items.map(item => item.str).join(' ');
      
      console.log('Texto extraído de la página:', fullText);
      
      // Buscar patrones en el texto extraído
      const patterns = {
        'Nombre': /Nombre:\s*([^\n\r,]+)/i,
        'Apellidos': /Apellidos:\s*([^\n\r,]+)/i,
        'DNI': /DNI[:\s]*([A-Z0-9]{8,9})/i,
        'Fecha de nacimiento': /Fecha de nacimiento:\s*([^\n\r,]+)/i,
        'Nacionalidad': /Nacionalidad:\s*([^\n\r,]+)/i,
        'LugarNacimiento': /Lugar de nacimiento[:\s]*([^\n\r,]+)/i,
        'Teléfono': /Teléfono:\s*([^\n\r,]+)/i,
        'Email': /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/i
      };
      
      const extractedValues = {};
      Object.entries(patterns).forEach(([field, pattern]) => {
        const match = fullText.match(pattern);
        if (match && match[1]) {
          extractedValues[field] = String(match[1].trim());
        }
      });
      
      // Crear anotaciones con los valores extraídos
      const initialAnnotations = [];
      Object.entries(extractedValues).forEach(([field, value]) => {
        const editableField = editableFields.find(f => f.key === field);
        if (editableField && value && value.trim()) {
          initialAnnotations.push({
            id: Date.now() + Math.random(),
            field: String(field),
            text: String(value).trim(),
            x: editableField.x,
            y: editableField.y
          });
        }
      });
      
      console.log('Anotaciones creadas desde texto:', initialAnnotations);
      
      setAnnotations(initialAnnotations);
    } catch (err) {
      console.warn('Error extrayendo texto de la página:', err);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setAnnotations([]);
    setCurrentAnnotation(null);
  };

  const handleSave = async () => {
    if (!pdfBytes) return;

    // Verificar que hay al menos una anotación con texto
    const validAnnotations = annotations.filter(annotation => annotation.text && annotation.text.trim());
    if (validAnnotations.length === 0) {
      setError('No hay cambios para guardar. Escribe algo en los campos.');
      return;
    }

    setSaving(true);
    setError('');

    try {
      console.log('Guardando PDF con anotaciones:', validAnnotations);
      
      // No necesitamos crear el PDF localmente, el backend lo hace
      
      // Crear un diccionario con los campos modificados para enviar al backend
      const fieldUpdates = {};
      validAnnotations.forEach(annotation => {
        fieldUpdates[annotation.field] = annotation.text;
      });
      
      console.log('Enviando campos al backend:', fieldUpdates);
      
      // Usar el endpoint existente de edición
      const result = await hpsService.editFilledPDF(hpsId, fieldUpdates);
      console.log('Resultado del backend:', result);
      
      if (result.success) {
        // Mostrar mensaje de éxito
        alert('✅ PDF guardado correctamente');
        
        // Limpiar el blob URL anterior para forzar recarga
        if (pdfUrl) {
          URL.revokeObjectURL(pdfUrl);
          setPdfUrl('');
        }
        setPdfBytes(null);
        
        // Recargar el PDF actualizado desde el servidor
        setLoading(true);
        try {
          const bytesResult = await hpsService.getFilledPDFBytes(hpsId);
          if (bytesResult.success) {
            // Crear nuevo blob URL con el PDF actualizado
            const blob = new Blob([bytesResult.data], { type: 'application/pdf' });
            const url = URL.createObjectURL(blob);
            setPdfUrl(url);
            setPdfBytes(bytesResult.data);
          } else {
            setError('Error al recargar el PDF actualizado');
          }
        } catch (reloadErr) {
          console.error('Error recargando PDF:', reloadErr);
          setError('Error al recargar el PDF actualizado');
        } finally {
          setLoading(false);
        }
        
        // Salir del modo edición pero mantener el modal abierto para ver los cambios
        setIsEditing(false);
        setAnnotations([]);
        setCurrentAnnotation(null);
        
        // Notificar al componente padre que se guardó
        onSave && onSave();
      } else {
        // Si el endpoint no existe, mostrar mensaje informativo
        if (result.error && result.error.includes('404')) {
          const errorMsg = 'La funcionalidad de edición de PDF no está disponible en el backend.';
          setError(errorMsg);
          alert('⚠️ ' + errorMsg);
        } else {
          const errorMsg = String(result.error) || 'Error al guardar el PDF';
          setError(errorMsg);
          alert('❌ ' + errorMsg);
        }
      }
    } catch (err) {
      console.error('Error saving PDF:', err);
      const errorMsg = formatErrorForDisplay(err);
      setError('Error al guardar el PDF: ' + errorMsg);
      alert('❌ Error al guardar el PDF: ' + errorMsg);
    } finally {
      setSaving(false);
    }
  };


  const handleClose = () => {
    setIsEditing(false);
    setAnnotations([]);
    setCurrentAnnotation(null);
    if (pdfUrl) {
      URL.revokeObjectURL(pdfUrl);
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2">
      <div className="bg-white rounded-lg shadow-xl w-full h-[95vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            {isEditing ? 'Editor de PDF - Traspaso HPS' : 'Visualizador de PDF'}
          </h2>
          <div className="flex items-center space-x-2">
            {!isEditing ? (
              <button
                onClick={handleEdit}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
              >
                <PencilIcon className="h-4 w-4 mr-2" />
                Editar PDF
              </button>
            ) : (
              <>
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center"
                >
                  {saving ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Guardando...
                    </>
                  ) : (
                      <>
                        <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
                        Guardar PDF
                      </>
                  )}
                </button>
              </>
            )}
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex min-h-0">
          {/* PDF Viewer */}
          <div className="flex-1 relative bg-gray-100">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Cargando PDF...</p>
                </div>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-red-600 text-center p-8">
                  <div className="text-6xl mb-4">⚠️</div>
                  <p className="text-xl font-semibold mb-2">Error al cargar el PDF</p>
                  <p className="text-sm">{String(error)}</p>
                </div>
              </div>
            ) : pdfUrl ? (
              <div className="relative h-full w-full overflow-auto">
                <iframe
                  src={pdfUrl}
                  className="w-full h-full border-0"
                  title="PDF Viewer"
                  style={{ minHeight: '600px' }}
                />
                
                {/* Overlay de estado del PDF */}
                {!isEditing && (
                  <div className="absolute top-4 right-4 bg-blue-100 text-blue-800 px-3 py-1 rounded-md text-sm font-medium shadow-md">
                    📖 Solo lectura
                  </div>
                )}
                {isEditing && (
                  <div className="absolute top-4 right-4 bg-green-100 text-green-800 px-3 py-1 rounded-md text-sm font-medium shadow-md">
                    ✏️ Modo edición - Usa el panel lateral
                  </div>
                )}
              </div>
            ) : null}
          </div>

          {/* Panel de edición */}
          {isEditing && (
            <div className="w-72 border-l bg-white p-4 overflow-y-auto shadow-lg">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Editar Campos</h3>
                {extracting && (
                  <div className="mt-2 flex items-center text-sm text-blue-600">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                    Extrayendo campos del PDF...
                  </div>
                )}
                {!extracting && annotations.length === 0 && isEditing && (
                  <div className="mt-2 flex items-center justify-between text-sm">
                    <span className="text-orange-600">No se pudieron cargar los campos</span>
                    <button
                      onClick={extractTextFromPDF}
                      className="px-2 py-1 text-xs bg-orange-100 text-orange-700 rounded hover:bg-orange-200"
                    >
                      Reintentar
                    </button>
                  </div>
                )}
              </div>
              
              <div className="space-y-3">
                {editableFields.map((field) => {
                  const annotation = annotations.find(a => a.field === field.key);
                  return (
                    <div key={String(field.key)} className="space-y-1">
                      <label className="block text-sm font-medium text-gray-700">
                        {String(field.label)}
                      </label>
                      <div className="flex items-center space-x-2">
                        <input
                          type="text"
                          value={String(annotation?.text || '')}
                          onChange={(e) => {
                            const newAnnotation = {
                              id: Date.now(),
                              field: field.key,
                              text: String(e.target.value),
                              x: field.x,
                              y: field.y
                            };
                            setAnnotations(prev => [...prev.filter(a => a.field !== field.key), newAnnotation]);
                          }}
                          className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                          placeholder={String(field.label.toLowerCase())}
                        />
                        {annotation && (
                          <CheckIcon className="h-4 w-4 text-green-500 flex-shrink-0" />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-xs text-blue-800">
                  💡 <strong>Valores extraídos del PDF:</strong> Los campos se han pre-rellenado con los valores encontrados en el PDF. Modifica solo los que necesites cambiar.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PDFViewerEditor;
