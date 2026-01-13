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
        "odmc_numero": None
    },
    "empresa_origen": {
        "nombre": None, "direccion": None, "codigo_postal": None, "ciudad": None, "provincia": None, "pais": None, "codigo_odmc": None, "codigo_emad": None, "nif": None, "telefono": None, "email": None
    },
    "empresa_destino": {
        "nombre": None, "direccion": None, "codigo_postal": None, "ciudad": None, "provincia": None, "pais": None, "codigo_odmc": None, "codigo_emad": None, "nif": None, "telefono": None, "email": None
    },
    "articulos": [],  # Cada artículo tiene: codigo_producto (TÍTULO CORTO/EDICIÓN), descripcion (OBSERVACIONES), cantidad, numero_serie_inicio, numero_serie_fin, cc
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
            # Puede venir como codigo_producto, titulo_corto, codigo, o descripcion (legacy)
            codigo_producto = (
                article.get("codigo_producto") or 
                article.get("titulo_corto") or 
                article.get("codigo") or 
                article.get("descripcion") or  # Legacy: si viene como descripcion, usarlo como código
                ""
            )
            
            # Extraer descripción: viene de "OBSERVACIONES" del AC21
            # Puede venir como descripcion u observaciones
            descripcion = (
                article.get("descripcion") or 
                article.get("observaciones") or 
                ""
            )
            
            sanitized_article = {
                "codigo_producto": str(codigo_producto).strip(),
                "descripcion": str(descripcion).strip(),
                "numero_serie_inicio": str(article.get("numero_serie_inicio") or "").strip(),
                "numero_serie_fin": str(article.get("numero_serie_fin") or "").strip(),
                "observaciones": str(article.get("observaciones") or "").strip(),  # Mantener observaciones por compatibilidad
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
                        
                        1.  **Cabecera**: Extrae los campos de la parte superior:
                            - `numero_registro_salida`: **CRÍTICO** - Número de registro de salida. Este es un NÚMERO o CÓDIGO alfanumérico (ej: "SA2024-0001", "12345", etc.), NO es una dirección física. Busca etiquetas como "Nº Registro de Salida", "Número Registro Salida", "Registro Salida", etc. en la parte superior del documento. Si encuentras una dirección completa (con calle, número, ciudad), NO la uses aquí. Si no encuentras un número de registro de salida, usa una cadena vacía "".
                            - `fecha_informe`: **CRÍTICO** - Fecha del informe. Busca etiquetas en ESPAÑOL: "Fecha del Informe", "Fecha Informe", "Fecha Informe:". Busca etiquetas en INGLÉS: "Report Date", "Date of Report", "Report Date:", "Date:". **IMPORTANTE**: Este campo debe contener SOLO una FECHA en formato YYYY-MM-DD (ej: "2024-12-15"). NO uses números ODMC, códigos, ni ningún otro valor que no sea una fecha. Si no encuentras una fecha, usa una cadena vacía "".
                            - `numero_registro_entrada`: **CRÍTICO** - Número de registro de entrada. Este es un NÚMERO o CÓDIGO alfanumérico, NO es un número ODMC, NO es "ACCT. NO". Busca etiquetas en ESPAÑOL: "Nº Registro de Entrada", "Registro Entrada". Busca etiquetas en INGLÉS: "Incoming Number", "Incoming No.", "Entry Registration Number", "Entry Reg. No.". **IMPORTANTE**: Si encuentras "ACCT. NO" o un número ODMC, NO lo uses aquí. Si no encuentras un número de registro de entrada, usa una cadena vacía "".
                            - `fecha_transaccion`: **🔥 CRÍTICO - ESTE CAMPO ES PRIORITARIO** - Fecha de la transacción. **⚠️⚠️⚠️ ATENCIÓN: Este campo es DIFERENTE de "Fecha del Informe" / "Date of Report". NO los confundas. ⚠️⚠️⚠️** 
                          
                          **INSTRUCCIONES ESPECÍFICAS PARA EXTRAER `fecha_transaccion`:**
                          1. Busca en la CABECERA del documento (parte superior) cualquier etiqueta que mencione "TRANSACCIÓN" o "TRANSACTION".
                          2. Etiquetas en ESPAÑOL que debes buscar: "Fecha de la Transacción", "Fecha Transacción", "Fecha Transacción:", "Fecha de Transacción", "Fecha Transacción", "Fecha Transacción", "Fecha Transacción".
                          3. Etiquetas en INGLÉS que debes buscar: "Date of Transaction", "Transaction Date", "Date of Transaction:", "Transaction Date:", "Date Transaction", "Transaction Date", "Transaction Date", "Date of Transaction", "Transaction Date", "Date Transaction".
                          4. **BUSCA ACTIVAMENTE**: Escanea toda la cabecera buscando estas palabras clave. Si ves "Transaction" o "Transacción" cerca de una fecha, esa fecha probablemente es `fecha_transaccion`.
                          5. **DIFERENCIA CRÍTICA**: 
                             - "Date of Report" / "Report Date" / "Fecha del Informe" → va a `fecha_informe`
                             - "Date of Transaction" / "Transaction Date" / "Fecha de la Transacción" → va a `fecha_transaccion`
                          6. Este campo debe contener SOLO una FECHA en formato YYYY-MM-DD (ej: "2024-12-15").
                          7. NO uses números ODMC, códigos, ni ningún otro valor que no sea una fecha.
                          8. **SI ENCUENTRAS una fecha junto a "Transaction" / "Transacción" en la cabecera, esa es `fecha_transaccion`.**
                          9. Si NO encuentras ninguna fecha etiquetada como "Transaction" / "Transacción", usa una cadena vacía "" en lugar de inventar una fecha.
                            - `odmc_numero`: **CRÍTICO** - Número ODMC. Busca etiquetas en ESPAÑOL: "ODMC", "ODMC Nº", "ODMC Number", "ODMC No.". Busca etiquetas en INGLÉS: "ODMC", "ODMC Number", "ODMC No.", "ACCT. NO" (Account Number - el número que aparece debajo de "ACCT. NO" es el ODMC). El formato del ODMC puede variar mucho: alfanumérico con guiones (ej: "EMAD-004-E08", "EMAD - 004", "ODMC-123"), solo números (ej: "000303", "123456"), o códigos alfanuméricos sin guiones (ej: "EMAD004", "ABC123"). **IMPORTANTE**: Si encuentras cualquier código o número junto a las etiquetas "ODMC", "ACCT. NO", o "EMAD", ese es el ODMC. Este es un código/número específico, NO es una fecha. NO lo pongas en campos de fecha.
                        2.  **Empresas (DE/PARA)**: Identifica claramente la empresa de origen (DE/FROM) y la de destino (PARA/TO/DESTINATION). Extrae nombre, dirección completa, código postal, ciudad, provincia (por separado), y códigos ODMC/EMAD. **CRÍTICO**: Cada empresa (DE y PARA) puede tener su propio número ODMC. Busca "ACCT. NO" o "ODMC" en AMBAS secciones:
                           - En la sección DE/FROM: el número debajo de "ACCT. NO" es el `numero_odmc` de `empresa_origen`
                           - En la sección PARA/TO/DESTINATION: el número debajo de "ACCT. NO" es el `numero_odmc` de `empresa_destino`
                           NO confundas el ODMC de una empresa con el de la otra. Cada empresa tiene su propio ODMC.
                        3.  **Tabla de Artículos**:
                            - Primero, cuenta el número TOTAL de filas de la tabla de inventario (excluyendo cabeceras).
                            - Debes devolver EXACTAMENTE ese mismo número de elementos en la lista `articulos`. No debes agrupar ni fusionar filas aunque parezcan similares o repetidas.
                            - Extrae CADA fila de la tabla en una lista de objetos `articulos` (una fila = un elemento en `articulos`).
                            - Para CADA artículo, DEBES extraer los siguientes campos de la tabla:
                              * `indice_fila`: el número de la fila tal y como aparece en la primera columna de la tabla (1, 2, 3, ...).
                              * `codigo_producto` o `titulo_corto`: El valor de la columna "TÍTULO CORTO / EDICIÓN" (este es el código del producto)
                              * `descripcion`: El valor de la columna "OBSERVACIONES" (esta es la descripción del producto)
                              * `cantidad`: El número de la columna "CANTIDAD" (debe ser un número entero)
                              * `numero_serie_inicio`: El valor de la columna "NÚMERO DE SERIE - INICIO"
                              * `numero_serie_fin`: El valor de la columna "NÚMERO DE SERIE - FIN"
                              * `cc`: El valor de la columna "CC" (código de contabilidad)
                            - Es CRÍTICO que no omitas ningún artículo, aunque dos filas sean idénticas o casi idénticas. Si hay 30 filas en la tabla, debe haber 30 elementos en `articulos`, con `indice_fila` de 1 a 30 sin huecos.
                            - IMPORTANTE: "TÍTULO CORTO / EDICIÓN" va a `codigo_producto`, y "OBSERVACIONES" va a `descripcion`.
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

                        REGLAS ESTRICTAS PARA EL JSON DE SALIDA (MUY IMPORTANTE):
                        - El resultado debe ser SIEMPRE un único objeto JSON válido, sin texto adicional antes ni después.
                        - Si algún valor de texto contiene comillas dobles en el documento original, reemplázalas por comillas simples en el valor para evitar errores de JSON.
                        - Evita saltos de línea dentro de los valores de texto; usa espacios en su lugar siempre que sea posible.
                        - Si no estás seguro de un valor de texto, usa una cadena vacía "" en lugar de inventar contenido complejo.
                        - No añadas comentarios, explicaciones ni campos extra fuera de la estructura indicada.

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
                          "empresa_origen": { "nombre": "String", "direccion": "String", "codigo_postal": "String", "ciudad": "String", "provincia": "String", "codigo_odmc": "String", "codigo_emad": "String", "numero_odmc": "String" },
                          "empresa_destino": { "nombre": "String", "direccion": "String", "codigo_postal": "String", "ciudad": "String", "provincia": "String", "codigo_odmc": "String", "numero_odmc": "String" },
                          "articulos": [
                            { "indice_fila": "Int (número de fila en la tabla, empezando en 1)", "codigo_producto": "String (TÍTULO CORTO / EDICIÓN)", "descripcion": "String (OBSERVACIONES)", "cantidad": "Int", "numero_serie_inicio": "String", "numero_serie_fin": "String", "cc": "String" }
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
                          * `tipo_transaccion`: Tipo de transacción (TRANSFERENCIA, INVENTARIO, etc.)
                          * `numero_registro_salida`: **CRÍTICO** - Número de registro de salida. Este es un NÚMERO o CÓDIGO alfanumérico (ej: "SA2024-0001", "12345", etc.), NO es una dirección física, NO es un número ODMC, NO es "ACCT. NO". Busca etiquetas en ESPAÑOL: "Nº Registro de Salida", "Número Registro Salida", "Registro Salida". Busca etiquetas en INGLÉS: "Outgoing Number", "Outgoing No.", "Exit Registration Number", "Registration Number", "Exit Reg. No.", "Reg. No.". **IMPORTANTE**: Si encuentras "ACCT. NO" o un número ODMC, NO lo uses aquí. Si encuentras una dirección completa (con calle, número, ciudad), NO la uses aquí. Si no encuentras un número de registro de salida, usa una cadena vacía "".
                          * `fecha_informe`: **CRÍTICO** - Fecha del informe. Busca etiquetas en ESPAÑOL: "Fecha del Informe", "Fecha Informe", "Fecha Informe:". Busca etiquetas en INGLÉS: "Report Date", "Date of Report", "Report Date:", "Date:". **IMPORTANTE**: Este campo debe contener SOLO una FECHA en formato YYYY-MM-DD (ej: "2024-12-15"). NO uses números ODMC, códigos, "ACCT. NO", ni ningún otro valor que no sea una fecha. Si no encuentras una fecha, usa una cadena vacía "".
                          * `numero_registro_entrada`: **CRÍTICO** - Número de registro de entrada. Este es un NÚMERO o CÓDIGO alfanumérico, NO es un número ODMC, NO es "ACCT. NO". Busca etiquetas en ESPAÑOL: "Nº Registro de Entrada", "Registro Entrada". Busca etiquetas en INGLÉS: "Incoming Number", "Incoming No.", "Entry Registration Number", "Entry Reg. No.". **IMPORTANTE**: Si encuentras "ACCT. NO" o un número ODMC, NO lo uses aquí. Si no encuentras un número de registro de entrada, usa una cadena vacía "".
                          * `fecha_transaccion`: **🔥 CRÍTICO - ESTE CAMPO ES PRIORITARIO** - Fecha de la transacción. **⚠️⚠️⚠️ ATENCIÓN: Este campo es DIFERENTE de "Fecha del Informe" / "Date of Report". NO los confundas. ⚠️⚠️⚠️** 
                          
                          **INSTRUCCIONES ESPECÍFICAS PARA EXTRAER `fecha_transaccion`:**
                          1. Busca en la CABECERA del documento (parte superior) cualquier etiqueta que mencione "TRANSACCIÓN" o "TRANSACTION".
                          2. Etiquetas en ESPAÑOL que debes buscar: "Fecha de la Transacción", "Fecha Transacción", "Fecha Transacción:", "Fecha de Transacción", "Fecha Transacción", "Fecha Transacción", "Fecha Transacción".
                          3. Etiquetas en INGLÉS que debes buscar: "Date of Transaction", "Transaction Date", "Date of Transaction:", "Transaction Date:", "Date Transaction", "Transaction Date", "Transaction Date", "Date of Transaction", "Transaction Date", "Date Transaction".
                          4. **BUSCA ACTIVAMENTE**: Escanea toda la cabecera buscando estas palabras clave. Si ves "Transaction" o "Transacción" cerca de una fecha, esa fecha probablemente es `fecha_transaccion`.
                          5. **DIFERENCIA CRÍTICA**: 
                             - "Date of Report" / "Report Date" / "Fecha del Informe" → va a `fecha_informe`
                             - "Date of Transaction" / "Transaction Date" / "Fecha de la Transacción" → va a `fecha_transaccion`
                          6. Este campo debe contener SOLO una FECHA en formato YYYY-MM-DD (ej: "2024-12-15").
                          7. NO uses números ODMC, códigos, ni ningún otro valor que no sea una fecha.
                          8. **SI ENCUENTRAS una fecha junto a "Transaction" / "Transacción" en la cabecera, esa es `fecha_transaccion`.**
                          9. Si NO encuentras ninguna fecha etiquetada como "Transaction" / "Transacción", usa una cadena vacía "".
                          * `odmc_numero`: **CRÍTICO** - Número ODMC. Busca etiquetas en ESPAÑOL: "ODMC", "ODMC Nº", "ODMC Number", "ODMC No.". Busca etiquetas en INGLÉS: "ODMC", "ODMC Number", "ODMC No.", "ACCT. NO" (Account Number - el número que aparece debajo de "ACCT. NO" es el ODMC). El formato del ODMC puede variar mucho: alfanumérico con guiones (ej: "EMAD-004-E08", "EMAD - 004", "ODMC-123"), solo números (ej: "000303", "123456"), o códigos alfanuméricos sin guiones (ej: "EMAD004", "ABC123"). **IMPORTANTE**: Si encuentras cualquier código o número junto a las etiquetas "ODMC", "ACCT. NO", o "EMAD", ese es el ODMC. Este es un código/número específico, NO es una fecha. NO lo pongas en campos de fecha.
                        - Los datos de EMPRESA ORIGEN (DE) y EMPRESA DESTINO (PARA): 
                          * `nombre`: Nombre de la empresa
                          * `direccion`: Dirección completa (calle, número, etc.)
                          * `codigo_postal`: Código postal (extraer por separado)
                          * `ciudad`: Ciudad (extraer por separado)
                          * `provincia`: Provincia (extraer por separado)
                          * `numero_odmc` o `codigo_odmc`: **CRÍTICO** - Número/código ODMC de la empresa. Busca etiquetas en ESPAÑOL: "ODMC", "ODMC Nº", "ODMC Number", "ODMC No." en la sección de cada empresa (DE/PARA). Busca etiquetas en INGLÉS: "ODMC", "ODMC Number", "ODMC No.", "ACCT. NO" (Account Number - el número que aparece debajo de "ACCT. NO" en la sección de la empresa es el ODMC de esa empresa). El formato del ODMC puede variar mucho: alfanumérico con guiones (ej: "EMAD-004-E08", "EMAD - 004", "ODMC-123"), solo números (ej: "000303", "123456"), o códigos alfanuméricos sin guiones (ej: "EMAD004", "ABC123"). **IMPORTANTE**: Debes buscar el ODMC TANTO en la sección DE (FROM) como en la sección PARA (TO/DESTINATION). Cada empresa puede tener su propio número ODMC. Si encuentras "ACCT. NO" en la sección DE, el número debajo es el ODMC de la empresa origen. Si encuentras "ACCT. NO" en la sección PARA/TO/DESTINATION, el número debajo es el ODMC de la empresa destino. Este es un código/número específico de la empresa, NO es una fecha ni un número de registro. Si encuentras un número ODMC en la sección de la empresa, colócalo aquí. Si no encuentras un número ODMC para la empresa, usa una cadena vacía "".
                          * `codigo_emad`: Código EMAD (si está disponible)
                        - El ESTADO DEL MATERIAL (recibido, inventariado, destruido)
                        - Las FIRMAS (bloque izquierdo = destinatario, bloque derecho = testigo)
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
                            "tipo_transaccion": "String",
                            "numero_registro_salida": "String",
                            "fecha_informe": "String (YYYY-MM-DD)",
                            "numero_registro_entrada": "String",
                            "fecha_transaccion": "String (YYYY-MM-DD)",
                            "odmc_numero": "String"
                          },
                          "empresa_origen": { "nombre": "String", "direccion": "String", "codigo_odmc": "String", "codigo_emad": "String" },
                          "empresa_destino": { "nombre": "String", "direccion": "String", "codigo_odmc": "String" },
                          "estado_material": {
                             "recibido": "Boolean",
                             "inventariado": "Boolean",
                             "destruido": "Boolean"
                          },
                          "firmas": {
                            "destinatario": { "nombre": "String", "cargo": "String", "empleo_rango": "String" },
                            "testigo": { "nombre": "String", "cargo": "String", "empleo_rango": "String" }
                          },
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
                          * `codigo_producto` (TÍTULO CORTO / EDICIÓN)
                          * `descripcion` (OBSERVACIONES). Debe incluir TODO el texto visible en la celda de observaciones:
                            - No te quedes solo con las palabras en negrita; incluye también el texto normal y las frases completas.
                            - No resumas ni te limites al “título” en negrita: concatena todas las líneas de la celda en una sola cadena, separadas por espacios.
                          * `cantidad` (CANTIDAD, entero)
                          * `numero_serie_inicio` (NÚMERO DE SERIE - INICIO)
                          * `numero_serie_fin` (NÚMERO DE SERIE - FIN)
                          * `cc` (CC)

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