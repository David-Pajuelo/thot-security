/**
 * Utilidades para manejo de errores
 */

/**
 * Convierte cualquier tipo de error a string para renderizado seguro en React
 * @param {any} error - El error a convertir
 * @returns {string} - String seguro para renderizar
 */
export const formatErrorForDisplay = (error) => {
  // Si es null o undefined
  if (!error) {
    return 'Error desconocido';
  }
  
  // Si es string, devolverlo directamente
  if (typeof error === 'string') {
    return error;
  }
  
  // Si es un Event (DOM Event)
  if (error instanceof Event) {
    return 'Error de conexión. Por favor, intenta de nuevo.';
  }
  
  // Si es un objeto
  if (error && typeof error === 'object') {
    // Si es un objeto de error de validación con estructura específica
    if (error.type && error.loc && error.msg) {
      return `Error de validación: ${error.msg}`;
    }
    
    // Si tiene una propiedad detail
    if (error.detail) {
      return typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail);
    }
    
    // Si tiene una propiedad message
    if (error.message) {
      return error.message;
    }
    
    // Si es un Error estándar
    if (error instanceof Error) {
      return error.message || 'Error desconocido';
    }
    
    // Si es un array de errores
    if (Array.isArray(error)) {
      return error.map(e => typeof e === 'string' ? e : JSON.stringify(e)).join(', ');
    }
    
    // Si tiene toString personalizado
    if (error.toString && error.toString !== Object.prototype.toString) {
      const str = error.toString();
      if (str !== '[object Object]' && str !== '[object Event]') {
        return str;
      }
    }
    
    // Como último recurso, intentar convertir a JSON
    try {
      const json = JSON.stringify(error);
      if (json !== '{}' && json !== 'null') {
        return json;
      }
    } catch (e) {
      // Si falla la serialización, usar toString genérico
    }
  }
  
  return 'Error desconocido';
};
