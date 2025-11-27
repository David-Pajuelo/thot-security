# Sistema HPS - Frontend

Frontend del Sistema de Habilitación Personal de Seguridad desarrollado en React.

## 🚀 Inicio Rápido

### Prerrequisitos
- Node.js 18+
- npm o yarn

### Instalación
```bash
# Instalar dependencias
npm install

# Ejecutar en modo desarrollo
npm start

# Construir para producción
npm run build
```

### Variables de Entorno
```bash
REACT_APP_API_URL=http://localhost:8001
REACT_APP_WS_URL=ws://localhost:8001
```

## 📁 Estructura del Proyecto
```
frontend/
├── public/          # Archivos estáticos
├── src/             # Código fuente
│   ├── components/  # Componentes React
│   ├── pages/       # Páginas de la aplicación
│   ├── services/    # Servicios API
│   ├── hooks/       # Custom hooks
│   ├── context/     # Context API
│   └── utils/       # Utilidades
├── config/          # Configuración
└── package.json     # Dependencias
```

## 🔧 Scripts Disponibles
- `npm start` - Ejecutar en modo desarrollo
- `npm run build` - Construir para producción
- `npm test` - Ejecutar tests
- `npm run eject` - Eyectar configuración (irreversible)

## 🌐 Puertos
- **Desarrollo**: 3000
- **Backend API**: 8001
- **WebSocket**: 8001
