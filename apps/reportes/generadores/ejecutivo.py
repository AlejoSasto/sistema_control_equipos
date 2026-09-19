"""Reporte ejecutivo / resumen gerencial."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from control_acceso.models import Movimiento
from equipos.models import Equipo
from personas.models import Persona
from reportes.estilos import COLOR_VERDE
from reportes.filtros import FiltroFecha, acotar_por_alcance, fusionar_filtros
from reportes.generadores.base import (
    ResultadoReporte,
    abrir_workbook,
    cerrar_workbook,
    insertar_serie_oculta,
    nombre_archivo,
    ref_rango,
    verificar_umbral,
)


def generar(user, data) -> ResultadoReporte:
    f_fecha = FiltroFecha.from_data(data, obligatorio=True)
    f_fecha.validar()
    filtros = fusionar_filtros(f_fecha)

    movs = Movimiento.objects.all()
    movs = f_fecha.aplicar(movs, campo="timestamp")
    movs = acotar_por_alcance(user, movs)
    total_movs = movs.count()
    verificar_umbral(total_movs)

    personas_activas = Persona.objects.filter(activo=True).count()
    equipos_total = Equipo.objects.count()
    eq_inst = Equipo.objects.filter(propiedad=Equipo.PROPIEDAD_INSTITUCIONAL).count()
    eq_pers = Equipo.objects.filter(propiedad=Equipo.PROPIEDAD_PERSONAL).count()
    pct_inst = (eq_inst / equipos_total) if equipos_total else 0.0
    pct_pers = (eq_pers / equipos_total) if equipos_total else 0.0

    alertas = movs.exclude(resultado=Movimiento.RESULTADO_OK).count()
    tasa_alerta = (alertas / total_movs) if total_movs else 0.0

    buffer, wb, fmts = abrir_workbook()
    hoja = wb.add_worksheet("Resumen")
    hoja_s = wb.add_worksheet("_series")
    hoja_s.hide()

    # Tarjetas KPI
    kpis = [
        ("Personas activas", personas_activas),
        ("Equipos registrados", equipos_total),
        ("% Institucionales", f"{pct_inst * 100:.1f}%"),
        ("% Personales", f"{pct_pers * 100:.1f}%"),
        ("Movimientos del periodo", total_movs),
        ("Tasa de alertas", f"{tasa_alerta * 100:.1f}%"),
    ]
    for i, (label, valor) in enumerate(kpis):
        col = (i % 3) * 3
        row = (i // 3) * 4
        hoja.merge_range(row, col, row, col + 2, label, fmts["tarjeta_label"])
        hoja.merge_range(row + 1, col, row + 2, col + 2, valor, fmts["tarjeta_valor"])

    # Movimientos por semana + tasa alerta
    por_semana = defaultdict(lambda: {"total": 0, "alertas": 0})
    for m in movs.only("timestamp", "resultado").iterator(chunk_size=2000):
        ts = timezone.localtime(m.timestamp)
        # lunes de la semana ISO
        lunes = (ts.date() - timedelta(days=ts.weekday())).isoformat()
        por_semana[lunes]["total"] += 1
        if m.resultado != Movimiento.RESULTADO_OK:
            por_semana[lunes]["alertas"] += 1

    semanas = sorted(por_semana.keys())
    totals = [por_semana[s]["total"] for s in semanas]
    tasas = [
        (por_semana[s]["alertas"] / por_semana[s]["total"]) if por_semana[s]["total"] else 0
        for s in semanas
    ]
    r1, r2, col_cat, col_map = insertar_serie_oculta(
        hoja_s,
        0,
        semanas,
        {"Movimientos": totals, "Tasa alerta": tasas},
        fmts,
    )
    chart_combo = wb.add_chart({"type": "column"})
    chart_combo.add_series(
        {
            "name": "Movimientos",
            "categories": ref_rango("_series", r1, col_cat, r2),
            "values": ref_rango("_series", r1, col_map["Movimientos"], r2),
            "fill": {"color": COLOR_VERDE},
        }
    )
    line = wb.add_chart({"type": "line"})
    line.add_series(
        {
            "name": "Tasa de alerta",
            "categories": ref_rango("_series", r1, col_cat, r2),
            "values": ref_rango("_series", r1, col_map["Tasa alerta"], r2),
            "y2_axis": True,
            "line": {"color": "#C0392B"},
        }
    )
    chart_combo.combine(line)
    chart_combo.set_title({"name": "Movimientos por semana y tasa de alerta"})
    chart_combo.set_y2_axis({"name": "Tasa alerta", "num_format": "0%"})
    chart_combo.set_size({"width": 780, "height": 360})
    hoja.insert_chart("A10", chart_combo)

    # Personas por sede
    por_sede = (
        Persona.objects.filter(activo=True)
        .values("sede__nombre")
        .annotate(n=Count("id"))
        .order_by("-n")
    )
    labels = [r["sede__nombre"] or "(Sin sede)" for r in por_sede]
    vals = [r["n"] for r in por_sede]
    r1b, r2b, col_cat_b, col_map_b = insertar_serie_oculta(
        hoja_s, 5, labels, {"Personas": vals}, fmts
    )
    chart_sede = wb.add_chart({"type": "column"})
    chart_sede.add_series(
        {
            "name": "Personas activas",
            "categories": ref_rango("_series", r1b, col_cat_b, r2b),
            "values": ref_rango("_series", r1b, col_map_b["Personas"], r2b),
            "fill": {"color": COLOR_VERDE},
        }
    )
    chart_sede.set_title({"name": "Personas activas por sede"})
    chart_sede.set_size({"width": 720, "height": 320})
    hoja.insert_chart("A30", chart_sede)

    for col in range(9):
        hoja.set_column(col, col, 14)

    contenido = cerrar_workbook(buffer, wb)
    return ResultadoReporte(
        contenido=contenido,
        nombre_archivo=nombre_archivo("ejecutivo"),
        filas=total_movs,
        filtros=filtros,
    )
