"""
Servicio para operaciones del complemento de navegador
Adaptado desde hps-system/backend/src/extension/service.py
"""
import logging
from typing import List, Optional
from django.db import connection
from .models import HpsRequest

logger = logging.getLogger(__name__)


class ExtensionService:
    """Servicio para operaciones del complemento de navegador"""
    
    @staticmethod
    def get_personas_pendientes(tipo: Optional[str] = None) -> List[dict]:
        """
        Obtener lista de personas con estado 'pending'
        
        Args:
            tipo: Filtro opcional ('solicitud' o 'traslado')
            
        Returns:
            Lista de diccionarios con datos de personas
        """
        try:
            queryset = HpsRequest.objects.filter(status='pending')
            
            # Añadir filtro por tipo si se especifica
            if tipo == 'solicitud':
                queryset = queryset.filter(request_type='new')
            elif tipo == 'traslado':
                queryset = queryset.filter(request_type='transfer')
            
            queryset = queryset.order_by('first_name', 'first_last_name')
            
            personas = []
            for hps in queryset:
                personas.append({
                    'tipo_documento': hps.document_type or '',
                    'numero_documento': hps.document_number or '',
                    'fecha_nacimiento': hps.birth_date,
                    'nombre': hps.first_name or '',
                    'primer_apellido': hps.first_last_name or '',
                    'segundo_apellido': hps.second_last_name or '',
                    'nacionalidad': hps.nationality,
                    'lugar_nacimiento': hps.birth_place,
                    'correo': hps.email,
                    'telefono': hps.phone,
                    'operacion': hps.request_type,
                    'hps_type': hps.form_type
                })
            
            return personas
            
        except Exception as e:
            logger.error(f"Error obteniendo personas pendientes: {e}")
            return []
    
    @staticmethod
    def get_persona_por_dni(numero_documento: str) -> Optional[dict]:
        """
        Obtener datos detallados de una persona por número de documento
        
        Args:
            numero_documento: Número de documento a buscar
            
        Returns:
            Diccionario con datos de la persona o None si no se encuentra
        """
        try:
            hps = HpsRequest.objects.filter(document_number=numero_documento).first()
            
            if not hps:
                return None
            
            return {
                'tipo_documento': hps.document_type or '',
                'numero_documento': hps.document_number or '',
                'fecha_nacimiento': hps.birth_date,
                'nombre': hps.first_name or '',
                'primer_apellido': hps.first_last_name or '',
                'segundo_apellido': hps.second_last_name or '',
                'nacionalidad': hps.nationality,
                'lugar_nacimiento': hps.birth_place,
                'correo': hps.email,
                'telefono': hps.phone,
                'operacion': hps.request_type,
                'estado': hps.status or ''
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo persona por DNI {numero_documento}: {e}")
            return None
    
    @staticmethod
    def actualizar_estado_solicitud(numero_documento: str, nuevo_estado: str) -> dict:
        """
        Actualizar estado de una solicitud
        
        Args:
            numero_documento: Número de documento
            nuevo_estado: Nuevo estado a asignar
            
        Returns:
            Diccionario con success y message
        """
        try:
            hps = HpsRequest.objects.filter(document_number=numero_documento).first()
            
            if not hps:
                return {
                    'success': False,
                    'message': f'No se encontró solicitud con DNI {numero_documento}'
                }
            
            hps.status = nuevo_estado
            hps.save(update_fields=['status', 'updated_at'])
            
            logger.info(f"Estado actualizado a '{nuevo_estado}' para DNI {numero_documento}")
            
            return {
                'success': True,
                'message': f"Estado actualizado a '{nuevo_estado}' para DNI {numero_documento}"
            }
                
        except Exception as e:
            logger.error(f"Error actualizando estado para DNI {numero_documento}: {e}")
            return {
                'success': False,
                'message': f'Error actualizando estado: {str(e)}'
            }

