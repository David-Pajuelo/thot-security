from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CatalogoProducto, Albaran, MovimientoProducto, TipoProducto, LineaTemporalProducto, InventarioProducto, Empresa, UserProfile
from django.contrib.auth.models import User

class TipoProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoProducto
        fields = '__all__'

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado para incluir información adicional del usuario en el JWT token.
    Permite autenticar con email o username.
    """
    username = serializers.CharField(required=False)  # Hacer username opcional
    
    def validate(self, attrs):
        """
        Sobrescribir validate para permitir autenticación con email o username
        """
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        username_or_email = attrs.get('username', '').strip()
        password = attrs.get('password', '')
        
        if not username_or_email:
            raise serializers.ValidationError({
                'username': 'Este campo es requerido.'
            })
        
        # Intentar buscar usuario por username primero
        user = None
        try:
            user = User.objects.get(username=username_or_email)
        except User.DoesNotExist:
            # Si no se encuentra por username, intentar buscar por email
            try:
                user = User.objects.get(email=username_or_email)
            except User.DoesNotExist:
                # Usuario no encontrado, pero validar contraseña para evitar timing attacks
                from django.contrib.auth.hashers import check_password
                # Hash dummy para mantener tiempo constante
                dummy_hash = 'pbkdf2_sha256$600000$dummy$dummyhash'
                check_password(password, dummy_hash)
                raise serializers.ValidationError({
                    'username': 'Usuario o email no encontrado.',
                    'password': 'Credenciales inválidas.'
                })
        
        # Verificar contraseña
        if not user.check_password(password):
            raise serializers.ValidationError({
                'password': 'Contraseña incorrecta.'
            })
        
        # Verificar que el usuario esté activo
        if not user.is_active:
            raise serializers.ValidationError({
                'username': 'Este usuario está inactivo.'
            })
        
        # Actualizar attrs con el username correcto para el resto del proceso
        attrs['username'] = user.username
        
        # Llamar al método validate del padre con los attrs actualizados
        return super().validate(attrs)
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Agregar campos personalizados al token
        token['is_superuser'] = user.is_superuser
        token['username'] = user.username
        token['email'] = user.email  # Agregar email al token
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        
        # Agregar must_change_password desde el perfil HPS (prioridad) o perfil productos
        # Usar la misma lógica que HPS System: is_temp_password o must_change_password
        must_change_password = False
        role = None
        team_id = None
        
        # Prioridad: usar perfil HPS si existe (mismo sistema que HPS System)
        if hasattr(user, 'hps_profile') and user.hps_profile:
            # Si tiene contraseña temporal O debe cambiar contraseña, marcar como requerido
            must_change_password = user.hps_profile.is_temp_password or user.hps_profile.must_change_password
            # Agregar role y team_id desde el perfil HPS
            if user.hps_profile.role:
                role = user.hps_profile.role.name
            if user.hps_profile.team:
                team_id = str(user.hps_profile.team.id)
        elif hasattr(user, 'profile'):
            # Fallback: usar perfil de productos si no hay perfil HPS
            must_change_password = user.profile.must_change_password
        
        token['must_change_password'] = must_change_password
        if role:
            token['role'] = role
        if team_id:
            token['team_id'] = team_id
        
        return token

class CatalogoProductoSerializer(serializers.ModelSerializer):
    tipo_nombre = serializers.CharField(source="tipo.nombre", read_only=True)

    class Meta:
        model = CatalogoProducto
        fields = ["id", "codigo_producto", "descripcion", "tipo", "tipo_nombre"]

class MovimientoProductoBasicoSerializer(serializers.ModelSerializer):
    """Serializador básico para MovimientoProducto sin relaciones profundas"""
    producto_codigo = serializers.CharField(source='producto.codigo_producto', read_only=True)
    producto_descripcion = serializers.CharField(source='producto.descripcion', read_only=True)
    albaran_numero = serializers.CharField(source='albaran.numero', read_only=True)
    albaran_id = serializers.IntegerField(source='albaran.id', read_only=True)
    tipo_movimiento_display = serializers.CharField(source='get_tipo_movimiento_display', read_only=True)
    
    # Campos multipágina del albarán
    pagina_origen = serializers.IntegerField(source='albaran.pagina_numero', read_only=True)
    pagina_id = serializers.IntegerField(source='albaran.id', read_only=True)

    class Meta:
        model = MovimientoProducto
        fields = [
            'id', 'producto_codigo', 'producto_descripcion', 'numero_serie', 'descripcion',
            'albaran_numero', 'albaran_id', 'fecha', 'tipo_movimiento', 'tipo_movimiento_display',
            'estado_anterior', 'estado_nuevo', 'cantidad', 'cc', 'observaciones',
            # Campos multipágina
            'pagina_origen', 'pagina_id'
        ]

class InventarioProductoSerializer(serializers.ModelSerializer):
    codigo_producto = serializers.CharField(source='producto.codigo_producto', read_only=True)
    descripcion = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    tipo_nombre = serializers.CharField(source='producto.tipo.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    ultimo_movimiento_info = MovimientoProductoBasicoSerializer(source='ultimo_movimiento', read_only=True)

    class Meta:
        model = InventarioProducto
        fields = [
            'id', 'codigo_producto', 'descripcion', 'tipo_nombre',
            'numero_serie', 'estado', 'estado_display', 'ubicacion',
            'ultima_actualizacion', 'ultimo_movimiento_info', 'notas'
        ]

class MovimientoProductoSerializer(MovimientoProductoBasicoSerializer):
    """Serializador completo para MovimientoProducto con todas las relaciones"""
    inventario_actual = InventarioProductoSerializer(read_only=True)

    class Meta(MovimientoProductoBasicoSerializer.Meta):
        fields = MovimientoProductoBasicoSerializer.Meta.fields + ['inventario_actual']

class EmpresaSerializer(serializers.ModelSerializer):
    direccion_completa = serializers.CharField(read_only=True)

    class Meta:
        model = Empresa
        fields = [
            'id', 'nombre', 'direccion', 'ciudad', 'codigo_postal', 
            'provincia', 'numero_odmc', 'direccion_completa',
            'activa'
        ]

class AlbaranSerializer(serializers.ModelSerializer):
    empresa_origen_info = EmpresaSerializer(source='empresa_origen', read_only=True)
    empresa_destino_info = EmpresaSerializer(source='empresa_destino', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    tipo_documento_display = serializers.CharField(source='get_tipo_documento_display', read_only=True)
    direccion_transferencia_display = serializers.CharField(source='get_direccion_transferencia_display', read_only=True)
    estado_material_display = serializers.CharField(source='get_estado_material_display', read_only=True)
    
    # Campos multipágina
    es_documento_principal = serializers.BooleanField(read_only=True)
    documento_principal_info = serializers.SerializerMethodField()
    numero_paginas_total = serializers.IntegerField(source='total_paginas', read_only=True)
    
    # Campos de imagen de documento
    tiene_imagen_documento = serializers.SerializerMethodField()
    imagen_documento_url = serializers.SerializerMethodField()
    
    def get_documento_principal_info(self, obj):
        """Retorna información básica del documento principal"""
        if obj.documento_principal:
            return {
                'id': obj.documento_principal.id,
                'numero': obj.documento_principal.numero,
                'fecha': obj.documento_principal.fecha
            }
        return None
    
    def get_tiene_imagen_documento(self, obj):
        """Indica si el albarán tiene imagen de documento asociada"""
        return bool(obj.imagen_documento)
    
    def get_imagen_documento_url(self, obj):
        """Retorna la URL para acceder a la imagen del documento"""
        if obj.imagen_documento:
            return f"/albaranes/{obj.id}/imagen-documento/"
        return None

    class Meta:
        model = Albaran
        fields = [
            'id', 'numero', 'fecha',
            # Campos multipágina
            'pagina_numero', 'total_paginas', 'documento_principal', 
            'es_documento_principal', 'documento_principal_info', 'numero_paginas_total',
            'empresa_origen', 'empresa_destino',
            'empresa_origen_info', 'empresa_destino_info',
            'tipo_documento', 'tipo_documento_display',
            'direccion_transferencia',
            'direccion_transferencia_display',
            'odmc_numero', 'fecha_informe', 
            'numero_registro_salida', 'fecha_transaccion',
            'numero_registro_entrada', 'codigo_contabilidad',
            'accesorios', 'equipos_prueba',  # Nuevos campos
            'estado_material', 'estado_material_display',
            'destinatario_autorizado_testigo', 'destinatario_autorizado_otro', 'destinatario_autorizado_otro_especificar',
            'firma_a', 'firma_a_empleo_rango', 'firma_a_nombre_apellidos', 'firma_a_cargo',
            'firma_b', 'firma_b_empleo_rango', 'firma_b_nombre_apellidos', 'firma_b_cargo',
            'destinatario_autorizado_nombre', 'destinatario_autorizado_cargo',
            'firma_remitente_nombre', 'firma_remitente_cargo',
            'observaciones_odmc',
            'created_by', 'updated_by',
            'created_by_username', 'updated_by_username',
            'created_at', 'updated_at',
            # Campos de imagen de documento
            'tiene_imagen_documento', 'imagen_documento_url'
        ]
        read_only_fields = ['created_by', 'updated_by', 'created_at', 'updated_at']

class LineaTemporalProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineaTemporalProducto
        fields = '__all__'
        read_only_fields = ('usuario',)

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil de usuario
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'first_name', 'last_name', 'must_change_password', 'created_at']
