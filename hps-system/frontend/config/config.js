// Configuración del frontend
const config = {
  // URLs de la API
  API_BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8001',
  WS_BASE_URL: process.env.REACT_APP_WS_URL || 'ws://localhost:8001',
  
  // Configuración de la aplicación
  APP_NAME: 'Sistema HPS',
  APP_VERSION: '1.0.0',
  
  // Configuración de desarrollo
  DEBUG: process.env.NODE_ENV === 'development',
  
  // Timeouts
  API_TIMEOUT: 10000,
  WS_TIMEOUT: 5000,
};

export default config;
