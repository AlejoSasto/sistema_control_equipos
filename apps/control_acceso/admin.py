from django.contrib import admin
from .models import Movimiento


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "resultado",
        "equipo",
        "token_escaneado",
        "usuario_control",
        "observacion",
    )
    list_filter = ("resultado", "timestamp")
    search_fields = (
        "token_escaneado",
        "equipo__serial",
        "equipo__persona__nombres",
        "equipo__persona__apellidos",
        "usuario_control__username",
    )
    readonly_fields = ("timestamp",)
