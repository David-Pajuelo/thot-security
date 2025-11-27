import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import { FileText, Plus, AlertCircle, Building, Calendar, Hash, Files } from 'lucide-react';
import { Albaran } from '@/lib/types';

interface DocumentoExistenteModalProps {
  isOpen: boolean;
  onClose: () => void;
  documentoExistente: Albaran;
  numeroRegistro: string;
  onCrearNuevaPagina: () => void;
  onCrearDocumentoIndependiente: () => void;
}

export default function DocumentoExistenteModal({
  isOpen,
  onClose,
  documentoExistente,
  numeroRegistro,
  onCrearNuevaPagina,
  onCrearDocumentoIndependiente
}: DocumentoExistenteModalProps) {

  const esPrimeraVez = documentoExistente.total_paginas === 1;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader className="pb-4">
          <DialogTitle className="flex items-center gap-3 text-lg">
            <div className="p-2 bg-amber-100 rounded-full">
              <AlertCircle className="h-5 w-5 text-amber-600" />
            </div>
            Documento AC21 Existente
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Mensaje principal */}
          <Alert className="border-amber-200 bg-amber-50">
            <FileText className="h-4 w-4 text-amber-600" />
            <AlertDescription className="text-amber-800">
              Ya existe un documento AC21 con el número de registro <strong className="font-semibold">{numeroRegistro}</strong>
            </AlertDescription>
          </Alert>

          {/* Información del documento */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <FileText className="h-4 w-4 text-blue-600" />
              Documento existente
            </h3>
            
            <div className="grid grid-cols-1 gap-3">
              <div className="flex items-center gap-3">
                <Hash className="h-4 w-4 text-gray-400" />
                <div>
                  <span className="text-sm text-gray-500">Número:</span>
                  <span className="ml-2 font-mono font-medium">{documentoExistente.numero}</span>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <Calendar className="h-4 w-4 text-gray-400" />
                <div>
                  <span className="text-sm text-gray-500">Fecha:</span>
                  <span className="ml-2">{new Date(documentoExistente.fecha).toLocaleDateString('es-ES')}</span>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <Building className="h-4 w-4 text-gray-400 mt-0.5" />
                <div className="flex-1">
                  <div className="text-sm text-gray-500">Origen:</div>
                  <div className="font-medium text-sm">{documentoExistente.empresa_origen_info?.nombre}</div>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <Building className="h-4 w-4 text-gray-400 mt-0.5" />
                <div className="flex-1">
                  <div className="text-sm text-gray-500">Destino:</div>
                  <div className="font-medium text-sm">{documentoExistente.empresa_destino_info?.nombre}</div>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <Files className="h-4 w-4 text-gray-400" />
                <div>
                  <span className="text-sm text-gray-500">Páginas:</span>
                  <span className="ml-2 font-medium">{documentoExistente.total_paginas}</span>
                  <span className="ml-1 text-xs text-gray-500">
                    {esPrimeraVez ? "(página única)" : "(documento multipágina)"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Pregunta de acción */}
          <div className="text-center">
            <h3 className="font-medium text-gray-900 mb-1">¿Qué deseas hacer?</h3>
            <p className="text-sm text-gray-600">Selecciona una de las siguientes opciones:</p>
          </div>
        </div>

        <DialogFooter className="flex-col gap-3 pt-6">
          <Button 
            onClick={onCrearNuevaPagina}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white"
            size="lg"
          >
            <Plus className="h-4 w-4 mr-2" />
            Agregar como página {documentoExistente.total_paginas + 1}
          </Button>
          
          <Button 
            variant="outline" 
            onClick={onCrearDocumentoIndependiente}
            className="w-full border-gray-300 hover:bg-gray-50"
            size="lg"
          >
            <FileText className="h-4 w-4 mr-2" />
            Crear documento independiente
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
} 