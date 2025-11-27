"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useParams } from "next/navigation";
import { fetchProductoById } from "@/lib/api"; // Función para obtener un solo producto
import { Producto } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Package, ArrowLeft } from "lucide-react"; // Íconos

export default function ProductoDetalles() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [producto, setProducto] = useState<Producto | null>(null);

  useEffect(() => {
    if (id) {
      fetchProductoById(id)
        .then(setProducto)
        .catch(console.error);
    }
  }, [id]);

  if (!producto) {
    return <p className="text-center text-gray-500 mt-10">Cargando producto...</p>;
  }

  return (
    <div className="max-w-2xl mx-auto py-10">
      <Card className="shadow-lg border border-gray-200">
        <CardHeader className="flex items-center gap-4">
          <Package className="w-10 h-10 text-blue-500" />
          <CardTitle className="text-xl font-bold">{producto.codigo_producto}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600 text-lg">{producto.descripcion}</p>
          <div className="flex justify-between mt-6">
            {/* Botón de Volver usando useRouter */}
            <Button variant="outline" onClick={() => router.push("/productos")}>
              <ArrowLeft className="w-4 h-4 mr-2" /> Volver
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
