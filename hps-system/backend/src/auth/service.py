# Servicio de autenticación para HPS
from datetime import timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.models.user import User
from src.auth.jwt import verify_password, get_password_hash, create_access_token
from src.auth.schemas import UserLogin, UserCreate, Token, PasswordChange
from src.config.settings import settings
from typing import Optional

class AuthService:
    """Servicio para operaciones de autenticación"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(self, login_data: UserLogin) -> Optional[User]:
        """Autenticar usuario con email y password
        
        Nota: Para prevenir timing attacks, siempre se verifica la contraseña
        incluso si el usuario no existe, usando un hash dummy válido de bcrypt.
        """
        user = self.db.query(User).filter(User.email == login_data.email).first()
        
        # Si el usuario no existe, usar un hash dummy válido de bcrypt para mantener tiempo constante
        # Esto previene timing attacks que podrían revelar si un email existe
        # Hash bcrypt válido que siempre fallará la verificación pero tomará el mismo tiempo
        dummy_hash = "$2b$12$ycuo0CzVnuXPw99FIG/n3.41g/8v8Oekydn82gLQ6aWff9JC5Y54K"
        password_hash_to_check = user.password_hash if user else dummy_hash
        
        # Siempre verificar la contraseña para mantener tiempo constante
        # Esto previene que un atacante pueda determinar si un email existe
        # basándose en diferencias de tiempo de respuesta
        password_valid = verify_password(login_data.password, password_hash_to_check)
        
        # Si no hay usuario o la contraseña es inválida, retornar None
        if not user or not password_valid:
            return None
        
        # Verificar si el usuario está activo
        if not user.is_active:
            return None
            
        return user
    
    def create_user_token(self, user: User) -> Token:
        """Crear token JWT para usuario autenticado"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Datos a incluir en el token
        token_data = {
            "sub": user.email,
            "user_id": str(user.id),  # Convertir UUID a string
            "role": user.role.name
        }
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # En segundos
            user_id=str(user.id),
            email=user.email,
            role=user.role.name
        )
    
    def login(self, login_data: UserLogin) -> Token:
        """Proceso completo de login"""
        user = self.authenticate_user(login_data)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Actualizar last_login
        from datetime import datetime
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        return self.create_user_token(user)
    
    def create_user(self, user_data: UserCreate) -> User:
        """Crear nuevo usuario"""
        # Verificar que el username no exista
        existing_user = self.db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya está en uso"
            )
        
        # Verificar que el email no exista
        existing_email = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso"
            )
        
        # Crear hash del password
        password_hash = get_password_hash(user_data.password)
        
        # Crear usuario
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            password_hash=password_hash,
            role=user_data.role.value,
            team_id=user_data.team_id,
            is_active=True
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def change_password(self, user: User, password_data: PasswordChange) -> bool:
        """Cambiar contraseña de usuario"""
        # Verificar contraseña actual
        if not verify_password(password_data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contraseña actual incorrecta"
            )
        
        # Verificar que las nuevas contraseñas coincidan
        if password_data.new_password != password_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Las contraseñas nuevas no coinciden"
            )
        
        # Actualizar contraseña
        user.password_hash = get_password_hash(password_data.new_password)
        user.is_temp_password = False  # Marcar como contraseña permanente
        self.db.commit()
        
        return True
    
    def deactivate_user(self, user_id: int) -> bool:
        """Desactivar usuario"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        user.is_active = False
        self.db.commit()
        
        return True
    
    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Obtener usuario por ID y retornar como diccionario"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            return {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role_name": user.role.name if user.role else "member",
                "is_active": user.is_active,
                "team_id": str(user.team_id) if user.team_id else None
            }
        except Exception:
            return None
    
    def activate_user(self, user_id: int) -> bool:
        """Activar usuario"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        user.is_active = True
        self.db.commit()
        
        return True

# Función auxiliar para usar fuera de la clase
async def get_user_by_id(db: Session, user_id: str) -> Optional[dict]:
    """Función auxiliar para obtener usuario por ID"""
    auth_service = AuthService(db)
    return auth_service.get_user_by_id(user_id)
