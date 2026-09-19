from django.db import models


class Movimiento(models.Model):
    RESULTADO_OK = "ok"
    RESULTADO_ALERTA = "alerta"
    RESULTADO_NO_ENCONTRADO = "no_encontrado"

    OPCIONES_RESULTADO = [
        (RESULTADO_OK, "Coincide / Autorizado (OK)"),
        (RESULTADO_ALERTA, "Alerta de Seguridad"),
        (RESULTADO_NO_ENCONTRADO, "No Encontrado en Base de Datos"),
    ]

    equipo = models.ForeignKey(
        "equipos.Equipo",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="movimientos",
        help_text="Equipo escaneado (null si no existe en BD)",
    )
    token_escaneado = models.CharField(
        max_length=100,
        blank=True,
        help_text="Cadena exacta recibida por el lector de código de barras/QR",
    )
    usuario_control = models.ForeignKey(
        "accounts.Usuario",
        on_delete=models.RESTRICT,
        related_name="movimientos_controlados",
        help_text="Celador o personal de control que realizó el escaneo",
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    resultado = models.CharField(
        max_length=20,
        choices=OPCIONES_RESULTADO,
        default=RESULTADO_OK,
    )
    observacion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "movimiento"
        verbose_name = "Movimiento de Control"
        verbose_name_plural = "Movimientos de Control"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["timestamp"]),
            models.Index(fields=["equipo"]),
            models.Index(fields=["resultado"]),
        ]

    def __str__(self):
        fecha = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        serial = self.equipo.serial if self.equipo else self.token_escaneado
        return f"[{self.resultado.upper()}] {serial} ({fecha})"
