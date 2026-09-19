# 05 — Sistema de Diseño v2 (revisión: sin amarillo, Inter + Bootstrap)

> Este documento **reemplaza** las secciones de tipografía, espaciado y color de `04-diseno-ux-ui.md`. Las secciones de pantallas (5) y accesibilidad (6) de `04` siguen aplicando conceptualmente, solo se ajustan los valores de color/tipografía/espaciado a lo definido aquí.

## 0. Qué cambia respecto a `04`

- Se **elimina el amarillo institucional** (`#FBE122`) y el dorado (`#DAAA00`) de la interfaz. El color institucional que sostiene la identidad visual pasa a ser exclusivamente el **verde** de la Universidad, en sus dos tonos.
- Tipografía: de Montserrat pasa a **Inter**, más estándar en dashboards/SaaS y con mejor rendimiento en pantallas pequeñas y tamaños de texto reducidos.
- Espaciado, radios y tamaños de componentes: se adopta el **sistema de espaciado de Bootstrap** (escala 4/8/16/24/48 px) en vez de valores libres.

## 1. Paleta de color final (sin amarillo)

### 1.1 Marca (uso con moderación — navegación, botones primarios, estados de éxito)

| Color | HEX | Uso |
|---|---|---|
| Verde institucional | `#007B3E` | Botón primario, enlaces activos, ítem de navegación activo, estado "coincide" |
| Verde oscuro | `#00482B` | Hover de elementos primarios, texto de marca sobre fondo claro |

### 1.2 Funcionales (solo para estado, nunca decorativos)

| Color | HEX | Uso |
|---|---|---|
| Rojo de alerta | `#C62828` | Estado "alerta" en control de salida, botones destructivos (dar de baja) |
| Naranja de advertencia | `#F7931E` | Estado "pendiente / revisar" (uso puntual, no como color de marca) |
| Turquesa informativo | `#00A99D` | Badges informativos, enlaces secundarios (uso opcional y moderado) |

### 1.3 Neutros (base de toda la interfaz — el protagonista visual real)

| Color | HEX | Uso |
|---|---|---|
| Blanco | `#FFFFFF` | Fondo base |
| Gris superficie | `#F5F6F5` | Fondo de cards, sidebar, secciones alternas |
| Gris borde | `#E1E3E1` | Bordes de inputs, cards, separadores |
| Gris texto secundario | `#5B615D` | Texto secundario, labels, placeholders |
| Gris texto principal | `#1C201D` | Texto principal (evitar negro puro) |

**Regla de uso:** en una pantalla típica, el 85-90% de la superficie debe ser blanco/gris neutro; el verde institucional aparece solo en elementos de acción o estado activo, nunca como fondo extenso de página.

## 2. Tipografía — Inter

| Uso | Peso | Tamaño |
|---|---|---|
| Texto normal (cuerpo) | 400 | 16px |
| Texto secundario | 400 | 14px |
| Texto pequeño / ayudas | 400 | 12px |
| Navegación, etiquetas, botones | 500 | 14–16px |
| Subtítulos | 600 | 18–20px |
| Títulos de sección | 600 | 24px |
| Títulos principales | 700 | 32px |
| Títulos de páginas importantes | 700 | 36–40px |
| Pantalla de control (kiosco) | 700 | 32–40px (excepción: prioriza legibilidad a distancia sobre la escala estándar) |

Evitar pesos 800/900 — reservar el peso 700 únicamente para títulos principales.

## 3. Espaciado (escala Bootstrap)

| Token | Valor |
|---|---|
| 1 | 4px |
| 2 | 8px |
| 3 | 16px |
| 4 | 24px |
| 5 | 48px |

**Aplicación práctica:**

| Relación | Espacio |
|---|---|
| Título → subtítulo | 8–12px |
| Subtítulo → contenido | 16–24px |
| Card → card | 16–24px |
| Sección → sección | 32–48px |
| Padding de card normal | 24px |
| Padding de card pequeña | 16px |
| Padding de modal | 24–32px |
| Padding de contenido principal | 24–32px |

Uso predominante: `p-3` (16px) y `p-4` (24px). Evitar el abuso de `p-5` fuera de separaciones entre secciones grandes.

## 4. Componentes

### 4.1 Botones

| Tamaño | Altura | Padding horizontal |
|---|---|---|
| Pequeño | 32–36px | 12px |
| Normal | 40–44px | 16px |
| Grande | 48–52px | 16–20px |

- Primario: fondo `#007B3E`, texto blanco, hover `#00482B`.
- Secundario: fondo blanco, borde `#007B3E` 1px, texto `#007B3E`.
- Destructivo: fondo `#C62828`, texto blanco (solo panel admin).
- Border radius: 6–8px. `rounded-pill` se reserva para badges/tags/estados, no para botones de acción general.

### 4.2 Inputs

- Altura: 40–44px. Padding: 10–12px vertical / 16px horizontal.
- Border radius: 6–8px. Borde `#E1E3E1` en reposo, `#007B3E` 2px en foco.
- Label siempre visible encima del input, peso 500, 14px, separación de 8px respecto al campo.
- Separación entre campos distintos: 16–24px.

### 4.3 Cards

- Padding: 24px (16px en cards compactas de listado).
- Border radius: 10–12px. Borde 1px `#E1E3E1`. Sombra muy ligera (`0 1px 2px rgba(0,0,0,0.06)`), nunca sombras pronunciadas.

### 4.4 Badges / estados

- Border radius: pill (50%/9999px).
- Colores según estado: verde (coincide), rojo (alerta), gris (no encontrado/inactivo), naranja (pendiente).
- Siempre acompañados de texto o ícono, nunca solo color (accesibilidad).

### 4.5 Avatares

- Border radius: circular (50%). Usado para foto de la persona en la pantalla de control y en el panel de personas.

## 5. Layout

- **Contenedor:** `container-fluid` para las vistas tipo dashboard (panel admin, mis equipos).
- **Sidebar:** 240–260px de ancho en escritorio; en móvil se colapsa a menú offcanvas.
- **Header:** 64px de alto, fijo, con el imagotipo institucional a la izquierda (respetando su área de seguridad) y acciones de usuario a la derecha.
- **Grid:** `row` + `col-*` para organizar contenido; `gap-3`/`gap-4` para separación entre elementos flexibles/grid.

### Padding responsive

| Breakpoint | Padding de contenido |
|---|---|
| Móvil | 16px |
| Tablet | 24px |
| Desktop | 32px |
| Pantallas grandes | hasta 40px (los componentes internos no crecen, solo el margen) |

## 6. Cómo evitar que se vea "genérico / hecho por IA"

Esta sección es la que marca la diferencia entre una interfaz funcional y una que se percibe como diseñada con criterio real:

- **Un solo color de marca, no un arcoíris de acentos.** El verde institucional es el único color con peso visual fuerte; todo lo demás (rojo, naranja, turquesa) es funcional y aparece solo cuando comunica un estado, nunca como decoración.
- **Nada de degradados genéricos ni "glassmorphism".** Fondos sólidos, bordes sutiles, sombras casi imperceptibles. Los degradados llamativos en botones/headers son el sello más reconocible de una interfaz "genérica".
- **Un solo set de íconos**, coherente en todo el sistema (recomendado: Bootstrap Icons, ya que el proyecto usa Bootstrap). Nada de mezclar emojis con íconos SVG — los emojis (✅🚫⚠️) sirven bien en prototipos pero en producción se reemplazan por íconos vectoriales del mismo set, con el color de estado aplicado al ícono.
- **Jerarquía tipográfica real**, no todo en el mismo tamaño con distinto peso. La diferencia entre un título (32px/700) y el cuerpo (16px/400) debe ser notoria; los pasos intermedios tibios (ej. todo en 18-20px) son los que dan sensación de plantilla sin trabajar.
- **Alineación estricta a la grilla.** Elementos que no se alinean entre secciones (un botón desplazado 4px respecto a la card de arriba) es lo primero que delata una interfaz sin revisión de detalle.
- **Contenido real en las maquetas**, no "Lorem ipsum" ni nombres de ejemplo genéricos tipo "Usuario 1". Usa nombres, seriales y datos con la forma real que tendrán en producción (formato de documento colombiano, marcas de equipos reales, etc.) desde el primer prototipo.
- **Evitar centrar todo por defecto.** El centrado excesivo (títulos, párrafos, botones todos centrados) es otro patrón típico de plantilla genérica; usa alineación a la izquierda para texto de lectura y reserva el centrado para estados vacíos o pantallas de una sola acción (login, pantalla de control).
- **Estados vacíos y de error diseñados, no dejados por defecto.** Una lista de equipos vacía, un QR no reconocido, un formulario con error — cada uno debe tener su propio mensaje y disposición, no un genérico "No data" del framework.

## 7. Resumen de tokens para implementación directa

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

  --font-family: 'Inter', sans-serif;

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 16px;
  --space-4: 24px;
  --space-5: 48px;

  --header-height: 64px;
  --sidebar-width: 250px;
}
```
