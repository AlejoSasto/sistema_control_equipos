from django.urls import path
from . import views

app_name = "control_acceso"

urlpatterns = [
    path("", views.control_salida_view, name="dashboard"),
    path("control-salida/", views.control_salida_view, name="escanear"),
    path("verificar-qr/", views.escanear_qr_salida, name="verificar_codigo"),
    path("historico/", views.movimientos_list, name="movimientos_list"),
]
