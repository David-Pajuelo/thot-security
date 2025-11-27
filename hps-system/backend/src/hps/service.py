"""
Servicios para la gestión de solicitudes HPS (Habilitación Personal de Seguridad)
"""
import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc

from src.models.hps import HPSRequest
from src.models.user import User
from src.models.team import Team
from src.auth.schemas import UserRole
from src.hps.schemas import (
    HPSRequestCreate, HPSRequestUpdate, HPSRequestResponse,
    HPSRequestList, HPSStatsResponse, HPSRequestType, HPSStatus
)


class HPSService:
    """Servicio para gestión de solicitudes HPS"""

    @staticmethod
    def create_hps_request(
        db: Session,
        hps_data: HPSRequestCreate,
        submitted_by_user_id: uuid.UUID
    ) -> HPSRequestResponse:
        """
        Crear una nueva solicitud HPS
        """
        try:
            # Determinar el user_id para la solicitud
            target_user_id = None
            
            if hps_data.user_id:
                # Verificar que el usuario existe
                target_user = HPSService.get_user_by_id(db, hps_data.user_id)
                if not target_user:
                    raise ValueError(f"Usuario con ID {hps_data.user_id} no encontrado")
                target_user_id = target_user.id
            else:
                # Buscar usuario por email
                target_user = db.query(User).filter(User.email == hps_data.email).first()
                if target_user:
                    target_user_id = target_user.id
                else:
                    # El usuario no existe, se podría crear automáticamente o devolver error
                    # Por ahora requerimos que el usuario exista
                    raise ValueError(f"Usuario con email {hps_data.email} no encontrado. El usuario debe existir antes de crear una solicitud HPS.")

            # Verificar que no exista una solicitud activa (pendiente o enviada) para este usuario
            existing_active = db.query(HPSRequest).filter(
                and_(
                    HPSRequest.user_id == target_user_id,
                    HPSRequest.status.in_([HPSStatus.PENDING, HPSStatus.SUBMITTED])
                )
            ).first()
            
            if existing_active:
                status_text = "pendiente" if existing_active.status == HPSStatus.PENDING else "enviada y esperando respuesta"
                raise ValueError(f"Ya existe una solicitud HPS {status_text} para este usuario (ID: {existing_active.id})")

            # Mapear request_type a type
            hps_type = 'solicitud'  # Por defecto
            if hps_data.request_type == 'transfer':
                hps_type = 'traslado'
            elif hps_data.request_type in ['new', 'renewal']:
                hps_type = 'solicitud'
            
            # Crear la nueva solicitud HPS
            hps_request = HPSRequest(
                user_id=target_user_id,
                request_type=hps_data.request_type,
                type=hps_type,
                status=HPSStatus.PENDING,
                document_type=hps_data.document_type,
                document_number=hps_data.document_number,
                birth_date=hps_data.birth_date,
                first_name=hps_data.first_name,
                first_last_name=hps_data.first_last_name,
                second_last_name=hps_data.second_last_name,
                nationality=hps_data.nationality,
                birth_place=hps_data.birth_place,
                email=hps_data.email,
                phone=hps_data.phone,
                submitted_by=submitted_by_user_id
            )

            db.add(hps_request)
            db.commit()
            db.refresh(hps_request)

            # Cargar relaciones para la respuesta
            hps_request = db.query(HPSRequest).options(
                joinedload(HPSRequest.user),
                joinedload(HPSRequest.submitted_by_user),
                joinedload(HPSRequest.approved_by_user)
            ).filter(HPSRequest.id == hps_request.id).first()

            return HPSRequestResponse.from_hps_request(hps_request)

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_hps_request_by_id(
        db: Session,
        request_id: str,
        current_user: User
    ) -> Optional[HPSRequestResponse]:
        """
        Obtener una solicitud HPS por ID, con control de acceso
        """
        try:
            request_uuid = uuid.UUID(request_id)
        except ValueError:
            return None

        query = db.query(HPSRequest).options(
            joinedload(HPSRequest.user),
            joinedload(HPSRequest.submitted_by_user),
            joinedload(HPSRequest.approved_by_user)
        ).filter(HPSRequest.id == request_uuid)

        # Control de acceso según el rol del usuario
        if current_user.role.name in ["admin", "jefe_seguridad", "security_chief"]:
            # Admin y jefes de seguridad pueden ver todas las solicitudes
            pass
        elif current_user.role.name == "team_leader":
            # Team leader puede ver solicitudes de su equipo
            query = query.join(User, HPSRequest.user_id == User.id).filter(
                User.team_id == current_user.team_id
            )
        else:
            # Member solo puede ver sus propias solicitudes
            query = query.filter(HPSRequest.user_id == current_user.id)

        hps_request = query.first()
        if not hps_request:
            return None

        return HPSRequestResponse.from_hps_request(hps_request)

    @staticmethod
    def get_hps_requests(
        db: Session,
        current_user: User,
        page: int = 1,
        per_page: int = 10,
        status: Optional[HPSStatus] = None,
        request_type: Optional[HPSRequestType] = None,
        user_id: Optional[str] = None,
        hps_type: Optional[str] = None
    ) -> HPSRequestList:
        """
        Obtener lista paginada de solicitudes HPS con filtros
        """
        query = db.query(HPSRequest).options(
            joinedload(HPSRequest.user),
            joinedload(HPSRequest.submitted_by_user),
            joinedload(HPSRequest.approved_by_user)
        )

        # Control de acceso según el rol del usuario
        if current_user.role.name in ["admin", "jefe_seguridad", "security_chief"]:
            # Admin y jefes de seguridad pueden ver todas las solicitudes
            pass
        elif current_user.role.name == "team_leader":
            # Team leader puede ver solicitudes de su equipo
            query = query.join(User, HPSRequest.user_id == User.id).filter(
                User.team_id == current_user.team_id
            )
        else:
            # Member solo puede ver sus propias solicitudes
            query = query.filter(HPSRequest.user_id == current_user.id)

        # Aplicar filtros
        if status:
            print(f"DEBUG: Applying status filter: {status}")
            query = query.filter(HPSRequest.status == status)
        
        if request_type:
            print(f"DEBUG: Applying request_type filter: {request_type}")
            query = query.filter(HPSRequest.request_type == request_type)
        
        if user_id:
            try:
                user_uuid = uuid.UUID(user_id)
                query = query.filter(HPSRequest.user_id == user_uuid)
            except ValueError:
                pass

        # Filtrar por hps_type si se especifica
        if hps_type:
            query = query.filter(HPSRequest.type == hps_type)

        # Contar total de registros
        total = query.count()

        # Aplicar paginación
        offset = (page - 1) * per_page
        requests = query.order_by(desc(HPSRequest.created_at)).offset(offset).limit(per_page).all()

        # Convertir a respuestas
        request_responses = [
            HPSRequestResponse.from_hps_request(req) for req in requests
        ]

        # Calcular páginas totales
        pages = (total + per_page - 1) // per_page

        return HPSRequestList(
            requests=request_responses,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )

    @staticmethod
    def update_hps_request(
        db: Session,
        request_id: str,
        hps_data: HPSRequestUpdate,
        current_user: User
    ) -> Optional[HPSRequestResponse]:
        """
        Actualizar una solicitud HPS (solo admin o team leader)
        """
        # Solo admin y team leader pueden actualizar solicitudes
        if current_user.role.name not in ["admin", "team_leader"]:
            raise ValueError("No tienes permisos para actualizar solicitudes HPS")

        try:
            request_uuid = uuid.UUID(request_id)
        except ValueError:
            return None

        # Buscar la solicitud
        query = db.query(HPSRequest).filter(HPSRequest.id == request_uuid)
        
        # Control de acceso para team leader
        if current_user.role.name == "team_leader":
            query = query.join(User, HPSRequest.user_id == User.id).filter(
                User.team_id == current_user.team_id
            )

        hps_request = query.first()
        if not hps_request:
            return None

        try:
            # Actualizar campos
            if hps_data.status is not None:
                hps_request.status = hps_data.status
                
                # Si se aprueba o rechaza, registrar quién lo hizo y cuándo
                if hps_data.status in [HPSStatus.APPROVED, HPSStatus.REJECTED]:
                    hps_request.approved_by = current_user.id
                    hps_request.approved_at = func.now()
                    
                    # Si se aprueba y no se especifica fecha de expiración, usar 5 años
                    if hps_data.status == HPSStatus.APPROVED and not hps_data.expires_at:
                        hps_request.expires_at = date.today() + timedelta(days=1825)  # 5 años

            if hps_data.notes is not None:
                hps_request.notes = hps_data.notes

            if hps_data.expires_at is not None:
                hps_request.expires_at = hps_data.expires_at

            db.commit()
            db.refresh(hps_request)

            # Cargar relaciones para la respuesta
            hps_request = db.query(HPSRequest).options(
                joinedload(HPSRequest.user),
                joinedload(HPSRequest.submitted_by_user),
                joinedload(HPSRequest.approved_by_user)
            ).filter(HPSRequest.id == hps_request.id).first()

            return HPSRequestResponse.from_hps_request(hps_request)

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def delete_hps_request(
        db: Session,
        request_id: str,
        current_user: User
    ) -> bool:
        """
        Eliminar una solicitud HPS (solo admin)
        """
        if current_user.role.name != "admin":
            raise ValueError("Solo los administradores pueden eliminar solicitudes HPS")

        try:
            request_uuid = uuid.UUID(request_id)
        except ValueError:
            return False

        hps_request = db.query(HPSRequest).filter(HPSRequest.id == request_uuid).first()
        if not hps_request:
            return False

        try:
            db.delete(hps_request)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_hps_stats(
        db: Session,
        current_user: User
    ) -> HPSStatsResponse:
        """
        Obtener estadísticas de solicitudes HPS
        """
        base_query = db.query(HPSRequest)

        # Control de acceso según el rol del usuario
        if current_user.role.name in ["admin", "jefe_seguridad", "security_chief"]:
            # Admin y jefes de seguridad pueden ver estadísticas de todas las solicitudes
            pass
        elif current_user.role.name == "team_leader":
            # Team leader puede ver estadísticas de su equipo
            base_query = base_query.join(User, HPSRequest.user_id == User.id).filter(
                User.team_id == current_user.team_id
            )
        else:
            # Member solo puede ver estadísticas de sus propias solicitudes
            base_query = base_query.filter(HPSRequest.user_id == current_user.id)

        # Contar por estado
        total_requests = base_query.count()
        pending_requests = base_query.filter(HPSRequest.status == HPSStatus.PENDING).count()
        waiting_dps_requests = base_query.filter(HPSRequest.status == HPSStatus.WAITING_DPS).count()
        submitted_requests = base_query.filter(HPSRequest.status == HPSStatus.SUBMITTED).count()
        approved_requests = base_query.filter(HPSRequest.status == HPSStatus.APPROVED).count()
        rejected_requests = base_query.filter(HPSRequest.status == HPSStatus.REJECTED).count()
        expired_requests = base_query.filter(HPSRequest.status == HPSStatus.EXPIRED).count()

        # Contar por tipo de solicitud
        requests_by_type = {}
        for request_type in HPSRequestType:
            count = base_query.filter(HPSRequest.request_type == request_type).count()
            requests_by_type[request_type.value] = count

        # Obtener solicitudes recientes (últimas 5)
        recent_requests_query = base_query.options(
            joinedload(HPSRequest.user),
            joinedload(HPSRequest.submitted_by_user),
            joinedload(HPSRequest.approved_by_user)
        ).order_by(desc(HPSRequest.created_at)).limit(5)

        recent_requests = [
            HPSRequestResponse.from_hps_request(req, include_user_details=False)
            for req in recent_requests_query.all()
        ]

        return HPSStatsResponse(
            total_requests=total_requests,
            pending_requests=pending_requests,
            waiting_dps_requests=waiting_dps_requests,
            submitted_requests=submitted_requests,
            approved_requests=approved_requests,
            rejected_requests=rejected_requests,
            expired_requests=expired_requests,
            requests_by_type=requests_by_type,
            recent_requests=recent_requests
        )

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """
        Obtener usuario por ID (helper method)
        """
        try:
            user_uuid = uuid.UUID(user_id)
            return db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            return None

    @staticmethod
    def approve_hps_request(
        db: Session,
        request_id: str,
        current_user: User,
        expires_at: Optional[date] = None,
        notes: Optional[str] = None
    ) -> Optional[HPSRequestResponse]:
        """
        Aprobar una solicitud HPS específica
        """
        hps_data = HPSRequestUpdate(
            status=HPSStatus.APPROVED,
            expires_at=expires_at,
            notes=notes
        )
        return HPSService.update_hps_request(db, request_id, hps_data, current_user)

    @staticmethod
    def reject_hps_request(
        db: Session,
        request_id: str,
        current_user: User,
        notes: Optional[str] = None
    ) -> Optional[HPSRequestResponse]:
        """
        Rechazar una solicitud HPS específica
        """
        hps_data = HPSRequestUpdate(
            status=HPSStatus.REJECTED,
            notes=notes
        )
        return HPSService.update_hps_request(db, request_id, hps_data, current_user)

    @staticmethod
    def submit_hps_request(
        db: Session,
        request_id: str,
        current_user: User,
        notes: Optional[str] = None
    ) -> Optional[HPSRequestResponse]:
        """
        Marcar una solicitud HPS como enviada a la entidad externa
        """
        hps_data = HPSRequestUpdate(
            status=HPSStatus.SUBMITTED,
            notes=notes
        )
        return HPSService.update_hps_request(db, request_id, hps_data, current_user)

    @staticmethod
    def get_pending_requests(
        db: Session,
        current_user: User
    ) -> List[HPSRequestResponse]:
        """
        Obtener todas las solicitudes pendientes de envío (solo admin o team leader)
        """
        if current_user.role.name not in ["admin", "team_leader"]:
            raise ValueError("No tienes permisos para ver solicitudes pendientes de envío")

        query = db.query(HPSRequest).options(
            joinedload(HPSRequest.user),
            joinedload(HPSRequest.submitted_by_user),
            joinedload(HPSRequest.approved_by_user)
        ).filter(HPSRequest.status == HPSStatus.PENDING)

        # Control de acceso para team leader
        if current_user.role.name == "team_leader":
            query = query.join(User, HPSRequest.user_id == User.id).filter(
                User.team_id == current_user.team_id
            )

        requests = query.order_by(HPSRequest.created_at).all()
        
        return [
            HPSRequestResponse.from_hps_request(req) for req in requests
        ]

    @staticmethod
    def get_submitted_requests(
        db: Session,
        current_user: User
    ) -> List[HPSRequestResponse]:
        """
        Obtener todas las solicitudes enviadas esperando respuesta (solo admin o team leader)
        """
        if current_user.role.name not in ["admin", "team_leader"]:
            raise ValueError("No tienes permisos para ver solicitudes enviadas")

        query = db.query(HPSRequest).options(
            joinedload(HPSRequest.user),
            joinedload(HPSRequest.submitted_by_user),
            joinedload(HPSRequest.approved_by_user)
        ).filter(HPSRequest.status == HPSStatus.SUBMITTED)

        # Control de acceso para team leader
        if current_user.role.name == "team_leader":
            query = query.join(User, HPSRequest.user_id == User.id).filter(
                User.team_id == current_user.team_id
            )

        requests = query.order_by(HPSRequest.created_at).all()
        
        return [
            HPSRequestResponse.from_hps_request(req) for req in requests
        ]

    @staticmethod
    def delete_hps_requests_by_user_id(
        db: Session,
        user_id: uuid.UUID
    ) -> int:
        """
        Eliminar todas las solicitudes HPS de un usuario específico
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario cuyas solicitudes se van a eliminar
            
        Returns:
            Número de solicitudes eliminadas
        """
        try:
            # Buscar todas las solicitudes HPS del usuario
            hps_requests = db.query(HPSRequest).filter(
                HPSRequest.user_id == user_id
            ).all()
            
            count = len(hps_requests)
            
            # Eliminar todas las solicitudes
            for hps_request in hps_requests:
                db.delete(hps_request)
            
            db.commit()
            return count
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def create_hps_request_with_token(
        db: Session,
        hps_data: HPSRequestCreate,
        email: str,
        submitted_by_user_id: uuid.UUID,
        hps_type: str = "solicitud"
    ) -> HPSRequestResponse:
        """
        Crear una nueva solicitud HPS usando token (sin autenticación)
        """
        try:
            # Variables para controlar si se crea un nuevo usuario
            user_was_created = False
            temp_password = None
            
            # Buscar usuario por email
            target_user = db.query(User).filter(User.email == email).first()
            
            # Si el usuario existe, verificar si necesita cambiar de equipo
            if target_user:
                # Obtener el usuario que está solicitando el HPS
                submitted_by_user = db.query(User).filter(User.id == submitted_by_user_id).first()
                if submitted_by_user and submitted_by_user.role.name in ["team_leader", "team_lead"]:
                    # Si es jefe de equipo y el usuario objetivo no está en su equipo, moverlo
                    if target_user.team_id != submitted_by_user.team_id:
                        print(f"🔍 DEBUG: Moviendo usuario {target_user.email} al equipo del jefe: {submitted_by_user.team_id}")
                        target_user.team_id = submitted_by_user.team_id
                        db.commit()
                        db.refresh(target_user)
            
            if not target_user:
                # Si el usuario no existe, crear uno básico
                # Obtener el usuario que está solicitando el HPS para usar su team_id
                submitted_by_user = db.query(User).filter(User.id == submitted_by_user_id).first()
                if not submitted_by_user:
                    raise ValueError("Usuario que solicita el HPS no encontrado")
                
                # Determinar el team_id según el rol del usuario que solicita
                target_team_id = None
                if submitted_by_user.role.name in ["team_leader", "team_lead"]:
                    # Si es jefe de equipo, usar su team_id
                    target_team_id = submitted_by_user.team_id
                    print(f"🔍 DEBUG: Jefe de equipo solicitando HPS, asignando al equipo: {target_team_id}")
                else:
                    # Si no es jefe de equipo, usar equipo AICOX por defecto
                    aicox_team = db.query(Team).filter(Team.name == "AICOX").first()
                    if not aicox_team:
                        raise ValueError("Equipo AICOX no encontrado en la base de datos")
                    target_team_id = aicox_team.id
                    print(f"🔍 DEBUG: Usuario no-jefe solicitando HPS, asignando al equipo AICOX: {target_team_id}")
                
                # Generar contraseña temporal
                import secrets
                import string
                from src.auth.jwt import get_password_hash
                
                # Generar contraseña temporal de 12 caracteres
                temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
                password_hash = get_password_hash(temp_password)
                
                target_user = User(
                    id=uuid.uuid4(),
                    email=email,
                    first_name=hps_data.first_name or "Usuario",
                    last_name=hps_data.first_last_name or "HPS",
                    password_hash=password_hash,  # Contraseña temporal generada
                    role_id=3,  # Member role por defecto (ID 3 = member)
                    team_id=target_team_id,  # UUID del equipo del jefe de equipo o AICOX
                    is_active=True,
                    email_verified=False,
                    is_temp_password=True  # Marcar como contraseña temporal
                )
                db.add(target_user)
                db.commit()
                db.refresh(target_user)
                user_was_created = True
                
                # Enviar notificaciones de nuevo usuario
                try:
                    from src.email.service import EmailService
                    from src.email.user_notification_service import UserNotificationService
                    from src.config.settings import settings
                    
                    # Crear servicio de email con configuración del .env
                    email_service = EmailService(
                        smtp_host=settings.SMTP_HOST,
                        smtp_port=settings.SMTP_PORT,
                        smtp_username=settings.SMTP_USER,
                        smtp_password=settings.SMTP_PASSWORD,
                        imap_host=settings.IMAP_HOST,
                        imap_port=settings.IMAP_PORT,
                        imap_username=settings.IMAP_USER,
                        imap_password=settings.IMAP_PASSWORD,
                        from_name=settings.SMTP_FROM_NAME,
                        reply_to=settings.SMTP_REPLY_TO
                    )
                    
                    # Crear servicio de notificaciones
                    notification_service = UserNotificationService(email_service)
                    
                    # Enviar notificaciones
                    notification_result = notification_service.notify_new_user(target_user, submitted_by_user, db)
                    
                    if notification_result["success"]:
                        print(f"✅ Notificaciones enviadas para nuevo usuario {target_user.email}: {notification_result['notifications_sent']} correos")
                    else:
                        print(f"⚠️ Error enviando notificaciones para {target_user.email}: {notification_result['message']}")
                            
                except Exception as e:
                    print(f"❌ Error enviando notificaciones para nuevo usuario {target_user.email}: {str(e)}")
                    # No fallar la creación del usuario por errores de notificación

            # Crear la solicitud HPS
            print(f"🔍 DEBUG: request_type recibido: '{hps_data.request_type}'")
            print(f"🔍 DEBUG: hps_type recibido: '{hps_type}'")
            
            # Mapear hps_type a request_type
            if hps_type == 'traslado':
                final_request_type = 'transfer'
            elif hps_type == 'renovacion':
                final_request_type = 'renewal'
            elif hps_type == 'nueva':
                final_request_type = 'new'
            else:
                final_request_type = hps_data.request_type
            print(f"🔍 DEBUG: final_request_type: '{final_request_type}'")
            
            hps_request = HPSRequest(
                id=uuid.uuid4(),
                user_id=target_user.id,
                request_type=final_request_type,
                type=hps_type,
                document_type=hps_data.document_type,
                document_number=hps_data.document_number,
                birth_date=hps_data.birth_date,
                first_name=hps_data.first_name,
                first_last_name=hps_data.first_last_name,
                second_last_name=hps_data.second_last_name,
                nationality=hps_data.nationality,
                birth_place=hps_data.birth_place,
                email=hps_data.email,
                phone=hps_data.phone,
                status=HPSStatus.PENDING,
                submitted_by=submitted_by_user_id,  # Usuario que creó el token
                notes="",  # Campo notes vacío por defecto
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            db.add(hps_request)
            db.commit()
            db.refresh(hps_request)

            # Si es un traslado, generar PDF rellenado
            print(f"🔍 DEBUG: hps_type recibido: '{hps_type}'")
            if hps_type == 'traslado':
                try:
                    from src.hps.pdf_service import PDFService
                    from src.hps.template_service import HpsTemplateService
                    
                    # Obtener el usuario que solicitó el traspaso para seleccionar la plantilla correcta
                    submitted_by_user = db.query(User).filter(User.id == submitted_by_user_id).first()
                    template_service = HpsTemplateService(db)
                    
                    # Seleccionar plantilla según el rol del usuario que solicita el traspaso
                    template_type = "jefe_seguridad"  # Por defecto
                    if submitted_by_user and submitted_by_user.role:
                        user_role = submitted_by_user.role.name
                        if user_role == "jefe_seguridad_suplente":
                            template_type = "jefe_seguridad_suplente"
                        elif user_role == "jefe_seguridad":
                            template_type = "jefe_seguridad"
                        elif user_role == "admin":
                            # Admin usa la plantilla de jefe_seguridad por defecto
                            template_type = "jefe_seguridad"
                    
                    # Obtener plantilla activa del tipo correspondiente
                    active_template = template_service.get_template_by_type(template_type)
                    
                    # Si no hay plantilla del tipo específico, intentar con la genérica
                    if not active_template:
                        from src.models.hps_template import HpsTemplate
                        active_template = db.query(HpsTemplate).filter(HpsTemplate.active == True).first()
                    
                    if active_template and active_template.template_pdf:
                        # Preparar datos del usuario
                        user_data = {
                            'first_name': hps_data.first_name,
                            'first_last_name': hps_data.first_last_name,
                            'second_last_name': hps_data.second_last_name,
                            'email': hps_data.email,
                            'phone': hps_data.phone,
                            'document_number': hps_data.document_number,
                            'birth_date': hps_data.birth_date,
                            'birth_place': hps_data.birth_place,
                            'nationality': hps_data.nationality,
                        }
                        
                        # Intentar rellenar el template
                        try:
                            filled_pdf = PDFService.fill_pdf_template(
                                active_template.template_pdf, 
                                user_data
                            )
                        except Exception as e:
                            # Si falla, crear PDF simple
                            filled_pdf = PDFService.create_simple_filled_pdf(user_data)
                        
                        # Guardar PDF rellenado en la solicitud
                        hps_request.filled_pdf = filled_pdf
                        hps_request.template_id = active_template.id
                        db.commit()
                        db.refresh(hps_request)
                        
                except Exception as e:
                    # Si hay error generando PDF, continuar sin él
                    print(f"Error generando PDF para traslado: {str(e)}")

            return HPSRequestResponse.from_hps_request(
                hps_request, 
                temp_password=temp_password,
                user_created=user_was_created
            )

        except Exception as e:
            db.rollback()
            raise ValueError(f"Error creando solicitud HPS: {str(e)}")

    @staticmethod
    def create_transfer_request(
        db: Session,
        hps_data: HPSRequestCreate,
        submitted_by_user_id: uuid.UUID,
        template_id: Optional[int] = None,
        submitted_by_user: Optional[User] = None
    ) -> HPSRequestResponse:
        """
        Crear una nueva solicitud de traslado HPS
        """
        try:
            # Determinar el user_id para la solicitud
            target_user_id = None
            
            if hps_data.user_id:
                # Verificar que el usuario existe
                target_user = HPSService.get_user_by_id(db, hps_data.user_id)
                if not target_user:
                    raise ValueError(f"Usuario con ID {hps_data.user_id} no encontrado")
                target_user_id = target_user.id
            else:
                # Buscar usuario por email
                target_user = db.query(User).filter(User.email == hps_data.email).first()
                if target_user:
                    target_user_id = target_user.id
                else:
                    raise ValueError(f"Usuario con email {hps_data.email} no encontrado. El usuario debe existir antes de crear una solicitud de traslado.")

            # Verificar que no exista una solicitud activa para este usuario
            existing_active = db.query(HPSRequest).filter(
                and_(
                    HPSRequest.user_id == target_user_id,
                    HPSRequest.status.in_([HPSStatus.PENDING, HPSStatus.SUBMITTED])
                )
            ).first()
            
            if existing_active:
                status_text = "pendiente" if existing_active.status == HPSStatus.PENDING else "enviada y esperando respuesta"
                raise ValueError(f"Ya existe una solicitud HPS {status_text} para este usuario (ID: {existing_active.id})")

            # Si no se proporciona template_id, seleccionar automáticamente según el rol del usuario
            if not template_id and submitted_by_user:
                from src.models.hps_template import HpsTemplate
                from src.hps.template_service import HpsTemplateService
                
                template_service = HpsTemplateService(db)
                user_role = submitted_by_user.role.name if submitted_by_user.role else None
                
                if user_role == "jefe_seguridad_suplente":
                    template_type = "jefe_seguridad_suplente"
                elif user_role == "jefe_seguridad":
                    template_type = "jefe_seguridad"
                elif user_role == "admin":
                    # Admin usa la plantilla de jefe_seguridad por defecto
                    template_type = "jefe_seguridad"
                else:
                    template_type = "jefe_seguridad"
                
                active_template = template_service.get_template_by_type(template_type)
                if active_template:
                    template_id = active_template.id

            # Crear la nueva solicitud de traslado HPS
            hps_request = HPSRequest(
                user_id=target_user_id,
                request_type=hps_data.request_type,
                status=HPSStatus.PENDING,
                type='traslado',
                template_id=template_id,
                document_type=hps_data.document_type,
                document_number=hps_data.document_number,
                birth_date=hps_data.birth_date,
                first_name=hps_data.first_name,
                first_last_name=hps_data.first_last_name,
                second_last_name=hps_data.second_last_name,
                nationality=hps_data.nationality,
                birth_place=hps_data.birth_place,
                email=hps_data.email,
                phone=hps_data.phone,
                submitted_by=submitted_by_user_id
            )

            db.add(hps_request)
            db.commit()
            db.refresh(hps_request)

            # Cargar relaciones para la respuesta
            hps_request = db.query(HPSRequest).options(
                joinedload(HPSRequest.user),
                joinedload(HPSRequest.submitted_by_user),
                joinedload(HPSRequest.approved_by_user),
                joinedload(HPSRequest.template)
            ).filter(HPSRequest.id == hps_request.id).first()

            return HPSRequestResponse.from_hps_request(hps_request)

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def upload_filled_pdf(
        db: Session,
        request_id: str,
        pdf_content: bytes,
        current_user: User
    ) -> Optional[HPSRequestResponse]:
        """
        Subir PDF rellenado por el empleado
        """
        try:
            request_uuid = uuid.UUID(request_id)
        except ValueError:
            return None

        # Buscar la solicitud
        query = db.query(HPSRequest).filter(HPSRequest.id == request_uuid)
        
        # Control de acceso
        if current_user.role.name == "admin":
            pass
        elif current_user.role.name == "team_leader":
            query = query.join(User, HPSRequest.user_id == User.id).filter(
                User.team_id == current_user.team_id
            )
        else:
            # Member solo puede subir PDF de sus propias solicitudes
            query = query.filter(HPSRequest.user_id == current_user.id)

        hps_request = query.first()
        if not hps_request:
            return None

        # Verificar que es un traslado
        if hps_request.type != 'traslado':
            raise ValueError("Solo se pueden subir PDFs para solicitudes de traslado")

        # Actualizar el PDF rellenado
        hps_request.filled_pdf = pdf_content
        hps_request.status = HPSStatus.SUBMITTED  # Cambiar estado a enviado
        
        db.commit()
        db.refresh(hps_request)

        # Cargar relaciones para la respuesta
        hps_request = db.query(HPSRequest).options(
            joinedload(HPSRequest.user),
            joinedload(HPSRequest.submitted_by_user),
            joinedload(HPSRequest.approved_by_user),
            joinedload(HPSRequest.template)
        ).filter(HPSRequest.id == hps_request.id).first()

        return HPSRequestResponse.from_hps_request(hps_request)

    @staticmethod
    def upload_response_pdf(
        db: Session,
        request_id: str,
        pdf_content: bytes,
        current_user: User
    ) -> Optional[HPSRequestResponse]:
        """
        Subir PDF de respuesta oficial (solo admin)
        """
        if current_user.role.name != "admin":
            raise ValueError("Solo los administradores pueden subir PDFs de respuesta")

        try:
            request_uuid = uuid.UUID(request_id)
        except ValueError:
            return None

        hps_request = db.query(HPSRequest).filter(HPSRequest.id == request_uuid).first()
        if not hps_request:
            return None

        # Verificar que es un traslado
        if hps_request.type != 'traslado':
            raise ValueError("Solo se pueden subir PDFs de respuesta para solicitudes de traslado")

        # Actualizar el PDF de respuesta
        hps_request.response_pdf = pdf_content
        hps_request.status = HPSStatus.APPROVED  # Cambiar estado a aprobado
        
        db.commit()
        db.refresh(hps_request)

        # Cargar relaciones para la respuesta
        hps_request = db.query(HPSRequest).options(
            joinedload(HPSRequest.user),
            joinedload(HPSRequest.submitted_by_user),
            joinedload(HPSRequest.approved_by_user),
            joinedload(HPSRequest.template)
        ).filter(HPSRequest.id == hps_request.id).first()

        return HPSRequestResponse.from_hps_request(hps_request)

    @staticmethod
    def get_transfer_requests(
        db: Session,
        current_user: User,
        page: int = 1,
        per_page: int = 10,
        status: Optional[HPSStatus] = None
    ) -> HPSRequestList:
        """
        Obtener lista paginada de solicitudes de traslado
        """
        query = db.query(HPSRequest).options(
            joinedload(HPSRequest.user),
            joinedload(HPSRequest.submitted_by_user),
            joinedload(HPSRequest.approved_by_user),
            joinedload(HPSRequest.template)
        ).filter(HPSRequest.type == 'traslado')

        # Control de acceso según el rol del usuario
        if current_user.role.name == "admin":
            pass
        elif current_user.role.name == "team_leader":
            query = query.join(User, HPSRequest.user_id == User.id).filter(
                User.team_id == current_user.team_id
            )
        else:
            query = query.filter(HPSRequest.user_id == current_user.id)

        # Aplicar filtros
        if status:
            query = query.filter(HPSRequest.status == status)

        # Contar total de registros
        total = query.count()

        # Aplicar paginación
        offset = (page - 1) * per_page
        requests = query.order_by(desc(HPSRequest.created_at)).offset(offset).limit(per_page).all()

        # Convertir a respuestas
        request_responses = [
            HPSRequestResponse.from_hps_request(req) for req in requests
        ]

        # Calcular páginas totales
        pages = (total + per_page - 1) // per_page

        return HPSRequestList(
            requests=request_responses,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )