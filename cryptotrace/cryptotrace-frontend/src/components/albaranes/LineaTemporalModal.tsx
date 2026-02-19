"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import GestionLineaTemporal from "./GestionLineaTemporal";

interface LineaTemporalModalProps {
  isOpen: boolean;
  onClose: () => void;
  ac21Data?: {
    cabecera: any;
    empresa_origen: any;
    empresa_destino: any;
    articulos: any[];
    accesorios: any[];
    equipos_prueba: any[];
    firmas: any;
    observaciones: string;
    imagen?: File | Blob;
  };
}

export default function LineaTemporalModal({ isOpen, onClose, ac21Data }: LineaTemporalModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="!max-w-[100vw] !max-h-[100vh] !w-screen !h-screen !m-0 !p-6 !overflow-hidden !flex !flex-col !rounded-none !left-0 !top-0 !translate-x-0 !translate-y-0">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>Tipificación de Productos</DialogTitle>
        </DialogHeader>
        <div className="flex-1 overflow-y-auto mt-4 min-h-0">
          <GestionLineaTemporal onClose={onClose} ac21Data={ac21Data} />
        </div>
      </DialogContent>
    </Dialog>
  );
}
