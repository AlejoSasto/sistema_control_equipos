# Login por cédula + username institucional

**Estado:** Completado  
**Fecha:** 2026-09-21

## Objetivo

- Autenticar con número de documento (cédula), username o correo.
- En perfiles con correo institucional (`dominio_correo_requerido`), el username es la parte local del correo.

## Checklist

- [x] `auth_utils.py`: `username_desde_correo`, `resolver_usuario_por_identificador`
- [x] `DocumentoOUsuarioBackend` + `AUTHENTICATION_BACKENDS`
- [x] Autorregistro: username institucional + unicidad
- [x] Panel `usuario_create`: deriva username si email `@ucundinamarca.edu.co`
- [x] Vigilante sin cambio (username = correo)
- [x] UI login alineada
- [x] Tests y documentación
- [x] Listo para deploy: sin migración de datos destructiva (solo código + settings)

## Despliegue (Render)

No requiere migración de BD nueva. Al hacer push:

1. `migrate` (sin operaciones pendientes relacionadas a login/cedula).
2. `seed_data` (idempotente; no resetea passwords ni borra usuarios reales).
3. Verificar login con documento / username local / correo.

Usuarios ya creados con `username=correo completo` **no se migran**; siguen entrando por ese username, email o cédula.

## Notas

- Externo / vigilante: username = correo completo.
- Backend: `apps/accounts/backends.py`.
