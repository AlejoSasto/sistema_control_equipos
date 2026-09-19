# 09 — Guía completa de diseño UX/UI

**Proyecto:** Sistema de Control de Salida de Equipos de Cómputo  
**Institución:** Universidad de Cundinamarca  
**Estado:** Vigente (refleja la implementación real en código)  
**Fuente de estilos:** [`static/css/custom.css`](../static/css/custom.css)  
**Documentos base:** [`05-sistema-diseno-v2.md`](05-sistema-diseno-v2.md) (tokens) · [`04-diseno-ux-ui.md`](04-diseno-ux-ui.md) (histórico)

> Esta guía es la **referencia única** de cómo se ve y se comporta la interfaz hoy. Si hay conflicto con `04`, gana este documento y el CSS.

---

## 1. Principios de producto

| Principio | Qué significa en la práctica |
|-----------|------------------------------|
| **Institucional y sobrio** | Herramienta de control interno, no marketing. Claridad > decoración. |
| **Legibilidad en portería** | El kiosco se lee a 1–2 m: tipografía grande, estados inequívocos (verde / rojo / gris). |
| **Modo claro fijo** | Sin dark mode. Fondos blanco / gris neutro en todas las pantallas. |
| **Un solo color de marca** | Verde `#007B3E`. Rojo, naranja y turquesa solo comunican estado. |
| **Desktop-first preservado** | El escritorio conserva el diseño v2; el responsive solo actúa en media queries. |
| **Accesibilidad WCAG AA** | Contraste texto ≥ 4.5:1; estados nunca solo por color (texto + ícono SVG). |

### Qué evitar (anti-patrones)

- Amarillo / dorado institucional en UI (`#FBE122`, `#DAAA00`) — eliminados.
- Degradados, glassmorphism, sombras fuertes, glows.
- Emojis como íconos de estado (✅🚫) — usar SVG.
- Centrar todo el contenido (salvo login / estados vacíos / QR en pantalla).
- “Lorem ipsum” o datos genéricos en maquetas.

---

## 2. Paleta de color

### 2.1 Marca (uso moderado: ~10–15% de la pantalla)

| Token CSS | HEX | Uso |
|-----------|-----|-----|
| `--color-primary` | `#007B3E` | Botón primario, nav activo, badges OK, kiosco “coincide” |
| `--color-primary-dark` | `#00482B` | Hover de primario, texto de marca sobre fondo claro |

### 2.2 Funcionales (solo estado)

| Token CSS | HEX | Uso |
|-----------|-----|-----|
| `--color-danger` | `#C62828` | Alerta en kiosco, botones destructivos, badge peligro |
| `--color-warning` | `#F7931E` | Advertencia / pendiente (puntual) |
| `--color-info` | `#00A99D` | Badge informativo (opcional, moderado) |

### 2.3 Neutros (85–90% de la superficie)

| Token CSS | HEX | Uso |
|-----------|-----|-----|
| `--color-bg` | `#FFFFFF` | Fondo de página, topbar, cards blancas |
| `--color-surface` | `#F5F6F5` | Sidebar, cards de superficie, fondos de tabla th |
| `--color-border` | `#E1E3E1` | Bordes de inputs, cards, separadores |
| `--color-text` | `#1C201D` | Texto principal (no negro puro) |
| `--color-text-secondary` | `#5B615D` | Labels, ayudas, placeholders, subtítulos |

### 2.4 Superficies auxiliares (feedback)

| Clase | Fondo | Uso |
|-------|-------|-----|
| `.feedback-success` | `#EBF5F0` | Mensajes OK |
| `.feedback-danger` | `#FDE8E8` | Errores |
| `.feedback-warning` | `#FEF3C7` | Advertencias |
| Nav hover | `#ECEEEC` | Hover de `.nav-link` |
| Nav activo | `#EBF5F0` + borde izquierdo verde | Ítem de menú activo |

### 2.5 Regla de composición

```
Pantalla típica ≈ 85–90% neutros + 10–15% verde de acción/estado
                 + color funcional solo donde hay semáforo
```

---

## 3. Tipografía

| Familia | Token / uso |
|---------|-------------|
| **Inter** (400, 500, 600, 700) | UI general — `--font-family` |
| **JetBrains Mono** | Seriales, tokens, input de QR — `--font-mono` |

| Rol | Peso | Tamaño aprox. | Clase / contexto |
|-----|------|---------------|------------------|
| Cuerpo | 400 | 16px | `body` |
| Secundario | 400–500 | 14px (0.875rem) | Labels, tablas, botones |
| Pequeño / caps | 500–600 | 11–12px | `.nav-section-title`, `.brand-subtitle` |
| Título topbar | 600 | 20px (1.25rem) | `.topbar-title` |
| Título de card | 600 | 18px (1.125rem) | `.card-title` |
| Kiosco headline | 700 | 34–38px | `.kiosk-headline` |
| Stat numérico | 700 | ~30px | `.stat-value` |

No usar pesos 800/900.

---

## 4. Espaciado, radios y sombra

### Escala Bootstrap (tokens)

| Token | Valor |
|-------|-------|
| `--space-1` | 4px |
| `--space-2` | 8px |
| `--space-3` | 16px |
| `--space-4` | 24px |
| `--space-5` | 48px |

### Radios

| Token | Valor | Uso |
|-------|-------|-----|
| `--radius-sm` | 6px | Botones, inputs, nav links |
| `--radius-md` | 10px | Cards, paneles kiosco |
| `--radius-lg` | 16px | Contenedores amplios |
| `--radius-pill` | 9999px | Badges, indicador de sede |

### Sombra

```css
--shadow-subtle: 0 1px 2px rgba(0, 0, 0, 0.06);
```

Una sola sombra suave. Nunca multi-capa ni glow.

---

## 5. Layout estructural

```
┌─────────────┬──────────────────────────────────────┐
│  Sidebar    │  Topbar (64px)                       │
│  250px      ├──────────────────────────────────────┤
│  #F5F6F5    │  page-body (max 1400px, centrado)    │
│             │  padding 24px / 32px (≥1200px)       │
└─────────────┴──────────────────────────────────────┘
```

| Elemento | Medida | Notas |
|----------|--------|-------|
| Sidebar | `--sidebar-width: 250px` | Fija en desktop; offcanvas ≤1023px |
| Topbar | `--header-height: 64px` | Sticky; una sola línea en desktop |
| Contenido | `max-width: 1400px` | `.page-body` |
| Auth (login/registro) | Centrado vertical | Sin sidebar |

### Navegación

- Brand: escudo oficial (`static/img/logo-uc.png`) + título “Control Equipos”.
- Secciones: Portería, Mi Espacio, Panel, Catálogos (según permisos).
- Ítem activo: fondo verde suave + borde izquierdo 3px `#007B3E`.
- Footer: avatar inicial + nombre + rol + logout.

---

## 6. Responsive (desktop-first)

Los estilos **base** = escritorio. Los cambios móviles van solo en `@media`.

| Breakpoint | Comportamiento |
|------------|----------------|
| **≥1024px** | Sidebar fija, topbar 64px, filtros en fila, cards `minmax(340px)`, padding 24/32px |
| **≤1023px** | Hamburguesa + sidebar offcanvas + overlay; filtros 2 columnas |
| **≤767px** | Forms/detalles/filtros → 1 columna; topbar puede wrap; cards `280px` |
| **≤640px** | Padding contenido 16px; stats 1 columna; cards más compactas |

### Clases de grid

| Clase | Desktop | Móvil |
|-------|---------|-------|
| `.filters-grid--6` | `1.5fr 1fr 1fr 1fr 1fr auto` | 2 cols → 1 col |
| `.filters-grid--5` | `1.5fr 1fr 1fr 1fr auto` | 2 cols → 1 col |
| `.filters-grid--4` | `1.5fr 1fr 1fr auto` | 2 cols → 1 col |
| `.form-grid-2` | `1fr 1fr` | 1 col |
| `.form-grid-3` | `1fr 1fr 1fr` | 1 col |
| `.form-grid-1-2` | `1fr 2fr` | 1 col |
| `.detail-grid` / `-wide` / `-split` / `-scan` | 2 columnas proporcionales | 1 col |
| `.stats-grid-4` | 4 columnas | 2 → 1 |
| `.cards-grid` | `minmax(340px, 1fr)` | `minmax(280px, 1fr)` |

Tablas: siempre dentro de `.table-responsive` (scroll horizontal permitido).

---

## 7. Componentes UI

### 7.1 Botones (`.btn`)

| Variante | Clase | Apariencia |
|----------|-------|------------|
| Primario | `.btn-primary` | Fondo verde, texto blanco, hover verde oscuro |
| Secundario | `.btn-secondary` / `.btn-outline` | Fondo blanco, borde y texto verde |
| Destructivo | `.btn-danger` / `.btn-destructivo` | Fondo rojo, texto blanco |
| Pequeño | `.btn-sm` | Altura ~34px |
| Grande | `.btn-lg` | Altura ~50px |

- Altura normal: **42px**. Radius: 6px. **Nunca** pill en botones de acción general.

### 7.2 Formularios

- `.form-group` + `.form-label` (arriba, 500, 14px) + `.form-control` / `.form-select`
- Altura input: **42px**; foco: borde verde 2px
- Separación entre grupos: `--space-4` (24px)

### 7.3 Cards

| Clase | Uso |
|-------|-----|
| `.card` | Superficie `#F5F6F5`, borde, radius 10px, padding 24px |
| `.card-white` | Fondo blanco |
| `.card-sm` | Padding 16px |
| `.card-header` / `.card-title` / `.card-subtitle` | Encabezado interno |

### 7.4 Badges / estados

| Clase | Significado |
|-------|-------------|
| `.badge-success` / `.badge-ok` | Activo / coincide |
| `.badge-danger` / `.badge-alert` | Alerta / baja |
| `.badge-warning` | Pendiente |
| `.badge-info` | Informativo |
| `.badge-neutral` | Inactivo / neutro |
| `.badge-subtle` | Chip suave con borde |

Siempre con texto (y preferible ícono SVG). Forma: pill.

### 7.5 Tablas

- `.table` sobre fondo blanco; cabecera en superficie gris.
- Hover de fila: `#FAFAFA`.
- Contenedor: `.table-responsive`.

### 7.6 Feedback

- `.feedback-box` + `.feedback-success` | `.feedback-danger` | `.feedback-warning`

### 7.7 Kiosco de portería

| Clase | Rol |
|-------|-----|
| `.kiosk-grid` | Scanner + resultado (1 col ≤1024px) |
| `.kiosk-state-ok` | Fondo `#007B3E`, texto blanco |
| `.kiosk-state-alert` | Fondo `#C62828`, texto blanco |
| `.kiosk-state-notfound` | Fondo `#5B615D`, texto blanco |
| `.kiosk-headline` | 34–38px bold |
| `.kiosk-input` | Mono, altura 52px |

### 7.8 Stats y QR

- `.stats-grid` / `.stat-card` / `.stat-value` / `.stat-label`
- `.qr-display-container` / `.qr-code-box` / `.qr-info-box` — pase móvil centrado, max ~460px

---

## 8. Pantallas y patrones UX

| Pantalla | Patrón UX |
|----------|-----------|
| **Login / Registro** | Una acción dominante; formulario centrado; sin sidebar |
| **Puesto de salida (QR)** | Semáforo inmediato; input siempre listo para pistola; tipografía a distancia |
| **Mis equipos** | Cards con estado y CTA “Mostrar QR” |
| **Inventario / listados** | Filtros en fila (desktop) + tabla limpia |
| **Detalle equipo** | Dos columnas (info + QR sticky); 1 col en móvil |
| **Mi perfil** | Stats + datos personales |
| **Panel admin** | CRUD sobrio; permisos solo lectura; confirmaciones claras en bajas |

### Flujos clave

1. **Comunidad:** registro → login → registrar equipo → mostrar QR en pantalla.
2. **Portería:** login celador → escanear → OK / alerta / no encontrado → histórico.
3. **Admin:** personas → usuarios → roles → catálogos (sedes, programas, áreas, tipos de vínculo).

### Estados vacíos

Cada lista vacía debe tener mensaje + ícono SVG + CTA cuando aplique (ej. “Registrar primer equipo”), no un “No data” genérico.

---

## 9. Iconografía

- **SVG stroke** inline (24×24 viewBox), coherentes en todo el sistema.
- Color: `currentColor` para heredar del texto / estado.
- No mezclar emojis con SVG en producción.

---

## 10. Tokens CSS canónicos (`:root`)

```css
:root {
  --color-primary: #007B3E;
  --color-primary-dark: #00482B;
  --color-danger: #C62828;
  --color-warning: #F7931E;
  --color-info: #00A99D;

  --color-bg: #FFFFFF;
  --color-surface: #F5F6F5;
  --color-border: #E1E3E1;
  --color-text: #1C201D;
  --color-text-secondary: #5B615D;

  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-pill: 9999px;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 16px;
  --space-4: 24px;
  --space-5: 48px;

  --header-height: 64px;
  --sidebar-width: 250px;

  --shadow-subtle: 0 1px 2px rgba(0, 0, 0, 0.06);
}
```

---

## 11. Checklist al diseñar / implementar una pantalla nueva

1. ¿El 85%+ es neutro (blanco/gris)? ¿El verde solo en acciones o estado?
2. ¿Tipografía Inter + jerarquía clara (título ≠ cuerpo)?
3. ¿Espaciado solo de la escala 4/8/16/24/48?
4. ¿Desktop se ve igual al resto del sistema (sin layouts “móviles” en base)?
5. ¿≤767px apila a 1 columna y el menú es offcanvas?
6. ¿Estados con texto + color (no solo color)?
7. ¿Íconos SVG, sin emojis ni degradados?
8. ¿Estado vacío y error diseñados?

---

## 12. Relación con otros documentos

| Documento | Rol |
|-----------|-----|
| [`04-diseno-ux-ui.md`](04-diseno-ux-ui.md) | Histórico (Montserrat + amarillo) — no usar para implementar |
| [`05-sistema-diseno-v2.md`](05-sistema-diseno-v2.md) | Especificación de tokens v2 |
| **Este `09`** | Guía operativa completa alineada al código |
| [`planes/sistema-responsive-completo.md`](planes/sistema-responsive-completo.md) | Responsive desktop-first |
| [`planes/desktop-intacto-responsive.md`](planes/desktop-intacto-responsive.md) | Corrección look escritorio |
