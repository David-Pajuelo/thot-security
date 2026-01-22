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
import traceback
from copy import deepcopy
from io import BytesIO

try:
    from PIL import Image  # type: ignore
except ImportError:
    Image = None

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
        "tipo_transaccion": "transferencia"  # Valores posibles: "transferencia", "inventario", "destruccion", "recibo_en_mano", "otro"
    },
    "empresa_origen": {
        "nombre": None, "direccion": None, "codigo_postal": None, "ciudad": None, "provincia": None, "numero_odmc": None
    },
    "empresa_destino": {
        "nombre": None, "direccion": None, "codigo_postal": None, "ciudad": None, "provincia": None, "numero_odmc": None
    },
    "articulos": [],  # Cada artículo tiene: codigo_producto (TÍTULO CORTO/EDICIÓN), observaciones (OBSERVACIONES/REMARKS), cantidad, numero_serie_inicio, numero_serie_fin, cc
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

    def _crop_image_for_items(self, image_bytes: bytes, crop_params: Optional[Dict[str, float]] = None) -> bytes:
        """
        Genera una versión recortada de la imagen centrada en la zona de la tabla de inventario.

        - Si se proporcionan crop_params (top/bottom/left/right en [0,1]), se usan esos valores.
        - Si NO se proporcionan crop_params (None), NO se aplica recorte y se devuelve la imagen original.
        - Si PIL no está disponible o hay error, se devuelve la imagen original.
        """
        # Si no hay parámetros explícitos de recorte, no recortar (recorte opcional)
        if crop_params is None:
            print("ℹ️ [CROP ITEMS] Sin parámetros de recorte: usando imagen completa para ITEMS")
            return image_bytes

        if Image is None:
            print("⚠️ PIL no está disponible, usando imagen completa para ITEMS")
            return image_bytes

        try:
            original = Image.open(BytesIO(image_bytes)).convert("RGB")
            w, h = original.size

            # Valores por defecto en caso de que falte algún porcentaje concreto
            default_top = 0.25
            default_bottom = 0.98
            default_left = 0.03
            default_right = 0.97

            top_pct = float(crop_params.get("top", default_top))
            bottom_pct = float(crop_params.get("bottom", default_bottom))
            left_pct = float(crop_params.get("left", default_left))
            right_pct = float(crop_params.get("right", default_right))

            # Asegurar rangos válidos
            top_pct = max(0.0, min(0.95, top_pct))
            bottom_pct = max(top_pct + 0.01, min(1.0, bottom_pct))
            left_pct = max(0.0, min(0.95, left_pct))
            right_pct = max(left_pct + 0.01, min(1.0, right_pct))

            top = int(h * top_pct)
            bottom = int(h * bottom_pct)
            left = int(w * left_pct)
            right = int(w * right_pct)

            print(f"📐 [CROP ITEMS] Tamaño original imagen: {w}x{h}")
            print(f"✂️ [CROP ITEMS] Recorte: top={top_pct:.2f}, bottom={bottom_pct:.2f}, left={left_pct:.2f}, right={right_pct:.2f}")

            cropped = original.crop((left, top, right, bottom))
            cw, ch = cropped.size
            print(f"✂️  [CROP ITEMS] Tamaño recortado: {cw}x{ch} (box=({left},{top})-({right},{bottom}))")

            output = BytesIO()
            cropped.save(output, format="PNG")
            return output.getvalue()
        except Exception as e:
            print(f"❌ [CROP ITEMS] Error al recortar imagen para ITEMS: {str(e)}")
            print(f"📚 Stack trace: {traceback.format_exc()}")
            return image_bytes
        
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
            
            # Extraer código de producto: viene de "TÍTULO CORTO / EDICIÓN" del AC21
            # Solo usar codigo_producto (eliminado codigo, titulo_corto, descripcion legacy)
            codigo_producto = (
                article.get("codigo_producto") or 
                article.get("titulo_corto") or  # Mantener por compatibilidad temporal
                ""
            )
            
            # Extraer observaciones: viene de "OBSERVACIONES/REMARKS" del AC21
            # Este campo se mapeará a descripcion en la BD
            observaciones = (
                article.get("observaciones") or 
                article.get("descripcion") or  # Mantener por compatibilidad temporal
                ""
            )
            
            sanitized_article = {
                "codigo_producto": str(codigo_producto).strip(),
                "observaciones": str(observaciones).strip(),  # Se mapeará a descripcion en la BD
                "numero_serie_inicio": str(article.get("numero_serie_inicio") or "").strip(),
                "numero_serie_fin": str(article.get("numero_serie_fin") or "").strip(),
            }

            # Índice de fila (opcional): número de línea tal y como aparece en la tabla del AC21
            try:
                idx_raw = article.get("indice_fila") or article.get("indice") or article.get("fila")
                if idx_raw is not None and str(idx_raw).strip() != "":
                    sanitized_article["indice_fila"] = int(str(idx_raw))
            except (ValueError, TypeError):
                # Si no se puede convertir, simplemente no añadimos el campo
                pass
            
            # Extraer cantidad: debe ser un número entero válido
            try:
                cantidad_raw = article.get("cantidad")
                if cantidad_raw is None or cantidad_raw == "":
                    sanitized_article["cantidad"] = 1
                else:
                    # Intentar convertir a entero (permite "1.0" -> 1)
                    cantidad_int = int(float(str(cantidad_raw)))
                    sanitized_article["cantidad"] = max(1, cantidad_int)  # Mínimo 1
            except (ValueError, TypeError):
                sanitized_article["cantidad"] = 1
            
            # CC puede ser cualquier valor o estar vacío
            cc_value = article.get("cc")
            if cc_value is None:
                sanitized_article["cc"] = ""
            else:
                # Mantener como string para permitir cualquier valor
                sanitized_article["cc"] = str(cc_value).strip()
            
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
        
    def _safe_parse_json(self, content: str) -> Dict:
        """
        Intenta parsear el JSON devuelto por OpenAI de forma robusta.
        1) Primero hace json.loads directo.
        2) Si falla, intenta:
           - Recortar todo lo que haya antes del primer '{'
           - Recortar todo lo que haya después del último '}'
        3) Si aún así falla, relanza el error.
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ Error al parsear JSON (primer intento): {str(e)}")
            # Mostrar un resumen de la zona problemática
            print(f"Fragmento alrededor del error: {content[max(0, e.pos-120):e.pos+120]}...")

            # Intentar limpiar: quedarnos solo con el bloque entre el primer '{' y el último '}'
            start = content.find("{")
            end = content.rfind("}")

            if start != -1 and end != -1 and end > start:
                cleaned = content[start:end+1]
                print("🔧 Intentando parsear JSON limpiado (recortado entre primer '{' y último '}')...")
                try:
                    parsed = json.loads(cleaned)
                    print("✅ JSON limpiado parseado correctamente")
                    return parsed
                except json.JSONDecodeError as e2:
                    print(f"❌ Falló también el parseo del JSON limpiado: {str(e2)}")
                    print(f"Contenido limpiado (inicio): {cleaned[:500]}...")
                    raise
            else:
                print("⚠️ No se pudo encontrar un bloque JSON bien delimitado entre '{' y '}'")
                raise

    def process_image(self, image_bytes: bytes, crop_params: Optional[Dict[str, float]] = None) -> Dict:
        """
        Procesa una imagen usando GPT-4 Vision en DOS PASADAS:
        1) Cabecera, empresas, estado del material, firmas, observaciones.
        2) Tabla de artículos, accesorios y equipos de prueba.
        Después fusiona los resultados y aplica el post-procesado habitual.
        """
        print("🖼️ Iniciando procesamiento de imagen (modo 2-pasadas)...")
        try:
            # 1. Codificar imagen completa (para cabecera/empresas/firmas)
            base64_image_full = self.encode_image(image_bytes)
            print("✅ Imagen completa codificada en base64")

            # 1b. Generar imagen recortada para la tabla (ITEMS) y codificarla
            cropped_bytes = self._crop_image_for_items(image_bytes, crop_params=crop_params)
            base64_image_items = self.encode_image(cropped_bytes)
            print("✅ Imagen recortada para ITEMS codificada en base64")

            # 2. Primera llamada: cabecera + empresas + estado + firmas + observaciones
            print("🔄 [PASO 1] Preparando llamada a OpenAI para CABECERA/EMPRESAS/FIRMAS...")
            header_messages = self._create_openai_prompt_header(base64_image_full)

            print("📞 [PASO 1] Llamando a OpenAI API (cabecera/empresas/firmas)...")
            header_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=header_messages,
                max_tokens=1600,
                temperature=0,
                response_format={"type": "json_object"}
            )
            print("✅ [PASO 1] Respuesta recibida de OpenAI")

            header_content = header_response.choices[0].message.content
            print("================== RAW OPENAI RESPONSE (HEADER) ==================")
            print(header_content)
            print("==================================================================")

            header_data = self._safe_parse_json(header_content)
            print("================== PARSED JSON DATA (HEADER) =====================")
            print(json.dumps(header_data, indent=2))
            print("==================================================================")
            
            # Log específico para empresas (codigo_postal, ciudad, provincia)
            if 'empresa_origen' in header_data:
                emp_origen = header_data['empresa_origen']
                print("🔍 [DEBUG EMPRESA ORIGEN]")
                print(f"   nombre: {emp_origen.get('nombre', 'N/A')}")
                print(f"   direccion: {emp_origen.get('direccion', 'N/A')}")
                print(f"   codigo_postal: {emp_origen.get('codigo_postal', 'N/A')} (tipo: {type(emp_origen.get('codigo_postal')).__name__})")
                print(f"   ciudad: {emp_origen.get('ciudad', 'N/A')} (tipo: {type(emp_origen.get('ciudad')).__name__})")
                print(f"   provincia: {emp_origen.get('provincia', 'N/A')} (tipo: {type(emp_origen.get('provincia')).__name__})")
                print(f"   numero_odmc: {emp_origen.get('numero_odmc', 'N/A')}")
            
            if 'empresa_destino' in header_data:
                emp_destino = header_data['empresa_destino']
                print("🔍 [DEBUG EMPRESA DESTINO]")
                print(f"   nombre: {emp_destino.get('nombre', 'N/A')}")
                print(f"   direccion: {emp_destino.get('direccion', 'N/A')}")
                print(f"   codigo_postal: {emp_destino.get('codigo_postal', 'N/A')} (tipo: {type(emp_destino.get('codigo_postal')).__name__})")
                print(f"   ciudad: {emp_destino.get('ciudad', 'N/A')} (tipo: {type(emp_destino.get('ciudad')).__name__})")
                print(f"   provincia: {emp_destino.get('provincia', 'N/A')} (tipo: {type(emp_destino.get('provincia')).__name__})")
                print(f"   numero_odmc: {emp_destino.get('numero_odmc', 'N/A')}")

            # 3. Segunda llamada: SOLO artículos / accesorios / equipos de prueba (una sola pasada)
            print("🔄 [PASO 2] Preparando llamada a OpenAI para ARTÍCULOS/ACCESORIOS/EQUIPOS...")
            items_messages = self._create_openai_prompt_items(base64_image_items)

            print("📞 [PASO 2] Llamando a OpenAI API (artículos/accesorios/equipos)...")
            items_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=items_messages,
                max_tokens=1600,
                temperature=0,
                response_format={"type": "json_object"}
            )
            print("✅ [PASO 2] Respuesta recibida de OpenAI")

            items_content = items_response.choices[0].message.content
            print("================== RAW OPENAI RESPONSE (ITEMS) ====================")
            print(items_content)
            print("===================================================================")

            # Intentar parsear ITEMS con el parser robusto
            try:
                items_data = self._safe_parse_json(items_content)
            except json.JSONDecodeError:
                print("⚠️ [PASO 2] Error al parsear JSON de ITEMS, intentando reparación con OpenAI...")
                items_data = self._fix_json_with_openai(items_content, context="items")

            print("================== PARSED JSON DATA (ITEMS) ======================")
            print(json.dumps(items_data, indent=2))
            print("===================================================================")

            # 4. Fusionar resultados de ambas llamadas en una sola estructura cruda
            raw_data: Dict[str, Any] = {}
            raw_data.update(header_data or {})
            # Los campos de artículos/accesorios/equipos de prueba vienen de la llamada de ITEMS
            for key in ("articulos", "accesorios", "equipos_prueba"):
                if isinstance(items_data, dict) and key in items_data:
                    raw_data[key] = items_data.get(key)

            print("================== RAW DATA COMBINADO ============================")
            print(json.dumps(raw_data, indent=2))
            print("==================================================================")
            
            # Guardar datos RAW para debug (antes del post-procesamiento)
            raw_empresa_origen = raw_data.get('empresa_origen', {})
            raw_empresa_destino = raw_data.get('empresa_destino', {})

            # 5. Post-procesar los datos para corregir errores y mapear
            print("🔄 Post-procesando datos combinados...")
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

            print("================== FINAL PROCESSED DATA =================")
            print(json.dumps(result, indent=2))
            print("=========================================================")
            print(f"📊 Resumen: {len(result.get('articulos', []))} artículos, {len(result.get('accesorios', []))} accesorios")

            # Añadir información de debug para el frontend
            debug_info = {
                "empresa_origen_final": {
                    "nombre": result.get('empresa_origen', {}).get('nombre'),
                    "direccion": result.get('empresa_origen', {}).get('direccion'),
                    "codigo_postal": result.get('empresa_origen', {}).get('codigo_postal'),
                    "ciudad": result.get('empresa_origen', {}).get('ciudad'),
                    "provincia": result.get('empresa_origen', {}).get('provincia'),
                    "numero_odmc": result.get('empresa_origen', {}).get('numero_odmc'),
                },
                "empresa_destino_final": {
                    "nombre": result.get('empresa_destino', {}).get('nombre'),
                    "direccion": result.get('empresa_destino', {}).get('direccion'),
                    "codigo_postal": result.get('empresa_destino', {}).get('codigo_postal'),
                    "ciudad": result.get('empresa_destino', {}).get('ciudad'),
                    "provincia": result.get('empresa_destino', {}).get('provincia'),
                    "numero_odmc": result.get('empresa_destino', {}).get('numero_odmc'),
                },
                "empresa_origen_raw_ocr": raw_empresa_origen if 'raw_empresa_origen' in locals() else {},
                "empresa_destino_raw_ocr": raw_empresa_destino if 'raw_empresa_destino' in locals() else {},
            }
            result["_debug"] = debug_info

            return result

        except Exception as e:
            print(f"❌ Error en el procesamiento: {str(e)}")
            print(f"📚 Stack trace: {traceback.format_exc()}")
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
                        
                        **FORMATO JSON IMPORTANTE**: Todos los campos de texto (strings) deben ser cadenas de texto. Si un campo está vacío o no se encuentra, usa una cadena vacía "" (NO uses null, None, ni ningún otro valor). Ejemplos: `"codigo_postal": ""`, `"ciudad": ""`, `"provincia": ""`, `"numero_registro_entrada": ""`. Solo los campos booleanos pueden ser `false` o `true`, y las listas pueden estar vacías `[]`.
                        
                        1.  **Cabecera**: Extrae los campos de la parte superior:
                            - `tipo_transaccion`: **CRÍTICO** - Tipo de transacción. **BUSCA ESPECÍFICAMENTE EL PUNTO 1**: Busca "1." seguido de las opciones: "TRANSFER", "INVENTORY", "DESTRUCTION", "HAND RECEIPT", "OTHER" (INGLÉS) o "TRANSFERENCIA", "INVENTARIO", "DESTRUCCION", "RECIBO EN MANO", "OTRO" (ESPAÑOL). Detecta qué casilla está marcada (✓, X, o cualquier marca visible) en el punto 1. **IMPORTANTE**: Solo una casilla debe estar marcada. Si ninguna está marcada o no puedes detectarlo, devuelve `"transferencia"` como valor por defecto. Devuelve el valor como string: `"transferencia"`, `"inventario"`, `"destruccion"`, `"recibo_en_mano"`, o `"otro"`. Si no encuentras ninguna marca, usa `"transferencia"` como valor por defecto.
                            - `numero_registro_salida`: **CRÍTICO** - Número de registro de salida. Este es un NÚMERO o CÓDIGO alfanumérico (ej: "SA2024-0001", "12345", etc.), **NO es una FECHA, NO es "DATE OF REPORT", NO es "DATE OF TRANSACTION"**. **BUSCA ESPECÍFICAMENTE EL PUNTO 4**: Busca "4." seguido de "Nº Registro de Salida" (ESPAÑOL) o "Outgoing Number" (INGLÉS). Etiquetas en ESPAÑOL: "4. Nº Registro de Salida", "Nº Registro de Salida", "Número Registro Salida", "Registro Salida". Etiquetas en INGLÉS: "4. Outgoing Number", "Outgoing No.", "Exit Registration Number", "Registration Number", "Exit Reg. No.", "Reg. No.". **⚠️⚠️⚠️ CRÍTICO - NO CONFUNDAS CON FECHAS**: Si encuentras una fecha (formato YYYY-MM-DD, DD/MM/YYYY, o similar) en el punto 4, NO la uses. Las fechas pertenecen a los puntos 3 (DATE OF REPORT) y 5 (DATE OF TRANSACTION), NO al punto 4. **IMPORTANTE**: Si en el punto 4 no encuentras ningún valor o el campo está vacío, usa una cadena vacía "". NO inventes valores. Si encuentras una fecha, NO la uses aquí. Si encuentras una dirección completa (con calle, número, ciudad), NO la uses aquí. Si no encuentras un número de registro de salida en el punto 4, usa una cadena vacía "".
                            - `fecha_informe`: **CRÍTICO** - Fecha del informe. **BUSCA ESPECÍFICAMENTE EL PUNTO 3**: Busca "3." seguido de "DATE OF REPORT" o "Fecha del Informe". Etiquetas en ESPAÑOL: "3. Fecha del Informe", "Fecha del Informe", "Fecha Informe", "Fecha Informe:". Etiquetas en INGLÉS: "3. DATE OF REPORT", "3. Report Date", "Report Date", "Date of Report", "Report Date:", "Date:". **IMPORTANTE**: Este campo debe contener SOLO una FECHA en formato YYYY-MM-DD (ej: "2024-12-15"). NO uses números ODMC, códigos, ni ningún otro valor que no sea una fecha. Si no encuentras una fecha en el punto 3, usa una cadena vacía "".
                            - `numero_registro_entrada`: **CRÍTICO** - Número de registro de entrada. Este es un NÚMERO o CÓDIGO alfanumérico, **NO es una FECHA, NO es "DATE OF REPORT", NO es "DATE OF TRANSACTION", NO es un número ODMC, NO es "ACCT. NO", NO es el número ODMC de ninguna empresa**. **BUSCA ESPECÍFICAMENTE EL PUNTO 6**: Busca "6." seguido de "Nº Registro de Entrada" (ESPAÑOL) o "Incoming Number" (INGLÉS). Etiquetas en ESPAÑOL: "6. Nº Registro de Entrada", "Nº Registro de Entrada", "Registro Entrada". Etiquetas en INGLÉS: "6. Incoming Number", "Incoming No.", "Entry Registration Number", "Entry Reg. No.". **⚠️⚠️⚠️ CRÍTICO - NO CONFUNDAS CON FECHAS**: Si encuentras una fecha (formato YYYY-MM-DD, DD/MM/YYYY, o similar) en el punto 6, NO la uses. Las fechas pertenecen a los puntos 3 (DATE OF REPORT) y 5 (DATE OF TRANSACTION), NO al punto 6. **⚠️⚠️⚠️ CRÍTICO - NO CONFUNDAS CON ODMC**: Si encuentras un número que está en la sección de empresas (junto a "ACCT. NO" o "ODMC"), ese número pertenece a `numero_odmc` de la empresa, NO a `numero_registro_entrada`. Ejemplos de números ODMC que NO debes usar aquí: "000303", "EMAD-004-E08", "02.01.06.21", etc. **IMPORTANTE**: Si en el punto 6 no encuentras ningún valor o el campo está vacío, usa una cadena vacía "". NO inventes valores. Si encuentras una fecha, NO la uses aquí. Si encuentras "ACCT. NO" o un número ODMC, NO lo uses aquí. Si no encuentras un número de registro de entrada en el punto 6, usa una cadena vacía "".
                            - `fecha_transaccion`: **🔥 CRÍTICO - ESTE CAMPO ES PRIORITARIO** - Fecha de la transacción. **⚠️⚠️⚠️ ATENCIÓN: Este campo es DIFERENTE de "Fecha del Informe" / "Date of Report". NO los confundas. ⚠️⚠️⚠️** 
                          
                          **INSTRUCCIONES ESPECÍFICAS PARA EXTRAER `fecha_transaccion`:**
                          1. **BUSCA ESPECÍFICAMENTE EL PUNTO 5**: Busca "5." seguido de texto que mencione "DATE OF" o "FECHA DE". La sección 5 es SIEMPRE la fecha de transacción. NO confundas con el punto 3 que es la fecha del informe.
                          2. Etiquetas en ESPAÑOL que debes buscar: "5. Fecha de la Transacción", "5. Fecha Transacción", "5. Fecha de Transacción", "Fecha de la Transacción", "Fecha Transacción".
                          3. Etiquetas en INGLÉS que debes buscar: "5. DATE OF TRASACTION" (con error de ortografía), "5. DATE OF TRANSACTION", "5. DATE OF TRAS ACTION", "5. DATE OF TRASACTION" (con error), "5. Transaction Date".
                          4. **REGLA ABSOLUTA**: 
                             - Si ves "3." seguido de "DATE OF REPORT" o "Fecha del Informe" → esa fecha va a `fecha_informe` (punto 3)
                             - Si ves "5." seguido de "DATE OF TRANSACTION" / "DATE OF TRASACTION" / "Fecha de la Transacción" → esa fecha va a `fecha_transaccion` (punto 5)
                          5. **BUSCA ACTIVAMENTE EL PUNTO 5**: Escanea la cabecera buscando específicamente "5." seguido de "DATE OF" o "FECHA DE" y luego una fecha. Esa fecha es `fecha_transaccion`.
                          6. Este campo debe contener SOLO una FECHA en formato YYYY-MM-DD (ej: "2024-12-15").
                          7. NO uses números ODMC, códigos, ni ningún otro valor que no sea una fecha.
                          8. **SI ENCUENTRAS una fecha en el punto 5 (junto a "5." y "Transaction"/"Transacción"/"Trasaction"), esa es `fecha_transaccion`.**
                          9. Si NO encuentras ninguna fecha en el punto 5, usa una cadena vacía "" en lugar de inventar una fecha.
                        2.  **Empresas**: 
                            - Busca dos secciones de empresa en el documento. Identifícalas por posición visual:
                              * La sección que está ARRIBA (parte superior del documento) → `empresa_origen`
                              * La sección que está ABAJO (parte inferior del documento) → `empresa_destino`
                            - Si hay etiquetas explícitas, úsalas como referencia adicional:
                              * "DE", "FROM", "ORIGEN", "ORIGIN" → `empresa_origen`
                              * "PARA", "TO", "DESTINATION" → `empresa_destino`
                            - Para cada empresa extrae los siguientes campos siguiendo el orden típico (puede haber saltos):
                              * **`numero_odmc`**: Busca "ACCT. NO" o "ODMC" y extrae el número/código que aparece debajo o junto a esa etiqueta. Formato ODMC puede ser: alfanumérico con guiones (ej: "EMAD-004-E08", "EMAD - 004"), con puntos (ej: "02.01.06.21"), solo números (ej: "000303", "2010622"), o códigos alfanuméricos sin guiones (ej: "EMAD004").
                              * **`nombre`**: El nombre completo de la empresa/organización. Está después del número ODMC, ANTES de las líneas de dirección/ciudad. Las letras sueltas (T, R, F, OM, etc.) son parte de "TO" o "FROM" escritas en VERTICAL, NO son etiquetas. Ignora esas letras verticales. El nombre puede ser una línea completa o múltiples líneas si forman parte del nombre de la empresa. **NO uses ciudades o direcciones como nombre**.
                              * **`direccion`**: La dirección física completa (calle, número, etc.). Aparece después del nombre. Si es una calle con número, es `direccion`. Si es solo un nombre de lugar/ciudad sin calle, puede ser `ciudad` o `direccion` según el contexto. Si solo aparece una ciudad sin calle, déjala en `ciudad` y `direccion` vacío.
                              * **`codigo_postal`**: **🔥🔥🔥 CRÍTICO - BUSCA ACTIVAMENTE ESTE CAMPO** - Código postal numérico (típicamente 5 dígitos en España). **ESTE CAMPO SIEMPRE ESTÁ PRESENTE EN LA INFORMACIÓN DE LA EMPRESA, DESPUÉS DE LA DIRECCIÓN**. **FORMATOS COMUNES**:
                                - **Formato con guión y paréntesis**: "28300-ARANJUEZ (MADRID)" → codigo_postal: "28300", ciudad: "ARANJUEZ", provincia: "MADRID"
                                - **Formato con guión y paréntesis**: "28703-SAN SEBASTIAN DE LOS REYES (MADRID)" → codigo_postal: "28703", ciudad: "SAN SEBASTIAN DE LOS REYES", provincia: "MADRID"
                                - **Formato con guión**: "28071 – Madrid" → codigo_postal: "28071", ciudad: "Madrid"
                                - **Formato separado por espacio**: "28071 Madrid" → codigo_postal: "28071", ciudad: "Madrid"
                                - **Formato separado por coma**: "28071, Madrid" → codigo_postal: "28071", ciudad: "Madrid"
                                - **Formato en línea separada**: Dirección en una línea, código postal y ciudad en la siguiente línea
                                - **PATRÓN CLAVE**: Busca un número de 5 dígitos (ej: "28071", "28300", "28703", "08001", "41001") que aparece DESPUÉS de la dirección y ANTES o JUNTO a la ciudad
                                - **EJEMPLOS REALES DE DOCUMENTOS**:
                                  * "C/ JOAQUIN RODRIGO, 11\n28300-ARANJUEZ (MADRID)" → codigo_postal: "28300"
                                  * "AV.SOMOSIERRA,12\n28703-SAN SEBASTIAN DE LOS REYES (MADRID)" → codigo_postal: "28703"
                                  * "C/ Vitruvio, 1\n28071 – Madrid" → codigo_postal: "28071"
                                - Si no encuentras un código postal (5 dígitos numéricos), usa "".
                              * **`ciudad`**: **🔥🔥🔥 CRÍTICO - BUSCA ACTIVAMENTE ESTE CAMPO** - Nombre de la ciudad. **ESTE CAMPO SIEMPRE ESTÁ PRESENTE EN LA INFORMACIÓN DE LA EMPRESA, DESPUÉS DEL CÓDIGO POSTAL**. **FORMATOS COMUNES**:
                                - **Formato con guión y paréntesis**: "28300-ARANJUEZ (MADRID)" → ciudad: "ARANJUEZ"
                                - **Formato con guión y paréntesis**: "28703-SAN SEBASTIAN DE LOS REYES (MADRID)" → ciudad: "SAN SEBASTIAN DE LOS REYES"
                                - **Formato con guión**: "28071 – Madrid" → ciudad: "Madrid"
                                - **Formato separado por espacio**: "28071 Madrid" → ciudad: "Madrid"
                                - **PATRÓN CLAVE**: Busca el nombre de la ciudad que aparece DESPUÉS del código postal (separado por guión "-" o espacio). La ciudad está ANTES de la provincia (que puede estar entre paréntesis).
                                - **EJEMPLOS REALES DE DOCUMENTOS**:
                                  * "28300-ARANJUEZ (MADRID)" → ciudad: "ARANJUEZ"
                                  * "28703-SAN SEBASTIAN DE LOS REYES (MADRID)" → ciudad: "SAN SEBASTIAN DE LOS REYES"
                                  * "28071 – Madrid" → ciudad: "Madrid"
                                - Ejemplos comunes: "Madrid", "ARANJUEZ", "SAN SEBASTIAN DE LOS REYES", "Barcelona", "Valencia", "Sevilla", etc.
                                - **NO confundas ciudades con nombres de empresa**. Si aparece "Madrid", "ARANJUEZ", "SAN SEBASTIAN DE LOS REYES", etc., es `ciudad`, NO es nombre de empresa.
                                - Si no encuentras una ciudad claramente identificable, usa "".
                              * **`provincia`**: **🔥🔥🔥 CRÍTICO - BUSCA ACTIVAMENTE ESTE CAMPO** - Nombre de la provincia/región. **ESTE CAMPO PUEDE ESTAR ENTRE PARÉNTESIS DESPUÉS DE LA CIUDAD**. **FORMATOS COMUNES**:
                                - **Formato entre paréntesis**: "28300-ARANJUEZ (MADRID)" → provincia: "MADRID"
                                - **Formato entre paréntesis**: "28703-SAN SEBASTIAN DE LOS REYES (MADRID)" → provincia: "MADRID"
                                - **Formato implícito**: "28071 – Madrid" → provincia: "Madrid" (cuando la ciudad y provincia tienen el mismo nombre)
                                - **PATRÓN CLAVE**: Busca texto entre paréntesis "(...)" después de la ciudad. Ese texto suele ser la provincia. Si no hay paréntesis pero la ciudad es una capital (ej: "Madrid", "Barcelona"), la provincia suele ser la misma que la ciudad.
                                - **EJEMPLOS REALES DE DOCUMENTOS**:
                                  * "28300-ARANJUEZ (MADRID)" → provincia: "MADRID"
                                  * "28703-SAN SEBASTIAN DE LOS REYES (MADRID)" → provincia: "MADRID"
                                  * "28071 – Madrid" → provincia: "Madrid" (mismo nombre que la ciudad)
                                - Ejemplos comunes: "MADRID", "Madrid", "Barcelona", "Valencia", "Sevilla", etc.
                                - Si no encuentras una provincia claramente identificable, usa "".
                            - **ORDEN TÍPICO DE INFORMACIÓN** (puede haber saltos): Número ODMC → Nombre → Dirección → Código Postal → Ciudad → Provincia
                            - **NOTA**: Las letras sueltas (T, R, F, OM) son parte de "TO"/"FROM" escritas verticalmente. Ignóralas al extraer datos.
                            - **NO confundas**: El nombre de la empresa NO es una ciudad. "San Agustin de Guadalix" es ciudad, NO nombre de empresa. "EMPRESA AICOX" es nombre de empresa.
                            - **NO inviertas**: ARRIBA = origen, ABAJO = destino.
                        3.  **Tabla de Artículos**:
                            - Primero, cuenta el número TOTAL de filas de la tabla de inventario (excluyendo cabeceras).
                            - Debes devolver EXACTAMENTE ese mismo número de elementos en la lista `articulos`. No debes agrupar ni fusionar filas aunque parezcan similares o repetidas.
                            - Extrae CADA fila de la tabla en una lista de objetos `articulos` (una fila = un elemento en `articulos`).
                            - Para CADA artículo, DEBES extraer los siguientes campos de la tabla:
                              * `indice_fila`: el número de la fila tal y como aparece en la primera columna de la tabla (1, 2, 3, ...).
                              * `codigo_producto`: **CRÍTICO** - El valor de la columna "TÍTULO CORTO / EDICIÓN" (en ESPAÑOL) o "SHORT TITLE / EDITION" (en INGLÉS). Este es el código del producto. **NO confundir con OBSERVACIONES/REMARKS**.
                              * `observaciones`: **CRÍTICO** - El valor de la columna "OBSERVACIONES" (en ESPAÑOL) o "REMARKS" (en INGLÉS). Esta es la descripción/observaciones del producto. **MUY IMPORTANTE**: 
                                - Este campo NO debe contener el mismo valor que "TÍTULO CORTO / EDICIÓN" o "SHORT TITLE / EDITION".
                                - Si la celda de OBSERVACIONES/REMARKS está vacía o contiene el mismo texto que el título corto, usa una cadena vacía "".
                                - Solo extrae texto que sea diferente del título corto y que sea información adicional sobre el producto.
                              * `cantidad`: El número de la columna "CANTIDAD" (debe ser un número entero)
                              * `numero_serie_inicio`: El valor de la columna "NÚMERO DE SERIE - INICIO"
                              * `numero_serie_fin`: El valor de la columna "NÚMERO DE SERIE - FIN"
                              * `cc`: El valor de la columna "CC" o "ALC" (código de contabilidad / Accounting Legend Code). **BUSCA ESPECÍFICAMENTE LA COLUMNA 12**: Busca "12. ALC" (INGLÉS) o "12. CC" (ESPAÑOL) en la cabecera de la tabla. Esta columna puede estar etiquetada como "ALC", "CC", "12. ALC", o "12. CC". Los valores más comunes son 1, 2 o 3:
                                - **1**: Contabilizable por número de serie (Accountable by serial number)
                                - **2**: Contabilizable por cantidad (Accountable by quantity)
                                - **3**: Acuse de recibo inicial (Initial receipt required)
                                **IMPORTANTE**: Extrae el valor numérico que aparece en la celda de la columna 12 (ALC/CC). Puede aparecer solo el número (ej: "1"), o con marcas (ej: "1 ☑", "1 #", "1✓"). Extrae SOLO el número, ignorando las marcas. Si la celda está vacía, usa una cadena vacía "". Si encuentras cualquier otro valor numérico, extrae ese valor tal como aparece.
                                Devuelve el valor como string (puede ser "1", "2", "3", otro valor numérico, o "" si está vacío).
                            - Es CRÍTICO que no omitas ningún artículo, aunque dos filas sean idénticas o casi idénticas. Si hay 30 filas en la tabla, debe haber 30 elementos en `articulos`, con `indice_fila` de 1 a 30 sin huecos.
                            - **IMPORTANTE**: 
                              - "TÍTULO CORTO / EDICIÓN" (ESPAÑOL) o "SHORT TITLE / EDITION" (INGLÉS) va a `codigo_producto`.
                              - "OBSERVACIONES" (ESPAÑOL) o "REMARKS" (INGLÉS) va a `observaciones`.
                              - **NO dupliques información**: Si OBSERVACIONES/REMARKS contiene el mismo texto que TÍTULO CORTO/EDICIÓN, deja `observaciones` como cadena vacía "".
                              - `observaciones` solo debe contener información adicional que NO esté en el título corto.
                        4.  **Accesorios y Equipos de Prueba**: Extrae las listas de "ACCESORIOS ENTREGADOS" y "EQUIPOS PRUEBAS". A veces el título puede variar ligeramente (p.ej. "EQUIPOS DE PRUEBA AICOX"); debes poder manejar estas variaciones.
                        5.  **Firmas (CRÍTICO)**:
                            - El documento tiene dos bloques de firma: uno a la **izquierda (recuadro 15)** y otro a la **derecha (recuadro 16)**.
                            - **Usa la posición visual como criterio principal.**
                            - Los datos del bloque de la **izquierda** corresponden al objeto `destinatario`.
                            - Los datos del bloque de la **derecha** corresponden al objeto `testigo`.
                            - Es crucial que no mezcles la información. Si solo hay una firma en el bloque derecho, `destinatario` debe ser `null` o un objeto con campos vacíos.
                            - Para cada bloque, busca explícitamente las etiquetas y extrae sus valores:
                              * **Nombre**: Busca "Nombre y Apellidos" (ESPAÑOL) o "Name", "Name and Surname" (INGLÉS). Extrae el valor para el campo `nombre`. A menudo el nombre está precedido por "D./Dª." en español.
                              * **Empleo/Rango**: Busca "Empleo" o "Rango" (ESPAÑOL) o "Grade" (INGLÉS). Extrae el valor para el campo `empleo_rango`.
                              * **Cargo**: Busca "Cargo" (ESPAÑOL) o "Service" (INGLÉS). Extrae el valor para el campo `cargo`.
                        6.  **Observaciones Generales**: Extrae el campo "17. OBSERVACIONES DEL ODMC REMITENTE".
                        7.  **Casillas de verificación - Estado del Material (CRÍTICO)**: 
                            - Busca la sección "14. EL MATERIAL HA SIDO:" o "14. THE MATERIAL HAS BEEN:" en el documento.
                            - Detecta qué casilla está marcada (✓, X, o cualquier marca visible):
                              * Si "RECIBIDO" (ESPAÑOL) o "RECEIVED" (INGLÉS) está marcado → `estado_material.recibido = true`, los demás `false`
                              * Si "INVENTARIADO" (ESPAÑOL) o "INVENTORIED" (INGLÉS) está marcado → `estado_material.inventariado = true`, los demás `false`
                              * Si "DESTRUIDO" (ESPAÑOL) o "DESTROYED" (INGLÉS) está marcado → `estado_material.destruido = true`, los demás `false`
                            - **IMPORTANTE**: Solo una casilla debe estar marcada. Si ninguna está marcada, todos los campos deben ser `false`.
                        8.  **Casillas de verificación - Sección 16 (CRÍTICO)**:
                            - Busca la sección "16." en el documento, cerca de las firmas.
                            - Detecta qué casillas están marcadas (✓, X, o cualquier marca visible):
                              * Si "TESTIGO" (ESPAÑOL) o "WITNESS" (INGLÉS) está marcado → `testigo = true`, si no `false`
                              * Si "OTRO" (ESPAÑOL) o "OTHER" (INGLÉS) está marcado → `otro = true`, si no `false`
                            - **IMPORTANTE**: Ambas casillas pueden estar marcadas o ninguna. Si no encuentras la sección 16, ambos campos deben ser `false`.

                        REGLAS ESTRICTAS PARA EL JSON DE SALIDA (MUY IMPORTANTE):
                        - El resultado debe ser SIEMPRE un único objeto JSON válido, sin texto adicional antes ni después.
                        - Si algún valor de texto contiene comillas dobles en el documento original, reemplázalas por comillas simples en el valor para evitar errores de JSON.
                        - Evita saltos de línea dentro de los valores de texto; usa espacios en su lugar siempre que sea posible.
                        - Si no estás seguro de un valor de texto, usa una cadena vacía "" en lugar de inventar contenido complejo.
                        - No añadas comentarios, explicaciones ni campos extra fuera de la estructura indicada.

                        El JSON final debe tener esta estructura exacta. No incluyas texto o caracteres fuera del objeto JSON.
                        {
                          "cabecera": {
                            "tipo_transaccion": "String (valores posibles: 'transferencia', 'inventario', 'destruccion', 'recibo_en_mano', 'otro')",
                            "numero_registro_salida": "String",
                            "fecha_informe": "String (YYYY-MM-DD)",
                            "numero_registro_entrada": "String",
                            "fecha_transaccion": "String (YYYY-MM-DD)",
                          },
                          "empresa_origen": { "nombre": "String", "direccion": "String", "codigo_postal": "String", "ciudad": "String", "provincia": "String", "numero_odmc": "String" },
                          "empresa_destino": { "nombre": "String", "direccion": "String", "codigo_postal": "String", "ciudad": "String", "provincia": "String", "numero_odmc": "String" },
                          "articulos": [
                            { "indice_fila": "Int (número de fila en la tabla, empezando en 1)", "codigo_producto": "String (TÍTULO CORTO / EDICIÓN)", "observaciones": "String (OBSERVACIONES/REMARKS)", "cantidad": "Int", "numero_serie_inicio": "String", "numero_serie_fin": "String", "cc": "String (valores válidos: '1', '2' o '3')" }
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
                          "testigo": "Boolean (true si la casilla TESTIGO está marcada en sección 16)",
                          "otro": "Boolean (true si la casilla OTRO está marcada en sección 16)",
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

    def _create_openai_prompt_header(self, image_base64: str) -> list:
        """
        Prompt enfocado SOLO en cabecera, empresas, estado del material, firmas y observaciones.
        No debe devolver artículos ni accesorios (o dejarlos como listas vacías).
        """
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
                        Analiza la imagen de este documento AC-21 y EXTRAe ÚNICAMENTE:
                        - La CABECERA:
                          * `tipo_transaccion`: **CRÍTICO** - Tipo de transacción. **BUSCA ESPECÍFICAMENTE EL PUNTO 1**: Busca "1." seguido de las opciones: "TRANSFER", "INVENTORY", "DESTRUCTION", "HAND RECEIPT", "OTHER" (INGLÉS) o "TRANSFERENCIA", "INVENTARIO", "DESTRUCCION", "RECIBO EN MANO", "OTRO" (ESPAÑOL). Detecta qué casilla está marcada (✓, X, o cualquier marca visible) en el punto 1. **IMPORTANTE**: Solo una casilla debe estar marcada. Si ninguna está marcada o no puedes detectarlo, devuelve `"transferencia"` como valor por defecto. Devuelve el valor como string: `"transferencia"`, `"inventario"`, `"destruccion"`, `"recibo_en_mano"`, o `"otro"`. Si no encuentras ninguna marca, usa `"transferencia"` como valor por defecto.
                          * `numero_registro_salida`: **CRÍTICO** - Número de registro de salida. Este es un NÚMERO o CÓDIGO alfanumérico (ej: "SA2024-0001", "12345", etc.), **NO es una FECHA, NO es "DATE OF REPORT", NO es "DATE OF TRANSACTION", NO es una dirección física, NO es un número ODMC, NO es "ACCT. NO"**. **BUSCA ESPECÍFICAMENTE EL PUNTO 4**: Busca "4." seguido de "Nº Registro de Salida" (ESPAÑOL) o "Outgoing Number" (INGLÉS). Etiquetas en ESPAÑOL: "4. Nº Registro de Salida", "Nº Registro de Salida", "Número Registro Salida", "Registro Salida". Etiquetas en INGLÉS: "4. Outgoing Number", "Outgoing No.", "Exit Registration Number", "Registration Number", "Exit Reg. No.", "Reg. No.". **⚠️⚠️⚠️ CRÍTICO - NO CONFUNDAS CON FECHAS**: Si encuentras una fecha (formato YYYY-MM-DD, DD/MM/YYYY, o similar) en el punto 4, NO la uses. Las fechas pertenecen a los puntos 3 (DATE OF REPORT) y 5 (DATE OF TRANSACTION), NO al punto 4. **IMPORTANTE**: Si en el punto 4 no encuentras ningún valor o el campo está vacío, usa una cadena vacía "". NO inventes valores. Si encuentras una fecha, NO la uses aquí. Si encuentras "ACCT. NO" o un número ODMC, NO lo uses aquí. Si encuentras una dirección completa (con calle, número, ciudad), NO la uses aquí. Si no encuentras un número de registro de salida en el punto 4, usa una cadena vacía "".
                          * `fecha_informe`: **CRÍTICO** - Fecha del informe. **BUSCA ESPECÍFICAMENTE EL PUNTO 3**: Busca "3." seguido de "DATE OF REPORT" o "Fecha del Informe". Etiquetas en ESPAÑOL: "3. Fecha del Informe", "Fecha del Informe", "Fecha Informe", "Fecha Informe:". Etiquetas en INGLÉS: "3. DATE OF REPORT", "3. Report Date", "Report Date", "Date of Report", "Report Date:", "Date:". **IMPORTANTE**: Este campo debe contener SOLO una FECHA en formato YYYY-MM-DD (ej: "2024-12-15"). NO uses números ODMC, códigos, "ACCT. NO", ni ningún otro valor que no sea una fecha. Si no encuentras una fecha en el punto 3, usa una cadena vacía "".
                          * `numero_registro_entrada`: **CRÍTICO** - Número de registro de entrada. Este es un NÚMERO o CÓDIGO alfanumérico, **NO es un número ODMC, NO es "ACCT. NO", NO es el número ODMC de ninguna empresa**. **BUSCA ESPECÍFICAMENTE EL PUNTO 6**: Busca "6." seguido de "Nº Registro de Entrada" (ESPAÑOL) o "Incoming Number" (INGLÉS). Etiquetas en ESPAÑOL: "6. Nº Registro de Entrada", "Nº Registro de Entrada", "Registro Entrada". Etiquetas en INGLÉS: "6. Incoming Number", "Incoming No.", "Entry Registration Number", "Entry Reg. No.". **⚠️⚠️⚠️ CRÍTICO - NO CONFUNDAS**: Si encuentras un número que está en la sección de empresas (junto a "ACCT. NO" o "ODMC"), ese número pertenece a `numero_odmc` de la empresa, NO a `numero_registro_entrada`. Ejemplos de números ODMC que NO debes usar aquí: "000303", "EMAD-004-E08", "02.01.06.21", etc. **IMPORTANTE**: Si en el punto 6 no encuentras ningún valor o el campo está vacío, usa una cadena vacía "". NO inventes valores. Si encuentras "ACCT. NO" o un número ODMC, NO lo uses aquí. Si no encuentras un número de registro de entrada en el punto 6, usa una cadena vacía "".
                          * `fecha_transaccion`: **🔥 CRÍTICO - ESTE CAMPO ES PRIORITARIO** - Fecha de la transacción. **⚠️⚠️⚠️ ATENCIÓN: Este campo es DIFERENTE de "Fecha del Informe" / "Date of Report". NO los confundas. ⚠️⚠️⚠️** 
                          
                          **INSTRUCCIONES ESPECÍFICAS PARA EXTRAER `fecha_transaccion`:**
                          1. **BUSCA ESPECÍFICAMENTE EL PUNTO 5**: Busca "5." seguido de texto que mencione "DATE OF" o "FECHA DE". La sección 5 es SIEMPRE la fecha de transacción. NO confundas con el punto 3 que es la fecha del informe.
                          2. **BUSCA EN LA CABECERA**: Escanea toda la parte superior del documento (cabecera) buscando:
                             - "5." seguido de "DATE OF TRASACTION" o "DATE OF TRANSACTION" o "FECHA DE TRANSACCIÓN"
                             - Cualquier fecha que aparezca después del punto 5 y antes del punto 6 o 7
                          3. Etiquetas en ESPAÑOL: "5. Fecha de la Transacción", "5. Fecha Transacción", "5. Fecha de Transacción", "Fecha de la Transacción", "Fecha Transacción".
                          4. Etiquetas en INGLÉS: "5. DATE OF TRASACTION" (con error de ortografía), "5. DATE OF TRANSACTION", "5. DATE OF TRAS ACTION", "5. Transaction Date", "5. DATE OF TRASACTION" (con error).
                          5. **REGLA ABSOLUTA**: 
                             - Si ves "3." seguido de "DATE OF REPORT" o "Fecha del Informe" → esa fecha va a `fecha_informe` (punto 3)
                             - Si ves "5." seguido de "DATE OF TRANSACTION" / "DATE OF TRASACTION" / "Fecha de la Transacción" → esa fecha va a `fecha_transaccion` (punto 5)
                          6. **BUSCA ACTIVAMENTE EL PUNTO 5**: Escanea la cabecera buscando específicamente "5." seguido de "DATE OF" o "FECHA DE" y luego una fecha. Esa fecha es `fecha_transaccion`. Si el punto 5 está vacío o no tiene fecha visible, busca cualquier fecha que esté en la misma fila o cerca del punto 5.
                          7. Este campo debe contener SOLO una FECHA en formato YYYY-MM-DD (ej: "2024-12-15").
                          8. NO uses números ODMC, códigos, ni ningún otro valor que no sea una fecha.
                          9. **SI ENCUENTRAS una fecha en el punto 5 (junto a "5." y "Transaction"/"Transacción"/"Trasaction"), esa es `fecha_transaccion`.**
                          10. **IMPORTANTE**: Si el punto 5 existe pero no tiene fecha visible o está vacío, busca en la misma área visual (misma fila o columna) cualquier fecha que pueda corresponder al punto 5.
                          11. Si NO encuentras ninguna fecha en el punto 5 o cerca del punto 5, usa una cadena vacía "".
                        - **Empresas**: 
                          * Busca dos secciones de empresa. Identifícalas por posición:
                            - ARRIBA (parte superior) → `empresa_origen`
                            - ABAJO (parte inferior) → `empresa_destino`
                          * Si hay etiquetas, úsalas como referencia:
                            - "DE", "FROM", "ORIGEN" → `empresa_origen`
                            - "PARA", "TO", "DESTINATION" → `empresa_destino`
                          * Extrae para cada empresa siguiendo el orden típico (puede haber saltos):
                            - **`numero_odmc`**: Busca "ACCT. NO" o "ODMC" y extrae el código. Formato: "EMAD-004-E08", "02.01.06.21", "000303", "2010622", etc.
                            - **`nombre`**: Nombre completo de la empresa/organización. Está después del número ODMC, ANTES de dirección/ciudad. Las letras sueltas (T, R, F, OM, etc.) son parte de "TO" o "FROM" escritas en VERTICAL, NO son etiquetas. Ignora esas letras verticales. El nombre puede ser múltiples líneas. **NO uses ciudades como nombre**.
                            - **`direccion`**: Dirección física (calle, número). Aparece después del nombre. Si solo hay ciudad sin calle, deja vacío.
                            - **`codigo_postal`**: **🔥🔥🔥 CRÍTICO - BUSCA ACTIVAMENTE ESTE CAMPO** - Código postal numérico (típicamente 5 dígitos en España). **ESTE CAMPO SIEMPRE ESTÁ PRESENTE EN LA INFORMACIÓN DE LA EMPRESA, DESPUÉS DE LA DIRECCIÓN**. **FORMATOS COMUNES**:
                              - **Formato con guión y paréntesis**: "28300-ARANJUEZ (MADRID)" → codigo_postal: "28300", ciudad: "ARANJUEZ", provincia: "MADRID"
                              - **Formato con guión y paréntesis**: "28703-SAN SEBASTIAN DE LOS REYES (MADRID)" → codigo_postal: "28703", ciudad: "SAN SEBASTIAN DE LOS REYES", provincia: "MADRID"
                              - **Formato con guión**: "28071 – Madrid" → codigo_postal: "28071", ciudad: "Madrid"
                              - **Formato separado por espacio**: "28071 Madrid" → codigo_postal: "28071", ciudad: "Madrid"
                              - **PATRÓN CLAVE**: Busca un número de 5 dígitos (ej: "28071", "28300", "28703", "08001", "41001") que aparece DESPUÉS de la dirección y ANTES o JUNTO a la ciudad
                              - **EJEMPLOS REALES DE DOCUMENTOS**:
                                * "C/ JOAQUIN RODRIGO, 11\n28300-ARANJUEZ (MADRID)" → codigo_postal: "28300"
                                * "AV.SOMOSIERRA,12\n28703-SAN SEBASTIAN DE LOS REYES (MADRID)" → codigo_postal: "28703"
                                * "C/ Vitruvio, 1\n28071 – Madrid" → codigo_postal: "28071"
                              - Si no encuentras un código postal (5 dígitos numéricos), usa "".
                            - **`ciudad`**: **🔥🔥🔥 CRÍTICO - BUSCA ACTIVAMENTE ESTE CAMPO** - Nombre de la ciudad. **ESTE CAMPO SIEMPRE ESTÁ PRESENTE EN LA INFORMACIÓN DE LA EMPRESA, DESPUÉS DEL CÓDIGO POSTAL**. **FORMATOS COMUNES**:
                              - **Formato con guión y paréntesis**: "28300-ARANJUEZ (MADRID)" → ciudad: "ARANJUEZ"
                              - **Formato con guión y paréntesis**: "28703-SAN SEBASTIAN DE LOS REYES (MADRID)" → ciudad: "SAN SEBASTIAN DE LOS REYES"
                              - **Formato con guión**: "28071 – Madrid" → ciudad: "Madrid"
                              - **Formato separado por espacio**: "28071 Madrid" → ciudad: "Madrid"
                              - **PATRÓN CLAVE**: Busca el nombre de la ciudad que aparece DESPUÉS del código postal (separado por guión "-" o espacio). La ciudad está ANTES de la provincia (que puede estar entre paréntesis).
                              - **EJEMPLOS REALES DE DOCUMENTOS**:
                                * "28300-ARANJUEZ (MADRID)" → ciudad: "ARANJUEZ"
                                * "28703-SAN SEBASTIAN DE LOS REYES (MADRID)" → ciudad: "SAN SEBASTIAN DE LOS REYES"
                                * "28071 – Madrid" → ciudad: "Madrid"
                              - Ejemplos comunes: "Madrid", "ARANJUEZ", "SAN SEBASTIAN DE LOS REYES", "Barcelona", "Valencia", "Sevilla", etc.
                              - **NO confundas ciudades con nombres de empresa**. Si aparece "Madrid", "ARANJUEZ", "SAN SEBASTIAN DE LOS REYES", etc., es `ciudad`, NO es nombre de empresa.
                              - Si no encuentras una ciudad claramente identificable, usa "".
                            - **`provincia`**: **🔥🔥🔥 CRÍTICO - BUSCA ACTIVAMENTE ESTE CAMPO** - Nombre de la provincia/región. **ESTE CAMPO PUEDE ESTAR ENTRE PARÉNTESIS DESPUÉS DE LA CIUDAD**. **FORMATOS COMUNES**:
                              - **Formato entre paréntesis**: "28300-ARANJUEZ (MADRID)" → provincia: "MADRID"
                              - **Formato entre paréntesis**: "28703-SAN SEBASTIAN DE LOS REYES (MADRID)" → provincia: "MADRID"
                              - **Formato implícito**: "28071 – Madrid" → provincia: "Madrid" (cuando la ciudad y provincia tienen el mismo nombre)
                              - **PATRÓN CLAVE**: Busca texto entre paréntesis "(...)" después de la ciudad. Ese texto suele ser la provincia. Si no hay paréntesis pero la ciudad es una capital (ej: "Madrid", "Barcelona"), la provincia suele ser la misma que la ciudad.
                              - **EJEMPLOS REALES DE DOCUMENTOS**:
                                * "28300-ARANJUEZ (MADRID)" → provincia: "MADRID"
                                * "28703-SAN SEBASTIAN DE LOS REYES (MADRID)" → provincia: "MADRID"
                                * "28071 – Madrid" → provincia: "Madrid" (mismo nombre que la ciudad)
                              - Ejemplos comunes: "MADRID", "Madrid", "Barcelona", "Valencia", "Sevilla", etc.
                              - Si no encuentras una provincia claramente identificable, usa "".
                          * **ORDEN TÍPICO**: Número ODMC → Nombre → Dirección → Código Postal → Ciudad → Provincia
                          * **NOTA**: Las letras sueltas (T, R, F, OM) son parte de "TO"/"FROM" escritas verticalmente. Ignóralas al extraer datos.
                          * **NO inviertas**: ARRIBA = origen, ABAJO = destino.
                        - El ESTADO DEL MATERIAL (sección "14. EL MATERIAL HA SIDO:" o "14. THE MATERIAL HAS BEEN:"):
                          * Detecta qué casilla está marcada: "RECIBIDO"/"RECEIVED", "INVENTARIADO"/"INVENTORIED", o "DESTRUIDO"/"DESTROYED"
                          * Devuelve `estado_material` con los campos booleanos correspondientes (solo uno debe ser `true`)
                        - Las FIRMAS (bloque izquierdo = destinatario, bloque derecho = testigo):
                          * Para cada bloque de firma, busca las etiquetas:
                            - **Nombre**: "Nombre y Apellidos" (ESPAÑOL) o "Name", "Name and Surname" (INGLÉS) → campo `nombre`
                            - **Empleo/Rango**: "Empleo" o "Rango" (ESPAÑOL) o "Grade" (INGLÉS) → campo `empleo_rango`
                            - **Cargo**: "Cargo" (ESPAÑOL) o "Service" (INGLÉS) → campo `cargo`
                        - Las OBSERVACIONES GENERALES del punto 17

                        NO debes extraer la tabla de artículos en detalle en esta llamada. 
                        Si por cualquier motivo incluyes el campo "articulos", "accesorios" o "equipos_prueba", debe ser siempre una lista vacía.

                        REGLAS ESTRICTAS PARA EL JSON DE SALIDA:
                        - El resultado debe ser SIEMPRE un único objeto JSON válido, sin texto adicional antes ni después.
                        - Si algún valor de texto contiene comillas dobles en el documento original, reemplázalas por comillas simples en el valor para evitar errores de JSON.
                        - Evita saltos de línea dentro de los valores de texto; usa espacios en su lugar siempre que sea posible.
                        - Si no estás seguro de un valor de texto, usa una cadena vacía "" en lugar de inventar contenido complejo.
                        - No añadas comentarios, explicaciones ni campos extra fuera de la estructura indicada.

                        El JSON de salida debe tener al menos esta estructura:
                        {
                          "cabecera": {
                            "tipo_transaccion": "String (valores posibles: 'transferencia', 'inventario', 'destruccion', 'recibo_en_mano', 'otro')",
                            "numero_registro_salida": "String",
                            "fecha_informe": "String (YYYY-MM-DD)",
                            "numero_registro_entrada": "String",
                            "fecha_transaccion": "String (YYYY-MM-DD)",
                          },
                          "empresa_origen": { "nombre": "String", "direccion": "String", "codigo_postal": "String", "ciudad": "String", "provincia": "String", "numero_odmc": "String" },
                          "empresa_destino": { "nombre": "String", "direccion": "String", "codigo_postal": "String", "ciudad": "String", "provincia": "String", "numero_odmc": "String" },
                          "estado_material": {
                             "recibido": "Boolean",
                             "inventariado": "Boolean",
                             "destruido": "Boolean"
                          },
                          "firmas": {
                            "destinatario": { "nombre": "String", "cargo": "String", "empleo_rango": "String" },
                            "testigo": { "nombre": "String", "cargo": "String", "empleo_rango": "String" }
                          },
                          "testigo": "Boolean (true si la casilla TESTIGO está marcada en sección 16)",
                          "otro": "Boolean (true si la casilla OTRO está marcada en sección 16)",
                          "observaciones_generales": "String",
                          "articulos": [],
                          "accesorios": [],
                          "equipos_prueba": []
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

    def _create_openai_prompt_items(self, image_base64: str) -> list:
        """
        Prompt enfocado EXCLUSIVAMENTE en la tabla de artículos, accesorios y equipos de prueba.
        Ignora cabecera, empresas y firmas (no es necesario devolver esos campos aquí).
        """
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
                        Analiza SOLO las tablas de inventario del documento AC-21 y extrae:
                        - La lista completa de ARTÍCULOS (cada fila de la tabla principal de inventario)
                        - La lista de ACCESORIOS ENTREGADOS
                        - La lista de EQUIPOS DE PRUEBA

                        Reglas para los ARTÍCULOS:
                        - Primero, cuenta el número TOTAL de filas de la tabla de inventario (excluyendo cabeceras).
                        - Debes devolver EXACTAMENTE ese mismo número de elementos en la lista `articulos`. 
                          No debes agrupar ni fusionar filas aunque parezcan similares o repetidas.
                        - Extrae CADA fila de la tabla en un objeto dentro de `articulos` (una fila = un elemento).
                        - Para cada artículo, extrae:
                          * `codigo_producto`: **CRÍTICO** - El valor de la columna "TÍTULO CORTO / EDICIÓN" (en ESPAÑOL) o "SHORT TITLE / EDITION" (en INGLÉS). Este es el código del producto. **NO confundir con OBSERVACIONES/REMARKS**.
                          * `descripcion`: **CRÍTICO** - El valor de la columna "OBSERVACIONES" (en ESPAÑOL) o "REMARKS" (en INGLÉS). Esta es la descripción/observaciones del producto. **MUY IMPORTANTE**: 
                            - Busca la columna etiquetada como "OBSERVACIONES" (ESPAÑOL) o "REMARKS" (INGLÉS).
                            - Debe incluir TODO el texto visible en la celda de observaciones/remarks:
                              * No te quedes solo con las palabras en negrita; incluye también el texto normal y las frases completas.
                              * No resumas ni te limites al "título" en negrita: concatena todas las líneas de la celda en una sola cadena, separadas por espacios.
                            - **MUY IMPORTANTE - NO DUPLICAR INFORMACIÓN**:
                              * Si el contenido de OBSERVACIONES/REMARKS es idéntico o muy similar al contenido de TÍTULO CORTO/EDICIÓN, usa una cadena vacía "" para `descripcion`.
                              * `descripcion` solo debe contener información adicional que NO esté ya en `codigo_producto`.
                              * Si la celda de OBSERVACIONES/REMARKS está vacía, usa una cadena vacía "".
                          * `cantidad` (CANTIDAD, entero)
                          * `numero_serie_inicio` (NÚMERO DE SERIE - INICIO)
                          * `numero_serie_fin` (NÚMERO DE SERIE - FIN)
                          * `cc`: **CRÍTICO** - El valor de la columna "CC" o "ALC" (código de contabilidad / Accounting Legend Code). **BUSCA ESPECÍFICAMENTE LA COLUMNA 12**: Busca "12. ALC" (INGLÉS) o "12. CC" (ESPAÑOL) en la cabecera de la tabla. Esta columna puede estar etiquetada como "ALC", "CC", "12. ALC", o "12. CC". Los valores más comunes son 1, 2 o 3:
                            - **1**: Contabilizable por número de serie (Accountable by serial number)
                            - **2**: Contabilizable por cantidad (Accountable by quantity)
                            - **3**: Acuse de recibo inicial (Initial receipt required)
                            **IMPORTANTE**: Extrae el valor numérico que aparece en la celda de la columna 12 (ALC/CC). Puede aparecer solo el número (ej: "1"), o con marcas (ej: "1 ☑", "1 #", "1✓", "1#"). Extrae SOLO el número, ignorando las marcas (☑, ✓, #, etc.). Si la celda está vacía, usa una cadena vacía "". Si encuentras cualquier otro valor numérico, extrae ese valor tal como aparece.
                            Devuelve el valor como string (puede ser "1", "2", "3", otro valor numérico, o "" si está vacío).

                        Reglas para ACCESORIOS y EQUIPOS DE PRUEBA:
                        - `accesorios`: lista de objetos { "descripcion": "String", "cantidad": "Int" }
                        - `equipos_prueba`: lista de objetos { "codigo": "String" }

                        IMPORTANTE:
                        - En esta llamada NO es necesario devolver cabecera, empresas ni firmas. 
                          Si incluyes esos campos, déjalos vacíos o con valores mínimos.

                        REGLAS ESTRICTAS PARA EL JSON DE SALIDA:
                        - El resultado debe ser SIEMPRE un único objeto JSON válido, sin texto adicional antes ni después.
                        - Si algún valor de texto contiene comillas dobles en el documento original, reemplázalas por comillas simples en el valor para evitar errores de JSON.
                        - Evita saltos de línea dentro de los valores de texto; usa espacios en su lugar siempre que sea posible.
                        - Si no estás seguro de un valor de texto, usa una cadena vacía "" en lugar de inventar contenido complejo.

                        El JSON de salida debe tener al menos esta estructura:
                        {
                          "articulos": [
                            { "indice_fila": "Int", "codigo_producto": "String", "descripcion": "String", "cantidad": "Int", "numero_serie_inicio": "String", "numero_serie_fin": "String", "cc": "String" }
                          ],
                          "accesorios": [
                            { "descripcion": "String", "cantidad": "Int" }
                          ],
                          "equipos_prueba": [
                            { "codigo": "String" }
                          ]
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

    def _fix_json_with_openai(self, broken_json: str, context: str = "items") -> Dict:
        """
        Cuando OpenAI devuelve un JSON casi correcto pero con errores de sintaxis,
        usamos una segunda llamada para que *corrija* exclusivamente la estructura
        del JSON sin cambiar el contenido.
        """
        try:
            print("🛠️ Iniciando reparación de JSON con OpenAI...")
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""
                            Has generado el siguiente JSON para el contexto '{context}', pero contiene errores de sintaxis
                            (comas, llaves o nombres de propiedades sin comillas).

                            TU ÚNICA TAREA es devolver el MISMO JSON pero con sintaxis válida:
                            - No cambies los valores existentes.
                            - No elimines objetos ni elementos de las listas.
                            - No añadas texto fuera del objeto JSON.
                            - Mantén las mismas claves y el mismo número de elementos en 'articulos', 'accesorios' y 'equipos_prueba'.

                            Devuelve exclusivamente un único objeto JSON válido y nada más.
                            A continuación tienes el JSON roto:
                            ```json
                            {broken_json}
                            ```
                            """
                        }
                    ]
                }
            ]

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=2048,
                temperature=0,
                response_format={"type": "json_object"}
            )

            fixed_content = response.choices[0].message.content
            print("================== RAW OPENAI RESPONSE (JSON FIX) =================")
            print(fixed_content)
            print("===================================================================")

            fixed_data = json.loads(fixed_content)
            print("✅ Reparación de JSON completada correctamente")
            return fixed_data

        except Exception as e:
            print(f"❌ Falló la reparación de JSON con OpenAI: {str(e)}")
            print(f"📚 Stack trace: {traceback.format_exc()}")
            # Como último recurso, devolvemos un objeto mínimo para no romper el flujo,
            # pero indicamos que no hay artículos válidos.
            return {
                "articulos": [],
                "accesorios": [],
                "equipos_prueba": []
            }

    def _extract_postal_city_province_from_direccion(self, direccion: str) -> dict:
        """
        Intenta extraer código postal, ciudad y provincia de la dirección.
        Formatos comunes:
        - "28300-ARANJUEZ (MADRID)"
        - "28703-SAN SEBASTIAN DE LOS REYES (MADRID)"
        - "28071 – Madrid"
        """
        result = {"codigo_postal": None, "ciudad": None, "provincia": None}
        
        if not direccion or not isinstance(direccion, str):
            return result
        
        direccion = direccion.strip()
        print(f"🔍 [EXTRACT] Analizando dirección: '{direccion}'")
        
        # Patrón 1: "28300-ARANJUEZ (MADRID)" o "28703-SAN SEBASTIAN DE LOS REYES (MADRID)"
        pattern1 = r'(\d{5})-([A-ZÁÉÍÓÚÑ\s]+)\s*\(([A-ZÁÉÍÓÚÑ\s]+)\)'
        match1 = re.search(pattern1, direccion, re.IGNORECASE)
        if match1:
            result["codigo_postal"] = match1.group(1)
            result["ciudad"] = match1.group(2).strip()
            result["provincia"] = match1.group(3).strip()
            print(f"✅ [EXTRACT] Patrón 1 encontrado: CP={result['codigo_postal']}, Ciudad={result['ciudad']}, Provincia={result['provincia']}")
            return result
        
        # Patrón 2: "28071 – Madrid" o "28071 Madrid"
        pattern2 = r'(\d{5})\s*[–-]?\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+)'
        match2 = re.search(pattern2, direccion, re.IGNORECASE)
        if match2:
            result["codigo_postal"] = match2.group(1)
            result["ciudad"] = match2.group(2).strip()
            # Si la ciudad es una capital común, la provincia es la misma
            capitales = ["Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao", "Zaragoza"]
            if result["ciudad"] in capitales:
                result["provincia"] = result["ciudad"]
            print(f"✅ [EXTRACT] Patrón 2 encontrado: CP={result['codigo_postal']}, Ciudad={result['ciudad']}, Provincia={result['provincia']}")
            return result
        
        # Patrón 3: Buscar código postal de 5 dígitos en cualquier parte de la dirección
        pattern3 = r'\b(\d{5})\b'
        match3 = re.search(pattern3, direccion)
        if match3:
            result["codigo_postal"] = match3.group(1)
            print(f"⚠️ [EXTRACT] Solo código postal encontrado: {result['codigo_postal']}")
            
            # Intentar extraer ciudad y provincia después del código postal
            # Patrón: "28071 Madrid" o "28071, Madrid" o "28071 – Madrid"
            pattern3b = r'\d{5}\s*[–,\s]+\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+?)(?:\s*\(([A-ZÁÉÍÓÚÑ\s]+)\))?'
            match3b = re.search(pattern3b, direccion, re.IGNORECASE)
            if match3b:
                if not result["ciudad"]:
                    result["ciudad"] = match3b.group(1).strip()
                if match3b.group(2) and not result["provincia"]:
                    result["provincia"] = match3b.group(2).strip()
                print(f"✅ [EXTRACT] Patrón 3b encontrado: CP={result['codigo_postal']}, Ciudad={result['ciudad']}, Provincia={result['provincia']}")
                return result
        
        if not result["codigo_postal"] and not result["ciudad"] and not result["provincia"]:
            print(f"❌ [EXTRACT] No se encontró patrón válido en: '{direccion}'")
        return result

    def _post_process_data(self, data: dict) -> dict:
        """
        Realiza un post-procesamiento para normalizar y limpiar los datos,
        incluyendo una corrección robusta para la asignación de firmas.
        """
        
        # POST-PROCESAMIENTO DE EMPRESAS: Extraer codigo_postal, ciudad, provincia de la dirección
        for empresa_key in ['empresa_origen', 'empresa_destino']:
            if empresa_key in data:
                empresa = data[empresa_key]
                if isinstance(empresa, dict):
                    direccion = empresa.get('direccion', '')
                    codigo_postal = empresa.get('codigo_postal')
                    ciudad = empresa.get('ciudad')
                    provincia = empresa.get('provincia')
                    
                    print(f"🔍 [POST-PROCESS] {empresa_key}:")
                    print(f"   Dirección: '{direccion}'")
                    print(f"   CP actual: {codigo_postal} (tipo: {type(codigo_postal).__name__})")
                    print(f"   Ciudad actual: {ciudad} (tipo: {type(ciudad).__name__})")
                    print(f"   Provincia actual: {provincia} (tipo: {type(provincia).__name__})")
                    
                    # Si faltan campos, intentar extraerlos de la dirección
                    # Intentar extraer si falta al menos uno de los campos
                    if direccion and ((not codigo_postal or codigo_postal is None or codigo_postal == '') or 
                                      (not ciudad or ciudad is None or ciudad == '') or 
                                      (not provincia or provincia is None or provincia == '')):
                        print(f"   ⚠️ Campos faltantes detectados, intentando extraer de dirección...")
                        extracted = self._extract_postal_city_province_from_direccion(direccion)
                        
                        if extracted['codigo_postal'] and (not codigo_postal or codigo_postal is None or codigo_postal == ''):
                            empresa['codigo_postal'] = extracted['codigo_postal']
                            print(f"   ✅ CP extraído: {extracted['codigo_postal']}")
                        
                        if extracted['ciudad'] and (not ciudad or ciudad is None or ciudad == ''):
                            empresa['ciudad'] = extracted['ciudad']
                            print(f"   ✅ Ciudad extraída: {extracted['ciudad']}")
                        
                        if extracted['provincia'] and (not provincia or provincia is None or provincia == ''):
                            empresa['provincia'] = extracted['provincia']
                            print(f"   ✅ Provincia extraída: {extracted['provincia']}")
                    
                    # Convertir None a string vacío para campos de texto
                    if empresa.get('codigo_postal') is None:
                        empresa['codigo_postal'] = ""
                    if empresa.get('ciudad') is None:
                        empresa['ciudad'] = ""
                    if empresa.get('provincia') is None:
                        empresa['provincia'] = ""
        
        # POST-PROCESAMIENTO DE CABECERA: Validar que numero_registro_salida y numero_registro_entrada NO sean fechas
        cabecera = data.get('cabecera', {})
        if isinstance(cabecera, dict):
            import re
            
            def is_date_format(value: str) -> bool:
                """Detecta si un valor es una fecha en formato YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, etc."""
                if not value or not isinstance(value, str):
                    return False
                value = value.strip()
                # Patrón para YYYY-MM-DD
                if re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                    return True
                # Patrón para DD/MM/YYYY o DD-MM-YYYY
                if re.match(r'^\d{2}[\/\-]\d{2}[\/\-]\d{4}$', value):
                    return True
                # Patrón para YYYY/MM/DD
                if re.match(r'^\d{4}\/\d{2}\/\d{2}$', value):
                    return True
                return False
            
            # Validar numero_registro_salida
            num_reg_salida = cabecera.get('numero_registro_salida', '')
            if num_reg_salida and is_date_format(num_reg_salida):
                print(f"⚠️ [POST-PROCESS] numero_registro_salida contiene una fecha ({num_reg_salida}), limpiando...")
                cabecera['numero_registro_salida'] = ""
            
            # Validar numero_registro_entrada
            num_reg_entrada = cabecera.get('numero_registro_entrada', '')
            if num_reg_entrada and is_date_format(num_reg_entrada):
                print(f"⚠️ [POST-PROCESS] numero_registro_entrada contiene una fecha ({num_reg_entrada}), limpiando...")
                cabecera['numero_registro_entrada'] = ""
        
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