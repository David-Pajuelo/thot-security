# Router para endpoints del complemento de navegador
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.database.database import get_db
from src.extension.service import ExtensionService
from src.extension.schemas import PersonaListResponse, PersonaDetailResponse, UpdateEstadoRequest, UpdateEstadoResponse

router = APIRouter(prefix="/api/v1/extension", tags=["Extension"])

@router.get("/personas", response_model=List[PersonaListResponse])
async def get_personas_pendientes(
    tipo: str = None,
    db: Session = Depends(get_db)
):
    """
    Obtener lista de personas con estado 'pending' para el complemento de navegador
    """
    try:
        service = ExtensionService(db)
        personas = service.get_personas_pendientes(tipo)
        return personas
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo personas: {str(e)}"
        )

@router.get("/persona/{numero_documento}", response_model=PersonaDetailResponse)
async def get_persona_por_dni(numero_documento: str, db: Session = Depends(get_db)):
    """
    Obtener datos detallados de una persona por número de documento
    """
    try:
        service = ExtensionService(db)
        persona = service.get_persona_por_dni(numero_documento)
        
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró persona con DNI {numero_documento}"
            )
        
        return persona
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo persona: {str(e)}"
        )

@router.put("/solicitud/{numero_documento}/estado", response_model=UpdateEstadoResponse)
async def actualizar_estado_solicitud(
    numero_documento: str,
    request: UpdateEstadoRequest,
    db: Session = Depends(get_db)
):
    """
    Actualizar estado de una solicitud HPS
    """
    try:
        service = ExtensionService(db)
        result = service.actualizar_estado_solicitud(numero_documento, request.estado)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando estado: {str(e)}"
        )

@router.put("/solicitud/{numero_documento}/enviada", response_model=UpdateEstadoResponse)
async def marcar_solicitud_enviada(numero_documento: str, db: Session = Depends(get_db)):
    """
    Marcar solicitud como enviada (cambiar estado a 'submitted')
    """
    try:
        service = ExtensionService(db)
        result = service.actualizar_estado_solicitud(numero_documento, "submitted")
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marcando solicitud como enviada: {str(e)}"
        )

@router.put("/traslado/{numero_documento}/enviado", response_model=UpdateEstadoResponse)
async def marcar_traslado_enviado(numero_documento: str, db: Session = Depends(get_db)):
    """
    Marcar traslado como enviado (cambiar estado a 'submitted')
    """
    try:
        service = ExtensionService(db)
        result = service.actualizar_estado_solicitud(numero_documento, "submitted")
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marcando traslado como enviado: {str(e)}"
        )

@router.get("/traslado/{numero_documento}/pdf")
async def descargar_pdf_traslado(numero_documento: str, db: Session = Depends(get_db)):
    """
    Descargar PDF de traslado por número de documento
    """
    try:
        from src.models.hps import HPSRequest
        from fastapi.responses import StreamingResponse
        import io
        import re
        
        # Buscar solicitud de traslado por DNI
        hps_request = db.query(HPSRequest).filter(
            HPSRequest.document_number == numero_documento,
            HPSRequest.type == 'traslado',
            HPSRequest.status == 'pending'
        ).first()
        
        if not hps_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traslado no encontrado o no está pendiente"
            )
        
        if not hps_request.filled_pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay PDF rellenado para este traslado"
            )
        
        # Generar nombre del archivo
        user_name = f"{hps_request.first_name} {hps_request.first_last_name}".strip()
        if hps_request.second_last_name:
            user_name += f" {hps_request.second_last_name}"
        
        # Limpiar caracteres no válidos
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', user_name)
        filename = f"{safe_name} - Traslado HPS.pdf"
        
        return StreamingResponse(
            io.BytesIO(hps_request.filled_pdf),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error descargando PDF: {str(e)}"
        )

