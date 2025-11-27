"use client";

import { useEffect, useState } from "react";
import { fetchProductos, fetchProductosAgrupados, crearProductoCatalogo, fetchTiposProducto } from "@/lib/api";
import { Producto } from "@/lib/types";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { ArrowUpDown, Search } from "lucide-react";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

export default function ProductosTable() {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortColumn, setSortColumn] = useState<keyof Producto | null>(null);
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [showForm, setShowForm] = useState(false);
  const [tiposDisponibles, setTiposDisponibles] = useState<{id:number, nombre:string}[]>([]);
  const [form, setForm] = useState({ codigo: "", descripcion: "", tipo: "" });
  const [formError, setFormError] = useState<string | null>(null);
  const [formLoading, setFormLoading] = useState(false);

  useEffect(() => {
    fetchProductos()
      .then((data) => {
        setProductos(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error al obtener productos:", err);
        setError("Error al cargar el catálogo de productos");
        setLoading(false);
      });
    // Obtener tipos disponibles para el formulario
    fetchTiposProducto()
      .then((tipos) => {
        setTiposDisponibles(tipos);
      })
      .catch(() => setTiposDisponibles([]));
  }, []);

  const handleSort = (column: keyof Producto) => {
    if (sortColumn === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(column);
      setSortOrder("asc");
    }
  };

  const filteredProductos = productos.filter((prod) =>
    [prod.codigo_producto, prod.descripcion, prod.tipo_nombre]
      .join(" ")
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
  );

  const sortedProductos = [...filteredProductos].sort((a, b) => {
    if (!sortColumn) return 0;
    const valueA = a[sortColumn] || "";
    const valueB = b[sortColumn] || "";

    return sortOrder === "asc"
      ? valueA.toString().localeCompare(valueB.toString(), "es", { numeric: true })
      : valueB.toString().localeCompare(valueA.toString(), "es", { numeric: true });
  });

  if (loading) return <p className="text-center text-gray-500">Cargando catálogo de productos...</p>;
  if (error) return <p className="text-center text-red-500">{error}</p>;

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-4xl font-bold text-center mb-6">Catálogo de Productos</h1>
      <div className="flex justify-between mb-4">
        <Button onClick={() => setShowForm(true)} className="bg-blue-600 text-white px-4 py-2 rounded-md">+ Nuevo producto</Button>
        <div className="relative">
          <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
          <Input
            type="text"
            placeholder="Buscar en el catálogo..."
            className="pl-10 pr-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>
      {/* Formulario modal */}
      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent>
          <DialogTitle>Nuevo producto en catálogo</DialogTitle>
          <DialogDescription>
            Rellena los campos para dar de alta un nuevo producto en el catálogo.
          </DialogDescription>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setFormError(null);
              setFormLoading(true);
              try {
                if (!form.codigo || !form.tipo) {
                  setFormError("El código y el tipo son obligatorios");
                  setFormLoading(false);
                  return;
                }
                await crearProductoCatalogo({ codigo_producto: form.codigo, descripcion: form.descripcion, tipo: form.tipo });
                setShowForm(false);
                setForm({ codigo: "", descripcion: "", tipo: "" });
                setFormLoading(false);
                // Recargar productos
                setLoading(true);
                const data = await fetchProductos();
                setProductos(data);
                setLoading(false);
              } catch (err: any) {
                setFormError(err.message || "Error al crear el producto");
                setFormLoading(false);
              }
            }}
            className="flex flex-col gap-4 mt-4"
          >
            <label className="flex flex-col gap-1">
              Código de producto*
              <Input value={form.codigo} onChange={e => setForm(f => ({ ...f, codigo: e.target.value }))} required />
            </label>
            <label className="flex flex-col gap-1">
              Descripción
              <Input value={form.descripcion} onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))} />
            </label>
            <label className="flex flex-col gap-1">
              Tipo*
              <select value={form.tipo} onChange={e => setForm(f => ({ ...f, tipo: e.target.value }))} required className="border rounded px-2 py-1">
                <option value="">Selecciona un tipo</option>
                {tiposDisponibles.map(tipo => (
                  <option key={tipo.id} value={tipo.id}>{tipo.nombre}</option>
                ))}
              </select>
            </label>
            {formError && <p className="text-red-500 text-sm">{formError}</p>}
            <Button type="submit" disabled={formLoading}>{formLoading ? "Guardando..." : "Guardar"}</Button>
          </form>
        </DialogContent>
      </Dialog>
      <div className="overflow-x-auto">
        <Table className="w-full border border-gray-300">
          <TableHeader>
            <TableRow className="bg-gray-100">
              <TableHead className="px-4 py-2 text-left cursor-pointer" onClick={() => handleSort("codigo_producto")}>
                Código de Producto <ArrowUpDown className="inline-block w-4 h-4" />
              </TableHead>
              <TableHead className="px-4 py-2 text-left cursor-pointer" onClick={() => handleSort("descripcion")}>
                Descripción <ArrowUpDown className="inline-block w-4 h-4" />
              </TableHead>
              <TableHead className="px-4 py-2 text-left cursor-pointer" onClick={() => handleSort("tipo_nombre")}>
                Tipo <ArrowUpDown className="inline-block w-4 h-4" />
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedProductos.length > 0 ? (
              sortedProductos.map((prod) => (
                <TableRow key={prod.id} className="border-t">
                  <TableCell className="px-4 py-2">{prod.codigo_producto}</TableCell>
                  <TableCell className="px-4 py-2">{prod.descripcion || "Sin descripción"}</TableCell>
                  <TableCell className="px-4 py-2">{prod.tipo_nombre || "No asignado"}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={3} className="text-center text-gray-500 py-4">
                  No hay productos en el catálogo.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
} 