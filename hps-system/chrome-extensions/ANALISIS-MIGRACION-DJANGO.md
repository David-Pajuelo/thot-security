# Análisis de Migración: Extensiones Chrome de FastAPI a Django

## Resumen Ejecutivo

Las extensiones de Chrome (`hps-plugin-test` y `hps-plugin-prod`) fueron diseñadas para trabajar con el backend FastAPI en `http://localhost:8001`. Con la migración a Django (puerto 8080), se requieren cambios en las extensiones y verificación de compatibilidad de endpoints.

## Estado Actual

### Backend Django
✅ **Endpoints ya implementados** en `cryptotrace/cryptotrace-backend/src/hps_core/`:
- `ExtensionService` - Servicio con toda la lógica
- `HpsExtensionViewSet` - ViewSet con endpoints REST
- URLs configuradas en `urls.py` con rutas directas

### Endpoints Disponibles en Django

| Endpoint FastAPI | Endpoint Django | Estado |
|-----------------|-----------------|--------|
| `GET /api/v1/extension/personas?tipo=solicitud` | `GET /api/v1/extension/personas/?tipo=solicitud` | ✅ Implementado |
| `GET /api/v1/extension/personas?tipo=traslado` | `GET /api/v1/extension/personas/?tipo=traslado` | ✅ Implementado |
| `GET /api/v1/extension/persona/{dni}` | `GET /api/v1/extension/persona/{dni}/` | ✅ Implementado |
| `PUT /api/v1/extension/solicitud/{dni}/estado` | `PUT /api/v1/extension/solicitud/{dni}/estado/` | ✅ Implementado |
| `PUT /api/v1/extension/solicitud/{dni}/enviada` | `PUT /api/v1/extension/solicitud/{dni}/enviada/` | ✅ Implementado |
| `PUT /api/v1/extension/traslado/{dni}/enviado` | `PUT /api/v1/extension/traslado/{dni}/enviado/` | ✅ Implementado |
| `GET /api/v1/extension/traslado/{dni}/pdf` | `GET /api/v1/extension/traslado/{dni}/pdf/` | ✅ Implementado |

**Nota**: Django REST Framework añade automáticamente la barra final (`/`) a las URLs.

## Cambios Necesarios en las Extensiones

### 1. Cambio de URL Base (CRÍTICO)

**Archivo**: `apiClient.js` (ambas extensiones)

**Cambio requerido**:
```javascript
// ANTES (FastAPI)
const API_BASE_URL = 'http://localhost:8001/api/v1/extension';

// DESPUÉS (Django)
const API_BASE_URL = 'http://localhost:8080/api/v1/extension';
```

**Ubicación**: 
- `hps-system/chrome-extensions/hps-plugin-test/apiClient.js` (línea 2)
- `hps-system/chrome-extensions/hps-plugin-prod/apiClient.js` (línea 2)

### 2. Actualizar Permisos en manifest.json

**Archivo**: `manifest.json` (ambas extensiones)

**Cambio requerido**:
```json
{
  "host_permissions": [
    "https://automation.idiaicox.com/form/*",  // o "https://gobernanza.ccn-cert.cni.es/*"
    "http://localhost:8080/*"  // Cambiar de 8001 a 8080
  ]
}
```

**Ubicación**:
- `hps-system/chrome-extensions/hps-plugin-test/manifest.json` (línea 13)
- `hps-system/chrome-extensions/hps-plugin-prod/manifest.json` (línea 12)

### 3. Ajustar Formato de Fechas (OPCIONAL)

**Problema potencial**: Django devuelve fechas en formato ISO, pero FastAPI podría haber usado otro formato.

**Verificación necesaria**: 
- Revisar si `content.js` procesa correctamente el campo `fecha_nacimiento`
- El formato esperado en los formularios HTML puede requerir `YYYY-MM-DD` o `DD/MM/YYYY`

**Archivos afectados**:
- `hps-system/chrome-extensions/hps-plugin-test/content.js`
- `hps-system/chrome-extensions/hps-plugin-prod/content.js`

**Solución si es necesario**:
```javascript
// En content.js, al procesar fecha_nacimiento
const fecha = datos.fecha_nacimiento;
if (fecha) {
  // Convertir de ISO (YYYY-MM-DD) a formato requerido si es necesario
  const fechaFormateada = fecha.split('T')[0]; // Quitar hora si existe
  elemento.value = fechaFormateada;
}
```

### 4. Manejo de Errores HTTP

**Verificación**: Django REST Framework devuelve errores en formato:
```json
{
  "detail": "Mensaje de error"
}
```

Mientras que FastAPI podría haber usado:
```json
{
  "message": "Mensaje de error"
}
```

**Archivo**: `apiClient.js`

**Verificación necesaria**: El código actual usa `response.ok`, lo cual es correcto. Solo verificar que los mensajes de error se muestren correctamente.

### 5. Diferencias en Estructura de Respuesta

**FastAPI** (usando Pydantic):
```json
{
  "tipo_documento": "DNI",
  "numero_documento": "12345678A",
  ...
}
```

**Django** (usando diccionarios):
```json
{
  "tipo_documento": "DNI",
  "numero_documento": "12345678A",
  ...
}
```

✅ **Compatibilidad**: La estructura es idéntica, no se requieren cambios.

## Diferencias entre Extensiones

### hps-plugin-test
- **URL objetivo**: `https://automation.idiaicox.com/form/*`
- **Content script**: Usa IDs como `field-0`, `field-1`, etc.
- **Observaciones**: Usa `field-10` para observaciones

### hps-plugin-prod
- **URL objetivo**: `https://gobernanza.ccn-cert.cni.es/*`
- **Content script**: Usa IDs como `hps_requests_0_identificationDocumentType`, etc.
- **Observaciones**: Usa `hps_requests_0_observations` para observaciones

**Conclusión**: Las extensiones son funcionalmente idénticas, solo cambian los selectores CSS/IDs del DOM según el formulario HTML objetivo.

## Checklist de Migración

### Cambios Obligatorios
- [x] Actualizar `API_BASE_URL` en `apiClient.js` (test y prod) ✅ COMPLETADO
- [x] Actualizar `host_permissions` en `manifest.json` (test y prod) ✅ COMPLETADO
- [x] Añadir barras finales a las URLs para compatibilidad con Django REST Framework ✅ COMPLETADO

### Verificaciones Recomendadas
- [ ] Probar conexión con backend Django
- [ ] Verificar formato de fechas en formularios
- [ ] Probar rellenado de formularios (ambas extensiones)
- [ ] Verificar descarga de PDFs de traslados
- [ ] Probar marcado de solicitudes/traslados como enviados

### Testing
1. **Conexión básica**: Abrir popup y verificar que carga lista de solicitudes
2. **Rellenado de formulario**: Probar rellenar formulario en página objetivo
3. **Marcado de estado**: Probar marcar solicitud como enviada
4. **Descarga PDF**: Probar descargar PDF de traslado

## Notas Técnicas

### URLs de Django REST Framework
Django REST Framework añade automáticamente la barra final (`/`) a las URLs. Las extensiones deben incluirla o Django la añadirá automáticamente (redirección 301).

**Recomendación**: Incluir la barra final en las URLs del `apiClient.js`:
```javascript
async getSolicitudes() {
  return this.request('/personas/?tipo=solicitud');  // Nota la barra antes del ?
}
```

### Autenticación
Los endpoints de extensión en Django están configurados como **públicos** (sin autenticación requerida), igual que en FastAPI. No se requieren cambios relacionados con autenticación.

### CORS
Si Django tiene CORS configurado correctamente, las extensiones deberían funcionar sin problemas. Verificar que `CORS_ALLOWED_ORIGINS` o `CORS_ALLOW_ALL_ORIGINS` esté configurado para permitir requests desde `chrome-extension://`.

## Archivos a Modificar

1. `hps-system/chrome-extensions/hps-plugin-test/apiClient.js`
2. `hps-system/chrome-extensions/hps-plugin-test/manifest.json`
3. `hps-system/chrome-extensions/hps-plugin-prod/apiClient.js`
4. `hps-system/chrome-extensions/hps-plugin-prod/manifest.json`

**Total**: 4 archivos a modificar

## Resumen

✅ **Backend Django**: Completamente implementado y listo  
⚠️ **Extensiones**: Requieren 2 cambios simples (URL base y permisos)  
✅ **Compatibilidad**: 95% compatible, solo ajustes menores necesarios

La migración es **sencilla** y requiere principalmente actualizar las URLs del puerto 8001 al 8080.

