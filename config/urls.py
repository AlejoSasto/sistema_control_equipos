from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    # Redirección raíz a la pantalla de control de portería
    path("", lambda request: redirect("control_acceso:escanear"), name="home"),
    path("registro/", lambda request: redirect("accounts:registro"), name="registro_shortcut"),
    path(
        "admin/tipos-vinculo/",
        lambda request: redirect("personas:tipo_vinculo_list"),
        name="admin_tipos_vinculo",
    ),

    # Django Admin
    path("admin/", admin.site.urls),

    # Apps del sistema
    path("accounts/", include("accounts.urls")),
    path("organizacion/", include("organizacion.urls")),
    path("personas/", include("personas.urls")),
    path("equipos/", include("equipos.urls")),
    path("acceso/", include("control_acceso.urls")),
    path("panel/", include("panel.urls")),
]

# Servir archivos estáticos y media (códigos QR) en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
