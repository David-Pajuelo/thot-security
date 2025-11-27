# Servicio para el complemento de navegador
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from src.extension.schemas import PersonaListResponse, PersonaDetailResponse, UpdateEstadoResponse

class ExtensionService:
    """Servicio para operaciones del complemento de navegador"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_personas_pendientes(self, tipo: str = None) -> List[PersonaListResponse]:
        """Obtener lista de personas con estado 'pending'"""
        try:
            # Construir consulta SQL con filtro opcional por tipo
            base_query = """
                SELECT 
                    document_type as tipo_documento,
                    document_number as numero_documento,
                    birth_date as fecha_nacimiento,
                    first_name as nombre,
                    first_last_name as primer_apellido,
                    second_last_name as segundo_apellido,
                    nationality as nacionalidad,
                    birth_place as lugar_nacimiento,
                    email as correo,
                    phone as telefono,
                    request_type as operacion,
                    type as hps_type
                FROM hps_requests 
                WHERE status = 'pending'
            """
            
            # Añadir filtro por tipo si se especifica
            if tipo == 'solicitud':
                base_query += " AND request_type = 'new'"
            elif tipo == 'traslado':
                base_query += " AND request_type = 'transfer'"
            
            base_query += " ORDER BY first_name, first_last_name"
            
            query = text(base_query)
            
            result = self.db.execute(query)
            personas = []
            
            for row in result:
                persona = PersonaListResponse(
                    tipo_documento=row.tipo_documento or "",
                    numero_documento=row.numero_documento or "",
                    fecha_nacimiento=row.fecha_nacimiento,
                    nombre=row.nombre or "",
                    primer_apellido=row.primer_apellido or "",
                    segundo_apellido=row.segundo_apellido or "",
                    nacionalidad=row.nacionalidad,
                    lugar_nacimiento=row.lugar_nacimiento,
                    correo=row.correo,
                    telefono=row.telefono,
                    operacion=row.operacion
                )
                personas.append(persona)
            
            return personas
            
        except Exception as e:
            print(f"Error obteniendo personas pendientes: {e}")
            return []
    
    def get_persona_por_dni(self, numero_documento: str) -> Optional[PersonaDetailResponse]:
        """Obtener datos detallados de una persona por número de documento"""
        try:
            query = text("""
                SELECT 
                    document_type as tipo_documento,
                    document_number as numero_documento,
                    birth_date as fecha_nacimiento,
                    first_name as nombre,
                    first_last_name as primer_apellido,
                    second_last_name as segundo_apellido,
                    nationality as nacionalidad,
                    birth_place as lugar_nacimiento,
                    email as correo,
                    phone as telefono,
                    request_type as operacion,
                    status as estado
                FROM hps_requests 
                WHERE document_number = :numero_documento
            """)
            
            result = self.db.execute(query, {"numero_documento": numero_documento})
            row = result.fetchone()
            
            if not row:
                return None
            
            return PersonaDetailResponse(
                tipo_documento=row.tipo_documento or "",
                numero_documento=row.numero_documento or "",
                fecha_nacimiento=row.fecha_nacimiento,
                nombre=row.nombre or "",
                primer_apellido=row.primer_apellido or "",
                segundo_apellido=row.segundo_apellido or "",
                nacionalidad=row.nacionalidad,
                lugar_nacimiento=row.lugar_nacimiento,
                correo=row.correo,
                telefono=row.telefono,
                operacion=row.operacion,
                estado=row.estado or ""
            )
            
        except Exception as e:
            print(f"Error obteniendo persona por DNI {numero_documento}: {e}")
            return None
    
    def actualizar_estado_solicitud(self, numero_documento: str, nuevo_estado: str) -> UpdateEstadoResponse:
        """Actualizar estado de una solicitud"""
        try:
            query = text("""
                UPDATE hps_requests 
                SET status = :nuevo_estado, updated_at = NOW()
                WHERE document_number = :numero_documento
            """)
            
            result = self.db.execute(query, {
                "numero_documento": numero_documento,
                "nuevo_estado": nuevo_estado
            })
            
            self.db.commit()
            
            if result.rowcount > 0:
                return UpdateEstadoResponse(
                    success=True,
                    message=f"Estado actualizado a '{nuevo_estado}' para DNI {numero_documento}"
                )
            else:
                return UpdateEstadoResponse(
                    success=False,
                    message=f"No se encontró solicitud con DNI {numero_documento}"
                )
                
        except Exception as e:
            self.db.rollback()
            print(f"Error actualizando estado para DNI {numero_documento}: {e}")
            return UpdateEstadoResponse(
                success=False,
                message=f"Error actualizando estado: {str(e)}"
            )
