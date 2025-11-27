from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class HpsTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    template_type: Optional[str] = "jefe_seguridad"  # 'jefe_seguridad' o 'jefe_seguridad_suplente'
    version: Optional[str] = "1.0"
    active: Optional[bool] = True


class HpsTemplateCreate(HpsTemplateBase):
    template_pdf: bytes


class HpsTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    template_type: Optional[str] = None
    version: Optional[str] = None
    active: Optional[bool] = None
    template_pdf: Optional[bytes] = None


class HpsTemplateResponse(HpsTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime
    template_type: str = "jefe_seguridad"  # Asegurar que siempre tenga un valor
    
    class Config:
        from_attributes = True


class HpsTemplatePDFResponse(BaseModel):
    id: int
    name: str
    version: str
    template_pdf: bytes
    created_at: datetime
    
    class Config:
        from_attributes = True


class HpsTemplateListResponse(BaseModel):
    templates: List[HpsTemplateResponse]
    total: int
    page: int
    per_page: int
