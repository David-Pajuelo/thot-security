
console.log('Content script cargado');

chrome.runtime.onMessage.addListener(async (message, sender, sendResponse) => {
  if (message.action === 'rellenarFormulario') {
    const numeroDocumento = message.dni;
    console.log('Content script: recibida acción rellenarFormulario para:', numeroDocumento);

    chrome.runtime.sendMessage({ action: 'getDatosPorDni', dni: numeroDocumento }, (response) => {
      if (response.error) {
        console.error("Content script: Error obteniendo datos:", response.error);
        sendResponse({ error: response.error });
        return;
      }

      const datos = response.data;
      if (!datos) {
        console.warn('Content script: No se recibieron datos para el número documento:', numeroDocumento);
        sendResponse({ error: 'No hay datos para ese número' });
        return;
      }

      console.log('Content script: Datos recibidos para rellenar:', datos);

      // 1. Valor fijo para "Cargo/Perfil en Empresa"
      const perfilEmpresa = document.getElementById('hps_requests_0_companyProfile');
      if (perfilEmpresa) {
        perfilEmpresa.value = '211';  // value para PERSONAL DEL CONTRATISTA
        perfilEmpresa.dispatchEvent(new Event('change', { bubbles: true }));
      }

      // 2. Valor fijo para "Grado único HPS solicitada"
      const gradoUnico = document.getElementById('hps_requests_0_hpsUniqueGrade');
      if (gradoUnico) {
        gradoUnico.value = '220';  // value para RESERVADO o equivalente (SECRET)
        gradoUnico.dispatchEvent(new Event('change', { bubbles: true }));
      }

      // 3. Valor fijo para "El interesado es personal laboral ajeno"
      const personalAjeno = document.getElementById('hps_requests_0_isCompanyProfileOutside');
      if (personalAjeno) {
        personalAjeno.value = '231';  // value para No
        personalAjeno.dispatchEvent(new Event('change', { bubbles: true }));
      }

      // 4. Condición: si nacionalidad === "ESPAÑA", poner "No" en Solicitud al extranjero
      if (datos.nacionalidad && datos.nacionalidad.toUpperCase() === 'ESPAÑA') {
        const solicitudExtranjero = document.getElementById('hps_requests_0_foreignApplication');
        if (solicitudExtranjero) {
          solicitudExtranjero.value = '231'; // Valor para No
          solicitudExtranjero.dispatchEvent(new Event('change', { bubbles: true }));
        }
      } else {
        const solicitudExtranjero = document.getElementById('hps_requests_0_foreignApplication');
        if (solicitudExtranjero) {
          solicitudExtranjero.value = '230'; // Valor para Sí
          solicitudExtranjero.dispatchEvent(new Event('change', { bubbles: true }));
        }
      }

      // 5. Observaciones.
      const observations = document.getElementById('field-8');
      if (observations) {
        const nombreCompleto = `${datos.nombre} ${datos.primer_apellido} ${datos.segundo_apellido}`;
        observations.value = `Se solicita nueva HPS para nuestro compañero ${nombreCompleto}, ya que va a participar en proyectos para los que necesita acceso a documentación clasificada.`;
        observations.dispatchEvent(new Event('input', { bubbles: true }));
      }


      // Configuración inputs
      const campoConfig = [
        { id: 'field-0', tipo: 'select', key: 'tipo_documento' },
        { id: 'field-1', tipo: 'input', key: 'numero_documento' },
        { id: 'field-2', tipo: 'input', key: 'fecha_nacimiento' },
        { id: 'field-3', tipo: 'input', key: 'nombre' },
        { id: 'field-4', tipo: 'input', key: 'primer_apellido' },
        { id: 'field-5', tipo: 'input', key: 'segundo_apellido' },
        { id: 'field-6', tipo: 'input', key: 'correo' },
        { id: 'field-7', tipo: 'select', key: 'nacionalidad' },
        // Para añadir mas campos:
        // { id: '', tipo: 'input', key: 'telefono' },

      ];

      // 🔄 Función para actualizar campos
      const actualizarCampo = ({ id, tipo, key }) => {
        const elemento = document.getElementById(id);
        const valor = datos[key];

        if (!elemento || valor == null) return;

        elemento.value = valor;

        // Disparar el evento adecuado
        const evento = tipo === 'select'
          ? new Event('change', { bubbles: true })
          : new Event('input', { bubbles: true });

        elemento.dispatchEvent(evento);
      };

      campoConfig.forEach(actualizarCampo);

      sendResponse({ status: 'Formulario rellenado correctamente' });
    });

    return true;
  }
});
