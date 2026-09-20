from django.urls import path
from .views import (
    CustomLoginView,
    CustomLogoutView,
    registro_externo_view,
    registrar_visita_view,
    mi_perfil_view,
    mfa_verify_view,
    mfa_setup_view,
)

app_name = "accounts"

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("registro/", registro_externo_view, name="registro"),
    path("registrar-visita/", registrar_visita_view, name="registrar_visita"),
    path("mi-perfil/", mi_perfil_view, name="mi_perfil"),
    path("mfa/verificar/", mfa_verify_view, name="mfa_verify"),
    path("mfa/configurar/", mfa_setup_view, name="mfa_setup"),
]
