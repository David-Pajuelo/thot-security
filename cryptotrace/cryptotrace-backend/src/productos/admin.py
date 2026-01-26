from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from .models import CatalogoProducto, Albaran, MovimientoProducto, TipoProducto, LineaTemporalProducto, InventarioProducto, Empresa, UserProfile

# ADMIN SIMPLIFICADO - Sin generación automática de contraseñas por ahora

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'must_change_password', 'created_at']
    list_filter = ['must_change_password', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'ciudad', 'numero_odmc']
    search_fields = ['nombre', 'numero_odmc']
    list_filter = ['provincia']

@admin.register(Albaran)
class AlbaranAdmin(admin.ModelAdmin):
    list_display = ['numero', 'fecha', 'tipo_documento', 'direccion_transferencia', 'pagina_numero', 'total_paginas', 'documento_principal', 'estado_material', 'empresa_origen', 'empresa_destino', 'get_firmas_info', 'tiene_imagen_documento_display']
    list_filter = ['estado_material', 'tipo_documento', 'direccion_transferencia', 'documento_principal']
    search_fields = ['numero', 'odmc_numero', 'numero_registro_salida', 'numero_registro_entrada']
    readonly_fields = ['created_by', 'updated_by', 'created_at', 'updated_at', 'get_imagen_info']
    fieldsets = [
        ('Información Básica', {
            'fields': ['numero', 'fecha', 'tipo_documento', 'direccion_transferencia']
        }),
        ('Gestión Multipágina', {
            'fields': ['documento_principal', 'pagina_numero', 'total_paginas'],
            'description': 'Campos para gestión de documentos con múltiples páginas'
        }),
        ('Empresas', {
            'fields': ['empresa_origen', 'empresa_destino']
        }),
        ('Información AC21', {
            'fields': [
                'odmc_numero', 'fecha_informe', 'numero_registro_salida',
                'fecha_transaccion', 'numero_registro_entrada', 'codigo_contabilidad'
            ]
        }),
        ('Accesorios y Equipos de Prueba', {
            'fields': ['accesorios', 'equipos_prueba'],
            'description': 'Información adicional sobre accesorios y equipos de prueba incluidos en el AC21'
        }),
        ('Estado y Autorizaciones', {
            'fields': [
                'estado_material', 'destinatario_autorizado_testigo', 
                'destinatario_autorizado_otro', 'destinatario_autorizado_otro_especificar'
            ]
        }),
        ('Firmas - Persona A', {
            'fields': [
                'firma_a_nombre_apellidos', 'firma_a_cargo', 'firma_a_empleo_rango', 'firma_a'
            ]
        }),
        ('Firmas - Persona B', {
            'fields': [
                'firma_b_nombre_apellidos', 'firma_b_cargo', 'firma_b_empleo_rango', 'firma_b'
            ]
        }),
        ('Campos Legacy (Compatibilidad)', {
            'fields': [
                'destinatario_autorizado_nombre', 'destinatario_autorizado_cargo',
                'firma_remitente_nombre', 'firma_remitente_cargo'
            ],
            'classes': ['collapse']
        }),
        ('Observaciones', {
            'fields': ['observaciones_odmc']
        }),
        ('Imagen del Documento', {
            'fields': ['imagen_documento', 'get_imagen_info'],
            'description': 'Imagen del documento AC21 original procesado por OCR'
        }),
        ('Auditoría', {
            'fields': ['created_by', 'updated_by', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]

    def get_firmas_info(self, obj):
        """Muestra información resumida de las firmas"""
        firmas = []
        if obj.firma_a_nombre_apellidos:
            firmas.append(f"A: {obj.firma_a_nombre_apellidos}")
        if obj.firma_b_nombre_apellidos:
            firmas.append(f"B: {obj.firma_b_nombre_apellidos}")
        return " | ".join(firmas) if firmas else "Sin firmas"
    get_firmas_info.short_description = 'Firmas'

    def get_imagen_info(self, obj):
        """Muestra información sobre la imagen del documento"""
        if obj.imagen_documento:
            try:
                # Mostrar el nombre del archivo y tamaño si es posible
                nombre = obj.imagen_documento.name.split('/')[-1]
                try:
                    tamaño = obj.imagen_documento.size
                    tamaño_mb = round(tamaño / (1024 * 1024), 2)
                    return f"📷 {nombre} ({tamaño_mb} MB)"
                except:
                    return f"📷 {nombre}"
            except:
                return "📷 Imagen presente (error al acceder)"
        return "❌ Sin imagen"
    get_imagen_info.short_description = 'Estado de Imagen'

    def tiene_imagen_documento_display(self, obj):
        """Muestra icono simple para indicar si tiene imagen en la lista"""
        return "📷" if obj.imagen_documento else "❌"
    tiene_imagen_documento_display.short_description = 'Imagen'
    tiene_imagen_documento_display.admin_order_field = 'imagen_documento'

    def save_model(self, request, obj, form, change):
        if not change:  # Si es una creación nueva
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(TipoProducto)
class TipoProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)
    ordering = ('nombre',)

@admin.register(CatalogoProducto)
class CatalogoProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo_producto', 'descripcion', 'tipo')
    list_filter = ('tipo', 'inventario__estado')
    search_fields = ('codigo_producto', 'descripcion')
    ordering = ('codigo_producto',)
    list_per_page = 25

    def get_model_perms(self, request):
        """
        Retorna un diccionario de permisos para mostrar en el índice del admin
        """
        return {
            'add': self.has_add_permission(request),
            'change': self.has_change_permission(request),
            'delete': self.has_delete_permission(request),
            'view': self.has_view_permission(request),
        }

@admin.register(MovimientoProducto)
class MovimientoProductoAdmin(admin.ModelAdmin):
    list_display = (
        'get_producto_codigo', 
        'descripcion',
        'numero_serie', 
        'albaran', 
        'fecha', 
        'tipo_movimiento',
        'cantidad',
        'cc'
    )
    list_filter = ('tipo_movimiento', 'estado_nuevo')
    search_fields = ('producto__codigo_producto', 'numero_serie', 'descripcion')
    list_select_related = ('producto', 'albaran')

    def get_producto_codigo(self, obj):
        if obj.producto:
            return obj.producto.codigo_producto
        return None
    get_producto_codigo.short_description = 'Cód. Producto'
    get_producto_codigo.admin_order_field = 'producto__codigo_producto'

@admin.register(InventarioProducto)
class InventarioProductoAdmin(admin.ModelAdmin):
    list_display = (
        'get_catalogo_codigo', 
        'numero_serie', 
        'descripcion',
        'estado', 
        'ubicacion', 
        'ultima_actualizacion'
    )
    list_filter = ('estado', 'producto__tipo')
    search_fields = (
        'producto__codigo_producto', 
        'numero_serie', 
        'descripcion',
        'ubicacion'
    )
    list_select_related = ('producto', 'producto__tipo')

    def get_catalogo_codigo(self, obj):
        if obj.producto:
            return obj.producto.codigo_producto
        return None
    get_catalogo_codigo.short_description = 'Cód. Producto (Catálogo)'
    get_catalogo_codigo.admin_order_field = 'producto__codigo_producto'

@admin.register(LineaTemporalProducto)
class LineaTemporalProductoAdmin(admin.ModelAdmin):
    list_display = ('numero_albaran', 'codigo_producto', 'numero_serie', 'cantidad', 'tipo_producto', 'procesado', 'created_at')
    list_filter = ('procesado', 'usuario', 'created_at')
    search_fields = ('numero_albaran', 'codigo_producto', 'numero_serie')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = [
        ('Información Básica', {
            'fields': ['usuario', 'numero_albaran', 'codigo_producto', 'descripcion', 'numero_serie']
        }),
        ('Detalles AC-21', {
            'fields': ['cantidad', 'cc', 'observaciones']
        }),
        ('Estado', {
            'fields': ['procesado']
        }),
        ('Datos Adicionales', {
            'fields': ['datos_adicionales'],
            'classes': ['collapse']
        }),
        ('Auditoría', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
