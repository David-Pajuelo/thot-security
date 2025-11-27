from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'productos', views.CatalogoProductoViewSet)
router.register(r'albaranes', views.AlbaranViewSet)
router.register(r'movimientos', views.MovimientoProductoViewSet)
router.register(r'tipos-producto', views.TipoProductoViewSet)
router.register(r'lineas-temporales', views.LineaTemporalProductoViewSet)
router.register(r'inventario', views.InventarioProductoViewSet)
router.register(r'empresas', views.EmpresaViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # URLs para gestión de usuarios
    path('auth/cambiar-password/', views.cambiar_password, name='cambiar-password'),
    path('auth/perfil/', views.perfil_usuario, name='perfil-usuario'),
]
