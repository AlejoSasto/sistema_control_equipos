"""Reporte de movimientos de control de salida."""

from __future__ import annotations

from collections import Counter, defaultdict

from django.utils import timezone

from control_acceso.models import Movimiento
from reportes.estilos import COLOR_VERDE
from reportes.filtros import (
    FiltroCelador,
    FiltroFecha,
    FiltroResultado,
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


RESULTADO_LABEL = dict(Movimiento.OPCIONES_RESULTADO)


def queryset_movimientos(user, data):
    f_fecha = FiltroFecha.from_data(data, obligatorio=True)
    f_sede = FiltroSede.from_data(data, lookup="equipo__persona__sede_id")
    f_resultado = FiltroResultado.from_data(data)
    f_vinculo = FiltroTipoVinculo.from_data(data, lookup="equipo__persona__tipo_vinculo_id__in")
    f_celador = FiltroCelador.from_data(data)

    qs = Movimiento.objects.select_related(
        "equipo__persona__sede",
        "equipo__persona__tipo_vinculo",
        "usuario_control",
    )
    qs = f_fecha.aplicar(qs, campo="timestamp")
    qs = f_sede.aplicar(qs)
    qs = f_resultado.aplicar(qs)
    qs = f_vinculo.aplicar(qs)
    qs = f_celador.aplicar(qs)
    qs = acotar_por_alcance(user, qs)
    filtros = fusionar_filtros(f_fecha, f_sede, f_resultado, f_vinculo, f_celador)
    return qs.order_by("timestamp"), filtros


def generar(user, data) -> ResultadoReporte:
    qs, filtros = queryset_movimientos(user, data)
    total = qs.count()
    verificar_umbral(total)

    buffer, wb, fmts = abrir_workbook()
    hoja = wb.add_worksheet("Datos")
    hoja_g = wb.add_worksheet("Gráficos")
    hoja_s = wb.add_worksheet("_series")
    hoja_s.hide()

    encabezados = [
        "Fecha",
        "Hora",
        "Persona",
        "Documento",
        "Equipo",
        "Serial",
        "Sede",
        "Resultado",
        "Celador",
    ]
    filas = []
    por_dia = Counter()
    por_sede_resultado = defaultdict(Counter)
    por_resultado = Counter()

    for m in qs.iterator(chunk_size=2000):
        ts = timezone.localtime(m.timestamp)
        persona = m.equipo.persona if m.equipo_id else None
        sede_nom = persona.sede.nombre if persona and persona.sede_id else "(Sin sede)"
        filas.append(
            [
                ts.date(),
                ts.strftime("%H:%M"),
                persona.nombre_completo if persona else "",
                persona.numero_documento if persona else "",
                f"{m.equipo.marca} {m.equipo.modelo}" if m.equipo_id else "",
                m.equipo.serial if m.equipo_id else (m.token_escaneado or ""),
                sede_nom,
                RESULTADO_LABEL.get(m.resultado, m.resultado),
                m.usuario_control.get_username() if m.usuario_control_id else "",
            ]
        )
        dia = ts.date().isoformat()
        por_dia[dia] += 1
        por_sede_resultado[sede_nom][m.resultado] += 1
        por_resultado[m.resultado] += 1

    escribir_tabla(
        hoja,
        encabezados,
        filas,
        fmts,
        tipos_col=["fecha", "texto", "celda", "texto", "celda", "texto", "celda", "celda", "celda"],
    )

    # Serie 1: movimientos por día
    dias = sorted(por_dia.keys())
    vals_dia = [por_dia[d] for d in dias]
    r1, r2, col_cat, col_map = insertar_serie_oculta(
        hoja_s, 0, dias, {"Movimientos": vals_dia}, fmts
    )
    chart_line = wb.add_chart({"type": "line"})
    chart_line.add_series(
        {
            "name": "Movimientos por día",
            "categories": ref_rango("_series", r1, col_cat, r2),
            "values": ref_rango("_series", r1, col_map["Movimientos"], r2),
            "line": {"color": COLOR_VERDE},
        }
    )
    chart_line.set_title({"name": "Tendencia de movimientos"})
    chart_line.set_size({"width": 720, "height": 320})
    hoja_g.insert_chart("B2", chart_line)

    # Serie 2: barras apiladas resultado x sede
    sedes = sorted(por_sede_resultado.keys())
    series_stack = {
        "OK": [por_sede_resultado[s][Movimiento.RESULTADO_OK] for s in sedes],
        "Alerta": [por_sede_resultado[s][Movimiento.RESULTADO_ALERTA] for s in sedes],
        "No encontrado": [
            por_sede_resultado[s][Movimiento.RESULTADO_NO_ENCONTRADO] for s in sedes
        ],
    }
    r1b, r2b, col_cat_b, col_map_b = insertar_serie_oculta(
        hoja_s, 4, sedes, series_stack, fmts
    )
    chart_bar = wb.add_chart({"type": "column", "subtype": "stacked"})
    for nombre, color in (
        ("OK", COLOR_VERDE),
        ("Alerta", "#C0392B"),
        ("No encontrado", "#F39C12"),
    ):
        chart_bar.add_series(
            {
                "name": nombre,
                "categories": ref_rango("_series", r1b, col_cat_b, r2b),
                "values": ref_rango("_series", r1b, col_map_b[nombre], r2b),
                "fill": {"color": color},
            }
        )
    chart_bar.set_title({"name": "Resultados por sede"})
    chart_bar.set_size({"width": 720, "height": 320})
    hoja_g.insert_chart("B20", chart_bar)

    # Serie 3: pastel global
    cats_pie = ["OK", "Alerta", "No encontrado"]
    vals_pie = [
        por_resultado[Movimiento.RESULTADO_OK],
        por_resultado[Movimiento.RESULTADO_ALERTA],
        por_resultado[Movimiento.RESULTADO_NO_ENCONTRADO],
    ]
    r1c, r2c, col_cat_c, col_map_c = insertar_serie_oculta(
        hoja_s, 10, cats_pie, {"Total": vals_pie}, fmts
    )
    chart_pie = wb.add_chart({"type": "pie"})
    chart_pie.add_series(
        {
            "name": "Proporción de resultados",
            "categories": ref_rango("_series", r1c, col_cat_c, r2c),
            "values": ref_rango("_series", r1c, col_map_c["Total"], r2c),
        }
    )
    chart_pie.set_title({"name": "Proporción global de resultados"})
    chart_pie.set_size({"width": 480, "height": 320})
    hoja_g.insert_chart("B38", chart_pie)

    contenido = cerrar_workbook(buffer, wb)
    return ResultadoReporte(
        contenido=contenido,
        nombre_archivo=nombre_archivo("movimientos"),
        filas=total,
        filtros=filtros,
    )
