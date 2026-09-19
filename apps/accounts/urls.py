from django.urls import path
from .views import CustomLoginView, CustomLogoutView, registro_externo_view, mi_perfil_view

app_name = "accounts"

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("registro/", registro_externo_view, name="registro"),
    path("mi-perfil/", mi_perfil_view, name="mi_perfil"),
]
