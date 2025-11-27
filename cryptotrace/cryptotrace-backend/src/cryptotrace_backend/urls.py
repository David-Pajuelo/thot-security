from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from rest_framework_simplejwt.views import TokenRefreshView
from productos.views import CustomTokenObtainPairView
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path
import os

def redirect_to_admin(request):
    return redirect('admin:index')

urlpatterns = [
    path('', redirect_to_admin, name='home'),  # Redirección desde la raíz
    path('admin/', admin.site.urls),
    path('api/', include('productos.urls')),  # Rutas de productos
    path('api/', include('hps_core.urls')),  # Rutas HPS migradas
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # Login JWT
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh Token
]

# Servir archivos media en producción usando serve directamente
urlpatterns += [
    # Servir archivos media generales
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
    # Servir documentos de albaranes desde su ubicación específica  
    re_path(r'^albaranes/documentos/(?P<path>.*)$', serve, {
        'document_root': '/app/albaranes/documentos',
    }),
]
