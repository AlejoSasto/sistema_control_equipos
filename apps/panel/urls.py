from django.urls import path
from . import views
from . import views_organizacion
from . import views_equipos
from reportes import views_dashboard

app_name = "panel"

urlpatterns = [
    path("", views.panel_index, name="index"),

    # Dashboard administrador (lógica en reportes, rutas bajo /panel/)
    path("dashboard/", views_dashboard.dashboard, name="dashboard"),
    path("dashboard/parcial/", views_dashboard.dashboard_parcial, name="dashboard_parcial"),
    path("dashboard/datos-grafico/", views_dashboard.dashboard_datos, name="dashboard_datos"),

    # Personas
    path("personas/", views.personas_list, name="personas_list"),
    path("personas/nueva/", views.persona_create, name="persona_create"),
    path("personas/vigilante/nuevo/", views.vigilante_create, name="vigilante_create"),
    path("personas/<int:pk>/editar/", views.persona_edit, name="persona_edit"),
    path("personas/<int:pk>/toggle/", views.persona_toggle, name="persona_toggle"),

    # Usuarios
    path("usuarios/", views.usuarios_list, name="usuarios_list"),
    path("usuarios/nuevo/", views.usuario_create, name="usuario_create"),
    path("usuarios/<int:pk>/", views.usuario_detail, name="usuario_detail"),
    path("usuarios/<int:pk>/toggle/", views.usuario_toggle, name="usuario_toggle"),
    path(
        "usuarios/<int:pk>/desbloquear/",
        views.usuario_desbloquear,
        name="usuario_desbloquear",
    ),

    # Roles
    path("roles/", views.roles_list, name="roles_list"),
    path("roles/nuevo/", views.rol_form, name="rol_create"),
    path("roles/<int:pk>/editar/", views.rol_form, name="rol_edit"),
    path("roles/<int:pk>/permisos/", views.rol_permisos, name="rol_permisos"),

    # Permisos (solo lectura)
    path("permisos/", views.permisos_list, name="permisos_list"),

    # Equipos institucionales
    path(
        "equipos/institucionales/nuevo/",
        views_equipos.equipos_inventario_nuevo,
        name="equipos_inventario_nuevo",
    ),
    path(
        "equipos/asignar-institucional/",
        views_equipos.equipos_asignar_institucional,
        name="equipos_asignar_institucional",
    ),
    path(
        "equipos/institucionales/",
        views_equipos.equipos_institucionales_list,
        name="equipos_institucionales",
    ),
    path(
        "equipos/buscar-personas/",
        views_equipos.buscar_personas_unidad,
        name="equipos_buscar_personas",
    ),
    path(
        "equipos/sugerir-fecha-fin/",
        views_equipos.sugerir_fecha_fin_persona,
        name="equipos_sugerir_fecha_fin",
    ),
    path(
        "equipos/<int:pk>/reasignar/",
        views_equipos.equipo_reasignar,
        name="equipo_reasignar",
    ),
    path(
        "equipos/<int:pk>/renovar/",
        views_equipos.equipo_renovar,
        name="equipo_renovar",
    ),
    path(
        "equipos/<int:pk>/devolver/",
        views_equipos.equipo_devolver_inventario,
        name="equipo_devolver",
    ),
    path(
        "equipos/<int:pk>/dar-de-baja/",
        views_equipos.equipo_dar_de_baja,
        name="equipo_dar_de_baja",
    ),
    path(
        "equipos/<int:pk>/dar-de-alta/",
        views_equipos.equipo_dar_de_alta,
        name="equipo_dar_de_alta",
    ),

    # Responsables de dependencia
    path(
        "responsables-dependencia/",
        views_equipos.responsables_list,
        name="responsables_list",
    ),
    path(
        "responsables-dependencia/nuevo/",
        views_equipos.responsable_form,
        name="responsable_create",
    ),
    path(
        "responsables-dependencia/<int:pk>/editar/",
        views_equipos.responsable_form,
        name="responsable_edit",
    ),
    path(
        "responsables-dependencia/<int:pk>/toggle/",
        views_equipos.responsable_toggle,
        name="responsable_toggle",
    ),

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
