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
        productos_por_pagina = 21
        
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
                print(f"📄 [PDF Generator] Accesorios por página: {[len(a) for a in accesorios_por_pagina]}")
                print(f"📄 [PDF Generator] Equipos por página: {[len(e) for e in equipos_por_pagina]}")
                inicio = 0
                
                for pagina in range(1, total_paginas + 1):
                    productos_en_esta_pagina = estructura_original[pagina - 1]
                    fin = inicio + productos_en_esta_pagina
                    productos_pagina = lineas_producto[inicio:fin]
                    
                    # Crear una copia de los datos para esta página
                    datos_pagina = ac21_data.copy()
                    datos_pagina["lineas_producto"] = productos_pagina
                    datos_pagina["pagina_actual"] = pagina
                    datos_pagina["total_paginas"] = total_paginas
                    
                    # Usar accesorios y equipos específicos de esta página si están disponibles
                    if accesorios_por_pagina and len(accesorios_por_pagina) >= pagina:
                        datos_pagina["accesorios"] = accesorios_por_pagina[pagina - 1]
                    if equipos_por_pagina and len(equipos_por_pagina) >= pagina:
                        datos_pagina["equipos_prueba"] = equipos_por_pagina[pagina - 1]
                    
                    datos_pagina["data"] = datos_pagina
                    
                    print(f"📄 [PDF Generator] Generando página {pagina}: {len(productos_pagina)} productos, {len(datos_pagina.get('accesorios', []))} accesorios, {len(datos_pagina.get('equipos_prueba', []))} equipos (estructura original)")
                    
                    # Renderizar esta página
                    template = template_env.get_template('ac21_pdf_template.html')
                    html_pagina = template.render(datos_pagina)
                    html_pages.append(html_pagina)
                    
                    inicio = fin
            else:
                # Fallback: dividir automáticamente en páginas de 21 productos
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
                    datos_pagina["data"] = datos_pagina
                    
                    print(f"📄 [PDF Generator] Generando página {pagina}: {len(productos_pagina)} productos (división automática)")
                    
                    # Renderizar esta página
                    template = template_env.get_template('ac21_pdf_template.html')
                    html_pagina = template.render(datos_pagina)
                    html_pages.append(html_pagina)
            
            # Combinar todas las páginas con salto de página
            html_string = '\n<div class="page-break"></div>\n'.join(html_pages)
            
        elif len(lineas_producto) <= productos_por_pagina:
            # Una sola página
            ac21_data["pagina_actual"] = 1
            ac21_data["total_paginas"] = 1
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
                datos_pagina["data"] = datos_pagina
                
                # Renderizar esta página
                template = template_env.get_template('ac21_pdf_template.html')
                html_pagina = template.render(datos_pagina)
                html_pages.append(html_pagina)
            
            # Combinar todas las páginas con salto de página
            html_string = '\n<div class="page-break"></div>\n'.join(html_pages)
        
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