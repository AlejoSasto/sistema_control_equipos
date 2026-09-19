"""Utilidades base para generar libros Excel en memoria."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import BytesIO

import xlsxwriter

from reportes.estilos import autoajustar_anchos, formatos_libro, formato_fila, escribir_encabezados
from reportes.umbrales import MAX_FILAS_SYNC


class UmbralExcedido(Exception):
    def __init__(self, filas: int, limite: int = MAX_FILAS_SYNC):
        self.filas = filas
        self.limite = limite
        super().__init__(
            f"La consulta devolvió {filas} filas (máximo síncrono: {limite}). "
            "Acote los filtros e intente de nuevo."
        )


@dataclass
class ResultadoReporte:
    contenido: bytes
    nombre_archivo: str
    filas: int
    filtros: dict


def nombre_archivo(tipo: str, cuando: date | None = None) -> str:
    cuando = cuando or date.today()
    return f"reporte_{tipo}_{cuando.isoformat()}.xlsx"


def abrir_workbook() -> tuple[BytesIO, xlsxwriter.Workbook, dict]:
    buffer = BytesIO()
    workbook = xlsxwriter.Workbook(buffer, {"in_memory": True, "strings_to_numbers": False})
    fmts = formatos_libro(workbook)
    return buffer, workbook, fmts


def cerrar_workbook(buffer: BytesIO, workbook: xlsxwriter.Workbook) -> bytes:
    workbook.close()
    buffer.seek(0)
    return buffer.getvalue()


def verificar_umbral(count: int):
    if count > MAX_FILAS_SYNC:
        raise UmbralExcedido(count)


def escribir_tabla(hoja, encabezados, filas, fmts, tipos_col=None):
    """
    tipos_col: lista opcional de claves de formato por columna
    ('celda', 'texto', 'fecha', 'hora', 'numero').
    """
    escribir_encabezados(hoja, encabezados, fmts["encabezado"])
    tipos_col = tipos_col or ["celda"] * len(encabezados)
    for i, fila in enumerate(filas):
        for j, valor in enumerate(fila):
            clave = tipos_col[j] if j < len(tipos_col) else "celda"
            hoja.write(i + 1, j, valor if valor is not None else "", formato_fila(fmts, i, clave))
    autoajustar_anchos(hoja, [encabezados] + [[str(c) if c is not None else "" for c in f] for f in filas])
    if len(filas) > 20:
        hoja.freeze_panes(1, 0)


def insertar_serie_oculta(hoja, col_inicio: int, categorias, series: dict[str, list], fmts):
    """
    Escribe categorías y series a partir de col_inicio para alimentar gráficos.
    series = {"Nombre serie": [valores...]}
    Devuelve (primera_fila_dato, ultima_fila_dato, col_cat, mapa_col_serie).
    """
    hoja.write(0, col_inicio, "Categoría", fmts["encabezado"])
    col_map = {}
    for offset, nombre in enumerate(series.keys(), start=1):
        hoja.write(0, col_inicio + offset, nombre, fmts["encabezado"])
        col_map[nombre] = col_inicio + offset

    cats = list(categorias)
    for i, cat in enumerate(cats):
        hoja.write(i + 1, col_inicio, cat)
        for nombre, valores in series.items():
            val = valores[i] if i < len(valores) else 0
            hoja.write(i + 1, col_map[nombre], val)

    n = len(cats)
    return 1, n, col_inicio, col_map


def ref_rango(hoja_nombre: str, fila_ini: int, col: int, fila_fin: int) -> str:
    """Referencia estilo Excel A1 (1-index filas en API xlsxwriter write es 0-index)."""
    from xlsxwriter.utility import xl_rowcol_to_cell

    c1 = xl_rowcol_to_cell(fila_ini, col, row_abs=True, col_abs=True)
    c2 = xl_rowcol_to_cell(fila_fin, col, row_abs=True, col_abs=True)
    return f"='{hoja_nombre}'!{c1}:{c2}"
