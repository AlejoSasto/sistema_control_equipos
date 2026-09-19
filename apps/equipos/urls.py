from django.urls import path
from . import views

app_name = "equipos"

urlpatterns = [
    path("", views.equipo_list, name="equipos_list"),
    path("mis-equipos/", views.mis_equipos, name="mis_equipos"),
    path("registrar/", views.equipo_create, name="equipo_create"),
    path("<int:pk>/", views.equipo_detail, name="equipo_detail"),
    path("mostrar-qr/<uuid:token_qr>/", views.ver_qr_pantalla, name="mostrar_qr_pantalla"),
    path("render-qr/<uuid:token_qr>.png", views.render_qr_image, name="render_qr_image"),
]
