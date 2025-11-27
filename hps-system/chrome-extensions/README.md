# HPS System - Chrome Extensions

Este directorio contiene las extensiones de Chrome para el sistema HPS (Habilitación Personal de Seguridad).

## Estructura

- **`hps-plugin-prod/`** - Extensión para producción
- **`hps-plugin-test/`** - Extensión para testing/desarrollo

## Instalación

### Desarrollo
1. Abrir Chrome y ir a `chrome://extensions/`
2. Activar "Modo de desarrollador"
3. Hacer clic en "Cargar extensión sin empaquetar"
4. Seleccionar la carpeta `hps-plugin-test/`

### Producción
1. Abrir Chrome y ir a `chrome://extensions/`
2. Activar "Modo de desarrollador"
3. Hacer clic en "Cargar extensión sin empaquetar"
4. Seleccionar la carpeta `hps-plugin-prod/`

## Funcionalidades

Las extensiones permiten:
- Conectar directamente con el servicio HPS
- Interactuar con el sistema desde cualquier página web
- Funcionalidades específicas del sistema HPS

## Archivos

- **`manifest.json`** - Configuración de la extensión
- **`popup.html/popup.js`** - Interfaz del popup
- **`background.js`** - Script de fondo
- **`content.js`** - Script de contenido
- **`apiClient.js`** - Cliente para comunicación con la API

## Configuración

Cada extensión está configurada para conectarse con su respectivo entorno:
- **Test**: Entorno de desarrollo
- **Prod**: Entorno de producción
