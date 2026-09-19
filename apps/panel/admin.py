from django.contrib import admin
from .models import LogCambioRol


@admin.register(LogCambioRol)
class LogCambioRolAdmin(admin.ModelAdmin):
    list_display = ("created_at", "usuario_que_modifico", "descripcion_corta")
    list_filter = ("created_at",)
    search_fields = ("descripcion", "usuario_que_modifico__username")
    readonly_fields = ("usuario_que_modifico", "descripcion", "created_at")

    def descripcion_corta(self, obj):
        return obj.descripcion[:80]
    descripcion_corta.short_description = "Descripción"
