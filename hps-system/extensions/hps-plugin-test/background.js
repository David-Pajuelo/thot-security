import { apiClient } from './apiClient.js';

console.log('Background service worker iniciado');

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Mensaje recibido en background:', message);

  if (message.action === 'getPersonas') {
    apiClient.getPersonas()
      .then(data => {
        console.log("Resultados filtrados:", data);
        console.log('Datos recibidos de API:', data);
        sendResponse({ data });
      })
      .catch(e => {
        console.error('Excepción en getPersonas:', e.message);
        sendResponse({ error: e.message });
      });
    return true; // Mantiene el canal abierto para respuesta async

  } else if (message.action === 'getDatosPorDni') {
    const { dni } = message; // Usamos dni como numero_documento
    apiClient.getPersonaPorDni(dni)
      .then(data => {
        console.log('Datos individuales recibidos:', data);
        sendResponse({ data });
      })
      .catch(e => {
        console.error('Excepción en getDatosPorDni:', e.message);
        sendResponse({ error: e.message });
      });
    return true;

  } else if (message.action === 'marcarSolicitudEnviada') {
    const { dni } = message;
    apiClient.marcarSolicitudEnviada(dni)
      .then(response => {
        console.log(`Solicitud marcada como enviada para DNI ${dni}`);
        sendResponse({ success: true });
      })
      .catch(e => {
        console.error('Excepción en marcarSolicitudEnviada:', e.message);
        sendResponse({ error: e.message });
      });
    return true;
  
  } else {
    console.warn('Acción no reconocida:', message.action);
    sendResponse({ error: 'Acción no reconocida' });
    return false;
  }
});
