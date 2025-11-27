// Elementos del DOM
const tabs = document.querySelectorAll('.tab');
const tabContents = document.querySelectorAll('.tab-content');

// Elementos de Solicitudes
const solicitudesSelect = document.getElementById('solicitudesSelect');
const rellenarBtn = document.getElementById('rellenarBtn');
const solicitudBtn = document.getElementById('solicitudEnviadaBtn');

// Elementos de Traslados
const trasladosSelect = document.getElementById('trasladosSelect');
const descargarPdfBtn = document.getElementById('descargarPdfBtn');
const trasladoBtn = document.getElementById('trasladoEnviadoBtn');

// Variables globales
let solicitudes = [];
let traslados = [];
let currentTab = 'solicitudes';

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
  initializeTabs();
  loadData();
  setupEventListeners();
});

// Configurar pestañas
function initializeTabs() {
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const tabName = tab.dataset.tab;
      switchTab(tabName);
    });
  });
}

// Cambiar pestaña
function switchTab(tabName) {
  // Actualizar pestañas
  tabs.forEach(tab => {
    tab.classList.toggle('active', tab.dataset.tab === tabName);
  });
  
  // Actualizar contenido
  tabContents.forEach(content => {
    content.classList.toggle('active', content.id === `${tabName}-content`);
  });
  
  currentTab = tabName;
}

// Cargar datos iniciales
function loadData() {
  loadSolicitudes();
  loadTraslados();
}

// Cargar solicitudes
function loadSolicitudes() {
  chrome.runtime.sendMessage({ action: 'getSolicitudes' }, (response) => {
    if (chrome.runtime.lastError) {
      solicitudesSelect.innerHTML = `<option>Error de conexión: ${chrome.runtime.lastError.message}</option>`;
      return;
    }

    if (!response) {
      solicitudesSelect.innerHTML = `<option>Error: no se recibió respuesta</option>`;
      return;
    }

    if (response.error) {
      solicitudesSelect.innerHTML = `<option>Error al cargar: ${response.error}</option>`;
      return;
    }

    console.log("Solicitudes cargadas:", response);
    solicitudes = response.data || [];
    console.log("Datos de solicitudes:", solicitudes);
    populateSelect(solicitudesSelect, solicitudes);
  });
}

// Cargar traslados
function loadTraslados() {
  chrome.runtime.sendMessage({ action: 'getTraslados' }, (response) => {
    if (chrome.runtime.lastError) {
      trasladosSelect.innerHTML = `<option>Error de conexión: ${chrome.runtime.lastError.message}</option>`;
      return;
    }

    if (!response) {
      trasladosSelect.innerHTML = `<option>Error: no se recibió respuesta</option>`;
      return;
    }

    if (response.error) {
      trasladosSelect.innerHTML = `<option>Error al cargar: ${response.error}</option>`;
      return;
    }

    console.log("Traslados cargados:", response);
    traslados = response.data || [];
    console.log("Datos de traslados:", traslados);
    populateSelect(trasladosSelect, traslados);
  });
}

// Poblar select con datos
function populateSelect(selectElement, data) {
  selectElement.innerHTML = '';
  
  if (data.length === 0) {
    selectElement.innerHTML = '<option>No hay datos disponibles</option>';
    return;
  }

  data.forEach(item => {
    const option = document.createElement('option');
    option.value = item.numero_documento || item.document_number;
    option.textContent = `${item.nombre || item.first_name} ${item.primer_apellido || item.first_last_name} ${item.segundo_apellido || item.second_last_name || ''}`.trim();
    selectElement.appendChild(option);
  });
}

// Configurar event listeners
function setupEventListeners() {
  // Botón rellenar formulario (solo para solicitudes)
  rellenarBtn.addEventListener('click', async () => {
    const dni = solicitudesSelect.value;
    if (!dni) return alert('Selecciona una persona');

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    console.log('Pestaña activa URL:', tab.url);

    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['content.js']
    });

    chrome.tabs.sendMessage(tab.id, {
      action: 'rellenarFormulario',
      dni: dni
    }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('Error enviando mensaje:', chrome.runtime.lastError.message);
      } else {
        console.log('Respuesta del content script:', response);
      }
    });
  });

  // Botón solicitud enviada
  solicitudBtn.addEventListener('click', () => {
    const dni = solicitudesSelect.value;
    if (!dni) return alert('Selecciona una persona');

    chrome.runtime.sendMessage({
      action: 'marcarSolicitudEnviada',
      dni: dni
    }, (response) => {
      if (response.error) {
        alert(`Error al actualizar: ${response.error}`);
      } else {
        alert('Solicitud marcada como enviada');
        loadSolicitudes(); // Recargar lista
      }
    });
  });

  // Botón descargar PDF (solo para traslados)
  descargarPdfBtn.addEventListener('click', () => {
    const dni = trasladosSelect.value;
    if (!dni) return alert('Selecciona una persona');

    // Deshabilitar botón temporalmente
    descargarPdfBtn.disabled = true;
    descargarPdfBtn.textContent = 'Descargando...';

    chrome.runtime.sendMessage({
      action: 'descargarPdf',
      dni: dni
    }, (response) => {
      // Rehabilitar botón
      descargarPdfBtn.disabled = false;
      descargarPdfBtn.textContent = 'Descargar PDF';

      if (response.error) {
        alert(`Error al descargar PDF: ${response.error}`);
      } else {
        // No mostrar alert, el PDF se abre automáticamente
        console.log('PDF abierto en nueva pestaña');
      }
    });
  });

  // Botón traslado enviado
  trasladoBtn.addEventListener('click', () => {
    const dni = trasladosSelect.value;
    if (!dni) return alert('Selecciona una persona');

    chrome.runtime.sendMessage({
      action: 'marcarTrasladoEnviado',
      dni: dni
    }, (response) => {
      if (response.error) {
        alert(`Error al actualizar: ${response.error}`);
      } else {
        alert('Traslado marcado como enviado');
        loadTraslados(); // Recargar lista
      }
    });
  });
}
