"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Upload, History, FileText } from "lucide-react";
import Link from "next/link";
import { fetchProductosAgrupados } from "@/lib/api";

export default function AlbaranesActions() {
  const [tieneProductos, setTieneProductos] = useState(false);

  useEffect(() => {
    const verificarProductos = async () => {
      try {
        const data = await fetchProductosAgrupados();
        setTieneProductos(data && Array.isArray(data.productos) && data.productos.length > 0);
      } catch (error) {
        console.error('Error al verificar productos:', error);
      }
    };

    verificarProductos();
  }, []);

  return (
    <div className="flex justify-between items-center mb-6">
      <h1 className="text-4xl font-bold">📄 Acciones de Entrada</h1>
      <div className="flex gap-4">
        <Link href="/albaranes/upload-ac21" className="focus:outline-none">
          <Button
            className="bg-purple-500 text-white px-4 py-2 rounded-md flex items-center gap-2 hover:bg-purple-600 transition shadow-md"
            aria-label="Subir AC21"
          >
            <FileText className="w-5 h-5" /> Subir AC21
          </Button>
        </Link>

        <Link href="/albaranes/upload" className="focus:outline-none">
          <Button
            className="bg-green-500 text-white px-4 py-2 rounded-md flex items-center gap-2 hover:bg-green-600 transition shadow-md"
            aria-label="Subir Excel"
          >
            <Upload className="w-5 h-5" /> Subir Excel
          </Button>
        </Link>

        <Link href="/albaranes/gestion-linea-temporal" className={!tieneProductos ? 'pointer-events-none' : ''}>
          <Button
            className={`px-4 py-2 rounded-md flex items-center gap-2 transition shadow-md ${
              tieneProductos 
                ? 'bg-blue-500 hover:bg-blue-600 text-white' 
                : 'bg-gray-300 text-gray-600 cursor-not-allowed'
            }`}
            aria-label="Historial de Movimientos"
            disabled={!tieneProductos}
            title={!tieneProductos ? "No hay productos en la línea temporal" : ""}
          >
            <History className="w-5 h-5" /> Historial de Movimientos
          </Button>
        </Link>
      </div>
    </div>
  );
} 