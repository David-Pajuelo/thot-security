"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { ArrowLeft, FileText } from "lucide-react";
import { Albaran } from "@/lib/types";
import { fetchAlbaranById } from "@/lib/api";
import AlbaranMovimientos from "./AlbaranMovimientos";
import AC21Detail from "./AC21Detail";

// Función para formatear la fecha
const formatearFecha = (fecha: string) => {
  const date = new Date(fecha);
  return date.toLocaleString('es-ES', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

interface AlbaranDetailProps {
  id: string;
}

export default function AlbaranDetail({ id }: AlbaranDetailProps) {
  const router = useRouter();
  const [albaran, setAlbaran] = useState<Albaran | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const cargarAlbaran = async () => {
      try {
        setLoading(true);
        const data = await fetchAlbaranById(id);
        setAlbaran(data);
      } catch (error: any) {
        console.error("❌ Error cargando albarán:", error);
        // Verificar si es un error 404
        if (error.message?.includes('404') || error.message?.includes('No Albaran matches')) {
          setError(`El albarán con ID ${id} no existe en la base de datos.`);
        } else {
          setError("Error al cargar el albarán. Por favor, inténtalo de nuevo.");
        }
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      cargarAlbaran();
    }
  }, [id]);

  if (loading) return (
    <div className="container mx-auto py-6">
      <p className="text-gray-500 text-center">Cargando albarán...</p>
    </div>
  );
  
  if (error) return (
    <div className="container mx-auto py-6">
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600 text-center">{error}</p>
        <div className="mt-4 text-center">
          <Button 
            variant="outline" 
            onClick={() => router.push("/albaranes")}
            className="flex items-center gap-2 mx-auto"
          >
            <ArrowLeft className="w-4 h-4" /> 
            Volver a la lista
          </Button>
        </div>
      </div>
    </div>
  );

  if (!albaran) return <p className="text-gray-500 text-center">Albarán no encontrado.</p>;

  // Detectar si es un AC21 basándose en la presencia de empresas origen y destino
  // Los AC21 siempre tienen empresas asignadas, los albaranes Excel no
  const isAC21 = albaran.empresa_origen && albaran.empresa_destino;

  // Si es un AC21, usar el componente específico
  if (isAC21) {
    const handleBack = () => {
      // Navegar a la página correcta según el tipo de AC21
      if (albaran.direccion_transferencia === 'SALIDA') {
        router.push("/salidas/albaranes");
      } else {
        router.push("/albaranes"); // Por defecto, entradas
      }
    };

    return (
      <AC21Detail 
        albaran={albaran} 
        onBack={handleBack} 
      />
    );
  }

  // Vista tradicional para albaranes importados desde Excel
  return (
    <div className="container mx-auto py-6">
      {/* Información principal del albarán */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <FileText className="w-8 h-8 text-green-500" />
            <h1 className="text-2xl font-bold">Albarán {albaran.numero}</h1>
          </div>
          <Button 
            variant="outline" 
            onClick={() => router.push("/albaranes")}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" /> 
            Volver a la lista
          </Button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-500">Número</p>
            <p className="text-lg font-semibold">{albaran.numero}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-500">Fecha</p>
            <p className="text-lg font-semibold">{formatearFecha(albaran.fecha)}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-500">Tipo</p>
            <p className="text-lg font-semibold">{albaran.tipo_entrada}</p>
          </div>
        </div>
      </div>

      {/* Sección para la lista de movimientos */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">Movimientos del Albarán</h2>
        <AlbaranMovimientos albaranId={id} />
      </div>
    </div>
  );
} 