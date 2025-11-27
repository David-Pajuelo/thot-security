"use client";

import { useState, useEffect } from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { PlusCircle, Edit, Trash, AlertTriangle } from "lucide-react";
import { fetchEmpresas, deleteEmpresa } from "@/lib/api";
import { Empresa } from "@/lib/types";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import EmpresaForm from "./EmpresaForm";

export default function EmpresasTable() {
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedEmpresa, setSelectedEmpresa] = useState<Empresa | undefined>();
  const [empresaToDelete, setEmpresaToDelete] = useState<Empresa | undefined>();

  const loadEmpresas = async () => {
    try {
      const data = await fetchEmpresas();
      setEmpresas(data);
      setError(null);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEmpresas();
  }, []);

  const handleCreate = () => {
    setSelectedEmpresa(undefined);
    setIsDialogOpen(true);
  };

  const handleEdit = (empresa: Empresa) => {
    setSelectedEmpresa(empresa);
    setIsDialogOpen(true);
  };

  const handleDeleteClick = (empresa: Empresa) => {
    setEmpresaToDelete(empresa);
    setIsDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!empresaToDelete) return;

    try {
      await deleteEmpresa(empresaToDelete.id);
      await loadEmpresas();
      setIsDeleteDialogOpen(false);
      setEmpresaToDelete(undefined);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Error al eliminar la empresa');
    }
  };

  const handleFormSuccess = () => {
    setIsDialogOpen(false);
    loadEmpresas();
  };

  const formatDireccion = (empresa: Empresa) => {
    const partes = [
      empresa.direccion,
      empresa.codigo_postal,
      empresa.ciudad,
      empresa.provincia
    ].filter(Boolean);
    return partes.join(', ');
  };

  if (loading) return <div className="text-center p-4">Cargando empresas...</div>;
  if (error) return <div className="text-red-500 text-center p-4">{error}</div>;

  return (
    <>
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">Listado de Empresas</h2>
          <Button className="flex items-center gap-2" onClick={handleCreate}>
            <PlusCircle className="w-4 h-4" />
            Nueva Empresa
          </Button>
        </div>

        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nombre</TableHead>
                <TableHead className="w-1/3">Dirección Completa</TableHead>
                <TableHead>Número ODMC</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {empresas.map((empresa) => (
                <TableRow key={empresa.id}>
                  <TableCell className="font-medium">{empresa.nombre}</TableCell>
                  <TableCell className="whitespace-normal">
                    {formatDireccion(empresa)}
                  </TableCell>
                  <TableCell>{empresa.numero_odmc || '-'}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button variant="ghost" size="icon" onClick={() => handleEdit(empresa)}>
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="text-red-500 hover:text-red-700"
                        onClick={() => handleDeleteClick(empresa)}
                      >
                        <Trash className="w-4 h-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {empresas.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-gray-500">
                    No hay empresas registradas
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {selectedEmpresa ? 'Editar Empresa' : 'Nueva Empresa'}
            </DialogTitle>
            <DialogDescription>
              {selectedEmpresa 
                ? 'Modifica los datos de la empresa seleccionada.' 
                : 'Completa el formulario para crear una nueva empresa.'}
            </DialogDescription>
          </DialogHeader>
          <EmpresaForm
            empresa={selectedEmpresa}
            onSuccess={handleFormSuccess}
            onCancel={() => setIsDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>

      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Confirmar Eliminación
            </DialogTitle>
            <DialogDescription>
              ¿Está seguro de que desea eliminar la empresa <span className="font-semibold">{empresaToDelete?.nombre}</span>?
              <br />
              Esta acción no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setIsDeleteDialogOpen(false)}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
            >
              Eliminar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
} 