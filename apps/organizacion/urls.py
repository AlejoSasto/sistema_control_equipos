from django.urls import path
from . import views

app_name = "organizacion"

urlpatterns = [
    path("", views.sedes_list, name="sedes_list"),
]
