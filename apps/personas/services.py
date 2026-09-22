"""Servicios de VisitaExterno (doc 16) — vigencia y cierre automático."""

from __future__ import annotations

from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from equipos.services import nombre_unidad
from organizacion.models import Area, Decanatura, Programa, Sede
from personas.models import (
    CODIGO_VINCULO_EXTERNO,
    Persona,
    VisitaExterno,
)

VIGENTE = "vigente"
VENCIDA = "vencida"
NO_VIGENTE = "no_vigente"
SIN_VISITA = "sin_visita"


def visita_activa(persona: Persona | None) -> VisitaExterno | None:
    if persona is None:
        return None
    return (
        VisitaExterno.objects.filter(persona=persona, estado=VisitaExterno.ESTADO_ACTIVA)
        .select_related("sede")
        .order_by("-fecha_inicio", "-id")
        .first()
    )


def vigencia_visita(visita: VisitaExterno | None, hoy: date | None = None) -> str:
    if visita is None:
        return SIN_VISITA
    hoy = hoy or timezone.localdate()
    if hoy < visita.fecha_inicio:
        return NO_VIGENTE
    if hoy > visita.fecha_fin:
        return VENCIDA
    return VIGENTE


def nombre_dependencia_visita(visita: VisitaExterno | None) -> str:
    if visita is None:
        return ""
    return nombre_unidad(visita.unidad_tipo, visita.unidad_id)


def _validar_unidad(unidad_tipo: str, unidad_id: int, sede: Sede | None = None) -> None:
    if unidad_tipo == "facultad":
        if not Decanatura.objects.filter(pk=unidad_id, activo=True).exists():
            raise ValidationError("La facultad seleccionada no es válida.")
        if sede and not Programa.objects.filter(
            facultad_id=unidad_id, sede_id=sede.id, activo=True
        ).exists():
            raise ValidationError(
                "La facultad seleccionada no tiene programas en la sede indicada."
            )
    elif unidad_tipo == "programa":
        programa = Programa.objects.filter(pk=unidad_id, activo=True).first()
        if not programa:
            raise ValidationError("El programa seleccionado no es válido.")
        if sede and programa.sede_id != sede.id:
            raise ValidationError("El programa seleccionado no pertenece a la sede indicada.")
    elif unidad_tipo == "area":
        area = Area.objects.filter(pk=unidad_id, activo=True).first()
        if not area:
            raise ValidationError("El área seleccionada no es válida.")
        if sede and area.sede_id != sede.id:
            raise ValidationError("El área seleccionada no pertenece a la sede indicada.")
    else:
        raise ValidationError("Tipo de dependencia no válido.")


@transaction.atomic
def registrar_visita(
    *,
    persona: Persona,
    sede: Sede,
    unidad_tipo: str,
    unidad_id: int,
    fecha_inicio: date,
    fecha_fin: date,
) -> VisitaExterno:
    if not persona.tipo_vinculo_id or persona.tipo_vinculo.codigo != CODIGO_VINCULO_EXTERNO:
        raise ValidationError("Solo el personal externo puede registrar visitas.")
    if fecha_fin < fecha_inicio:
        raise ValidationError("La fecha fin debe ser mayor o igual a la fecha inicio.")
    _validar_unidad(unidad_tipo, unidad_id, sede=sede)

    VisitaExterno.objects.filter(
        persona=persona, estado=VisitaExterno.ESTADO_ACTIVA
    ).update(estado=VisitaExterno.ESTADO_FINALIZADA)

    visita = VisitaExterno(
        persona=persona,
        sede=sede,
        unidad_tipo=unidad_tipo,
        unidad_id=unidad_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        estado=VisitaExterno.ESTADO_ACTIVA,
    )
    visita.save()

    if persona.sede_id != sede.id:
        persona.sede = sede
        persona.save(update_fields=["sede", "updated_at"])

    return visita


@transaction.atomic
def cerrar_visita_vencida(persona: Persona, hoy: date | None = None) -> VisitaExterno | None:
    """Si hay visita activa vencida, la finaliza. No inactiva la Persona."""
    hoy = hoy or timezone.localdate()
    visita = visita_activa(persona)
    if visita is None:
        return None
    if visita.fecha_fin >= hoy:
        return None
    visita.estado = VisitaExterno.ESTADO_FINALIZADA
    visita.save(update_fields=["estado"])
    return visita


def cerrar_visitas_vencidas_batch(hoy: date | None = None) -> int:
    hoy = hoy or timezone.localdate()
    qs = VisitaExterno.objects.filter(
        estado=VisitaExterno.ESTADO_ACTIVA,
        fecha_fin__lt=hoy,
    )
    return qs.update(estado=VisitaExterno.ESTADO_FINALIZADA)
