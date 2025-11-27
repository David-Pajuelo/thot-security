"""
Módulo de autenticación JWT para el Sistema HPS
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración JWT
# Priorizar JWT_SECRET_KEY (usado por Django SimpleJWT) sobre SECRET_KEY
# Django SimpleJWT usa JWT_SECRET_KEY para firmar tokens (ver settings.py línea 74)
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY", "your_jwt_secret_key_here_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

# Configuración de base de datos
# NOTA: Ahora usa la base de datos compartida de cryptotrace
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "cryptotrace-db"),  # Cambiado a cryptotrace-db
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "cryptotrace"),  # Cambiado a cryptotrace
    "user": os.getenv("POSTGRES_USER", "postgres"),  # Cambiado a postgres
    "password": os.getenv("POSTGRES_PASSWORD", "postgres")  # Cambiado a postgres
}

# Configuración de encriptación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuración de seguridad HTTP
security = HTTPBearer()

class AuthManager:
    """Gestor de autenticación JWT"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verificar contraseña con hash bcrypt"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generar hash de contraseña con bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Crear token JWT de acceso"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verificar y decodificar token JWT"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def verify_token_websocket(token: str) -> Optional[dict]:
        """Verificar y decodificar token JWT para WebSocket (sin excepciones HTTP)"""
        try:
            logger.info(f"Verificando token WebSocket con SECRET_KEY: {SECRET_KEY[:20] if SECRET_KEY else 'None'}...")
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            logger.info(f"Token decodificado exitosamente: {payload}")
            return payload
        except JWTError as e:
            logger.error(f"Error JWT al verificar token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al verificar token: {e}")
            return None
    
    @staticmethod
    def get_db_connection():
        """Obtener conexión a la base de datos"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            return conn
        except Exception as e:
            logger.error(f"Error conectando a la base de datos: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error de conexión a la base de datos"
            )
    
    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[dict]:
        """Autenticar usuario con email y contraseña"""
        conn = AuthManager.get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Buscar usuario por email
                cur.execute("""
                    SELECT u.id, u.email, u.password_hash, u.first_name, u.last_name, 
                           u.is_active, r.name as role_name, r.permissions
                    FROM users u
                    JOIN roles r ON u.role_id = r.id
                    WHERE u.email = %s
                """, (email,))
                
                user_data = cur.fetchone()
                
                if not user_data:
                    return None
                
                if not user_data['is_active']:
                    return None
                
                if not AuthManager.verify_password(password, user_data['password_hash']):
                    return None
                
                return dict(user_data)
                
        except Exception as e:
            logger.error(f"Error autenticando usuario: {e}")
            return None
        finally:
            conn.close()
    
    @staticmethod
    def create_user_session(user_id: str, token_hash: str, ip_address: str = None, user_agent: str = None) -> bool:
        """Crear sesión de usuario en la base de datos"""
        conn = AuthManager.get_db_connection()
        try:
            with conn.cursor() as cur:
                # Calcular expiración
                expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                
                # Insertar sesión
                cur.execute("""
                    INSERT INTO user_sessions (user_id, token_hash, expires_at, ip_address, user_agent)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, token_hash, expires_at, ip_address, user_agent))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error creando sesión: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    @staticmethod
    def cleanup_expired_sessions() -> int:
        """Limpiar sesiones expiradas"""
        conn = AuthManager.get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM user_sessions WHERE expires_at < NOW()")
                deleted_count = cur.rowcount
                conn.commit()
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error limpiando sesiones: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()

# Función para obtener usuario actual desde token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Obtener usuario actual desde token JWT"""
    token = credentials.credentials
    
    try:
        # Verificar token
        payload = AuthManager.verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        
        # Obtener datos del usuario desde la base de datos
        conn = AuthManager.get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT u.id, u.email, u.first_name, u.last_name, u.is_active,
                           r.name as role_name, r.permissions, u.team_id
                    FROM users u
                    JOIN roles r ON u.role_id = r.id
                    WHERE u.id = %s
                """, (user_id,))
                
                user_data = cur.fetchone()
                
                if not user_data:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Usuario no encontrado"
                    )
                
                if not user_data['is_active']:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Usuario inactivo"
                    )
                
                return dict(user_data)
                
        finally:
            conn.close()
            
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

# Función para verificar permisos de administrador
async def get_current_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Verificar que el usuario actual sea administrador"""
    if current_user.get("role_name") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: Se requieren permisos de administrador"
        )
    return current_user

# Función para verificar permisos de jefe de equipo
async def get_current_team_lead_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Verificar que el usuario actual sea jefe de equipo o administrador"""
    role = current_user.get("role_name")
    if role not in ["admin", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: Se requieren permisos de jefe de equipo"
        )
    return current_user
