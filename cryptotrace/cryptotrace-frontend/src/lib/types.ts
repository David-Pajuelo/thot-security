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
  activa: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ProductoCatalogo {
  id: number;
  codigo_producto: string;
  descripcion: string;
  tipo?: string;
  tipo_nombre?: string;
}

