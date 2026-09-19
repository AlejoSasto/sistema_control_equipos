# 04 — Diseño UX/UI (Identidad Universidad de Cundinamarca)

> Este documento complementa `00`, `01`, `02` y `03`. Define el sistema visual y las pantallas del MVP. Modo claro únicamente (sin modo oscuro), siguiendo el Manual de Imagen Institucional (ECOM002 V.17) de la Universidad de Cundinamarca.

## 1. Principios de diseño

- **Institucional y sobrio**: el sistema es una herramienta de control interno, no una pieza de marketing. Prioriza claridad y velocidad de lectura sobre decoración.
- **Legibilidad ante todo**: la pantalla de control la usa personal de portería, muchas veces con poca luz o afán. Contraste alto, tipografía grande, estados inequívocos (verde = ok, rojo = alerta).
- **Modo claro fijo**: no se implementa modo oscuro. Fondos claros (blanco/gris muy claro) en todas las pantallas, consistente con el uso institucional del blanco como color dominante (símbolo de transparencia según el manual).
- **Accesibilidad WCAG AA**: relación de contraste mínima 3:1 en elementos gráficos y 4.5:1 en texto, siguiendo la directriz de accesibilidad del propio manual institucional.

## 2. Paleta de color (oficial, tomada del Manual de Imagen Institucional)

### 2.1 Paleta principal — uso predominante en toda la interfaz

| Color | HEX | Uso recomendado en la app |
|---|---|---|
| Verde institucional | `#007B3E` | Color primario: botones principales, barra de navegación, encabezados, estado "✅ coincide" |
| Verde oscuro | `#00482B` | Hover/estado activo de elementos primarios, texto sobre fondos claros de marca, footer |
| Dorado | `#DAAA00` | Acentos secundarios, íconos de advertencia leve, elementos destacados (no botones primarios) |
| Amarillo institucional | `#FBE122` | Solo detalles pequeños o resaltados puntuales — por su bajo contraste con blanco, **nunca usarlo como fondo de texto ni como único indicador de estado** |

### 2.2 Paleta secundaria — apoyo y variedad visual (uso moderado)

| Color | HEX | Uso recomendado en la app |
|---|---|---|
| Turquesa | `#00A99D` | Enlaces, elementos informativos, badges de "en proceso" |
| Verde lima | `#79C000` | Gráficos, indicadores secundarios de progreso |
| Naranja | `#F7931E` | Alertas de advertencia media (ej. "equipo sin foto registrada") |
| Gris | `#4D4D4D` | Texto secundario, bordes, placeholders |

### 2.3 Color funcional adicional (fuera del manual, uso exclusivo de estado)

| Color | HEX | Uso recomendado en la app |
|---|---|---|
| Rojo de alerta | `#C62828` | **Único** uso: estado "🚫 alerta" en la pantalla de control. No es un color institucional — se usa exclusivamente como semáforo funcional, nunca en branding, botones de navegación ni elementos decorativos |

### 2.4 Neutros base

| Color | HEX | Uso |
|---|---|---|
| Blanco | `#FFFFFF` | Fondo principal de todas las pantallas |
| Gris claro | `#F4F5F4` | Fondo de tarjetas y secciones secundarias |
| Gris oscuro (texto) | `#1F2421` | Texto principal (mejor contraste que negro puro sobre verde institucional) |

## 3. Tipografía

El manual institucional define tres familias: Century Gothic, Times New Roman y Montserrat. Para interfaz digital se recomienda:

- **Montserrat** como tipografía principal de la aplicación (títulos y cuerpo de texto): es la familia que el propio manual reserva para aplicaciones digitales modernas y tiene mejor legibilidad en pantalla a tamaños pequeños que Century Gothic.
- **Century Gothic** reservada únicamente para el imagotipo/encabezado institucional si se incluye como elemento gráfico fijo (ej. pie de página con el nombre de la universidad), no para texto funcional de la interfaz.

| Uso | Tipografía | Peso | Tamaño sugerido |
|---|---|---|---|
| Títulos de pantalla | Montserrat | Bold (700) | 24–28px |
| Subtítulos / encabezados de sección | Montserrat | SemiBold (600) | 18–20px |
| Texto de cuerpo | Montserrat | Regular (400) | 15–16px |
| Texto en pantalla de control (kiosco) | Montserrat | Bold (700) | 32–40px (debe leerse a distancia) |
| Texto secundario / ayudas | Montserrat | Regular (400) | 13px, color gris `#4D4D4D` |

## 4. Sistema de componentes

### 4.1 Botones

- **Primario**: fondo `#007B3E`, texto blanco, hover `#00482B`. Uso: "Registrar equipo", "Iniciar sesión", "Mostrar QR".
- **Secundario**: fondo blanco, borde `#007B3E` 1.5px, texto `#007B3E`. Uso: "Cancelar", "Volver".
- **De alerta** (solo en panel admin, ej. "Dar de baja equipo"): fondo `#C62828`, texto blanco.
- Bordes redondeados moderados (8px), nunca completamente circulares salvo botones de ícono.

### 4.2 Tarjetas (cards)

- Fondo `#F4F5F4`, borde sutil `#E0E0E0`, esquinas 12px.
- Usadas para: lista de equipos, lista de personas, historial de movimientos.

### 4.3 Estados / badges

| Estado | Color de fondo | Color de texto | Ícono sugerido |
|---|---|---|---|
| Coincide (ok) | `#007B3E` | Blanco | ✅ / check |
| Alerta | `#C62828` | Blanco | 🚫 / equis |
| No encontrado | `#4D4D4D` | Blanco | ❓ / signo de interrogación |
| Pendiente / en revisión | `#F7931E` | Blanco | ⚠ |

### 4.4 Formularios

- Inputs con borde `#4D4D4D` en reposo, borde `#007B3E` 2px en foco (nunca solo cambio de color de fondo, para cumplir contraste).
- Etiquetas siempre visibles encima del campo (no placeholder-only), por accesibilidad.

## 5. Pantallas del MVP

### 5.1 Login

- Fondo blanco. Tarjeta centrada con el imagotipo de la universidad en la parte superior (respetando el área de seguridad del manual).
- Campos: usuario/documento, contraseña.
- Botón primario "Iniciar sesión" en verde institucional.

### 5.2 Mis equipos (persona autenticada)

- Encabezado verde institucional (`#007B3E`) con el nombre de la persona.
- Lista de tarjetas, una por equipo: marca, modelo, serial (parcialmente enmascarado, ej. `****4821`), botón "Mostrar QR".
- Botón flotante o superior "Registrar nuevo equipo".

### 5.3 Modal / pantalla "Mostrar QR"

- QR grande centrado sobre fondo blanco (máximo contraste para lectura del escáner).
- Debajo: nombre de la persona y datos del equipo, en texto legible.
- Sin elementos decorativos alrededor del QR que puedan interferir con el escaneo.

### 5.4 Pantalla de control de salida (kiosco, uso del celador)

- Diseño de alto contraste, pensado para verse a 1–2 metros de distancia.
- Estado inicial: fondo gris claro, mensaje "Esperando escaneo…", input invisible pero con foco activo.
- Al escanear:
  - **Coincide:** fondo cambia a verde institucional, se muestra foto + nombre + equipo en tipografía grande (32–40px), ✅.
  - **Alerta:** fondo cambia a rojo de alerta, se muestra el mismo detalle con 🚫 y el motivo (equipo inactivo / persona inactiva / no coincide).
  - **No encontrado:** fondo gris oscuro, mensaje "QR no reconocido".
- Botón secundario pequeño en esquina: "Ver historial del día" (acceso rápido para el celador o el administrador).

### 5.5 Panel administrativo

- Navegación lateral con secciones: Sedes, Decanaturas, Programas, Personas, Equipos, Roles y Permisos, Historial de movimientos.
- Uso de tablas simples con filtros por fecha/resultado en el historial de movimientos.
- Reservar el amarillo institucional (`#FBE122`) únicamente para pequeños indicadores o iconografía dentro de las tablas (ej. una etiqueta de "nuevo"), nunca como fondo extenso.

## 6. Accesibilidad — checklist

- [ ] Contraste texto/fondo mínimo 4.5:1 en todo el sistema (verificar especialmente textos sobre `#DAAA00` y `#FBE122`).
- [ ] Ningún estado (ok/alerta) depende solo del color: siempre acompañado de ícono y texto.
- [ ] Tamaños de fuente ajustables/legibles sin zoom en la pantalla de control.
- [ ] Etiquetas de formulario visibles, no solo placeholders.
- [ ] Sin ventanas emergentes bloqueantes, siguiendo la directriz del propio manual institucional de evitar pop-ups por accesibilidad.

## 7. Cómo se integra con el plan de implementación (`03`)

Este sistema de diseño se aplica a partir de la **Fase 2** (login) y se vuelve crítico en la **Fase 5** (pantalla de control), donde el contraste y la velocidad de lectura son el factor que determina si el celador detecta o no una alerta a tiempo. Se recomienda construir primero los componentes base (botones, tarjetas, badges de estado) como un pequeño set reutilizable de plantillas/CSS antes de iniciar la Fase 2, para no rehacer estilos pantalla por pantalla.
