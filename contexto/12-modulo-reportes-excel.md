# 12 — Módulo de Reportes en Excel (filtros + gráficos)

> Nueva app `reportes`, que consulta los datos ya definidos en `02` (Persona, Equipo, Movimiento, TipoVinculo, Sede/Facultad/Programa/Área) y genera archivos `.xlsx` con gráficos nativos de Excel, no imágenes pegadas — el usuario puede seguir interactuando con el gráfico dentro de Excel.

## 1. Elección de librería: `xlsxwriter` sobre `openpyxl`

| Criterio | `xlsxwriter` | `openpyxl` |
|---|---|---|
| Calidad y variedad de gráficos nativos | Alta (barras, líneas, pastel, dispersión, área, combinados) | Media, API más limitada |
| Formato visual (colores, bordes, formatos numéricos) | Muy completo | Completo pero más verboso |
| Lectura de archivos existentes | No soporta (solo escritura) | Sí |
| Uso en este módulo | Ideal — solo generamos reportes, nunca leemos `.xlsx` de vuelta | — |

**Decisión:** `xlsxwriter`, ya que el módulo solo genera reportes de salida; no necesita leer Excel.

## 2. Arquitectura del módulo

```
apps/
  reportes/
    filtros.py       → clases de filtro reutilizables (rango de fechas, sede, tipo_vinculo, etc.)
    generadores/
      movimientos.py
      equipos.py
      personas.py
      alertas.py
      ejecutivo.py
    views.py          → vista de configuración de filtros + endpoint de descarga
```

- Permiso nuevo: `reportes.ver` (acceder al módulo) y `reportes.exportar` (generar/descargar el archivo). Se separan porque un rol podría ver estadísticas en pantalla sin poder exportar datos personales masivamente.
- Cada exportación queda registrada en la tabla de auditoría (`auditoria_cambio`, definida en `11`) con `usuario_id`, `tipo_reporte`, `filtros_aplicados` y `timestamp` — exportar datos de 20.000 personas es una acción sensible que debe ser trazable.

## 3. Filtros comunes (reutilizables entre reportes)

| Filtro | Aplica a | Tipo |
|---|---|---|
| Rango de fechas (`fecha_inicio`, `fecha_fin`) | Movimientos, Alertas, evolución de Personas/Equipos | Selector de fecha |
| Sede | Todos | Select (dinámico desde catálogo) |
| Facultad | Personas, Programas | Select |
| Programa | Personas | Select, dependiente de Facultad |
| Área/dependencia | Personas administrativas, Equipos institucionales | Select |
| Tipo de vínculo | Personas, Equipos (por dueño) | Multi-select (docente, estudiante, administrativo, graduado) |
| Estado (activo/inactivo) | Personas, Equipos | Select |
| Propiedad del equipo | Equipos | Select (institucional/personal) |
| Resultado del movimiento | Movimientos, Alertas | Multi-select (ok/alerta/no_encontrado) |
| Usuario de control (celador) | Movimientos | Select |

Los filtros se arman con clases reutilizables (`FiltroFecha`, `FiltroSede`, `FiltroTipoVinculo`, etc.) para no repetir la lógica de validación en cada generador de reporte.

## 4. Reportes del módulo

### 4.1 Reporte de Movimientos (control de salida)

**Filtros:** rango de fechas (obligatorio, máximo 90 días por exportación directa — ver sección 6), sede, resultado, tipo de vínculo, celador.

**Hojas:**
- `Datos`: tabla con columnas `fecha`, `hora`, `persona`, `documento`, `equipo`, `serial`, `sede`, `resultado`, `celador`. Con autofiltro y encabezado congelado (`freeze_panes`).
- `Gráficos`:
  - **Línea:** movimientos por día en el rango seleccionado (tendencia general).
  - **Barras apiladas:** resultados (ok/alerta/no_encontrado) por sede.
  - **Pastel:** proporción global ok vs. alerta vs. no_encontrado.

### 4.2 Reporte de Equipos

**Filtros:** sede, tipo de equipo, propiedad, estado, tipo de vínculo del dueño.

**Hojas:**
- `Datos`: `serial`, `marca`, `modelo`, `tipo`, `propiedad`, `dueño`, `sede`, `estado`, `fecha_registro`.
- `Gráficos`:
  - **Barras horizontales:** cantidad de equipos por sede.
  - **Pastel:** institucional vs. personal.
  - **Barras:** equipos por marca (top 10).

### 4.3 Reporte de Personas

**Filtros:** sede, facultad, programa, tipo de vínculo, estado.

**Hojas:**
- `Datos`: `nombre`, `documento`, `tipo_vinculo`, `sede`, `programa`/`área`, `estado`, `fecha_registro`.
- `Gráficos`:
  - **Barras:** personas por tipo de vínculo.
  - **Barras:** personas por sede.
  - **Línea:** registros acumulados por mes (crecimiento de la comunidad en el sistema).

### 4.4 Reporte de Alertas / Seguridad

**Filtros:** rango de fechas, sede, tipo de alerta.

**Hojas:**
- `Datos`: detalle de cada movimiento con resultado distinto de "ok".
- `Top ofensores`: tabla + **barras horizontales** de las 10 personas/equipos con más alertas en el periodo.
- `Patrón horario`: tabla cruzada hora del día × día de la semana, con **formato condicional tipo mapa de calor** (escala de color, de verde a rojo según cantidad de alertas) — útil para detectar franjas horarias críticas de portería.

### 4.5 Reporte Ejecutivo (resumen gerencial)

Pensado para un directivo que no quiere filtrar nada, solo ver el panorama general del periodo seleccionado.

**Filtros:** rango de fechas únicamente.

**Hojas:**
- `Resumen`: celdas destacadas tipo "tarjeta" (fondo verde institucional, número grande) con: total de personas activas, total de equipos registrados, % de equipos institucionales vs. personales, movimientos del periodo, tasa de alertas (%).
- **Gráfico combinado** (barras + línea): movimientos totales por semana (barras) con la tasa de alerta superpuesta como línea.
- **Barras:** distribución de personas por sede.

## 5. Diseño visual del Excel (coherente con `05`/`09`)

- Encabezado de tabla: fondo verde institucional `#007B3E`, texto blanco, negrita — mismo color de marca que el resto del sistema.
- Filas alternadas con banda gris muy clara (`#F5F6F5`) para legibilidad en tablas largas.
- Números de documento y seriales en formato de texto (para no perder ceros a la izquierda).
- Fechas en formato `DD/MM/AAAA`, horas en `HH:MM`.
- Columnas con ancho autoajustado según el contenido más largo.
- Encabezado de fila congelado (`freeze_panes`) en toda hoja de datos con más de 20 filas.
- Nombre de archivo con fecha de generación: `reporte_movimientos_2026-09-19.xlsx`.

### Ejemplo de generación de un gráfico (ilustrativo)

```python
import xlsxwriter

workbook = xlsxwriter.Workbook("reporte_movimientos.xlsx")
hoja_datos = workbook.add_worksheet("Datos")
hoja_graficos = workbook.add_worksheet("Gráficos")

formato_encabezado = workbook.add_format({
    "bold": True, "bg_color": "#007B3E", "font_color": "#FFFFFF"
})
hoja_datos.write_row(0, 0, ["Fecha", "Persona", "Equipo", "Resultado"], formato_encabezado)
hoja_datos.freeze_panes(1, 0)

grafico_linea = workbook.add_chart({"type": "line"})
grafico_linea.add_series({
    "name": "Movimientos por día",
    "categories": "=Datos!$A$2:$A$31",
    "values": "=Datos!$D$2:$D$31",
    "line": {"color": "#007B3E"},
})
grafico_linea.set_title({"name": "Tendencia de movimientos"})
hoja_graficos.insert_chart("B2", grafico_linea)

workbook.close()
```

## 6. Rendimiento con 20.000 usuarios / grandes volúmenes

- **Exportación directa (síncrona):** permitida solo si el resultado filtrado no supera un umbral razonable (ej. 20.000 filas / 90 días de movimientos). Por debajo de eso, el archivo se genera y descarga en la misma petición.
- **Exportación en segundo plano (asíncrona):** para consultas más grandes (ej. "todo el histórico de movimientos"), se encola la generación (Celery/RQ) y se notifica al usuario cuando el archivo está listo para descargar (o se envía por correo institucional).
- **Consultas optimizadas:** usar `select_related`/`prefetch_related` en el ORM para evitar N+1 queries al armar cada fila del reporte — con miles de registros, esto es la diferencia entre segundos y minutos de generación.

## 7. Seguridad del módulo (alineado a `11`)

- Todo endpoint de reportes requiere `reportes.ver` (para configurar filtros) o `reportes.exportar` (para descargar el archivo).
- Si el sistema evoluciona a que un decano o coordinador de programa tenga acceso, el reporte debe **filtrarse automáticamente a su alcance** (su facultad/programa), no confiar en que el filtro del formulario sea el único control — la consulta en el backend debe acotarse igual aunque el usuario intente pedir "todas las sedes" manipulando el formulario.
- Cada exportación se registra en `auditoria_cambio`: quién exportó, qué reporte, con qué filtros, cuándo — exportar datos personales de miles de personas es una acción que debe quedar trazada.
- Los archivos generados no se almacenan indefinidamente en el servidor; se sirven para descarga inmediata y se eliminan (o expiran) del almacenamiento temporal en un plazo corto (ej. 24 horas) si se usa el modo asíncrono.

## 8. Plan de implementación

1. **Día 1:** crear app `reportes`, definir permisos (`reportes.ver`, `reportes.exportar`), construir las clases de filtro reutilizables (sección 3).
2. **Día 2:** implementar el generador de "Movimientos" completo (datos + 3 gráficos) como plantilla de referencia para los demás.
3. **Día 3:** implementar "Equipos" y "Personas" reutilizando la base del día 2.
4. **Día 4:** implementar "Alertas/Seguridad" (incluye el mapa de calor por formato condicional) y el "Reporte Ejecutivo".
5. **Día 5:** integrar el registro en auditoría, definir el umbral síncrono/asíncrono, y pruebas con volúmenes grandes simulados.

## 9. Checklist final

- [x] Los 5 reportes generan `.xlsx` con datos + al menos un gráfico nativo cada uno.
- [x] Ningún reporte se puede exportar sin el permiso `reportes.exportar`.
- [x] Toda exportación queda registrada en `auditoria_cambio`.
- [x] Existe un umbral definido para exportación síncrona vs. asíncrona.
- [x] El diseño visual del Excel usa los colores institucionales (`05`), no colores por defecto de la librería.
- [ ] Los archivos temporales de reportes asíncronos expiran automáticamente. *(Fase 2: sin cola Celery/RQ en esta entrega; solo sync en memoria.)*

> **Nota de implementación (2026-09-19):** exportación síncrona con `MAX_FILAS_SYNC=20000` y `MAX_DIAS_MOVIMIENTOS=90`. Si se supera el umbral, la vista rechaza y pide acotar filtros. Async + expiración 24h queda pendiente.
