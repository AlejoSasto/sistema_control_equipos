"""Alcance, inventario y ciclo de vida de asignaciones institucionales (docs 14–15)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from organizacion.models import (
    UNIDAD_AREA,
    UNIDAD_FACULTAD,
    UNIDAD_PROGRAMA,
    Area,
    Decanatura,
    Programa,
    ResponsableDependencia,
)
from personas.models import Persona


VIGENTE = "vigente"
VENCIDA = "vencida"
NO_VIGENTE = "no_vigente"
SIN_ASIGNACION = "sin_asignacion"
POR_VENCER = "por_vencer"

DIAS_AVISO_POR_VENCER = 15


@dataclass(frozen=True)
class UnidadRef:
    tipo: str
    id: int
    nombre: str
    codigo: str = ""

    @property
    def clave(self) -> str:
        return f"{self.tipo}:{self.id}"

    @property
    def etiqueta(self) -> str:
        if self.codigo:
            return f"{self.nombre} ({self.codigo})"
        return self.nombre


def es_admin_global(usuario) -> bool:
    """Admin con alcance GLOBAL (FUSA = usuario global, no hardcodeado)."""
    if not usuario or not getattr(usuario, "is_authenticated", False):
        return False
    if getattr(usuario, "is_superuser", False):
        return True
    from accounts.alcance import alcance_es_global

    if not alcance_es_global(usuario):
        return False
    return usuario.tiene_permiso("equipos.gestionar_responsables") or usuario.roles.filter(
        activo=True, nombre="admin_sistema"
    ).exists()


def nombre_unidad(unidad_tipo: str | None, unidad_id: int | None) -> str:
    if not unidad_tipo or not unidad_id:
        return ""
    if unidad_tipo == UNIDAD_FACULTAD:
        obj = Decanatura.objects.filter(pk=unidad_id).first()
        return obj.nombre if obj else f"Facultad #{unidad_id}"
    if unidad_tipo == UNIDAD_PROGRAMA:
        obj = Programa.objects.select_related("facultad", "sede").filter(pk=unidad_id).first()
        return obj.nombre if obj else f"Programa #{unidad_id}"
    if unidad_tipo == UNIDAD_AREA:
        obj = Area.objects.filter(pk=unidad_id).first()
        return f"{obj.codigo} — {obj.nombre}" if obj else f"Área #{unidad_id}"
    return f"{unidad_tipo}:{unidad_id}"


def _resolver_unidad(tipo: str, unidad_id: int) -> UnidadRef | None:
    if tipo == UNIDAD_FACULTAD:
        obj = Decanatura.objects.filter(pk=unidad_id, activo=True).first()
        return UnidadRef(tipo, unidad_id, obj.nombre, obj.codigo) if obj else None
    if tipo == UNIDAD_PROGRAMA:
        obj = Programa.objects.filter(pk=unidad_id, activo=True).first()
        return UnidadRef(tipo, unidad_id, obj.nombre, obj.codigo) if obj else None
    if tipo == UNIDAD_AREA:
        obj = Area.objects.filter(pk=unidad_id, activo=True).first()
        return UnidadRef(tipo, unidad_id, obj.nombre, obj.codigo) if obj else None
    return None


def _tiene_permiso_unidad(usuario) -> bool:
    return (
        usuario.tiene_permiso("equipos.asignar_institucional")
        or usuario.tiene_permiso("equipos.inventario_institucional")
    )


def unidades_de(usuario) -> list[UnidadRef]:
    from accounts.alcance import alcance_de
    from organizacion.models import AlcanceUsuario

    if es_admin_global(usuario):
        unidades: list[UnidadRef] = []
        for f in Decanatura.objects.filter(activo=True).order_by("nombre"):
            unidades.append(UnidadRef(UNIDAD_FACULTAD, f.pk, f.nombre, f.codigo))
        for p in Programa.objects.filter(activo=True).order_by("nombre"):
            unidades.append(UnidadRef(UNIDAD_PROGRAMA, p.pk, p.nombre, p.codigo))
        for a in Area.objects.filter(activo=True).order_by("nombre"):
            unidades.append(UnidadRef(UNIDAD_AREA, a.pk, a.nombre, a.codigo))
        return unidades

    if not _tiene_permiso_unidad(usuario):
        return []

    refs: list[UnidadRef] = []
    vistos: set[str] = set()
    alcance = alcance_de(usuario)
    if not alcance.es_global:
        for fid in alcance.facultades:
            ref = _resolver_unidad(UNIDAD_FACULTAD, fid)
            if ref and ref.clave not in vistos:
                refs.append(ref)
                vistos.add(ref.clave)
        for pid in alcance.programas:
            ref = _resolver_unidad(UNIDAD_PROGRAMA, pid)
            if ref and ref.clave not in vistos:
                refs.append(ref)
                vistos.add(ref.clave)
        for aid in alcance.areas:
            ref = _resolver_unidad(UNIDAD_AREA, aid)
            if ref and ref.clave not in vistos:
                refs.append(ref)
                vistos.add(ref.clave)
        if alcance.sedes:
            for p in Programa.objects.filter(sede_id__in=alcance.sedes, activo=True).order_by("nombre"):
                ref = UnidadRef(UNIDAD_PROGRAMA, p.pk, p.nombre, p.codigo)
                if ref.clave not in vistos:
                    refs.append(ref)
                    vistos.add(ref.clave)

    for fila in ResponsableDependencia.objects.filter(usuario=usuario, activo=True):
        ref = _resolver_unidad(fila.unidad_tipo, fila.unidad_id)
        if ref and ref.clave not in vistos:
            refs.append(ref)
            vistos.add(ref.clave)
    return refs


def tiene_alcance_asignacion(usuario) -> bool:
    return es_admin_global(usuario) or (
        usuario.tiene_permiso("equipos.asignar_institucional") and bool(unidades_de(usuario))
    )


def tiene_alcance_inventario(usuario) -> bool:
    return es_admin_global(usuario) or (
        usuario.tiene_permiso("equipos.inventario_institucional") and bool(unidades_de(usuario))
    )


def persona_pertenece_a(persona: Persona, unidad_tipo: str, unidad_id: int) -> bool:
    if unidad_tipo == UNIDAD_AREA:
        return persona.area_id == unidad_id
    if unidad_tipo == UNIDAD_PROGRAMA:
        return persona.programa_id == unidad_id
    if unidad_tipo == UNIDAD_FACULTAD:
        if not persona.programa_id:
            return False
        facultad_id = getattr(persona.programa, "facultad_id", None)
        if facultad_id is None:
            from organizacion.models import Programa as Prog

            facultad_id = Prog.objects.filter(pk=persona.programa_id).values_list(
                "facultad_id", flat=True
            ).first()
        return facultad_id == unidad_id
    return False


def personas_de_unidad(unidad_tipo: str, unidad_id: int) -> QuerySet[Persona]:
    qs = Persona.objects.filter(activo=True).select_related(
        "sede", "programa", "programa__facultad", "area", "tipo_vinculo"
    )
    if unidad_tipo == UNIDAD_AREA:
        return qs.filter(area_id=unidad_id)
    if unidad_tipo == UNIDAD_PROGRAMA:
        return qs.filter(programa_id=unidad_id)
    if unidad_tipo == UNIDAD_FACULTAD:
        return qs.filter(programa__facultad_id=unidad_id)
    return Persona.objects.none()


def puede_gestionar_unidad(usuario, unidad_tipo: str, unidad_id: int) -> bool:
    if es_admin_global(usuario):
        return True
    if not _tiene_permiso_unidad(usuario):
        return False
    if ResponsableDependencia.objects.filter(
        usuario=usuario,
        unidad_tipo=unidad_tipo,
        unidad_id=unidad_id,
        activo=True,
    ).exists():
        return True
    from accounts.alcance import alcance_de
    from organizacion.models import AlcanceUsuario

    alcance = alcance_de(usuario)
    if alcance.es_global:
        return True
    if unidad_tipo == UNIDAD_FACULTAD:
        return unidad_id in alcance.facultades
    if unidad_tipo == UNIDAD_PROGRAMA:
        return unidad_id in alcance.programas
    if unidad_tipo == UNIDAD_AREA:
        return unidad_id in alcance.areas
    return False


def asignacion_activa(equipo):
    from equipos.models import AsignacionEquipo

    return (
        AsignacionEquipo.objects.filter(equipo=equipo, estado=AsignacionEquipo.ESTADO_ACTIVA)
        .select_related("persona", "asignado_por_usuario")
        .first()
    )


def unidad_de_equipo(equipo) -> tuple[str | None, int | None]:
    return getattr(equipo, "unidad_tipo", None), getattr(equipo, "unidad_id", None)


def puede_gestionar_equipo_institucional(usuario, equipo) -> bool:
    if getattr(equipo, "propiedad", None) != "institucional":
        return False
    if es_admin_global(usuario):
        return True
    if not _tiene_permiso_unidad(usuario):
        return False
    unidad_tipo, unidad_id = unidad_de_equipo(equipo)
    if not unidad_tipo or not unidad_id:
        return False
    return puede_gestionar_unidad(usuario, unidad_tipo, unidad_id)


def filtro_equipos_institucionales_alcance(usuario) -> Q:
    if es_admin_global(usuario):
        return Q(propiedad="institucional")
    unidades = unidades_de(usuario)
    if not unidades:
        return Q(pk__in=[])
    q = Q()
    for u in unidades:
        q |= Q(unidad_tipo=u.tipo, unidad_id=u.id)
    return Q(propiedad="institucional") & q


def vigencia_asignacion(asignacion, hoy: date | None = None) -> str:
    if asignacion is None:
        return SIN_ASIGNACION
    hoy = hoy or timezone.localdate()
    if hoy < asignacion.fecha_inicio:
        return NO_VIGENTE
    if hoy > asignacion.fecha_fin:
        return VENCIDA
    return VIGENTE


def estado_listado_equipo(equipo, asignacion=None, hoy: date | None = None) -> str:
    """Estado UI: de_baja | disponible | vencida | por_vencer | vigente | no_vigente | sin_asignacion."""
    from equipos.models import Equipo

    if not equipo.activo or equipo.estado_inventario == Equipo.ESTADO_DE_BAJA:
        return "de_baja"
    if equipo.estado_inventario == Equipo.ESTADO_DISPONIBLE:
        return "disponible"
    asig = asignacion if asignacion is not None else asignacion_activa(equipo)
    vig = vigencia_asignacion(asig, hoy)
    if vig == VIGENTE and asig:
        hoy = hoy or timezone.localdate()
        if 0 <= (asig.fecha_fin - hoy).days <= DIAS_AVISO_POR_VENCER:
            return POR_VENCER
    return vig


def sugerir_fecha_fin(persona: Persona, fecha_inicio: date) -> date:
    """Heurística R10: estudiante → fin de semestre; resto → +1 año."""
    codigo = ""
    if persona.tipo_vinculo_id:
        codigo = getattr(persona.tipo_vinculo, "codigo", "") or ""
    if codigo == "creador_oportunidades":
        if fecha_inicio.month <= 6:
            return date(fecha_inicio.year, 6, 30)
        return date(fecha_inicio.year, 12, 15)
    return fecha_inicio + timedelta(days=365)


def _liberar_equipo_inventario(equipo):
    from equipos.models import Equipo

    Equipo.objects.filter(pk=equipo.pk).update(
        persona_id=None,
        estado_inventario=Equipo.ESTADO_DISPONIBLE,
    )
    equipo.persona_id = None
    equipo.estado_inventario = Equipo.ESTADO_DISPONIBLE


def cerrar_asignacion(asignacion, hoy: date | None = None, liberar_inventario: bool = False):
    from equipos.models import AsignacionEquipo

    if asignacion is None or asignacion.estado != AsignacionEquipo.ESTADO_ACTIVA:
        return asignacion
    hoy = hoy or timezone.localdate()
    nuevo = (
        AsignacionEquipo.ESTADO_FINALIZADA
        if asignacion.fecha_fin < hoy
        else AsignacionEquipo.ESTADO_REVOCADA
    )
    AsignacionEquipo.objects.filter(pk=asignacion.pk).update(estado=nuevo)
    asignacion.estado = nuevo
    if liberar_inventario:
        _liberar_equipo_inventario(asignacion.equipo)
    return asignacion


@transaction.atomic
def liberar_asignacion_vencida(equipo, hoy: date | None = None):
    """Cierra asignación vencida y deja el equipo disponible (doc 15 §9)."""
    from equipos.models import AsignacionEquipo

    hoy = hoy or timezone.localdate()
    asig = asignacion_activa(equipo)
    if not asig or asig.fecha_fin >= hoy:
        return None
    AsignacionEquipo.objects.filter(pk=asig.pk).update(estado=AsignacionEquipo.ESTADO_FINALIZADA)
    asig.estado = AsignacionEquipo.ESTADO_FINALIZADA
    _liberar_equipo_inventario(equipo)
    return asig


@transaction.atomic
def cerrar_asignaciones_vencidas_batch(hoy: date | None = None) -> int:
    """Job diario: cierra todas las activas con fecha_fin < hoy."""
    from equipos.models import AsignacionEquipo, Equipo

    hoy = hoy or timezone.localdate()
    qs = (
        AsignacionEquipo.objects.filter(
            estado=AsignacionEquipo.ESTADO_ACTIVA,
            fecha_fin__lt=hoy,
        )
        .select_related("equipo")
    )
    n = 0
    for asig in qs:
        AsignacionEquipo.objects.filter(pk=asig.pk).update(estado=AsignacionEquipo.ESTADO_FINALIZADA)
        Equipo.objects.filter(pk=asig.equipo_id).update(
            persona_id=None,
            estado_inventario=Equipo.ESTADO_DISPONIBLE,
        )
        n += 1
    return n


@transaction.atomic
def crear_equipo_inventario(
    *,
    tipo: str,
    marca: str,
    modelo: str,
    serial: str,
    unidad_tipo: str,
    unidad_id: int,
    creado_por_usuario,
):
    from equipos.models import Equipo

    if Equipo.objects.filter(serial__iexact=serial).exists():
        raise ValidationError({"serial": f"Ya existe un equipo con el serial {serial}."})

    equipo = Equipo(
        persona=None,
        tipo=tipo,
        marca=marca,
        modelo=modelo,
        serial=serial,
        propiedad=Equipo.PROPIEDAD_INSTITUCIONAL,
        unidad_tipo=unidad_tipo,
        unidad_id=unidad_id,
        estado_inventario=Equipo.ESTADO_DISPONIBLE,
        creado_por_usuario=creado_por_usuario,
        dependencia_id=unidad_id if unidad_tipo == UNIDAD_AREA else None,
        activo=True,
    )
    equipo.save()
    return equipo


@transaction.atomic
def crear_asignacion(
    *,
    equipo,
    persona,
    fecha_inicio: date,
    fecha_fin: date,
    asignado_por_usuario,
):
    from equipos.models import AsignacionEquipo, Equipo

    if equipo.propiedad != Equipo.PROPIEDAD_INSTITUCIONAL:
        raise ValidationError("Solo se asignan equipos institucionales.")
    if not equipo.unidad_tipo or not equipo.unidad_id:
        raise ValidationError("El equipo no tiene unidad propietaria.")
    if not fecha_inicio or not fecha_fin:
        raise ValidationError("fecha_inicio y fecha_fin son obligatorias.")
    if fecha_fin < fecha_inicio:
        raise ValidationError({"fecha_fin": "La fecha fin no puede ser anterior a la fecha inicio."})

    previa = asignacion_activa(equipo)
    if previa:
        cerrar_asignacion(previa)

    asig = AsignacionEquipo(
        equipo=equipo,
        persona=persona,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        estado=AsignacionEquipo.ESTADO_ACTIVA,
        asignado_por_usuario=asignado_por_usuario,
    )
    asig.save()

    Equipo.objects.filter(pk=equipo.pk).update(
        persona_id=persona.pk,
        estado_inventario=Equipo.ESTADO_ASIGNADO,
        activo=True,
    )
    equipo.persona_id = persona.pk
    equipo.estado_inventario = Equipo.ESTADO_ASIGNADO
    return asig


@transaction.atomic
def devolver_al_inventario(equipo, hoy: date | None = None):
    """Cierra asignación activa y deja el equipo disponible."""
    from equipos.models import Equipo

    if equipo.propiedad != Equipo.PROPIEDAD_INSTITUCIONAL:
        raise ValidationError("Solo aplica a equipos institucionales.")
    asig = asignacion_activa(equipo)
    if asig:
        cerrar_asignacion(asig, hoy=hoy, liberar_inventario=True)
    else:
        _liberar_equipo_inventario(equipo)
    return equipo


@transaction.atomic
def dar_de_baja_institucional(equipo):
    from equipos.models import Equipo

    asig = asignacion_activa(equipo)
    if asig:
        cerrar_asignacion(asig)
    Equipo.objects.filter(pk=equipo.pk).update(
        activo=False,
        persona_id=None,
        estado_inventario=Equipo.ESTADO_DE_BAJA,
    )
    equipo.activo = False
    equipo.persona_id = None
    equipo.estado_inventario = Equipo.ESTADO_DE_BAJA
    return equipo
