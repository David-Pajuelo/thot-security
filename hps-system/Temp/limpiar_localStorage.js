// Script para limpiar localStorage del chat
// Ejecutar en la consola del navegador

console.log('🧹 Limpiando localStorage del chat...');

// Limpiar datos específicos del chat
localStorage.removeItem('hps-chat-storage');
localStorage.removeItem('hps_token');
localStorage.removeItem('hps_user');

console.log('✅ localStorage limpiado');
console.log('📋 Datos eliminados:');
console.log('- hps-chat-storage (mensajes del chat)');
console.log('- hps_token (token de autenticación)');
console.log('- hps_user (datos del usuario)');

console.log('🔄 Recarga la página para aplicar los cambios');



