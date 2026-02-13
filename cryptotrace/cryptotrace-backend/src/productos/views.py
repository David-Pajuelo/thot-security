import logging
import requests
from rest_framework import viewsets, status
from django.db.models import OuterRef, Exists, Count, Subquery, Value, Sum
from django.db.models.functions import Coalesce
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import HttpResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .models import (
    CatalogoProducto, Albaran, MovimientoProducto, TipoProducto, LineaTemporalProducto, InventarioProducto, Empresa, Cryptocustodio, UserProfile
)
from .serializers import (
    CatalogoProductoSerializer, AlbaranSerializer, MovimientoProductoSerializer,
    TipoProductoSerializer, LineaTemporalProductoSerializer, InventarioProductoSerializer,
    EmpresaSerializer, CryptocustodioSerializer, MovimientoProductoBasicoSerializer, CustomTokenObtainPairSerializer, UserProfileSerializer
)
from django.db import models
import json

# Configurar logger
logger = logging.getLogger(__name__)

# 🔹 Vista personalizada para JWT con información de usuario (sin throttling para permitir login)
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para generar tokens JWT con información adicional del usuario.
    throttle_classes = [] para evitar 429 en login (AnonRateThrottle en prod).
    """
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = []


class CustomTokenRefreshView(TokenRefreshView):
    """Refresh token sin throttling para no bloquear sesiones válidas."""
    throttle_classes = []

# 🔹 ModelViewSets para los modelos principales
class TipoProductoViewSet(viewsets.ModelViewSet):
    queryset = TipoProducto.objects.all()
    serializer_class = TipoProductoSerializer

class CatalogoProductoViewSet(viewsets.ModelViewSet):
    queryset = CatalogoProducto.objects.all()
    serializer_class = CatalogoProductoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Personalizar queryset para soportar filtros personalizados
        """
        queryset = super().get_queryset()
        
        # Soporte para codigo_producto (búsqueda exacta)
        codigo_producto = self.request.query_params.get('codigo_producto', None)
        if codigo_producto:
            queryset = queryset.filter(codigo_producto=codigo_producto)
        
        # Soporte para codigo_producto__in (lista separada por comas)
        codigo_producto_in = self.request.query_params.get('codigo_producto__in', None)
        if codigo_producto_in:
            # Dividir por comas y limpiar espacios
            codigos = [c.strip() for c in codigo_producto_in.split(',') if c.strip()]
            if codigos:
                queryset = queryset.filter(codigo_producto__in=codigos)
        
        return queryset
    
    @action(detail=False, methods=['get'], url_path='productos-sin-tipo', permission_classes=[IsAuthenticated])
    def productos_sin_tipo(self, request):
        """
        Obtiene productos del catálogo que no tienen tipo asignado
        """
        try:
            productos_sin_tipo = CatalogoProducto.objects.filter(tipo__isnull=True).order_by('-ultima_actualizacion')
            
            # Agregar información de movimientos para cada producto
            productos_data = []
            for producto in productos_sin_tipo:
                movimientos_count = MovimientoProducto.objects.filter(producto=producto).count()
                
                productos_data.append({
                    'id': producto.id,
                    'codigo_producto': producto.codigo_producto,
                    'descripcion': producto.descripcion,
                    'ultima_actualizacion': producto.ultima_actualizacion,
                    'movimientos_count': movimientos_count,
                    'es_huerfano': movimientos_count == 0  # Sin movimientos = huérfano
                })
            
            return Response({
                'productos': productos_data,
                'total': len(productos_data),
                'huerfanos': len([p for p in productos_data if p['es_huerfano']]),
                'con_movimientos': len([p for p in productos_data if not p['es_huerfano']])
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ Error obteniendo productos sin tipo: {str(e)}")
            return Response(
                {"error": "Error obteniendo productos sin tipo"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='limpiar-huerfanos', permission_classes=[IsAuthenticated])
    def limpiar_huerfanos(self, request):
        """
        Elimina productos del catálogo que no tienen tipo asignado y no tienen movimientos
        """
        try:
            # Buscar productos huérfanos (sin tipo y sin movimientos)
            productos_huerfanos = CatalogoProducto.objects.filter(tipo__isnull=True)
            
            productos_a_eliminar = []
            for producto in productos_huerfanos:
                movimientos_count = MovimientoProducto.objects.filter(producto=producto).count()
                if movimientos_count == 0:
                    productos_a_eliminar.append({
                        'id': producto.id,
                        'codigo': producto.codigo_producto,
                        'descripcion': producto.descripcion
                    })
            
            # Confirmación desde el frontend
            confirmacion = request.data.get('confirmar', False)
            
            if not confirmacion:
                return Response({
                    'productos_a_eliminar': productos_a_eliminar,
                    'total': len(productos_a_eliminar),
                    'mensaje': 'Se encontraron productos huérfanos para eliminar. Confirma la operación.',
                    'requiere_confirmacion': True
                }, status=status.HTTP_200_OK)
            
            # Proceder con la eliminación
            ids_eliminados = [p['id'] for p in productos_a_eliminar]
            eliminados = CatalogoProducto.objects.filter(
                id__in=ids_eliminados,
                tipo__isnull=True
            ).delete()
            
            print(f"✅ [BACKEND] Eliminados {eliminados[0]} productos huérfanos: {[p['codigo'] for p in productos_a_eliminar]}")
            
            return Response({
                'success': True,
                'eliminados': eliminados[0],
                'productos_eliminados': productos_a_eliminar,
                'mensaje': f'Se eliminaron {eliminados[0]} productos huérfanos del catálogo'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ Error limpiando productos huérfanos: {str(e)}")
            return Response(
                {"error": "Error limpiando productos huérfanos"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='asignar-tipo-automatico', permission_classes=[IsAuthenticated])
    def asignar_tipo_automatico(self, request):
        """
        Intenta asignar tipos automáticamente basándose en patrones de código y descripción
        """
        try:
            # Obtener productos sin tipo
            productos_sin_tipo = CatalogoProducto.objects.filter(tipo__isnull=True)
            
            # Obtener todos los tipos disponibles
            tipos_disponibles = TipoProducto.objects.all()
            
            asignaciones_sugeridas = []
            asignaciones_realizadas = []
            
            for producto in productos_sin_tipo:
                tipo_sugerido = None
                razon = ""
                
                # Buscar productos similares con tipo asignado
                for tipo in tipos_disponibles:
                    productos_del_tipo = CatalogoProducto.objects.filter(tipo=tipo)
                    
                    for prod_existente in productos_del_tipo:
                        # Comparar por patrones en código
                        if self._productos_similares_por_codigo(producto.codigo_producto, prod_existente.codigo_producto):
                            tipo_sugerido = tipo
                            razon = f"Código similar a '{prod_existente.codigo_producto}'"
                            break
                        
                        # Comparar por palabras clave en descripción
                        if self._productos_similares_por_descripcion(producto.descripcion, prod_existente.descripcion):
                            tipo_sugerido = tipo
                            razon = f"Descripción similar a '{prod_existente.descripcion}'"
                            break
                    
                    if tipo_sugerido:
                        break
                
                if tipo_sugerido:
                    asignaciones_sugeridas.append({
                        'producto_id': producto.id,
                        'codigo': producto.codigo_producto,
                        'descripcion': producto.descripcion,
                        'tipo_sugerido_id': tipo_sugerido.id,
                        'tipo_sugerido_nombre': tipo_sugerido.nombre,
                        'razon': razon
                    })
            
            # Si se envía confirmación, aplicar las asignaciones
            aplicar = request.data.get('aplicar', False)
            asignaciones_a_aplicar = request.data.get('asignaciones', [])
            
            if aplicar and asignaciones_a_aplicar:
                for asignacion in asignaciones_a_aplicar:
                    try:
                        producto = CatalogoProducto.objects.get(id=asignacion['producto_id'])
                        tipo = TipoProducto.objects.get(id=asignacion['tipo_id'])
                        producto.tipo = tipo
                        producto.save()
                        
                        asignaciones_realizadas.append({
                            'codigo': producto.codigo_producto,
                            'tipo': tipo.nombre
                        })
                        
                        print(f"✅ [BACKEND] Asignado tipo '{tipo.nombre}' a producto '{producto.codigo_producto}'")
                        
                    except (CatalogoProducto.DoesNotExist, TipoProducto.DoesNotExist) as e:
                        print(f"❌ Error asignando tipo: {str(e)}")
                        continue
                
                return Response({
                    'success': True,
                    'asignaciones_realizadas': asignaciones_realizadas,
                    'total_asignadas': len(asignaciones_realizadas),
                    'mensaje': f'Se asignaron tipos a {len(asignaciones_realizadas)} productos'
                }, status=status.HTTP_200_OK)
            
            return Response({
                'asignaciones_sugeridas': asignaciones_sugeridas,
                'total_sugerencias': len(asignaciones_sugeridas),
                'mensaje': 'Asignaciones automáticas sugeridas. Confirma para aplicar.',
                'requiere_confirmacion': True
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ Error en asignación automática: {str(e)}")
            return Response(
                {"error": "Error en asignación automática de tipos"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _productos_similares_por_codigo(self, codigo1, codigo2):
        """
        Determina si dos códigos de producto son similares
        """
        # Remover espacios y convertir a mayúsculas
        c1 = codigo1.replace(' ', '').replace('-', '').upper()
        c2 = codigo2.replace(' ', '').replace('-', '').upper()
        
        # Si comparten prefijo de 4+ caracteres
        if len(c1) >= 4 and len(c2) >= 4 and c1[:4] == c2[:4]:
            return True
        
        # Si comparten 70% de caracteres
        if len(c1) > 0 and len(c2) > 0:
            coincidencias = sum(a == b for a, b in zip(c1, c2))
            similitud = coincidencias / max(len(c1), len(c2))
            return similitud >= 0.7
        
        return False

    def _productos_similares_por_descripcion(self, desc1, desc2):
        """
        Determina si dos descripciones son similares
        """
        if not desc1 or not desc2:
            return False
        
        # Convertir a minúsculas y dividir en palabras
        palabras1 = set(desc1.lower().split())
        palabras2 = set(desc2.lower().split())
        
        # Si comparten palabras clave significativas (3+ caracteres)
        palabras1_significativas = {p for p in palabras1 if len(p) >= 3}
        palabras2_significativas = {p for p in palabras2 if len(p) >= 3}
        
        if palabras1_significativas and palabras2_significativas:
            interseccion = palabras1_significativas.intersection(palabras2_significativas)
            similitud = len(interseccion) / max(len(palabras1_significativas), len(palabras2_significativas))
            return similitud >= 0.3  # 30% de palabras en común
        
        return False

class AlbaranViewSet(viewsets.ModelViewSet):
    queryset = Albaran.objects.all()
    serializer_class = AlbaranSerializer
    search_fields = ['numero', 'empresa_origen__nombre', 'empresa_destino__nombre', 'productos__producto__codigo_producto', 'productos__numero_serie']
    ordering_fields = ['fecha', 'numero', 'empresa_origen__nombre', 'empresa_destino__nombre']
    
    def get_queryset(self):
        """
        Personalizar queryset para soportar búsqueda por numero_registro
        """
        queryset = super().get_queryset()
        numero_registro = self.request.query_params.get('numero_registro', None)
        
        if numero_registro:
            # Buscar por numero_registro_entrada o numero_registro_salida
            queryset = queryset.filter(
                models.Q(numero_registro_entrada=numero_registro) | 
                models.Q(numero_registro_salida=numero_registro)
            )
        
        return queryset

    def create(self, request, *args, **kwargs):
        print(f"DEBUG AC21: request.data={request.data}")
        print(f"DEBUG AC21: request.content_type={request.content_type}")
        
        # Manejar FormData (cuando se envía imagen)
        parsed_data = request.data
        if 'multipart/form-data' in request.content_type:
            print("🖼️ [BACKEND] Recibiendo FormData con imagen")
            # Extraer imagen del FormData
            imagen_documento = request.FILES.get('imagen_documento')
            if imagen_documento:
                print(f"🖼️ [BACKEND] Imagen recibida: {imagen_documento.name}, {imagen_documento.size} bytes")
            
            # Extraer datos JSON del FormData
            data_str = request.data.get('data')
            if data_str:
                import json
                try:
                    # Parsear el JSON string
                    if isinstance(data_str, str):
                        parsed_data = json.loads(data_str)
                    else:
                        parsed_data = data_str
                    print(f"✅ [BACKEND] Datos parseados desde FormData")
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"❌ [BACKEND] Error parseando JSON de FormData: {e}")
                    return Response({"error": f"Error parseando datos JSON: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                print("⚠️ [BACKEND] No se encontró campo 'data' en FormData, usando request.data directamente")
                parsed_data = request.data
        
        # Usar parsed_data si es dict, sino usar request.data
        data_source = parsed_data if isinstance(parsed_data, dict) else request.data
        cabecera = data_source.get('cabecera', {})
        
        # Asegurar que cabecera sea un dict (puede venir como string JSON desde FormData)
        if isinstance(cabecera, str):
            import json
            try:
                cabecera = json.loads(cabecera)
            except (json.JSONDecodeError, TypeError):
                cabecera = {}
        elif not isinstance(cabecera, dict):
            cabecera = {}
        
        def get_first_nonempty(*args):
            for v in args:
                if v is not None and str(v).strip() != '':
                    return v
            return None
        numero = get_first_nonempty(
            data_source.get('numero'),
            data_source.get('numero_registro_entrada'),
            data_source.get('numero_registro_salida'),
            cabecera.get('numero'),
            cabecera.get('numero_registro_entrada'),
            cabecera.get('numero_registro_salida')
        )
        print(f"DEBUG AC21: numero extraído (robusto)={numero}")
        if not numero:
            return Response({'error': 'No se encontró número de registro en el AC21. El payload debe incluir un campo "numero_registro_salida" o equivalente.'}, status=status.HTTP_400_BAD_REQUEST)
        # Si el frontend pide agregar productos a un albarán existente
        if data_source.get('modo') == 'agregar_a_existente':
            # Usar el mismo método que en encontrar_documento_existente para consistencia
            albaran = Albaran.encontrar_documento_existente(numero)
            if not albaran:
                return Response({'error': 'No existe un albarán con ese número'}, status=status.HTTP_404_NOT_FOUND)
            articulos = data_source.get('articulos', [])
            nuevos = 0
            for articulo in articulos:
                codigo = articulo.get('codigo')
                numero_serie = articulo.get('numero_serie')
                if not codigo or not numero_serie:
                    continue
                producto_catalogo, created = CatalogoProducto.objects.get_or_create(
                    codigo_producto=codigo,
                    defaults={"descripcion": articulo.get('descripcion', '')}
                )
                
                if created:
                    print(f"⚠️ [BACKEND] Producto creado automáticamente sin tipo (agregar_a_existente): {codigo} - {articulo.get('descripcion', '')}")
                existe = MovimientoProducto.objects.filter(
                    albaran=albaran,
                    producto=producto_catalogo,
                    numero_serie=numero_serie
                ).exists()
                if existe:
                    continue
                tipo_movimiento_valido = albaran.tipo_documento or 'INVENTARIO'
                if 'tipo_movimiento' in articulo and articulo['tipo_movimiento']:
                    tipo_articulo = str(articulo['tipo_movimiento']).upper()
                    opciones_validas = [k for k, _ in Albaran.TIPO_DOCUMENTO_CHOICES]
                    if tipo_articulo in opciones_validas:
                        tipo_movimiento_valido = tipo_articulo
                if not tipo_movimiento_valido:
                    tipo_movimiento_valido = 'INVENTARIO'
                MovimientoProducto.objects.create(
                    albaran=albaran,
                    producto=producto_catalogo,
                    numero_serie=numero_serie,
                    tipo_movimiento=tipo_movimiento_valido,
                    estado_anterior='inactivo',
                    estado_nuevo='activo'
                )
                nuevos += 1
            serializer = self.get_serializer(albaran)
            return Response({"success": True, "data": serializer.data, "nuevos": nuevos}, status=status.HTTP_200_OK)
        # --- Nueva lógica: bloquear alta directa de AC21 DE ENTRADA (no salida) ---
        # PERO permitir modo 'agregar_a_existente' que solo agrega productos a un albarán existente
        modo = data_source.get('modo')
        if modo == 'agregar_a_existente':
            # Este modo ya se maneja arriba, no bloquear
            pass
        else:
            tipo_documento = data_source.get('tipo_documento') or cabecera.get('tipo_transaccion')
            direccion_transferencia = data_source.get('direccion_transferencia', 'ENTRADA')
            
            # Normalizar tipo_documento para comparación
            tipo_documento_normalizado = None
            if tipo_documento:
                tipo_documento_str = str(tipo_documento).upper().replace(' ', '_')
                # Mapear variaciones comunes
                tipo_map = {
                    'RECIBO_EN_MANO': 'RECIBO_MANO',
                    'RECIBO EN MANO': 'RECIBO_MANO',
                    'RECIBOENMANO': 'RECIBO_MANO',
                }
                tipo_documento_normalizado = tipo_map.get(tipo_documento_str, tipo_documento_str)
            
            print(f"🔍 [BACKEND] Validación AC21 - tipo_documento: '{tipo_documento}' -> normalizado: '{tipo_documento_normalizado}', direccion: '{direccion_transferencia}'")
            
            # Solo bloquear AC21s de ENTRADA - las SALIDAS pueden crearse directamente
            if (tipo_documento_normalizado and tipo_documento_normalizado in ['TRANSFERENCIA', 'RECIBO_MANO', 'DESTRUCCION', 'OTRO'] 
                and direccion_transferencia == 'ENTRADA'):
                print(f"🚫 [BACKEND] Bloqueando creación directa de AC21 ENTRADA - debe usar flujo temporal")
                return Response({
                    'error': 'El alta de AC21 debe realizarse a través de la gestión temporal (línea temporal) para tipificación de productos. Sube el AC21, valida los artículos y continúa el flujo en la gestión temporal.'
                }, status=status.HTTP_400_BAD_REQUEST)
        # --- Fin bloqueo ---
        # Verificar si existe un albarán con el mismo número de registro (entrada o salida)
        # Usar el mismo método que en encontrar_documento_existente para consistencia
        albaran_existente = Albaran.encontrar_documento_existente(numero)
        if albaran_existente:
            movimientos = MovimientoProducto.objects.filter(albaran=albaran_existente)
            productos_existentes = MovimientoProductoBasicoSerializer(movimientos, many=True).data
            return Response({
                "success": False,
                "message": "Ya existe un albarán con este número.",
                "productos_existentes": productos_existentes,
                "albaran_id": albaran_existente.id
            }, status=status.HTTP_409_CONFLICT)
        # Usar parsed_data si es dict, sino usar request.data
        serializer = self.get_serializer(data=parsed_data if isinstance(parsed_data, dict) else request.data)
        if not serializer.is_valid():
            print(f"❌ [BACKEND] Errores de validación del serializer: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        albaran_instance = self.perform_create(serializer, numero)
        response_serializer = self.get_serializer(albaran_instance)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, numero=None):
        try:
            with transaction.atomic():
                TIPO_MAP = {display.lower(): key for key, display in Albaran.TIPO_DOCUMENTO_CHOICES}
                TIPO_MAP.update({key.lower(): key for key, _ in Albaran.TIPO_DOCUMENTO_CHOICES})
                tipo_payload_value = None
                possible_fields = ['tipo_albaran', 'tipo_documento', 'tipo_operacion']
                for field in possible_fields:
                    if field in self.request.data and self.request.data[field]:
                        tipo_payload_value = str(self.request.data[field]).lower()
                        print(f"[AlbaranViewSet.create] Payload para tipo de documento encontrado en '{field}': '{tipo_payload_value}'")
                        break
                tipo_documento_final = TIPO_MAP.get(tipo_payload_value)
                if not tipo_documento_final:
                    tipo_documento_final = serializer.validated_data.get('tipo_documento')
                print(f"[AlbaranViewSet.create] Tipo de documento final determinado: '{tipo_documento_final}'")
                direccion_transferencia_valor = serializer.validated_data.get('direccion_transferencia')
                if not direccion_transferencia_valor and tipo_documento_final in ['TRANSFERENCIA', 'RECIBO_MANO']:
                    direccion_transferencia_valor = 'ENTRADA'
                if not numero:
                    cabecera = self.request.data.get('cabecera', {})
                    numero = get_first_nonempty(
                        self.request.data.get('numero'),
                        self.request.data.get('numero_registro_entrada'),
                        self.request.data.get('numero_registro_salida'),
                        cabecera.get('numero'),
                        cabecera.get('numero_registro_entrada'),
                        cabecera.get('numero_registro_salida')
                    )

                # Verificar si es página adicional
                es_pagina_adicional = self.request.data.get('es_pagina_adicional', False)
                documento_principal_id = self.request.data.get('documento_principal_id')
                documento_principal_ref = None
                nueva_pagina = 1  # Valor por defecto
                
                if es_pagina_adicional and documento_principal_id:
                    try:
                        documento_principal_ref = Albaran.objects.get(id=documento_principal_id)
                        print(f"[AlbaranViewSet] Creando página adicional para documento principal: {documento_principal_ref.numero}")
                        
                        # Generar número con sufijo para la página adicional
                        numero_existente = documento_principal_ref.numero
                        # Usar el mismo método que el modelo para calcular siguiente_pagina
                        from django.db.models import Max
                        max_pagina = documento_principal_ref.obtener_todas_las_paginas().aggregate(
                            max_pagina=Max('pagina_numero')
                        )['max_pagina'] or 0
                        nueva_pagina = max_pagina + 1
                        numero = f"{numero_existente}-P{nueva_pagina}"
                        
                        print(f"[AlbaranViewSet] Número generado para página adicional: {numero}, Max página: {max_pagina}, Nueva: {nueva_pagina}")
                    except Albaran.DoesNotExist:
                        print(f"[AlbaranViewSet] Error: Documento principal {documento_principal_id} no encontrado")
                        documento_principal_ref = None

                albaran = serializer.save(
                    numero=numero,
                    created_by=self.request.user,
                    updated_by=self.request.user,
                    tipo_documento=tipo_documento_final,
                    direccion_transferencia=direccion_transferencia_valor,
                    documento_principal=documento_principal_ref,
                    pagina_numero=nueva_pagina if es_pagina_adicional and documento_principal_ref else 1
                )
                
                # Si es página adicional, actualizar el total_paginas del documento principal
                if es_pagina_adicional and documento_principal_ref:
                    # Usar el método del modelo para actualizar correctamente
                    documento_principal_ref.actualizar_total_paginas()
                    documento_principal_ref.refresh_from_db()
                    print(f"[AlbaranViewSet] Actualizado total_paginas del documento principal a: {documento_principal_ref.total_paginas}")
                elif not es_pagina_adicional:
                    # Para documentos principales, establecer total_paginas = 1 inicialmente
                    albaran.total_paginas = 1
                    albaran.save()
                articulos = self.request.data.get('articulos', [])
                if (albaran.tipo_documento in ['TRANSFERENCIA', 'RECIBO_MANO', 'DESTRUCCION', 'OTRO'] 
                    and albaran.direccion_transferencia == 'ENTRADA'):
                    # AC21s de ENTRADA van a gestión temporal
                    for articulo in articulos:
                        # Mapear observaciones del OCR a descripcion en BD
                        observaciones_ocr = articulo.get('observaciones') or articulo.get('descripcion', '')
                        LineaTemporalProducto.objects.create(
                            usuario=self.request.user,
                            numero_albaran=albaran.numero,
                            codigo_producto=articulo.get('codigo_producto') or articulo.get('codigo', '') or 'SIN_CODIGO',
                            descripcion=observaciones_ocr,  # Mapeado desde observaciones del OCR
                            numero_serie=articulo.get('numero_serie_inicio') or articulo.get('numero_serie_fin', ''),
                            observaciones=''  # Campo observaciones en BD queda vacío
                        )
                elif (albaran.tipo_documento in ['TRANSFERENCIA', 'RECIBO_MANO', 'DESTRUCCION', 'OTRO'] 
                      and albaran.direccion_transferencia == 'SALIDA'):
                    # AC21s de SALIDA crean movimientos directamente
                    for articulo in articulos:
                        producto_catalogo, created = CatalogoProducto.objects.get_or_create(
                            codigo_producto=articulo.get('codigo'),
                            defaults={"descripcion": articulo.get('descripcion', '')}
                        )
                        
                        if created:
                            print(f"⚠️ [BACKEND] Producto AC21 Salida creado sin tipo: {articulo.get('codigo')} - {articulo.get('descripcion', '')}")
                        
                        # Determinar el estado anterior del producto en el inventario
                        inventario = InventarioProducto.objects.filter(
                            producto=producto_catalogo,
                            numero_serie=articulo.get('numero_serie')
                        ).first()
                        estado_anterior = inventario.estado if inventario else 'inactivo'
                        
                        # Para salidas, el estado nuevo siempre es 'inactivo' (el producto sale de custodia)
                        estado_nuevo = 'inactivo'
                        
                        # Crear el movimiento de producto
                        movimiento = MovimientoProducto.objects.create(
                            albaran=albaran,
                            producto=producto_catalogo,
                            numero_serie=articulo.get('numero_serie'),
                            descripcion=producto_catalogo.descripcion,
                            tipo_movimiento=albaran.tipo_documento,
                            estado_anterior=estado_anterior,
                            estado_nuevo=estado_nuevo,
                            cantidad=articulo.get('cantidad', 1),
                            observaciones=articulo.get('observaciones', '')
                        )
                        
                        # Actualizar el inventario del producto
                        if inventario:
                            inventario.estado = estado_nuevo
                            inventario.ultimo_movimiento = movimiento
                            inventario.ultima_actualizacion = timezone.now()
                            inventario.save()
                else:
                    for articulo in articulos:
                        producto_catalogo, created = CatalogoProducto.objects.get_or_create(
                            codigo_producto=articulo.get('codigo'),
                            defaults={"descripcion": articulo.get('descripcion', '')}
                        )
                        
                        if created:
                            print(f"⚠️ [BACKEND] Producto creado sin tipo: {articulo.get('codigo')} - {articulo.get('descripcion', '')}")
                        inventario = InventarioProducto.objects.filter(
                            producto=producto_catalogo,
                            numero_serie=articulo.get('numero_serie')
                        ).first()
                        estado_anterior = 'inactivo'
                        if albaran.tipo_documento == 'INVENTARIO':
                            estado_anterior = 'inactivo'
                        elif inventario:
                            estado_anterior = inventario.estado
                        tipo_movimiento_valido = albaran.tipo_documento or 'INVENTARIO'
                        if 'tipo_movimiento' in articulo and articulo['tipo_movimiento']:
                            tipo_articulo = str(articulo['tipo_movimiento']).upper()
                            opciones_validas = [k for k, _ in Albaran.TIPO_DOCUMENTO_CHOICES]
                            if tipo_articulo in opciones_validas:
                                tipo_movimiento_valido = tipo_articulo
                        if not tipo_movimiento_valido:
                            tipo_movimiento_valido = 'INVENTARIO'
                            estado_nuevo = 'activo'
                        if hasattr(albaran, 'direccion_transferencia'):
                            if albaran.direccion_transferencia == 'SALIDA':
                                estado_nuevo = 'inactivo'
                            elif albaran.direccion_transferencia == 'ENTRADA':
                                estado_nuevo = 'activo'
                        movimiento = MovimientoProducto(
                            albaran=albaran,
                            producto=producto_catalogo,
                            numero_serie=articulo.get('numero_serie'),
                            tipo_movimiento=tipo_movimiento_valido,
                            estado_anterior=estado_anterior,
                            estado_nuevo=estado_nuevo
                        )
                        movimiento.save()
                        inventario_producto, created = InventarioProducto.objects.update_or_create(
                            producto=producto_catalogo,
                            numero_serie=articulo.get('numero_serie'),
                            defaults={
                                'estado': estado_nuevo,
                                'ultimo_movimiento': movimiento,
                                'descripcion': articulo.get('descripcion', ''),
                                'ultima_actualizacion': timezone.now()
                            }
                        )
                return albaran
        except Exception as e:
            print(f"❌ Error creando albarán: {str(e)}")
            raise

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        updated_instance = self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        # Re-serializar para obtener los campos de display actualizados
        response_serializer = self.get_serializer(updated_instance)
        return Response(response_serializer.data)

    def perform_update(self, serializer):
        # Guardar los cambios del albarán
        instance = serializer.save(updated_by=self.request.user)
        
        # Procesar actualizaciones de movimientos si se proporcionan
        movimientos_data = self.request.data.get('movimientos')
        if movimientos_data is not None:
            self._actualizar_movimientos(instance, movimientos_data)
        
        return instance
    
    def _actualizar_movimientos(self, albaran, movimientos_data):
        """
        Actualiza los movimientos de un albarán.
        Elimina los existentes y crea los nuevos basándose en los datos recibidos.
        """
        try:
            with transaction.atomic():
                # Obtener movimientos existentes
                movimientos_existentes = MovimientoProducto.objects.filter(albaran=albaran)
                
                # Mapear movimientos por ID para eficiencia
                movimientos_por_id = {mov.id: mov for mov in movimientos_existentes}
                
                # IDs de movimientos que vienen en la actualización
                ids_recibidos = set()
                
                # Procesar cada movimiento en los datos
                for mov_data in movimientos_data:
                    mov_id = mov_data.get('id')
                    
                    if mov_id and mov_id in movimientos_por_id:
                        # Actualizar movimiento existente
                        ids_recibidos.add(mov_id)
                        movimiento = movimientos_por_id[mov_id]
                        
                        # Actualizar campos editables
                        if 'producto_codigo' in mov_data:
                            # Buscar o crear el producto en el catálogo
                            # Intentar preservar el tipo del producto original si se está cambiando código
                            tipo_original = movimiento.producto.tipo if movimiento.producto else None
                            
                            producto, created = CatalogoProducto.objects.get_or_create(
                                codigo_producto=mov_data['producto_codigo'],
                                defaults={
                                    'descripcion': mov_data.get('descripcion', ''),
                                    'tipo': tipo_original  # Preservar tipo original si existe
                                }
                            )
                            
                            # Si el producto ya existía pero no tenía tipo, y tenemos un tipo original, actualizarlo
                            if not created and not producto.tipo and tipo_original:
                                producto.tipo = tipo_original
                                producto.save()
                                
                            movimiento.producto = producto
                        
                        if 'cantidad' in mov_data:
                            movimiento.cantidad = mov_data['cantidad']
                        if 'numero_serie' in mov_data:
                            movimiento.numero_serie = mov_data['numero_serie']
                        if 'cc' in mov_data:
                            # Convertir cadena vacía a None para el campo IntegerField
                            cc_value = mov_data['cc']
                            if cc_value == '' or cc_value is None:
                                movimiento.cc = None
                            else:
                                try:
                                    movimiento.cc = int(cc_value) if cc_value else None
                                except (ValueError, TypeError):
                                    movimiento.cc = None
                        if 'observaciones' in mov_data:
                            movimiento.observaciones = mov_data['observaciones']
                        if 'descripcion' in mov_data:
                            movimiento.descripcion = mov_data['descripcion']
                            
                        movimiento.save()
                        
                    elif not mov_id:  # Nuevo movimiento (id es null)
                        # Crear nuevo movimiento
                        if mov_data.get('producto_codigo'):
                            # Para nuevos movimientos, buscar si existe el código en el catálogo
                            producto, created = CatalogoProducto.objects.get_or_create(
                                codigo_producto=mov_data['producto_codigo'],
                                defaults={'descripcion': mov_data.get('descripcion', '')}
                            )
                            
                            # Normalizar el valor de cc: convertir cadena vacía a None
                            cc_value = mov_data.get('cc')
                            if cc_value == '' or cc_value is None:
                                cc_value = None
                            else:
                                try:
                                    cc_value = int(cc_value) if cc_value else None
                                except (ValueError, TypeError):
                                    cc_value = None
                            
                            MovimientoProducto.objects.create(
                                albaran=albaran,
                                producto=producto,
                                numero_serie=mov_data.get('numero_serie', ''),
                                descripcion=mov_data.get('descripcion', ''),
                                cantidad=mov_data.get('cantidad', 1),
                                cc=cc_value,  # None si está vacío o no es un número válido
                                observaciones=mov_data.get('observaciones', ''),
                                tipo_movimiento=albaran.tipo_documento or 'INVENTARIO',
                                estado_anterior='inactivo',
                                estado_nuevo='activo'
                            )
                
                # Eliminar movimientos que ya no están en los datos recibidos
                movimientos_a_eliminar = movimientos_existentes.exclude(id__in=ids_recibidos)
                movimientos_a_eliminar.delete()
                
                print(f"✅ [BACKEND] Movimientos actualizados para albarán {albaran.id}")
                
        except Exception as e:
            print(f"❌ [BACKEND] Error actualizando movimientos: {str(e)}")
            raise

    @action(detail=True, methods=['get'])
    def movimientos(self, request, pk=None):
        """
        Obtiene los movimientos asociados a un albarán específico.
        """
        try:
            albaran = self.get_object()
            movimientos = MovimientoProducto.objects.filter(albaran=albaran).select_related('producto', 'producto__tipo')
            serializer = MovimientoProductoSerializer(movimientos, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": f"Error obteniendo movimientos: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='agregar-productos', permission_classes=[IsAuthenticated])
    def agregar_productos(self, request, pk=None):
        """
        Endpoint para agregar productos a un albarán existente.
        """
        try:
            # Obtener el albarán existente
            albaran = self.get_object()
            
            articulos = request.data.get('articulos', [])
            if not articulos:
                return Response(
                    {"error": "No se proporcionaron artículos para agregar"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            nuevos = 0
            duplicados = 0
            
            with transaction.atomic():
                for articulo in articulos:
                    codigo = articulo.get('codigo')
                    numero_serie = articulo.get('numero_serie')
                    
                    if not codigo or not numero_serie:
                        continue
                    
                    # Crear o obtener el producto del catálogo
                    producto_catalogo, created = CatalogoProducto.objects.get_or_create(
                        codigo_producto=codigo,
                        defaults={"descripcion": articulo.get('descripcion', '')}
                    )
                    
                    if created:
                        print(f"⚠️ [BACKEND] Producto creado automáticamente sin tipo: {codigo} - {articulo.get('descripcion', '')}")
                    
                    # Verificar si ya existe este producto en el albarán
                    existe = MovimientoProducto.objects.filter(
                        albaran=albaran,
                        producto=producto_catalogo,
                        numero_serie=numero_serie
                    ).exists()
                    
                    if existe:
                        duplicados += 1
                        continue
                    
                    # Determinar el tipo de movimiento
                    tipo_movimiento_valido = albaran.tipo_documento or 'INVENTARIO'
                    if 'tipo_movimiento' in articulo and articulo['tipo_movimiento']:
                        tipo_articulo = str(articulo['tipo_movimiento']).upper()
                        opciones_validas = [k for k, _ in Albaran.TIPO_DOCUMENTO_CHOICES]
                        if tipo_articulo in opciones_validas:
                            tipo_movimiento_valido = tipo_articulo
                    
                    if not tipo_movimiento_valido:
                        tipo_movimiento_valido = 'INVENTARIO'
                    
                    # Determinar estado anterior del inventario
                    inventario = InventarioProducto.objects.filter(
                        producto=producto_catalogo,
                        numero_serie=numero_serie
                    ).first()
                    estado_anterior = inventario.estado if inventario else 'inactivo'

                    # Determinar estado nuevo basado en dirección de transferencia
                    estado_nuevo = 'activo'  # Por defecto
                    if hasattr(albaran, 'direccion_transferencia'):
                        if albaran.direccion_transferencia == 'SALIDA':
                            estado_nuevo = 'inactivo'  # Productos salen de custodia
                        elif albaran.direccion_transferencia == 'ENTRADA':
                            estado_nuevo = 'activo'   # Productos entran en custodia

                    # Crear el movimiento
                    movimiento = MovimientoProducto.objects.create(
                        albaran=albaran,
                        producto=producto_catalogo,
                        numero_serie=numero_serie,
                        tipo_movimiento=tipo_movimiento_valido,
                        estado_anterior=estado_anterior,
                        estado_nuevo=estado_nuevo
                    )

                    # Actualizar o crear registro de inventario
                    InventarioProducto.objects.update_or_create(
                        producto=producto_catalogo,
                        numero_serie=numero_serie,
                        defaults={
                            'estado': estado_nuevo,
                            'ultimo_movimiento': movimiento,
                            'ultima_actualizacion': timezone.now()
                        }
                    )
                    nuevos += 1
            
            # Actualizar el albarán
            albaran.updated_by = request.user
            albaran.save()
            
            serializer = self.get_serializer(albaran)
            return Response({
                "success": True, 
                "data": serializer.data, 
                "nuevos": nuevos,
                "duplicados": duplicados,
                "message": f"Se agregaron {nuevos} productos nuevos. {duplicados} productos ya existían."
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ Error agregando productos al albarán: {str(e)}")
            return Response(
                {"error": "Error interno del servidor"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='productos-de-albaran', permission_classes=[IsAuthenticated])
    def productos_de_albaran(self, request):
        """
        Dado un número de albarán, devuelve TODOS los productos de ese albarán.
        El frontend comparará localmente cuáles son duplicados.
        """
        numero = request.data.get('numero')
        
        if not numero:
            return Response({"error": "Falta el número de albarán."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Buscar albarán usando el método unificado (puede ser página principal o adicional)
        albaran = Albaran.encontrar_documento_existente(numero, solo_principal=False)
        
        if not albaran:
            return Response({"productos": [], "albaran_id": None}, status=status.HTTP_200_OK)
            
        # Obtener todos los movimientos/productos del albarán
        movimientos = MovimientoProducto.objects.filter(albaran=albaran).select_related('producto')
        productos_data = []
        
        for mov in movimientos:
            productos_data.append({
                "codigo": mov.producto.codigo_producto,
                "numero_serie": mov.numero_serie,
                "descripcion": mov.descripcion or mov.producto.descripcion,
                "tipo_movimiento": mov.tipo_movimiento,
                "fecha": mov.fecha.isoformat() if mov.fecha else None
            })
        
        return Response({
            "productos": productos_data, 
            "albaran_id": albaran.id,
            "albaran_numero": albaran.numero
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='siguiente-numero-registro-salida', permission_classes=[IsAuthenticated])
    def siguiente_numero_registro_salida(self, request):
        """
        Genera el siguiente número de registro de salida disponible
        """
        try:
            año = request.query_params.get('año')
            if año:
                año = int(año)
            
            siguiente_numero = Albaran.generar_siguiente_numero_registro_salida(año)
            
            return Response({
                'success': True,
                'numero_registro_salida': siguiente_numero,
                'año': año or timezone.now().year
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Error generando siguiente número de registro de salida: {str(e)}")
            return Response({
                'error': 'Error generando el siguiente número de registro'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='generar-ac21-html', permission_classes=[IsAuthenticated])
    def generar_ac21_html(self, request, pk=None):
        try:
            import requests
            from django.http import HttpResponse
            
            albaran = self.get_object()
            
            # Verificar si es un documento multipágina
            todas_las_paginas = albaran.obtener_todas_las_paginas()
            es_multipagina = len(todas_las_paginas) > 1
            
            print(f"📄 [PDF] Generando AC21 para documento {albaran.numero}")
            print(f"📄 [PDF] Es multipágina: {es_multipagina}, Total páginas: {len(todas_las_paginas)}")
            
            if es_multipagina:
                # Para documentos multipágina, combinar TODOS los productos de todas las hojas físicas
                # y luego dividirlos en páginas de 18 productos para el PDF imprimible
                todos_los_productos = []
                productos_por_hoja_fisica = []  # Para tracking/debugging
                accesorios_por_hoja_fisica = []
                equipos_por_hoja_fisica = []
                
                # Recopilar todos los productos de todas las hojas físicas en orden
                for pagina in todas_las_paginas:
                    movimientos_pagina = MovimientoProducto.objects.filter(albaran=pagina).select_related('producto').order_by('id')
                    count_movimientos = movimientos_pagina.count()
                    print(f"📄 [PDF] Hoja física {pagina.pagina_numero} (Albarán ID={pagina.id}, número={pagina.numero}): {count_movimientos} productos")
                    
                    productos_hoja = []
                    for mov in movimientos_pagina:
                        producto_data = {
                            'codigo_producto': mov.producto.codigo_producto,
                            'cantidad': mov.cantidad or 1,
                            'descripcion_producto': mov.descripcion or mov.producto.descripcion,
                            'numero_serie': mov.numero_serie or 'N/A',
                            'observaciones': mov.observaciones or ''
                        }
                        productos_hoja.append(producto_data)
                        todos_los_productos.append(producto_data)
                    
                    productos_por_hoja_fisica.append(productos_hoja)
                    
                    # Recopilar accesorios y equipos de cada hoja física
                    accesorios_hoja = self._procesar_accesorios(pagina.accesorios)
                    equipos_hoja = self._procesar_equipos_prueba(pagina.equipos_prueba)
                    accesorios_por_hoja_fisica.append(accesorios_hoja)
                    equipos_por_hoja_fisica.append(equipos_hoja)
                
                # Calcular cuántas páginas del PDF imprimible necesitamos (18 productos por página)
                import math
                total_productos = len(todos_los_productos)
                total_paginas_pdf = math.ceil(total_productos / 18)
                
                print(f"📄 [PDF] Total productos de todas las hojas físicas: {total_productos}")
                print(f"📄 [PDF] Productos por hoja física: {[len(p) for p in productos_por_hoja_fisica]}")
                print(f"📄 [PDF] Total páginas PDF imprimible calculadas: {total_paginas_pdf}")
                
                # Dividir productos en páginas de 18 para el PDF imprimible
                productos_por_pagina_pdf = []
                accesorios_por_pagina_pdf = []
                equipos_por_pagina_pdf = []
                
                for pagina_pdf in range(total_paginas_pdf):
                    inicio = pagina_pdf * 18
                    fin = min(inicio + 18, total_productos)
                    productos_pagina = todos_los_productos[inicio:fin]
                    productos_por_pagina_pdf.append(productos_pagina)
                    
                    # Determinar qué accesorios/equipos van en esta página del PDF
                    # Si la página del PDF contiene productos de múltiples hojas físicas,
                    # combinamos los accesorios/equipos de esas hojas
                    accesorios_pagina = []
                    equipos_pagina = []
                    
                    # Calcular qué hojas físicas contribuyen a esta página del PDF
                    productos_antes = inicio
                    productos_despues = fin
                    
                    # Recorrer las hojas físicas para ver cuáles contribuyen
                    productos_acumulados = 0
                    for idx_hoja, productos_hoja in enumerate(productos_por_hoja_fisica):
                        productos_en_hoja = len(productos_hoja)
                        inicio_hoja = productos_acumulados
                        fin_hoja = productos_acumulados + productos_en_hoja
                        
                        # Si esta hoja física tiene productos en el rango de esta página del PDF
                        if inicio_hoja < productos_despues and fin_hoja > productos_antes:
                            # Esta hoja física contribuye a esta página del PDF
                            accesorios_hoja = accesorios_por_hoja_fisica[idx_hoja]
                            equipos_hoja = equipos_por_hoja_fisica[idx_hoja]
                            
                            # Combinar accesorios y equipos (evitar duplicados)
                            for acc in accesorios_hoja:
                                if acc not in accesorios_pagina:
                                    accesorios_pagina.append(acc)
                            for eq in equipos_hoja:
                                if eq not in equipos_pagina:
                                    equipos_pagina.append(eq)
                        
                        productos_acumulados += productos_en_hoja
                    
                    accesorios_por_pagina_pdf.append(accesorios_pagina)
                    equipos_por_pagina_pdf.append(equipos_pagina)
                    
                    print(f"📄 [PDF] Página PDF {pagina_pdf + 1}: {len(productos_pagina)} productos, {len(accesorios_pagina)} accesorios, {len(equipos_pagina)} equipos")
                
                # Usar datos de la primera página para información general
                pagina_principal = todas_las_paginas[0]
                pagina_actual = 1
                
                # Estructura para enviar al PDF generator
                estructura_productos = [len(p) for p in productos_por_pagina_pdf]
                
                print(f"📄 [PDF] Estructura final para PDF imprimible:")
                print(f"📄 [PDF] Total páginas PDF: {total_paginas_pdf}")
                print(f"📄 [PDF] Productos por página PDF: {estructura_productos}")
                print(f"📄 [PDF] Accesorios por página PDF: {[len(a) for a in accesorios_por_pagina_pdf]}")
                print(f"📄 [PDF] Equipos por página PDF: {[len(e) for e in equipos_por_pagina_pdf]}")
                
            else:
                # Para documentos de página única
                movimientos = MovimientoProducto.objects.filter(albaran=albaran).select_related('producto')
                todos_los_productos = []
                
                for mov in movimientos:
                    todos_los_productos.append({
                        'codigo_producto': mov.producto.codigo_producto,
                        'cantidad': mov.cantidad or 1,
                        'descripcion_producto': mov.descripcion or mov.producto.descripcion,
                        'numero_serie': mov.numero_serie or 'N/A',
                        'observaciones': mov.observaciones or ''
                    })
                
                pagina_principal = albaran
                total_paginas = 1
                pagina_actual = 1
                # Definir variables para mantener consistencia con documentos multipágina
                productos_por_pagina = [todos_los_productos]
                accesorios_por_pagina = [self._procesar_accesorios(albaran.accesorios)]
                equipos_por_pagina = [self._procesar_equipos_prueba(albaran.equipos_prueba)]

            # Preparar datos en el formato que espera el servicio PDF
            ac21_data = {
                'numero_albaran': pagina_principal.numero,
                'tipo_transaccion': pagina_principal.tipo_documento,
                'empresa_origen': {
                    'nombre': pagina_principal.empresa_origen.nombre if pagina_principal.empresa_origen else '',
                    'direccion': pagina_principal.empresa_origen.direccion if pagina_principal.empresa_origen else '',
                    'localidad_provincia_cp': f"{pagina_principal.empresa_origen.codigo_postal} {pagina_principal.empresa_origen.ciudad}, {pagina_principal.empresa_origen.provincia}" if pagina_principal.empresa_origen else '',
                    'numero_odmc': pagina_principal.empresa_origen.numero_odmc if pagina_principal.empresa_origen else ''
                } if pagina_principal.empresa_origen else {},
                'empresa_destino': {
                    'nombre': pagina_principal.empresa_destino.nombre if pagina_principal.empresa_destino else '',
                    'direccion': pagina_principal.empresa_destino.direccion if pagina_principal.empresa_destino else '',
                    'localidad_provincia_cp': f"{pagina_principal.empresa_destino.codigo_postal} {pagina_principal.empresa_destino.ciudad}, {pagina_principal.empresa_destino.provincia}" if pagina_principal.empresa_destino else '',
                    'numero_odmc': pagina_principal.empresa_destino.numero_odmc if pagina_principal.empresa_destino else ''
                } if pagina_principal.empresa_destino else {},
                'fecha_informe': pagina_principal.fecha_informe.strftime('%d/%m/%Y') if pagina_principal.fecha_informe else '',
                'numero_registro_salida': pagina_principal.numero_registro_salida or '',
                'fecha_transaccion_dma': pagina_principal.fecha_transaccion.strftime('%d/%m/%Y') if pagina_principal.fecha_transaccion else '',
                'numero_registro_entrada': pagina_principal.numero_registro_entrada or '',
                'codigos_contabilidad': pagina_principal.codigo_contabilidad or '',
                'lineas_producto': todos_los_productos,
                'pagina_actual': pagina_actual,
                'total_paginas': total_paginas_pdf if es_multipagina else total_paginas,
                'productos_por_pagina_estructura': estructura_productos if es_multipagina else [len(p) for p in productos_por_pagina],  # Información de estructura para PDF imprimible
                'accesorios_por_pagina': accesorios_por_pagina_pdf if es_multipagina else accesorios_por_pagina,  # Accesorios específicos de cada página PDF
                'equipos_por_pagina': equipos_por_pagina_pdf if es_multipagina else equipos_por_pagina,  # Equipos específicos de cada página PDF
                'flags': {
                    'firme_y_devuelva': False,  # Ningún checkbox marcado por defecto
                    'para_su_archivo': False
                },
                'material_ha_sido': pagina_principal.estado_material or '',  # Mapear del campo estado_material del modelo
                'destinatario_autorizado': {
                    'testigo': getattr(pagina_principal, 'destinatario_autorizado_testigo', False),
                    'otro_especificar': bool(getattr(pagina_principal, 'destinatario_autorizado_otro_especificar', '')),
                    'otro_texto': getattr(pagina_principal, 'destinatario_autorizado_otro_especificar', '')
                },
                'firma_entrega': {
                    'nombre_apellidos': pagina_principal.firma_a_nombre_apellidos or '',
                    'cargo': pagina_principal.firma_a_cargo or '',
                    'empleo_rango': pagina_principal.firma_a_empleo_rango or '',
                    'firma_texto': pagina_principal.firma_a or ''
                },
                'firma_recibe': {
                    'nombre_apellidos': pagina_principal.firma_b_nombre_apellidos or '',
                    'cargo': pagina_principal.firma_b_cargo or '',
                    'empleo_rango': pagina_principal.firma_b_empleo_rango or '',
                    'firma_texto': pagina_principal.firma_b or ''
                },
                'observaciones_odmc_remitente': pagina_principal.observaciones_odmc or '',
                # NO incluir accesorios y equipos aquí - se usarán los específicos por página desde accesorios_por_pagina y equipos_por_pagina
                # Solo incluir si es documento de página única y no hay estructura por página
                'accesorios': [] if es_multipagina else self._procesar_accesorios(pagina_principal.accesorios),
                'equipos_prueba': [] if es_multipagina else self._procesar_equipos_prueba(pagina_principal.equipos_prueba)
            }

            total_paginas_final = total_paginas_pdf if es_multipagina else total_paginas
            print(f"📄 [PDF] Enviando datos al servicio PDF: {len(todos_los_productos)} productos, {total_paginas_final} páginas PDF")

            # Llamar al servicio cryptotrace-pdf-generator
            pdf_service_url = 'http://pdf-generator:5003/generate-ac21-pdf'
            response = requests.post(pdf_service_url, json=ac21_data, timeout=30)
            
            if response.status_code == 200:
                # Devolver el HTML directamente
                return HttpResponse(response.text, content_type='text/html')
            else:
                return Response(
                    {'error': f'Error del servicio PDF: {response.status_code}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except requests.exceptions.RequestException as e:
            return Response(
                {'error': f'Error conectando con el servicio PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {'error': f'Error generando AC21: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get', 'post'], url_path='paginas', permission_classes=[IsAuthenticated])
    def paginas(self, request, pk=None):
        """
        GET: Obtiene todas las páginas de un documento multipágina
        POST: Crea una página adicional para un documento existente
        """
        albaran = self.get_object()
        
        if request.method == 'GET':
            # Obtener todas las páginas del documento
            todas_las_paginas = albaran.obtener_todas_las_paginas()
            
            # Serializar y devolver directamente el array de páginas
            serializer = self.get_serializer(todas_las_paginas, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Crear página adicional usando el método del modelo
            try:
                # Extraer datos del payload
                payload = request.data if isinstance(request.data, dict) else {}
                
                # Si el payload viene con estructura de AC21 (cabecera, firmas, etc.), extraer campos
                if 'cabecera' in payload:
                    from django.utils import timezone
                    from django.utils.dateparse import parse_datetime, parse_date
                    from datetime import datetime
                    
                    cabecera = payload.get('cabecera', {})
                    firmas = payload.get('firmas', {})
                    firma_a = firmas.get('firma_a', {}) if isinstance(firmas, dict) else {}
                    firma_b = firmas.get('firma_b', {}) if isinstance(firmas, dict) else {}
                    
                    # Extraer fechas de la cabecera con conversión adecuada
                    fecha_informe_raw = cabecera.get('fecha_informe')
                    fecha_transaccion_raw = cabecera.get('fecha_transaccion')
                    
                    # Convertir fecha_informe
                    fecha_informe = None
                    if fecha_informe_raw:
                        if isinstance(fecha_informe_raw, str):
                            parsed_dt = parse_datetime(fecha_informe_raw)
                            if parsed_dt:
                                fecha_informe = parsed_dt.date() if hasattr(parsed_dt, 'date') else parsed_dt
                            else:
                                parsed_date = parse_date(fecha_informe_raw)
                                if parsed_date:
                                    fecha_informe = parsed_date
                        else:
                            fecha_informe = fecha_informe_raw
                    
                    if not fecha_informe:
                        fecha_informe = timezone.now().date()
                    
                    # Convertir fecha_transaccion
                    fecha_transaccion = None
                    if fecha_transaccion_raw:
                        if isinstance(fecha_transaccion_raw, str):
                            parsed_dt = parse_datetime(fecha_transaccion_raw)
                            if parsed_dt:
                                fecha_transaccion = parsed_dt.date() if hasattr(parsed_dt, 'date') else parsed_dt
                            else:
                                parsed_date = parse_date(fecha_transaccion_raw)
                                if parsed_date:
                                    fecha_transaccion = parsed_date
                        else:
                            fecha_transaccion = fecha_transaccion_raw
                    
                    if not fecha_transaccion:
                        fecha_transaccion = fecha_informe
                    
                    # Convertir fecha_informe a datetime para el campo fecha
                    from datetime import time
                    fecha_final = timezone.make_aware(datetime.combine(fecha_informe, time.min))
                    
                    # Crear página adicional con datos del AC21
                    nueva_pagina = albaran.crear_pagina_adicional(
                        fecha=fecha_final,
                        fecha_informe=fecha_informe,
                        fecha_transaccion=fecha_transaccion,
                        accesorios=payload.get('accesorios', []),
                        equipos_prueba=payload.get('equipos_prueba', []),
                        observaciones_odmc=payload.get('observaciones', '') or payload.get('observaciones_odmc', ''),
                        firma_a_nombre_apellidos=firma_a.get('nombre', ''),
                        firma_a_cargo=firma_a.get('cargo', ''),
                        firma_a_empleo_rango=firma_a.get('empleo_rango', ''),
                        firma_b_nombre_apellidos=firma_b.get('nombre', ''),
                        firma_b_cargo=firma_b.get('cargo', ''),
                        firma_b_empleo_rango=firma_b.get('empleo_rango', ''),
                        created_by=request.user
                    )
                else:
                    # Payload directo (campos del albarán)
                    from django.utils import timezone
                    from django.utils.dateparse import parse_datetime, parse_date
                    from datetime import datetime, time
                    
                    # Extraer fechas con fallbacks
                    fecha_informe_raw = payload.get('fecha_informe') or payload.get('fecha')
                    fecha_transaccion_raw = payload.get('fecha_transaccion')
                    
                    # Convertir fechas si vienen como strings
                    fecha_informe = None
                    if fecha_informe_raw:
                        if isinstance(fecha_informe_raw, str):
                            # Intentar parsear como datetime o date
                            parsed_dt = parse_datetime(fecha_informe_raw)
                            if parsed_dt:
                                fecha_informe = parsed_dt.date() if hasattr(parsed_dt, 'date') else parsed_dt
                            else:
                                parsed_date = parse_date(fecha_informe_raw)
                                if parsed_date:
                                    fecha_informe = parsed_date
                        else:
                            fecha_informe = fecha_informe_raw
                    
                    fecha_transaccion = None
                    if fecha_transaccion_raw:
                        if isinstance(fecha_transaccion_raw, str):
                            parsed_dt = parse_datetime(fecha_transaccion_raw)
                            if parsed_dt:
                                fecha_transaccion = parsed_dt.date() if hasattr(parsed_dt, 'date') else parsed_dt
                            else:
                                parsed_date = parse_date(fecha_transaccion_raw)
                                if parsed_date:
                                    fecha_transaccion = parsed_date
                        else:
                            fecha_transaccion = fecha_transaccion_raw
                    
                    # Usar fecha del documento principal o fecha_informe o timezone.now() como fallback
                    fecha_final = None
                    if fecha_informe:
                        # Convertir date a datetime para el campo fecha
                        fecha_final = timezone.make_aware(datetime.combine(fecha_informe, time.min))
                    elif albaran.fecha:
                        fecha_final = albaran.fecha
                    else:
                        fecha_final = timezone.now()
                    
                    # Asegurar valores por defecto para fecha_informe y fecha_transaccion
                    if not fecha_informe:
                        fecha_informe = fecha_final.date() if hasattr(fecha_final, 'date') else fecha_final
                    if not fecha_transaccion:
                        fecha_transaccion = fecha_informe
                    
                    nueva_pagina = albaran.crear_pagina_adicional(
                        fecha=fecha_final,
                        fecha_informe=fecha_informe,
                        fecha_transaccion=fecha_transaccion,
                        accesorios=payload.get('accesorios', []),
                        equipos_prueba=payload.get('equipos_prueba', []),
                        observaciones_odmc=payload.get('observaciones_odmc', ''),
                        firma_a_nombre_apellidos=payload.get('firma_a_nombre_apellidos', ''),
                        firma_a_cargo=payload.get('firma_a_cargo', ''),
                        firma_a_empleo_rango=payload.get('firma_a_empleo_rango', ''),
                        firma_b_nombre_apellidos=payload.get('firma_b_nombre_apellidos', ''),
                        firma_b_cargo=payload.get('firma_b_cargo', ''),
                        firma_b_empleo_rango=payload.get('firma_b_empleo_rango', ''),
                        created_by=request.user
                    )
                
                # Si hay artículos en el payload, crear líneas temporales para ellos
                articulos = payload.get('articulos', [])
                if articulos:
                    from productos.models import LineaTemporalProducto
                    
                    # Extraer datos generales del payload para guardarlos en datos_adicionales
                    cabecera_payload = payload.get('cabecera', {})
                    empresa_origen_payload = payload.get('empresa_origen', {})
                    empresa_destino_payload = payload.get('empresa_destino', {})
                    accesorios_payload = payload.get('accesorios', [])
                    equipos_prueba_payload = payload.get('equipos_prueba', [])
                    firmas_payload = payload.get('firmas', {})
                    observaciones_payload = payload.get('observaciones', '')
                    
                    # Si no hay cabecera en el payload, intentar obtenerla del documento principal
                    if not cabecera_payload and albaran:
                        # Construir cabecera desde el documento principal
                        cabecera_payload = {
                            'numero_registro_salida': albaran.numero_registro_salida or '',
                            'numero_registro_entrada': albaran.numero_registro_entrada or '',
                            'fecha_informe': str(albaran.fecha_informe) if albaran.fecha_informe else '',
                            'fecha_transaccion': str(albaran.fecha_transaccion) if albaran.fecha_transaccion else '',
                            'tipo_transaccion': albaran.tipo_documento or '',
                        }
                    
                    for articulo in articulos:
                        # Preparar datos adicionales con la cabecera completa
                        datos_adicionales = {
                            'cabecera': cabecera_payload,
                            'empresa_origen': empresa_origen_payload,
                            'empresa_destino': empresa_destino_payload,
                            'accesorios': accesorios_payload,
                            'equipos_prueba': equipos_prueba_payload,
                            'firmas': firmas_payload,
                            'observaciones_generales': observaciones_payload,
                        }
                        
                        # Extraer y validar CC - puede estar vacío
                        cc_raw = articulo.get('cc', '')
                        cc = None  # Valor por defecto: NULL
                        if cc_raw and str(cc_raw).strip():
                            try:
                                cc = int(float(str(cc_raw).strip()))
                            except (ValueError, TypeError):
                                cc = None  # No convertible, dejar como NULL
                        
                        # Extraer y validar cantidad
                        cantidad_raw = articulo.get('cantidad', 1)
                        try:
                            cantidad = int(float(str(cantidad_raw))) if cantidad_raw else 1
                            cantidad = max(1, cantidad)
                        except (ValueError, TypeError):
                            cantidad = 1
                        
                        LineaTemporalProducto.objects.create(
                            usuario=request.user,
                            numero_albaran=nueva_pagina.numero,
                            codigo_producto=articulo.get('codigo') or articulo.get('codigo_producto', ''),
                            descripcion=articulo.get('descripcion', ''),
                            numero_serie=articulo.get('numero_serie_inicio') or articulo.get('numero_serie_fin', '') or articulo.get('numero_serie', ''),
                            observaciones=articulo.get('observaciones', ''),
                            cantidad=cantidad,
                            cc=cc,
                            datos_adicionales=datos_adicionales
                        )
                
                serializer = self.get_serializer(nueva_pagina)
                return Response({
                    "success": True,
                    "data": serializer.data,
                    "message": f"Página {nueva_pagina.pagina_numero} creada correctamente"
                }, status=201)
            except Exception as e:
                print(f"❌ Error creando página adicional: {str(e)}")
                import traceback
                traceback.print_exc()
                return Response({
                    "success": False,
                    "error": f"Error creando página adicional: {str(e)}"
                }, status=500)

    @action(detail=False, methods=['get'], url_path='principales', permission_classes=[IsAuthenticated])
    def documentos_principales(self, request):
        """
        Lista solo los documentos principales (página 1) para el listado principal
        """
        queryset = self.get_queryset().filter(
            documento_principal__isnull=True  # Solo documentos principales
        )
        
        # Aplicar filtros existentes
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='imagen-documento', permission_classes=[IsAuthenticated])
    def obtener_imagen_documento(self, request, pk=None):
        """
        Devuelve la imagen del documento AC21 asociada al albarán
        """
        albaran = self.get_object()
        
        if not albaran.imagen_documento:
            return Response({"detail": "Este albarán no tiene imagen de documento asociada."}, status=404)
        
        try:
            from django.http import FileResponse
            import mimetypes
            
            # Determinar el tipo MIME basado en la extensión
            content_type, _ = mimetypes.guess_type(albaran.imagen_documento.name)
            if not content_type:
                content_type = 'image/jpeg'  # Por defecto
            
            # Abrir el archivo y devolver respuesta
            response = FileResponse(
                albaran.imagen_documento.open('rb'),
                content_type=content_type
            )
            response['Content-Disposition'] = f'inline; filename="{albaran.imagen_documento.name}"'
            
            return response
            
        except FileNotFoundError:
            return Response({"detail": "El archivo de imagen no se pudo encontrar."}, status=404)
        except Exception as e:
            return Response({"detail": f"Error al servir la imagen: {str(e)}"}, status=500)

    def _procesar_accesorios(self, accesorios_data):
        """
        Procesa los datos de accesorios del modelo para enviar al PDF generator
        """
        if not accesorios_data:
            return []
        
        try:
            # Si es string, parsear JSON
            if isinstance(accesorios_data, str):
                accesorios_data = json.loads(accesorios_data)
            
            # Si es dict vacío, devolver lista vacía
            if isinstance(accesorios_data, dict) and not accesorios_data:
                return []
            
            # Si es lista, devolverla tal como está
            if isinstance(accesorios_data, list):
                return accesorios_data
            
            # Si es dict con datos, convertir a lista
            if isinstance(accesorios_data, dict):
                return [accesorios_data]
                
        except (json.JSONDecodeError, TypeError):
            print(f"⚠️ Error procesando accesorios: {accesorios_data}")
            return []
        
        return []
    
    def _procesar_equipos_prueba(self, equipos_data):
        """
        Procesa los datos de equipos de prueba del modelo para enviar al PDF generator
        """
        if not equipos_data:
            return []
        
        try:
            # Si es string, parsear JSON
            if isinstance(equipos_data, str):
                equipos_data = json.loads(equipos_data)
            
            # Si es dict vacío, devolver lista vacía
            if isinstance(equipos_data, dict) and not equipos_data:
                return []
            
            # Si es lista, devolverla tal como está
            if isinstance(equipos_data, list):
                return equipos_data
            
            # Si es dict con datos, convertir a lista
            if isinstance(equipos_data, dict):
                return [equipos_data]
                
        except (json.JSONDecodeError, TypeError):
            print(f"⚠️ Error procesando equipos de prueba: {equipos_data}")
            return []
        
        return []

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        print(f"🗑️ [BACKEND] destroy - Eliminando albarán ID={instance.id}, número={instance.numero}, tipo={instance.tipo_documento}, dirección={instance.direccion_transferencia}")
        
        with transaction.atomic():
            movimientos = list(MovimientoProducto.objects.filter(albaran=instance))
            print(f"🗑️ [BACKEND] destroy - Encontrados {len(movimientos)} movimientos para el albarán")
            
            # Recopilar información de productos a eliminar (después de procesar todos los movimientos)
            productos_a_eliminar = []
            
            for mov in movimientos:
                try:
                    producto = mov.producto
                    numero_serie = mov.numero_serie
                    print(f"🗑️ [BACKEND] destroy - Procesando movimiento: producto={producto.codigo_producto}, serie={numero_serie}")
                except Exception as e:
                    print(f"⚠️ [BACKEND] destroy - Error accediendo a producto del movimiento: {str(e)}")
                    continue
                
                # Buscar movimientos anteriores a este albarán para este producto/serie
                movimientos_anteriores = MovimientoProducto.objects.filter(
                    producto=producto,
                    numero_serie=numero_serie
                ).exclude(albaran=instance).order_by('-fecha')
                print(f"🗑️ [BACKEND] destroy - Movimientos anteriores encontrados: {movimientos_anteriores.count()}")
                
                inventario = InventarioProducto.objects.filter(producto=producto, numero_serie=numero_serie).first()
                print(f"🗑️ [BACKEND] destroy - Inventario encontrado: {inventario is not None} (ID={inventario.id if inventario else 'N/A'})")
                
                # Verificar si es un AC21 de ENTRADA (independientemente del tipo_documento)
                es_entrada = instance.direccion_transferencia == 'ENTRADA'
                
                if es_entrada:
                    # AC21 de ENTRADA (independientemente del tipo_documento: TRANSFERENCIA, RECIBO_MANO, etc.)
                    print(f"🗑️ [BACKEND] destroy - AC21 de ENTRADA detectado (tipo_documento={instance.tipo_documento})")
                    # AC21 de entrada: restaurar estado anterior o ELIMINAR del inventario
                    if movimientos_anteriores.exists():
                        mov_ant = movimientos_anteriores.first()
                        print(f"🗑️ [BACKEND] destroy - Hay movimientos anteriores, restaurando estado: {mov_ant.estado_nuevo}")
                        if inventario:
                            inventario.estado = mov_ant.estado_nuevo
                            inventario.ultimo_movimiento = mov_ant
                            inventario.ultima_actualizacion = timezone.now()
                            inventario.save()
                            print(f"✅ [BACKEND] destroy - Inventario restaurado a estado anterior")
                    else:
                        # Si no hay movimientos anteriores, eliminar del inventario
                        # porque el producto fue añadido por este AC21 de entrada
                        print(f"🗑️ [BACKEND] destroy - NO hay movimientos anteriores, ELIMINANDO inventario")
                        if inventario:
                            print(f"🗑️ [BACKEND] Eliminando inventario ID={inventario.id} para producto {producto.codigo_producto}, serie {numero_serie} (AC21 ENTRADA eliminado)")
                            inventario.delete()
                            print(f"✅ [BACKEND] destroy - Inventario eliminado correctamente")
                        else:
                            print(f"⚠️ [BACKEND] destroy - No se encontró inventario para eliminar (producto={producto.codigo_producto}, serie={numero_serie})")
                        
                        # Verificar si el producto debe eliminarse (después de procesar todos los movimientos)
                        otros_movimientos = MovimientoProducto.objects.filter(producto=producto).exclude(albaran=instance)
                        print(f"🗑️ [BACKEND] destroy - Otros movimientos del producto: {otros_movimientos.count()}")
                        if not otros_movimientos.exists():
                            # Guardar para eliminar después
                            productos_a_eliminar.append(producto.id)
                            print(f"🗑️ [BACKEND] destroy - Producto {producto.codigo_producto} marcado para eliminación (sin otros movimientos)")
                        else:
                            print(f"ℹ️ [BACKEND] destroy - Producto NO eliminado porque tiene {otros_movimientos.count()} otros movimientos")
                elif instance.tipo_documento == 'INVENTARIO' and not es_entrada:
                    # Inventario normal (no AC21 de entrada)
                    # Si no hay movimientos anteriores, eliminar del inventario
                    if not movimientos_anteriores.exists():
                        if inventario:
                            print(f"🗑️ [BACKEND] destroy - Eliminando inventario (INVENTARIO sin movimientos anteriores)")
                            inventario.delete()
                        # Además, si el producto del catálogo fue creado por este albarán y no tiene otros movimientos, eliminarlo
                        otros_movimientos = MovimientoProducto.objects.filter(producto=producto).exclude(albaran=instance)
                        if not otros_movimientos.exists():
                            print(f"🗑️ [BACKEND] destroy - Eliminando producto del catálogo (INVENTARIO sin otros movimientos)")
                            producto.delete()
                    else:
                        mov_ant = movimientos_anteriores.first()
                        if inventario:
                            inventario.estado = mov_ant.estado_nuevo
                            inventario.ultimo_movimiento = mov_ant
                            inventario.ultima_actualizacion = timezone.now()
                            inventario.save()
                elif instance.tipo_documento == 'TRANSFERENCIA' and instance.direccion_transferencia == 'SALIDA':
                        # AC21 de salida: restaurar estado anterior o poner activo
                        if movimientos_anteriores.exists():
                            mov_ant = movimientos_anteriores.first()
                            if inventario:
                                inventario.estado = mov_ant.estado_nuevo
                                inventario.ultimo_movimiento = mov_ant
                                inventario.ultima_actualizacion = timezone.now()
                                inventario.save()
                        else:
                            if inventario:
                                inventario.estado = 'activo'
                                inventario.ultimo_movimiento = None
                                inventario.ultima_actualizacion = timezone.now()
                                inventario.save()
            
            # Eliminar productos del catálogo que no tienen otros movimientos (después de procesar todos los movimientos)
            for producto_id in productos_a_eliminar:
                try:
                    producto = CatalogoProducto.objects.get(id=producto_id)
                    # Verificar nuevamente que no tenga otros movimientos (por si acaso)
                    otros_movimientos = MovimientoProducto.objects.filter(producto=producto).exclude(albaran=instance)
                    if not otros_movimientos.exists():
                        print(f"🗑️ [BACKEND] Eliminando producto del catálogo ID={producto.id}, código {producto.codigo_producto} (sin otros movimientos)")
                        producto.delete()
                        print(f"✅ [BACKEND] destroy - Producto del catálogo eliminado correctamente")
                except CatalogoProducto.DoesNotExist:
                    print(f"⚠️ [BACKEND] destroy - Producto ID={producto_id} ya no existe")
                except Exception as e:
                    print(f"⚠️ [BACKEND] destroy - Error eliminando producto ID={producto_id}: {str(e)}")
            
            # Borrar el albarán (esto borra los movimientos por cascade)
            response = super().destroy(request, *args, **kwargs)
        return response

class MovimientoProductoViewSet(viewsets.ModelViewSet):
    queryset = MovimientoProducto.objects.all()
    serializer_class = MovimientoProductoSerializer


class LineaTemporalProductoViewSet(viewsets.ModelViewSet):
    queryset = LineaTemporalProducto.objects.all()
    serializer_class = LineaTemporalProductoSerializer

    def get_queryset(self):
        user = self.request.user
        # Verificar permisos basándose en el rol de HPS (admin o crypto)
        has_admin_permissions = False
        if hasattr(user, 'hps_profile') and user.hps_profile and user.hps_profile.role:
            role_name = user.hps_profile.role.name
            has_admin_permissions = role_name in ['admin', 'crypto']
        # Fallback a is_superuser si no tiene perfil HPS (compatibilidad)
        if not has_admin_permissions:
            has_admin_permissions = user.is_superuser
        
        base_queryset = LineaTemporalProducto.objects.all() if has_admin_permissions else LineaTemporalProducto.objects.filter(usuario=user)
        
        # Filtros opcionales por parámetros de consulta
        procesado = self.request.query_params.get('procesado', 'false').lower()
        if procesado == 'true':
            return base_queryset.filter(procesado=True)
        elif procesado == 'all':
            return base_queryset
        else:
            # Por defecto, solo mostrar productos no procesados (pendientes)
            return base_queryset.filter(procesado=False)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    # 🔹 Endpoint para carga masiva
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def bulk_create(self, request):
        """
        Endpoint para crear múltiples registros en `LineaTemporalProducto` a partir de un AC21 o Excel.
        Ahora acepta un objeto con campos generales (cabecera, empresas, accesorios, firmas, etc.) y un array de articulos.
        También puede recibir FormData con una imagen del documento.
        """
        print("🚀 [BACKEND] bulk_create - INICIO")
        print("🚀 [BACKEND] Usuario:", request.user.username)
        print("🚀 [BACKEND] Método:", request.method)
        print("🚀 [BACKEND] URL:", request.path)
        print("🚀 [BACKEND] Content-Type:", request.content_type)
        
        # Detectar si es FormData (con imagen) o JSON
        imagen_documento = None
        if 'multipart/form-data' in request.content_type:
            print("🖼️ [BACKEND] Recibiendo FormData con imagen")
            # Extraer imagen del FormData
            imagen_documento = request.FILES.get('imagen_documento')
            if imagen_documento:
                print(f"🖼️ [BACKEND] Imagen recibida: {imagen_documento.name}, {imagen_documento.size} bytes, {imagen_documento.content_type}")
            
            # Extraer datos JSON del FormData
            data_str = request.data.get('data')
            if data_str:
                data = json.loads(data_str)
            else:
                print("❌ [BACKEND] ERROR: No se encontró campo 'data' en FormData")
                return Response({"error": "Campo 'data' requerido en FormData"}, status=400)
        else:
            print("📢 [BACKEND] Recibiendo JSON tradicional")
            data = request.data
        
        print("📢 [BACKEND] Datos procesados en bulk_create:", json.dumps(data, indent=2, default=str))

        # Esperamos un objeto con campos generales y un array de articulos
        cabecera = data.get('cabecera', {})
        empresa_origen = data.get('empresa_origen', {})
        empresa_destino = data.get('empresa_destino', {})
        accesorios = data.get('accesorios', [])
        equipos_prueba = data.get('equipos_prueba', [])
        firmas = data.get('firmas', [])
        observaciones = data.get('observaciones', '')
        articulos = data.get('articulos', [])
        
        print("📋 [BACKEND] Cabecera extraída:", cabecera)
        print("🏢 [BACKEND] Empresa origen:", empresa_origen)
        print("🏢 [BACKEND] Empresa destino:", empresa_destino)
        print("📦 [BACKEND] Artículos:", len(articulos))

        # Extraer número de albarán de la cabecera
        numero_albaran = (
            cabecera.get('numero') or
            cabecera.get('numero_registro_entrada') or
            cabecera.get('numero_registro_salida')
        )
        print("📋 [BACKEND] Número de albarán extraído:", numero_albaran)

        if not numero_albaran:
            print("❌ [BACKEND] ERROR: No se encontró número de registro")
            return Response({"error": "No se encontró número de registro en la cabecera del documento"}, status=400)

        if not articulos:
            print("❌ [BACKEND] ERROR: No hay artículos")
            return Response({"error": "No se proporcionaron artículos"}, status=400)

        # 🔹 Eliminar TODOS los registros temporales no procesados del usuario
        # Esto evita que se acumulen registros "colgados" de procesamientos anteriores no completados
        registros_existentes = LineaTemporalProducto.objects.filter(
            usuario=request.user,
            procesado=False
        )
        count_existentes = registros_existentes.count()
        if count_existentes > 0:
            print(f"🧹 [BACKEND] Eliminando {count_existentes} registros temporales no procesados del usuario antes de crear nuevos")
            registros_existentes.delete()

        # Crear registros temporales
        registros_creados = []
        print("🔄 [BACKEND] Creando registros temporales...")
        
        for i, articulo in enumerate(articulos):
            print(f"📦 [BACKEND] Procesando artículo {i+1}/{len(articulos)}: {articulo}")
            
            # Extraer números de serie del OCR
            numero_serie_inicio = str(articulo.get('numero_serie_inicio') or articulo.get('numero_serie') or '').strip()
            numero_serie_fin = str(articulo.get('numero_serie_fin') or articulo.get('numero_serie') or '').strip()
            
            # Para el campo numero_serie del modelo, usar inicio si está disponible, sino fin, sino vacío
            numero_serie = numero_serie_inicio or numero_serie_fin or ''
            
            # Extraer y validar cantidad del OCR
            cantidad_raw = articulo.get('cantidad')
            try:
                if cantidad_raw is None or cantidad_raw == '':
                    cantidad = 1
                else:
                    # Convertir a entero (permite "3.0" -> 3)
                    cantidad = int(float(str(cantidad_raw)))
                    cantidad = max(1, cantidad)  # Mínimo 1
            except (ValueError, TypeError):
                cantidad = 1
            
            # Extraer CC del OCR (puede ser cualquier valor o estar vacío)
            cc_raw = articulo.get('cc')
            cc = None  # Valor por defecto: NULL (puede estar vacío)
            if cc_raw is not None and cc_raw != '':
                try:
                    # Intentar convertir a int si es numérico
                    cc = int(float(str(cc_raw)))
                except (ValueError, TypeError):
                    # Si no es numérico, dejar como NULL
                    cc = None
            
            # Preparar datos adicionales para el campo JSON (incluyendo números de serie completos y cantidad)
            datos_adicionales = {
                'cabecera': cabecera,
                'empresa_origen': empresa_origen,
                'empresa_destino': empresa_destino,
                'accesorios': accesorios,
                'equipos_prueba': equipos_prueba,
                'firmas': firmas,
                'observaciones_generales': observaciones,
                'tiene_imagen_documento': imagen_documento is not None,
                'numero_serie_inicio': numero_serie_inicio,
                'numero_serie_fin': numero_serie_fin,
                'cantidad': cantidad,  # Guardar cantidad validada del OCR
                'cc': cc  # Guardar CC validado del OCR
            }
            
            # Extraer código de producto: viene de "TÍTULO CORTO / EDICIÓN" del AC21
            # Solo usar codigo_producto (eliminado codigo, titulo_corto legacy)
            codigo_producto = (
                articulo.get('codigo_producto') or 
                articulo.get('titulo_corto') or  # Mantener por compatibilidad temporal
                articulo.get('titulo') or  # Campo editable del frontend
                ''
            )
            
            # Extraer observaciones del OCR: viene de "OBSERVACIONES/REMARKS" del AC21
            # Este campo se mapea a descripcion en la BD
            observaciones_ocr = (
                articulo.get('observaciones') or 
                articulo.get('descripcion') or  # Mantener por compatibilidad temporal
                ''
            )
            
            # Mapear observaciones -> descripcion para la BD
            descripcion = observaciones_ocr.strip() if observaciones_ocr else ''
            
            # Asegurar que al menos haya código
            if not codigo_producto:
                codigo_producto = descripcion if descripcion else 'SIN_CODIGO'
            
            print(f"📦 [BACKEND] Artículo procesado - código: '{codigo_producto}', descripción (de observaciones): '{descripcion}', cantidad: {cantidad}, número_serie: '{numero_serie}'")
            
            registro = LineaTemporalProducto.objects.create(
                usuario=request.user,
                numero_albaran=numero_albaran,
                codigo_producto=codigo_producto,
                descripcion=descripcion,  # Mapeado desde observaciones del OCR
                numero_serie=numero_serie,
                cantidad=cantidad,  # Usar cantidad validada
                observaciones='',  # Campo observaciones en BD queda vacío (la info está en descripcion)
                # tipo_producto se deja como null por defecto (se asignará en el modal)
                # cc del OCR se guarda en datos_adicionales['cc']
                datos_adicionales=datos_adicionales
            )
            registros_creados.append(registro)
            print(f"✅ [BACKEND] Registro temporal creado: ID={registro.id}")

        # Si tenemos imagen de documento, guardarla temporalmente
        imagen_temporal_path = None
        if imagen_documento:
            import os
            import tempfile
            from django.conf import settings
            
            print("🖼️ [BACKEND] Imagen presente - guardando temporalmente")
            
            # Crear directorio temporal si no existe
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_documentos')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Guardar imagen temporal con nombre único basado en usuario y timestamp
            import time
            timestamp = str(int(time.time() * 1000))
            extension = imagen_documento.name.split('.')[-1] if '.' in imagen_documento.name else 'jpg'
            nombre_temporal = f"temp_{request.user.id}_{timestamp}_AC21.{extension}"
            imagen_temporal_path = os.path.join(temp_dir, nombre_temporal)
            
            # Escribir archivo temporal
            with open(imagen_temporal_path, 'wb') as f:
                for chunk in imagen_documento.chunks():
                    f.write(chunk)
            
            print(f"🖼️ [BACKEND] Imagen guardada temporalmente en: {imagen_temporal_path}")
            
            # Actualizar datos adicionales de todos los registros con la ruta temporal
            for registro in registros_creados:
                datos_actualizados = registro.datos_adicionales.copy()
                datos_actualizados['imagen_temporal_path'] = imagen_temporal_path
                datos_actualizados['imagen_temporal_name'] = imagen_documento.name
                registro.datos_adicionales = datos_actualizados
                registro.save(update_fields=['datos_adicionales'])
        
        print(f"🎉 [BACKEND] bulk_create COMPLETADO - {len(registros_creados)} registros creados en línea temporal")
        return Response({
            "success": True,
            "message": f"Se crearon {len(registros_creados)} productos en la línea temporal",
            "count": len(registros_creados),
            "con_imagen": imagen_documento is not None
        }, status=201)
        

    # 🔹 Endpoint para obtener productos agrupados por código de producto
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def agrupados(self, request):
        """
        Devuelve los productos agrupados por `codigo_producto`, junto con la cantidad,
        si están tipificados y la descripción de uno de los productos en el grupo.
        También incluye el tipo de producto si ya está asociado.
        """
        
        # Filtrar solo productos no procesados del usuario actual
        queryset_filtrado = self.get_queryset().filter(
            usuario=request.user,
            procesado=False
        )

        # 🔹 Obtener la descripción de un producto dentro del grupo
        descripcion_subquery = queryset_filtrado.filter(
            codigo_producto=OuterRef("codigo_producto")
        ).values("descripcion")[:1]

        # 🔹 Obtener el tipo de `CatalogoProducto` (para carga automática)
        tipo_catalogo_subquery = CatalogoProducto.objects.filter(
            codigo_producto=OuterRef("codigo_producto"),
            tipo__isnull=False
        ).values("tipo__id")[:1]
        
        tipo_catalogo_nombre_subquery = CatalogoProducto.objects.filter(
            codigo_producto=OuterRef("codigo_producto"),
            tipo__isnull=False
        ).values("tipo__nombre")[:1]

        # Filtrar solo productos no procesados del usuario actual
        queryset_filtrado = self.get_queryset().filter(
            usuario=request.user,
            procesado=False
        )
        
        # Agrupar por codigo_producto y tipo_producto (puede ser null)
        from django.db.models import Q
        
        productos_agrupados = (
            queryset_filtrado
            .values("codigo_producto", "tipo_producto")
            .annotate(
                cantidad=Count("id"),  # Contar registros, no sumar cantidades (cada registro = 1 unidad)
                tipificado=Exists(CatalogoProducto.objects.filter(
                    codigo_producto=OuterRef("codigo_producto"), tipo__isnull=False
                )),
                descripcion=Subquery(descripcion_subquery),
                tipo_catalogo_id=Coalesce(Subquery(tipo_catalogo_subquery), None),  # ID del tipo desde CatalogoProducto
                tipo_catalogo_nombre=Coalesce(Subquery(tipo_catalogo_nombre_subquery), None)  # Nombre del tipo desde CatalogoProducto
            )
            .order_by("codigo_producto", "tipo_producto")
        )
        
        # Enriquecer con información de números de serie y concatenar observaciones desde datos_adicionales
        productos_enriquecidos = []
        for producto in productos_agrupados:
            # Obtener todos los registros que coinciden con este grupo (codigo_producto + tipo_producto)
            # Ordenar por created_at para mantener el orden original del documento
            filtro = {'codigo_producto': producto['codigo_producto']}
            if producto['tipo_producto'] is not None:
                filtro['tipo_producto'] = producto['tipo_producto']
            else:
                filtro['tipo_producto__isnull'] = True
            registros = queryset_filtrado.filter(**filtro).order_by('created_at')  # Ordenar por fecha de creación para mantener orden original
            
            # Recopilar descripciones (observaciones) y números de serie en el mismo orden
            descripciones_ordenadas = []  # Lista para mantener el orden
            descripciones_vistas = set()  # Set para evitar duplicados
            rangos_serie = []
            
            for registro in registros:
                # Recopilar descripción (observaciones) manteniendo el orden de aparición
                desc = registro.descripcion
                if desc and desc.strip():  # Solo agregar si no está vacío
                    desc_stripped = desc.strip()
                    # Solo agregar si no la hemos visto antes (evitar duplicados)
                    if desc_stripped not in descripciones_vistas:
                        descripciones_ordenadas.append(desc_stripped)
                        descripciones_vistas.add(desc_stripped)
                
                # Recopilar números de serie en el mismo orden
                datos_adic = registro.datos_adicionales or {}
                numero_serie_inicio = datos_adic.get('numero_serie_inicio', '').strip() if datos_adic.get('numero_serie_inicio') else ''
                numero_serie_fin = datos_adic.get('numero_serie_fin', '').strip() if datos_adic.get('numero_serie_fin') else ''
                
                # Si hay inicio Y fin
                if numero_serie_inicio and numero_serie_fin:
                    # Si son iguales, mostrar solo uno (una sola unidad)
                    if numero_serie_inicio == numero_serie_fin:
                        rangos_serie.append(numero_serie_inicio)
                    else:
                        # Si son diferentes, mostrar rango "inicio - fin"
                        rangos_serie.append(f"{numero_serie_inicio} - {numero_serie_fin}")
                elif numero_serie_inicio:
                    rangos_serie.append(numero_serie_inicio)
                elif numero_serie_fin:
                    rangos_serie.append(numero_serie_fin)
            
            # Concatenar descripciones manteniendo el orden de aparición
            descripcion_final = None
            if len(descripciones_ordenadas) > 1:
                # Hay múltiples descripciones diferentes: concatenarlas en el orden de aparición
                descripcion_final = ', '.join(descripciones_ordenadas)
            elif len(descripciones_ordenadas) == 1:
                # Solo una descripción única: usar esa
                descripcion_final = descripciones_ordenadas[0]
            # Si está vacío, descripcion_final queda None
            
            # Concatenar todos los rangos con comas (manteniendo el orden)
            rango_serie = ', '.join(rangos_serie) if rangos_serie else None
            
            # Para compatibilidad, también guardar el primer inicio y último fin
            numero_serie_inicio = None
            numero_serie_fin = None
            if rangos_serie:
                # Extraer el primer inicio y último fin de todos los rangos
                primeros_inicios = []
                ultimos_fins = []
                for registro in registros:
                    datos_adic = registro.datos_adicionales or {}
                    if datos_adic.get('numero_serie_inicio'):
                        primeros_inicios.append(datos_adic['numero_serie_inicio'].strip())
                    if datos_adic.get('numero_serie_fin'):
                        ultimos_fins.append(datos_adic['numero_serie_fin'].strip())
                
                if primeros_inicios:
                    numero_serie_inicio = min(primeros_inicios)  # Primer número de serie (mínimo)
                if ultimos_fins:
                    numero_serie_fin = max(ultimos_fins)  # Último número de serie (máximo)
            
            # Incluir observaciones concatenadas y tipo_producto en la respuesta
            # Si tipo_producto es null pero hay tipo_catalogo_id, usar ese para carga automática
            tipo_producto_id = producto['tipo_producto']
            tipo_producto_nombre = None
            if tipo_producto_id:
                try:
                    tipo_obj = TipoProducto.objects.get(id=tipo_producto_id)
                    tipo_producto_nombre = tipo_obj.nombre
                except TipoProducto.DoesNotExist:
                    pass
            elif producto.get('tipo_catalogo_id'):
                # Si no hay tipo_producto pero hay tipo en CatalogoProducto, usar ese para carga automática
                tipo_producto_id = producto['tipo_catalogo_id']
                tipo_producto_nombre = producto.get('tipo_catalogo_nombre')
            
            productos_enriquecidos.append({
                **producto,
                'observaciones': descripcion_final,  # Descripciones concatenadas si son diferentes
                'descripcion': descripcion_final,  # También en descripcion para compatibilidad
                'tipo_producto_id': tipo_producto_id,  # ID del TipoProducto asignado (o desde CatalogoProducto si es null)
                'tipo_producto_nombre': tipo_producto_nombre,  # Nombre del TipoProducto
                'tipo_catalogo_id': producto.get('tipo_catalogo_id'),  # ID del tipo desde CatalogoProducto (para carga automática)
                'tipo_catalogo_nombre': producto.get('tipo_catalogo_nombre'),  # Nombre del tipo desde CatalogoProducto
                'numero_serie_inicio': numero_serie_inicio,
                'numero_serie_fin': numero_serie_fin,
                'rango_serie': rango_serie  # Todos los rangos concatenados
            })

        # 🔹 Obtener todos los tipos de producto disponibles con su ID
        tipos_disponibles = TipoProducto.objects.all().values('id', 'nombre')

        return Response({
            "productos": productos_enriquecidos,
            "tipos_disponibles": list(tipos_disponibles)  # Lista de {id, nombre}
        }, status=status.HTTP_200_OK)
    


    @action(detail=False, methods=["post"], url_path="asignar-tipo", permission_classes=[IsAuthenticated])
    def asignar_tipo(self, request):
        """
        Asigna un tipo de producto a un `codigo_producto` en Producto.
        Si el producto no existe, lo crea automáticamente.
        """
        codigo_producto = request.data.get("codigo_producto")
        tipo_nombre = request.data.get("tipo")

        if not codigo_producto or not tipo_nombre:
            return Response({"error": "Código de producto y tipo son obligatorios"}, status=status.HTTP_400_BAD_REQUEST)

        tipo, _ = TipoProducto.objects.get_or_create(nombre=tipo_nombre)
        
        producto, created = CatalogoProducto.objects.update_or_create(
            codigo_producto=codigo_producto,
            defaults={"tipo": tipo}
        )

        # Si el producto fue recién creado, asignamos la descripción y guardamos
        if created:
            producto.descripcion = f"Producto {codigo_producto}"
            producto.save()

        return Response({"message": "Tipo asignado correctamente", "created": created}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="actualizar-cc", permission_classes=[IsAuthenticated])
    def actualizar_cc(self, request):
        """
        Actualiza el campo tipo_producto (tipo de cryptocustodio) de todas las líneas temporales
        no procesadas del usuario actual que tengan el mismo codigo_producto.
        También actualiza el CatalogoProducto asociado si existe.
        tipo_producto_id: ID del TipoProducto (ForeignKey)
        """
        codigo_producto = request.data.get("codigo_producto")
        tipo_producto_id = request.data.get("tipo_producto_id")

        if not codigo_producto:
            return Response({"error": "Código de producto es obligatorio"}, status=status.HTTP_400_BAD_REQUEST)
        
        if tipo_producto_id is None:
            return Response({"error": "El campo tipo_producto_id es obligatorio"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener el TipoProducto
        try:
            tipo_producto = TipoProducto.objects.get(id=tipo_producto_id)
        except TipoProducto.DoesNotExist:
            return Response({"error": f"TipoProducto con ID {tipo_producto_id} no existe"}, status=status.HTTP_400_BAD_REQUEST)

        # Actualizar todas las líneas temporales no procesadas del usuario con este codigo_producto
        lineas_actualizadas = LineaTemporalProducto.objects.filter(
            usuario=request.user,
            codigo_producto=codigo_producto,
            procesado=False
        ).update(tipo_producto=tipo_producto)

        # Actualizar también el CatalogoProducto si existe
        producto_catalogo = CatalogoProducto.objects.filter(codigo_producto=codigo_producto).first()
        if producto_catalogo:
            producto_catalogo.tipo = tipo_producto
            producto_catalogo.save()
            print(f"✅ [BACKEND] CatalogoProducto {codigo_producto} actualizado con tipo {tipo_producto.nombre}")

        return Response({
            "message": f"Tipo de cryptocustodio actualizado correctamente",
            "lineas_actualizadas": lineas_actualizadas
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def limpiar_procesados(self, request):
        """
        Elimina registros temporales procesados más antiguos que X días.
        Por defecto elimina los de más de 30 días.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        dias = int(request.data.get('dias', 30))
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        # Solo el usuario puede limpiar sus propios registros, excepto admins/cryptos
        # Verificar permisos basándose en el rol de HPS (admin o crypto)
        has_admin_permissions = False
        if hasattr(request.user, 'hps_profile') and request.user.hps_profile and request.user.hps_profile.role:
            role_name = request.user.hps_profile.role.name
            has_admin_permissions = role_name in ['admin', 'crypto']
        # Fallback a is_superuser si no tiene perfil HPS (compatibilidad)
        if not has_admin_permissions:
            has_admin_permissions = request.user.is_superuser
        
        if has_admin_permissions:
            registros_antiguos = LineaTemporalProducto.objects.filter(
                procesado=True,
                created_at__lt=fecha_limite  # Asumiendo que tienes un campo created_at
            )
        else:
            registros_antiguos = LineaTemporalProducto.objects.filter(
                usuario=request.user,
                procesado=True,
                created_at__lt=fecha_limite
            )
        
        count = registros_antiguos.count()
        registros_antiguos.delete()
        
        return Response({
            "message": f"Se eliminaron {count} registros procesados anteriores a {fecha_limite.strftime('%Y-%m-%d')}",
            "count": count
        }, status=200)
    
    @action(detail=False, methods=["post"], url_path="procesar-directo", permission_classes=[IsAuthenticated])
    def procesar_directo(self, request):
        """
        Procesa un AC21 directamente desde el frontend sin usar línea temporal.
        Recibe todos los datos del AC21 y crea directamente:
        - Albaran
        - Movimientos
        - Inventario
        
        También detecta si existe documento con mismo número y permite crear
        página adicional o documento independiente.
        
        Este es el nuevo flujo: datos en memoria → procesamiento directo.
        """
        print("🚀 [BACKEND] procesar_directo - INICIO")
        print("🚀 [BACKEND] Usuario:", request.user.username)
        print("🚀 [BACKEND] Método:", request.method)
        print("🚀 [BACKEND] URL:", request.path)
        
        # Manejar FormData (cuando se envía imagen)
        parsed_data = request.data
        imagen_documento = None
        
        if 'multipart/form-data' in request.content_type:
            print("🖼️ [BACKEND] Recibiendo FormData con imagen")
            imagen_documento = request.FILES.get('imagen_documento')
            if imagen_documento:
                print(f"🖼️ [BACKEND] Imagen recibida: {imagen_documento.name}, {imagen_documento.size} bytes")
            
            # Extraer datos JSON del FormData
            data_str = request.data.get('data')
            if data_str:
                try:
                    if isinstance(data_str, str):
                        parsed_data = json.loads(data_str)
                    else:
                        parsed_data = data_str
                    print("✅ [BACKEND] Datos parseados desde FormData")
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"❌ [BACKEND] Error parseando JSON de FormData: {e}")
                    return Response({"error": f"Error parseando datos JSON: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                print("⚠️ [BACKEND] No se encontró campo 'data' en FormData")
                return Response({"error": "Campo 'data' requerido en FormData"}, status=status.HTTP_400_BAD_REQUEST)
        
        print("📢 [BACKEND] Payload recibido en procesar_directo:", json.dumps(parsed_data, indent=2, default=str))
        
        # Extraer datos del payload
        cabecera = parsed_data.get('cabecera', {})
        empresa_origen = parsed_data.get('empresa_origen', {})
        empresa_destino = parsed_data.get('empresa_destino', {})
        articulos = parsed_data.get('articulos', [])
        accesorios = parsed_data.get('accesorios', [])
        equipos_prueba = parsed_data.get('equipos_prueba', [])
        firmas = parsed_data.get('firmas', {})
        observaciones = parsed_data.get('observaciones', '')
        
        # 1. VALIDACIÓN: Número de registro de salida (obligatorio)
        numero_registro_salida = cabecera.get('numero_registro_salida')
        if not numero_registro_salida or str(numero_registro_salida).strip() == '':
            print("❌ [BACKEND] ERROR: Número de registro de salida es obligatorio")
            return Response({
                "error": "El número de registro de salida es obligatorio"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"✅ [BACKEND] Número de registro de salida validado: {numero_registro_salida}")
        
        # 2. DETECCIÓN: Verificar si existe documento con mismo número
        # PERO solo si NO se está procesando una decisión ya tomada (crear_pagina_adicional)
        crear_pagina_adicional = parsed_data.get('crear_pagina_adicional', False)
        documento_existente_id = parsed_data.get('documento_existente_id', None)
        
        # Si ya se decidió crear página adicional, saltar la verificación y continuar
        if not (crear_pagina_adicional and documento_existente_id):
            documento_existente = Albaran.encontrar_documento_existente(numero_registro_salida)
            
            if documento_existente:
                print(f"🔍 [BACKEND] Documento existente encontrado: ID={documento_existente.id}, Número={documento_existente.numero}")
                # Devolver información del documento existente para que el frontend pregunte
                return Response({
                    "documento_existente": {
                        "id": documento_existente.id,
                        "numero": documento_existente.numero,
                        "fecha": documento_existente.fecha.isoformat() if documento_existente.fecha else None,
                        "total_paginas": documento_existente.total_paginas if hasattr(documento_existente, 'total_paginas') else 1
                    },
                    "requiere_decision": True,
                    "mensaje": f"Ya existe un documento con el número {numero_registro_salida}. ¿Deseas crear una página adicional o un documento independiente?"
                }, status=status.HTTP_200_OK)
            
            print("✅ [BACKEND] No existe documento con mismo número, continuando con creación...")
        else:
            print(f"✅ [BACKEND] Procesando decisión de crear página adicional para documento ID={documento_existente_id}, saltando verificación...")
        
        # 3. PROCESAMIENTO: Crear albarán, movimientos e inventario
        from django.db import transaction
        from django.utils import timezone
        import os
        import time
        
        try:
            with transaction.atomic():
                # 3.1. Preparar datos para creación de albarán
                firma_a_data = firmas.get('firma_a', {}) if isinstance(firmas, dict) else {}
                firma_b_data = firmas.get('firma_b', {}) if isinstance(firmas, dict) else {}
                
                fecha_informe = cabecera.get('fecha_informe') or timezone.now().date()
                fecha_transaccion = cabecera.get('fecha_transaccion_dma') or cabecera.get('fecha_transaccion') or timezone.now().date()
                
                # Normalizar tipo_documento desde tipo_transaccion
                tipo_transaccion_raw = cabecera.get('tipo_transaccion', '')
                tipo_documento_normalizado = None
                
                if tipo_transaccion_raw:
                    if isinstance(tipo_transaccion_raw, dict):
                        tipos = []
                        if tipo_transaccion_raw.get('transferencia'): tipos.append('TRANSFERENCIA')
                        if tipo_transaccion_raw.get('inventario'): tipos.append('INVENTARIO')
                        if tipo_transaccion_raw.get('destruccion'): tipos.append('DESTRUCCION')
                        if tipo_transaccion_raw.get('recibo_en_mano'): tipos.append('RECIBO_MANO')
                        if tipo_transaccion_raw.get('otro'): tipos.append('OTRO')
                        tipo_documento_normalizado = tipos[0] if tipos else 'INVENTARIO'
                    else:
                        tipo_str = str(tipo_transaccion_raw).upper().replace(' ', '_')
                        tipo_map = {
                            'RECIBO_EN_MANO': 'RECIBO_MANO',
                            'RECIBO EN MANO': 'RECIBO_MANO',
                            'RECIBOENMANO': 'RECIBO_MANO',
                        }
                        tipo_documento_normalizado = tipo_map.get(tipo_str, tipo_str)
                        if len(tipo_documento_normalizado) > 20:
                            tipo_documento_normalizado = tipo_documento_normalizado[:20]
                
                if not tipo_documento_normalizado:
                    tipo_documento_normalizado = 'INVENTARIO'
                
                print(f"📋 [BACKEND] Tipo documento normalizado: '{tipo_documento_normalizado}'")
                
                # Verificar si se debe crear página adicional o documento independiente
                # (crear_pagina_adicional y documento_existente_id ya se obtuvieron arriba)
                
                if crear_pagina_adicional and documento_existente_id:
                    # Crear página adicional
                    documento_existente = Albaran.objects.get(id=documento_existente_id)
                    print(f"📄 [BACKEND] Creando página adicional para documento existente ID={documento_existente.id}, número={documento_existente.numero}")
                    print(f"📄 [BACKEND] Total páginas antes: {documento_existente.total_paginas}")
                    
                    albaran = documento_existente.crear_pagina_adicional(
                        fecha=fecha_informe,
                        fecha_informe=fecha_informe,
                        fecha_transaccion=fecha_transaccion,
                        accesorios=accesorios,
                        equipos_prueba=equipos_prueba,
                        observaciones_odmc=observaciones or '',
                        firma_a_nombre_apellidos=firma_a_data.get('nombre', ''),
                        firma_a_cargo=firma_a_data.get('cargo', ''),
                        firma_a_empleo_rango=firma_a_data.get('empleo_rango', ''),
                        firma_b_nombre_apellidos=firma_b_data.get('nombre', ''),
                        firma_b_cargo=firma_b_data.get('cargo', ''),
                        firma_b_empleo_rango=firma_b_data.get('empleo_rango', ''),
                        created_by=request.user
                    )
                    
                    # Refrescar documento principal para obtener total_paginas actualizado
                    documento_existente.refresh_from_db()
                    print(f"📄 [BACKEND] Página adicional creada: ID={albaran.id}, número={albaran.numero}, página={albaran.pagina_numero}")
                    print(f"📄 [BACKEND] Total páginas después: {documento_existente.total_paginas}")
                else:
                    # Crear documento nuevo
                    print("🏗️ [BACKEND] Creando nuevo documento (página principal)...")
                    
                    numero_registro_entrada = str(cabecera.get('numero_registro_entrada', ''))[:20] if cabecera.get('numero_registro_entrada') else ''
                    numero_registro_salida = str(numero_registro_salida)[:20] if len(str(numero_registro_salida)) > 20 else numero_registro_salida
                    
                    albaran = Albaran.objects.create(
                        numero=numero_registro_salida,
                        tipo_documento=tipo_documento_normalizado,
                        fecha=fecha_informe,
                        fecha_informe=fecha_informe,
                        fecha_transaccion=fecha_transaccion,
                        numero_registro_entrada=numero_registro_entrada,
                        numero_registro_salida=numero_registro_salida,
                        codigo_contabilidad=cabecera.get('codigos_contabilidad', ''),
                        empresa_origen_id=empresa_origen.get('id'),
                        empresa_destino_id=empresa_destino.get('id'),
                        direccion_transferencia='ENTRADA',  # Siempre ENTRADA para AC21 desde OCR
                        accesorios=accesorios,
                        equipos_prueba=equipos_prueba,
                        observaciones_odmc=observaciones or '',
                        pagina_numero=1,
                        total_paginas=1,
                        firma_a_nombre_apellidos=firma_a_data.get('nombre', ''),
                        firma_a_cargo=firma_a_data.get('cargo', ''),
                        firma_a_empleo_rango=firma_a_data.get('empleo_rango', ''),
                        firma_b_nombre_apellidos=firma_b_data.get('nombre', ''),
                        firma_b_cargo=firma_b_data.get('cargo', ''),
                        firma_b_empleo_rango=firma_b_data.get('empleo_rango', ''),
                        created_by=request.user
                    )
                
                print(f"✅ [BACKEND] Albarán creado: ID={albaran.id}, Número={albaran.numero}, Página={albaran.pagina_numero}/{albaran.total_paginas}")
                
                # 3.2. Guardar imagen si existe
                if imagen_documento:
                    try:
                        from django.core.files.base import ContentFile
                        extension = imagen_documento.name.split('.')[-1] if '.' in imagen_documento.name else 'jpg'
                        nombre_final = f"albaran_{albaran.id}_AC21_{int(time.time())}.{extension}"
                        albaran.imagen_documento.save(nombre_final, imagen_documento, save=True)
                        print(f"🖼️ [BACKEND] Imagen guardada: {albaran.imagen_documento.name}")
                    except Exception as e:
                        print(f"❌ [BACKEND] Error guardando imagen: {str(e)}")
                        # Continuar sin fallar el proceso
                
                # 3.3. Crear mapa de código → tipo_producto_id para actualizar catálogo
                codigo_a_tipo = {}
                for articulo in articulos:
                    codigo = articulo.get('codigo_producto')
                    tipo_id = articulo.get('tipo_producto_id')
                    if tipo_id and codigo:
                        codigo_a_tipo[codigo] = tipo_id
                        print(f"📋 [BACKEND] Mapeo código→tipo: {codigo} → tipo_id={tipo_id}")
                    elif codigo:
                        print(f"⚠️ [BACKEND] Artículo {codigo} sin tipo_producto_id (será null)")
                
                print(f"📋 [BACKEND] Total códigos a tipificar: {len(codigo_a_tipo)}")
                if codigo_a_tipo:
                    print(f"📋 [BACKEND] Códigos con tipo: {list(codigo_a_tipo.keys())}")
                
                # 3.4. Crear movimientos e inventario para cada artículo
                # NOTA: Los tipos se actualizarán DESPUÉS de crear todos los productos
                print("🔄 [BACKEND] Creando movimientos...")
                movimientos_creados = 0
                
                for articulo in articulos:
                    codigo_producto = articulo.get('codigo_producto')
                    if not codigo_producto:
                        print(f"⚠️ [BACKEND] Artículo sin código, se omite")
                        continue
                    
                    # Buscar/crear producto en catálogo
                    producto = CatalogoProducto.objects.filter(codigo_producto=codigo_producto).first()
                    if not producto:
                        descripcion = articulo.get('descripcion', '') or articulo.get('observaciones', '')
                        producto, created = CatalogoProducto.objects.get_or_create(
                            codigo_producto=codigo_producto,
                            defaults={'descripcion': descripcion}
                        )
                        if created:
                            print(f"➕ [BACKEND] Producto creado: ID={producto.id}, código={codigo_producto}")
                    
                    # Verificar duplicados
                    numero_serie = articulo.get('numero_serie', '')
                    existe = MovimientoProducto.objects.filter(
                        albaran=albaran,
                        producto=producto,
                        numero_serie=numero_serie
                    ).exists()
                    
                    if existe:
                        print(f"⚠️ [BACKEND] Movimiento duplicado para producto {producto.id}, serie {numero_serie}. Se omite.")
                        continue
                    
                    # Determinar estados
                    inventario_existente = InventarioProducto.objects.filter(
                        producto=producto,
                        numero_serie=numero_serie
                    ).first()
                    estado_anterior = inventario_existente.estado if inventario_existente else 'inactivo'
                    estado_nuevo = 'activo'  # Siempre activo para ENTRADA
                    
                    # Obtener CC del OCR - puede estar vacío, respetar el vacío usando NULL
                    cc_del_ocr_raw = articulo.get('cc', '')
                    cc_del_ocr = None  # Valor por defecto: NULL (campo puede estar vacío)
                    
                    # Si el campo viene con valor, intentar convertirlo a entero
                    if cc_del_ocr_raw is not None and cc_del_ocr_raw != '':
                        if isinstance(cc_del_ocr_raw, str):
                            cc_str = cc_del_ocr_raw.strip()
                            if cc_str:  # Solo si no está vacío después de trim
                                try:
                                    cc_del_ocr = int(float(cc_str))
                                    print(f"✅ [BACKEND] CC extraído del OCR: {cc_del_ocr}")
                                except (ValueError, TypeError):
                                    # Si no se puede convertir, dejar como NULL
                                    print(f"⚠️ [BACKEND] CC no convertible '{cc_del_ocr_raw}', dejando como NULL")
                                    cc_del_ocr = None
                            else:
                                # Cadena vacía después de trim - el OCR indicó que está vacío
                                print(f"ℹ️ [BACKEND] CC vacío en OCR, guardando como NULL")
                                cc_del_ocr = None
                        elif isinstance(cc_del_ocr_raw, (int, float)):
                            cc_del_ocr = int(cc_del_ocr_raw)
                            print(f"✅ [BACKEND] CC extraído del OCR: {cc_del_ocr}")
                    else:
                        # None o cadena vacía - el OCR no proporcionó valor
                        print(f"ℹ️ [BACKEND] CC no proporcionado en OCR (None o ''), guardando como NULL")
                        cc_del_ocr = None
                    # Si el usuario quiere respetar el vacío, necesitaríamos cambiar el modelo a null=True
                    
                    # Crear movimiento
                    movimiento = MovimientoProducto.objects.create(
                        albaran=albaran,
                        producto=producto,
                        numero_serie=numero_serie,
                        descripcion=producto.descripcion,
                        tipo_movimiento=tipo_documento_normalizado,
                        cantidad=articulo.get('cantidad', 1),
                        cc=cc_del_ocr,
                        observaciones=articulo.get('observaciones', ''),
                        estado_anterior=estado_anterior,
                        estado_nuevo=estado_nuevo
                    )
                    movimientos_creados += 1
                    print(f"✅ [BACKEND] Movimiento creado ID={movimiento.id} para {codigo_producto}, serie={numero_serie}")
                
                print(f"🎉 [BACKEND] {movimientos_creados} movimientos creados")
                
                # 3.5. Actualizar tipos en catálogo DESPUÉS de crear todos los productos
                # Esto asegura que tanto productos nuevos como existentes tengan el tipo correcto
                if codigo_a_tipo:
                    print(f"📋 [BACKEND] Actualizando tipos en catálogo para {len(codigo_a_tipo)} códigos...")
                    for codigo, tipo_id in codigo_a_tipo.items():
                        try:
                            producto = CatalogoProducto.objects.filter(codigo_producto=codigo).first()
                            if producto:
                                tipo_producto = TipoProducto.objects.get(id=tipo_id)
                                producto_anterior_tipo = producto.tipo.nombre if producto.tipo else "sin tipo"
                                producto.tipo = tipo_producto
                                producto.save()
                                print(f"✅ [BACKEND] CatalogoProducto {codigo} actualizado: {producto_anterior_tipo} → {tipo_producto.nombre}")
                            else:
                                print(f"⚠️ [BACKEND] Producto {codigo} no encontrado en catálogo para actualizar tipo")
                        except TipoProducto.DoesNotExist:
                            print(f"⚠️ [BACKEND] TipoProducto con ID {tipo_id} no existe para código {codigo}")
                        except Exception as e:
                            print(f"⚠️ [BACKEND] Error actualizando tipo para {codigo}: {str(e)}")
                            import traceback
                            traceback.print_exc()
                else:
                    print(f"⚠️ [BACKEND] No hay códigos con tipo_producto_id para actualizar en catálogo")
                
                # Obtener total_paginas actualizado
                doc_principal = albaran.obtener_documento_principal if albaran.documento_principal else albaran
                doc_principal.refresh_from_db()  # Asegurar que tenemos el valor más reciente
                total_paginas_actualizado = doc_principal.total_paginas
                
                print(f"📊 [BACKEND] Respuesta final - albaran_id={albaran.id}, es_pagina_adicional={albaran.documento_principal is not None}, total_paginas={total_paginas_actualizado}")
                
                return Response({
                    "detail": "AC21 procesado correctamente",
                    "albaran_id": albaran.id,
                    "albaran_numero": albaran.numero,
                    "es_pagina_adicional": albaran.documento_principal is not None,
                    "total_paginas": total_paginas_actualizado,
                    "movimientos_creados": movimientos_creados
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            import traceback
            print(f"❌ [BACKEND] ERROR en procesar_directo: {str(e)}")
            traceback.print_exc()
            return Response({
                "error": f"Error procesando el AC21: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def procesar(self, request):
        """
        Procesa los productos temporales y genera un albarán con todos los datos generales y de productos,
        permitiendo la tipificación previa igual que en el flujo de Excel.
        """
        print("🚀 [BACKEND] procesar - INICIO")
        print("🚀 [BACKEND] Usuario:", request.user.username)
        print("🚀 [BACKEND] Método:", request.method)
        print("🚀 [BACKEND] URL:", request.path)
        print("📢 [BACKEND] Payload recibido en procesar:", json.dumps(request.data, indent=2, default=str))
        
        from django.db import transaction
        # Obtener todos los productos temporales no procesados del usuario
        productos_temporales_base = self.get_queryset().filter(procesado=False, usuario=request.user)
        print(f"📦 [BACKEND] Productos temporales no procesados encontrados: {productos_temporales_base.count()}")

        if not productos_temporales_base.exists():
            print("❌ [BACKEND] ERROR: No hay productos temporales")
            return Response({"detail": "No hay productos temporales para procesar."}, status=400)

        # Extraer campos generales del primer producto temporal (todos comparten cabecera, empresas, etc.)
        p0 = productos_temporales_base.first()
        print(f"📋 [BACKEND] Primer producto temporal: ID={p0.id}, numero_albaran={p0.numero_albaran}")
        
        # 🔹 FILTRAR POR numero_albaran: Solo procesar productos del mismo documento
        # Esto evita mezclar productos de diferentes documentos
        numero_albaran_documento = p0.numero_albaran
        productos_temporales = productos_temporales_base.filter(numero_albaran=numero_albaran_documento)
        print(f"📦 [BACKEND] Productos temporales del documento {numero_albaran_documento}: {productos_temporales.count()}")
        
        if not productos_temporales.exists():
            print("❌ [BACKEND] ERROR: No hay productos temporales para este documento")
            return Response({"detail": "No hay productos temporales para procesar en este documento."}, status=400)
        
        # Obtener datos desde el campo JSON datos_adicionales
        datos_adicionales = getattr(p0, 'datos_adicionales', {}) or {}
        cabecera = datos_adicionales.get('cabecera', {})
        empresa_origen = datos_adicionales.get('empresa_origen', {})
        empresa_destino = datos_adicionales.get('empresa_destino', {})
        accesorios = datos_adicionales.get('accesorios', [])
        equipos_prueba = datos_adicionales.get('equipos_prueba', [])
        firmas = datos_adicionales.get('firmas', [])
        observaciones = datos_adicionales.get('observaciones_generales', '')
        
        print("📋 [BACKEND] Datos extraídos del temporal:")
        print("  - Cabecera:", cabecera)
        print("  - Empresa origen:", empresa_origen)
        print("  - Empresa destino:", empresa_destino)

        # Permitir override desde el payload si se envía algo nuevo
        cabecera = request.data.get('cabecera', cabecera)
        empresa_origen = request.data.get('empresa_origen', empresa_origen)
        empresa_destino = request.data.get('empresa_destino', empresa_destino)
        accesorios = request.data.get('accesorios', accesorios)
        equipos_prueba = request.data.get('equipos_prueba', equipos_prueba)
        firmas = request.data.get('firmas', firmas)
        observaciones = request.data.get('observaciones', observaciones)
        
        print("📋 [BACKEND] Datos finales tras override:")
        print("  - Cabecera:", cabecera)

        # Extraer número de albarán de la cabecera
        def get_first_nonempty(*args):
            for v in args:
                if v is not None and str(v).strip() != '':
                    return v
            return None
        
        # Intentar extraer número de múltiples fuentes
        numero = get_first_nonempty(
            cabecera.get('numero'),
            cabecera.get('numero_registro_entrada'),
            cabecera.get('numero_registro_salida'),
            # También intentar desde el numero_albaran del producto temporal
            numero_albaran_documento,
        )
        print(f"📋 [BACKEND] Número extraído: {numero}")
        print(f"📋 [BACKEND] Cabecera completa: {cabecera}")
        print(f"📋 [BACKEND] numero_albaran_documento: {numero_albaran_documento}")
        
        if not numero:
            print("❌ [BACKEND] ERROR: No se encontró número de registro")
            print("❌ [BACKEND] Cabecera recibida:", cabecera)
            print("❌ [BACKEND] Datos adicionales del primer producto:", datos_adicionales)
            return Response({"detail": "No se encontró número de registro en el AC21. Verifica que la cabecera contenga 'numero_registro_salida' o 'numero_registro_entrada'."}, status=400)

        # Verificar si existe un documento con el mismo número de registro
        numero_registro_completo = cabecera.get('numero_registro_entrada') or cabecera.get('numero_registro_salida')
        documento_existente = None
        
        if numero_registro_completo:
            documento_existente = Albaran.encontrar_documento_existente(numero_registro_completo)
            print(f"🔍 [BACKEND] Búsqueda de documento existente: {documento_existente}")

        # Crear el albarán y movimientos dentro de una transacción
        try:
            import os
            import time
            print("🔄 [BACKEND] Iniciando transacción...")
            with transaction.atomic():
                # Extraer datos de firmas para campos específicos
                firma_a_data = firmas.get('firma_a', {}) if isinstance(firmas, dict) else {}
                firma_b_data = firmas.get('firma_b', {}) if isinstance(firmas, dict) else {}
                
                # Preparar fechas con valores por defecto
                from django.utils import timezone
                fecha_informe = cabecera.get('fecha_informe') or timezone.now().date()
                fecha_transaccion = cabecera.get('fecha_transaccion_dma') or timezone.now().date()
                
                # Verificar si algún producto temporal tiene imagen de documento
                imagen_documento_temporal = None
                imagen_temporal_path = None
                imagen_temporal_name = None
                
                for p_temp in productos_temporales:
                    datos_add = getattr(p_temp, 'datos_adicionales', {})
                    if datos_add and datos_add.get('tiene_imagen_documento'):
                        imagen_temporal_path = datos_add.get('imagen_temporal_path')
                        imagen_temporal_name = datos_add.get('imagen_temporal_name')
                        print(f"🖼️ [BACKEND] Imagen temporal encontrada: {imagen_temporal_path}")
                        break
                
                if documento_existente:
                    # Es una página adicional de un documento existente
                    print(f"📄 [BACKEND] Creando página adicional para documento existente ID={documento_existente.id}")
                    # Verificar si ya existe una página adicional vacía reciente (últimos 5 minutos) para este documento
                    from django.utils import timezone
                    from datetime import timedelta
                    tiempo_limite = timezone.now() - timedelta(minutes=5)
                    # Buscar páginas vacías consultando directamente desde MovimientoProducto
                    paginas_con_movimientos = MovimientoProducto.objects.filter(
                        albaran__documento_principal=documento_existente,
                        albaran__created_at__gte=tiempo_limite
                    ).values_list('albaran_id', flat=True).distinct()
                    
                    paginas_vacias_recientes = Albaran.objects.filter(
                        documento_principal=documento_existente,
                        created_at__gte=tiempo_limite
                    ).exclude(id__in=paginas_con_movimientos)
                    
                    if paginas_vacias_recientes.exists():
                        # Reutilizar la página vacía existente en lugar de crear una nueva
                        albaran = paginas_vacias_recientes.first()
                        print(f"📄 [BACKEND] Reutilizando página vacía existente: {albaran.numero}")
                        # Actualizar los campos de la página existente
                        albaran.fecha = fecha_informe
                        albaran.fecha_informe = fecha_informe
                        albaran.fecha_transaccion = fecha_transaccion
                        albaran.accesorios = accesorios
                        albaran.equipos_prueba = equipos_prueba
                        albaran.observaciones_odmc = observaciones or ''
                        albaran.firma_a_nombre_apellidos = firma_a_data.get('nombre', '')
                        albaran.firma_a_cargo = firma_a_data.get('cargo', '')
                        albaran.firma_a_empleo_rango = firma_a_data.get('empleo_rango', '')
                        albaran.firma_b_nombre_apellidos = firma_b_data.get('nombre', '')
                        albaran.firma_b_cargo = firma_b_data.get('cargo', '')
                        albaran.firma_b_empleo_rango = firma_b_data.get('empleo_rango', '')
                        albaran.save()
                    else:
                        # Crear nueva página adicional
                        albaran = documento_existente.crear_pagina_adicional(
                            fecha=fecha_informe,
                            fecha_informe=fecha_informe,
                            fecha_transaccion=fecha_transaccion,
                            accesorios=accesorios,
                            equipos_prueba=equipos_prueba,
                            observaciones_odmc=observaciones or '',
                            # Campos de firma A
                            firma_a_nombre_apellidos=firma_a_data.get('nombre', ''),
                            firma_a_cargo=firma_a_data.get('cargo', ''),
                            firma_a_empleo_rango=firma_a_data.get('empleo_rango', ''),
                            # Campos de firma B
                            firma_b_nombre_apellidos=firma_b_data.get('nombre', ''),
                            firma_b_cargo=firma_b_data.get('cargo', ''),
                            firma_b_empleo_rango=firma_b_data.get('empleo_rango', ''),
                            created_by=request.user
                        )
                else:
                    # Es un documento nuevo (página principal)
                    print("🏗️ [BACKEND] Creando nuevo documento (página principal)...")
                    
                    # Normalizar tipo_documento desde tipo_transaccion
                    tipo_transaccion_raw = cabecera.get('tipo_transaccion', '')
                    tipo_documento_normalizado = None
                    
                    if tipo_transaccion_raw:
                        # Si es un objeto (checkboxes), extraer el primer tipo marcado
                        if isinstance(tipo_transaccion_raw, dict):
                            tipos = []
                            if tipo_transaccion_raw.get('transferencia'): tipos.append('TRANSFERENCIA')
                            if tipo_transaccion_raw.get('inventario'): tipos.append('INVENTARIO')
                            if tipo_transaccion_raw.get('destruccion'): tipos.append('DESTRUCCION')
                            if tipo_transaccion_raw.get('recibo_en_mano'): tipos.append('RECIBO_MANO')
                            if tipo_transaccion_raw.get('otro'): tipos.append('OTRO')
                            tipo_documento_normalizado = tipos[0] if tipos else 'INVENTARIO'
                        else:
                            # Si es string, normalizarlo
                            tipo_str = str(tipo_transaccion_raw).upper().replace(' ', '_')
                            # Mapear variaciones comunes
                            tipo_map = {
                                'RECIBO_EN_MANO': 'RECIBO_MANO',
                                'RECIBO EN MANO': 'RECIBO_MANO',
                                'RECIBOENMANO': 'RECIBO_MANO',
                            }
                            tipo_documento_normalizado = tipo_map.get(tipo_str, tipo_str)
                            # Truncar a 20 caracteres si es necesario
                            if len(tipo_documento_normalizado) > 20:
                                tipo_documento_normalizado = tipo_documento_normalizado[:20]
                    
                    # Si no se pudo determinar, usar INVENTARIO por defecto
                    if not tipo_documento_normalizado:
                        tipo_documento_normalizado = 'INVENTARIO'
                    
                    print(f"📋 [BACKEND] Tipo documento normalizado: '{tipo_documento_normalizado}' (desde: {tipo_transaccion_raw})")
                    
                    # Truncar campos numéricos a 20 caracteres si es necesario
                    numero_registro_entrada = str(cabecera.get('numero_registro_entrada', ''))[:20] if cabecera.get('numero_registro_entrada') else ''
                    numero_registro_salida = str(cabecera.get('numero_registro_salida', ''))[:20] if cabecera.get('numero_registro_salida') else ''
                    
                    albaran = Albaran.objects.create(
                        numero=numero[:20] if len(str(numero)) > 20 else numero,  # Truncar numero si es necesario
                        tipo_documento=tipo_documento_normalizado,
                        fecha=fecha_informe,
                        fecha_informe=fecha_informe,
                        fecha_transaccion=fecha_transaccion,
                        numero_registro_entrada=numero_registro_entrada,
                        numero_registro_salida=numero_registro_salida,
                        codigo_contabilidad=cabecera.get('codigos_contabilidad', ''),
                        empresa_origen_id=empresa_origen.get('id'),
                        empresa_destino_id=empresa_destino.get('id'),
                        direccion_transferencia='ENTRADA',  # Los AC-21 procesados desde tabla temporal son siempre de ENTRADA
                        accesorios=accesorios,
                        equipos_prueba=equipos_prueba,
                        observaciones_odmc=observaciones or '',
                        # Campos multipágina (por defecto página 1)
                        pagina_numero=1,
                        total_paginas=1,
                        # Campos de firma A
                        firma_a_nombre_apellidos=firma_a_data.get('nombre', ''),
                        firma_a_cargo=firma_a_data.get('cargo', ''),
                        firma_a_empleo_rango=firma_a_data.get('empleo_rango', ''),
                        # Campos de firma B
                        firma_b_nombre_apellidos=firma_b_data.get('nombre', ''),
                        firma_b_cargo=firma_b_data.get('cargo', ''),
                        firma_b_empleo_rango=firma_b_data.get('empleo_rango', ''),
                        created_by=request.user
                    )
                    
                print(f"✅ [BACKEND] Albarán creado: ID={albaran.id}, Número={albaran.numero}, Página={albaran.pagina_numero}/{albaran.total_paginas}")
                
                # Transferir imagen temporal al albarán si existe
                if imagen_temporal_path and os.path.exists(imagen_temporal_path):
                    print(f"🖼️ [BACKEND] Transfiriendo imagen temporal al albarán...")
                    
                    try:
                        from django.core.files import File
                        from django.core.files.base import ContentFile
                        import shutil
                        
                        # Leer el archivo temporal
                        with open(imagen_temporal_path, 'rb') as temp_file:
                            contenido_imagen = temp_file.read()
                        
                        # Crear nombre para el archivo final
                        extension = imagen_temporal_name.split('.')[-1] if '.' in imagen_temporal_name else 'jpg'
                        nombre_final = f"albaran_{albaran.id}_AC21_{int(time.time())}.{extension}"
                        
                        # Guardar imagen en el albarán
                        archivo_django = ContentFile(contenido_imagen, name=nombre_final)
                        albaran.imagen_documento.save(nombre_final, archivo_django, save=True)
                        
                        print(f"🖼️ [BACKEND] Imagen transferida exitosamente: {albaran.imagen_documento.name}")
                        
                        # Limpiar archivo temporal
                        os.remove(imagen_temporal_path)
                        print(f"🧹 [BACKEND] Archivo temporal eliminado: {imagen_temporal_path}")
                        
                    except Exception as e:
                        print(f"❌ [BACKEND] Error transfiriendo imagen: {str(e)}")
                        # Continuar sin fallar el proceso completo
                
                # Crear movimientos para cada producto temporal
                print("🔄 [BACKEND] Creando movimientos...")
                movimientos_creados = 0
                for p in productos_temporales:
                    print(f"📦 [BACKEND] Procesando producto temporal ID={p.id}, código={p.codigo_producto}")
                    
                    producto = CatalogoProducto.objects.filter(codigo_producto=p.codigo_producto).first()
                    print(f"🔍 [BACKEND] Búsqueda de producto: código={p.codigo_producto}, encontrado={producto is not None}, producto_id={producto.id if producto else 'N/A'}")
                    if not producto:
                        # Crear el producto automáticamente si no existe
                        print(f"➕ [BACKEND] Producto con código {p.codigo_producto} no encontrado. Creando nuevo producto en catálogo...")
                        descripcion = getattr(p, 'descripcion', '') or getattr(p, 'observaciones', '') or ''
                        producto, created = CatalogoProducto.objects.get_or_create(
                            codigo_producto=p.codigo_producto,
                            defaults={'descripcion': descripcion}
                        )
                        if created:
                            print(f"✅ [BACKEND] Producto creado: ID={producto.id}, código={producto.codigo_producto}")
                        else:
                            print(f"✅ [BACKEND] Producto encontrado después de creación: ID={producto.id}")
                    
                    # Actualizar CatalogoProducto.tipo con el tipo_producto de LineaTemporalProducto si existe
                    if p.tipo_producto:
                        producto.tipo = p.tipo_producto
                        producto.save()
                        print(f"✅ [BACKEND] CatalogoProducto {p.codigo_producto} actualizado con tipo {p.tipo_producto.nombre}")
                        
                    existe = MovimientoProducto.objects.filter(
                        albaran=albaran,
                        producto=producto,
                        numero_serie=p.numero_serie
                    ).exists()
                    print(f"🔍 [BACKEND] Verificación duplicado: albaran_id={albaran.id}, producto_id={producto.id}, serie={p.numero_serie}, existe={existe}")
                    if existe:
                        print(f"⚠️ [BACKEND] Movimiento duplicado para producto {producto.id}, serie {p.numero_serie}, albarán {albaran.id}. Se omite.")
                        continue
                    
                    print(f"✅ [BACKEND] Producto encontrado y sin duplicados. Continuando con creación de movimiento...")
                    
                    # Normalizar tipo_movimiento igual que tipo_documento
                    tipo_movimiento_normalizado = tipo_documento_normalizado if 'tipo_documento_normalizado' in locals() else 'INVENTARIO'
                    print(f"📋 [BACKEND] Tipo movimiento normalizado: {tipo_movimiento_normalizado}")
                    if len(tipo_movimiento_normalizado) > 20:
                        tipo_movimiento_normalizado = tipo_movimiento_normalizado[:20]
                    
                    # Obtener cc desde datos_adicionales (del OCR del AC21)
                    datos_add = getattr(p, 'datos_adicionales', {}) or {}
                    cc_del_ocr_raw = datos_add.get('cc', '')
                    cc_del_ocr = None  # Valor por defecto: NULL (campo puede estar vacío)
                    
                    # Si el campo viene con valor, intentar convertirlo a entero
                    if cc_del_ocr_raw is not None and cc_del_ocr_raw != '':
                        if isinstance(cc_del_ocr_raw, str):
                            cc_str = cc_del_ocr_raw.strip()
                            if cc_str:
                                try:
                                    cc_del_ocr = int(float(cc_str))
                                except (ValueError, TypeError):
                                    cc_del_ocr = None  # No convertible, dejar como NULL
                            else:
                                cc_del_ocr = None  # Cadena vacía - dejar como NULL
                        elif isinstance(cc_del_ocr_raw, (int, float)):
                            cc_del_ocr = int(cc_del_ocr_raw)
                    # Si es None o '', cc_del_ocr ya está como None
                    
                    # Determinar estados anterior y nuevo basándose en la dirección de transferencia
                    inventario_existente = InventarioProducto.objects.filter(
                        producto=producto,
                        numero_serie=p.numero_serie
                    ).first()
                    estado_anterior = inventario_existente.estado if inventario_existente else 'inactivo'
                    
                    # Determinar estado_nuevo según dirección de transferencia
                    if albaran.direccion_transferencia == 'SALIDA':
                        estado_nuevo = 'inactivo'
                    elif albaran.direccion_transferencia == 'ENTRADA':
                        estado_nuevo = 'activo'
                    else:
                        # Por defecto, si no hay dirección, usar 'activo' para inventarios
                        estado_nuevo = 'activo'
                    
                    print(f"🔄 [BACKEND] Creando MovimientoProducto: producto={producto.codigo_producto}, serie={p.numero_serie}, estado_anterior={estado_anterior}, estado_nuevo={estado_nuevo}")
                    try:
                        movimiento = MovimientoProducto.objects.create(
                            albaran=albaran,
                            producto=producto,
                            numero_serie=p.numero_serie,
                            descripcion=producto.descripcion,
                            tipo_movimiento=tipo_movimiento_normalizado,
                            cantidad=getattr(p, 'cantidad', 1),
                            cc=cc_del_ocr,  # Usar cc del OCR desde datos_adicionales
                            observaciones=getattr(p, 'observaciones', ''),
                            estado_anterior=estado_anterior,
                            estado_nuevo=estado_nuevo
                        )
                        movimientos_creados += 1
                        print(f"✅ [BACKEND] Movimiento creado ID={movimiento.id} para producto {producto.codigo_producto} con cc={cc_del_ocr}, estado_anterior={estado_anterior}, estado_nuevo={estado_nuevo}")
                        
                        # Verificar si el inventario se creó/actualizó correctamente
                        inventario_verificado = InventarioProducto.objects.filter(
                            producto=producto,
                            numero_serie=p.numero_serie
                        ).first()
                        if inventario_verificado:
                            print(f"✅ [BACKEND] Inventario verificado: ID={inventario_verificado.id}, estado={inventario_verificado.estado}")
                        else:
                            print(f"⚠️ [BACKEND] ADVERTENCIA: Inventario NO encontrado después de crear movimiento")
                    except Exception as e:
                        import traceback
                        print(f"❌ [BACKEND] ERROR al crear movimiento: {str(e)}")
                        traceback.print_exc()
                        raise  # Re-lanzar para que la transacción haga rollback
                
                print(f"🎉 [BACKEND] {movimientos_creados} movimientos creados")
                
                # Marcar productos temporales como procesados
                productos_temporales.update(procesado=True)
                print("✅ [BACKEND] Productos temporales marcados como procesados")
                
                # 🔹 LIMPIAR registros no procesados restantes del usuario
                # Esto elimina cualquier registro "huérfano" que pueda quedar de procesamientos anteriores
                registros_restantes = LineaTemporalProducto.objects.filter(
                    usuario=request.user,
                    procesado=False
                )
                count_restantes = registros_restantes.count()
                if count_restantes > 0:
                    print(f"🧹 [BACKEND] Eliminando {count_restantes} registros temporales no procesados restantes del usuario")
                    registros_restantes.delete()
                
                print(f"🎉 [BACKEND] procesar COMPLETADO - Albarán ID={albaran.id}")
                # Verificar si hay más productos temporales no procesados del mismo usuario
                # (podrían ser de otra página del mismo PDF)
                productos_restantes = LineaTemporalProducto.objects.filter(
                    usuario=request.user,
                    procesado=False
                ).count()
                
                # Limpiar páginas vacías del documento (sin movimientos) que no sean la página principal
                if albaran.documento_principal or documento_existente:
                    doc_principal = albaran.obtener_documento_principal
                    # Buscar páginas vacías consultando directamente desde MovimientoProducto
                    paginas_con_movimientos = MovimientoProducto.objects.filter(
                        albaran__documento_principal=doc_principal
                    ).values_list('albaran_id', flat=True).distinct()
                    
                    paginas_vacias = Albaran.objects.filter(
                        documento_principal=doc_principal
                    ).exclude(id__in=paginas_con_movimientos)
                    
                    # No eliminar la página que acabamos de crear si tiene movimientos
                    if MovimientoProducto.objects.filter(albaran=albaran).exists():
                        paginas_vacias = paginas_vacias.exclude(id=albaran.id)
                    
                    if paginas_vacias.exists():
                        print(f"🧹 [BACKEND] Eliminando {paginas_vacias.count()} página(s) vacía(s) del documento {doc_principal.numero}")
                        paginas_vacias.delete()
                        # Actualizar total_paginas después de eliminar páginas vacías
                        doc_principal.actualizar_total_paginas()
                
                return Response({
                    "detail": "Albarán creado correctamente.", 
                    "albaran_id": albaran.id,
                    "albaran_numero": albaran.numero,
                    "es_pagina_adicional": albaran.documento_principal is not None,
                    "total_paginas": albaran.obtener_documento_principal.total_paginas if albaran.documento_principal else 1,
                    "hay_mas_productos_temporales": productos_restantes > 0
                }, status=201)
        except Exception as e:
            import traceback
            print(f"❌ [BACKEND] ERROR INESPERADO en procesar. Usuario: {request.user.username}, Albarán: {numero}. Error: {str(e)}")
            traceback.print_exc()
            return Response({"detail": f"Error procesando el albarán: {str(e)}"}, status=500)

class InventarioProductoViewSet(viewsets.ModelViewSet):
    queryset = InventarioProducto.objects.select_related(
        'producto', 
        'producto__tipo',
        'ultimo_movimiento',
        'ultimo_movimiento__albaran'
    ).all()
    serializer_class = InventarioProductoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        estado = self.request.query_params.get('estado', None)
        ubicacion = self.request.query_params.get('ubicacion', None)
        numero_serie = self.request.query_params.get('numero_serie', None)
        codigo_producto = self.request.query_params.get('codigo_producto', None)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        if ubicacion:
            queryset = queryset.filter(ubicacion=ubicacion)
        if numero_serie:
            queryset = queryset.filter(numero_serie__icontains=numero_serie)
        if codigo_producto:
            queryset = queryset.filter(producto__codigo_producto__icontains=codigo_producto)
            
        return queryset

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """
        Devuelve un resumen del inventario con el total de productos y su estado
        """
        resumen = {
            'total': self.get_queryset().count(),
            'en_custodia': self.get_queryset().filter(estado='activo').count(),
            'fuera_custodia': self.get_queryset().filter(estado='inactivo').count(),
        }
        
        return Response(resumen)

    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        """
        Devuelve el historial de movimientos de un producto específico
        """
        inventario = self.get_object()
        movimientos = MovimientoProducto.objects.filter(
            producto=inventario.producto,
            numero_serie=inventario.numero_serie
        ).order_by('-fecha')
        
        serializer = MovimientoProductoSerializer(movimientos, many=True)
        return Response(serializer.data)

class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Por defecto, solo mostrar empresas activas
        return Empresa.objects.filter(activa=True)

    def create(self, request, *args, **kwargs):
        print(f"🏢 [BACKEND] Creando empresa - request.data: {request.data}")
        print(f"🏢 [BACKEND] Content-Type: {request.content_type}")
        
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print(f"❌ [BACKEND] Errores de validación: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        print(f"✅ [BACKEND] Empresa creada: {serializer.data}")
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        empresa = self.get_object()
        empresa.activa = False
        empresa.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CryptocustodioViewSet(viewsets.ModelViewSet):
    queryset = Cryptocustodio.objects.all()
    serializer_class = CryptocustodioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Cryptocustodio.objects.select_related('empresa')
        empresa_id = self.request.query_params.get('empresa')
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)
        return qs.order_by('empresa', 'nombre_apellidos')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cambiar_password(request):
    """
    Endpoint para cambiar la contraseña del usuario
    Maneja tanto cambio obligatorio (primer login) como cambio voluntario
    """
    user = request.user
    data = request.data
    
    # Validar campos requeridos
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        return Response({
            'error': 'Todos los campos son requeridos'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validar que las contraseñas nuevas coincidan
    if new_password != confirm_password:
        return Response({
            'error': 'Las contraseñas nuevas no coinciden'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validar contraseña actual
    if not authenticate(username=user.username, password=current_password):
        return Response({
            'error': 'Contraseña actual incorrecta'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validar longitud mínima de la nueva contraseña
    if len(new_password) < 8:
        return Response({
            'error': 'La nueva contraseña debe tener al menos 8 caracteres'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Cambiar contraseña
        user.set_password(new_password)
        user.save()
        
        # Actualizar must_change_password en ambos perfiles (productos y HPS)
        password_was_required = False
        
        # Actualizar perfil de productos (si existe)
        if hasattr(user, 'profile') and user.profile.must_change_password:
            user.profile.must_change_password = False
            user.profile.save()
            password_was_required = True
        
        # Actualizar perfil HPS (si existe) - usar el mismo sistema que HPS System
        if hasattr(user, 'hps_profile'):
            if user.hps_profile.must_change_password or user.hps_profile.is_temp_password:
                user.hps_profile.must_change_password = False
                user.hps_profile.is_temp_password = False
                user.hps_profile.save(update_fields=['must_change_password', 'is_temp_password'])
                password_was_required = True
        
        if password_was_required:
            return Response({
                'message': 'Contraseña cambiada exitosamente. Ya puedes acceder al sistema.',
                'password_change_required': False
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'Contraseña cambiada exitosamente'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({
            'error': f'Error al cambiar la contraseña: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil_usuario(request):
    """
    Obtener información del perfil del usuario actual
    """
    try:
        # Asegurar que el usuario tiene perfil
        if not hasattr(request.user, 'profile'):
            UserProfile.objects.create(user=request.user)
        
        serializer = UserProfileSerializer(request.user.profile)
        return Response(serializer.data)
        
    except Exception as e:
        return Response({
            'error': f'Error al obtener perfil: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



