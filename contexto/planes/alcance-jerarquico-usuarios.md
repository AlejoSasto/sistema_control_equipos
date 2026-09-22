# Alcance jerárquico por usuario

**Estado:** Completado  
**Fecha:** 2026-09-21

## Objetivo

Introducir alcance jerárquico (GLOBAL / SEDE / FACULTAD / PROGRAMA / DEPENDENCIA) ortogonal a permisos, con filtrado central en panel, reportes, equipos y control de acceso. FUSA no se hardcodea: es un usuario con alcance `GLOBAL`.

## Checklist

- [x] Modelo `AlcanceUsuario` + migración de datos (`ResponsableDependencia`, `admin_sistema`, vigilantes)
- [x] Módulo `apps/accounts/alcance.py` (`aplicar_alcance`, helpers, `puede_ver_objeto`, `puede_asignar_alcance`)
- [x] Decorador `@requiere_permiso` inyecta `request.alcance`; context processor badge topbar
- [x] Alcance en panel personas/usuarios/vigilantes y selects
- [x] Alcance en equipos institucionales, catálogos organización y `equipos.views`
- [x] Histórico kiosco + `acotar_por_alcance` real en reportes/dashboard
- [x] `es_admin_global` / `unidades_de` / `puede_gestionar_unidad` integrados con alcance
- [x] Permiso `usuarios.gestionar_alcance`, seed GLOBAL para `admin`, UI en ficha usuario
- [x] Tests de filtrado, IDOR y escritura (`apps/accounts/tests_alcance.py`)
- [x] Documentación en `contexto-completo-sistema.md` e índices
- [x] Migraciones listas para producción (`organizacion.0005`–`0006`, `accounts.0011`)

## Entregables (código)

| Pieza | Ruta |
|-------|------|
| Modelo | `apps/organizacion/models.py` → `AlcanceUsuario` |
| Filtrado | `apps/accounts/alcance.py` |
| Permiso | `usuarios.gestionar_alcance` (seed + migración `0011`) |
| UI | `templates/panel/usuario_detail.html` + badge en `templates/base.html` |
| Context processor | `apps/accounts/context_processors.py` |
| Tests | `apps/accounts/tests_alcance.py` |

## Despliegue (Render / Docker)

El `entrypoint.sh` ya ejecuta `migrate` → `seed_data` → `collectstatic`. Al desplegar este cambio:

1. Push a `main` (o Manual Deploy en Render).
2. En logs del arranque deben aparecer (si aún no aplicadas):
   - `Applying organizacion.0005_alcance_usuario`
   - `Applying organizacion.0006_alcance_usuario_indexes`
   - `Applying accounts.0011_usuarios_gestionar_alcance_permission`
   - `Cargando catálogos institucionales` (seed upsert; **no** borra usuarios/personas reales)
3. Post-deploy: login `admin` → ficha de otro usuario → sección **Alcance**; topbar «Alcance: Global».
4. Checklist: un admin con solo `SEDE` no ve personas/equipos/reportes de otra sede.

Migración de datos en `0005` (aditiva):

- Usuarios con rol `admin_sistema` → `AlcanceUsuario(nivel=global)` si no tienen.
- Filas activas de `ResponsableDependencia` → alcance facultad/programa/área.
- Vigilantes con `persona.sede` → alcance `sede`.

No elimina filas de negocio existentes.

## Notas de diseño

- Permisos = *qué puede hacer*; alcance = *sobre qué filas*.
- Varias filas de alcance = **unión**; `GLOBAL` gana.
- `ResponsableDependencia` se mantiene para inventariar/asignar institucionales.
- Un actor no puede ampliar su propio alcance ni otorgar un nivel superior al suyo.
- Vigilante al crearse recibe alcance `SEDE` de su persona; el badge «Otra sede» en kiosco se conserva.
