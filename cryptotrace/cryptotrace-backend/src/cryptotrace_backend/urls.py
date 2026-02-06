from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from productos.views import CustomTokenObtainPairView, CustomTokenRefreshView
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
    # Rutas de token primero (más específicas) para que no las capturen los include('api/')
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # Login JWT
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),  # Refresh Token (sin throttling)
    path('api/', include('productos.urls')),  # Rutas de productos
    path('api/', include('hps_core.urls')),  # Rutas HPS migradas
]

# Servir archivos media y estáticos en desarrollo
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    
    # Servir archivos media en desarrollo
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
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
        # Servir archivos estáticos en producción
        re_path(r'^static/(?P<path>.*)$', serve, {
            'document_root': settings.STATIC_ROOT,
        }),
    ]
