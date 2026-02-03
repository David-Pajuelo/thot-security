"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Cryptocustodio } from "@/lib/types";
import { createCryptocustodio, updateCryptocustodio } from "@/lib/api";

export type CryptocustodioInitialData = {
  empleo_rango?: string;
  nombre_apellidos?: string;
  cargo?: string;
};

interface CryptocustodioFormProps {
  empresaId: number;
  cryptocustodio?: Cryptocustodio;
  /** Valores iniciales para crear (p. ej. lo que haya rellenado el OCR o el usuario en los campos de firma) */
  initialData?: CryptocustodioInitialData;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function CryptocustodioForm({ empresaId, cryptocustodio, initialData, onSuccess, onCancel }: CryptocustodioFormProps) {
  const [formData, setFormData] = useState({
    empleo_rango: cryptocustodio?.empleo_rango ?? initialData?.empleo_rango ?? "",
    nombre_apellidos: cryptocustodio?.nombre_apellidos ?? initialData?.nombre_apellidos ?? "",
    cargo: cryptocustodio?.cargo ?? initialData?.cargo ?? "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (cryptocustodio?.id) {
        await updateCryptocustodio(cryptocustodio.id, {
          empleo_rango: formData.empleo_rango || undefined,
          nombre_apellidos: formData.nombre_apellidos,
          cargo: formData.cargo || undefined,
        });
      } else {
        await createCryptocustodio({
          empresa: empresaId,
          empleo_rango: formData.empleo_rango || undefined,
          nombre_apellidos: formData.nombre_apellidos,
          cargo: formData.cargo || undefined,
        });
      }
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="empleo_rango" className="text-sm font-medium block mb-1">Empleo/Rango</label>
        <Input
          id="empleo_rango"
          value={formData.empleo_rango}
          onChange={(e) => setFormData((p) => ({ ...p, empleo_rango: e.target.value }))}
        />
      </div>
      <div>
        <label htmlFor="nombre_apellidos" className="text-sm font-medium block mb-1">Nombre y Apellidos</label>
        <Input
          id="nombre_apellidos"
          value={formData.nombre_apellidos}
          onChange={(e) => setFormData((p) => ({ ...p, nombre_apellidos: e.target.value }))}
          required
        />
      </div>
      <div>
        <label htmlFor="cargo" className="text-sm font-medium block mb-1">Cargo</label>
        <Input
          id="cargo"
          value={formData.cargo}
          onChange={(e) => setFormData((p) => ({ ...p, cargo: e.target.value }))}
        />
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={loading}>Cancelar</Button>
        <Button type="submit" disabled={loading}>{loading ? "Guardando..." : cryptocustodio ? "Actualizar" : "Crear"}</Button>
      </div>
    </form>
  );
}
