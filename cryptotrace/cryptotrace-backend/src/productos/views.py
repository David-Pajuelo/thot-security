import logging
import requests
from rest_framework import viewsets, status
from django.db.models import OuterRef, Exists, Count, Subquery, Value
from django.db.models.functions import Coalesce
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import HttpResponse
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import (
    CatalogoProducto, Albaran, MovimientoProducto, TipoProducto, LineaTemporalProducto, InventarioProducto, Empresa, UserProfile
)
from .serializers import (
    CatalogoProductoSerializer, AlbaranSerializer, MovimientoProductoSerializer,
    TipoProductoSerializer, LineaTemporalProductoSerializer, InventarioProductoSerializer,
    EmpresaSerializer, MovimientoProductoBasicoSerializer, CustomTokenObtainPairSerializer, UserProfileSerializer
)
from django.db import models
import json

# Configurar logger
logger = logging.getLogger(__name__)

# 🔹 Vista personalizada para JWT con información de usuario
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para generar tokens JWT con información adicional del usuario
    """
    serializer_class = CustomTokenObtainPairSerializer

# 🔹 ModelViewSets para los modelos principales
class TipoProductoViewSet(viewsets.ModelViewSet):
    queryset = TipoProducto.objects.all()
    serializer_class = TipoProductoSerializer

class CatalogoProductoViewSet(viewsets.ModelViewSet):
    queryset = CatalogoProducto.objects.all()
    serializer_class = CatalogoProductoSerializer
    permission_classes = [IsAuthenticated]
    
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

    def create(self, request, *args, **kwargs):
        print(f"DEBUG AC21: request.data={request.data}")
        cabecera = request.data.get('cabecera', {})
        def get_first_nonempty(*args):
            for v in args:
                if v is not None and str(v).strip() != '':
                    return v
            return None
        numero = get_first_nonempty(
            request.data.get('numero'),
            request.data.get('numero_registro_entrada'),
            request.data.get('numero_registro_salida'),
            cabecera.get('numero'),
            cabecera.get('numero_registro_entrada'),
            cabecera.get('numero_registro_salida')
        )
        print(f"DEBUG AC21: numero extraído (robusto)={numero}")
        if not numero:
            return Response({'error': 'No se encontró número de registro en el AC21. El payload debe incluir un campo "numero_registro_salida" o equivalente.'}, status=status.HTTP_400_BAD_REQUEST)
        # Si el frontend pide agregar productos a un albarán existente
        if request.data.get('modo') == 'agregar_a_existente':
            albaran = Albaran.objects.filter(
                models.Q(numero=numero) | models.Q(numero_registro_salida=numero)
            ).first()
            if not albaran:
                return Response({'error': 'No existe un albarán con ese número'}, status=status.HTTP_404_NOT_FOUND)
            articulos = request.data.get('articulos', [])
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
        tipo_documento = request.data.get('tipo_documento') or cabecera.get('tipo_transaccion')
        direccion_transferencia = request.data.get('direccion_transferencia', 'ENTRADA')
        
        # Solo bloquear AC21s de ENTRADA - las SALIDAS pueden crearse directamente
        if (tipo_documento and str(tipo_documento).upper() in ['TRANSFERENCIA', 'RECIBO_MANO', 'DESTRUCCION', 'OTRO'] 
            and direccion_transferencia == 'ENTRADA'):
            return Response({
                'error': 'El alta de AC21 debe realizarse a través de la gestión temporal (línea temporal) para tipificación de productos. Sube el AC21, valida los artículos y continúa el flujo en la gestión temporal.'
            }, status=status.HTTP_400_BAD_REQUEST)
        # --- Fin bloqueo ---
            albaran_existente = Albaran.objects.filter(
                models.Q(numero=numero) | models.Q(numero_registro_salida=numero)
            ).first()
            if albaran_existente:
                movimientos = MovimientoProducto.objects.filter(albaran=albaran_existente)
                productos_existentes = MovimientoProductoBasicoSerializer(movimientos, many=True).data
                return Response({
                    "success": False,
                    "message": "Ya existe un albarán con este número.",
                    "productos_existentes": productos_existentes,
                    "albaran_id": albaran_existente.id
                }, status=status.HTTP_409_CONFLICT)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
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
                        total_paginas_actual = documento_principal_ref.total_paginas or 1
                        nueva_pagina = total_paginas_actual + 1
                        numero = f"{numero_existente}-P{nueva_pagina}"
                        
                        print(f"[AlbaranViewSet] Número generado para página adicional: {numero}")
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
                    documento_principal_ref.total_paginas = nueva_pagina
                    documento_principal_ref.save()
                    print(f"[AlbaranViewSet] Actualizado total_paginas del documento principal a: {nueva_pagina}")
                elif not es_pagina_adicional:
                    # Para documentos principales, establecer total_paginas = 1 inicialmente
                    albaran.total_paginas = 1
                    albaran.save()
                articulos = self.request.data.get('articulos', [])
                if (albaran.tipo_documento in ['TRANSFERENCIA', 'RECIBO_MANO', 'DESTRUCCION', 'OTRO'] 
                    and albaran.direccion_transferencia == 'ENTRADA'):
                    # AC21s de ENTRADA van a gestión temporal
                    for articulo in articulos:
                        LineaTemporalProducto.objects.create(
                            usuario=self.request.user,
                            numero_albaran=albaran.numero,
                            descripcion=articulo.get('descripcion', ''),
                            numero_serie=articulo.get('numero_serie_inicio') or articulo.get('numero_serie_fin', ''),
                            observaciones=articulo.get('observaciones', '')
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
                            movimiento.cc = mov_data['cc']
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
                            
                            MovimientoProducto.objects.create(
                                albaran=albaran,
                                producto=producto,
                                numero_serie=mov_data.get('numero_serie', ''),
                                descripcion=mov_data.get('descripcion', ''),
                                cantidad=mov_data.get('cantidad', 1),
                                cc=mov_data.get('cc', 1),
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
            
        # Buscar albarán por numero o numero_registro_salida
        albaran = Albaran.objects.filter(
            models.Q(numero=numero) | models.Q(numero_registro_salida=numero)
        ).first()
        
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
                # Para documentos multipágina, organizar productos por página manteniendo la estructura original
                productos_por_pagina = []
                accesorios_por_pagina = []
                equipos_por_pagina = []
                
                for pagina in todas_las_paginas:
                    movimientos_pagina = MovimientoProducto.objects.filter(albaran=pagina).select_related('producto')
                    print(f"📄 [PDF] Página {pagina.pagina_numero}: {movimientos_pagina.count()} productos")
                    
                    productos_pagina = []
                    for mov in movimientos_pagina:
                        productos_pagina.append({
                            'codigo_producto': mov.producto.codigo_producto,
                            'cantidad': mov.cantidad or 1,
                            'descripcion_producto': mov.descripcion or mov.producto.descripcion,
                            'numero_serie': mov.numero_serie or 'N/A',
                            'observaciones': mov.observaciones or ''
                        })
                    productos_por_pagina.append(productos_pagina)
                    
                    # Recopilar accesorios y equipos de cada página
                    accesorios_pagina = self._procesar_accesorios(pagina.accesorios)
                    equipos_pagina = self._procesar_equipos_prueba(pagina.equipos_prueba)
                    accesorios_por_pagina.append(accesorios_pagina)
                    equipos_por_pagina.append(equipos_pagina)
                
                # Combinar todos los productos para enviar al PDF generator
                todos_los_productos = []
                for productos_pagina in productos_por_pagina:
                    todos_los_productos.extend(productos_pagina)
                
                # Usar datos de la primera página para información general
                pagina_principal = todas_las_paginas[0]
                total_paginas = len(todas_las_paginas)
                pagina_actual = 1  # Para documentos multipágina, siempre empezar desde 1 para que el PDF generator genere todas las páginas
                
                print(f"📄 [PDF] Total productos combinados: {len(todos_los_productos)}")
                print(f"📄 [PDF] Productos por página: {[len(p) for p in productos_por_pagina]}")
                print(f"📄 [PDF] Accesorios por página: {[len(a) for a in accesorios_por_pagina]}")
                print(f"📄 [PDF] Equipos por página: {[len(e) for e in equipos_por_pagina]}")
                
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
                'total_paginas': total_paginas,
                'productos_por_pagina_estructura': [len(p) for p in productos_por_pagina],  # Información de estructura original
                'accesorios_por_pagina': accesorios_por_pagina,  # Accesorios específicos de cada página
                'equipos_por_pagina': equipos_por_pagina,  # Equipos específicos de cada página
                'flags': {
                    'firme_y_devuelva': False,  # TODO: mapear estos campos cuando estén en el modelo
                    'para_su_archivo': True
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
                # Agregar accesorios y equipos de prueba
                'accesorios': self._procesar_accesorios(pagina_principal.accesorios),
                'equipos_prueba': self._procesar_equipos_prueba(pagina_principal.equipos_prueba)
            }

            print(f"📄 [PDF] Enviando datos al servicio PDF: {len(todos_los_productos)} productos, página {pagina_actual} de {total_paginas}")

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

    @action(detail=True, methods=['get'], url_path='paginas', permission_classes=[IsAuthenticated])
    def obtener_paginas(self, request, pk=None):
        """
        Obtiene todas las páginas de un documento multipágina
        """
        albaran = self.get_object()
        
        # Obtener todas las páginas del documento
        todas_las_paginas = albaran.obtener_todas_las_paginas()
        
        # Serializar y devolver directamente el array de páginas
        serializer = self.get_serializer(todas_las_paginas, many=True)
        return Response(serializer.data)

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
        with transaction.atomic():
            movimientos = list(MovimientoProducto.objects.filter(albaran=instance))
            for mov in movimientos:
                producto = mov.producto
                numero_serie = mov.numero_serie
                # Buscar movimientos anteriores a este albarán para este producto/serie
                movimientos_anteriores = MovimientoProducto.objects.filter(
                    producto=producto,
                    numero_serie=numero_serie
                ).exclude(albaran=instance).order_by('-fecha')
                inventario = InventarioProducto.objects.filter(producto=producto, numero_serie=numero_serie).first()
                if instance.tipo_documento == 'INVENTARIO':
                    # Si no hay movimientos anteriores, eliminar del inventario
                    if not movimientos_anteriores.exists():
                        if inventario:
                            inventario.delete()
                        # Además, si el producto del catálogo fue creado por este albarán y no tiene otros movimientos, eliminarlo
                        otros_movimientos = MovimientoProducto.objects.filter(producto=producto).exclude(albaran=instance)
                        if not otros_movimientos.exists():
                            producto.delete()
                    else:
                        mov_ant = movimientos_anteriores.first()
                        if inventario:
                            inventario.estado = mov_ant.estado_nuevo
                            inventario.ultimo_movimiento = mov_ant
                            inventario.ultima_actualizacion = timezone.now()
                            inventario.save()
                elif instance.tipo_documento == 'TRANSFERENCIA':
                    if instance.direccion_transferencia == 'ENTRADA':
                        # AC21 de entrada: restaurar estado anterior o poner inactivo
                        if movimientos_anteriores.exists():
                            mov_ant = movimientos_anteriores.first()
                            if inventario:
                                inventario.estado = mov_ant.estado_nuevo
                                inventario.ultimo_movimiento = mov_ant
                                inventario.ultima_actualizacion = timezone.now()
                                inventario.save()
                        else:
                            if inventario:
                                inventario.estado = 'inactivo'
                                inventario.ultimo_movimiento = None
                                inventario.ultima_actualizacion = timezone.now()
                                inventario.save()
                    elif instance.direccion_transferencia == 'SALIDA':
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
        base_queryset = LineaTemporalProducto.objects.all() if user.is_superuser else LineaTemporalProducto.objects.filter(usuario=user)
        
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
            return Response({"error": "No se encontró número de registro en el AC21"}, status=400)

        if not articulos:
            print("❌ [BACKEND] ERROR: No hay artículos")
            return Response({"error": "No se proporcionaron artículos"}, status=400)

        # Crear registros temporales
        registros_creados = []
        print("🔄 [BACKEND] Creando registros temporales...")
        
        for i, articulo in enumerate(articulos):
            print(f"📦 [BACKEND] Procesando artículo {i+1}/{len(articulos)}: {articulo}")
            
            # Preparar datos adicionales para el campo JSON
            datos_adicionales = {
                'cabecera': cabecera,
                'empresa_origen': empresa_origen,
                'empresa_destino': empresa_destino,
                'accesorios': accesorios,
                'equipos_prueba': equipos_prueba,
                'firmas': firmas,
                'observaciones_generales': observaciones,
                'tiene_imagen_documento': imagen_documento is not None
            }
            
            # Extraer número de serie: puede venir como 'numero_serie', 'numero_serie_inicio' o 'numero_serie_fin'
            numero_serie = (
                articulo.get('numero_serie') or 
                articulo.get('numero_serie_inicio') or 
                articulo.get('numero_serie_fin') or 
                ''
            )
            
            registro = LineaTemporalProducto.objects.create(
                usuario=request.user,
                numero_albaran=numero_albaran,
                codigo_producto=articulo.get('codigo', ''),
                descripcion=articulo.get('descripcion', ''),
                numero_serie=numero_serie,
                cantidad=articulo.get('cantidad', 1),
                observaciones=articulo.get('observaciones', ''),
                cc=articulo.get('cc', 1),
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

        # 🔹 Obtener la descripción de un producto dentro del grupo
        descripcion_subquery = self.get_queryset().filter(
            codigo_producto=OuterRef("codigo_producto")
        ).values("descripcion")[:1]

        # 🔹 Obtener el tipo de `Producto`
        tipo_subquery = CatalogoProducto.objects.filter(
            codigo_producto=OuterRef("codigo_producto"),
            tipo__isnull=False
        ).values("tipo__nombre")[:1]

        productos_agrupados = (
            self.get_queryset()
            .values("codigo_producto")
            .annotate(
                cantidad=Count("codigo_producto"),
                tipificado=Exists(CatalogoProducto.objects.filter(
                    codigo_producto=OuterRef("codigo_producto"), tipo__isnull=False
                )),
                descripcion=Subquery(descripcion_subquery),
                tipo=Coalesce(Subquery(tipo_subquery), None)  # Evita valores nulos
            )
            .order_by("codigo_producto")
        )

        # 🔹 Obtener todos los tipos de producto disponibles
        tipos_disponibles = TipoProducto.objects.values_list("nombre", flat=True)

        return Response({
            "productos": list(productos_agrupados),
            "tipos_disponibles": list(tipos_disponibles)
        }, status=status.HTTP_200_OK)
    


    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
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
        
        # Solo el usuario puede limpiar sus propios registros, excepto superusuarios
        if request.user.is_superuser:
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
        productos_temporales = self.get_queryset().filter(procesado=False, usuario=request.user)
        print(f"📦 [BACKEND] Productos temporales encontrados: {productos_temporales.count()}")

        if not productos_temporales.exists():
            print("❌ [BACKEND] ERROR: No hay productos temporales")
            return Response({"detail": "No hay productos temporales para procesar."}, status=400)

        # Extraer campos generales del primer producto temporal (todos comparten cabecera, empresas, etc.)
        p0 = productos_temporales.first()
        print(f"📋 [BACKEND] Primer producto temporal: ID={p0.id}")
        
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
        numero = get_first_nonempty(
            cabecera.get('numero'),
            cabecera.get('numero_registro_entrada'),
            cabecera.get('numero_registro_salida'),
        )
        print(f"📋 [BACKEND] Número extraído: {numero}")
        
        if not numero:
            print("❌ [BACKEND] ERROR: No se encontró número de registro")
            return Response({"detail": "No se encontró número de registro en el AC21."}, status=400)

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
                    albaran = documento_existente.crear_pagina_adicional(
                        fecha=fecha_informe,
                        fecha_informe=fecha_informe,
                        fecha_transaccion=fecha_transaccion,
                        accesorios=accesorios,
                        equipos_prueba=equipos_prueba,
                        observaciones_odmc=observaciones,
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
                    albaran = Albaran.objects.create(
                        numero=numero,
                        tipo_documento=cabecera.get('tipo_transaccion', ''),
                        fecha=fecha_informe,
                        fecha_informe=fecha_informe,
                        fecha_transaccion=fecha_transaccion,
                        numero_registro_entrada=cabecera.get('numero_registro_entrada', ''),
                        numero_registro_salida=cabecera.get('numero_registro_salida', ''),
                        codigo_contabilidad=cabecera.get('codigos_contabilidad', ''),
                        empresa_origen_id=empresa_origen.get('id'),
                        empresa_destino_id=empresa_destino.get('id'),
                        direccion_transferencia='ENTRADA',  # Los AC-21 procesados desde tabla temporal son siempre de ENTRADA
                        accesorios=accesorios,
                        equipos_prueba=equipos_prueba,
                        observaciones_odmc=observaciones,
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
                    if not producto:
                        print(f"⚠️ [BACKEND] Producto con código {p.codigo_producto} no encontrado. Se omite movimiento.")
                        continue
                        
                    existe = MovimientoProducto.objects.filter(
                        albaran=albaran,
                        producto=producto,
                        numero_serie=p.numero_serie
                    ).exists()
                    if existe:
                        print(f"⚠️ [BACKEND] Movimiento duplicado para producto {producto.id}, serie {p.numero_serie}, albarán {albaran.id}. Se omite.")
                        continue
                    
                    MovimientoProducto.objects.create(
                        albaran=albaran,
                        producto=producto,
                        numero_serie=p.numero_serie,
                        descripcion=producto.descripcion,
                        tipo_movimiento=cabecera.get('tipo_transaccion', 'INVENTARIO'),
                        cantidad=getattr(p, 'cantidad', 1),
                        cc=getattr(p, 'cc', 1),
                        observaciones=getattr(p, 'observaciones', '')
                    )
                    movimientos_creados += 1
                    print(f"✅ [BACKEND] Movimiento creado para producto {producto.codigo_producto}")
                
                print(f"🎉 [BACKEND] {movimientos_creados} movimientos creados")
                
                # Marcar productos temporales como procesados
                productos_temporales.update(procesado=True)
                print("✅ [BACKEND] Productos temporales marcados como procesados")
                
                print(f"🎉 [BACKEND] procesar COMPLETADO - Albarán ID={albaran.id}")
                return Response({"detail": "Albarán creado correctamente.", "albaran_id": albaran.id}, status=201)
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

    def destroy(self, request, *args, **kwargs):
        empresa = self.get_object()
        empresa.activa = False
        empresa.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

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
        
        # Si el usuario tenía que cambiar la contraseña, marcar como completado
        if hasattr(user, 'profile') and user.profile.must_change_password:
            user.profile.must_change_password = False
            user.profile.save()
            
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



