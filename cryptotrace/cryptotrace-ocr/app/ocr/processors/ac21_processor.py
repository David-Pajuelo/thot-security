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
    
    def preprocess_image(self, image_bytes: bytes) -> bytes:
        """
        Preprocesa la imagen para mejorar la calidad del OCR:
        - Aumenta resolución si es muy pequeña
        - Mejora contraste
        - Reduce ruido (opcional)
        """
        if Image is None:
            print("⚠️ PIL no disponible, saltando preprocesamiento")
            return image_bytes
        
        try:
            img = Image.open(BytesIO(image_bytes)).convert("RGB")
            original_size = img.size
            print(f"📐 [PREPROCESS] Tamaño original: {original_size[0]}x{original_size[1]}")
            
            # Aumentar resolución si es muy pequeña (< 2000px de ancho)
            if img.width < 2000:
                scale_factor = 2000 / img.width
                new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
                img = img.resize(new_size, Image.LANCZOS)
                print(f"🔍 [PREPROCESS] Resolución aumentada: {new_size[0]}x{new_size[1]} (factor: {scale_factor:.2f}x)")
            
            # Mejorar contraste
            try:
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.3)  # Aumentar contraste 30%
                print("✨ [PREPROCESS] Contraste mejorado (+30%)")
            except Exception as e:
                print(f"⚠️ [PREPROCESS] Error mejorando contraste: {e}")
            
            # Convertir de vuelta a bytes
            output = BytesIO()
            img.save(output, format="PNG", optimize=True)
            processed_bytes = output.getvalue()
            print(f"✅ [PREPROCESS] Preprocesamiento completado: {len(processed_bytes)} bytes")
            return processed_bytes
            
        except Exception as e:
            print(f"❌ [PREPROCESS] Error en preprocesamiento: {str(e)}")
            print(f"📚 Stack trace: {traceback.format_exc()}")
            return image_bytes  # Devolver original si falla

    def detect_table_bounds(self, image_bytes: bytes) -> Dict[str, float]:
        """
        Detecta automáticamente los límites de la tabla usando análisis de densidad de contenido.
        Retorna top, bottom, left, right como porcentajes [0-1].
        """
        if Image is None:
            print("⚠️ PIL no disponible, usando límites por defecto")
            return {"top": 0.25, "bottom": 0.98, "left": 0.03, "right": 0.97}
        
        try:
            img = Image.open(BytesIO(image_bytes)).convert("L")  # Escala de grises
            width, height = img.size
            print(f"🔍 [DETECT BOUNDS] Analizando imagen: {width}x{height}")
            
            # Análisis por filas horizontales (detectar zona de tabla)
            row_densities = []
            sample_step = max(5, height // 200)  # Muestrear cada 5px o menos si imagen pequeña
            
            for y in range(0, height, sample_step):
                row = img.crop((0, y, width, min(y + sample_step, height)))
                # Calcular densidad: desviación estándar indica variación (más contenido = más variación)
                from PIL import ImageStat
                stat = ImageStat.Stat(row)
                row_densities.append((y, stat.stddev[0]))
            
            if not row_densities:
                print("⚠️ [DETECT BOUNDS] No se pudieron analizar filas, usando valores por defecto")
                return {"top": 0.25, "bottom": 0.98, "left": 0.03, "right": 0.97}
            
            # Encontrar umbral de densidad (percentil 70 = zona con más contenido)
            densities = [d[1] for d in row_densities]
            threshold = sorted(densities)[int(len(densities) * 0.70)]
            
            # Encontrar inicio y fin de tabla (zonas de alta densidad)
            table_start_y = None
            table_end_y = None
            
            for y, density in row_densities:
                if density > threshold:
                    if table_start_y is None:
                        table_start_y = y
                    table_end_y = y
            
            # Convertir a porcentajes con márgenes de seguridad
            if table_start_y is not None and table_end_y is not None:
                top = max(0.0, (table_start_y / height) - 0.02)  # Margen 2% arriba
                bottom = min(1.0, (table_end_y / height) + 0.02)  # Margen 2% abajo
                print(f"✅ [DETECT BOUNDS] Tabla detectada: top={top:.2%}, bottom={bottom:.2%}")
            else:
                print("⚠️ [DETECT BOUNDS] No se detectaron límites claros, usando valores por defecto")
                top = 0.25
                bottom = 0.98
            
            # Márgenes laterales fijos (las tablas suelen estar centradas)
            left = 0.03
            right = 0.97
            
            return {
                "top": top,
                "bottom": bottom,
                "left": left,
                "right": right
            }
            
        except Exception as e:
            print(f"❌ [DETECT BOUNDS] Error detectando límites: {str(e)}")
            print(f"📚 Stack trace: {traceback.format_exc()}")
            return {"top": 0.25, "bottom": 0.98, "left": 0.03, "right": 0.97}
    
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
        Respeta el indice_fila extraído del documento (puede tener saltos).
        Si el OCR no proporcionó indice_fila, asigna uno secuencial basándose en la posición.
        """
        sanitized = []
        if not isinstance(articles, list):
            return sanitized
            
        for index, article in enumerate(articles, start=1):
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
            
            # Índice de fila: OBLIGATORIO - debe venir del OCR
            # NO usar fallbacks - si falta, es un error del OCR
            indice_fila = None
            try:
                idx_raw = article.get("indice_fila") or article.get("indice") or article.get("fila")
                if idx_raw is not None and str(idx_raw).strip() != "":
                    indice_fila = int(str(idx_raw))
            except (ValueError, TypeError):
                pass
            
            # Si no se pudo extraer del OCR, registrar advertencia pero NO asignar fallback
            if indice_fila is None:
                codigo_art = article.get("codigo_producto") or article.get("titulo_corto") or f"artículo_{index}"
                logger.warning(f"⚠️ [OCR] ADVERTENCIA CRÍTICA: Artículo sin indice_fila extraído del documento. Código: {codigo_art}, Posición en array: {index}. El OCR debe extraer el número de la primera columna del documento.")
                # Dejar como None - el frontend debe validar y rechazar si falta
            
            sanitized_article = {
                "indice_fila": indice_fila,  # Respeta el número del documento (puede tener saltos)
                "codigo_producto": str(codigo_producto).strip(),
                "observaciones": str(observaciones).strip(),  # Se mapeará a descripcion en la BD
                "numero_serie_inicio": str(article.get("numero_serie_inicio") or "").strip(),
                "numero_serie_fin": str(article.get("numero_serie_fin") or "").strip(),
            }
            
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
            
            # CC: aceptar cualquier valor (número o código alfanumérico) tal como viene del OCR; vacío → ""
            cc_value = article.get("cc")
            if cc_value is None:
                sanitized_article["cc"] = ""
            else:
                cc_str = str(cc_value).strip()
                # Eliminar solo si está vacío; si tiene contenido (número o alfanumérico), conservarlo
                sanitized_article["cc"] = cc_str if cc_str else ""
            
            sanitized.append(sanitized_article)
        
        # VALIDACIÓN POST-SANITIZACIÓN: Detectar duplicados en indice_fila
        # NOTA: Los duplicados pueden ser legítimos si el documento original tiene filas con el mismo número.
        # Por lo tanto, NO eliminamos duplicados automáticamente, solo registramos una advertencia.
        indices_vistos = {}
        duplicados_encontrados = []
        for idx, art in enumerate(sanitized):
            indice_fila = art.get("indice_fila")
            if indice_fila is not None:
                if indice_fila in indices_vistos:
                    # Duplicado detectado - puede ser legítimo del documento o un error del OCR
                    duplicados_encontrados.append({
                        "indice_fila": indice_fila,
                        "primera_ocurrencia": indices_vistos[indice_fila],
                        "ocurrencia_duplicada": idx,
                        "codigo_primera": sanitized[indices_vistos[indice_fila]].get("codigo_producto", "sin código"),
                        "codigo_duplicada": art.get("codigo_producto", "sin código")
                    })
                    logger.warning(f"⚠️ [OCR] DUPLICADO DETECTADO: indice_fila {indice_fila} aparece en posiciones {indices_vistos[indice_fila]} y {idx}")
                    # Agregar también a indices_vistos para detectar múltiples duplicados del mismo número
                    if isinstance(indices_vistos[indice_fila], list):
                        indices_vistos[indice_fila].append(idx)
                    else:
                        indices_vistos[indice_fila] = [indices_vistos[indice_fila], idx]
                else:
                    indices_vistos[indice_fila] = idx
        
        # Si hay duplicados, registrar advertencia pero NO eliminar (pueden ser legítimos del documento)
        if duplicados_encontrados:
            logger.warning(f"⚠️ [OCR] ADVERTENCIA: Se detectaron {len(duplicados_encontrados)} indice_fila duplicados.")
            logger.warning(f"   Esto puede ser legítimo si el documento original tiene filas con el mismo número.")
            logger.warning(f"   O puede ser un error del OCR si está inventando filas que no existen.")
            logger.warning(f"   Se mantienen TODAS las filas para que el usuario pueda revisar.")
            for dup in duplicados_encontrados:
                logger.warning(f"   - indice_fila {dup['indice_fila']}: primera en posición {dup['primera_ocurrencia']} (código: {dup['codigo_primera']}), duplicada en posición {dup['ocurrencia_duplicada']} (código: {dup['codigo_duplicada']})")
            # NO eliminamos duplicados - se mantienen todas las filas para revisión manual
                
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
            # 0. Preprocesar imagen (mejorar calidad)
            print("🔄 [PREPROCESS] Aplicando preprocesamiento de imagen...")
            processed_image_bytes = self.preprocess_image(image_bytes)
            
            # 1. Codificar imagen completa (para cabecera/empresas/firmas)
            base64_image_full = self.encode_image(processed_image_bytes)
            print("✅ Imagen completa codificada en base64")

            # 1b. Detectar límites de tabla automáticamente si no se proporcionan
            if crop_params is None:
                print("🔍 [DETECT BOUNDS] Detectando límites de tabla automáticamente...")
                detected_bounds = self.detect_table_bounds(processed_image_bytes)
                crop_params = detected_bounds
                print(f"✅ [DETECT BOUNDS] Límites detectados: {crop_params}")
            
            # 1c. Generar imagen recortada para la tabla (ITEMS) y codificarla
            cropped_bytes = self._crop_image_for_items(processed_image_bytes, crop_params=crop_params)
            base64_image_items = self.encode_image(cropped_bytes)
            print("✅ Imagen recortada para ITEMS codificada en base64")

            # 2. Primera llamada: cabecera + empresas + estado + firmas + observaciones
            print("🔄 [PASO 1] Preparando llamada a OpenAI para CABECERA/EMPRESAS/FIRMAS...")
            header_messages = self._create_openai_prompt_header(base64_image_full)

            print("📞 [PASO 1] Llamando a OpenAI API (cabecera/empresas/firmas)...")
            header_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=header_messages,
                max_tokens=2000,  # Tokens para extracción de cabecera, empresas y firmas
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
                max_tokens=10000,  # Tokens para capturar todas las líneas (hasta 35 artículos con datos completos)
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

            # 8. Validación post-OCR: Verificar integridad de extracción
            validation_info = self._validate_extraction(cropped_bytes, result)
            if validation_info:
                result["_validation"] = validation_info
                if validation_info.get("discrepancy", 0) > 2:
                    print(f"⚠️ [VALIDATION] ADVERTENCIA: Se detectaron {validation_info['discrepancy']} líneas faltantes")
                    print(f"   Visible: {validation_info.get('estimated_visible_rows', 'N/A')}, Extraído: {validation_info.get('extracted_count', 'N/A')}")
                else:
                    print(f"✅ [VALIDATION] Validación OK: {validation_info.get('extracted_count', 0)} artículos extraídos")

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
                            - `fecha_informe`: **CRÍTICO** - Fecha del informe. **BUSCA ESPECÍFICAMENTE EL PUNTO 3**: Busca "3." seguido de "DATE OF REPORT" o "Fecha del Informe". Etiquetas en ESPAÑOL: "3. Fecha del Informe", "Fecha del Informe", "Fecha Informe", "Fecha Informe:". Etiquetas en INGLÉS: "3. DATE OF REPORT", "3. Report Date", "Report Date", "Date of Report", "Report Date:", "Date:". **IMPORTANTE**: Este campo debe contener SOLO una FECHA en formato YYYY-MM-DD (ej: "2024-12-15") o DD-MM-YYYY (ej: "15-12-2024"). Devuélvela tal como aparece en el documento. NO uses números ODMC, códigos, ni ningún otro valor que no sea una fecha. Si no encuentras una fecha en el punto 3, usa una cadena vacía "".
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
                          6. Este campo debe contener SOLO una FECHA en formato YYYY-MM-DD (ej: "2024-12-15") o DD-MM-YYYY (ej: "15-12-2024"). Devuélvela tal como aparece en el documento.
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
                              * `indice_fila`: **OBLIGATORIO - EXTRAE el número de la PRIMERA COLUMNA del documento** (puede ser 1, 2, 3, 4, 5, etc.). 
                                - **CRÍTICO**: Este campo es OBLIGATORIO. SIEMPRE debe tener un valor.
                                - Si el documento tiene saltos en los números (ej: 1, 2, 5, 6...), respeta esos saltos EXACTAMENTE.
                                - Si la primera columna NO tiene número visible, reporta `null` o `0`, pero NUNCA inventes un número secuencial.
                                - **NO asignes números secuenciales automáticamente si no ves el número en el documento.**
                                - El `indice_fila` debe reflejar el número REAL del documento, no forzar secuencia.
                              * `codigo_producto`: **CRÍTICO** - El valor de la columna "TÍTULO CORTO / EDICIÓN" (en ESPAÑOL) o "SHORT TITLE / EDITION" (en INGLÉS). Este es el código del producto. **NO confundir con OBSERVACIONES/REMARKS**.
                              * `observaciones`: **CRÍTICO** - El valor de la columna "OBSERVACIONES" (en ESPAÑOL) o "REMARKS" (en INGLÉS). Esta es la descripción/observaciones del producto. **MUY IMPORTANTE**: 
                                - **EXTRAE TODO el texto visible en la celda** (negrita, normal, todas las líneas, todo el contenido, sin omitir nada).
                                - **NO omitas texto** - si hay texto en la celda OBSERVACIONES/REMARKS, debe aparecer completo en `observaciones`.
                                - **REGLA DE DUPLICACIÓN (SOLO SI ES EXACTAMENTE IGUAL)**: Si el texto de OBSERVACIONES/REMARKS es EXACTAMENTE el mismo (carácter por carácter) que el texto de "TÍTULO CORTO / EDICIÓN", entonces usa "" (cadena vacía). Si hay CUALQUIER diferencia, incluso mínima, incluye el texto completo.
                                - Si la celda está completamente vacía, usa "".
                                - **IMPORTANTE**: Incluye TODO el texto de la celda OBSERVACIONES/REMARKS, sin filtrar ni omitir partes. Solo omite si es EXACTAMENTE igual al título corto.
                              * `cantidad`: El número de la columna "CANTIDAD" (debe ser un número entero)
                              * `numero_serie_inicio`: El valor de la columna "NÚMERO DE SERIE - INICIO"
                              * `numero_serie_fin`: El valor de la columna "NÚMERO DE SERIE - FIN"
                              * `cc`: El valor de la columna "CC" o "ALC" (código de contabilidad / Accounting Legend Code). **BUSCA ESPECÍFICAMENTE LA COLUMNA 12**: Busca "12. ALC" (INGLÉS) o "12. CC" (ESPAÑOL) en la cabecera de la tabla. Esta columna puede estar etiquetada como "ALC", "CC", "12. ALC", o "12. CC".
                                **CRÍTICO - EXTRAE EXACTAMENTE LO QUE HAY - PUEDE ESTAR VACÍO EN TODAS LAS FILAS:**
                                - Si la celda tiene un número visible y claro (ej: "1", "2", "3", "4", etc.), extrae ese número como string.
                                - Si la celda tiene un número con marcas (ej: "1 ☑", "1 #", "1✓"), extrae SOLO el número, ignorando las marcas.
                                - Si la celda está vacía, tiene solo símbolos sin número, tiene solo puntos/círculos, o no hay número visible, usa "" (cadena vacía).
                                - **PROHIBIDO:** NO inventes valores. NO asumas valores por defecto. NO uses valores de otras filas. NO asumas que debe haber un valor.
                                - **Si no estás 100% seguro de que hay un número visible y claro, usa "".**
                                - Si no encuentras la columna CC/ALC en la cabecera, usa "" para TODAS las filas.
                                - **RECUERDA: Es PERFECTAMENTE NORMAL que CC esté vacío en TODAS las filas. No intentes "completar" valores faltantes.**
                                Devuelve el valor como string (puede ser cualquier número visible en la celda, o "" si está vacío - ES NORMAL que esté vacío).
                            - Es CRÍTICO que no omitas ningún artículo, aunque dos filas sean idénticas o casi idénticas. Si hay 30 filas en la tabla, debe haber 30 elementos en `articulos`, con `indice_fila` de 1 a 30 sin huecos.
                            - **IMPORTANTE**: 
                              - "TÍTULO CORTO / EDICIÓN" (ESPAÑOL) o "SHORT TITLE / EDITION" (INGLÉS) va a `codigo_producto`.
                              - "OBSERVACIONES" (ESPAÑOL) o "REMARKS" (INGLÉS) va a `observaciones`.
                              - **REGLA DE DUPLICACIÓN (SOLO SI ES EXACTAMENTE IGUAL)**: Si el texto de OBSERVACIONES/REMARKS es EXACTAMENTE igual (carácter por carácter) al texto de TÍTULO CORTO/EDICIÓN, entonces deja `observaciones` como cadena vacía "". Si hay CUALQUIER diferencia, incluye el texto completo de OBSERVACIONES/REMARKS.
                              - **NO filtres texto parcialmente**: Si OBSERVACIONES/REMARKS contiene texto que también aparece parcialmente en el título corto, DEBES incluirlo completo en `observaciones`. Solo omite si es EXACTAMENTE igual.
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
                            "fecha_informe": "String (YYYY-MM-DD o DD-MM-YYYY)",
                            "numero_registro_entrada": "String",
                            "fecha_transaccion": "String (YYYY-MM-DD o DD-MM-YYYY)",
                          },
                          "empresa_origen": { "nombre": "String", "direccion": "String", "codigo_postal": "String", "ciudad": "String", "provincia": "String", "numero_odmc": "String" },
                          "empresa_destino": { "nombre": "String", "direccion": "String", "codigo_postal": "String", "ciudad": "String", "provincia": "String", "numero_odmc": "String" },
                          "articulos": [
                            { "indice_fila": "Int (número de fila en la tabla, empezando en 1)", "codigo_producto": "String (TÍTULO CORTO / EDICIÓN)", "observaciones": "String (OBSERVACIONES/REMARKS)", "cantidad": "Int", "numero_serie_inicio": "String", "numero_serie_fin": "String", "cc": "String (puede ser cualquier número visible en la celda CC/ALC, o '' si está vacío - ES NORMAL que esté vacío en todas las filas)" }
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
                        Extrae SOLO la cabecera, empresas, firmas y observaciones del documento AC-21.

                        **REGLAS FUNDAMENTALES:**
                        1. NO inventes datos. Si un campo está vacío o no es visible, usa "" (cadena vacía).
                        2. NO confundas campos. Cada campo tiene su ubicación específica.
                        3. NO uses valores por defecto a menos que se indique explícitamente.

                        **CABECERA:**

                        * `tipo_transaccion`: Busca "1." y detecta qué casilla está marcada:
                          - "TRANSFER"/"TRANSFERENCIA" → "transferencia"
                          - "INVENTORY"/"INVENTARIO" → "inventario"
                          - "DESTRUCTION"/"DESTRUCCION" → "destruccion"
                          - "HAND RECEIPT"/"RECIBO EN MANO" → "recibo_en_mano"
                          - "OTHER"/"OTRO" → "otro"
                          - Si ninguna está marcada o no es visible, usa "transferencia" (único caso con valor por defecto).

                        * `numero_registro_salida`: Busca "4." seguido de "Nº Registro de Salida" (ES) o "Outgoing Number" (EN).
                          - Extrae el número/código alfanumérico que aparece ahí.
                          - NO uses fechas, direcciones, ni números ODMC.
                          - Si está vacío o no es visible, usa "".

                        * `fecha_informe`: Busca "3." seguido de "DATE OF REPORT" (EN) o "Fecha del Informe" (ES).
                          - Extrae SOLO la fecha en formato YYYY-MM-DD o DD-MM-YYYY (devuélvela tal como aparece).
                          - NO uses números ODMC, códigos, ni otros valores.
                          - Si no hay fecha visible, usa "".

                        * `fecha_transaccion`: Busca "5." seguido de "DATE OF TRANSACTION" (EN) o "Fecha de la Transacción" (ES).
                          - Extrae SOLO la fecha en formato YYYY-MM-DD o DD-MM-YYYY (devuélvela tal como aparece).
                          - NO confundas con fecha_informe (punto 3).
                          - Si no hay fecha visible, usa "".

                        * `numero_registro_entrada`: Busca "6." seguido de "Nº Registro de Entrada" (ES) o "Incoming Number" (EN).
                          - Extrae el número/código alfanumérico que aparece ahí.
                          - NO uses números ODMC (esos van en `numero_odmc` de empresas).
                          - Si está vacío o no es visible, usa "".
                        **EMPRESAS:**
                        - Busca dos secciones: ARRIBA = `empresa_origen`, ABAJO = `empresa_destino`.
                        - Para cada empresa, extrae en este orden:
                          * `numero_odmc`: Busca "ACCT. NO" o "ODMC" y extrae el código visible.
                          * `nombre`: Nombre de la empresa (después de ODMC, antes de dirección). NO uses ciudades como nombre.
                          * `direccion`: Calle y número. Si solo hay ciudad, deja "".
                          * `codigo_postal`: Busca número de 5 dígitos (ej: "28071", "28300"). Si no hay, usa "".
                          * `ciudad`: Nombre de ciudad después del código postal. Si no hay, usa "".
                          * `provincia`: Texto entre paréntesis después de ciudad, o igual a ciudad si es capital. Si no hay, usa "".
                        - Si algún campo no es visible, usa "".

                        **ESTADO DEL MATERIAL:**
                        - Busca "14. EL MATERIAL HA SIDO:" o "14. THE MATERIAL HAS BEEN:".
                        - Detecta casilla marcada: "RECIBIDO"/"RECEIVED" → recibido=true, "INVENTARIADO"/"INVENTORIED" → inventariado=true, "DESTRUIDO"/"DESTROYED" → destruido=true.
                        - Si ninguna está marcada, todos false.

                        **FIRMAS:**
                        - Bloque IZQUIERDA = `destinatario`, bloque DERECHA = `testigo`.
                        - Para cada bloque, busca etiquetas y extrae:
                          * `nombre`: "Nombre y Apellidos" (ES) o "Name" (EN).
                          * `empleo_rango`: "Empleo"/"Rango" (ES) o "Grade" (EN).
                          * `cargo`: "Cargo" (ES) o "Service" (EN).
                        - Si no hay valor visible, usa "".

                        **OBSERVACIONES GENERALES:**
                        - Extrae "17. OBSERVACIONES DEL ODMC REMITENTE". Si no hay, usa "".

                        **IMPORTANTE:**
                        - NO extraigas la tabla de artículos aquí. Deja "articulos", "accesorios", "equipos_prueba" como listas vacías [].
                        - NO inventes datos. Si no ves algo, usa "".
                        - JSON válido, sin texto adicional.

                        El JSON de salida debe tener al menos esta estructura:
                        {
                          "cabecera": {
                            "tipo_transaccion": "String (valores posibles: 'transferencia', 'inventario', 'destruccion', 'recibo_en_mano', 'otro')",
                            "numero_registro_salida": "String",
                            "fecha_informe": "String (YYYY-MM-DD o DD-MM-YYYY)",
                            "numero_registro_entrada": "String",
                            "fecha_transaccion": "String (YYYY-MM-DD o DD-MM-YYYY)",
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
                        Extrae SOLO las tablas de inventario del documento AC-21.

                        **REGLAS FUNDAMENTALES (OBLIGATORIAS):**
                        1. NO inventes datos. Si un campo está vacío o no es visible, usa "" (cadena vacía).
                        2. NO omitas información. Extrae TODO lo que veas, sin excepciones.
                        3. NO asumas valores. Si no ves un número, no pongas "1" por defecto.
                        4. **CC**: Para CADA fila debes leer la celda de la columna "12. CC"/"12. ALC" y asignar su valor a `cc` (o "" si vacía). Un valor CC por fila; no omitas la columna en ninguna fila. No inventes ni copies de otra fila.

                        **PROCESO DE EXTRACCIÓN:**

                        **PASO 1 - CONTAR Y VERIFICAR FILAS:**
                        - Cuenta EXACTAMENTE cuántas filas de datos hay en la tabla (excluyendo cabeceras).
                        - Rango típico: 1-35 filas. Si ves más de 35, verifica que no estés contando cabeceras/pie.
                        - Anota: N = número de filas contadas.
                        - **CRÍTICO - NO INVENTAR FILAS**: 
                          * SOLO extrae filas que REALMENTE VES en el documento.
                          * NO inventes filas que no existen en el documento.
                          * NO dupliques filas (cada `indice_fila` debe aparecer UNA SOLA VEZ).
                          * Si el documento tiene filas 31, 32, 33, 35, 36... (NO hay fila 44), NO extraigas una fila 44.
                          * Si el documento tiene filas 31, 32, 33, 35, 36... (NO hay fila 34), NO extraigas una fila 34.
                          * **REGLA DE ORO**: Si NO ves la fila en el documento, NO la extraigas.
                        - **CRÍTICO - VERIFICAR CONTINUIDAD**: Después de extraer, verifica que los `indice_fila` extraídos no tengan saltos dentro del rango visible. Si extraes filas con índices 31, 32, 34, 35... (falta la 33), eso es un ERROR - debes revisar la imagen y extraer la fila faltante. PERO si el documento NO tiene la fila 33 visible, NO la inventes.

                        **PASO 2 - EXTRAER ARTÍCULOS:**
                        - Extrae EXACTAMENTE N elementos (una fila = un elemento).
                        - Orden: según el orden en que aparecen en el documento (puede tener saltos en numeración).
                        - **CRÍTICO - NO INVENTAR FILAS**: 
                          * SOLO extrae filas que REALMENTE VES en el documento.
                          * NO inventes filas que no existen.
                          * NO dupliques filas (cada `indice_fila` debe ser ÚNICO).
                          * Si el documento muestra filas 31, 32, 33, 35, 36... y NO hay fila 44 visible, NO extraigas una fila 44.
                          * **ANTES DE EXTRAER CADA FILA**: Verifica en la imagen que esa fila REALMENTE existe en el documento.
                        - **CRÍTICO - NO OMITIR FILAS**: 
                          * Debes extraer TODAS las filas visibles en la tabla, sin excepciones.
                          * Si ves una fila en el documento, DEBES extraerla, aunque parezca similar a otra.
                          * NO omitas filas porque tengan el mismo código_producto o contenido similar.
                        - **CRÍTICO - VALIDACIÓN DE CONTENIDO**: 
                          * Para cada fila extraída, verifica que el contenido (código_producto, observaciones, cantidad, numero_serie, cc) coincide EXACTAMENTE con lo que aparece en esa fila del documento original.
                          * Compara mentalmente cada campo extraído con lo que ves en la imagen. Si hay discrepancia, revisa la imagen y corrige.
                          * Asegúrate de que el código_producto, observaciones, cantidad, numero_serie y cc de cada fila extraída corresponden a la misma fila del documento.
                        - Para cada fila, extrae estos campos de sus columnas correspondientes:

                          * `indice_fila`: **OBLIGATORIO - EXTRAE el número que aparece en la PRIMERA COLUMNA de la tabla del documento** (puede ser 1, 2, 3, 4, 5, etc.). 
                            - **CRÍTICO**: Este campo es OBLIGATORIO. SIEMPRE debe tener un valor.
                            - Si el documento tiene saltos (ej: 1, 2, 5, 6...), respeta esos saltos EXACTAMENTE.
                            - Si la primera columna NO tiene número visible, debes reportar esto explícitamente usando `null` o `0`, pero NUNCA inventes un número secuencial.
                            - El `indice_fila` debe reflejar el número REAL del documento, no forzar secuencia.
                            - **NO asignes números secuenciales automáticamente si no ves el número en el documento.**

                          * `codigo_producto`: Valor de columna "TÍTULO CORTO / EDICIÓN" (ES) o "SHORT TITLE / EDITION" (EN).
                            - NO uses el valor de "OBSERVACIONES/REMARKS" aquí.
                            - Si está vacío, usa "".

                          * `observaciones`: **CRÍTICO** - Valor de columna "OBSERVACIONES" (ES) o "REMARKS" (EN).
                            - **EXTRAE TODO el texto de la celda** (negrita + normal, todas las líneas, todo el contenido visible, sin omitir nada).
                            - **NO omitas texto** - si hay texto en la celda, debe aparecer completo en `observaciones`.
                            - **REGLA DE DUPLICACIÓN (SOLO SI ES EXACTAMENTE IGUAL)**: Si el texto de OBSERVACIONES/REMARKS es EXACTAMENTE igual (carácter por carácter) al texto de `codigo_producto`, entonces usa "" (cadena vacía). Si hay CUALQUIER diferencia, incluso mínima, incluye el texto completo.
                            - Si la celda está completamente vacía, usa "".
                            - **IMPORTANTE**: Incluye TODO el texto de la celda OBSERVACIONES/REMARKS, sin filtrar ni omitir partes. Solo omite si es EXACTAMENTE igual al título corto.

                          * `cantidad`: Número entero de columna "CANTIDAD".
                            - Si está vacío o no es visible, usa 1 (mínimo permitido).

                          * `numero_serie_inicio`: Valor de columna "NÚMERO DE SERIE - INICIO".
                            - Si está vacío, usa "".

                          * `numero_serie_fin`: Valor de columna "NÚMERO DE SERIE - FIN".
                            - Si está vacío, usa "".

                          * `cc`: **OBLIGATORIO POR FILA - LEE LA COLUMNA CC/ALC EN CADA FILA**
                            - Localiza la columna "12. CC" (ES) o "12. ALC" (EN) en la cabecera de la tabla.
                            - **Para CADA fila que extraigas debes leer explícitamente la celda de ESA fila en la columna CC/ALC.** No omitas la columna CC en ninguna fila. Si hay 20 artículos, debes haber leído 20 celdas CC (una por fila).
                            - Contenido a extraer: si en la celda hay un número o código visible ("1", "2", "3", "C", "1A", etc.), ponlo como string; si hay número con marcas ("1 ☑"), extrae solo el número; si la celda está vacía o solo tiene símbolos/círculos sin dígito, usa "".
                            - **PROHIBIDO:** NO inventes. NO copies el valor de otra fila. Cada fila tiene su propia celda; léela.
                            - Si la columna CC/ALC no existe en la cabecera, usa "" en todas las filas.

                        **PASO 3 - VALIDAR ANTES DE RESPONDER:**
                        - Verifica: `len(articulos) == N` (número contado en PASO 1).
                        - Si hay discrepancia, REVISA y corrige.
                        - **CRÍTICO - VALIDAR DUPLICADOS**: 
                          * Verifica que NO hay `indice_fila` duplicados en los artículos extraídos.
                          * Cada `indice_fila` debe aparecer UNA SOLA VEZ.
                          * Si encuentras duplicados (ej: dos artículos con `indice_fila: 44`), REVISA la imagen y elimina el duplicado incorrecto.
                          * **REGLA**: Si el documento NO muestra una fila con un número específico, NO debes tener un artículo con ese `indice_fila`.
                        - **VALIDACIÓN DE CONTENIDO FINAL**: 
                          * Revisa mentalmente cada artículo extraído y compara con la imagen del documento.
                          * Verifica que el contenido de cada fila (código_producto, observaciones, cantidad, numero_serie, cc) coincide EXACTAMENTE con lo que aparece en esa fila del documento.
                          * **CRÍTICO**: Verifica que `observaciones` contiene TODO el texto de la columna OBSERVACIONES/REMARKS, sin omitir nada (excepto si es exactamente igual al título corto).
                          * **VALIDACIÓN DE CC (OBLIGATORIA)**: Debe haber exactamente un valor `cc` por artículo (uno por fila). Recorre mentalmente cada fila y confirma que has leído la celda de la columna 12 para esa fila. Si falta `cc` en algún artículo, vuelve a la imagen y asígnale el valor de esa celda (o "" si está vacía).
                          * Si detectas alguna discrepancia, revisa la imagen y corrige antes de responder.
                        - **VALIDACIÓN DE ÍNDICES Y CONTINUIDAD**: 
                          * Los `indice_fila` deben reflejar los números de la primera columna del documento.
                          * **CRÍTICO - DETECCIÓN DE SALTOS EN EL RANGO VISIBLE**: 
                            * Extrae todos los `indice_fila` de los artículos extraídos.
                            * Calcula el rango: min_indice = mínimo `indice_fila`, max_indice = máximo `indice_fila`.
                            * **VERIFICAR SALTOS**: Revisa la imagen del documento y verifica si los saltos en `indice_fila` son del documento original o si omitiste una fila:
                              * Si el documento original muestra un salto (ej: tiene filas 31, 32, 33, 35... y NO hay fila 34 visible en el documento), entonces el salto es VÁLIDO - respétalo.
                              * Si el documento original tiene una fila visible que NO extrajiste (ej: el documento muestra fila 33 pero tú no la extrajiste), entonces es un ERROR - debes extraerla.
                            * **IMPORTANTE**: Antes de reportar un salto como válido, VERIFICA en la imagen que realmente no existe esa fila en el documento. Si ves una fila en el documento pero no la extrajiste, es un ERROR y debes corregirlo.
                            * Si el documento tiene secuencia continua pero tú extrajiste con saltos, es un ERROR - debes extraer todas las filas visibles.
                          * **SEPARACIÓN DE CAMPOS**: El campo `cc` se extrae de la columna CC/ALC; extrae exactamente lo que aparece en cada celda. Si la primera columna no tiene número visible, usa secuencia (1, 2, 3...) SOLO para `indice_fila`.

                        **ACCESORIOS y EQUIPOS DE PRUEBA (OBLIGATORIO EXTRAER SI ESTÁN EN LA IMAGEN):**
                        - Estas secciones suelen estar **DEBAJO** de la tabla principal de artículos.
                        - **ACCESORIOS:** Busca "ACCESORIOS ENTREGADOS CON CADA EQUIPO" (ES) o similar. Tabla con descripción y cantidad. Extrae cada fila como { "descripcion": "...", "cantidad": N }. Si no hay sección o está vacía, devuelve [].
                        - **EQUIPOS DE PRUEBA:** Busca cualquier etiqueta/título que indique equipos de prueba: "PRUEBAS AICOX", "EQUIPOS PRUEBAS AICOX", "EQUIPOS DE PRUEBA", "TEST EQUIPMENT" (EN), etc. El valor puede aparecer de **dos formas**:
                          * **(A) UNA SOLA LÍNEA (muy común):** El título/cabecera (ej. "PRUEBAS AICOX") va seguido del **código o valor** en la misma línea o en la línea siguiente. Ejemplo: "PRUEBAS AICOX" y a su derecha o debajo un valor como "ATQH 54" o "XYZ 123". En ese caso extrae ESE valor como **un único** elemento: equipos_prueba = [ { "codigo": "ATQH 54" } ]. No confundas el título con el código: el código es el valor que acompaña al título, no el texto "PRUEBAS AICOX".
                          * **(B) TABLA CON VARIAS FILAS:** Si hay una tabla de una columna con varios códigos (una fila por equipo), extrae cada fila como { "codigo": "valor" }; devuelve un elemento por fila.
                        - Si ves la etiqueta de equipos de prueba pero no hay ningún valor/código junto a ella, devuelve []. Si hay al menos un valor (en formato línea única o en tabla), inclúyelo en equipos_prueba. No omitas esta sección por estar al final del documento.

                        **FORMATO JSON:**
                        - Un único objeto JSON válido, sin texto adicional.
                        - Campos de texto vacíos = "" (no null, no undefined).
                        - **CRÍTICO - OBLIGATORIO**: `indice_fila` debe reflejar el número de la PRIMERA COLUMNA del documento. Si el documento tiene saltos (ej: 1, 2, 5, 6...), respétalos EXACTAMENTE. Si la primera columna NO tiene número visible, reporta `null` o `0`, pero NUNCA inventes un número secuencial. Este campo es OBLIGATORIO y debe estar presente en TODOS los artículos.
                        - Estructura:
                        {
                          "articulos": [
                            { "indice_fila": 1, "codigo_producto": "...", "observaciones": "...", "cantidad": 1, "numero_serie_inicio": "...", "numero_serie_fin": "...", "cc": "" },
                            { "indice_fila": 2, "codigo_producto": "...", "observaciones": "...", "cantidad": 1, "numero_serie_inicio": "...", "numero_serie_fin": "...", "cc": "" },
                            { "indice_fila": 5, "codigo_producto": "...", "observaciones": "...", "cantidad": 1, "numero_serie_inicio": "...", "numero_serie_fin": "...", "cc": "" },
                            ...
                          ],
                          "accesorios": [ { "descripcion": "...", "cantidad": 1 } ],
                          "equipos_prueba": [ { "codigo": "..." } ]
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
                max_tokens=2500,  # Tokens para reparación de JSON
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

    def _validate_extraction(self, image_bytes: bytes, extracted_data: Dict) -> Optional[Dict]:
        """
        Valida que el número de artículos extraídos es razonable comparado con la imagen.
        Retorna información de validación o None si no se puede validar.
        """
        if Image is None:
            return None
        
        try:
            extracted_count = len(extracted_data.get('articulos', []))
            
            # Estimación simple: contar líneas horizontales densas en la zona de tabla
            # Esto es una aproximación, no un conteo exacto
            # Los documentos AC21 típicamente tienen entre 1 y 35 líneas de inventario
            img = Image.open(BytesIO(image_bytes)).convert("L")
            width, height = img.size
            
            # Analizar densidad de líneas horizontales (las filas de tabla tienen más contenido)
            row_densities = []
            for y in range(0, height, 10):  # Muestrear cada 10px
                row = img.crop((0, y, width, min(y + 10, height)))
                from PIL import ImageStat
                stat = ImageStat.Stat(row)
                # Mayor desviación = más contenido (texto, bordes)
                row_densities.append(stat.stddev[0])
            
            if not row_densities:
                return None
            
            # Contar "picos" de densidad (cada pico = posible fila de tabla)
            threshold = sorted(row_densities)[int(len(row_densities) * 0.60)]  # Percentil 60
            peaks = 0
            in_peak = False
            
            for density in row_densities:
                if density > threshold:
                    if not in_peak:
                        peaks += 1
                        in_peak = True
                else:
                    in_peak = False
            
            estimated_visible_rows = max(peaks - 1, 0)  # Restar 1 por la cabecera
            # Limitar estimación a rango razonable (1-40 líneas, considerando margen)
            estimated_visible_rows = min(estimated_visible_rows, 40)
            discrepancy = estimated_visible_rows - extracted_count
            
            validation_info = {
                "extracted_count": extracted_count,
                "estimated_visible_rows": estimated_visible_rows,
                "discrepancy": discrepancy,
                "is_reasonable": abs(discrepancy) <= 2,  # Tolerancia de ±2 filas
                "needs_review": abs(discrepancy) > 5,  # Si faltan más de 5, necesita revisión
                "expected_range": "1-35 líneas típicas en documentos AC21",
                "within_expected_range": 1 <= extracted_count <= 40  # Rango esperado con margen
            }
            
            return validation_info
            
        except Exception as e:
            print(f"⚠️ [VALIDATION] Error en validación: {str(e)}")
            return None
    
    def _get_openai_client(self):
        return OpenAI(api_key=self.api_key)