"""Vistas del dashboard de administrador (doc 13)."""

from __future__ import annotations

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse

from accounts.alcance import sedes_visibles
from accounts.decorators import requiere_permiso
from control_acceso.models import Movimiento
from personas.models import TipoVinculo
from reportes.dashboard import (
    contexto_kpis,
    parse_dashboard_filtros,
    series_graficos,
)
from reportes.filtros import FiltroError


def _catalogos(user):
    return {
        "sedes": sedes_visibles(user).order_by("nombre"),
        "tipos_vinculo": TipoVinculo.objects.filter(activo=True).order_by("nombre"),
        "opciones_resultado": Movimiento.OPCIONES_RESULTADO,
        "presets": [
            ("hoy", "Hoy"),
            ("ayer", "Ayer"),
            ("7d", "Últimos 7 días"),
            ("mes", "Este mes"),
            ("custom", "Personalizado"),
        ],
    }


@requiere_permiso("reportes.ver")
def dashboard(request):
    try:
        filtros = parse_dashboard_filtros(request.GET or {"preset": "hoy"})
    except FiltroError as exc:
        messages.error(request, str(exc))
        filtros = parse_dashboard_filtros({"preset": "hoy"})

    ctx = {
        **contexto_kpis(request.user, filtros),
        **_catalogos(request.user),
        "datos_url": reverse("panel:dashboard_datos"),
        "parcial_url": reverse("panel:dashboard_parcial"),
        "selected_sede": filtros.sede.sede_id,
        "selected_vinculos": set(filtros.vinculo.ids),
        "selected_resultados": set(filtros.resultado.resultados),
    }
    return render(request, "reportes/dashboard.html", ctx)


@requiere_permiso("reportes.ver")
def dashboard_parcial(request):
    try:
        filtros = parse_dashboard_filtros(request.GET)
    except FiltroError as exc:
        return render(
            request,
            "reportes/partials/dashboard_error.html",
            {"mensaje": str(exc)},
            status=400,
        )

    ctx = {
        **contexto_kpis(request.user, filtros),
        "datos_url": reverse("panel:dashboard_datos"),
    }
    return render(request, "reportes/partials/dashboard_contenido.html", ctx)


@requiere_permiso("reportes.ver")
def dashboard_datos(request):
    try:
        filtros = parse_dashboard_filtros(request.GET)
    except FiltroError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    data = series_graficos(request.user, filtros)
    return JsonResponse(data)
