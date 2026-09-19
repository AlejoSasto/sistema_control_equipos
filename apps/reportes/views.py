"""Vistas del módulo de reportes Excel."""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render

from accounts.decorators import requiere_permiso
from accounts.models import Usuario
from auditoria.models import AuditoriaCambio
from auditoria.services import registrar_cambio
from control_acceso.models import Movimiento
from equipos.models import Equipo
from organizacion.models import Area, Decanatura, Programa, Sede
from personas.models import TipoVinculo
from reportes.filtros import FiltroError, defaults_fecha_rango
from reportes.generadores import GENERADORES, TIPOS_REPORTE
from reportes.generadores.base import UmbralExcedido


def _catalogos_contexto():
    return {
        "sedes": Sede.objects.filter(activo=True).order_by("nombre"),
        "facultades": Decanatura.objects.filter(activo=True).order_by("nombre"),
        "programas": Programa.objects.filter(activo=True)
        .select_related("sede", "facultad")
        .order_by("nombre"),
        "areas": Area.objects.filter(activo=True).order_by("nombre"),
        "tipos_vinculo": TipoVinculo.objects.filter(activo=True).order_by("nombre"),
        "opciones_resultado": Movimiento.OPCIONES_RESULTADO,
        "opciones_tipo_equipo": Equipo.OPCIONES_TIPO,
        "opciones_propiedad": Equipo.OPCIONES_PROPIEDAD,
        "opciones_alerta": [
            (Movimiento.RESULTADO_ALERTA, "Alerta de seguridad"),
            (Movimiento.RESULTADO_NO_ENCONTRADO, "No encontrado"),
        ],
        "celadores": Usuario.objects.filter(
            roles__permisos__codigo="control.escanear",
            is_active=True,
            activo=True,
        )
        .distinct()
        .order_by("username"),
    }


def _meta_tipo(tipo: str) -> dict | None:
    for item in TIPOS_REPORTE:
        if item["slug"] == tipo:
            return item
    return None


@requiere_permiso("reportes.ver")
def index(request):
    return render(request, "reportes/index.html", {"tipos": TIPOS_REPORTE})


@requiere_permiso("reportes.ver")
def configurar(request, tipo: str):
    meta = _meta_tipo(tipo)
    if not meta or tipo not in GENERADORES:
        messages.error(request, "Tipo de reporte no válido.")
        return redirect("reportes:index")

    fecha_inicio, fecha_fin = defaults_fecha_rango(30)
    ctx = {
        "meta": meta,
        "tipo": tipo,
        "fecha_inicio": request.GET.get("fecha_inicio", fecha_inicio),
        "fecha_fin": request.GET.get("fecha_fin", fecha_fin),
        "puede_exportar": request.user.puede_exportar_reportes,
        **_catalogos_contexto(),
    }
    return render(request, f"reportes/form_{tipo}.html", ctx)


@requiere_permiso("reportes.exportar")
def exportar(request, tipo: str):
    meta = _meta_tipo(tipo)
    if not meta or tipo not in GENERADORES:
        messages.error(request, "Tipo de reporte no válido.")
        return redirect("reportes:index")

    if request.method != "POST":
        return redirect("reportes:configurar", tipo=tipo)

    data = request.POST
    try:
        resultado = GENERADORES[tipo](request.user, data)
    except FiltroError as exc:
        messages.error(request, str(exc))
        return redirect("reportes:configurar", tipo=tipo)
    except UmbralExcedido as exc:
        messages.error(request, str(exc))
        return redirect("reportes:configurar", tipo=tipo)
    except Exception:
        messages.error(
            request,
            "No se pudo generar el reporte. Revise los filtros e intente de nuevo.",
        )
        return redirect("reportes:configurar", tipo=tipo)

    registrar_cambio(
        usuario=request.user,
        entidad="reporte",
        entidad_id=None,
        accion=AuditoriaCambio.ACCION_EXPORTAR,
        detalle={
            "tipo_reporte": tipo,
            "filtros_aplicados": resultado.filtros,
            "filas": resultado.filas,
            "archivo": resultado.nombre_archivo,
        },
        request=request,
    )

    response = HttpResponse(
        resultado.contenido,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{resultado.nombre_archivo}"'
    return response
