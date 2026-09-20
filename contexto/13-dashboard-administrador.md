# 13 — Dashboard de Administrador (dinámico, dentro de `apps/reportes`)

> Vive en la misma app `reportes` definida en `12`, reutilizando sus clases de filtro (sección 3 de `12`) y el sistema de diseño de `05`/`09` (`.stats-grid`, `.stat-card` ya existen en el CSS actual). No genera archivos — es la vista en pantalla, complementaria a las exportaciones de `12`.

## 1. Comportamiento por defecto

Al entrar a `/panel/dashboard/` sin aplicar ningún filtro, el sistema carga automáticamente los datos de **hoy** (00:00 a la hora actual). El administrador no tiene que configurar nada para ver algo útil de inmediato — los filtros existen para *cambiar* la vista, no para *activarla*.

## 2. Filtros dinámicos (reutilizan `12`, sección 3)

| Filtro | Comportamiento |
|---|---|
| Rango de fechas | Presets rápidos: **Hoy** (default), Ayer, Últimos 7 días, Este mes, Personalizado |
| Sede | Select, "Todas" por defecto |
| Tipo de vínculo | Multi-select, todos por defecto |
| Resultado de movimiento | Multi-select (ok/alerta/no_encontrado), todos por defecto |

**Interacción:** cada cambio de filtro dispara una actualización parcial (HTMX `hx-get` al mismo endpoint con los nuevos query params) que reemplaza solo la zona de tarjetas y gráficos — **sin recargar la página completa**. La URL se actualiza con los filtros aplicados (query params), para que el admin pueda compartir o guardar en favoritos una vista específica (ej. "dashboard de la sede Ubaté, últimos 7 días").

## 3. Layout (reutiliza clases ya existentes de `09`)

```
┌──────────────────────────────────────────────────────────┐
│  Filtros (fila, gap-3)                                    │
├──────────────────────────────────────────────────────────┤
│  .stats-grid-4                                             │
│  [Movimientos] [Alertas] [Equipos activos] [Personas act.] │
├───────────────────────────────┬────────────────────────────┤
│  Línea: movimientos en el tiempo │ Dona: resultado global     │
├───────────────────────────────┼────────────────────────────┤
│  Barras: movimientos por sede    │ Barras horiz.: top alertas │
└───────────────────────────────┴────────────────────────────┘
```

En móvil (`≤767px`, según `09`/`10`): las tarjetas pasan a 2 columnas y luego a 1; los gráficos se apilan en una sola columna.

## 4. Tarjetas KPI (`.stat-card`)

| Tarjeta | Cálculo | Nota |
|---|---|---|
| Movimientos del periodo | `COUNT(Movimiento)` en el rango filtrado | Valor grande, `.stat-value` |
| Alertas del periodo | `COUNT(Movimiento WHERE resultado='alerta')` + % sobre el total | Color de acento `--color-danger` si el % supera un umbral configurable (ej. 5%) |
| Equipos activos | `COUNT(Equipo WHERE activo=true)` (no depende del rango de fechas) | Dato estructural, no del periodo |
| Personas activas | `COUNT(Persona WHERE activo=true)` (no depende del rango de fechas) | Dato estructural |
| Sede con más movimiento | Texto destacado, no numérico | Se muestra como tarjeta adicional solo si hay más de una sede con datos en el periodo |

**Regla de diseño:** las dos tarjetas "estructurales" (equipos/personas activas) no cambian con el rango de fechas — solo las de "movimientos" y "alertas" son sensibles al periodo. Esto debe ser visualmente claro (ej. un subtítulo "dato actual" vs. "en el periodo seleccionado") para que el admin no interprete mal por qué un número no cambia al mover el filtro de fechas.

## 5. Gráficos (Chart.js, mismos tipos que en las exportaciones de `12` para consistencia mental)

| Gráfico | Tipo | Eje / agrupación |
|---|---|---|
| Movimientos en el tiempo | Línea | Por hora si el rango es "Hoy"; por día si es un rango mayor (el backend decide el nivel de agregación según el tamaño del rango) |
| Resultado global | Dona (doughnut) | ok / alerta / no_encontrado, con los mismos colores funcionales de `05`/`09` (`#007B3E` / `#C62828` / `#5B615D`) |
| Movimientos por sede | Barras verticales | Una barra por sede, ordenadas de mayor a menor |
| Top alertas | Barras horizontales | Top 5 personas o equipos con más alertas en el periodo; si no hay alertas, se muestra un estado vacío ("Sin alertas en este periodo" + ícono), nunca un gráfico en blanco |

**Por qué Chart.js:** ya está disponible como librería estándar del ecosistema Bootstrap/HTML, se integra bien con los tokens de color definidos (`--color-primary`, `--color-danger`, etc.), y usar los mismos tipos de gráfico que en el Excel de `12` hace que el admin reconozca la misma información en ambos lugares sin reaprender una visualización distinta.

## 6. Distinción de seguridad respecto a `12` (importante)

| Vista | Qué expone | Permiso requerido |
|---|---|---|
| Dashboard (`13`, este documento) | Solo **datos agregados** (conteos, porcentajes, nombres en el top de alertas) | `reportes.ver` |
| Exportación a Excel (`12`) | **Datos crudos** fila por fila (documento, nombre completo, etc.) | `reportes.exportar` |

Esta separación importa: un administrador con acceso de solo consulta puede monitorear el dashboard sin tener permiso para descargar el detalle completo de datos personales — principio de mínimo privilegio ya establecido en `07`/`11`.

## 7. Rendimiento (relevante a la escala de `10`)

- Los agregados del dashboard se **cachean con un TTL corto** (30–60 segundos) por combinación de filtros, para que múltiples administradores viendo el dashboard simultáneamente no disparen la misma consulta pesada repetidamente.
- Los KPIs "estructurales" (equipos/personas activas) pueden cachearse con un TTL más largo (ej. 5 minutos), ya que cambian con mucha menor frecuencia que los movimientos.
- Las consultas de agregación usan `annotate`/`aggregate` del ORM (no se traen las filas completas a Python para contarlas en el backend).

## 8. Mejora futura opcional (no bloquea el MVP del dashboard)

Actualización en vivo del contador de "Movimientos de hoy" mediante *polling* cada 30-60 segundos (una petición ligera que solo trae el número, no todo el dashboard) — útil si el admin deja el dashboard abierto durante el pico de salida de estudiantes. No se implementa con WebSockets en esta fase por complejidad innecesaria para el MVP; un `setInterval` con `fetch` ligero es suficiente.

## 9. Vistas y rutas

| Ruta | Permiso | Descripción |
|---|---|---|
| `/panel/dashboard/` | `reportes.ver` | Vista completa (carga inicial con filtro "Hoy") |
| `/panel/dashboard/parcial/` | `reportes.ver` | Endpoint HTMX que devuelve solo el HTML de tarjetas + contenedor de gráficos, según filtros en query params |
| `/panel/dashboard/datos-grafico/<tipo>/` | `reportes.ver` | Endpoint JSON que alimenta cada gráfico de Chart.js (uno por tipo de gráfico, o uno combinado) |

## 10. Plan de implementación

1. **Día 1:** vista base `/panel/dashboard/` con las 4 tarjetas KPI cargando datos de "Hoy" por defecto (sin filtros aún interactivos).
2. **Día 2:** filtros dinámicos con HTMX (rango de fechas con presets, sede, tipo de vínculo, resultado) actualizando las tarjetas sin recargar la página.
3. **Día 3:** integrar Chart.js con los 4 gráficos, alimentados por los endpoints JSON de la sección 9.
4. **Día 4:** caché de agregados (TTL corto/largo según el KPI) y estados vacíos para gráficos sin datos.
5. **Día 5 (opcional):** polling ligero para el contador de movimientos en vivo.

## 11. Checklist final

- [x] El dashboard carga datos de "Hoy" sin que el admin aplique ningún filtro.
- [x] Cambiar cualquier filtro actualiza tarjetas y gráficos sin recargar la página completa.
- [x] Las tarjetas "estructurales" (equipos/personas activas) están visualmente diferenciadas de las tarjetas "del periodo".
- [x] Ningún gráfico se muestra vacío sin un mensaje explicativo cuando no hay datos.
- [x] El dashboard requiere `reportes.ver`, nunca `reportes.exportar` (no expone descarga de datos crudos).
- [x] Los agregados están cacheados con un TTL razonable para soportar múltiples administradores concurrentes.

> **Nota de implementación (2026-09-19):** LocMemCache TTL 45 s (periodo) / 300 s (estructurales). Polling en vivo (§8) no incluido.
