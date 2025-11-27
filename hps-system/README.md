# 🚀 Sistema HPS (Habilitación Personal de Seguridad)

Sistema web para la gestión de Habilitaciones de Personal de Seguridad desarrollado con React, FastAPI y PostgreSQL.


## Monitorizacion de logs
npx @agentdeskai/browser-tools-server@latest


## 📋 **Descripción del Proyecto**

El Sistema HPS es una aplicación web que permite a los administradores y jefes de equipo gestionar las habilitaciones de seguridad de su personal a través de un agente conversacional inteligente.

### 🎯 **Características del MVP**
- ✅ Sistema de autenticación JWT
- ✅ Gestión de usuarios con roles (Admin, Team Lead, Member)
- ✅ Formulario HPS con 11 campos
- ✅ Agente IA conversacional
- ✅ Interfaz de chat en React
- ✅ Base de datos PostgreSQL con persistencia
- ✅ **Sistema de correo electrónico completo** (SMTP/IMAP con Gmail)
- ✅ **Integración con complemento de navegador** para automatización de formularios

## 🏗️ **Arquitectura del Sistema**

```
hps-system/
├── frontend/           # Aplicación React
├── backend/            # API FastAPI con endpoints de extensión
├── agente-ia/         # Servicio del agente conversacional
├── extensions/        # Complementos de navegador (prod y test)
├── db/                # Base de datos y migraciones
└── docs/              # Documentación técnica
```

## 🔌 **Integración con Complemento de Navegador**

El sistema incluye endpoints específicos para la integración con complementos de navegador que permiten:

- **Automatización de formularios**: Relleno automático de datos de personas
- **Gestión de solicitudes**: Listado y actualización de estados
- **API REST**: Endpoints sin autenticación para uso del complemento

### 📡 **Endpoints Disponibles**
- `GET /api/v1/extension/personas` - Lista de personas con solicitudes pendientes
- `GET /api/v1/extension/persona/{dni}` - Datos detallados de una persona
- `PUT /api/v1/extension/solicitud/{dni}/enviada` - Marcar solicitud como enviada

### 📚 **Documentación**
- [Integración del Complemento de Navegador](docs/desarrollo/integracion-complemento-navegador.md) - Detalles técnicos de la API
- [Integración de Email](docs/desarrollo/integracion-email.md) - Sistema de correo electrónico
- [Complementos de Navegador](extensions/README.md) - Guía de instalación y uso de las extensiones

### 🔌 **Complementos Incluidos**
- **`extensions/hps-plugin-prod/`** - Complemento de producción
- **`extensions/hps-plugin-test/`** - Complemento de testing

Ambos complementos están listos para instalar en Chrome y se integran automáticamente con el sistema HPS.

### 🔧 **Tecnologías Utilizadas**
- **Frontend**: React con Tailwind CSS
- **Backend**: FastAPI con SQLAlchemy y Alembic
- **Base de Datos**: PostgreSQL 15
- **Cache**: Redis
- **Contenedores**: Docker & Docker Compose
- **IA**: OpenAI GPT-4o-mini

## 🚀 **Instalación y Despliegue**

### 📋 **Prerrequisitos**
- Docker Desktop
- Docker Compose
- Git

### 🔧 **Configuración Inicial**

1. **Clonar el repositorio**
```bash
git clone <url-del-repositorio>
cd hps-system
```

2. **Configurar variables de entorno**
```bash
cp env.example .env
# Editar .env con tus credenciales
```

3. **Variables obligatorias en .env**
```bash
# OpenAI API
OPENAI_API_KEY=tu_api_key_aqui

# Base de datos
POSTGRES_PASSWORD=tu_password_seguro

# JWT
JWT_SECRET_KEY=tu_clave_secreta_aqui

# SMTP
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_password_de_app
```

### 🐳 **Despliegue con Docker**

1. **Construir y levantar servicios**
```bash
docker-compose up -d --build
```

2. **Verificar estado de servicios**
```bash
docker-compose ps
```

3. **Ver logs de un servicio**
```bash
docker-compose logs streamlit
docker-compose logs agente-ia
docker-compose logs db
```

### 🌐 **Acceso a la Aplicación**

- **Frontend React**: http://localhost:3000
- **Backend FastAPI**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Agente IA**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 👥 **Roles de Usuario**

### 🔐 **Administrador**
- Gestión completa de usuarios
- Acceso a todas las funcionalidades
- Configuración del sistema

### 👨‍💼 **Jefe de Equipo**
- Gestión de su equipo
- Solicitudes de HPS
- Consultas de estado

### 👤 **Miembro**
- Visualización de su HPS
- Edición de perfil
- Acceso básico al sistema

## 🤖 **Comandos del Agente IA**

### 📝 **Comandos Disponibles**
1. **"Dar alta jefe de equipo"** - Crear nuevo jefe de equipo
2. **"Solicitar HPS"** - Solicitar nueva habilitación
3. **"Consultar estado HPS usuario"** - Ver estado de HPS

### 💬 **Ejemplos de Uso**
```
Usuario: "Quiero dar de alta a un jefe de equipo con el email jefe@empresa.com"
Agente: "Perfecto, voy a crear el usuario jefe@empresa.com como jefe de equipo..."

Usuario: "Necesito solicitar un HPS para maria.garcia@empresa.com"
Agente: "Voy a procesar la solicitud de HPS para maria.garcia@empresa.com..."
```

## 📊 **Estructura de la Base de Datos**

### 🗃️ **Tablas Principales**
- **users**: Usuarios del sistema
- **roles**: Roles y permisos
- **teams**: Equipos de trabajo
- **hps_requests**: Solicitudes de HPS
- **audit_logs**: Logs de auditoría

## 🧪 **Testing y Desarrollo**

### 🔍 **Testing Local**
```bash
# Testing de Streamlit
cd streamlit
pytest

# Testing del Agente IA
cd agente-ia
pytest
```

### 🚀 **Desarrollo Local**
```bash
# Levantar solo la base de datos
docker-compose up db

# Desarrollar Streamlit localmente
cd streamlit
pip install -r requirements.txt
streamlit run src/main.py

# Desarrollar Agente IA localmente
cd agente-ia
pip install -r requirements.txt
uvicorn src.main:app --reload
```

## 📁 **Estructura de Archivos**

```
HPS/
├── .gitignore                 # Exclusiones Git
├── .env.example              # Variables de entorno de ejemplo
├── docker-compose.yml        # Orquestación Docker
├── README.md                 # Este archivo
├── frontend/                # Aplicación React
│   ├── Dockerfile           # Contenedor React
│   ├── package.json         # Dependencias Node.js
│   └── src/                 # Código fuente React
├── backend/                 # Servicio FastAPI
│   ├── Dockerfile           # Contenedor FastAPI
│   ├── requirements.txt     # Dependencias Python
│   └── src/                 # Código fuente FastAPI
│       ├── auth/            # Sistema de autenticación JWT
│       ├── users/           # Gestión de usuarios
│       ├── models/          # Modelos SQLAlchemy
│       └── database/        # Configuración BD y migraciones Alembic
├── agente-ia/               # Agente IA conversacional
│   ├── Dockerfile           # Contenedor Agente
│   ├── requirements.txt     # Dependencias Python
│   └── src/                 # Código fuente del agente
└── docs/                    # Documentación técnica
    ├── api/                 # Documentación de APIs
    └── planificacion/       # Planes de implementación
```

## 🚨 **Solución de Problemas**

### ❌ **Problemas Comunes**

1. **Error de conexión a base de datos**
```bash
docker-compose logs db
docker-compose restart db
```

2. **Error de OpenAI API**
```bash
# Verificar que OPENAI_API_KEY esté configurada en .env
docker-compose logs agente-ia
```

3. **Error de puertos ocupados**
```bash
# Verificar qué está usando el puerto
netstat -ano | findstr :8501
# Cambiar puerto en docker-compose.yml si es necesario
```

### 📝 **Logs y Debugging**
```bash
# Ver logs en tiempo real
docker-compose logs -f streamlit

# Ver logs de todos los servicios
docker-compose logs

# Acceder al contenedor de la base de datos
docker-compose exec db psql -U hps_user -d hps_system
```

## 🔒 **Seguridad**

### 🛡️ **Medidas Implementadas**
- Autenticación JWT con tokens de acceso y refresh
- Hashing de contraseñas con bcrypt
- Validación de entrada en formularios
- Logs de auditoría para todas las acciones
- Variables de entorno para credenciales sensibles

### ⚠️ **Recomendaciones de Producción**
- Cambiar todas las claves secretas por defecto
- Configurar SSL/TLS
- Implementar rate limiting
- Configurar backup automático de base de datos
- Monitoreo de logs y alertas

## 📞 **Soporte y Contacto**

### 🆘 **Problemas Técnicos**
- Revisar logs de Docker: `docker-compose logs`
- Verificar configuración en `.env`
- Comprobar conectividad entre servicios

### 📧 **Contacto**
- **Desarrollador**: [Tu información de contacto]
- **Documentación**: Ver carpeta `docs/`

## 📈 **Roadmap Post-MVP**

### 🚀 **Fase 2: Mejoras**
- Dashboard administrativo
- Sistema de reportes
- Validaciones avanzadas
- Temas claro/oscuro

### 🎯 **Fase 3: Producción**
- SSL/HTTPS completo
- Monitoreo avanzado
- Backup automático
- Optimizaciones de rendimiento

---

**✅ Estado**: MVP en desarrollo  
**📅 Versión**: 1.0.0-MVP  
**🎯 Objetivo**: Sistema funcional para validación del concepto
