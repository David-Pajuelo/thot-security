from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import io

from src.database.database import get_db
from src.auth.dependencies import get_current_user, require_admin
from src.hps.template_service import HpsTemplateService
from src.hps.template_schemas import (
    HpsTemplateCreate, 
    HpsTemplateUpdate, 
    HpsTemplateResponse,
    HpsTemplatePDFResponse,
    HpsTemplateListResponse
)

router = APIRouter(prefix="/hps/templates", tags=["HPS Templates"])


@router.post("/", response_model=HpsTemplateResponse)
async def create_template(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    template_type: str = Form("jefe_seguridad"),
    version: Optional[str] = Form("1.0"),
    active: bool = Form(True),
    template_pdf: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_admin())
):
    """Crear una nueva plantilla HPS. Si ya existe una activa del mismo tipo, la desactiva automáticamente."""
    if template_type not in ["jefe_seguridad", "jefe_seguridad_suplente"]:
        raise HTTPException(status_code=400, detail="template_type debe ser 'jefe_seguridad' o 'jefe_seguridad_suplente'")
    
    template_service = HpsTemplateService(db)
    
    # Leer el archivo PDF
    pdf_content = await template_pdf.read()
    
    # Manejar strings vacíos como None
    description_value = None
    if description:
        description_stripped = description.strip()
        description_value = description_stripped if description_stripped else None
    
    version_value = "1.0"
    if version:
        version_stripped = version.strip()
        version_value = version_stripped if version_stripped else "1.0"
    
    template_data = HpsTemplateCreate(
        name=name,
        description=description_value,
        template_type=template_type,
        version=version_value,
        active=active,
        template_pdf=pdf_content
    )
    
    return template_service.create_template(template_data)


@router.get("/", response_model=HpsTemplateListResponse)
async def get_templates(
    page: int = 1,
    per_page: int = 10,
    active: bool = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin())
):
    """Obtener todas las plantillas"""
    template_service = HpsTemplateService(db)
    return template_service.get_templates(page=page, per_page=per_page, active=active)


@router.get("/active", response_model=HpsTemplateResponse)
async def get_active_template(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin())
):
    """Obtener la plantilla activa actual"""
    template_service = HpsTemplateService(db)
    template = template_service.get_active_template()
    if not template:
        raise HTTPException(status_code=404, detail="No hay plantilla activa")
    return template


@router.get("/{template_id}", response_model=HpsTemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin())
):
    """Obtener una plantilla por ID"""
    template_service = HpsTemplateService(db)
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return template


@router.get("/{template_id}/pdf")
async def get_template_pdf(
    template_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin())
):
    """Descargar el PDF de una plantilla"""
    template_service = HpsTemplateService(db)
    pdf_content = template_service.get_template_pdf(template_id)
    if not pdf_content:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    return StreamingResponse(
        io.BytesIO(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=template_{template_id}.pdf"}
    )


@router.put("/{template_id}", response_model=HpsTemplateResponse)
async def update_template(
    template_id: int,
    template_data: HpsTemplateUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin())
):
    """Actualizar una plantilla (solo metadatos)"""
    template_service = HpsTemplateService(db)
    template = template_service.update_template(template_id, template_data)
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return template


@router.put("/{template_id}/pdf", response_model=HpsTemplateResponse)
async def update_template_with_pdf(
    template_id: int,
    name: str = Form(...),
    description: str = Form(None),
    template_type: str = Form(None),
    version: str = Form(None),
    active: bool = Form(None),
    template_pdf: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_admin())
):
    """Actualizar una plantilla incluyendo el PDF"""
    if template_type and template_type not in ["jefe_seguridad", "jefe_seguridad_suplente"]:
        raise HTTPException(status_code=400, detail="template_type debe ser 'jefe_seguridad' o 'jefe_seguridad_suplente'")
    
    template_service = HpsTemplateService(db)
    
    # Leer el archivo PDF
    pdf_content = await template_pdf.read()
    
    # Crear datos de actualización
    update_data = HpsTemplateUpdate(
        name=name,
        description=description,
        template_type=template_type,
        version=version,
        active=active,
        template_pdf=pdf_content
    )
    
    template = template_service.update_template(template_id, update_data)
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return template


@router.put("/{template_id}/activate", response_model=HpsTemplateResponse)
async def activate_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin())
):
    """Activar una plantilla"""
    template_service = HpsTemplateService(db)
    template = template_service.activate_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin())
):
    """Eliminar una plantilla"""
    template_service = HpsTemplateService(db)
    success = template_service.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return {"message": "Plantilla eliminada correctamente"}


@router.get("/{template_id}/extract-pdf-fields")
async def extract_template_pdf_fields(
    template_id: int,
    list_only: bool = False,  # Si es True, solo devuelve los nombres de los campos
    db: Session = Depends(get_db),
    current_user = Depends(require_admin())
):
    """Extraer campos del PDF de una plantilla usando PyMuPDF
    
    Args:
        list_only: Si es True, solo devuelve una lista con los nombres de los campos (sin valores)
    """
    try:
        from src.hps.pdf_service import PDFService
        
        template_service = HpsTemplateService(db)
        template = template_service.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        if not template.template_pdf:
            raise HTTPException(
                status_code=400,
                detail="La plantilla no tiene PDF"
            )
        
        # Extraer campos del PDF usando PyMuPDF
        extracted_fields = PDFService.extract_pdf_fields(template.template_pdf)
        
        # Si solo se piden los nombres, devolver solo la lista
        if list_only:
            return {"fields": list(extracted_fields.keys())}
        
        return extracted_fields
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extrayendo campos del PDF: {str(e)}"
        )


@router.post("/{template_id}/edit-pdf", response_model=HpsTemplateResponse)
async def edit_template_pdf(
    template_id: int,
    field_updates: dict,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin())
):
    """Editar campos específicos del PDF de una plantilla"""
    try:
        from src.hps.pdf_service import PDFService
        
        template_service = HpsTemplateService(db)
        template = template_service.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        if not template.template_pdf:
            raise HTTPException(
                status_code=400,
                detail="La plantilla no tiene PDF"
            )
        
        # Editar el PDF con los campos actualizados
        updated_pdf = PDFService.edit_existing_pdf(template.template_pdf, field_updates)
        
        # Actualizar el PDF de la plantilla
        template.template_pdf = updated_pdf
        db.commit()
        db.refresh(template)
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error editando PDF: {str(e)}"
        )
