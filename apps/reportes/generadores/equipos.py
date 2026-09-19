"""Reporte de equipos."""

from __future__ import annotations

from collections import Counter

from equipos.models import Equipo
from reportes.estilos import COLOR_VERDE
from reportes.filtros import (
    FiltroEstado,
    FiltroPropiedad,
    FiltroSede,
    FiltroTipoEquipo,
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

TIPO_LABEL = dict(Equipo.OPCIONES_TIPO)
PROP_LABEL = dict(Equipo.OPCIONES_PROPIEDAD)


def queryset_equipos(user, data):
    f_sede = FiltroSede.from_data(data, lookup="persona__sede_id")
    f_tipo = FiltroTipoEquipo.from_data(data)
    f_prop = FiltroPropiedad.from_data(data)
    f_estado = FiltroEstado.from_data(data)
    f_vinculo = FiltroTipoVinculo.from_data(data, lookup="persona__tipo_vinculo_id__in")

    qs = Equipo.objects.select_related(
        "persona__sede", "persona__tipo_vinculo", "dependencia"
    )
    qs = f_sede.aplicar(qs)
    qs = f_tipo.aplicar(qs)
    qs = f_prop.aplicar(qs)
    qs = f_estado.aplicar(qs)
    qs = f_vinculo.aplicar(qs)
    qs = acotar_por_alcance(user, qs)
    filtros = fusionar_filtros(f_sede, f_tipo, f_prop, f_estado, f_vinculo)
    return qs.order_by("serial"), filtros


def generar(user, data) -> ResultadoReporte:
    qs, filtros = queryset_equipos(user, data)
    total = qs.count()
    verificar_umbral(total)

    buffer, wb, fmts = abrir_workbook()
    hoja = wb.add_worksheet("Datos")
    hoja_g = wb.add_worksheet("Gráficos")
    hoja_s = wb.add_worksheet("_series")
    hoja_s.hide()

    encabezados = [
        "Serial",
        "Marca",
        "Modelo",
        "Tipo",
        "Propiedad",
        "Dueño",
        "Sede",
        "Estado",
        "Fecha registro",
    ]
    filas = []
    por_sede = Counter()
    por_prop = Counter()
    por_marca = Counter()

    for e in qs.iterator(chunk_size=2000):
        sede = e.persona.sede.nombre if e.persona_id and e.persona.sede_id else "(Sin sede)"
        filas.append(
            [
                e.serial,
                e.marca,
                e.modelo,
                TIPO_LABEL.get(e.tipo, e.tipo),
                PROP_LABEL.get(e.propiedad, e.propiedad),
                e.persona.nombre_completo if e.persona_id else "",
                sede,
                "Activo" if e.activo else "Inactivo",
                e.created_at.date() if e.created_at else None,
            ]
        )
        por_sede[sede] += 1
        por_prop[e.propiedad] += 1
        por_marca[e.marca] += 1

    escribir_tabla(
        hoja,
        encabezados,
        filas,
        fmts,
        tipos_col=["texto", "celda", "celda", "celda", "celda", "celda", "celda", "celda", "fecha"],
    )

    # Barras horizontales por sede
    sedes = [s for s, _ in por_sede.most_common()]
    vals = [por_sede[s] for s in sedes]
    r1, r2, col_cat, col_map = insertar_serie_oculta(
        hoja_s, 0, sedes, {"Equipos": vals}, fmts
    )
    chart_bar = wb.add_chart({"type": "bar"})
    chart_bar.add_series(
        {
            "name": "Equipos por sede",
            "categories": ref_rango("_series", r1, col_cat, r2),
            "values": ref_rango("_series", r1, col_map["Equipos"], r2),
            "fill": {"color": COLOR_VERDE},
        }
    )
    chart_bar.set_title({"name": "Cantidad de equipos por sede"})
    chart_bar.set_size({"width": 720, "height": 320})
    hoja_g.insert_chart("B2", chart_bar)

    # Pastel institucional vs personal
    cats_pie = ["Institucional", "Personal"]
    vals_pie = [
        por_prop.get(Equipo.PROPIEDAD_INSTITUCIONAL, 0),
        por_prop.get(Equipo.PROPIEDAD_PERSONAL, 0),
    ]
    r1b, r2b, col_cat_b, col_map_b = insertar_serie_oculta(
        hoja_s, 4, cats_pie, {"Total": vals_pie}, fmts
    )
    chart_pie = wb.add_chart({"type": "pie"})
    chart_pie.add_series(
        {
            "name": "Propiedad",
            "categories": ref_rango("_series", r1b, col_cat_b, r2b),
            "values": ref_rango("_series", r1b, col_map_b["Total"], r2b),
        }
    )
    chart_pie.set_title({"name": "Institucional vs personal"})
    chart_pie.set_size({"width": 480, "height": 320})
    hoja_g.insert_chart("B20", chart_pie)

    # Top 10 marcas
    top_marcas = por_marca.most_common(10)
    marcas = [m for m, _ in top_marcas]
    vals_m = [c for _, c in top_marcas]
    r1c, r2c, col_cat_c, col_map_c = insertar_serie_oculta(
        hoja_s, 8, marcas, {"Equipos": vals_m}, fmts
    )
    chart_marcas = wb.add_chart({"type": "column"})
    chart_marcas.add_series(
        {
            "name": "Equipos por marca",
            "categories": ref_rango("_series", r1c, col_cat_c, r2c),
            "values": ref_rango("_series", r1c, col_map_c["Equipos"], r2c),
            "fill": {"color": COLOR_VERDE},
        }
    )
    chart_marcas.set_title({"name": "Equipos por marca (top 10)"})
    chart_marcas.set_size({"width": 720, "height": 320})
    hoja_g.insert_chart("B38", chart_marcas)

    contenido = cerrar_workbook(buffer, wb)
    return ResultadoReporte(
        contenido=contenido,
        nombre_archivo=nombre_archivo("equipos"),
        filas=total,
        filtros=filtros,
    )
