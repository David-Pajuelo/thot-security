import { apiClient } from './apiClient.js';

console.log('Background service worker iniciado');

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Mensaje recibido en background:', message);

  if (message.action === 'getSolicitudes') {
    apiClient.getSolicitudes()
      .then(data => {
        console.log("Solicitudes cargadas:", data);
        console.log("Número de solicitudes:", data.length);
        sendResponse({ data });
      })
      .catch(e => {
        console.error('Excepción en getSolicitudes:', e);
        sendResponse({ error: e.message || e.toString() });
      });
    return true;

  } else if (message.action === 'getTraslados') {
    apiClient.getTraslados()
      .then(data => {
        console.log("Traslados cargados:", data);
        console.log("Número de traslados:", data.length);
        sendResponse({ data });
      })
      .catch(e => {
        console.error('Excepción en getTraslados:', e);
        sendResponse({ error: e.message || e.toString() });
      });
    return true;

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

  } else if (message.action === 'marcarTrasladoEnviado') {
    const { dni } = message;
    apiClient.marcarTrasladoEnviado(dni)
      .then(response => {
        console.log(`Traslado marcado como enviado para DNI ${dni}`);
        sendResponse({ success: true });
      })
      .catch(e => {
        console.error('Excepción en marcarTrasladoEnviado:', e.message);
        sendResponse({ error: e.message });
      });
    return true;

  } else if (message.action === 'descargarPdf') {
    const { dni } = message;
    apiClient.descargarPdf(dni)
      .then(response => {
        console.log(`URL del PDF obtenida para DNI ${dni}:`, response.url);
        
        // Crear nueva pestaña con la URL del PDF
        chrome.tabs.create({ url: response.url }, (tab) => {
          if (chrome.runtime.lastError) {
            console.error('Error creando pestaña:', chrome.runtime.lastError.message);
            sendResponse({ error: chrome.runtime.lastError.message });
          } else {
            console.log(`PDF abierto en nueva pestaña (ID: ${tab.id})`);
            sendResponse({ success: true, tabId: tab.id });
          }
        });
      })
      .catch(e => {
        console.error('Excepción en descargarPdf:', e);
        sendResponse({ error: e.message || e.toString() });
      });
    return true;
  
  } else {
    console.warn('Acción no reconocida:', message.action);
    sendResponse({ error: 'Acción no reconocida' });
    return false;
  }
});
