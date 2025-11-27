import React, { useState, useEffect, useRef } from 'react';
import { PDFDocument, rgb, StandardFonts } from 'pdf-lib';
import { PencilIcon, CheckIcon, XMarkIcon, DocumentArrowDownIcon } from '@heroicons/react/24/outline';
import templateService from '../services/templateService';
import { formatErrorForDisplay } from '../utils/errorHandler';

const TemplatePDFEditor = ({ templateId, isOpen, onClose, onSave }) => {
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

  // Campos editables del PDF (solo 3 campos)
  const editableFields = [
    { key: 'Identificación', label: 'Identificación', x: 100, y: 700, width: 200, height: 20 },
    { key: 'Correo electrónico_2', label: 'Correo electrónico', x: 100, y: 670, width: 200, height: 20 },
    { key: 'Teléfono_2', label: 'Teléfono', x: 100, y: 640, width: 200, height: 20 },
  ];

  useEffect(() => {
    if (isOpen && templateId) {
      loadPDF();
    }
  }, [isOpen, templateId]);

  const loadPDF = async () => {
    setLoading(true);
    setError('');

    try {
      const result = await templateService.getTemplatePDFBytes(templateId);
      if (result.success) {
        // Crear URL del PDF para mostrar
        const blob = new Blob([result.data], { type: 'application/pdf' });
        const url = URL.createObjectURL(blob);
        setPdfUrl(url);
        setPdfBytes(result.data);
      } else {
        setError(String(result.error) || 'Error al cargar el PDF');
      }
    } catch (err) {
      setError('Error al cargar el PDF');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = async () => {
    console.log('Iniciando modo edición...');
    setIsEditing(true);
    setExtracting(true);
    setError('');
    
    setTimeout(async () => {
      await extractTextFromPDF();
    }, 100);
  };

  const extractTextFromPDF = async () => {
    if (!pdfBytes) {
      setTimeout(() => extractTextFromPDF(), 200);
      return;
    }

    try {
      console.log('Iniciando extracción de campos del PDF...');
      
      const result = await templateService.extractTemplatePDFFields(templateId);
      
      console.log('🔍 Resultado completo del servicio:', result);
      
      if (result.success && result.data) {
        console.log('✅ Valores extraídos del backend:', result.data);
        console.log('📊 Total de campos recibidos:', Object.keys(result.data).length);
        console.log('📋 Lista de campos recibidos:', Object.keys(result.data));
        
        // Verificar específicamente los 3 campos que necesitamos
        const targetFields = ['Identificación', 'Correo electrónico_2', 'Teléfono_2'];
        console.log('🎯 Verificando campos objetivo:');
        targetFields.forEach(field => {
          if (field in result.data) {
            console.log(`   ✅ "${field}": "${result.data[field]}"`);
          } else {
            console.log(`   ❌ "${field}": NO ENCONTRADO`);
          }
        });
        
        if (Object.keys(result.data).length === 0) {
          console.warn('Backend devolvió datos vacíos, reintentando...');
          setTimeout(() => extractTextFromPDF(), 500);
          return;
        }
        
        const initialAnnotations = [];
        const processedFields = new Set();
        
        // Primero, procesar SOLO los 3 campos que necesitamos, en orden de prioridad
        const targetFieldNames = ['Identificación', 'Correo electrónico_2', 'Teléfono_2'];
        
        // Procesar primero los campos objetivo
        targetFieldNames.forEach(targetField => {
          if (targetField in result.data) {
            const value = result.data[targetField];
            const editableField = editableFields.find(f => f.key === targetField);
            
            if (editableField) {
              let processedValue = String(value || '').trim();
              // No convertir a mayúsculas el correo electrónico
              if (editableField.key.toLowerCase() !== 'email' && 
                  editableField.key.toLowerCase() !== 'correo electrónico_2' &&
                  editableField.key.toLowerCase() !== 'correo electrónico') {
                processedValue = processedValue.toUpperCase();
              }
              
              initialAnnotations.push({
                id: Date.now() + Math.random(),
                field: editableField.key,
                text: processedValue,
                x: editableField.x,
                y: editableField.y
              });
              console.log(`✅ Campo objetivo mapeado: "${targetField}" = "${processedValue}"`);
            }
          } else {
            console.log(`⚠️ Campo objetivo no encontrado: "${targetField}"`);
          }
        });
        
        // Ahora procesar el resto de campos (por si hay variaciones)
        Object.entries(result.data).forEach(([field, value]) => {
          // Si ya procesamos este campo en la primera pasada, saltarlo
          if (targetFieldNames.includes(field)) {
            return;
          }
          
          console.log(`📝 Procesando campo adicional: "${field}" = "${value}"`);
          
          // IGNORAR explícitamente "Teléfono" sin _2
          if (field === 'Teléfono' && !field.includes('_2')) {
            console.log(`   ⏭️ Ignorando campo "Teléfono" (sin _2)`);
            return;
          }
          
          let editableField = null;
          
          // Solo buscar mapeo si el campo tiene "_2" o es una variación válida
          if (field.includes('_2') || field.toLowerCase().includes('telefono2') || field.toLowerCase().includes('teléfono2')) {
            editableField = editableFields.find(f => f.key === 'Teléfono_2');
            if (editableField) {
              // Verificar que no existe ya
              const exists = initialAnnotations.find(a => a.field === 'Teléfono_2');
              if (!exists) {
                let processedValue = String(value || '').trim().toUpperCase();
                initialAnnotations.push({
                  id: Date.now() + Math.random(),
                  field: editableField.key,
                  text: processedValue,
                  x: editableField.x,
                  y: editableField.y
                });
                console.log(`✅ Campo adicional mapeado a Teléfono_2: "${field}" = "${processedValue}"`);
              }
            }
          }
          
        });
        
        console.log(`📊 Total de anotaciones creadas: ${initialAnnotations.length}`);
        console.log('📝 Anotaciones finales:', initialAnnotations);
        
        // Verificar que tenemos los 3 campos
        const foundFields = initialAnnotations.map(a => a.field);
        const missingFields = editableFields.filter(f => !foundFields.includes(f.key));
        if (missingFields.length > 0) {
          console.warn(`⚠️ Campos faltantes: ${missingFields.map(f => f.key).join(', ')}`);
          console.log('🔍 Intentando crear campos faltantes con valores vacíos...');
          missingFields.forEach(field => {
            initialAnnotations.push({
              id: Date.now() + Math.random(),
              field: field.key,
              text: '',
              x: field.x,
              y: field.y
            });
          });
          console.log(`✅ Campos faltantes añadidos. Total ahora: ${initialAnnotations.length}`);
        }
        
        setAnnotations(initialAnnotations);
        setExtracting(false);
      } else {
        setError('No se pudieron extraer campos del PDF');
        setExtracting(false);
      }
    } catch (err) {
      console.error('Error extrayendo campos:', err);
      setError('Error al extraer campos del PDF');
      setExtracting(false);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setAnnotations([]);
    setCurrentAnnotation(null);
  };

  const handleSave = async () => {
    if (!pdfBytes) return;

    const validAnnotations = annotations.filter(annotation => annotation.text && annotation.text.trim());
    if (validAnnotations.length === 0) {
      setError('No hay cambios para guardar. Escribe algo en los campos.');
      return;
    }

    setSaving(true);
    setError('');

    try {
      const fieldUpdates = {};
      validAnnotations.forEach(annotation => {
        fieldUpdates[annotation.field] = annotation.text;
      });
      
      const result = await templateService.editTemplatePDF(templateId, fieldUpdates);
      
      if (result.success) {
        handleClose();
        alert('✅ PDF de plantilla guardado correctamente');
        onSave && onSave();
      } else {
        const errorMsg = String(result.error) || 'Error al guardar el PDF';
        setError(errorMsg);
        alert('❌ ' + errorMsg);
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
            {isEditing ? 'Editor de PDF - Plantilla' : 'Visualizador de PDF'}
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

export default TemplatePDFEditor;
