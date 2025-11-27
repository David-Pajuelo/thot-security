# Integración del Complemento de Navegador con el Sistema HPS

## 📋 Resumen

Este documento describe la integración del complemento de navegador con el sistema HPS, incluyendo los endpoints creados, cambios realizados y funcionalidades implementadas.

## 🎯 Objetivo

Permitir que el complemento de navegador pueda:
- Obtener lista de personas con solicitudes HPS pendientes
- Rellenar automáticamente formularios con datos de las personas
- Marcar solicitudes como enviadas

## 🔧 Cambios Realizados

### 1. Nuevo Módulo de Extensión

**Ubicación**: `backend/src/extension/`

#### Archivos Creados:
- `__init__.py` - Inicialización del módulo
- `router.py` - Endpoints REST para el complemento
- `schemas.py` - Modelos de datos Pydantic
- `service.py` - Lógica de negocio

### 2. Endpoints Implementados

#### GET `/api/v1/extension/personas`
- **Descripción**: Obtiene lista de personas con estado "pending"
- **Respuesta**: Array de objetos PersonaListResponse
- **Filtro**: `WHERE estado = 'pending'`

#### GET `/api/v1/extension/persona/{numero_documento}`
- **Descripción**: Obtiene datos detallados de una persona por DNI
- **Parámetros**: `numero_documento` (string)
- **Respuesta**: Objeto PersonaDetailResponse

#### PUT `/api/v1/extension/solicitud/{numero_documento}/enviada`
- **Descripción**: Marca una solicitud como enviada
- **Parámetros**: `numero_documento` (string)
- **Acción**: Cambia estado a "submitted"

### 3. Integración en el Backend

**Archivo**: `backend/src/main.py`
- Línea 99: Import del router de extensión
- Línea 108: Registro del router en la aplicación

### 4. Modificación del Dockerfile

**Archivo**: `backend/Dockerfile`
- Cambio: Reemplazado ENTRYPOINT por CMD para facilitar desarrollo
- Comando: `python -m uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload`

## 📊 Modelos de Datos

### PersonaListResponse
```python
{
    "tipo_documento": "string",
    "numero_documento": "string", 
    "fecha_nacimiento": "date",
    "nombre": "string",
    "primer_apellido": "string",
    "segundo_apellido": "string",
    "nacionalidad": "string",
    "lugar_nacimiento": "string",
    "correo": "string",
    "telefono": "string",
    "operacion": "string"
}
```

### PersonaDetailResponse
```python
{
    "tipo_documento": "string",
    "numero_documento": "string",
    "fecha_nacimiento": "date", 
    "nombre": "string",
    "primer_apellido": "string",
    "segundo_apellido": "string",
    "nacionalidad": "string",
    "lugar_nacimiento": "string",
    "correo": "string",
    "telefono": "string",
    "operacion": "string",
    "estado": "string"
}
```

## 🔄 Flujo de Trabajo

1. **Complemento carga lista**: Llama a `/personas` para obtener solicitudes pendientes
2. **Usuario selecciona persona**: Del desplegable en el complemento
3. **Relleno automático**: Complemento rellena formulario con datos de la persona
4. **Marcar como enviada**: Usuario marca solicitud como enviada

## 🗄️ Base de Datos

### Vista Utilizada
- **Nombre**: `solicitudes_hps`
- **Propósito**: Mapear columnas de `hps_requests` a nombres esperados por el complemento
- **Filtro**: `WHERE estado = 'pending'`

### Estados de Solicitudes
- `pending` - Solicitud creada, pendiente de envío
- `submitted` - Enviada a entidad externa, esperando respuesta  
- `approved` - Aprobada por la entidad externa
- `rejected` - Rechazada por la entidad externa
- `expired` - HPS expirada

## 🧪 Testing

### Endpoints de Prueba
```bash
# Obtener lista de personas
curl http://localhost:8001/api/v1/extension/personas

# Obtener persona específica
curl http://localhost:8001/api/v1/extension/persona/53739366G

# Marcar como enviada
curl -X PUT http://localhost:8001/api/v1/extension/solicitud/53739366G/enviada
```

## 📝 Notas Técnicas

### Corrección de Filtro
- **Problema inicial**: Filtro buscaba estado "en curso" que no existía
- **Solución**: Cambiado a estado "pending" que es el estado real de las solicitudes nuevas

### Compatibilidad
- Los cambios son **aditivos** - no modifican funcionalidad existente
- Mantiene compatibilidad con el sistema HPS original
- Endpoints específicos para el complemento sin afectar otros módulos

## 🚀 Despliegue

### Requisitos
- Sistema HPS funcionando en `http://localhost:8001`
- Base de datos PostgreSQL con datos de prueba
- Complemento de navegador configurado para usar los nuevos endpoints

### Verificación
1. Verificar que el backend responde en `http://localhost:8001`
2. Probar endpoints de extensión
3. Cargar complemento en Chrome
4. Verificar que el desplegable se llena con datos

## 📚 Referencias

- [Documentación FastAPI](https://fastapi.tiangolo.com/)
- [Documentación Pydantic](https://pydantic-docs.helpmanual.io/)
- [Documentación SQLAlchemy](https://docs.sqlalchemy.org/)
