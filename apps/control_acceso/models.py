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

    MOTIVO_EQUIPO_INACTIVO = "equipo_inactivo"
    MOTIVO_PERSONA_INACTIVA = "persona_inactiva"
    MOTIVO_NO_COINCIDE = "no_coincide"
    MOTIVO_ASIGNACION_VENCIDA = "asignacion_vencida"
    MOTIVO_ASIGNACION_NO_VIGENTE = "asignacion_no_vigente"
    MOTIVO_SIN_ASIGNACION_ACTIVA = "sin_asignacion_activa"
    MOTIVO_VISITA_VENCIDA = "visita_vencida"
    MOTIVO_SIN_VISITA_ACTIVA = "sin_visita_activa"

    OPCIONES_MOTIVO_ALERTA = [
        (MOTIVO_EQUIPO_INACTIVO, "Equipo inactivo"),
        (MOTIVO_PERSONA_INACTIVA, "Persona inactiva"),
        (MOTIVO_NO_COINCIDE, "No coincide"),
        (MOTIVO_ASIGNACION_VENCIDA, "Asignación institucional vencida"),
        (MOTIVO_ASIGNACION_NO_VIGENTE, "Asignación institucional no vigente"),
        (MOTIVO_SIN_ASIGNACION_ACTIVA, "Sin asignación activa (disponible en inventario)"),
        (MOTIVO_VISITA_VENCIDA, "Visita de personal externo vencida"),
        (MOTIVO_SIN_VISITA_ACTIVA, "Sin visita activa de personal externo"),
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
        help_text="Vigilante o personal de control que realizó el escaneo",
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    resultado = models.CharField(
        max_length=20,
        choices=OPCIONES_RESULTADO,
        default=RESULTADO_OK,
    )
    motivo_alerta = models.CharField(
        max_length=40,
        choices=OPCIONES_MOTIVO_ALERTA,
        null=True,
        blank=True,
        db_index=True,
        help_text="Motivo tipificado cuando resultado=alerta",
    )
    otra_sede = models.BooleanField(
        default=False,
        help_text="True si la sede de la persona no coincide con la del vigilante (doc 16)",
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
