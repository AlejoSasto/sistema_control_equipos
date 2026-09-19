from django.contrib import admin
from .models import Area, Decanatura, Programa, Sede


@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "ciudad", "activo", "created_at")
    list_filter = ("ciudad", "activo")
    search_fields = ("codigo", "nombre", "ciudad")


@admin.register(Decanatura)
class DecanaturaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "activo", "created_at")
    list_filter = ("activo",)
    search_fields = ("codigo", "nombre")


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "activo", "created_at")
    list_filter = ("activo",)
    search_fields = ("codigo", "nombre")


@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "sede", "facultad", "nivel", "activo", "created_at")
    list_filter = ("nivel", "sede", "facultad", "activo")
    search_fields = ("codigo", "nombre")
