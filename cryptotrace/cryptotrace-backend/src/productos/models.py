from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.utils import timezone
import re
import os
from datetime import datetime

User = get_user_model()

def imagen_documento_upload_path(instance, filename):
    """
    Genera path consistente para almacenamiento de imágenes de documentos
    Estructura: albaranes/documentos/YYYY/MM/albaran_ID_AC21_timestamp.ext
    """
    # Extraer extensión del archivo
    ext = os.path.splitext(filename)[1]
    
    # Generar timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Nombre consistente para rclone
    new_filename = f"albaran_{instance.id}_AC21_{timestamp}{ext}"
    
    # Path organizado por fecha
    return f"albaranes/documentos/{datetime.now().strftime('%Y/%m/')}{new_filename}"

# Constante global TIPO_ENTRADA_CHOICES será eliminada
# TIPO_ENTRADA_CHOICES = [
#     ('inventario', 'Entrada por inventario'),
#     ('transferencia', 'Transferencia (AC21)'),
#     ('entrega_mano', 'Entrega en mano (AC21)'),
# ]

ESTADO_CHOICES = [
    ('activo', 'En custodia'),
    ('inactivo', 'Fuera de custodia'),
]

class UserProfile(models.Model):
    """
    Perfil extendido del usuario para agregar campos adicionales
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    must_change_password = models.BooleanField(default=False, help_text='Si el usuario debe cambiar su contraseña en el próximo login')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
    
    def __str__(self):
        return f"Perfil de {self.user.username}"

class TipoProducto(models.Model): 
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

class CatalogoProducto(models.Model):
    codigo_producto = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()
    tipo = models.ForeignKey(TipoProducto, on_delete=models.CASCADE, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="productos_creados")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="productos_actualizados")
    albaran = models.ForeignKey('Albaran', on_delete=models.CASCADE, related_name='productos', null=True, blank=True)
    cantidad = models.IntegerField(default=1)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Catálogo de Producto"
        verbose_name_plural = "Catálogo de Productos"
        ordering = ['codigo_producto']

    def __str__(self):
        return f"{self.codigo_producto} - {self.descripcion}"

class InventarioProducto(models.Model):
    producto = models.ForeignKey(CatalogoProducto, on_delete=models.CASCADE, related_name='inventario')
    numero_serie = models.CharField(max_length=100, null=True, blank=True)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    ubicacion = models.CharField(max_length=100, blank=True, null=True)
    ultimo_movimiento = models.ForeignKey('MovimientoProducto', on_delete=models.SET_NULL, null=True, related_name='inventario_actual')
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    notas = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Inventario de Producto"
        verbose_name_plural = "Inventario de Productos"
        unique_together = ['producto', 'numero_serie']

    def __str__(self):
        return f"Inventario de {self.producto.codigo_producto} - {self.numero_serie or 'Sin N/S'}"

class Empresa(models.Model):
    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=10)
    provincia = models.CharField(max_length=100)
    numero_odmc = models.CharField(max_length=20, blank=True, verbose_name='Número ODMC')
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def direccion_completa(self):
        return f"{self.direccion}, {self.codigo_postal} {self.ciudad}, {self.provincia}"

class Albaran(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('TRANSFERENCIA', 'Transferencia'),
        ('INVENTARIO', 'Inventario'),
        ('DESTRUCCION', 'Destrucción'),
        ('RECIBO_MANO', 'Recibo en Mano'),
        ('OTRO', 'Otro'),
    ]
    
    ESTADO_MATERIAL_CHOICES = [
        ('RECIBIDO', 'Recibido'),
        ('INVENTARIADO', 'Inventariado'),
        ('DESTRUIDO', 'Destruido'),
    ]

    # Campos básicos
    numero = models.CharField(max_length=20, unique=True)
    fecha = models.DateTimeField(default=timezone.now)
    
    # Campos para documentos multipágina
    pagina_numero = models.IntegerField(default=1, help_text='Número de página del documento')
    total_paginas = models.IntegerField(default=1, help_text='Total de páginas del documento')
    documento_principal = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='paginas_adicionales',
        help_text='Referencia al documento principal si esta es una página adicional'
    )

    # Definir DIRECCION_TRANSFERENCIA_CHOICES aquí dentro
    ENTRADA = 'ENTRADA'
    SALIDA = 'SALIDA'
    DIRECCION_TRANSFERENCIA_CHOICES = [
        (ENTRADA, 'Entrada'),
        (SALIDA, 'Salida'),
    ]
    direccion_transferencia = models.CharField(
        max_length=10,
        choices=DIRECCION_TRANSFERENCIA_CHOICES,
        null=True,
        blank=True,
        help_text="Para AC21s (transferencias), indica si es una entrada o una salida."
    )
    
    # Relaciones con empresas
    empresa_origen = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='albaranes_como_origen',
        verbose_name='DE',
        null=True,
        blank=True
    )
    empresa_destino = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='albaranes_como_destino',
        verbose_name='PARA',
        null=True,
        blank=True
    )
    
    # Información de documento AC21
    tipo_documento = models.CharField(
        max_length=20, 
        choices=TIPO_DOCUMENTO_CHOICES, 
        null=True, 
        blank=True,
        verbose_name="Tipo de Operación" # Cambiado el verbose_name
    )
    odmc_numero = models.CharField(max_length=20, blank=True)
    fecha_informe = models.DateField(default=timezone.now)
    numero_registro_salida = models.CharField(max_length=20, blank=True, null=True)
    fecha_transaccion = models.DateField(default=timezone.now)
    numero_registro_entrada = models.CharField(max_length=20, blank=True)
    codigo_contabilidad = models.CharField(max_length=100, blank=True)
    
    # Imagen del documento procesado
    imagen_documento = models.ImageField(
        upload_to=imagen_documento_upload_path,
        null=True, 
        blank=True,
        help_text="Imagen del documento AC21 procesado (rotada y optimizada)"
    )
    
    # Campos para AC21 - Accesorios y Equipos de Prueba
    accesorios = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        help_text='Lista de accesorios incluidos en el AC21'
    )
    equipos_prueba = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        help_text='Lista de equipos de prueba incluidos en el AC21'
    )
    
    # Estado del material
    estado_material = models.CharField(
        max_length=20, 
        choices=ESTADO_MATERIAL_CHOICES,
        blank=True,
        null=True,
        help_text='Estado del material: RECIBIDO, INVENTARIADO o DESTRUIDO'
    )
    
    # Destinatario autorizado del material de cifra (Sección 16)
    destinatario_autorizado_testigo = models.BooleanField(
        default=False,
        verbose_name='Destinatario autorizado - TESTIGO'
    )
    destinatario_autorizado_otro = models.BooleanField(
        default=False,
        verbose_name='Destinatario autorizado - OTRO'
    )
    destinatario_autorizado_otro_especificar = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Destinatario autorizado - Especificar OTRO',
        help_text='Especificar el tipo cuando se selecciona OTRO'
    )
    
    # Firmas y autorizaciones - Persona A
    firma_a = models.CharField(max_length=100, blank=True, null=True, verbose_name='Firma A')
    firma_a_empleo_rango = models.CharField(max_length=100, blank=True, null=True, verbose_name='Empleo/Rango A')
    firma_a_nombre_apellidos = models.CharField(max_length=100, blank=True, null=True, verbose_name='Nombre y Apellidos A')
    firma_a_cargo = models.CharField(max_length=100, blank=True, null=True, verbose_name='Cargo A')
    
    # Firmas y autorizaciones - Persona B  
    firma_b = models.CharField(max_length=100, blank=True, null=True, verbose_name='Firma B')
    firma_b_empleo_rango = models.CharField(max_length=100, blank=True, null=True, verbose_name='Empleo/Rango B')
    firma_b_nombre_apellidos = models.CharField(max_length=100, blank=True, null=True, verbose_name='Nombre y Apellidos B')
    firma_b_cargo = models.CharField(max_length=100, blank=True, null=True, verbose_name='Cargo B')
    
    # Campos legacy (mantener por compatibilidad)
    destinatario_autorizado_nombre = models.CharField(max_length=100, blank=True, null=True)
    destinatario_autorizado_cargo = models.CharField(max_length=100, blank=True, null=True)
    firma_remitente_nombre = models.CharField(max_length=100, blank=True, null=True)
    firma_remitente_cargo = models.CharField(max_length=100, blank=True, null=True)
    
    # Observaciones
    observaciones_odmc = models.TextField(blank=True)

    # Auditoría
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='albaranes_creados',
        null=True
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='albaranes_actualizados',
        null=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Albarán'
        verbose_name_plural = 'Albaranes'
        ordering = ['-fecha']

    def __str__(self):
        return f"Albarán {self.numero} - {self.fecha.strftime('%d/%m/%Y')}"
    
    @classmethod
    def generar_siguiente_numero_registro_salida(cls, año=None):
        """
        Genera el siguiente número de registro de salida con formato SAÑO-0001, SAÑO-0002, etc.
        
        Args:
            año (int, optional): Año para el cual generar el número. Si no se especifica, usa el año actual.
            
        Returns:
            str: El siguiente número de registro de salida disponible.
        """
        if año is None:
            año = timezone.now().year
        
        # Formato del patrón: S + año + - + 4 dígitos
        patron_base = f"S{año}-"
        
        # Buscar todos los registros de salida que coincidan con el patrón del año
        # Solo considerar AC21 de salida
        registros_existentes = cls.objects.filter(
            direccion_transferencia='SALIDA',
            numero_registro_salida__iregex=rf'^S{año}-\d{{4}}$'
        ).values_list('numero_registro_salida', flat=True)
        
        # Extraer los números secuenciales
        numeros_usados = []
        for registro in registros_existentes:
            if registro:
                # Extraer los últimos 4 dígitos después del guión
                match = re.match(rf'S{año}-(\d{{4}})$', registro)
                if match:
                    numeros_usados.append(int(match.group(1)))
        
        # Encontrar el siguiente número disponible
        if not numeros_usados:
            siguiente_numero = 1
        else:
            siguiente_numero = max(numeros_usados) + 1
        
        # Formatear con 4 dígitos y guión
        return f"S{año}-{siguiente_numero:04d}"

    @property
    def es_documento_principal(self):
        """Retorna True si este documento es la página principal (página 1 y sin documento_principal)"""
        return self.pagina_numero == 1 and self.documento_principal is None
    
    @property 
    def obtener_documento_principal(self):
        """Retorna el documento principal. Si este es el principal, se retorna a sí mismo"""
        return self.documento_principal if self.documento_principal else self
    
    def obtener_todas_las_paginas(self):
        """Retorna todas las páginas del documento ordenadas por número de página"""
        doc_principal = self.obtener_documento_principal
        return Albaran.objects.filter(
            models.Q(id=doc_principal.id) | models.Q(documento_principal=doc_principal)
        ).order_by('pagina_numero')
    
    def actualizar_total_paginas(self):
        """Actualiza el total de páginas en todas las páginas del documento"""
        todas_las_paginas = self.obtener_todas_las_paginas()
        total = todas_las_paginas.count()
        todas_las_paginas.update(total_paginas=total)
    
    @classmethod
    def encontrar_documento_existente(cls, numero_registro):
        """
        Busca un documento existente con el mismo número de registro (entrada o salida)
        Retorna la página principal si existe
        """
        # Buscar por número de registro de entrada o salida
        documento = cls.objects.filter(
            models.Q(numero_registro_entrada=numero_registro) | 
            models.Q(numero_registro_salida=numero_registro),
            documento_principal__isnull=True  # Solo páginas principales
        ).first()
        
        return documento
    
    def crear_pagina_adicional(self, **kwargs):
        """
        Crea una nueva página adicional para este documento
        Retorna la nueva página creada
        """
        doc_principal = self.obtener_documento_principal
        siguiente_pagina = doc_principal.obtener_todas_las_paginas().count() + 1
        
        # Crear nueva página con los datos base
        nueva_pagina = Albaran.objects.create(
            documento_principal=doc_principal,
            pagina_numero=siguiente_pagina,
            numero=f"{doc_principal.numero}-P{siguiente_pagina}",  # Generar número único
            numero_registro_entrada=doc_principal.numero_registro_entrada,
            numero_registro_salida=doc_principal.numero_registro_salida,
            tipo_documento=doc_principal.tipo_documento,
            direccion_transferencia=doc_principal.direccion_transferencia,
            empresa_origen=doc_principal.empresa_origen,
            empresa_destino=doc_principal.empresa_destino,
            **kwargs
        )
        
        # Actualizar total de páginas en todo el documento
        doc_principal.actualizar_total_paginas()
        
        return nueva_pagina

    def get_imagen_documento_url(self):
        """
        Obtiene la URL de la imagen del documento
        """
        if self.imagen_documento:
            return self.imagen_documento.url
        return None

    @property
    def tiene_imagen_documento(self):
        """
        Verifica si el albarán tiene una imagen de documento asociada
        """
        return bool(self.imagen_documento)

    def save(self, *args, **kwargs):
        # Auto-generar número de registro de salida si es un AC21 de salida y no tiene número
        if (self.direccion_transferencia == 'SALIDA' and 
            not self.numero_registro_salida and 
            self.tipo_documento == 'TRANSFERENCIA'):
            self.numero_registro_salida = self.generar_siguiente_numero_registro_salida()
        
        # Actualizar el campo 'numero' si es un AC21 de salida y se modifica numero_registro_salida
        if (self.direccion_transferencia == 'SALIDA' and 
            self.numero_registro_salida and 
            self.tipo_documento == 'TRANSFERENCIA'):
            
            # Si es página principal (sin documento_principal)
            if not self.documento_principal:
                self.numero = self.numero_registro_salida
            else:
                # Si es página adicional, usar formato: numero_registro_salida-P{pagina_numero}
                self.numero = f"{self.numero_registro_salida}-P{self.pagina_numero}"
        
        if not self.pk:  # Si es una creación nueva
            self.created_at = timezone.now()
            
            # Si tiene documento_principal pero no número de página, asignar siguiente
            if self.documento_principal and not self.pagina_numero:
                todas_las_paginas = self.documento_principal.obtener_todas_las_paginas()
                self.pagina_numero = todas_las_paginas.count() + 1
                
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
        
        # Actualizar total de páginas si es parte de un documento multipágina
        if self.documento_principal or self.pagina_numero > 1:
            self.actualizar_total_paginas()

class MovimientoProducto(models.Model):
    producto = models.ForeignKey(CatalogoProducto, on_delete=models.CASCADE, related_name='movimientos')
    numero_serie = models.CharField(max_length=100, null=True, blank=True)
    descripcion = models.TextField(blank=True, null=True)
    albaran = models.ForeignKey(Albaran, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    tipo_movimiento = models.CharField(
        max_length=20, # Ajustado para ser consistente con tipo_documento
        choices=Albaran.TIPO_DOCUMENTO_CHOICES, # Usar las choices de Albaran.TIPO_DOCUMENTO_CHOICES
        default='INVENTARIO' # Ejemplo de default, ajustar si es necesario
    )
    estado_anterior = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='inactivo')
    estado_nuevo = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    
    # Campos adicionales para AC-21
    cantidad = models.IntegerField(default=1, help_text='Cantidad del producto en el movimiento')
    cc = models.IntegerField(default=1, help_text='Campo CC del AC-21')
    observaciones = models.TextField(blank=True, null=True, help_text='Observaciones específicas del movimiento')

    class Meta:
        ordering = ['-fecha']
        unique_together = ['producto', 'numero_serie', 'albaran']

    def __str__(self):
        return f"{self.producto.codigo_producto} - {self.numero_serie or 'Sin N/S'} - {self.tipo_movimiento}"

    def save(self, *args, **kwargs):
        # Primero guardamos el movimiento
        super().save(*args, **kwargs)
        
        try:
            # Intentamos obtener el registro de inventario existente
            inventario = InventarioProducto.objects.filter(
                producto=self.producto,
                numero_serie=self.numero_serie
            ).first()

            if inventario:
                # Actualizamos el registro existente
                inventario.estado = self.estado_nuevo
                inventario.ultimo_movimiento = self
                inventario.ultima_actualizacion = self.fecha
                inventario.save()
            else:
                # Creamos un nuevo registro de inventario
                InventarioProducto.objects.create(
                    producto=self.producto,
                    numero_serie=self.numero_serie,
                    descripcion=self.producto.descripcion,
                    estado=self.estado_nuevo,
                    ultimo_movimiento=self,
                    ultima_actualizacion=self.fecha
                )
        except Exception as e:
            # Logueamos el error pero no interrumpimos la operación
            print(f"❌ Error actualizando inventario: {str(e)}")
            # Aquí podrías agregar logging más detallado si lo necesitas

class LineaTemporalProducto(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    numero_albaran = models.CharField(max_length=100)
    codigo_producto = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    numero_serie = models.CharField(max_length=100)
    bultos_total = models.IntegerField(null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)
    procesado = models.BooleanField(default=False)
    cantidad = models.IntegerField(default=1)
    cc = models.IntegerField(default=1)
    
    # Campo JSON para almacenar información adicional del AC21
    datos_adicionales = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        help_text='Información adicional del AC21 (cabecera, empresas, firmas, etc.)'
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.numero_albaran} - {self.codigo_producto} - {self.numero_serie}"