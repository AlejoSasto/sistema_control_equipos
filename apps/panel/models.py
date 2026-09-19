from django.db import models


class LogCambioRol(models.Model):
    """Auditoría mínima de cambios en roles y permisos (Documento 07, sección 7)."""

    usuario_que_modifico = models.ForeignKey(
        "accounts.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        related_name="logs_cambio_rol",
    )
    descripcion = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "log_cambio_rol"
        verbose_name = "Log de cambio de rol/permiso"
        verbose_name_plural = "Logs de cambios de rol/permiso"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} — {self.descripcion[:60]}"
