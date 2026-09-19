# Walkthrough: Implementación Completa de los Planes 01, 02, 03, 04 y 05

Se ha completado la ejecución paso a paso de los documentos rectores del **Sistema de Control de Salida de Equipos de Cómputo** para la **Universidad de Cundinamarca**:
1. [01-modelo-negocio-roles-permisos.md](01-modelo-negocio-roles-permisos.md) (Reglas de negocio y filosofía de salida)
2. [02-modelo-datos-diccionario.md](02-modelo-datos-diccionario.md) (Diccionario de datos e integridad referencial en PostgreSQL)
3. [03-plan-implementacion-paso-a-paso.md](03-plan-implementacion-paso-a-paso.md) (Ruta de construcción modular por fases)
4. [04-diseno-ux-ui.md](04-diseno-ux-ui.md) (Conceptos de pantallas y accesibilidad)
5. [05-sistema-diseno-v2.md](05-sistema-diseno-v2.md) (Sistema de diseño definitivo: sin amarillo, Inter + escala de espaciado Bootstrap, superficies neutras)

---

## 1. Novedades del Sistema de Diseño v2 (`05`)

En cumplimiento de las directrices de `05-sistema-diseno-v2.md`:
- **Eliminación Total de Amarillo y Dorado**: Se suprimieron `#FBE122` y `#DAAA00`. La marca se sostiene exclusivamente en el **Verde Institucional** (`#007B3E`) y Verde Oscuro (`#00482B`).
- **Superficies Neutras (85–90% de la interfaz)**: Fondo de pantalla blanco (`#FFFFFF`), cards y sidebar en gris superficie (`#F5F6F5`), bordes (`#E1E3E1`) y textos principales en `#1C201D` y secundarios en `#5B615D`.
- **Tipografía Inter**: Reemplazo de Montserrat por **Inter** (400, 500, 600, 700), mejorando la legibilidad en tablas y pantallas de información densa.
- **Escala de Espaciado Bootstrap**: Uso estricto de la escala 4px, 8px, 16px, 24px y 48px (`--space-1` a `--space-5`).
- **Cero Degradados ni Glassmorphism**: Fondos planos y limpios, sombras casi imperceptibles (`0 1px 2px rgba(0,0,0,0.06)`).
- **Íconos Vectoriales SVG**: Se reemplazaron los emojis informales (✅, 🚫, ❓) por íconos SVG vectoriales limpios y accesibles.
- **Kiosco de Portería**: Fondos planos de alta visibilidad: `#007B3E` (OK), `#C62828` (Alerta) y `#5B615D` (No encontrado) con tipografía de 34–40px Inter legible a 1–2 metros de distancia.

---

## 2. Arquitectura y Modelo de Datos (`02`)

11 tablas activas en **PostgreSQL 17** (`sistema_control`):
- `sede`, `decanatura`, `programa`, `persona`, `rol`, `permiso`, `rol_permiso`, `usuario`, `usuario_rol`, `equipo`, `movimiento`.

---

## 3. Demostración y Accesos

Servidor local activo en **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**:

| Perfil | Usuario | Contraseña | Enlace Directo |
|---|---|---|---|
| **Celador (Portería)** | `celador1` | `celador123` | [Puesto de Control Kiosco](http://127.0.0.1:8000/acceso/control-salida/) |
| **Docente (Comunidad)** | `docente1` | `docente123` | [Mis Equipos & Pases QR](http://127.0.0.1:8000/equipos/mis-equipos/) |
| **Administrador** | `admin` | `admin123` | [Auditoría de Salidas](http://127.0.0.1:8000/acceso/historico/) |
