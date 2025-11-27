"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Empresa } from "@/lib/types";
import { createEmpresa, updateEmpresa } from "@/lib/api";

interface EmpresaFormProps {
  empresa?: Empresa;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function EmpresaForm({ empresa, onSuccess, onCancel }: EmpresaFormProps) {
  const [formData, setFormData] = useState<Partial<Empresa>>(
    empresa || {
      nombre: "",
      direccion: "",
      ciudad: "",
      codigo_postal: "",
      provincia: "",
      pais: "",
      numero_odmc: "",
    }
  );

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (empresa?.id) {
        await updateEmpresa(empresa.id, formData);
      } else {
        await createEmpresa(formData as Omit<Empresa, "id">);
      }
      onSuccess();
    } catch (error) {
      setError(error instanceof Error ? error.message : "Error al guardar la empresa");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-4">
        <div>
          <label htmlFor="nombre" className="text-sm font-medium block mb-3">
            Nombre
          </label>
          <Input
            id="nombre"
            name="nombre"
            value={formData.nombre}
            onChange={handleChange}
            required
          />
        </div>

        <div>
          <label htmlFor="direccion" className="text-sm font-medium block mb-3">
            Dirección
          </label>
          <Input
            id="direccion"
            name="direccion"
            value={formData.direccion}
            onChange={handleChange}
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="codigo_postal" className="text-sm font-medium block mb-3">
              Código Postal
            </label>
            <Input
              id="codigo_postal"
              name="codigo_postal"
              value={formData.codigo_postal}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <label htmlFor="ciudad" className="text-sm font-medium block mb-3">
              Ciudad
            </label>
            <Input
              id="ciudad"
              name="ciudad"
              value={formData.ciudad}
              onChange={handleChange}
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="provincia" className="text-sm font-medium block mb-3">
              Provincia
            </label>
            <Input
              id="provincia"
              name="provincia"
              value={formData.provincia}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <label htmlFor="pais" className="text-sm font-medium block mb-3">
              País
            </label>
            <Input
              id="pais"
              name="pais"
              value={formData.pais || ''}
              onChange={handleChange}
            />
          </div>
        </div>

        <div>
          <label htmlFor="numero_odmc" className="text-sm font-medium block mb-3">
            Número ODMC
          </label>
          <Input
            id="numero_odmc"
            name="numero_odmc"
            value={formData.numero_odmc}
            onChange={handleChange}
          />
        </div>
      </div>

      {error && <p className="text-red-500 text-sm">{error}</p>}

      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={loading}>
          Cancelar
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? "Guardando..." : empresa ? "Actualizar" : "Crear"}
        </Button>
      </div>
    </form>
  );
} 