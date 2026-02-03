"use client";

import { useState, useEffect } from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { PlusCircle, Edit, Trash, AlertTriangle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Empresa } from "@/lib/types";
import { Cryptocustodio } from "@/lib/types";
import { fetchCryptocustodios, deleteCryptocustodio } from "@/lib/api";
import CryptocustodioForm from "./CryptocustodioForm";

interface CryptocustodiosModalProps {
  empresa: Empresa;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function CryptocustodiosModal({ empresa, open, onOpenChange }: CryptocustodiosModalProps) {
  const [list, setList] = useState<Cryptocustodio[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Cryptocustodio | undefined>();
  const [deleteTarget, setDeleteTarget] = useState<Cryptocustodio | null>(null);

  const loadList = async () => {
    if (!empresa?.id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCryptocustodios(empresa.id);
      setList(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open && empresa?.id) loadList();
  }, [open, empresa?.id]);

  const handleAdd = () => {
    setEditing(undefined);
    setFormOpen(true);
  };

  const handleEdit = (cc: Cryptocustodio) => {
    setEditing(cc);
    setFormOpen(true);
  };

  const handleDeleteClick = (cc: Cryptocustodio) => setDeleteTarget(cc);

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    try {
      await deleteCryptocustodio(deleteTarget.id);
      await loadList();
      setDeleteTarget(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al eliminar");
    }
  };

  const handleFormSuccess = () => {
    setFormOpen(false);
    setEditing(undefined);
    loadList();
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Cryptocustodios — {empresa?.nombre}</DialogTitle>
            <DialogDescription>
              Gestionar personas cryptocustodio asociadas a esta empresa.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="flex justify-end">
              <Button size="sm" className="flex items-center gap-2" onClick={handleAdd}>
                <PlusCircle className="w-4 h-4" />
                Añadir cryptocustodio
              </Button>
            </div>
            {loading ? (
              <p className="text-center text-gray-500">Cargando...</p>
            ) : error ? (
              <p className="text-red-500 text-sm">{error}</p>
            ) : (
              <div className="border rounded-lg overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Empleo/Rango</TableHead>
                      <TableHead>Nombre y Apellidos</TableHead>
                      <TableHead>Cargo</TableHead>
                      <TableHead className="text-right w-24">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {list.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center text-gray-500">
                          No hay cryptocustodios. Añade uno con el botón superior.
                        </TableCell>
                      </TableRow>
                    ) : (
                      list.map((cc) => (
                        <TableRow key={cc.id}>
                          <TableCell>{cc.empleo_rango ?? "-"}</TableCell>
                          <TableCell className="font-medium">{cc.nombre_apellidos}</TableCell>
                          <TableCell>{cc.cargo ?? "-"}</TableCell>
                          <TableCell className="text-right">
                            <Button variant="ghost" size="icon" onClick={() => handleEdit(cc)}>
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button variant="ghost" size="icon" className="text-red-500 hover:text-red-700" onClick={() => handleDeleteClick(cc)}>
                              <Trash className="w-4 h-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? "Editar cryptocustodio" : "Nuevo cryptocustodio"}</DialogTitle>
            <DialogDescription>
              {editing ? "Modifica los datos del cryptocustodio." : "Añade una persona cryptocustodio para esta empresa."}
            </DialogDescription>
          </DialogHeader>
          <CryptocustodioForm
            empresaId={empresa.id}
            cryptocustodio={editing}
            onSuccess={handleFormSuccess}
            onCancel={() => { setFormOpen(false); setEditing(undefined); }}
          />
        </DialogContent>
      </Dialog>

      <Dialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Confirmar eliminación
            </DialogTitle>
            <DialogDescription>
              ¿Eliminar a <span className="font-semibold">{deleteTarget?.nombre_apellidos}</span>? Esta acción no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>Cancelar</Button>
            <Button variant="destructive" onClick={handleDeleteConfirm}>Eliminar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
