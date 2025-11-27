from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Configuración de base de datos
    POSTGRES_HOST: str
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    
    # Configuración de JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    
    # Configuración de OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Configuración del agente IA
    AGENTE_IA_HOST: str
    AGENTE_IA_PORT: str = "8000"
    
    # Configuración de SMTP
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_NAME: Optional[str] = "HPS System"
    SMTP_REPLY_TO: Optional[str] = None
    
    # Configuración de IMAP
    IMAP_HOST: Optional[str] = None
    IMAP_PORT: int = 993
    IMAP_USER: Optional[str] = None
    IMAP_PASSWORD: Optional[str] = None
    IMAP_MAILBOX: Optional[str] = "INBOX"
    
    # Configuración de Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    
    # Configuración de la aplicación
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    @property
    def database_url(self) -> str:
        """Construir URL de conexión a la base de datos"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        env_file = "/app/.env"  # Fallback si no hay variables de entorno
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Las variables de entorno del contenedor tienen prioridad sobre el archivo .env

# Instancia global de configuración
settings = Settings()

# Debug: imprimir configuración de base de datos (sin password)
if settings.DEBUG:
    print(f"🔧 DB Config: {settings.POSTGRES_USER}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
