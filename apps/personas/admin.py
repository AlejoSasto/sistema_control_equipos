from django.contrib import admin
from .models import Persona, TipoVinculo


@admin.register(TipoVinculo)
class TipoVinculoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "permite_autoregistro",
        "dominio_correo_requerido",
        "rol_asignado",
        "activo",
    )
    list_filter = ("permite_autoregistro", "activo", "rol_asignado")
    search_fields = ("codigo", "nombre", "dominio_correo_requerido")


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = (
        "numero_documento",
        "tipo_documento",
        "apellidos",
        "nombres",
        "tipo_vinculo",
        "sede",
        "programa",
        "activo",
    )
    list_filter = ("tipo_vinculo", "sede", "activo")
    search_fields = ("numero_documento", "nombres", "apellidos")
