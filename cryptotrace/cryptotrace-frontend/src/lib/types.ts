export interface Producto {
  id?: number;
  codigo_producto: string;
  descripcion: string;
  tipo?: string;
  tipo_nombre?: string;
  part_number?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Albaran {
  id: number;
  numero_registro: string;
  tipo_documento: string;
  fecha_documento: string;
  empresa_origen?: Empresa;
  empresa_destino?: Empresa;
  estado_material: string;
  documento_principal?: number;
  created_at?: string;
  updated_at?: string;
}

export interface Empresa {
  id: number;
  nombre: string;
  codigo?: string;
  direccion?: string;
  ciudad?: string;
  codigo_postal?: string;
  provincia?: string;
  numero_odmc?: string;
  activa: boolean;
  created_at?: string;
  updated_at?: string;
}

/** Campos editables de empresa en AC21 (origen/destino) */
export interface EmpresaEditable {
  nombre: string;
  direccion: string;
  ciudad: string;
  codigo_postal: string;
  provincia: string;
  numero_odmc: string;
}

export interface Cryptocustodio {
  id: number;
  empleo_rango: string | null;
  nombre_apellidos: string;
  cargo: string | null;
  empresa: number;
  empresa_nombre?: string;
}

export interface ProductoCatalogo {
  id: number;
  codigo_producto: string;
  descripcion: string;
  tipo?: string;
  tipo_nombre?: string;
}

