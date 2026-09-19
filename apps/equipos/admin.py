from django.contrib import admin
from django.utils.html import format_html
from .models import Equipo


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = (
        "serial",
        "marca",
        "modelo",
        "tipo",
        "propiedad",
        "persona",
        "token_qr",
        "activo",
        "ver_qr",
    )
    list_filter = ("tipo", "propiedad", "activo")
    search_fields = ("serial", "marca", "modelo", "persona__numero_documento", "persona__nombres", "persona__apellidos")
    readonly_fields = ("token_qr", "qr_preview", "created_at", "updated_at")

    def ver_qr(self, obj):
        return format_html(
            '<img src="{}" width="38" height="38" style="border-radius:4px;" />',
            obj.generar_qr_base64(),
        )
    ver_qr.short_description = "QR"

    def qr_preview(self, obj):
        data_uri = obj.generar_qr_base64()
        return format_html(
            '<img src="{}" width="200" height="200" style="border:1px solid #ccc; padding:6px; border-radius:8px;" /><br><small>Token: {}</small>',
            data_uri,
            obj.token_qr,
        )
    qr_preview.short_description = "Vista previa del código QR"
