"""Reporte de alertas / seguridad."""

from __future__ import annotations

from collections import Counter, defaultdict

from django.db.models import Q
from django.utils import timezone

from control_acceso.models import Movimiento
from reportes.filtros import (
    FiltroFecha,
    FiltroSede,
    FiltroTipoAlerta,
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
DIAS_SEMANA = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def queryset_alertas(user, data):
    f_fecha = FiltroFecha.from_data(data, obligatorio=True)
    f_sede = FiltroSede.from_data(data, lookup="equipo__persona__sede_id")
    f_alerta = FiltroTipoAlerta.from_data(data)

    qs = Movimiento.objects.filter(
        ~Q(resultado=Movimiento.RESULTADO_OK)
    ).select_related(
        "equipo__persona__sede",
        "equipo__persona",
        "usuario_control",
    )
    qs = f_fecha.aplicar(qs, campo="timestamp")
    qs = f_sede.aplicar(qs)
    qs = f_alerta.aplicar(qs)
    qs = acotar_por_alcance(user, qs)
    filtros = fusionar_filtros(f_fecha, f_sede, f_alerta)
    return qs.order_by("timestamp"), filtros


def generar(user, data) -> ResultadoReporte:
    qs, filtros = queryset_alertas(user, data)
    total = qs.count()
    verificar_umbral(total)

    buffer, wb, fmts = abrir_workbook()
    hoja = wb.add_worksheet("Datos")
    hoja_top = wb.add_worksheet("Top ofensores")
    hoja_patron = wb.add_worksheet("Patrón horario")
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
        "Observación",
    ]
    filas = []
    ofensores_persona = Counter()
    matriz = defaultdict(int)  # (hora, dow) -> count

    for m in qs.iterator(chunk_size=2000):
        ts = timezone.localtime(m.timestamp)
        persona = m.equipo.persona if m.equipo_id else None
        sede_nom = persona.sede.nombre if persona and persona.sede_id else "(Sin sede)"
        nombre_p = persona.nombre_completo if persona else "(Sin persona)"
        serial = m.equipo.serial if m.equipo_id else (m.token_escaneado or "")
        filas.append(
            [
                ts.date(),
                ts.strftime("%H:%M"),
                nombre_p,
                persona.numero_documento if persona else "",
                f"{m.equipo.marca} {m.equipo.modelo}" if m.equipo_id else "",
                serial,
                sede_nom,
                RESULTADO_LABEL.get(m.resultado, m.resultado),
                m.usuario_control.get_username() if m.usuario_control_id else "",
                m.observacion or "",
            ]
        )
        ofensores_persona[nombre_p] += 1
        matriz[(ts.hour, ts.weekday())] += 1

    escribir_tabla(
        hoja,
        encabezados,
        filas,
        fmts,
        tipos_col=[
            "fecha",
            "texto",
            "celda",
            "texto",
            "celda",
            "texto",
            "celda",
            "celda",
            "celda",
            "celda",
        ],
    )

    # Top ofensores: combinar personas y equipos (top 10 por alertas de persona)
    top = ofensores_persona.most_common(10)
    top_headers = ["Persona / entidad", "Alertas"]
    top_filas = [[nombre, cnt] for nombre, cnt in top]
    escribir_tabla(hoja_top, top_headers, top_filas, fmts, tipos_col=["celda", "numero"])

    labels = [n for n, _ in top]
    vals = [c for _, c in top]
    r1, r2, col_cat, col_map = insertar_serie_oculta(
        hoja_s, 0, labels, {"Alertas": vals}, fmts
    )
    chart_bar = wb.add_chart({"type": "bar"})
    chart_bar.add_series(
        {
            "name": "Top alertas",
            "categories": ref_rango("_series", r1, col_cat, r2),
            "values": ref_rango("_series", r1, col_map["Alertas"], r2),
            "fill": {"color": "#C0392B"},
        }
    )
    chart_bar.set_title({"name": "Top 10 personas con más alertas"})
    chart_bar.set_size({"width": 720, "height": 360})
    hoja_top.insert_chart("D2", chart_bar)

    # Patrón horario: tabla cruzada + mapa de calor
    hoja_patron.write(0, 0, "Hora", fmts["encabezado"])
    for dow, nom in enumerate(DIAS_SEMANA):
        hoja_patron.write(0, dow + 1, nom, fmts["encabezado"])

    max_val = max(matriz.values()) if matriz else 1
    for hora in range(24):
        hoja_patron.write(hora + 1, 0, f"{hora:02d}:00", fmts["celda"])
        for dow in range(7):
            val = matriz.get((hora, dow), 0)
            # Escala verde → rojo
            if max_val <= 0:
                ratio = 0
            else:
                ratio = val / max_val
            # Interpolar #007B3E → #C0392B
            r = int(0x00 + (0xC0 - 0x00) * ratio)
            g = int(0x7B + (0x39 - 0x7B) * ratio)
            b = int(0x3E + (0x2B - 0x3E) * ratio)
            color = f"#{r:02X}{g:02X}{b:02X}"
            fmt = wb.add_format(
                {
                    "border": 1,
                    "bg_color": color if val else "#F5F6F5",
                    "font_color": "#FFFFFF" if ratio > 0.45 else "#1A1A1A",
                    "align": "center",
                }
            )
            hoja_patron.write(hora + 1, dow + 1, val, fmt)

    hoja_patron.freeze_panes(1, 1)
    for col in range(8):
        hoja_patron.set_column(col, col, 8 if col else 10)

    # Condicional adicional con color scale de xlsxwriter sobre el bloque
    hoja_patron.conditional_format(
        1,
        1,
        24,
        7,
        {
            "type": "3_color_scale",
            "min_color": "#007B3E",
            "mid_color": "#F1C40F",
            "max_color": "#C0392B",
        },
    )

    contenido = cerrar_workbook(buffer, wb)
    return ResultadoReporte(
        contenido=contenido,
        nombre_archivo=nombre_archivo("alertas"),
        filas=total,
        filtros=filtros,
    )
