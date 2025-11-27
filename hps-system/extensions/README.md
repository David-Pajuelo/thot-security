# 🔌 Complementos de Navegador HPS

Esta carpeta contiene los complementos de navegador (Chrome Extensions) que se integran con el sistema HPS para automatizar el rellenado de formularios.

## 📁 Estructura

```
extensions/
├── hps-plugin-prod/     # Complemento de producción
├── hps-plugin-test/     # Complemento de testing
└── README.md           # Este archivo
```

## 🎯 Funcionalidades

### Automatización de Formularios
- **Relleno automático**: Completa formularios con datos de personas registradas
- **Selección de personas**: Desplegable con lista de solicitudes pendientes
- **Validación de datos**: Verificación de campos antes del envío

### Gestión de Solicitudes
- **Listado de personas**: Muestra solicitudes con estado "pending"
- **Marcado de envío**: Actualiza estado a "submitted"
- **Sincronización**: Comunicación en tiempo real con el backend HPS

## 🔧 Instalación

### Requisitos
- Google Chrome o navegador compatible
- Sistema HPS funcionando en `http://localhost:8001`
- Permisos para instalar extensiones de desarrollador

### Pasos de Instalación

1. **Abrir Chrome** y navegar a `chrome://extensions/`
2. **Activar modo desarrollador** (toggle en la esquina superior derecha)
3. **Cargar extensión**:
   - Para **producción**: Seleccionar carpeta `hps-plugin-prod`
   - Para **testing**: Seleccionar carpeta `hps-plugin-test`
4. **Verificar instalación**: El icono del complemento debe aparecer en la barra de herramientas

## 🚀 Uso

### Configuración Inicial
1. **Asegurar que el backend HPS esté funcionando**
2. **Verificar conectividad** en `http://localhost:8001`
3. **Cargar página de formulario** en `https://automation.idiaicox.com/form/*`

### Flujo de Trabajo
1. **Hacer clic en el icono** del complemento en la barra de herramientas
2. **Seleccionar persona** del desplegable (solo aparecen solicitudes pendientes)
3. **Hacer clic en "Rellenar Formulario"** para completar automáticamente
4. **Revisar datos** y hacer clic en "Solicitud Enviada" cuando corresponda (cambia estado a "submitted")

## 📋 Archivos del Complemento

### Archivos Principales
- **`manifest.json`** - Configuración y permisos del complemento
- **`popup.html`** - Interfaz de usuario del popup
- **`popup.js`** - Lógica del popup y comunicación con background
- **`background.js`** - Service worker para comunicación con API
- **`content.js`** - Script inyectado para manipular formularios
- **`apiClient.js`** - Cliente para comunicación con backend HPS

### Configuración
- **URL del backend**: `http://localhost:8001/api/v1/extension`
- **Permisos**: Acceso a `http://localhost:8001/*` y `https://automation.idiaicox.com/*`
- **Host permissions**: Configurados en `manifest.json`

## 🔄 Diferencias entre Versiones

### hps-plugin-prod
- **Propósito**: Uso en producción
- **Configuración**: Optimizada para rendimiento
- **Logging**: Mínimo para producción

### hps-plugin-test
- **Propósito**: Testing y desarrollo
- **Configuración**: Incluye logging detallado
- **Debugging**: Herramientas adicionales para desarrollo

## 🐛 Troubleshooting

### Problemas Comunes

#### El desplegable está vacío
- **Causa**: No hay solicitudes con estado "pending"
- **Solución**: Verificar que el backend esté funcionando y tenga datos

#### Error de conexión
- **Causa**: Backend no disponible en `http://localhost:8001`
- **Solución**: Iniciar el sistema HPS con `docker-compose up -d`

#### Formulario no se rellena
- **Causa**: Página no es la correcta o elementos no encontrados
- **Solución**: Verificar que estás en `https://automation.idiaicox.com/form/*`

### Logs de Debug
1. **Abrir DevTools** (F12)
2. **Ir a Console** para ver logs del complemento
3. **Revisar Service Worker** en `chrome://extensions/` → Detalles → Inspeccionar vistas

## 🔗 Integración con Backend

### Endpoints Utilizados
- `GET /api/v1/extension/personas` - Lista de personas pendientes
- `GET /api/v1/extension/persona/{dni}` - Datos de persona específica
- `PUT /api/v1/extension/solicitud/{dni}/enviada` - Marcar como enviada

### Flujo de Datos
1. **Complemento** → `apiClient.getPersonas()` → **Backend**
2. **Backend** → Consulta BD con filtro `WHERE estado = 'pending'` → **Complemento**
3. **Complemento** → Muestra lista en desplegable
4. **Usuario** → Selecciona persona → **Complemento** rellena formulario

## 📚 Documentación Relacionada

- [Integración del Complemento de Navegador](../docs/desarrollo/integracion-complemento-navegador.md)
- [Documentación del Backend](../README.md)
- [API Reference](../docs/desarrollo/integracion-complemento-navegador.md#endpoints-implementados)

## 🛠️ Desarrollo

### Modificar el Complemento
1. **Editar archivos** en la carpeta correspondiente
2. **Recargar extensión** en `chrome://extensions/`
3. **Probar cambios** en la página de formulario

### Agregar Nuevas Funcionalidades
1. **Actualizar `manifest.json`** si se necesitan nuevos permisos
2. **Modificar `apiClient.js`** para nuevos endpoints
3. **Actualizar `popup.js`** para nueva UI
4. **Probar en ambas versiones** (prod y test)

## 📝 Notas de Versión

### v1.0.0 (2025-09-16)
- ✅ Integración inicial con sistema HPS
- ✅ Relleno automático de formularios
- ✅ Gestión de estados de solicitudes
- ✅ Versiones separadas para prod y test
- ✅ Documentación completa
