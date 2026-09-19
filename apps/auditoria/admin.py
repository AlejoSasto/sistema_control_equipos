from django.contrib import admin

from .models import AuditoriaCambio


@admin.register(AuditoriaCambio)
class AuditoriaCambioAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "accion", "entidad", "entidad_id", "usuario", "ip_origen")
    list_filter = ("accion", "entidad")
    search_fields = ("entidad", "ip_origen")
    readonly_fields = (
        "usuario",
        "entidad",
        "entidad_id",
        "accion",
        "detalle",
        "ip_origen",
        "timestamp",
    )
