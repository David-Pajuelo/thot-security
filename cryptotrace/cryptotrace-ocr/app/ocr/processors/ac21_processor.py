import os
import base64
from typing import Dict, Optional, Any, List
from dotenv import load_dotenv
from openai import OpenAI
import json
import logging
import httpx
import re
import demjson3
from copy import deepcopy

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Plantilla JSON unificada y por defecto
DEFAULT_JSON_TEMPLATE = {
    "cabecera": {
        "numero_registro_salida": None,
        "fecha_transaccion": None,
        "numero_registro_entrada": None,
        "fecha_informe": None,
        "odmc_numero": None
    },
    "empresa_origen": {
        "nombre": None, "direccion": None, "codigo_postal": None, "ciudad": None, "provincia": None, "pais": None, "codigo_odmc": None, "codigo_emad": None, "nif": None, "telefono": None, "email": None
    },
    "empresa_destino": {
        "nombre": None, "direccion": None, "codigo_postal": None, "ciudad": None, "provincia": None, "pais": None, "codigo_odmc": None, "codigo_emad": None, "nif": None, "telefono": None, "email": None
    },
    "articulos": [],
    "accesorios": [],
    "equipos_prueba": [],
    "firmas": {
        "firma_a": {
            "nombre": None,
            "cargo": None,
            "empleo_rango": None
        },
        "firma_b": {
            "nombre": None,
            "cargo": None,
            "empleo_rango": None
        }
    },
    "observaciones": None
}

class AC21Processor:
    def __init__(self):
        print("🔧 Inicializando AC21Processor...")
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY no está configurada en las variables de entorno")
        print("🔑 API Key encontrada, inicializando cliente OpenAI...")
        try:
            # Crear un cliente HTTP personalizado sin proxies
            http_client = httpx.Client(
                base_url="https://api.openai.com/v1",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=90.0  # Aumentado a 90 segundos
            )
            self.client = OpenAI(api_key=api_key, http_client=http_client)
            print("✅ Cliente OpenAI inicializado correctamente")
        except Exception as e:
            print(f"❌ Error al inicializar cliente OpenAI: {str(e)}")
            raise
        
    def encode_image(self, image_bytes: bytes) -> str:
        """
        Codifica la imagen en base64
        """
        return base64.b64encode(image_bytes).decode('utf-8')
        
    def extract_json_from_text(self, text: str) -> str:
        """
        Extrae el JSON de cualquier texto que lo contenga, incluso si está rodeado de otros caracteres
        """
        # Buscar el primer '{' y el último '}'
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            return text
        
        # Extraer solo el contenido JSON
        json_content = text[start_idx:end_idx + 1]
        return json_content

    def normalize_json_structure(self, content: str) -> str:
        """
        Normaliza la estructura del JSON eliminando problemas comunes
        """
        try:
            # Eliminar caracteres no imprimibles y espacios extra
            content = ''.join(char for char in content if char.isprintable() or char in ['\n', '\r', '\t'])
            
            # Normalizar saltos de línea
            content = content.replace('\r\n', '\n').replace('\r', '\n')
        
            # Eliminar espacios y tabs extra
            lines = [line.strip() for line in content.split('\n')]
            content = '\n'.join(line for line in lines if line)
            
            # Normalizar comillas
            content = content.replace("'", '"')
            content = content.replace('"', '"').replace('"', '"')
            
            # Normalizar valores nulos usando patrones más seguros
            patterns = [
                (r':\s*(?:null|undefined|NaN|"")\s*([,}])', r': null\1'),
                (r':\s*,', r': null,'),
                (r':\s*}', r': null}')
            ]
            
            for pattern, replacement in patterns:
                try:
                    content = re.sub(pattern, replacement, content)
                except re.error as e:
                    logger.error(f"Error en patrón regex '{pattern}': {str(e)}")
                    continue
            
            return content
            
        except Exception as e:
            logger.error(f"Error al normalizar estructura JSON: {str(e)}")
        return content
        
    def fix_json_structure(self, content: str) -> str:
        """
        Corrige problemas estructurales en el JSON
        """
        try:
            # Eliminar comas extra antes de cerrar objetos o arrays
            try:
                content = re.sub(r',(\s*[}\]])', r'\1', content)
            except re.error as e:
                logger.error(f"Error en regex de comas extra: {str(e)}")

            # Añadir comas entre elementos adyacentes
            try:
                content = re.sub(r'([}\]"])\s+([{["])', r'\1,\2', content)
            except re.error as e:
                logger.error(f"Error en regex de comas faltantes: {str(e)}")

            # Cerrar strings sin terminar
            open_quotes = False
            chars = list(content)
            for i in range(len(chars)):
                if chars[i] == '"' and (i == 0 or chars[i-1] != '\\'):
                    open_quotes = not open_quotes
                if i == len(chars) - 1 and open_quotes:
                    chars.append('"')
            content = ''.join(chars)

            # Balancear llaves y corchetes
            stack = []
            balanced_content = []
            
            for char in content:
                if char in '{[':
                    stack.append(char)
                    balanced_content.append(char)
                elif char in '}]':
                    if not stack:
                        # Si encontramos un cierre sin apertura, añadimos la apertura correspondiente al inicio
                        if char == '}':
                            balanced_content.insert(0, '{')
                            stack.append('{')
                        else:
                            balanced_content.insert(0, '[')
                            stack.append('[')
                    
                    if stack:
                        last_open = stack[-1]
                        if (char == '}' and last_open == '{') or (char == ']' and last_open == '['):
                            stack.pop()
                    balanced_content.append(char)
                else:
                    balanced_content.append(char)

            # Cerrar estructuras que quedaron abiertas
            while stack:
                char = stack.pop()
                balanced_content.append('}' if char == '{' else ']')

            return ''.join(balanced_content)

        except Exception as e:
            logger.error(f"Error al corregir estructura JSON: {str(e)}")
        return content
        
    def validate_and_fix_json(self, content: str) -> Dict:
        """
        Valida y corrige el JSON, asegurando que cumpla con la estructura esperada
        """
        try:
            # Primer intento: parsear directamente
            return json.loads(content)
        except json.JSONDecodeError:
            logger.info("Primer intento de parseo fallido, iniciando proceso de reparación")
            
            # Extraer JSON del texto
            content = self.extract_json_from_text(content)
            
            # Normalizar estructura
            content = self.normalize_json_structure(content)
            
            # Corregir estructura
            content = self.fix_json_structure(content)
            
            try:
                # Segundo intento: parsear JSON corregido
                return json.loads(content)
            except json.JSONDecodeError:
                logger.info("Segundo intento fallido, usando parser tolerante")
                try:
                    # Tercer intento: usar parser tolerante
                    return demjson3.decode(content)
                except Exception as e:
                    logger.error(f"Todos los intentos de parseo fallaron: {str(e)}")
                    # Devolver plantilla por defecto
                    return deepcopy(DEFAULT_JSON_TEMPLATE)

    def merge_with_template(self, data: Dict) -> Dict:
        """
        Combina los datos recibidos con la plantilla por defecto usando un deep merge
        que añade claves nuevas del origen al destino.
        """
        template = deepcopy(DEFAULT_JSON_TEMPLATE)
        
        def merge_dict(source: Dict, target: Dict) -> None:
            for key, value in source.items():
                # Si la clave existe en el destino y ambos valores son diccionarios, fusionar recursivamente.
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    merge_dict(value, target[key])
                # De lo contrario, si el valor no es nulo, actualizar/añadir en el destino.
                # Esto sobrescribirá listas y valores simples, y añadirá claves que no estaban en la plantilla.
                elif value is not None:
                    target[key] = value

        try:
            if isinstance(data, dict):
                merge_dict(data, template)
        except Exception as e:
            logger.error(f"Error al combinar datos con plantilla: {str(e)}")
        
        return template

    def sanitize_article_data(self, articles: List[Dict]) -> List[Dict]:
        """
        Sanitiza y valida los datos de los artículos principales.
        """
        sanitized = []
        if not isinstance(articles, list):
            return sanitized
            
        for article in articles:
            if not isinstance(article, dict):
                continue
            
            sanitized_article = {
                "descripcion": str(article.get("descripcion") or "").strip(),
                "numero_serie_inicio": str(article.get("numero_serie_inicio") or "").strip(),
                "numero_serie_fin": str(article.get("numero_serie_fin") or "").strip(),
                "observaciones": str(article.get("observaciones") or "").strip(),
            }
            try:
                sanitized_article["cantidad"] = int(article.get("cantidad") or 1)
            except (ValueError, TypeError):
                sanitized_article["cantidad"] = 1
            
            try:
                sanitized_article["cc"] = int(article.get("cc") or 0)
            except (ValueError, TypeError):
                sanitized_article["cc"] = 0
            
            sanitized.append(sanitized_article)
                
        return sanitized

    def sanitize_accesorios(self, accesorios: List[Dict]) -> List[Dict]:
        """
        Sanitiza y valida los datos de los accesorios.
        """
        sanitized = []
        if not isinstance(accesorios, list):
            return sanitized

        for item in accesorios:
            if not isinstance(item, dict):
                continue

            sanitized_item = {
                "descripcion": str(item.get("descripcion") or "").strip(),
            }
            try:
                sanitized_item["cantidad"] = int(item.get("cantidad") or 1)
            except (ValueError, TypeError):
                sanitized_item["cantidad"] = 1
            
            sanitized.append(sanitized_item)

        return sanitized

    def sanitize_equipos_prueba(self, equipos: List[Dict]) -> List[Dict]:
        """
        Sanitiza y valida los datos de los equipos de prueba.
        """
        sanitized = []
        if not isinstance(equipos, list):
            return sanitized

        for item in equipos:
            if not isinstance(item, dict):
                continue

            sanitized_item = {
                "codigo": str(item.get("codigo") or "").strip()
            }
            if sanitized_item["codigo"]:
                sanitized.append(sanitized_item)
        
        return sanitized
        
    def process_image(self, image_bytes: bytes) -> Dict:
        """
        Procesa una imagen usando GPT-4 Vision, llamando a los métodos
        de creación de prompt y post-procesamiento.
        """
        logger.info("🖼️ Iniciando procesamiento de imagen...")
        try:
            # 1. Codificar imagen
            base64_image = self.encode_image(image_bytes)
            logger.info("✅ Imagen codificada en base64")
        
            # 2. Crear el prompt dinámicamente llamando al método correcto
            logger.info("🔄 Preparando llamada a OpenAI usando _create_openai_prompt...")
            messages = self._create_openai_prompt(base64_image)
            
            # 3. Llamar a OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=2048,
                temperature=0,
                response_format={"type": "json_object"}
            )
            logger.info("✅ Respuesta recibida de OpenAI")
            
            # 4. Procesar respuesta JSON
            content = response.choices[0].message.content
            logger.info("================== RAW OPENAI RESPONSE ==================")
            logger.info(content)
            logger.info("=========================================================")
            
            raw_data = json.loads(content)
            logger.info("================== PARSED JSON DATA =====================")
            logger.info(json.dumps(raw_data, indent=2))
            logger.info("=========================================================")

            # 5. Post-procesar los datos para corregir errores y mapear
            processed_data = self._post_process_data(raw_data)
            
            # 6. Combinar con plantilla para asegurar estructura final
            result = self.merge_with_template(processed_data)
            
            # 7. Sanitizar listas
            if "articulos" in result:
                result["articulos"] = self.sanitize_article_data(result.get("articulos"))
            if "accesorios" in result:
                result["accesorios"] = self.sanitize_accesorios(result.get("accesorios"))
            if "equipos_prueba" in result:
                result["equipos_prueba"] = self.sanitize_equipos_prueba(result.get("equipos_prueba"))

            logger.info("================== FINAL PROCESSED DATA =================")
            logger.info(json.dumps(result, indent=2))
            logger.info("=========================================================")
            
            return result
            
        except Exception as e:
            logger.error(f"Error en el procesamiento: {str(e)}", exc_info=True)
            return deepcopy(DEFAULT_JSON_TEMPLATE)

    def _create_openai_prompt(self, image_base64: str) -> list:
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
                        Analiza la imagen de este documento AC-21 y extrae la información estructurada en formato JSON. Presta especial atención a los siguientes puntos:
                        
                        1.  **Cabecera**: Extrae los campos de la parte superior: `numero_registro_salida`, `fecha_informe`, `numero_registro_entrada`, `fecha_transaccion`, y `odmc_numero`.
                        2.  **Empresas (DE/PARA)**: Identifica claramente la empresa de origen (DE) y la de destino (PARA). Extrae nombre, dirección completa y códigos.
                        3.  **Tabla de Artículos**:
                            - Extrae CADA fila de la tabla en una lista de objetos `articulos`.
                            - Para CADA artículo, DEBES extraer: `descripcion` (el título corto o edición), `cantidad`, `numero_serie_inicio`, `numero_serie_fin`, `cc` y `observaciones`.
                            - Es CRÍTICO que no omitas ningún artículo.
                        4.  **Accesorios y Equipos de Prueba**: Extrae las listas de "ACCESORIOS ENTREGADOS" y "EQUIPOS PRUEBAS". A veces el título puede variar ligeramente (p.ej. "EQUIPOS DE PRUEBA AICOX"); debes poder manejar estas variaciones.
                        5.  **Firmas (CRÍTICO)**:
                            - El documento tiene dos bloques de firma: uno a la **izquierda (recuadro 15)** y otro a la **derecha (recuadro 16)**.
                            - **Usa la posición visual como criterio principal.**
                            - Los datos del bloque de la **izquierda** corresponden al objeto `destinatario`.
                            - Los datos del bloque de la **derecha** corresponden al objeto `testigo`.
                            - Es crucial que no mezcles la información. Si solo hay una firma en el bloque derecho, `destinatario` debe ser `null` o un objeto con campos vacíos.
                            - Para cada bloque, busca explícitamente las etiquetas "Nombre y Apellidos", "Empleo" y "Cargo" y extrae sus valores para los campos `nombre`, `empleo_rango` y `cargo` respectivamente. A menudo el nombre está precedido por "D./Dª.".
                        6.  **Observaciones Generales**: Extrae el campo "17. OBSERVACIONES DEL ODMC REMITENTE".
                        7.  **Casillas de verificación**: Detecta el estado de las casillas en la parte superior (TRANSFERENCIA, INVENTARIO, etc.) y en la sección de recepción (RECIBIDO, INVENTARIADO, etc.).

                        El JSON final debe tener esta estructura exacta. No incluyas texto o caracteres fuera del objeto JSON.
                        {
                          "cabecera": {
                            "tipo_transaccion": "String",
                            "numero_registro_salida": "String",
                            "fecha_informe": "String (YYYY-MM-DD)",
                            "numero_registro_entrada": "String",
                            "fecha_transaccion": "String (YYYY-MM-DD)",
                            "odmc_numero": "String"
                          },
                          "empresa_origen": { "nombre": "String", "direccion": "String", "codigo_odmc": "String", "codigo_emad": "String" },
                          "empresa_destino": { "nombre": "String", "direccion": "String", "codigo_odmc": "String" },
                          "articulos": [
                            { "descripcion": "String", "cantidad": "Int", "numero_serie_inicio": "String", "numero_serie_fin": "String", "cc": "String", "observaciones": "String" }
                          ],
                          "accesorios": [
                            { "descripcion": "String", "cantidad": "Int" }
                          ],
                          "equipos_prueba": [
                            { "codigo": "String" }
                          ],
                          "estado_material": {
                             "recibido": "Boolean",
                             "inventariado": "Boolean",
                             "destruido": "Boolean"
                          },
                          "firmas": {
                            "destinatario": { "nombre": "String", "cargo": "String", "empleo_rango": "String" },
                            "testigo": { "nombre": "String", "cargo": "String", "empleo_rango": "String" }
                          },
                          "observaciones_generales": "String"
                        }
                        """
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]

    def _post_process_data(self, data: dict) -> dict:
        """
        Realiza un post-procesamiento para normalizar y limpiar los datos,
        incluyendo una corrección robusta para la asignación de firmas.
        """
        
        firmas = data.get('firmas', {})
        destinatario_data = firmas.get('destinatario')
        testigo_data = firmas.get('testigo')

        # HEURÍSTICA DE CORRECCIÓN DE FIRMAS
        # Si hay firma en `destinatario` pero no en `testigo`, y el nombre no coincide
        # con la empresa destino, lo movemos a `testigo`.
        if (destinatario_data and 
            isinstance(destinatario_data, dict) and 
            destinatario_data.get('nombre') and
            (not testigo_data or not any(testigo_data.values()))):
            
            destinatario_nombre = destinatario_data.get('nombre', '')
            empresa_destino_nombre = data.get('empresa_destino', {}).get('nombre')

            if empresa_destino_nombre and destinatario_nombre.lower() not in empresa_destino_nombre.lower():
                logger.warning(
                    "CORRECCIÓN DE FIRMA: El nombre del firmante 'destinatario' "
                    f"('{destinatario_nombre}') no coincide con la empresa destino ('{empresa_destino_nombre}'). "
                    "Se asume que es el 'testigo' y se mueve al bloque derecho."
                )
                data['firmas']['testigo'] = destinatario_data
                data['firmas']['destinatario'] = {"nombre": None, "cargo": None, "empleo_rango": None}
        
        # Mapeo final para compatibilidad con el frontend
        final_firmas = data.get('firmas', {})
        data['firmas'] = {
            'firma_a': final_firmas.get('destinatario'),
            'firma_b': final_firmas.get('testigo')
        }

        logger.info(f"Datos post-procesados (firmas): {data.get('firmas')}")
        return data

    def _get_openai_client(self):
        return OpenAI(api_key=self.api_key)