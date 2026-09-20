# Plan: Área del gestor — asignación posterior al registro

**Estado:** Completado  
**Fecha:** 2026-09-20

## Objetivo

El gestor administrativo **no** diligencia área en el autorregistro. Puede usar la plataforma con área pendiente. Quien tiene `personas.administrar` (admin del sistema) la asigna después en el panel de personas.

## Checklist

- [x] Quitar validación y UI de área en `/registro/` para gestor administrativo
- [x] Relajar `Persona.clean()` para permitir administrativos sin área
- [x] Área opcional en formulario de persona del panel + badge/filtro «Sin área»
- [x] Actualizar tests de registro y panel
- [x] Actualizar `contexto-completo-sistema.md`, docs 07/08 e índices

## Entregables

| Pieza | Ubicación |
|-------|-----------|
| Autorregistro sin área | `apps/accounts/views.py`, `templates/accounts/registro.html` |
| Modelo | `apps/personas/models.py` |
| Panel asignación | `templates/panel/persona_form.html`, `personas_list.html`, `apps/panel/views.py` |
| Tests | `apps/accounts/tests.py`, `apps/panel/tests.py` |
