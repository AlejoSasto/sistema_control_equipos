"""
Alcance jerárquico por usuario (GLOBAL / SEDE / FACULTAD / PROGRAMA / DEPENDENCIA).

Única fuente de verdad para filtrar querysets en panel, reportes y control de acceso.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import wraps

from django.conf import settings
from django.db.models import Q, QuerySet

from organizacion.models import (
    UNIDAD_AREA,
    UNIDAD_FACULTAD,
    UNIDAD_PROGRAMA,
    AlcanceUsuario,
    Area,
    Decanatura,
    Programa,
    Sede,
)


@dataclass
class AlcanceEfectivo:
    es_global: bool = False
    sedes: set[int] = field(default_factory=set)
    facultades: set[int] = field(default_factory=set)
    programas: set[int] = field(default_factory=set)
    areas: set[int] = field(default_factory=set)

    def vacio(self) -> bool:
        return not self.es_global and not (
            self.sedes or self.facultades or self.programas or self.areas
        )


def _alcance_desde_bd(usuario_id: int) -> AlcanceEfectivo:
    filas = AlcanceUsuario.objects.filter(usuario_id=usuario_id, activo=True)
    alcance = AlcanceEfectivo()
    for fila in filas:
        if fila.nivel == AlcanceUsuario.NIVEL_GLOBAL:
            return AlcanceEfectivo(es_global=True)
        if fila.nivel == AlcanceUsuario.NIVEL_SEDE and fila.objeto_id:
            alcance.sedes.add(fila.objeto_id)
        elif fila.nivel == AlcanceUsuario.NIVEL_FACULTAD and fila.objeto_id:
            alcance.facultades.add(fila.objeto_id)
        elif fila.nivel == AlcanceUsuario.NIVEL_PROGRAMA and fila.objeto_id:
            alcance.programas.add(fila.objeto_id)
        elif fila.nivel == AlcanceUsuario.NIVEL_DEPENDENCIA and fila.objeto_id:
            alcance.areas.add(fila.objeto_id)
    return alcance


def alcance_de(user) -> AlcanceEfectivo:
    if not user or not getattr(user, "is_authenticated", False):
        return AlcanceEfectivo()
    if getattr(user, "is_superuser", False):
        return AlcanceEfectivo(es_global=True)
    cache = getattr(user, "_alcance_cache", None)
    if cache is not None:
        return cache
    alcance = _alcance_desde_bd(user.pk)
    user._alcance_cache = alcance
    return alcance


def alcance_es_global(user) -> bool:
    return alcance_de(user).es_global


def invalidar_cache_alcance(user) -> None:
    if user is not None:
        user._alcance_cache = None


def _programas_en_sedes(sede_ids: set[int]) -> set[int]:
    if not sede_ids:
        return set()
    return set(
        Programa.objects.filter(sede_id__in=sede_ids, activo=True).values_list("pk", flat=True)
    )


def _programas_en_facultades(facultad_ids: set[int]) -> set[int]:
    if not facultad_ids:
        return set()
    return set(
        Programa.objects.filter(facultad_id__in=facultad_ids, activo=True).values_list("pk", flat=True)
    )


def _q_persona(alcance: AlcanceEfectivo) -> Q:
    q = Q()
    if alcance.sedes:
        q |= Q(sede_id__in=alcance.sedes)
    if alcance.facultades:
        q |= Q(programa__facultad_id__in=alcance.facultades)
    if alcance.programas:
        q |= Q(programa_id__in=alcance.programas)
    if alcance.areas:
        q |= Q(area_id__in=alcance.areas)
    return q


def _q_equipo(alcance: AlcanceEfectivo) -> Q:
    q = Q()
    prog_sede = _programas_en_sedes(alcance.sedes)
    prog_fac = _programas_en_facultades(alcance.facultades)

    if alcance.sedes:
        q |= Q(persona__sede_id__in=alcance.sedes)
        q |= Q(unidad_tipo=UNIDAD_PROGRAMA, unidad_id__in=prog_sede)
    if alcance.facultades:
        q |= Q(persona__programa__facultad_id__in=alcance.facultades)
        q |= Q(unidad_tipo=UNIDAD_FACULTAD, unidad_id__in=alcance.facultades)
        q |= Q(unidad_tipo=UNIDAD_PROGRAMA, unidad_id__in=prog_fac)
    if alcance.programas:
        q |= Q(persona__programa_id__in=alcance.programas)
        q |= Q(unidad_tipo=UNIDAD_PROGRAMA, unidad_id__in=alcance.programas)
    if alcance.areas:
        q |= Q(persona__area_id__in=alcance.areas)
        q |= Q(unidad_tipo=UNIDAD_AREA, unidad_id__in=alcance.areas)
    return q


def _q_movimiento(alcance: AlcanceEfectivo) -> Q:
    q = Q()
    prog_sede = _programas_en_sedes(alcance.sedes)
    prog_fac = _programas_en_facultades(alcance.facultades)

    if alcance.sedes:
        q |= Q(equipo__persona__sede_id__in=alcance.sedes)
        q |= Q(equipo__unidad_tipo=UNIDAD_PROGRAMA, equipo__unidad_id__in=prog_sede)
    if alcance.facultades:
        q |= Q(equipo__persona__programa__facultad_id__in=alcance.facultades)
        q |= Q(equipo__unidad_tipo=UNIDAD_FACULTAD, equipo__unidad_id__in=alcance.facultades)
        q |= Q(equipo__unidad_tipo=UNIDAD_PROGRAMA, equipo__unidad_id__in=prog_fac)
    if alcance.programas:
        q |= Q(equipo__persona__programa_id__in=alcance.programas)
        q |= Q(equipo__unidad_tipo=UNIDAD_PROGRAMA, equipo__unidad_id__in=alcance.programas)
    if alcance.areas:
        q |= Q(equipo__persona__area_id__in=alcance.areas)
        q |= Q(equipo__unidad_tipo=UNIDAD_AREA, equipo__unidad_id__in=alcance.areas)
    return q


def _q_usuario(alcance: AlcanceEfectivo) -> Q:
    q = Q()
    if alcance.sedes:
        q |= Q(persona__sede_id__in=alcance.sedes)
    if alcance.facultades:
        q |= Q(persona__programa__facultad_id__in=alcance.facultades)
    if alcance.programas:
        q |= Q(persona__programa_id__in=alcance.programas)
    if alcance.areas:
        q |= Q(persona__area_id__in=alcance.areas)
    return q


def _q_programa(alcance: AlcanceEfectivo) -> Q:
    q = Q()
    if alcance.sedes:
        q |= Q(sede_id__in=alcance.sedes)
    if alcance.facultades:
        q |= Q(facultad_id__in=alcance.facultades)
    if alcance.programas:
        q |= Q(pk__in=alcance.programas)
    return q


def _q_sede(alcance: AlcanceEfectivo) -> Q:
    if alcance.sedes:
        return Q(pk__in=alcance.sedes)
    return Q(pk__in=[])


def _q_facultad(alcance: AlcanceEfectivo) -> Q:
    q = Q()
    if alcance.facultades:
        q |= Q(pk__in=alcance.facultades)
    if alcance.programas:
        fac_ids = Programa.objects.filter(pk__in=alcance.programas).values_list("facultad_id", flat=True)
        q |= Q(pk__in=set(fac_ids))
    if alcance.sedes:
        fac_ids = Programa.objects.filter(sede_id__in=alcance.sedes).values_list("facultad_id", flat=True)
        q |= Q(pk__in=set(fac_ids))
    return q


def _q_area(alcance: AlcanceEfectivo) -> Q:
    if alcance.areas:
        return Q(pk__in=alcance.areas)
    return Q(pk__in=[])


def _q_visita_externo(alcance: AlcanceEfectivo) -> Q:
    q = Q()
    if alcance.sedes:
        q |= Q(sede_id__in=alcance.sedes)
    if alcance.areas:
        q |= Q(unidad_tipo=UNIDAD_AREA, unidad_id__in=alcance.areas)
    if alcance.programas:
        q |= Q(unidad_tipo=UNIDAD_PROGRAMA, unidad_id__in=alcance.programas)
    if alcance.facultades:
        q |= Q(unidad_tipo=UNIDAD_FACULTAD, unidad_id__in=alcance.facultades)
    return q


MODEL_FILTERS = {
    "personas.Persona": _q_persona,
    "equipos.Equipo": _q_equipo,
    "control_acceso.Movimiento": _q_movimiento,
    "accounts.Usuario": _q_usuario,
    "organizacion.Programa": _q_programa,
    "organizacion.Sede": _q_sede,
    "organizacion.Decanatura": _q_facultad,
    "organizacion.Area": _q_area,
    "personas.VisitaExterno": _q_visita_externo,
}


def _model_key(model) -> str:
    return f"{model._meta.app_label}.{model.__name__}"


def aplicar_alcance(user, qs: QuerySet) -> QuerySet:
    """Filtra un queryset según el alcance del usuario."""
    alcance = alcance_de(user)
    if alcance.es_global:
        return qs

    key = _model_key(qs.model)
    builder = MODEL_FILTERS.get(key)
    if builder is None:
        if settings.DEBUG:
            raise RuntimeError(
                f"Modelo {key} no registrado en MODEL_FILTERS (alcance). "
                "Regístrelo en accounts/alcance.py."
            )
        return qs

    filtro = builder(alcance)
    if filtro == Q():
        return qs.none()
    return qs.filter(filtro).distinct()


def puede_ver_objeto(user, obj) -> bool:
    if not obj:
        return False
    model = obj.__class__
    qs = aplicar_alcance(user, model.objects.filter(pk=obj.pk))
    return qs.exists()


def puede_asignar_alcance(actor, nivel: str, objeto_id: int | None) -> bool:
    """El actor no puede otorgar un alcance más amplio que el suyo."""
    if not actor or not getattr(actor, "is_authenticated", False):
        return False
    if getattr(actor, "is_superuser", False):
        return True
    alcance_actor = alcance_de(actor)
    if alcance_actor.es_global:
        return True
    if nivel == AlcanceUsuario.NIVEL_GLOBAL:
        return False
    if nivel == AlcanceUsuario.NIVEL_SEDE:
        return objeto_id in alcance_actor.sedes
    if nivel == AlcanceUsuario.NIVEL_FACULTAD:
        return objeto_id in alcance_actor.facultades
    if nivel == AlcanceUsuario.NIVEL_PROGRAMA:
        return objeto_id in alcance_actor.programas
    if nivel == AlcanceUsuario.NIVEL_DEPENDENCIA:
        return objeto_id in alcance_actor.areas
    return False


def _resolver_nombre_objeto(nivel: str, objeto_id: int | None) -> str:
    if nivel == AlcanceUsuario.NIVEL_GLOBAL:
        return "Global"
    if not objeto_id:
        return "—"
    if nivel == AlcanceUsuario.NIVEL_SEDE:
        obj = Sede.objects.filter(pk=objeto_id).first()
        return obj.nombre if obj else f"Sede #{objeto_id}"
    if nivel == AlcanceUsuario.NIVEL_FACULTAD:
        obj = Decanatura.objects.filter(pk=objeto_id).first()
        return obj.nombre if obj else f"Facultad #{objeto_id}"
    if nivel == AlcanceUsuario.NIVEL_PROGRAMA:
        obj = Programa.objects.filter(pk=objeto_id).first()
        return obj.nombre if obj else f"Programa #{objeto_id}"
    if nivel == AlcanceUsuario.NIVEL_DEPENDENCIA:
        obj = Area.objects.filter(pk=objeto_id).first()
        return f"{obj.codigo} — {obj.nombre}" if obj else f"Área #{objeto_id}"
    return str(objeto_id)


def etiqueta_alcance(user) -> str:
    alcance = alcance_de(user)
    if alcance.es_global:
        return "Alcance: Global"
    partes = []
    for sid in sorted(alcance.sedes):
        partes.append(f"Sede {_resolver_nombre_objeto(AlcanceUsuario.NIVEL_SEDE, sid)}")
    for fid in sorted(alcance.facultades):
        partes.append(f"Facultad {_resolver_nombre_objeto(AlcanceUsuario.NIVEL_FACULTAD, fid)}")
    for pid in sorted(alcance.programas):
        partes.append(f"Programa {_resolver_nombre_objeto(AlcanceUsuario.NIVEL_PROGRAMA, pid)}")
    for aid in sorted(alcance.areas):
        partes.append(f"Área {_resolver_nombre_objeto(AlcanceUsuario.NIVEL_DEPENDENCIA, aid)}")
    if not partes:
        return "Alcance: sin definir"
    return "Alcance: " + ", ".join(partes)


def descripcion_fila_alcance(fila: AlcanceUsuario) -> str:
    nivel_label = dict(AlcanceUsuario.OPCIONES_NIVEL).get(fila.nivel, fila.nivel)
    if fila.nivel == AlcanceUsuario.NIVEL_GLOBAL:
        return nivel_label
    return f"{nivel_label}: {_resolver_nombre_objeto(fila.nivel, fila.objeto_id)}"


# --- Helpers de conveniencia ---

def personas_visibles(user):
    from personas.models import Persona

    return aplicar_alcance(user, Persona.objects.all())


def equipos_visibles(user):
    from equipos.models import Equipo

    return aplicar_alcance(user, Equipo.objects.all())


def movimientos_visibles(user):
    from control_acceso.models import Movimiento

    return aplicar_alcance(user, Movimiento.objects.all())


def usuarios_visibles(user):
    from accounts.models import Usuario

    return aplicar_alcance(user, Usuario.objects.all())


def sedes_visibles(user):
    return aplicar_alcance(user, Sede.objects.filter(activo=True))


def facultades_visibles(user):
    return aplicar_alcance(user, Decanatura.objects.filter(activo=True))


def programas_visibles(user):
    return aplicar_alcance(
        user, Programa.objects.filter(activo=True).select_related("sede", "facultad")
    )


def areas_visibles(user):
    return aplicar_alcance(user, Area.objects.filter(activo=True))


def visitas_visibles(user):
    from personas.models import VisitaExterno

    return aplicar_alcance(user, VisitaExterno.objects.all())


def con_alcance(view_func):
    """Inyecta request.alcance en la vista."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        request.alcance = alcance_de(request.user)
        return view_func(request, *args, **kwargs)

    return _wrapped


class AlcanceMixin:
    """Mixin para CBV: filtra get_queryset()."""

    def get_queryset(self):
        qs = super().get_queryset()
        return aplicar_alcance(self.request.user, qs)
