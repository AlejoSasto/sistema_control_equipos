from django.urls import path
from . import views

app_name = "personas"

urlpatterns = [
    path("", views.persona_list, name="personas_list"),
    path("nueva/", views.persona_create, name="persona_create"),
    path("<int:pk>/", views.persona_detail, name="persona_detail"),

    # Catálogo dinámico TipoVinculo (Documento 06)
    path("tipos-vinculo/", views.tipo_vinculo_list, name="tipo_vinculo_list"),
    path("tipos-vinculo/nuevo/", views.tipo_vinculo_form, name="tipo_vinculo_create"),
    path("tipos-vinculo/<int:pk>/editar/", views.tipo_vinculo_form, name="tipo_vinculo_edit"),
    path("tipos-vinculo/<int:pk>/toggle/", views.tipo_vinculo_toggle, name="tipo_vinculo_toggle"),
]
