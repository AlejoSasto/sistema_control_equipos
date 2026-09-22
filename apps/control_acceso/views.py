from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
from django_ratelimit.decorators import ratelimit
from accounts.alcance import movimientos_visibles
from accounts.decorators import requiere_permiso
from config.pagination import paginate_queryset
from equipos.models import Equipo
from equipos.services import (
    NO_VIGENTE,
    SIN_ASIGNACION,
    VENCIDA,
    asignacion_activa,
    liberar_asignacion_vencida,
    nombre_unidad,
    unidad_de_equipo,
    vigencia_asignacion,
)
from personas.models import CODIGO_VINCULO_EXTERNO
from personas.services import (
    VENCIDA as VISITA_VENCIDA,
    VIGENTE as VISITA_VIGENTE,
    SIN_VISITA,
    cerrar_visita_vencida,
    nombre_dependencia_visita,
    vigencia_visita,
    visita_activa,
)
from .models import Movimiento
from .utils import normalizar_codigo_escaneado


def _contexto_institucional(equipo, asignacion=None):
    es_institucional = equipo.propiedad == Equipo.PROPIEDAD_INSTITUCIONAL
    if not es_institucional:
        return {"es_institucional": False, "nombre_unidad": ""}
    ut, uid = unidad_de_equipo(equipo)
    return {"es_institucional": True, "nombre_unidad": nombre_unidad(ut, uid)}


def _contexto_externo(persona, visita=None):
    if not persona or not getattr(persona, "tipo_vinculo", None):
        return {"es_personal_externo": False}
    if persona.tipo_vinculo.codigo != CODIGO_VINCULO_EXTERNO:
        return {"es_personal_externo": False}
    visita = visita or visita_activa(persona)
    return {
        "es_personal_externo": True,
        "visita_externo": visita,
        "nombre_dependencia_visita": nombre_dependencia_visita(visita) if visita else "",
        "fecha_fin_visita": visita.fecha_fin if visita else None,
    }


def _contexto_otra_sede(request, persona):
    vigilante_persona = getattr(request.user, "persona", None)
    if not vigilante_persona or not persona or not persona.sede_id:
        return {"es_otra_sede": False, "nombre_otra_sede": ""}
    if not vigilante_persona.sede_id:
        return {"es_otra_sede": False, "nombre_otra_sede": ""}
    if vigilante_persona.sede_id == persona.sede_id:
        return {"es_otra_sede": False, "nombre_otra_sede": ""}
    return {
        "es_otra_sede": True,
        "nombre_otra_sede": persona.sede.nombre if persona.sede else "",
    }


def _movimientos_hoy_qs(user, hoy):
    return (
        movimientos_visibles(user)
        .select_related("equipo", "equipo__persona", "usuario_control")
        .filter(timestamp__date=hoy)
    )


def _alerta_render(request, *, equipo, persona, motivo_codigo, motivo_texto, hoy):
    movimiento = Movimiento.objects.create(
        equipo=equipo,
        token_escaneado=str(equipo.token_qr),
        usuario_control=request.user,
        resultado=Movimiento.RESULTADO_ALERTA,
        motivo_alerta=motivo_codigo,
        observacion=f"Alerta: {motivo_texto}",
    )
    movimientos = _movimientos_hoy_qs(request.user, hoy)[:20]
    return render(
        request,
        "control_acceso/partials/resultado_escaneo.html",
        {
            "equipo": equipo,
            "persona": persona,
            "resultado": "alerta",
            "motivo_alerta": motivo_texto,
            "motivo_alerta_codigo": motivo_codigo,
            "movimiento": movimiento,
            "movimientos_hoy": movimientos,
            **_contexto_institucional(equipo),
            **_contexto_externo(persona),
        },
    )


@login_required
@requiere_permiso("control.escanear")
def control_salida_view(request):
    hoy = timezone.localdate()
    movs_hoy = _movimientos_hoy_qs(request.user, hoy)
    movimientos_hoy = movs_hoy[:20]
    total_hoy = movs_hoy.count()
    total_ok = movs_hoy.filter(resultado=Movimiento.RESULTADO_OK).count()
    total_alertas = movs_hoy.filter(
        resultado__in=[Movimiento.RESULTADO_ALERTA, Movimiento.RESULTADO_NO_ENCONTRADO],
    ).count()
    return render(
        request,
        "control_acceso/scanner.html",
        {
            "movimientos_hoy": movimientos_hoy,
            "total_hoy": total_hoy,
            "total_ok": total_ok,
            "total_alertas": total_alertas,
        },
    )


@login_required
@requiere_permiso("control.escanear")
@require_POST
@ratelimit(key="user_or_ip", rate="60/m", method="POST", block=True)
def escanear_qr_salida(request):
    codigo_recibido = normalizar_codigo_escaneado(request.POST.get("codigo", ""))

    if not codigo_recibido:
        return render(
            request,
            "control_acceso/partials/resultado_escaneo.html",
            {"error_mensaje": "Por favor escanee el código QR presentado por la persona."},
        )

    equipo = Equipo.resolver_token_escaneado(codigo_recibido)
    hoy = timezone.localdate()

    if not equipo:
        movimiento = Movimiento.objects.create(
            equipo=None,
            token_escaneado=codigo_recibido[:100],
            usuario_control=request.user,
            resultado=Movimiento.RESULTADO_NO_ENCONTRADO,
            observacion="Código no registrado en el sistema institucional.",
        )
        movimientos_actualizados = _movimientos_hoy_qs(request.user, hoy)[:20]
        return render(
            request,
            "control_acceso/partials/resultado_escaneo.html",
            {
                "codigo_buscado": codigo_recibido,
                "resultado": "no_encontrado",
                "movimiento": movimiento,
                "movimientos_hoy": movimientos_actualizados,
            },
        )

    persona = equipo.persona

    if not equipo.activo:
        return _alerta_render(
            request,
            equipo=equipo,
            persona=persona,
            motivo_codigo=Movimiento.MOTIVO_EQUIPO_INACTIVO,
            motivo_texto="Equipo dado de baja o inactivo",
            hoy=hoy,
        )

    # Institucional: vigencia + cierre automático (doc 15 §5 / §9)
    if equipo.propiedad == Equipo.PROPIEDAD_INSTITUCIONAL:
        ut, uid = unidad_de_equipo(equipo)
        nombre = nombre_unidad(ut, uid)
        asig = asignacion_activa(equipo)
        vig = vigencia_asignacion(asig, hoy)

        if vig == VENCIDA:
            liberar_asignacion_vencida(equipo, hoy=hoy)
            equipo.refresh_from_db()
            persona = None
            texto = (
                f"Asignación institucional vencida — el equipo quedó disponible en {nombre}. "
                "Contactar a la dependencia."
                if nombre
                else "Asignación institucional vencida — el equipo quedó disponible en inventario."
            )
            return _alerta_render(
                request,
                equipo=equipo,
                persona=persona,
                motivo_codigo=Movimiento.MOTIVO_ASIGNACION_VENCIDA,
                motivo_texto=texto,
                hoy=hoy,
            )

        if (
            equipo.estado_inventario == Equipo.ESTADO_DISPONIBLE
            or vig == SIN_ASIGNACION
            or persona is None
        ):
            return _alerta_render(
                request,
                equipo=equipo,
                persona=persona,
                motivo_codigo=Movimiento.MOTIVO_SIN_ASIGNACION_ACTIVA,
                motivo_texto=(
                    f"Equipo en inventario sin asignación activa"
                    + (f" ({nombre})" if nombre else "")
                ),
                hoy=hoy,
            )

        if vig == NO_VIGENTE:
            return _alerta_render(
                request,
                equipo=equipo,
                persona=persona,
                motivo_codigo=Movimiento.MOTIVO_ASIGNACION_NO_VIGENTE,
                motivo_texto="Asignación institucional no vigente todavía",
                hoy=hoy,
            )

    if persona is None:
        return _alerta_render(
            request,
            equipo=equipo,
            persona=None,
            motivo_codigo=Movimiento.MOTIVO_SIN_ASIGNACION_ACTIVA,
            motivo_texto="Equipo sin titular asignado",
            hoy=hoy,
        )

    if not persona.activo:
        return _alerta_render(
            request,
            equipo=equipo,
            persona=persona,
            motivo_codigo=Movimiento.MOTIVO_PERSONA_INACTIVA,
            motivo_texto="Persona inactiva / desvinculada",
            hoy=hoy,
        )

    # Personal externo: visita vigente (doc 16) — no inactiva Persona
    visita = None
    if persona.tipo_vinculo and persona.tipo_vinculo.codigo == CODIGO_VINCULO_EXTERNO:
        visita = visita_activa(persona)
        vig_visita = vigencia_visita(visita, hoy)
        if vig_visita == VISITA_VENCIDA:
            cerrar_visita_vencida(persona, hoy=hoy)
            return _alerta_render(
                request,
                equipo=equipo,
                persona=persona,
                motivo_codigo=Movimiento.MOTIVO_VISITA_VENCIDA,
                motivo_texto="Visita de personal externo vencida — registrar una nueva visita",
                hoy=hoy,
            )
        if vig_visita == SIN_VISITA:
            return _alerta_render(
                request,
                equipo=equipo,
                persona=persona,
                motivo_codigo=Movimiento.MOTIVO_SIN_VISITA_ACTIVA,
                motivo_texto="Sin visita activa — el visitante debe registrar su llegada",
                hoy=hoy,
            )
        if vig_visita != VISITA_VIGENTE:
            return _alerta_render(
                request,
                equipo=equipo,
                persona=persona,
                motivo_codigo=Movimiento.MOTIVO_SIN_VISITA_ACTIVA,
                motivo_texto="Visita de personal externo aún no vigente",
                hoy=hoy,
            )

    ctx_otra = _contexto_otra_sede(request, persona)
    observacion = "Salida autorizada sin novedad."
    if ctx_otra["es_otra_sede"]:
        observacion = f"Salida autorizada — persona de otra sede ({ctx_otra['nombre_otra_sede']})."

    movimiento = Movimiento.objects.create(
        equipo=equipo,
        token_escaneado=str(equipo.token_qr),
        usuario_control=request.user,
        resultado=Movimiento.RESULTADO_OK,
        otra_sede=ctx_otra["es_otra_sede"],
        observacion=observacion,
    )
    movimientos_actualizados = _movimientos_hoy_qs(request.user, hoy)[:20]

    return render(
        request,
        "control_acceso/partials/resultado_escaneo.html",
        {
            "equipo": equipo,
            "persona": persona,
            "resultado": "ok",
            "movimiento": movimiento,
            "movimientos_hoy": movimientos_actualizados,
            **_contexto_institucional(equipo),
            **_contexto_externo(persona, visita),
            **ctx_otra,
        },
    )


@login_required
@requiere_permiso("control.ver_alertas")
def movimientos_list(request):
    query = request.GET.get("q", "").strip()
    resultado_filtro = request.GET.get("resultado", "")
    fecha_filtro = request.GET.get("fecha", "")

    movimientos = movimientos_visibles(request.user).select_related(
        "equipo", "equipo__persona", "usuario_control"
    )

    if query:
        movimientos = movimientos.filter(
            Q(equipo__serial__icontains=query)
            | Q(equipo__persona__nombres__icontains=query)
            | Q(equipo__persona__apellidos__icontains=query)
            | Q(equipo__persona__numero_documento__icontains=query)
            | Q(token_escaneado__icontains=query)
        )

    if resultado_filtro:
        movimientos = movimientos.filter(resultado=resultado_filtro)

    if fecha_filtro:
        movimientos = movimientos.filter(timestamp__date=fecha_filtro)

    page = paginate_queryset(request, movimientos)

    return render(
        request,
        "control_acceso/movimientos_list.html",
        {
            "movimientos": page,
            "page_obj": page,
            "query": query,
            "resultado_filtro": resultado_filtro,
            "fecha_filtro": fecha_filtro,
            "opciones_resultado": Movimiento.OPCIONES_RESULTADO,
        },
    )
