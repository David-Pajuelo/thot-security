from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import time
import logging
from contextlib import asynccontextmanager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar módulos de la aplicación
from src.database.database import check_db_connection, engine
from src.models import Base
import subprocess
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación"""
    # Startup
    logger.info("🚀 Iniciando aplicación HPS Backend...")
    
    # Verificar conexión a base de datos
    logger.info("🔍 Verificando conexión a base de datos...")
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        if check_db_connection():
            logger.info("✅ Conexión a base de datos establecida")
            break
        else:
            retry_count += 1
            logger.warning(f"⏳ Esperando conexión a base de datos... (intento {retry_count}/{max_retries})")
            time.sleep(2)
    
    if retry_count >= max_retries:
        logger.error("❌ No se pudo establecer conexión a la base de datos")
        raise Exception("No se pudo conectar a la base de datos")
    
    # Ejecutar migraciones automáticamente usando nuestro script de inicialización
    logger.info("🔄 Ejecutando migraciones automáticas...")
    try:
        from src.database.init_db import init_database
        
        # Ejecutar inicialización de base de datos
        if init_database():
            logger.info("✅ Migraciones ejecutadas correctamente")
        else:
            logger.warning("⚠️ Hubo problemas con las migraciones, pero continuando...")
            
    except Exception as e:
        logger.error(f"❌ Error ejecutando migraciones: {e}")
        # No levantar excepción para que la app pueda seguir arrancando
    
    # Crear tablas si no existen
    logger.info("🏗️ Creando tablas de base de datos...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas creadas/verificadas correctamente")
    except Exception as e:
        logger.error(f"❌ Error creando tablas: {e}")
        raise e
    
    logger.info("🎉 Aplicación HPS Backend iniciada correctamente")
    
    yield
    
    # Shutdown
    logger.info("🛑 Cerrando aplicación HPS Backend...")

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema HPS Backend",
    description="Backend del Sistema de Habilitación Personal de Seguridad",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importar y configurar routers
from src.auth.router import router as auth_router
from src.users.router import router as users_router
from src.teams.router import router as teams_router
from src.hps.router import router as hps_router
from src.hps.token_router import router as hps_token_router
from src.hps.template_router import router as hps_template_router
from src.chat.router import router as chat_router
from src.extension.router import router as extension_router
from src.email.router import router as email_router

# Registrar routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(teams_router, prefix="/api/v1")
app.include_router(hps_router, prefix="/api/v1/hps")
app.include_router(hps_token_router, prefix="/api/v1/hps")
app.include_router(hps_template_router, prefix="/api/v1")
app.include_router(chat_router)
app.include_router(extension_router)
app.include_router(email_router)

# Mensaje de bienvenida
@app.get("/", tags=["General"])
async def root():
    """Endpoint raíz del API"""
    return {
        "message": "🚀 Sistema HPS Backend API",
        "version": "1.0.0",
        "documentation": "/docs",
        "status": "operational",
        "features": [
            "JWT Authentication",
            "User Management", 
            "HPS Processing",
            "Team Management",
            "Audit Logging",
            "Email Integration"
        ]
    }

# Endpoint de health check
@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud del servicio"""
    try:
        # Verificar conexión a base de datos
        if check_db_connection():
            return JSONResponse(
                status_code=200,
                content={
                    "status": "healthy",
                    "service": "HPS Backend",
                    "database": "connected",
                    "timestamp": time.time()
                }
            )
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "service": "HPS Backend",
                    "database": "disconnected",
                    "timestamp": time.time()
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "service": "HPS Backend",
                "error": str(e),
                "timestamp": time.time()
            }
        )



# Endpoint de información del sistema
@app.get("/info")
async def system_info():
    """Información del sistema"""
    return {
        "system": "HPS Backend",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database_url": f"postgresql://{os.getenv('POSTGRES_USER', '***')}:***@{os.getenv('POSTGRES_HOST', '***')}:{os.getenv('POSTGRES_PORT', '***')}/{os.getenv('POSTGRES_DB', '***')}",
        "features": [
            "Autenticación JWT",
            "Gestión de usuarios y roles",
            "Solicitudes HPS",
            "Gestión de equipos",
            "Auditoría completa",
            "Migraciones automáticas",
            "Integración de correo electrónico"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
