# 10 — Plan de Mejora UX/UI: Responsivo y Escalable a 20.000 Usuarios

> Este documento **no reemplaza** `09-guia-diseno-ux-ui.md` (que sigue siendo la referencia visual vigente, alineada al código). Este plan toma esa base y añade lo que falta para dos objetivos nuevos: **experiencia fluida en PC y móvil por igual**, y **UI/UX que sostenga 20.000 usuarios** sin degradarse.

## 1. Diagnóstico: qué ya está bien y qué falta

### Ya resuelto en `09` (no se toca)

- Paleta sin amarillo, verde institucional como único color de marca.
- Tipografía Inter + JetBrains Mono para seriales/QR.
- Tokens de espaciado, radios y sombra consistentes.
- Kiosco de portería con semáforo de alto contraste.

### Lo que falta para "profesional a 20.000 usuarios"

| Brecha | Por qué importa a esta escala |
|---|---|
| Bootstrap usado parcialmente (clases propias como `.filters-grid--6` en vez de la grilla estándar) | Con 20.000 usuarios y múltiples desarrolladores, un grid no estándar es más difícil de mantener y de extender |
| Breakpoints personalizados (1024/767/640) en vez de los de Bootstrap (576/768/992/1200/1400) | Cualquier componente de Bootstrap que se agregue después (modales, offcanvas, tooltips) usa los breakpoints estándar — mezclar dos sistemas genera inconsistencias visuales |
| Tablas sin paginación server-side documentada | Un listado de "Personas" o "Equipos" con miles de filas no puede renderizarse completo — se necesita paginación, búsqueda con debounce y carga parcial |
| Sin estados de carga (loading/skeleton) definidos | Con más usuarios concurrentes, las respuestas no siempre son instantáneas; sin feedback visual, el usuario repite clics y genera más carga |
| Sin manejo explícito de errores de red en el kiosco | El kiosco de portería es la pantalla más crítica: si hay una fluctuación de red y no se le avisa al celador, puede dejar salir un equipo sin registrar el movimiento |
| Componentes documentados solo como clases CSS, no como piezas reutilizables de Django (partials) | A mayor escala de código, sin partials reutilizables cada pantalla nueva reinventa el HTML y se generan inconsistencias |

## 2. Adopción real de Bootstrap (grid, breakpoints, componentes nativos)

### 2.1 Grid y breakpoints — alinear a los estándar de Bootstrap

Los breakpoints custom de `09` (`≤1023px`, `≤767px`, `≤640px`) se reemplazan por los de Bootstrap 5, para que todo el sistema (tus componentes y los nativos de Bootstrap que se agreguen después) responda de forma consistente:

| Breakpoint Bootstrap | Ancho mínimo | Uso en el sistema |
|---|---|---|
| `xs` | <576px | Móvil pequeño: 1 columna en todo, kiosco simplificado |
| `sm` | ≥576px | Móvil grande: formularios de 1 columna, cards `280px` |
| `md` | ≥768px | Tablet: sidebar aún colapsada (offcanvas), filtros en 2 columnas |
| `lg` | ≥992px | Desktop: sidebar fija, filtros en fila completa |
| `xl` | ≥1200px | Desktop amplio: padding de contenido a 32px |
| `xxl` | ≥1400px | Pantallas grandes: `max-width` del contenido se mantiene en 1400px (ya definido en `09`) |

**Migración práctica:** los `filters-grid--N` custom pasan a usar `row` + `col-12 col-md-6 col-lg-3` (etc.) de Bootstrap; el offcanvas de sidebar usa el componente `Offcanvas` nativo de Bootstrap en vez de una implementación propia — menos JS propio que mantener, mejor soporte de accesibilidad (focus trap, ARIA) ya resuelto por el framework.

### 2.2 Componentes nativos de Bootstrap a adoptar (en vez de clases propias equivalentes)

| Necesidad actual (`09`) | Componente Bootstrap nativo recomendado |
|---|---|
| `.card`, `.card-white`, `.card-sm` | `card`, `card-body`, con utilities de padding (`p-3`, `p-4`) en vez de clases dedicadas |
| Sidebar offcanvas propia | `Offcanvas` de Bootstrap |
| `.feedback-box` | `alert` (`alert-success`, `alert-danger`, `alert-warning`) recoloreado con las variables de `09` |
| Confirmaciones de baja/inactivar | `Modal` de Bootstrap (accesible, focus trap incluido) |
| Paginación de listados | `pagination` nativo de Bootstrap |
| Mensajes de "guardado", "movimiento registrado" | `Toast` de Bootstrap (no bloqueante, se apila, se autodescarta) |
| Spinners de carga | `spinner-border` / `spinner-grow` nativos |
| `.badge-*` | `badge` nativo, con las clases de color ya definidas en `09` remapeadas a las variables Bootstrap (`--bs-success`, `--bs-danger`, etc., sobreescritas con los HEX institucionales) |

**Por qué importa:** reescribir un modal, un offcanvas o una paginación accesible desde cero es trabajo (y riesgo de bugs de accesibilidad) que Bootstrap ya resolvió. Con 20.000 usuarios, la superficie de errores de un componente custom mal probado se multiplica.

## 3. Rendimiento y experiencia a escala (20.000 usuarios)

### 3.1 Listados grandes (Personas, Equipos, Movimientos)

- **Paginación server-side obligatoria** en toda tabla que pueda superar ~50 filas — nunca renderizar 20.000 filas en una sola respuesta.
- **Búsqueda con debounce** (300-400ms) antes de disparar la consulta al servidor, para no saturar la base de datos con cada tecla.
- **Filtros combinables** (sede, programa, tipo de vínculo, estado) que se envían como query params, para que la URL sea compartible y el botón "atrás" del navegador funcione bien.
- **Índices de base de datos** sobre las columnas usadas en filtros y búsqueda (`documento`, `serial`, `token_qr`, `email`) — esto es un requisito de backend, pero determina directamente si el listado se siente "instantáneo" o "lento" para el usuario.

### 3.2 Estados de carga (nuevo, no estaba en `09`)

| Estado | Cuándo se usa | Cómo se ve |
|---|---|---|
| **Skeleton** | Al cargar un listado o card por primera vez | Bloques grises con animación sutil de pulso, misma forma que el contenido real |
| **Spinner inline** | Al enviar un formulario (botón) | El botón muestra `spinner-border` pequeño y se deshabilita, evitando doble envío |
| **Toast de confirmación** | Al completar una acción (guardar, registrar movimiento) | Aparece 2-3 segundos, no bloquea la pantalla |
| **Estado de reconexión** | Si una petición HTMX falla por red | Banner fijo arriba: "Sin conexión — reintentando…", con reintento automático |

### 3.3 El kiosco de portería es la pantalla más crítica a proteger

Con más usuarios y más tráfico en el sistema, la pantalla de escaneo no puede depender silenciosamente de que la red esté perfecta:

- Si una petición de escaneo falla, el kiosco **debe mostrar un estado explícito de error** ("No se pudo verificar — reintenta") y no un limbo sin respuesta.
- Considerar una **cola local mínima** (en memoria del navegador) que reintente automáticamente el último escaneo si la red se recupera en pocos segundos, para no perder un movimiento por una fluctuación momentánea.
- El input de escaneo debe **rechazar doble envío** del mismo token en menos de 2 segundos (evita duplicar `Movimiento` si el lector envía el dato dos veces).

### 3.4 Carga de assets

- Bootstrap y las fuentes (Inter, JetBrains Mono) se sirven desde CDN con `integrity` y `crossorigin`, o se auto-hospedan minificados si la universidad prefiere no depender de terceros.
- Sprite SVG único para los íconos (sección 9 de `09`) en vez de un archivo por ícono — reduce peticiones HTTP, relevante cuando miles de usuarios cargan la misma pantalla.

## 4. Componentes reutilizables en Django (no solo clases CSS)

Para que "profesional y escalable" también signifique mantenible, cada componente de `09` se documenta como un **partial de Django** (`{% include %}`), no solo como una clase CSS suelta:

```
templates/
  components/
    _card.html          → recibe {título, cuerpo, footer opcional}
    _badge.html          → recibe {texto, tipo: success|danger|warning|info|neutral}
    _table_paginada.html → recibe {headers, filas, page_obj, filtros}
    _empty_state.html     → recibe {mensaje, icono, cta opcional}
    _toast.html           → recibe {mensaje, tipo}
    _modal_confirmacion.html → recibe {titulo, mensaje, accion_url}
```

Esto evita que cada pantalla nueva reinvente el HTML de una card o un badge, y centraliza cualquier ajuste visual futuro en un solo archivo.

## 5. Flujo de experiencia de usuario — ajustes por rol

### 5.1 Miembro de comunidad (el rol con más volumen de usuarios)

- **Login → destino directo según su única acción relevante** (Mis Equipos), sin pantallas intermedias.
- **Registrar equipo:** formulario en un solo paso si son pocos campos (ya es el caso), con validación inline (no solo al enviar) — el usuario ve el error en el campo apenas sale de él, no después de enviar todo el formulario.
- **Mostrar QR:** debe cargar en menos de 1 segundo incluso en red móvil 3G/4G débil (común en zonas del campus con mala señal) — esto es un requisito de UX que se traduce en: QR generado server-side y cacheado, no regenerado en cada carga si el equipo no cambió.

### 5.2 Celador

- Pantalla de kiosco **sin navegación adicional visible** durante el uso normal — minimizar la posibilidad de que el celador se distraiga o navegue fuera por error durante el flujo de escaneo.
- Acceso rápido (una sola acción) al histórico del turno, sin perder el estado de "esperando escaneo".

### 5.3 Administrador

- Con 20.000 personas potenciales en el sistema, el panel de Personas/Equipos necesita **acciones masivas** razonables (ej. exportar el filtro actual a CSV) en vez de obligar a revisar fila por fila.
- Confirmaciones claras (modal, no `confirm()` nativo del navegador) para cualquier acción destructiva o de bajo impacto (inactivar, resetear contraseña).

## 6. Checklist de "fluidez" de experiencia (además del checklist visual de `09`)

- [x] Ningún listado carga más de ~50 filas sin paginación.
- [x] Toda acción que tarda más de ~300ms muestra un estado de carga (spinner o skeleton). *(spinner en submit + kiosco HTMX)*
- [x] Todo formulario deshabilita su botón de envío mientras procesa (evita doble envío).
- [x] El kiosco muestra un estado explícito ante fallos de red, nunca una pantalla congelada sin explicación.
- [x] Los componentes Bootstrap nativos (modal, offcanvas, toast, pagination) se usan en vez de reimplementaciones propias.
- [x] Los breakpoints de todo el CSS nuevo siguen la escala estándar de Bootstrap (576/768/992/1200/1400).
- [x] Cada pantalla nueva se construye a partir de los partials de la sección 4, no copiando HTML de otra pantalla. *(partials creados; migración gradual de pantallas existentes)*

## 7. Plan de implementación (sin romper lo ya construido)

1. **Auditoría rápida (0.5 día):** listar qué pantallas usan clases custom (`.filters-grid--N`, sidebar propia) que tienen equivalente directo en Bootstrap.
2. **Migrar breakpoints (1 día):** cambiar las media queries custom por las de Bootstrap, verificando visualmente cada pantalla en los 3 breakpoints clave (`sm`, `lg`, `xxl`).
3. **Adoptar componentes nativos (2 días):** reemplazar sidebar/offcanvas propia, feedback boxes → `alert`, confirmaciones → `Modal`, mensajes de acción → `Toast`.
4. **Paginación y búsqueda server-side (2 días):** aplicar a los listados de Personas, Equipos y Movimientos — los que más van a crecer con 20.000 usuarios.
5. **Estados de carga y manejo de red en el kiosco (1 día):** el punto más sensible del sistema, se prueba explícitamente simulando red lenta/caída.
6. **Extraer partials reutilizables (1-2 días, en paralelo):** a medida que se tocan las pantallas de los puntos anteriores, se van moviendo a `templates/components/`.

Este plan es incremental — cada punto se puede desplegar por separado sin dejar el sistema en un estado roto entre pasos.

---

## 8. Estado de implementación

| Paso | Estado | Notas |
|------|--------|-------|
| 1. Auditoría | Completado | Listados sin Paginator; offcanvas propio; sin Bootstrap CDN |
| 2. Breakpoints BS | Completado | Media queries en `991.98` / `767.98` / `575.98` + tokens `--bs-*` |
| 3. Componentes nativos | Completado | Bootstrap 5.3 CDN; `offcanvas-lg`; `alert`; `Modal`; `Toast`; `pagination` |
| 4. Paginación + debounce | Completado | 50 filas/página en equipos, personas, usuarios, movimientos; debounce 350ms en `q` |
| 5. Kiosco red / anti-doble | Completado | Banner de red, reintento, bloqueo 2s mismo token, spinner HTMX |
| 6. Partials | Completado | `templates/components/_*.html` + `static/js/ux.js` |

**Fecha de cierre:** 2026-09-19  
**Pendiente opcional (fase 2):** export CSV masivo admin; sprite SVG único; índices DB documentados en migraciones; skeleton loaders HTMX en todas las tablas.
