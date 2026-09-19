from django.urls import path
from . import views
from . import views_organizacion

app_name = "panel"

urlpatterns = [
    path("", views.panel_index, name="index"),

    # Personas
    path("personas/", views.personas_list, name="personas_list"),
    path("personas/nueva/", views.persona_create, name="persona_create"),
    path("personas/<int:pk>/editar/", views.persona_edit, name="persona_edit"),
    path("personas/<int:pk>/toggle/", views.persona_toggle, name="persona_toggle"),

    # Usuarios
    path("usuarios/", views.usuarios_list, name="usuarios_list"),
    path("usuarios/nuevo/", views.usuario_create, name="usuario_create"),
    path("usuarios/<int:pk>/", views.usuario_detail, name="usuario_detail"),
    path("usuarios/<int:pk>/toggle/", views.usuario_toggle, name="usuario_toggle"),

    # Roles
    path("roles/", views.roles_list, name="roles_list"),
    path("roles/nuevo/", views.rol_form, name="rol_create"),
    path("roles/<int:pk>/editar/", views.rol_form, name="rol_edit"),
    path("roles/<int:pk>/permisos/", views.rol_permisos, name="rol_permisos"),

    # Permisos (solo lectura)
    path("permisos/", views.permisos_list, name="permisos_list"),

    # Organización (Sedes, Facultades, Programas)
    path("organizacion/", views_organizacion.organizacion_list, name="organizacion_list"),
    path("organizacion/sedes/nueva/", views_organizacion.sede_form, name="sede_create"),
    path("organizacion/sedes/<int:pk>/editar/", views_organizacion.sede_form, name="sede_edit"),
    path("organizacion/sedes/<int:pk>/toggle/", views_organizacion.sede_toggle, name="sede_toggle"),
    path("organizacion/decanaturas/nueva/", views_organizacion.decanatura_form, name="decanatura_create"),
    path("organizacion/decanaturas/<int:pk>/editar/", views_organizacion.decanatura_form, name="decanatura_edit"),
    path("organizacion/decanaturas/<int:pk>/toggle/", views_organizacion.decanatura_toggle, name="decanatura_toggle"),
    path("organizacion/programas/nuevo/", views_organizacion.programa_form, name="programa_create"),
    path("organizacion/programas/<int:pk>/editar/", views_organizacion.programa_form, name="programa_edit"),
    path("organizacion/programas/<int:pk>/toggle/", views_organizacion.programa_toggle, name="programa_toggle"),
    path("organizacion/areas/nueva/", views_organizacion.area_form, name="area_create"),
    path("organizacion/areas/<int:pk>/editar/", views_organizacion.area_form, name="area_edit"),
    path("organizacion/areas/<int:pk>/toggle/", views_organizacion.area_toggle, name="area_toggle"),
]
