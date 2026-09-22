from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.generic import TemplateView

urlpatterns = [
    path("", lambda request: redirect("control_acceso:escanear"), name="home"),
    path("registro/", lambda request: redirect("accounts:registro"), name="registro_shortcut"),
    path(
        "admin/tipos-vinculo/",
        lambda request: redirect("personas:tipo_vinculo_list"),
        name="admin_tipos_vinculo",
    ),
    path(
        "legal/politica-datos/",
        TemplateView.as_view(
            template_name="legal/politica_datos.html",
            extra_context={"contacto_arco": settings.DATOS_PERSONALES_CONTACTO},
        ),
        name="politica_datos",
    ),
    path(settings.ADMIN_URL, admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("organizacion/", include("organizacion.urls")),
    path("personas/", include("personas.urls")),
    path("equipos/", include("equipos.urls")),
    path("acceso/", include("control_acceso.urls")),
    path("panel/", include("panel.urls")),
    path("reportes/", include("reportes.urls")),
    path("webhooks/", include("notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
