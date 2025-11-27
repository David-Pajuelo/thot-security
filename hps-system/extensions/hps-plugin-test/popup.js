const select = document.getElementById('personaSelect');
const rellenarBtn = document.getElementById('rellenarBtn');
const solicitudBtn = document.getElementById('solicitudEnviadaBtn');
let personas = [];

chrome.runtime.sendMessage({ action: 'getPersonas' }, (response) => {
  if (chrome.runtime.lastError) {
    select.innerHTML = `<option>Error de conexión: ${chrome.runtime.lastError.message}</option>`;
    return;
  }

  if (!response) {
    select.innerHTML = `<option>Error: no se recibió respuesta del background</option>`;
    return;
  }

  if (response.error) {
    select.innerHTML = `<option>Error al cargar: ${response.error}</option>`;
    return;
  }

  console.log("Popup: respuesta recibida para getPersonas:", response);

  personas = response.data;
  select.innerHTML = '';

  personas.forEach(p => {
    const option = document.createElement('option');
    option.value = p.numero_documento;
    option.textContent = `${p.nombre} ${p.primer_apellido} ${p.segundo_apellido}`;
    select.appendChild(option);
  });
});

rellenarBtn.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  console.log('Pestaña activa URL:', tab.url);

  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ['content.js']
  });

  chrome.tabs.sendMessage(tab.id, {
    action: 'rellenarFormulario',
    dni: select.value
  }, (response) => {
    if (chrome.runtime.lastError) {
      console.error('Error enviando mensaje:', chrome.runtime.lastError.message);
    } else {
      console.log('Respuesta del content script:', response);
    }
  });
});

solicitudBtn.addEventListener('click', () => {
  const dni = select.value;
  if (!dni) return alert('Selecciona una persona');

  chrome.runtime.sendMessage({
    action: 'marcarSolicitudEnviada',
    dni: dni
  }, (response) => {
    if (response.error) {
      alert(`Error al actualizar: ${response.error}`);
    } else {
      alert('Solicitud marcada como enviada');

      // 🔄 Recargar lista de personas tras actualizar
      chrome.runtime.sendMessage({ action: 'getPersonas' }, (response) => {
        if (response.error || !response.data) {
          select.innerHTML = `<option>Error recargando lista</option>`;
        } else {
          personas = response.data;
          select.innerHTML = '';
          personas.forEach(p => {
            const option = document.createElement('option');
            option.value = p.numero_documento;
            option.textContent = `${p.nombre} ${p.primer_apellido} ${p.segundo_apellido}`;
            select.appendChild(option);
          });
        }
      });
    }
  });
});
