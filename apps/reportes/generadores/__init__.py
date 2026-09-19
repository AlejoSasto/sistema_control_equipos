from reportes.generadores import alertas, equipos, ejecutivo, movimientos, personas

GENERADORES = {
    "movimientos": movimientos.generar,
    "equipos": equipos.generar,
    "personas": personas.generar,
    "alertas": alertas.generar,
    "ejecutivo": ejecutivo.generar,
}

TIPOS_REPORTE = [
    {
        "slug": "movimientos",
        "nombre": "Movimientos",
        "descripcion": "Control de salida con tendencia, resultados por sede y proporción global.",
    },
    {
        "slug": "equipos",
        "nombre": "Equipos",
        "descripcion": "Inventario por sede, propiedad y marcas principales.",
    },
    {
        "slug": "personas",
        "nombre": "Personas",
        "descripcion": "Comunidad académica por vínculo, sede y crecimiento acumulado.",
    },
    {
        "slug": "alertas",
        "nombre": "Alertas / Seguridad",
        "descripcion": "Movimientos no OK, top ofensores y mapa de calor horario.",
    },
    {
        "slug": "ejecutivo",
        "nombre": "Ejecutivo",
        "descripcion": "Resumen gerencial del periodo (KPIs y gráficos combinados).",
    },
]
