import os
import base64
from typing import Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI
import json
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

class ElbitProcessor:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def encode_image(self, image_bytes: bytes) -> str:
        """
        Codifica la imagen en base64
        """
        return base64.b64encode(image_bytes).decode('utf-8')
        
    def clean_json_response(self, content: str) -> str:
        """
        Limpia la respuesta JSON de marcadores markdown y espacios extra
        """
        # Eliminar marcadores de código markdown
        if content.startswith('```'):
            lines = content.split('\n')
            # Eliminar primera y última línea si contienen ```
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines[-1].startswith('```'):
                lines = lines[:-1]
            content = '\n'.join(lines)
        
        # Eliminar 'json' si está presente
        content = content.replace('json', '', 1)
        
        # Limpiar espacios extra
        content = content.strip()
        
        logger.info(f"JSON limpio: {content}")
        return content
        
    def process_image(self, image_bytes: bytes) -> Dict:
        """
        Procesa una imagen de un certificado de cumplimiento de Elbit Systems
        """
        base64_image = self.encode_image(image_bytes)
        
        prompt = """
        Extrae la información de este certificado de cumplimiento (Certificate of Compliance) de Elbit Systems.
        El documento contiene información sobre envíos y partes específicas.

        INSTRUCCIONES IMPORTANTES PARA LA EXTRACCIÓN:

        1. NÚMEROS DE SERIE:
           - Cada número de serie debe ser un elemento individual en el array
           - Si hay varios números separados por comas en el documento, sepáralos en elementos individuales
           - NO concatenes números de serie con comas dentro del mismo elemento del array
           - Extrae los números exactamente como aparecen, sin modificar ningún dígito
           - Ejemplo correcto: ["1368", "1370", "1426", "1420"] en lugar de ["1368,1370,1426,1420"]

        2. NÚMEROS DE CATÁLOGO:
           - Extrae el número exactamente como aparece en el campo "Catalog Number"
           - No incluyas información del campo "Product Name" en el número de catálogo

        3. NOMBRES DE PRODUCTOS:
           - Extrae el nombre completo del campo "Product Name"
           - Incluye cualquier sufijo o especificación adicional

        4. CANTIDADES Y ÓRDENES:
           - Las cantidades deben ser números enteros
           - Los números de orden y COC deben ser exactos

        La estructura del JSON debe ser:
        {
            "customer": {
                "name": string (nombre exacto del cliente),
                "shipment_no": string (número de envío exacto)
            },
            "items": [
                {
                    "catalog_number": string (solo el número de catálogo),
                    "product_name": string (nombre completo del producto),
                    "customer_part_no": string o null,
                    "qty": number (cantidad como número entero),
                    "order": string (número de orden exacto),
                    "coc_no": string (número de COC exacto),
                    "serial_numbers": array de strings (cada número de serie como elemento individual)
                }
            ],
            "certification": {
                "quality_authority": string (nombre completo),
                "electronic_signature": string (número exacto),
                "date": string (fecha exacta)
            }
        }

        IMPORTANTE:
        - NO inventes datos que no veas en la imagen
        - Usa null para campos no visibles o inciertos
        - Responde SOLO con el JSON, sin explicaciones ni texto adicional
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en extraer datos de certificados de cumplimiento de Elbit Systems. Tu tarea es extraer la información en formato JSON exactamente como se especifica, prestando especial atención a la precisión de los números de serie y catálogo."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=3000,
                temperature=0
            )
            
            message_content = response.choices[0].message.content.strip()
            logger.info(f"Contenido del mensaje original: {message_content}")
            
            # Limpiar el contenido
            clean_content = self.clean_json_response(message_content)
            
            try:
                result = json.loads(clean_content)
                processed_result = self._process_serial_numbers(result)
                return self._ensure_response_structure(processed_result)
            except json.JSONDecodeError as json_err:
                logger.error(f"Error al parsear JSON: {json_err}")
                logger.error(f"Contenido que causó el error: {clean_content}")
                return self._get_empty_response(f"Error al parsear JSON: {str(json_err)}")
            
        except Exception as e:
            logger.error(f"Error procesando la imagen: {str(e)}", exc_info=True)
            return self._get_empty_response(str(e))

    def _process_serial_numbers(self, result: Dict) -> Dict:
        """
        Procesa los números de serie para asegurar que estén correctamente formateados
        """
        if not result or 'items' not in result:
            return result

        for item in result['items']:
            if 'serial_numbers' in item and item['serial_numbers']:
                # Si es una lista, procesar cada elemento
                if isinstance(item['serial_numbers'], list):
                    processed_numbers = []
                    for number in item['serial_numbers']:
                        if isinstance(number, str):
                            # Dividir por comas y limpiar cada número
                            split_numbers = [n.strip() for n in number.split(',') if n.strip()]
                            processed_numbers.extend(split_numbers)
                    item['serial_numbers'] = processed_numbers
                # Si es un string, convertirlo a lista
                elif isinstance(item['serial_numbers'], str):
                    item['serial_numbers'] = [n.strip() for n in item['serial_numbers'].split(',') if n.strip()]

        return result

    def _ensure_response_structure(self, result: Dict) -> Dict:
        """
        Asegura que el resultado tenga la estructura correcta
        """
        template = {
            "customer": {
                "name": None,
                "shipment_no": None
            },
            "items": [],
            "certification": {
                "quality_authority": None,
                "electronic_signature": None,
                "date": None
            }
        }

        # Si no hay resultado, devolver la plantilla
        if not result:
            return template

        # Asegurar estructura principal
        for key in template:
            if key not in result:
                result[key] = template[key]
            elif result[key] is None and isinstance(template[key], dict):
                result[key] = template[key]

        # Asegurar subcampos de customer
        if isinstance(result["customer"], dict):
            for subkey in template["customer"]:
                if subkey not in result["customer"]:
                    result["customer"][subkey] = None

        # Asegurar subcampos de certification
        if isinstance(result["certification"], dict):
            for subkey in template["certification"]:
                if subkey not in result["certification"]:
                    result["certification"][subkey] = None

        # Asegurar items y sus campos
        if result["items"] is None:
            result["items"] = []
        elif isinstance(result["items"], list):
            for item in result["items"]:
                if isinstance(item, dict):
                    # Campos requeridos para cada item
                    required_fields = [
                        "catalog_number",
                        "product_name",
                        "customer_part_no",
                        "qty",
                        "order",
                        "coc_no",
                        "serial_numbers"
                    ]
                    
                    for field in required_fields:
                        if field not in item:
                            item[field] = None
                    
                    # Asegurar que serial_numbers sea siempre un array
                    if item["serial_numbers"] and not isinstance(item["serial_numbers"], list):
                        item["serial_numbers"] = [str(item["serial_numbers"])]

        return result

    def _get_empty_response(self, error_message: str) -> Dict:
        """
        Devuelve una respuesta vacía con la estructura correcta
        """
        return {
            "customer": {
                "name": None,
                "shipment_no": None
            },
            "items": [],
            "certification": {
                "quality_authority": None,
                "electronic_signature": None,
                "date": None
            },
            "error": error_message
        } 