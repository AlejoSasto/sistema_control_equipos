"""Reporte de personas."""

from __future__ import annotations

from collections import Counter
from datetime import date

from personas.models import Persona
from reportes.estilos import COLOR_VERDE
from reportes.filtros import (
    FiltroEstado,
    FiltroFacultad,
    FiltroPrograma,
    FiltroSede,
    FiltroTipoVinculo,
    acotar_por_alcance,
    fusionar_filtros,
)
from reportes.generadores.base import (
    ResultadoReporte,
    abrir_workbook,
    cerrar_workbook,
    insertar_serie_oculta,
    nombre_archivo,
    ref_rango,
    verificar_umbral,
    escribir_tabla,
)


def queryset_personas(user, data):
    f_sede = FiltroSede.from_data(data)
    f_facultad = FiltroFacultad.from_data(data)
    f_programa = FiltroPrograma.from_data(data)
    f_vinculo = FiltroTipoVinculo.from_data(data)
    f_estado = FiltroEstado.from_data(data)

    qs = Persona.objects.select_related("tipo_vinculo", "sede", "programa", "area")
    qs = f_sede.aplicar(qs)
    qs = f_facultad.aplicar(qs)
    qs = f_programa.aplicar(qs)
    qs = f_vinculo.aplicar(qs)
    qs = f_estado.aplicar(qs)
    qs = acotar_por_alcance(user, qs)
    filtros = fusionar_filtros(f_sede, f_facultad, f_programa, f_vinculo, f_estado)
    return qs.order_by("apellidos", "nombres"), filtros


def generar(user, data) -> ResultadoReporte:
    qs, filtros = queryset_personas(user, data)
    total = qs.count()
    verificar_umbral(total)

    buffer, wb, fmts = abrir_workbook()
    hoja = wb.add_worksheet("Datos")
    hoja_g = wb.add_worksheet("Gráficos")
    hoja_s = wb.add_worksheet("_series")
    hoja_s.hide()

    encabezados = [
        "Nombre",
        "Documento",
        "Tipo vínculo",
        "Sede",
        "Programa / Área",
        "Estado",
        "Fecha registro",
    ]
    filas = []
    por_vinculo = Counter()
    por_sede = Counter()

    for p in qs.iterator(chunk_size=2000):
        prog_area = ""
        if p.programa_id:
            prog_area = p.programa.nombre
        elif p.area_id:
            prog_area = p.area.nombre
        filas.append(
            [
                p.nombre_completo,
                p.numero_documento,
                p.tipo_vinculo.nombre if p.tipo_vinculo_id else "",
                p.sede.nombre if p.sede_id else "",
                prog_area,
                "Activo" if p.activo else "Inactivo",
                p.created_at.date() if p.created_at else None,
            ]
        )
        if p.tipo_vinculo_id:
            por_vinculo[p.tipo_vinculo.nombre] += 1
        sede = p.sede.nombre if p.sede_id else "(Sin sede)"
        por_sede[sede] += 1

    escribir_tabla(
        hoja,
        encabezados,
        filas,
        fmts,
        tipos_col=["celda", "texto", "celda", "celda", "celda", "celda", "fecha"],
    )

    # Barras por vínculo
    vinc = [v for v, _ in por_vinculo.most_common()]
    vals_v = [por_vinculo[v] for v in vinc]
    r1, r2, col_cat, col_map = insertar_serie_oculta(
        hoja_s, 0, vinc, {"Personas": vals_v}, fmts
    )
    chart_v = wb.add_chart({"type": "column"})
    chart_v.add_series(
        {
            "name": "Por tipo de vínculo",
            "categories": ref_rango("_series", r1, col_cat, r2),
            "values": ref_rango("_series", r1, col_map["Personas"], r2),
            "fill": {"color": COLOR_VERDE},
        }
    )
    chart_v.set_title({"name": "Personas por tipo de vínculo"})
    chart_v.set_size({"width": 720, "height": 320})
    hoja_g.insert_chart("B2", chart_v)

    # Barras por sede
    sedes = [s for s, _ in por_sede.most_common()]
    vals_s = [por_sede[s] for s in sedes]
    r1b, r2b, col_cat_b, col_map_b = insertar_serie_oculta(
        hoja_s, 4, sedes, {"Personas": vals_s}, fmts
    )
    chart_s = wb.add_chart({"type": "column"})
    chart_s.add_series(
        {
            "name": "Por sede",
            "categories": ref_rango("_series", r1b, col_cat_b, r2b),
            "values": ref_rango("_series", r1b, col_map_b["Personas"], r2b),
            "fill": {"color": COLOR_VERDE},
        }
    )
    chart_s.set_title({"name": "Personas por sede"})
    chart_s.set_size({"width": 720, "height": 320})
    hoja_g.insert_chart("B20", chart_s)

    # Línea acumulada por mes
    meses_count = Counter()
    for row in qs.values_list("created_at", flat=True).iterator(chunk_size=2000):
        if row:
            key = date(row.year, row.month, 1)
            meses_count[key] += 1
    meses = sorted(meses_count.keys())
    acumulado = []
    running = 0
    labels = []
    for m in meses:
        running += meses_count[m]
        acumulado.append(running)
        labels.append(m.strftime("%Y-%m"))
    r1c, r2c, col_cat_c, col_map_c = insertar_serie_oculta(
        hoja_s, 8, labels, {"Acumulado": acumulado}, fmts
    )
    chart_line = wb.add_chart({"type": "line"})
    chart_line.add_series(
        {
            "name": "Registros acumulados",
            "categories": ref_rango("_series", r1c, col_cat_c, r2c),
            "values": ref_rango("_series", r1c, col_map_c["Acumulado"], r2c),
            "line": {"color": COLOR_VERDE},
        }
    )
    chart_line.set_title({"name": "Crecimiento acumulado de personas"})
    chart_line.set_size({"width": 720, "height": 320})
    hoja_g.insert_chart("B38", chart_line)

    contenido = cerrar_workbook(buffer, wb)
    return ResultadoReporte(
        contenido=contenido,
        nombre_archivo=nombre_archivo("personas"),
        filas=total,
        filtros=filtros,
    )
