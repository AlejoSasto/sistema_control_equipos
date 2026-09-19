from django.conf import settings
from django.db import models


class AuditoriaCambio(models.Model):
    ACCION_CREAR = "crear"
    ACCION_EDITAR = "editar"
    ACCION_INACTIVAR = "inactivar"
    ACCION_EXPORTAR = "exportar"

    OPCIONES_ACCION = [
        (ACCION_CREAR, "Crear"),
        (ACCION_EDITAR, "Editar"),
        (ACCION_INACTIVAR, "Inactivar"),
        (ACCION_EXPORTAR, "Exportar"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auditorias",
    )
    entidad = models.CharField(max_length=50, db_index=True)
    entidad_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    accion = models.CharField(max_length=20, choices=OPCIONES_ACCION)
    detalle = models.JSONField(default=dict, blank=True)
    ip_origen = models.CharField(max_length=45, blank=True, default="")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "auditoria_cambio"
        verbose_name = "Auditoría de cambio"
        verbose_name_plural = "Auditorías de cambio"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} {self.accion} {self.entidad}/{self.entidad_id}"
