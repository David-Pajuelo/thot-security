# Servicio de gestión de usuarios para HPS
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
import logging
from src.models.user import User
from src.auth.schemas import UserCreate, UserUpdate, UserRole
from src.auth.jwt import get_password_hash
from src.auth.dependencies import can_manage_users

logger = logging.getLogger(__name__)

class UserService:
    """Servicio para operaciones CRUD de usuarios"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id) -> Optional[User]:
        """Obtener usuario por ID"""
        from sqlalchemy.orm import joinedload
        
        # Convertir string UUID a UUID si es necesario
        if isinstance(user_id, str):
            try:
                import uuid
                user_id = uuid.UUID(user_id)
            except ValueError:
                return None
        return self.db.query(User).options(
            joinedload(User.team),
            joinedload(User.role)
        ).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Obtener usuario por username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Obtener usuario por email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_team_members(self, team_id: str, current_user: User = None) -> List[User]:
        """Obtener miembros de un equipo específico"""
        from sqlalchemy.orm import joinedload
        
        # Verificar permisos
        if current_user.role.name not in ['admin', 'team_leader', 'team_lead']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a equipos"
            )
        
        # Si es team_leader o team_lead, solo puede acceder a su propio equipo
        if current_user.role.name in ['team_leader', 'team_lead'] and str(current_user.team_id) != str(team_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes acceder a tu propio equipo"
            )
        
        return self.db.query(User).options(
            joinedload(User.team),
            joinedload(User.role)
        ).filter(
            User.team_id == team_id,
            User.is_active == True
        ).all()
    
    def get_users(
        self, 
        skip: int = 0, 
        limit: int = 100,
        role: Optional[str] = None,
        team_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        current_user: User = None
    ) -> List[User]:
        """Obtener lista de usuarios con filtros"""
        from sqlalchemy.orm import joinedload
        
        query = self.db.query(User).options(
            joinedload(User.team),
            joinedload(User.role)
        )
        
        # Filtro por rol
        if role:
            query = query.filter(User.role.has(name=role))
        
        # Filtro por equipo
        if team_id is not None:
            query = query.filter(User.team_id == team_id)
        
        # Filtro por estado activo
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # Búsqueda por texto
        if search:
            search_filter = or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Control de acceso por equipo para team leaders
        if current_user and current_user.role.name == UserRole.TEAM_LEADER.value:
            query = query.filter(
                or_(
                    User.team_id == current_user.team_id,
                    User.id == current_user.id
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    def count_users(
        self,
        role: Optional[str] = None,
        team_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        current_user: User = None
    ) -> int:
        """Contar usuarios con filtros"""
        query = self.db.query(User)
        
        # Aplicar los mismos filtros que en get_users
        if role:
            query = query.filter(User.role.has(name=role))
        if team_id is not None:
            query = query.filter(User.team_id == team_id)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if search:
            search_filter = or_(
                User.username.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if current_user and current_user.role.name == UserRole.TEAM_LEADER.value:
            query = query.filter(
                or_(
                    User.team_id == current_user.team_id,
                    User.id == current_user.id
                )
            )
        
        return query.count()
    
    def create_user(self, user_data: UserCreate, created_by: User) -> User:
        """Crear nuevo usuario"""
        # Verificar permisos
        if not can_manage_users(created_by):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para crear usuarios"
            )
        
        # Verificar que el email no exista
        if self.get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso"
            )
        
        # Solo admin puede crear otros admins
        try:
            role_enum = user_data.get_role_enum()
        except ValueError:
            role_enum = UserRole.MEMBER  # Fallback para validación de permisos
        
        if role_enum == UserRole.ADMIN and created_by.role.name != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los administradores pueden crear otros administradores"
            )
        
        # Team leaders solo pueden crear usuarios en su equipo
        if created_by.role.name == UserRole.TEAM_LEADER.value:
            if user_data.team_id and str(user_data.team_id) != str(created_by.team_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo puedes crear usuarios en tu equipo"
                )
        
        # Convertir string a UserRole enum y obtener role_id desde la BD
        from src.models.user import Role
        try:
            role_enum = user_data.get_role_enum()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        role_record = self.db.query(Role).filter(Role.name == role_enum.value).first()
        if not role_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol '{role_enum.value}' no existe"
            )
        
        # Prevenir creación de usuarios con rol team_lead
        if role_enum.value == "team_lead":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede crear un usuario con rol team_lead directamente. Use la gestión de equipos para asignar líderes."
            )
        
        # Convertir team_id string a UUID si es necesario
        team_id_uuid = None
        if user_data.team_id:
            try:
                import uuid
                team_id_uuid = uuid.UUID(user_data.team_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="team_id debe ser un UUID válido"
                )
        else:
            # Si no se especifica team_id, usar AICOX como fallback
            import uuid
            DEFAULT_TEAM_ID = "d8574c01-851f-4716-9ac9-bbda45469bdf"
            team_id_uuid = uuid.UUID(DEFAULT_TEAM_ID)
        
        # Preparar nombres desde full_name
        name_parts = user_data.full_name.strip().split()
        first_name = name_parts[0] if name_parts else "Usuario"
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        # Crear hash del password
        password_hash = get_password_hash(user_data.password)
        
        # Crear usuario
        db_user = User(
            email=user_data.email,
            first_name=first_name,
            last_name=last_name,
            password_hash=password_hash,
            role_id=role_record.id,
            team_id=team_id_uuid,
            is_active=True
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        # Enviar notificaciones a jefes de seguridad y líderes de equipo
        try:
            from ..email.service import EmailService
            from ..email.user_notification_service import UserNotificationService
            import os
            
            # Crear servicio de email
            email_service = EmailService(
                smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
                smtp_port=int(os.getenv("SMTP_PORT", "587")),
                smtp_username=os.getenv("SMTP_USER", "aicoxidi@gmail.com"),
                smtp_password=os.getenv("SMTP_PASSWORD", ""),
                imap_host=os.getenv("IMAP_HOST", "imap.gmail.com"),
                imap_port=int(os.getenv("IMAP_PORT", "993")),
                imap_username=os.getenv("IMAP_USER", "aicoxidi@gmail.com"),
                imap_password=os.getenv("IMAP_PASSWORD", ""),
                from_name=os.getenv("SMTP_FROM_NAME", "HPS System"),
                reply_to=os.getenv("SMTP_REPLY_TO", "aicoxidi@gmail.com")
            )
            
            # Crear servicio de notificaciones
            notification_service = UserNotificationService(email_service)
            
            # Enviar notificaciones
            notification_result = notification_service.notify_new_user(db_user, created_by, self.db)
            
            if notification_result["success"]:
                logger.info(f"Notificaciones enviadas para nuevo usuario {db_user.email}: {notification_result['notifications_sent']} correos")
            else:
                logger.warning(f"Error enviando notificaciones para {db_user.email}: {notification_result['message']}")
                
        except Exception as e:
            logger.error(f"Error enviando notificaciones para nuevo usuario {db_user.email}: {str(e)}")
            # No fallar la creación del usuario por errores de notificación
        
        return db_user
    
    def update_user(self, user_id, user_data: UserUpdate, updated_by: User) -> User:
        """Actualizar usuario existente"""
        # Obtener usuario a actualizar
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar permisos
        if not can_manage_users(updated_by) and updated_by.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para actualizar este usuario"
            )
        
        # Solo admin puede cambiar roles a admin
        if user_data.role == UserRole.ADMIN.value and updated_by.role.name != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los administradores pueden asignar el rol de administrador"
            )
        
        # Team leaders no pueden cambiar roles de otros usuarios
        if (updated_by.role.name == UserRole.TEAM_LEADER.value and 
            str(updated_by.id) != str(user_id) and 
            user_data.role is not None):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los líderes de equipo no pueden cambiar roles de otros usuarios"
            )
        
        # Verificar email único si se está cambiando
        if user_data.email and user_data.email != user.email:
            if self.get_user_by_email(user_data.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El email ya está en uso"
                )
        
        # Aplicar cambios
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.full_name is not None:
            # Dividir full_name en first_name y last_name
            name_parts = user_data.full_name.strip().split()
            user.first_name = name_parts[0] if name_parts else "Usuario"
            user.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        if user_data.role is not None:
            # Prevenir cambio directo a team_lead
            if user_data.role == "team_lead":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede cambiar el rol a team_lead directamente. Use la gestión de equipos para asignar líderes."
                )
            
            # Obtener role_id desde la BD
            from src.models.user import Role
            role_record = self.db.query(Role).filter(Role.name == user_data.role).first()
            if role_record:
                user.role_id = role_record.id
        if user_data.team_id is not None:
            # Convertir team_id string a UUID si es necesario
            if user_data.team_id:
                try:
                    import uuid
                    user.team_id = uuid.UUID(user_data.team_id)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="team_id debe ser un UUID válido"
                    )
            else:
                user.team_id = None
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def delete_user(self, user_id, deleted_by: User) -> bool:
        """Eliminar usuario con eliminación en cascada"""
        # Obtener usuario a eliminar
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar permisos
        if not can_manage_users(deleted_by):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para eliminar usuarios"
            )
        
        # No se puede eliminar a sí mismo
        if user_id == deleted_by.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes eliminar tu propia cuenta"
            )
        
        # Solo admin puede eliminar otros admins
        if user.role.name == UserRole.ADMIN.value and deleted_by.role.name != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los administradores pueden eliminar otros administradores"
            )
        
        try:
            # Importar servicios necesarios para eliminación en cascada
            from src.hps.service import HPSService
            from src.hps.token_service import HPSTokenService
            
            # Eliminar en cascada:
            # 1. Eliminar todas las solicitudes HPS del usuario
            hps_deleted = HPSService.delete_hps_requests_by_user_id(self.db, user.id)
            
            # 2. Eliminar todos los tokens HPS generados por el usuario
            tokens_deleted = HPSTokenService.delete_tokens_by_user_id(self.db, user.id)
            
            # 3. Realizar soft delete del usuario
            user.is_active = False
            self.db.commit()
            
            # Log de la eliminación en cascada
            print(f"Usuario {user.email} eliminado. Solicitudes HPS eliminadas: {hps_deleted}, Tokens eliminados: {tokens_deleted}")
            
            return {
                "success": True,
                "hps_deleted": hps_deleted,
                "tokens_deleted": tokens_deleted
            }
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error eliminando usuario: {str(e)}"
            )
    
    def activate_user(self, user_id, activated_by: User) -> User:
        """Activar usuario"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        if not can_manage_users(activated_by):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para activar usuarios"
            )
        
        user.is_active = True
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def permanently_delete_user(self, user_id, deleted_by: User) -> dict:
        """Eliminar usuario definitivamente de la base de datos (hard delete)"""
        # Obtener usuario a eliminar
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Solo admins pueden hacer eliminación definitiva
        if deleted_by.role.name != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los administradores pueden eliminar usuarios definitivamente"
            )
        
        # No se puede eliminar a sí mismo
        if user_id == deleted_by.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes eliminar tu propia cuenta"
            )
        
        try:
            # Importar servicios necesarios para eliminación en cascada
            from src.hps.service import HPSService
            from src.hps.token_service import HPSTokenService
            
            # Eliminar en cascada:
            # 1. Eliminar todas las solicitudes HPS del usuario
            hps_deleted = HPSService.delete_hps_requests_by_user_id(self.db, user.id)
            
            # 2. Eliminar todos los tokens HPS generados por el usuario
            tokens_deleted = HPSTokenService.delete_tokens_by_user_id(self.db, user.id)
            
            # 3. Eliminar registros relacionados en otras tablas
            # Eliminar conversaciones de chat y sus mensajes
            from src.models.chat_conversation import ChatConversation
            from src.models.chat_message import ChatMessage
            
            # Primero eliminar todos los mensajes de las conversaciones del usuario
            conversations = self.db.query(ChatConversation).filter(ChatConversation.user_id == user.id).all()
            for conversation in conversations:
                # Eliminar todos los mensajes de esta conversación
                self.db.query(ChatMessage).filter(ChatMessage.conversation_id == conversation.id).delete()
            
            # Luego eliminar las conversaciones
            self.db.query(ChatConversation).filter(ChatConversation.user_id == user.id).delete()
            
            # Eliminar logs de auditoría
            from src.models.audit import AuditLog
            self.db.query(AuditLog).filter(AuditLog.user_id == user.id).delete()
            
            # UserSatisfaction eliminado - ya no existe
            
            # 4. Eliminar el usuario definitivamente
            self.db.delete(user)
            self.db.commit()
            
            # Log de la eliminación definitiva
            print(f"Usuario {user.email} eliminado definitivamente. Solicitudes HPS eliminadas: {hps_deleted}, Tokens eliminados: {tokens_deleted}")
            
            return {
                "success": True,
                "hps_deleted": hps_deleted,
                "tokens_deleted": tokens_deleted
            }
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error eliminando usuario definitivamente: {str(e)}"
            )
    
    def get_users_by_team(self, team_id: int, current_user: User) -> List[User]:
        """Obtener usuarios por equipo"""
        if not can_access_team_data(current_user, team_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a este equipo"
            )
        
        return self.db.query(User).filter(User.team_id == team_id).all()
    
    def get_users_by_role(self, role: UserRole, current_user: User) -> List[User]:
        """Obtener usuarios por rol"""
        if not can_manage_users(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para ver usuarios por rol"
            )
        
        return self.db.query(User).filter(User.role.has(name=role.value)).all()

