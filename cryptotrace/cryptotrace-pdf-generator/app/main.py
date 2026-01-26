# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, send_file, make_response
import jinja2
import io
import json # Asegurar que json esté importado para el manejo de datos
import sys
# Import WeasyPrint más adelante cuando se use
# from weasyprint import HTML

# Configurar encoding UTF-8
if sys.version_info[0] >= 3:
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Configurar Jinja2
template_loader = jinja2.FileSystemLoader(searchpath="./app/templates", encoding='utf-8') # Ruta correcta a templates
template_env = jinja2.Environment(loader=template_loader, autoescape=True)

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar que el servicio está activo."""
    return jsonify({'status': 'ok'}), 200

@app.route('/preview', methods=['GET'])
def preview_template():
    """Endpoint para previsualizar la plantilla con datos de muestra en el navegador."""
    try:
        # Usar datos de muestra
        ac21_data = get_sample_data()
        ac21_data["pagina_actual"] = 1
        ac21_data["total_paginas"] = 1
        
        # Renderizar la plantilla
        template = template_env.get_template('ac21_pdf_template.html')
        html_string = template.render(ac21_data)
        
        # Devolver el HTML para visualización directa en navegador
        response = make_response(html_string.encode('utf-8'))
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
        
    except Exception as e:
        print(f"Error en preview: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/generate-ac21-pdf', methods=['POST', 'GET']) # Permitir GET para pruebas fáciles
def generate_pdf_endpoint():
    # Datos de entrada: se podrían tomar del request.json si es POST
    if request.method == 'POST':
        data_ac21_input = request.json
        print(f"Datos recibidos vía POST: {data_ac21_input}")
        
        # Usar los datos recibidos desde Django
        if data_ac21_input:
            ac21_data = data_ac21_input.copy()
            ac21_data["data"] = ac21_data  # Para compatibilidad con la plantilla
        else:
            # Fallback a datos de muestra si no se reciben datos
            ac21_data = get_sample_data()
    else: 
        # Para GET, usamos datos fijos de muestra
        ac21_data = get_sample_data()

    try:
        # Verificar si ya viene con información de paginación del backend
        total_paginas_backend = ac21_data.get("total_paginas", 1)
        lineas_producto = ac21_data.get("lineas_producto", [])
        productos_por_pagina = 18  # Máximo 18 items por hoja
        
        print(f"📄 [PDF Generator] Total páginas del backend: {total_paginas_backend}")
        print(f"📄 [PDF Generator] Total productos: {len(lineas_producto)}")
        
        if total_paginas_backend > 1:
            # El backend ya procesó un documento multipágina, generar páginas automáticamente
            import math
            total_paginas = total_paginas_backend
            html_pages = []
            
            # Verificar si viene información de estructura original
            estructura_original = ac21_data.get("productos_por_pagina_estructura", [])
            accesorios_por_pagina = ac21_data.get("accesorios_por_pagina", [])
            equipos_por_pagina = ac21_data.get("equipos_por_pagina", [])
            
            if estructura_original and len(estructura_original) == total_paginas:
                # Usar la estructura original del documento multipágina
                print(f"📄 [PDF Generator] Usando estructura original: {estructura_original}")
                print(f"📄 [PDF Generator] Total productos recibidos: {len(lineas_producto)}")
                print(f"📄 [PDF Generator] Suma de productos por página: {sum(estructura_original)}")
                print(f"📄 [PDF Generator] Accesorios por página: {[len(a) for a in accesorios_por_pagina]}")
                print(f"📄 [PDF Generator] Equipos por página: {[len(e) for e in equipos_por_pagina]}")
                
                # Validar que la suma de productos por página coincida con el total
                suma_estructura = sum(estructura_original)
                if suma_estructura != len(lineas_producto):
                    print(f"❌ [PDF Generator] ERROR: La suma de productos por página ({suma_estructura}) no coincide con el total recibido ({len(lineas_producto)})")
                    print(f"❌ [PDF Generator] Estructura recibida: {estructura_original}")
                    print(f"❌ [PDF Generator] Esto indica un error en el backend. No se generará el PDF.")
                    raise ValueError(f"Estructura de productos inconsistente: {suma_estructura} productos en estructura vs {len(lineas_producto)} productos recibidos")
                
                inicio = 0
                
                for pagina in range(1, total_paginas + 1):
                    productos_en_esta_pagina = estructura_original[pagina - 1]
                    fin = inicio + productos_en_esta_pagina
                    
                    # Validar que no se exceda el límite de productos
                    if fin > len(lineas_producto):
                        print(f"❌ [PDF Generator] ERROR: Página {pagina} intenta acceder a productos {inicio}-{fin-1} pero solo hay {len(lineas_producto)} productos")
                        raise ValueError(f"Índice fuera de rango: página {pagina} intenta acceder a más productos de los disponibles")
                    
                    # Validar que no haya más de 18 productos por página
                    if productos_en_esta_pagina > 18:
                        print(f"⚠️ [PDF Generator] ADVERTENCIA: Página {pagina} tiene {productos_en_esta_pagina} productos (máximo 18). Se truncará a 18.")
                        productos_en_esta_pagina = 18
                        fin = inicio + 18
                    
                    productos_pagina = lineas_producto[inicio:fin]
                    
                    # Validar que el slice tenga exactamente los productos esperados
                    if len(productos_pagina) != productos_en_esta_pagina:
                        print(f"⚠️ [PDF Generator] ADVERTENCIA: Página {pagina} esperaba {productos_en_esta_pagina} productos pero obtuvo {len(productos_pagina)}")
                        # Ajustar para evitar errores
                        productos_pagina = productos_pagina[:productos_en_esta_pagina]
                    
                    # Crear una copia de los datos para esta página
                    datos_pagina = ac21_data.copy()
                    datos_pagina["lineas_producto"] = productos_pagina
                    datos_pagina["pagina_actual"] = pagina
                    datos_pagina["total_paginas"] = total_paginas
                    
                    # Usar accesorios y equipos específicos de esta página si están disponibles
                    # Si no hay para esta página, usar lista vacía (no los de la página principal)
                    if accesorios_por_pagina and len(accesorios_por_pagina) >= pagina:
                        datos_pagina["accesorios"] = accesorios_por_pagina[pagina - 1] or []
                    else:
                        datos_pagina["accesorios"] = []
                    
                    if equipos_por_pagina and len(equipos_por_pagina) >= pagina:
                        datos_pagina["equipos_prueba"] = equipos_por_pagina[pagina - 1] or []
                    else:
                        datos_pagina["equipos_prueba"] = []
                    
                    datos_pagina["data"] = datos_pagina
                    
                    print(f"📄 [PDF Generator] Generando página {pagina}: {len(productos_pagina)} productos, {len(datos_pagina.get('accesorios', []))} accesorios, {len(datos_pagina.get('equipos_prueba', []))} equipos (estructura original)")
                    
                    # Renderizar esta página
                    template = template_env.get_template('ac21_pdf_template.html')
                    html_pagina = template.render(datos_pagina)
                    html_pages.append(html_pagina)
                    
                    inicio = fin
            else:
                # Fallback: dividir automáticamente en páginas de 18 productos
                # Recalcular total_paginas basado en el número real de productos
                import math
                total_paginas_real = math.ceil(len(lineas_producto) / productos_por_pagina)
                if total_paginas_real != total_paginas:
                    print(f"⚠️ [PDF Generator] Ajustando total_paginas: {total_paginas} → {total_paginas_real} (basado en {len(lineas_producto)} productos)")
                    total_paginas = total_paginas_real
                
                print(f"📄 [PDF Generator] Dividiendo {len(lineas_producto)} productos en {total_paginas} páginas (división automática)")
                
                for pagina in range(1, total_paginas + 1):
                    # Calcular el rango de productos para esta página
                    inicio = (pagina - 1) * productos_por_pagina
                    fin = min(inicio + productos_por_pagina, len(lineas_producto))  # Asegurar que no se exceda
                    productos_pagina = lineas_producto[inicio:fin]
                    
                    print(f"📄 [PDF Generator] Página {pagina}: productos {inicio} a {fin-1} (total: {len(productos_pagina)})")
                    
                    # Crear una copia de los datos para esta página
                    datos_pagina = ac21_data.copy()
                    datos_pagina["lineas_producto"] = productos_pagina
                    datos_pagina["pagina_actual"] = pagina
                    datos_pagina["total_paginas"] = total_paginas
                    # Asegurar que accesorios y equipos estén vacíos si no hay datos específicos
                    if "accesorios" not in datos_pagina or not datos_pagina.get("accesorios"):
                        datos_pagina["accesorios"] = []
                    if "equipos_prueba" not in datos_pagina or not datos_pagina.get("equipos_prueba"):
                        datos_pagina["equipos_prueba"] = []
                    datos_pagina["data"] = datos_pagina
                    
                    # Renderizar esta página
                    template = template_env.get_template('ac21_pdf_template.html')
                    html_pagina = template.render(datos_pagina)
                    html_pages.append(html_pagina)
            
            # Envolver cada página en un contenedor para navegación
            html_pages_wrapped = []
            for i, html_page in enumerate(html_pages, 1):
                wrapped = f'<div class="page-container" data-page="{i}">{html_page}</div>'
                html_pages_wrapped.append(wrapped)
            
            # Agregar navegación JavaScript
            navigation_js = f'''
            <div class="page-navigation">
                <button id="btn-first">« Primera</button>
                <button id="btn-prev">‹ Anterior</button>
                <span id="page-info">Página 1 de {total_paginas}</span>
                <button id="btn-next">Siguiente ›</button>
                <button id="btn-last">Última »</button>
            </div>
            <script>
                (function() {{
                    let currentPage = 1;
                    const totalPages = {total_paginas};
                    
                    function showPage(page) {{
                        if (page < 1 || page > totalPages) return;
                        currentPage = page;
                        
                        // Ocultar todas las páginas
                        var containers = document.querySelectorAll('.page-container');
                        for (var i = 0; i < containers.length; i++) {{
                            containers[i].classList.remove('active');
                        }}
                        
                        // Mostrar página actual
                        var pageContainer = document.querySelector('.page-container[data-page="' + page + '"]');
                        if (pageContainer) {{
                            pageContainer.classList.add('active');
                        }}
                        
                        // Actualizar controles
                        updateNavigation();
                        
                        // Scroll al inicio
                        window.scrollTo(0, 0);
                    }}
                    
                    function showPrevPage() {{
                        if (currentPage > 1) showPage(currentPage - 1);
                    }}
                    
                    function showNextPage() {{
                        if (currentPage < totalPages) showPage(currentPage + 1);
                    }}
                    
                    function updateNavigation() {{
                        var pageInfo = document.getElementById('page-info');
                        var btnPrev = document.getElementById('btn-prev');
                        var btnNext = document.getElementById('btn-next');
                        var btnFirst = document.getElementById('btn-first');
                        var btnLast = document.getElementById('btn-last');
                        
                        if (pageInfo) pageInfo.textContent = 'Página ' + currentPage + ' de ' + totalPages;
                        if (btnPrev) btnPrev.disabled = currentPage === 1;
                        if (btnNext) btnNext.disabled = currentPage === totalPages;
                        if (btnFirst) btnFirst.disabled = currentPage === 1;
                        if (btnLast) btnLast.disabled = currentPage === totalPages;
                    }}
                    
                    function initNavigation() {{
                        var btnFirst = document.getElementById('btn-first');
                        var btnPrev = document.getElementById('btn-prev');
                        var btnNext = document.getElementById('btn-next');
                        var btnLast = document.getElementById('btn-last');
                        
                        if (btnFirst) btnFirst.onclick = function() {{ showPage(1); }};
                        if (btnPrev) btnPrev.onclick = function() {{ showPrevPage(); }};
                        if (btnNext) btnNext.onclick = function() {{ showNextPage(); }};
                        if (btnLast) btnLast.onclick = function() {{ showPage(totalPages); }};
                        
                        // Navegación con teclado
                        document.onkeydown = function(e) {{
                            if (e.key === 'ArrowLeft') showPrevPage();
                            if (e.key === 'ArrowRight') showNextPage();
                        }};
                        
                        // Inicializar mostrando primera página
                        showPage(1);
                    }}
                    
                    // Ejecutar cuando el DOM esté listo
                    if (document.readyState === 'loading') {{
                        document.addEventListener('DOMContentLoaded', initNavigation);
                    }} else {{
                        initNavigation();
                    }}
                }})();
            </script>
            '''
            
            html_string = navigation_js + '\n'.join(html_pages_wrapped)
            
        elif len(lineas_producto) <= productos_por_pagina:
            # Una sola página
            ac21_data["pagina_actual"] = 1
            ac21_data["total_paginas"] = 1
            # Asegurar que accesorios y equipos estén vacíos si no hay datos
            if "accesorios" not in ac21_data or not ac21_data.get("accesorios"):
                ac21_data["accesorios"] = []
            if "equipos_prueba" not in ac21_data or not ac21_data.get("equipos_prueba"):
                ac21_data["equipos_prueba"] = []
            template = template_env.get_template('ac21_pdf_template.html')
            html_string = template.render(ac21_data)
        else:
            # Múltiples páginas por cantidad de productos
            import math
            total_paginas = math.ceil(len(lineas_producto) / productos_por_pagina)
            html_pages = []
            
            for pagina in range(1, total_paginas + 1):
                # Calcular el rango de productos para esta página
                inicio = (pagina - 1) * productos_por_pagina
                fin = inicio + productos_por_pagina
                productos_pagina = lineas_producto[inicio:fin]
                
                # Crear una copia de los datos para esta página
                datos_pagina = ac21_data.copy()
                datos_pagina["lineas_producto"] = productos_pagina
                datos_pagina["pagina_actual"] = pagina
                datos_pagina["total_paginas"] = total_paginas
                # Asegurar que accesorios y equipos estén vacíos si no hay datos específicos
                if "accesorios" not in datos_pagina or not datos_pagina.get("accesorios"):
                    datos_pagina["accesorios"] = []
                if "equipos_prueba" not in datos_pagina or not datos_pagina.get("equipos_prueba"):
                    datos_pagina["equipos_prueba"] = []
                datos_pagina["data"] = datos_pagina
                
                # Renderizar esta página
                template = template_env.get_template('ac21_pdf_template.html')
                html_pagina = template.render(datos_pagina)
                html_pages.append(html_pagina)
            
            # Envolver cada página en un contenedor para navegación
            html_pages_wrapped = []
            for i, html_page in enumerate(html_pages, 1):
                wrapped = f'<div class="page-container" data-page="{i}">{html_page}</div>'
                html_pages_wrapped.append(wrapped)
            
            # Agregar navegación JavaScript
            navigation_js = f'''
            <div class="page-navigation">
                <button id="btn-first">« Primera</button>
                <button id="btn-prev">‹ Anterior</button>
                <span id="page-info">Página 1 de {total_paginas}</span>
                <button id="btn-next">Siguiente ›</button>
                <button id="btn-last">Última »</button>
            </div>
            <script>
                (function() {{
                    let currentPage = 1;
                    const totalPages = {total_paginas};
                    
                    function showPage(page) {{
                        if (page < 1 || page > totalPages) return;
                        currentPage = page;
                        
                        // Ocultar todas las páginas
                        var containers = document.querySelectorAll('.page-container');
                        for (var i = 0; i < containers.length; i++) {{
                            containers[i].classList.remove('active');
                        }}
                        
                        // Mostrar página actual
                        var pageContainer = document.querySelector('.page-container[data-page="' + page + '"]');
                        if (pageContainer) {{
                            pageContainer.classList.add('active');
                        }}
                        
                        // Actualizar controles
                        updateNavigation();
                        
                        // Scroll al inicio
                        window.scrollTo(0, 0);
                    }}
                    
                    function showPrevPage() {{
                        if (currentPage > 1) showPage(currentPage - 1);
                    }}
                    
                    function showNextPage() {{
                        if (currentPage < totalPages) showPage(currentPage + 1);
                    }}
                    
                    function updateNavigation() {{
                        var pageInfo = document.getElementById('page-info');
                        var btnPrev = document.getElementById('btn-prev');
                        var btnNext = document.getElementById('btn-next');
                        var btnFirst = document.getElementById('btn-first');
                        var btnLast = document.getElementById('btn-last');
                        
                        if (pageInfo) pageInfo.textContent = 'Página ' + currentPage + ' de ' + totalPages;
                        if (btnPrev) btnPrev.disabled = currentPage === 1;
                        if (btnNext) btnNext.disabled = currentPage === totalPages;
                        if (btnFirst) btnFirst.disabled = currentPage === 1;
                        if (btnLast) btnLast.disabled = currentPage === totalPages;
                    }}
                    
                    function initNavigation() {{
                        var btnFirst = document.getElementById('btn-first');
                        var btnPrev = document.getElementById('btn-prev');
                        var btnNext = document.getElementById('btn-next');
                        var btnLast = document.getElementById('btn-last');
                        
                        if (btnFirst) btnFirst.onclick = function() {{ showPage(1); }};
                        if (btnPrev) btnPrev.onclick = function() {{ showPrevPage(); }};
                        if (btnNext) btnNext.onclick = function() {{ showNextPage(); }};
                        if (btnLast) btnLast.onclick = function() {{ showPage(totalPages); }};
                        
                        // Navegación con teclado
                        document.onkeydown = function(e) {{
                            if (e.key === 'ArrowLeft') showPrevPage();
                            if (e.key === 'ArrowRight') showNextPage();
                        }};
                        
                        // Inicializar mostrando primera página
                        showPage(1);
                    }}
                    
                    // Ejecutar cuando el DOM esté listo
                    if (document.readyState === 'loading') {{
                        document.addEventListener('DOMContentLoaded', initNavigation);
                    }} else {{
                        initNavigation();
                    }}
                }})();
            </script>
            '''
            
            html_string = navigation_js + '\n'.join(html_pages_wrapped)
        
        # Por ahora, devolvemos el HTML renderizado para previsualización en navegador
        response = make_response(html_string.encode('utf-8'))
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response

    except jinja2.exceptions.TemplateNotFound:
        print("Error: Plantilla no encontrada. Asegúrate que 'ac21_pdf_template.html' está en 'app/templates/'")
        return jsonify({'error': 'Template not found'}), 500
    except Exception as e:
        print(f"Error generando HTML/PDF: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

def get_sample_data():
    """Datos de muestra para el AC21"""
    sample_ac21_data = {
        "numero_albaran": "AC21/007/24",
        "tipo_transaccion": "TRANSFERENCIA", # Puede ser TRANSFERENCIA, INVENTARIO, DESTRUCCION, RECIBO EN MANO, OTRO
        "empresa_origen": {
            "nombre": "EMAD",
            "direccion": "Estado Mayor de la Defensa",
            "localidad_provincia_cp": "C/ Vitruvio, 1",
            "codigo_odmc": "EMAD-004",
            "codigo_emad": "EMAD-004-E08"
        },
        "empresa_destino": {
            "nombre": "SR. CRIPTOCUSTODIO AICOX",
            "direccion": "",
            "localidad_provincia_cp": "",
            "codigo_odmc": "",
            "codigo_emad": ""
        },
        "fecha_informe": "2024-11-22",
        "numero_registro_salida": "NA-S-24-365",
        "fecha_transaccion_dma": "",
        "numero_registro_entrada": "",
        "codigos_contabilidad": "Proyecto Alpha / CC 98765",
        "lineas_producto": [
            {"codigo_producto": "PROD001", "cantidad": 2, "descripcion_producto": "Descripción Detallada del Producto Uno Algo Larga", "numero_serie": "SN001-A"},
            {"codigo_producto": "PROD002", "cantidad": 1, "descripcion_producto": "Descripción del Producto Dos", "numero_serie": "SN002-B"},
            {"codigo_producto": "SERV003", "cantidad": 5, "descripcion_producto": "Servicio de Consultoría Técnica Especializada", "numero_serie": "N/A"},
            {"codigo_producto": "PROD004", "cantidad": 10, "descripcion_producto": "Producto Cuatro con Nombre Extenso para Pruebas de Espacio", "numero_serie": "SN004-C"},
            {"codigo_producto": "ACC005", "cantidad": 3, "descripcion_producto": "Accesorio Cinco", "numero_serie": "SN005-D"},
            {"codigo_producto": "PROD006", "cantidad": 1, "descripcion_producto": "Producto Seis", "numero_serie": "SN006-E"},
            {"codigo_producto": "KIT007", "cantidad": 2, "descripcion_producto": "Kit Siete Completo", "numero_serie": "SN007-F"},
            {"codigo_producto": "PROD008", "cantidad": 1, "descripcion_producto": "Producto Ocho", "numero_serie": "SN008-G"},
            {"codigo_producto": "PROD009", "cantidad": 3, "descripcion_producto": "Producto Nueve", "numero_serie": "SN009-H"},
            {"codigo_producto": "PROD010", "cantidad": 1, "descripcion_producto": "Producto Diez", "numero_serie": "SN010-I"},
            {"codigo_producto": "PROD011", "cantidad": 2, "descripcion_producto": "Producto Once", "numero_serie": "SN011-J"},
            {"codigo_producto": "PROD012", "cantidad": 1, "descripcion_producto": "Producto Doce", "numero_serie": "SN012-K"},
            {"codigo_producto": "PROD013", "cantidad": 1, "descripcion_producto": "Producto Trece", "numero_serie": "SN013-L"},
            {"codigo_producto": "PROD014", "cantidad": 1, "descripcion_producto": "Producto Catorce", "numero_serie": "SN014-M"},
            {"codigo_producto": "PROD015", "cantidad": 1, "descripcion_producto": "Producto Quince", "numero_serie": "SN015-N"},
            {"codigo_producto": "PROD016", "cantidad": 1, "descripcion_producto": "Producto Dieciséis", "numero_serie": "SN016-O"},
            {"codigo_producto": "PROD017", "cantidad": 1, "descripcion_producto": "Producto Diecisiete", "numero_serie": "SN017-P"},
            {"codigo_producto": "PROD018", "cantidad": 1, "descripcion_producto": "Producto Dieciocho", "numero_serie": "SN018-Q"},
            {"codigo_producto": "PROD019", "cantidad": 1, "descripcion_producto": "Producto Diecinueve", "numero_serie": "SN019-R"},
            {"codigo_producto": "PROD020", "cantidad": 1, "descripcion_producto": "Producto Veinte", "numero_serie": "SN020-S"},
        ],
        "flags": { # Para los checkboxes de "Firme y devuelva" y "Para su archivo"
            "firme_y_devuelva": True,
            "para_su_archivo": False
        },
        "material_ha_sido": "RECIBIDO", # RECIBIDO, INVENTARIADO, DESTRUIDO
        "destinatario_autorizado": {
            "testigo": True,
            "otro_especificar": False, # Si es True, se mostraría el texto en el input
            "otro_texto": ""
        },
        "firma_entrega": {
            "firma_texto": "[Firma Entrega Digital]",
            "empleo_rango": "Sgto. Responsable Log.",
            "nombre_apellidos": "Carlos Pérez Rodríguez",
            "cargo": "Jefe de Expediciones"
        },
        "firma_recibe": {
            "firma_texto": "[Firma Recibe Digital]",
            "empleo_rango": "Cte. ODMC Destino",
            "nombre_apellidos": "Laura Gómez Fernández",
            "cargo": "Resp. Seguridad Material"
        },
        "observaciones_odmc_remitente": "Entrega conforme a lo acordado. Material en perfecto estado de conservación y embalaje. Se adjunta documentación adicional.",
        "pagina_actual": 1,
        "total_paginas": 1,
        "data": {} # Para compatibilidad con la plantilla si usa data.X directamente
    }
    sample_ac21_data["data"] = sample_ac21_data # Hacer que data referencie todo el sample_ac21_data
    return sample_ac21_data

if __name__ == '__main__':
    # Nota: Flask en modo debug no es para producción.
    # Usar un servidor WSGI como Gunicorn en producción.
    app.run(host='0.0.0.0', port=5003, debug=True) 