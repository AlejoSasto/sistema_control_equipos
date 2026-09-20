from django.core.management.base import BaseCommand
from django.utils import timezone

from equipos.services import cerrar_asignaciones_vencidas_batch


class Command(BaseCommand):
    help = (
        "Cierra AsignacionEquipo activas con fecha_fin < hoy y deja los equipos "
        "como disponibles en inventario (doc 15 §9.1.2)."
    )

    def handle(self, *args, **options):
        hoy = timezone.localdate()
        n = cerrar_asignaciones_vencidas_batch(hoy=hoy)
        self.stdout.write(
            self.style.SUCCESS(f"Cerradas {n} asignación(es) vencida(s) al {hoy.isoformat()}.")
        )
