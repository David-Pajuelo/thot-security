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

class TelefonicaDeliveryProcessor:
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
        Procesa una imagen de un albarán de Telefónica usando GPT-4 Vision
        """
        base64_image = self.encode_image(image_bytes)
        
        prompt = """
        Analiza esta imagen y determina primero si es un albarán de Telefónica en formato tabla o en formato clásico.

        Si es formato TABLA:
        - Extrae TODOS los números de serie de cada fila, separados por comas
        - Las mediciones deben ser exactamente como aparecen en la tabla (OK, N/A, etc.)
        - Cada fila de la tabla debe ser un artículo diferente
        - Los códigos de producto deben extraerse exactamente como aparecen
        - Las cantidades deben ser números
        - Incluye el número de posición (Pos.) de cada fila si existe

        Si es formato CLÁSICO:
        - Extrae la información de campos como emisor, destino, etc.
        - Los números de serie deben ser arrays
        - Las cantidades deben ser números

        La estructura del JSON debe ser:
        {
            "tipo_formato": "TABLA" o "CLASICO",
            "emisor": {
                "nombre": string,
                "direccion": string,
                "telefono": string,
                "fax": string,
                "cif": string
            },
            "albaran": {
                "numero": string,
                "nuestra_ref": string,
                "pedido": string,
                "terminos_envio": string,
                "poc": string,
                "cod_progr": string,
                "fecha": string
            },
            "destino": {
                "nombre": string,
                "direccion": string,
                "atencion": string
            },
            "articulos": [
                {
                    "pos": number o null,
                    "codigo": string,
                    "descripcion": string,
                    "numeros_serie": array de strings (IMPORTANTE: extraer TODOS los números de serie),
                    "cantidad": number,
                    "mediciones": {
                        "visual": string exacto de la tabla (OK, N/A, etc),
                        "funcional": string exacto de la tabla,
                        "dimensional": string exacto de la tabla,
                        "documentacion": string exacto de la tabla,
                        "embalaje": string exacto de la tabla
                    }
                }
            ],
            "observaciones": string
        }

        IMPORTANTE:
        - NO inventes datos que no veas en la imagen
        - Usa null para campos no visibles o inciertos
        - En formato tabla, es CRÍTICO extraer TODOS los números de serie y mediciones exactamente como aparecen
        - En formato tabla, cada fila debe ser un artículo independiente
        - Responde SOLO con el JSON, sin explicaciones ni texto adicional
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en extraer datos de albaranes de Telefónica en diferentes formatos. Tu tarea es extraer la información en formato JSON exactamente como se especifica, sin añadir explicaciones ni texto adicional."
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
            if message_content.startswith('```') and message_content.endswith('```'):
                message_content = message_content[3:-3].strip()
            
            if message_content.startswith('json'):
                message_content = message_content[4:].strip()
            
            # Eliminar cualquier texto antes o después del JSON
            start_idx = message_content.find('{')
            end_idx = message_content.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                message_content = message_content[start_idx:end_idx]
            
            try:
                result = json.loads(message_content)
                return self._ensure_response_structure(result)
            except json.JSONDecodeError as json_err:
                logger.error(f"Error al parsear JSON: {json_err}")
                logger.error(f"Contenido que causó el error: {message_content}")
                # Intento de recuperación: eliminar caracteres problemáticos
                clean_content = ''.join(char for char in message_content if char.isprintable())
                try:
                    result = json.loads(clean_content)
                    return self._ensure_response_structure(result)
                except:
                    return self._get_empty_response(f"Error al parsear JSON: {str(json_err)}")
            
        except Exception as e:
            logger.error(f"Error procesando la imagen: {str(e)}", exc_info=True)
            return self._get_empty_response(str(e))

    def _ensure_response_structure(self, result: Dict) -> Dict:
        """
        Asegura que el resultado tenga la estructura correcta
        """
        template = {
            "tipo_formato": None,
            "emisor": {
                "nombre": None,
                "direccion": None,
                "telefono": None,
                "fax": None,
                "cif": None
            },
            "albaran": {
                "numero": None,
                "nuestra_ref": None,
                "pedido": None,
                "terminos_envio": None,
                "poc": None,
                "cod_progr": None,
                "fecha": None
            },
            "destino": {
                "nombre": None,
                "direccion": None,
                "atencion": None
            },
            "articulos": [],
            "observaciones": None
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

        # Asegurar subcampos
        for key in ["emisor", "albaran", "destino"]:
            if isinstance(result[key], dict):
                for subkey in template[key]:
                    if subkey not in result[key]:
                        result[key][subkey] = None

        # Asegurar artículos y sus mediciones
        if result["articulos"] is None:
            result["articulos"] = []
        elif isinstance(result["articulos"], list):
            for articulo in result["articulos"]:
                if isinstance(articulo, dict):
                    # Campos básicos
                    for field in ["pos", "codigo", "descripcion", "numeros_serie", "cantidad"]:
                        if field not in articulo:
                            articulo[field] = None
                    
                    # Asegurar que numeros_serie sea siempre un array
                    if articulo["numeros_serie"] and not isinstance(articulo["numeros_serie"], list):
                        articulo["numeros_serie"] = [str(articulo["numeros_serie"])]
                    
                    # Campos de mediciones
                    if "mediciones" not in articulo:
                        articulo["mediciones"] = {}
                    
                    mediciones_template = {
                        "visual": None,
                        "funcional": None,
                        "dimensional": None,
                        "documentacion": None,
                        "embalaje": None
                    }
                    
                    for field in mediciones_template:
                        if field not in articulo["mediciones"]:
                            articulo["mediciones"][field] = None

        return result

    def _get_empty_response(self, error_message: str) -> Dict:
        """
        Devuelve una respuesta vacía con la estructura correcta
        """
        return {
            "emisor": {
                "nombre": None,
                "direccion": None,
                "telefono": None,
                "fax": None,
                "cif": None
            },
            "albaran": {
                "numero": None,
                "nuestra_ref": None,
                "pedido": None,
                "terminos_envio": None,
                "poc": None,
                "cod_progr": None,
                "fecha": None
            },
            "destino": {
                "nombre": None,
                "direccion": None,
                "atencion": None
            },
            "articulos": [],
            "observaciones": None,
            "error": error_message
        } 