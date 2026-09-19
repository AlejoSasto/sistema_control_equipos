"""Formatos visuales institucionales para libros xlsxwriter."""

from __future__ import annotations

COLOR_VERDE = "#007B3E"
COLOR_BANDA = "#F5F6F5"
COLOR_BLANCO = "#FFFFFF"


def formatos_libro(workbook):
    """Devuelve un dict de formatos reutilizables."""
    return {
        "encabezado": workbook.add_format(
            {
                "bold": True,
                "bg_color": COLOR_VERDE,
                "font_color": COLOR_BLANCO,
                "border": 1,
                "align": "center",
                "valign": "vcenter",
            }
        ),
        "celda": workbook.add_format({"border": 1, "valign": "vcenter"}),
        "celda_banda": workbook.add_format(
            {"border": 1, "bg_color": COLOR_BANDA, "valign": "vcenter"}
        ),
        "texto": workbook.add_format({"border": 1, "num_format": "@", "valign": "vcenter"}),
        "texto_banda": workbook.add_format(
            {"border": 1, "num_format": "@", "bg_color": COLOR_BANDA, "valign": "vcenter"}
        ),
        "fecha": workbook.add_format(
            {"border": 1, "num_format": "dd/mm/yyyy", "valign": "vcenter"}
        ),
        "fecha_banda": workbook.add_format(
            {
                "border": 1,
                "num_format": "dd/mm/yyyy",
                "bg_color": COLOR_BANDA,
                "valign": "vcenter",
            }
        ),
        "hora": workbook.add_format(
            {"border": 1, "num_format": "hh:mm", "valign": "vcenter"}
        ),
        "hora_banda": workbook.add_format(
            {"border": 1, "num_format": "hh:mm", "bg_color": COLOR_BANDA, "valign": "vcenter"}
        ),
        "numero": workbook.add_format(
            {"border": 1, "num_format": "#,##0", "valign": "vcenter"}
        ),
        "porcentaje": workbook.add_format(
            {"border": 1, "num_format": "0.0%", "valign": "vcenter"}
        ),
        "tarjeta_label": workbook.add_format(
            {
                "bold": True,
                "font_color": COLOR_BLANCO,
                "bg_color": COLOR_VERDE,
                "align": "center",
                "valign": "vcenter",
            }
        ),
        "tarjeta_valor": workbook.add_format(
            {
                "bold": True,
                "font_size": 18,
                "font_color": COLOR_VERDE,
                "align": "center",
                "valign": "vcenter",
                "border": 1,
            }
        ),
        "titulo_grafico": workbook.add_format({"bold": True, "font_size": 12}),
    }


def escribir_encabezados(hoja, encabezados, formato):
    for col, titulo in enumerate(encabezados):
        hoja.write(0, col, titulo, formato)
    hoja.freeze_panes(1, 0)
    hoja.autofilter(0, 0, 0, len(encabezados) - 1)


def formato_fila(fmts, fila_idx: int, clave: str = "celda"):
    """Alterna banda gris en filas de datos (fila_idx 0 = primera fila de datos)."""
    if fila_idx % 2 == 1:
        banda = f"{clave}_banda" if f"{clave}_banda" in fmts else "celda_banda"
        return fmts.get(banda, fmts["celda_banda"])
    return fmts[clave]


def autoajustar_anchos(hoja, filas: list[list], minimo: int = 10, maximo: int = 40):
    if not filas:
        return
    n_cols = max(len(r) for r in filas)
    for col in range(n_cols):
        largo = minimo
        for fila in filas:
            if col < len(fila) and fila[col] is not None:
                largo = max(largo, min(maximo, len(str(fila[col])) + 2))
        hoja.set_column(col, col, largo)
