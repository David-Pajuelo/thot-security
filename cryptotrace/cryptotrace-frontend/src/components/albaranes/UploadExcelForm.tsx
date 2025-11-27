"use client";

import { useState, useCallback } from "react";
import { uploadExcel } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Upload, AlertCircle, CheckCircle2 } from "lucide-react";
import { useRouter } from "next/navigation";

export default function UploadExcelForm() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info' | null; text: string }>({ type: null, text: '' });
  const router = useRouter();

  const validateAndSetFile = (file: File) => {
    if (!file.name.match(/\.(xlsx|xls)$/)) {
      setMessage({ type: 'error', text: 'Por favor, selecciona un archivo Excel válido (.xlsx o .xls)' });
      return;
    }
    setFile(file);
    setMessage({ type: 'info', text: `Archivo seleccionado: ${file.name}` });
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  };

  const handleDragEnter = useCallback((e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      validateAndSetFile(droppedFile);
    }
  }, []);

  const handleUpload = async () => {
    if (!file) {
      setMessage({ type: 'error', text: 'Por favor, selecciona un archivo Excel.' });
      return;
    }

    try {
      setLoading(true);
      setMessage({ type: 'info', text: 'Subiendo archivo...' });
      
      const response = await uploadExcel(file);
      console.log("📢 Respuesta del backend:", response);
      
      setMessage({ type: 'success', text: 'Archivo procesado correctamente.' });
      
      setTimeout(() => {
        router.push('/albaranes/gestion-linea-temporal');
      }, 2000);
      
    } catch (error) {
      console.error("📢 Error al subir archivo:", error);
      setMessage({ type: 'error', text: 'Error al procesar el archivo. Por favor, inténtalo de nuevo.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-8 rounded-lg shadow-md">
      <h1 className="text-2xl font-bold mb-6">Subir Archivo Excel</h1>
      
      <div className="mb-6">
        <div className="flex items-center justify-center w-full">
          <label 
            className={`flex flex-col items-center justify-center w-full h-32 border-2 ${
              isDragging 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-300 bg-gray-50 hover:bg-gray-100'
            } border-dashed rounded-lg cursor-pointer transition-colors duration-200`}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <Upload className={`w-10 h-10 mb-3 ${isDragging ? 'text-blue-500' : 'text-gray-400'}`} />
              <p className="mb-2 text-sm text-gray-500">
                <span className="font-semibold">Haz click para seleccionar</span> o arrastra y suelta
              </p>
              <p className="text-xs text-gray-500">Excel (.xlsx, .xls)</p>
            </div>
            <input
              type="file"
              className="hidden"
              accept=".xlsx,.xls"
              onChange={handleFileChange}
            />
          </label>
        </div>
      </div>

      {message.text && (
        <div className={`mb-6 p-4 rounded-md flex items-center gap-2 ${
          message.type === 'error' ? 'bg-red-100 text-red-700' :
          message.type === 'success' ? 'bg-green-100 text-green-700' :
          'bg-blue-100 text-blue-700'
        }`}>
          {message.type === 'error' && <AlertCircle className="w-5 h-5" />}
          {message.type === 'success' && <CheckCircle2 className="w-5 h-5" />}
          {message.type === 'info' && <Upload className="w-5 h-5" />}
          <p>{message.text}</p>
        </div>
      )}

      <div className="flex justify-end gap-4">
        <Button
          variant="outline"
          onClick={() => router.push('/albaranes')}
          className="px-4 py-2"
        >
          Cancelar
        </Button>
        <Button
          onClick={handleUpload}
          disabled={!file || loading}
          className={`px-4 py-2 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {loading ? 'Procesando...' : 'Subir Archivo'}
        </Button>
      </div>
    </div>
  );
} 