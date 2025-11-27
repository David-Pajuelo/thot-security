# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

## [Unreleased] - 2025-09-16

### Added
- **Nuevo módulo de extensión** (`backend/src/extension/`) para integración con complemento de navegador
- **Endpoint GET `/api/v1/extension/personas`** - Obtiene lista de personas con solicitudes HPS pendientes
- **Endpoint GET `/api/v1/extension/persona/{dni}`** - Obtiene datos detallados de una persona por DNI
- **Endpoint PUT `/api/v1/extension/solicitud/{dni}/enviada`** - Marca una solicitud como enviada
- **Modelos Pydantic** para respuestas de la API de extensión (`PersonaListResponse`, `PersonaDetailResponse`)
- **Servicio de extensión** con lógica de negocio para operaciones del complemento
- **Documentación completa** de la integración del complemento de navegador

### Changed
- **Dockerfile del backend** - Cambiado ENTRYPOINT por CMD para facilitar desarrollo
- **Integración en main.py** - Agregado router de extensión a la aplicación FastAPI
- **Filtro de estado** - Corregido de "en curso" a "pending" para coincidir con estados reales del sistema

### Fixed
- **Filtro de solicitudes** - Corregido estado inexistente "en curso" por "pending"
- **Estado de solicitud enviada** - Corregido estado "esperando respuesta" por "submitted" (estado oficial del sistema)
- **Compatibilidad de datos** - Mapeo correcto entre tabla `hps_requests` y formato esperado por complemento

### Technical Details
- **Base de datos**: Utiliza vista `solicitudes_hps` para mapear columnas
- **Estados**: Filtro por estado "pending" (solicitudes pendientes de envío)
- **API**: Endpoints REST sin autenticación para uso del complemento
- **Compatibilidad**: Cambios aditivos que no afectan funcionalidad existente

### Files Modified
- `backend/src/main.py` - Integración del router de extensión
- `backend/Dockerfile` - Configuración de desarrollo
- `backend/src/extension/` - Nuevo módulo completo

### Files Added
- `backend/src/extension/__init__.py`
- `backend/src/extension/router.py`
- `backend/src/extension/schemas.py`
- `backend/src/extension/service.py`
- `extensions/hps-plugin-prod/` - Complemento de navegador de producción
- `extensions/hps-plugin-test/` - Complemento de navegador de testing
- `extensions/README.md` - Documentación de los complementos
- `docs/desarrollo/integracion-complemento-navegador.md`
- `CHANGELOG.md`

### Files Removed
- `backend/test_password.py` - Archivo temporal de pruebas eliminado

## [Initial] - 2025-09-15

### Added
- Sistema HPS completo con backend FastAPI, frontend React y agente IA
- Autenticación JWT y gestión de usuarios
- Gestión de equipos y roles
- Sistema de solicitudes HPS con estados y flujos de trabajo
- Base de datos PostgreSQL con migraciones
- Docker Compose para orquestación de servicios
- Documentación de arquitectura y desarrollo
