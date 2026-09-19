from django.urls import path

from . import views

app_name = "reportes"

urlpatterns = [
    path("", views.index, name="index"),
    path("<slug:tipo>/", views.configurar, name="configurar"),
    path("<slug:tipo>/exportar/", views.exportar, name="exportar"),
]
