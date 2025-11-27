# 🔐 **Persistencia de Sesión - Sistema HPS**

## 📋 **Descripción General**

El sistema HPS implementa un mecanismo robusto de persistencia de sesión que permite a los usuarios mantener su autenticación activa incluso después de recargar la página del navegador o cerrar/abrir nuevas pestañas.

## 🏗️ **Arquitectura de la Solución**

### **1. Almacenamiento Local**
- **Token JWT**: Se almacena en `localStorage` como `hps_token`
- **Datos del Usuario**: Se almacenan en `localStorage` como `hps_user`
- **Estado de Autenticación**: Se persiste usando Zustand con persistencia automática

### **2. Verificación Automática**
- **Al Iniciar**: Se verifica automáticamente el token al cargar la aplicación
- **Periódica**: Se verifica cada 5 minutos mientras la sesión esté activa
- **Al Recuperar Foco**: Se verifica cuando la ventana del navegador recupera el foco

### **3. Manejo de Estados**
- **`loading`**: Durante la carga inicial de la aplicación
- **`verifying`**: Durante la verificación del token
- **`isAuthenticated`**: Estado de autenticación del usuario
- **`error`**: Mensajes de error relacionados con la autenticación

## 🔧 **Implementación Técnica**

### **Store de Autenticación (`authStore.js`)**

```javascript
// Estado principal
const useAuthStore = create(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      user: null,
      token: null,
      loading: false,
      verifying: false,
      error: null,
      
      // Funciones principales
      initializeAuth: async () => { /* ... */ },
      verifyToken: async () => { /* ... */ },
      checkAndRefreshToken: async () => { /* ... */ },
      login: async (email, password) => { /* ... */ },
      logout: async () => { /* ... */ }
    }),
    {
      name: 'hps-auth-store',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        token: state.token
      })
    }
  )
);
```

### **Hook de Persistencia (`useSessionPersistence.js`)**

```javascript
export const useSessionPersistence = () => {
  const { isAuthenticated, checkAndRefreshToken, logout } = useAuthStore();
  
  useEffect(() => {
    if (isAuthenticated) {
      // Verificar cada 5 minutos
      const interval = setInterval(async () => {
        const isValid = await checkAndRefreshToken();
        if (!isValid) logout();
      }, 5 * 60 * 1000);
      
      // Verificar al recuperar foco
      const handleFocus = async () => {
        const isValid = await checkAndRefreshToken();
        if (!isValid) logout();
      };
      
      window.addEventListener('focus', handleFocus);
      
      return () => {
        clearInterval(interval);
        window.removeEventListener('focus', handleFocus);
      };
    }
  }, [isAuthenticated, checkAndRefreshToken, logout]);
};
```

### **Servicio de API (`apiService.js`)**

```javascript
// Interceptor para manejo automático de tokens
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('hps_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  }
);

// Interceptor para manejo de respuestas
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('hps_token');
      localStorage.removeItem('hps_user');
    }
    return Promise.reject(error);
  }
);
```

## 🚀 **Flujo de Funcionamiento**

### **1. Carga Inicial de la Aplicación**
```
App.js → useEffect → initializeAuth() → 
Verificar localStorage → Establecer estado optimista → 
Verificar token con backend → Confirmar estado final
```

### **2. Verificación Periódica**
```
useSessionPersistence → setInterval (5 min) → 
checkAndRefreshToken() → verifyToken() → 
Mantener o cerrar sesión según resultado
```

### **3. Recuperación de Foco**
```
Window focus event → handleFocus → 
checkAndRefreshToken() → verifyToken() → 
Mantener o cerrar sesión según resultado
```

### **4. Manejo de Errores**
```
Error de red → Mantener estado actual → 
Error 401 → Logout automático → 
Error de servidor → Mantener estado actual
```

## 🛡️ **Seguridad**

### **Protecciones Implementadas**
- **Verificación Periódica**: El token se verifica cada 5 minutos
- **Verificación al Recuperar Foco**: Se verifica cuando el usuario regresa a la pestaña
- **Logout Automático**: Se cierra la sesión automáticamente si el token es inválido
- **Limpieza de Datos**: Se eliminan los datos del localStorage en caso de error 401

### **Manejo de Tokens Expirados**
- **Detección Automática**: El backend retorna 401 si el token ha expirado
- **Respuesta Inmediata**: El frontend detecta el 401 y cierra la sesión
- **Redirección**: El usuario es redirigido al login automáticamente

## 📱 **Experiencia del Usuario**

### **Ventajas**
- ✅ **No hay necesidad de relogin** al recargar la página
- ✅ **Sesión persistente** entre pestañas del navegador
- ✅ **Verificación automática** de la validez del token
- ✅ **Logout automático** si la sesión expira
- ✅ **Estado visual claro** durante la verificación

### **Estados Visuales**
- **🔄 Cargando**: Durante la carga inicial de la aplicación
- **🔍 Verificando**: Durante la verificación del token
- **✅ Autenticado**: Usuario autenticado correctamente
- **❌ Error**: Problemas de autenticación

## 🔍 **Debugging y Troubleshooting**

### **Logs de Consola**
```javascript
// Verificar estado de autenticación
console.log('Auth State:', useAuthStore.getState());

// Verificar localStorage
console.log('Token:', localStorage.getItem('hps_token'));
console.log('User:', localStorage.getItem('hps_user'));
```

### **Problemas Comunes**
1. **Token no se guarda**: Verificar que el login retorne `access_token`
2. **Verificación falla**: Revisar logs del backend para errores 500
3. **Logout automático**: Verificar que el token no haya expirado
4. **Estado inconsistente**: Limpiar localStorage y relogin

## 📚 **Referencias Técnicas**

- **Zustand**: Gestión de estado con persistencia
- **JWT**: Tokens de autenticación
- **localStorage**: Almacenamiento local del navegador
- **Axios Interceptors**: Manejo automático de requests/responses
- **React Hooks**: useEffect para efectos secundarios

## 🎯 **Próximas Mejoras**

- [ ] **Refresh Tokens**: Implementar renovación automática de tokens
- [ ] **Offline Support**: Cache de datos para funcionamiento offline
- [ ] **Multi-tab Sync**: Sincronización de estado entre pestañas
- [ ] **Session Timeout**: Configuración personalizable del timeout de sesión









