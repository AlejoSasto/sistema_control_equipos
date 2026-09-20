from django.core.management.base import BaseCommand
from django.utils import timezone

from personas.services import cerrar_visitas_vencidas_batch


class Command(BaseCommand):
    help = (
        "Cierra VisitaExterno activas con fecha_fin < hoy sin inactivar la Persona (doc 16)."
    )

    def handle(self, *args, **options):
        hoy = timezone.localdate()
        n = cerrar_visitas_vencidas_batch(hoy=hoy)
        self.stdout.write(
            self.style.SUCCESS(f"Cerradas {n} visita(s) vencida(s) al {hoy.isoformat()}.")
        )
