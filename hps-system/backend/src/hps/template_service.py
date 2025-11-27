from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from src.models.hps_template import HpsTemplate
from src.hps.template_schemas import HpsTemplateCreate, HpsTemplateUpdate, HpsTemplateResponse
import uuid


class HpsTemplateService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_template(self, template_data: HpsTemplateCreate) -> HpsTemplate:
        """Crear una nueva plantilla HPS. Si ya existe una activa del mismo tipo, la desactiva."""
        template_type = template_data.template_type or "jefe_seguridad"
        
        # Si la nueva plantilla va a estar activa, desactivar todas las del mismo tipo
        if template_data.active if template_data.active is not None else True:
            self.db.query(HpsTemplate).filter(
                HpsTemplate.template_type == template_type,
                HpsTemplate.active == True
            ).update({"active": False})
            self.db.commit()
        
        db_template = HpsTemplate(
            name=template_data.name,
            description=template_data.description,
            template_pdf=template_data.template_pdf,
            template_type=template_type,
            version=template_data.version or "1.0",
            active=template_data.active if template_data.active is not None else True
        )
        
        self.db.add(db_template)
        self.db.commit()
        self.db.refresh(db_template)
        return db_template
    
    def get_template(self, template_id: int) -> Optional[HpsTemplate]:
        """Obtener una plantilla por ID"""
        template = self.db.query(HpsTemplate).filter(HpsTemplate.id == template_id).first()
        if template and (not hasattr(template, 'template_type') or not template.template_type):
            template.template_type = 'jefe_seguridad'
        return template
    
    def get_active_template(self, template_type: str = None) -> Optional[HpsTemplate]:
        """Obtener la plantilla activa actual (opcionalmente filtrada por tipo)"""
        query = self.db.query(HpsTemplate).filter(HpsTemplate.active == True)
        if template_type:
            query = query.filter(
                (HpsTemplate.template_type == template_type) | 
                (HpsTemplate.template_type == None)
            )
        template = query.first()
        if template and (not hasattr(template, 'template_type') or not template.template_type):
            template.template_type = 'jefe_seguridad'
        return template
    
    def get_template_by_type(self, template_type: str) -> Optional[HpsTemplate]:
        """Obtener la plantilla activa de un tipo específico"""
        template = self.db.query(HpsTemplate).filter(
            and_(
                HpsTemplate.active == True,
                (HpsTemplate.template_type == template_type) | 
                (HpsTemplate.template_type == None)
            )
        ).first()
        if template and (not hasattr(template, 'template_type') or not template.template_type):
            template.template_type = 'jefe_seguridad'
        return template
    
    def get_templates(self, page: int = 1, per_page: int = 10, active: bool = None) -> dict:
        """Obtener todas las plantillas con paginación"""
        query = self.db.query(HpsTemplate)
        
        # Filtrar por estado activo si se especifica
        if active is not None:
            query = query.filter(HpsTemplate.active == active)
        
        # Contar total de registros
        total = query.count()
        
        # Aplicar paginación
        offset = (page - 1) * per_page
        templates = query.order_by(HpsTemplate.created_at.desc()).offset(offset).limit(per_page).all()
        
        # Asegurar que todas las plantillas tengan template_type
        for template in templates:
            if not hasattr(template, 'template_type') or not template.template_type:
                template.template_type = 'jefe_seguridad'
        
        return {
            "templates": templates,
            "total": total,
            "page": page,
            "per_page": per_page
        }
    
    def update_template(self, template_id: int, template_data: HpsTemplateUpdate) -> Optional[HpsTemplate]:
        """Actualizar una plantilla. Si se activa, desactiva las demás del mismo tipo."""
        db_template = self.get_template(template_id)
        if not db_template:
            return None
        
        update_data = template_data.dict(exclude_unset=True)
        
        # Si se está activando la plantilla, desactivar las demás del mismo tipo
        if update_data.get('active') is True:
            template_type = update_data.get('template_type') or db_template.template_type or "jefe_seguridad"
            self.db.query(HpsTemplate).filter(
                HpsTemplate.template_type == template_type,
                HpsTemplate.active == True,
                HpsTemplate.id != template_id
            ).update({"active": False})
        
        for field, value in update_data.items():
            setattr(db_template, field, value)
        
        # Asegurar que template_type tenga un valor
        if not hasattr(db_template, 'template_type') or not db_template.template_type:
            db_template.template_type = 'jefe_seguridad'
        
        self.db.commit()
        self.db.refresh(db_template)
        return db_template
    
    def delete_template(self, template_id: int) -> bool:
        """Eliminar una plantilla"""
        db_template = self.get_template(template_id)
        if not db_template:
            return False
        
        self.db.delete(db_template)
        self.db.commit()
        return True
    
    def activate_template(self, template_id: int) -> Optional[HpsTemplate]:
        """Activar una plantilla (desactivar las demás del mismo tipo)"""
        db_template = self.get_template(template_id)
        if not db_template:
            return None
        
        template_type = db_template.template_type or "jefe_seguridad"
        
        # Desactivar todas las plantillas del mismo tipo
        self.db.query(HpsTemplate).filter(
            HpsTemplate.template_type == template_type,
            HpsTemplate.active == True
        ).update({"active": False})
        
        # Activar la plantilla seleccionada
        db_template.active = True
        self.db.commit()
        self.db.refresh(db_template)
        
        return db_template
    
    def get_template_pdf(self, template_id: int) -> Optional[bytes]:
        """Obtener el PDF de una plantilla"""
        template = self.get_template(template_id)
        return template.template_pdf if template else None
