import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import { Info, ArrowRight, X } from 'lucide-react';

interface AC21EntradaModalProps {
  isOpen: boolean;
  onClose: () => void;
  onIrALineaTemporal: () => void;
}

export default function AC21EntradaModal({
  isOpen,
  onClose,
  onIrALineaTemporal
}: AC21EntradaModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader className="pb-4">
          <DialogTitle className="flex items-center gap-3 text-lg">
            <div className="p-2 bg-blue-100 rounded-full">
              <Info className="h-5 w-5 text-blue-600" />
            </div>
            AC21 de Entrada - Tipificación Requerida
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Mensaje principal */}
          <Alert className="border-blue-200 bg-blue-50">
            <Info className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800">
              Este AC21 es de <strong className="font-semibold">ENTRADA</strong> y requiere 
              que los productos sean tipificados antes de guardarse definitivamente.
            </AlertDescription>
          </Alert>

          {/* Información del proceso */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-3">Proceso de tipificación:</h3>
            
            <ol className="list-decimal list-inside space-y-2 text-sm text-gray-700">
              <li>Los productos se guardarán temporalmente en la línea temporal</li>
              <li>Deberás asignar el tipo de cada producto (C, CC, etc.)</li>
              <li>Una vez tipificados, podrás procesar el albarán definitivamente</li>
            </ol>
          </div>

          {/* Nota importante */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
            <p className="text-sm text-amber-800">
              <strong>Nota:</strong> El albarán no se creará hasta que todos los productos 
              estén tipificados en la línea temporal.
            </p>
          </div>
        </div>

        <DialogFooter className="flex-col gap-3 pt-6">
          <Button 
            onClick={onIrALineaTemporal}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white"
            size="lg"
          >
            <ArrowRight className="h-4 w-4 mr-2" />
            Ir a la Línea Temporal para Tipificar
          </Button>
          
          <Button 
            variant="outline" 
            onClick={onClose}
            className="w-full border-gray-300 hover:bg-gray-50"
            size="lg"
          >
            <X className="h-4 w-4 mr-2" />
            Cancelar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

