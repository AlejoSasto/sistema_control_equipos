# Plan: Módulo de Reportes Excel

**Estado:** Completado  
**Fecha:** 2026-09-19  
**Documento rector:** [`../12-modulo-reportes-excel.md`](../12-modulo-reportes-excel.md)

## Objetivo

Implementar la app `reportes` con cinco exportaciones `.xlsx` (xlsxwriter + gráficos nativos), filtros reutilizables, permisos `reportes.ver` / `reportes.exportar`, auditoría de exportaciones y umbral síncrono. La cola asíncrona (Celery/RQ) queda fuera de esta fase.

## Checklist

- [x] Documentación e índices actualizados
- [x] App `reportes` + `xlsxwriter` + URLs + permisos + menú + acción auditoría `exportar`
- [x] Filtros, estilos, umbrales y generador base
- [x] Generador Movimientos (referencia)
- [x] Generadores Equipos, Personas, Alertas, Ejecutivo
- [x] Vistas y templates
- [x] Tests y cierre (checklist doc 12)

## Entregables clave

| Área | Ubicación |
|------|-----------|
| App | `apps/reportes/` |
| Generadores | `apps/reportes/generadores/` |
| Templates | `templates/reportes/` |
| Permisos | migración `accounts.0005_reportes_permissions` + seed |
| Auditoría | acción `exportar` en `auditoria_cambio` |
| Tests | `apps/reportes/tests/test_reportes.py` |

## Notas

- Exportación solo síncrona: máx. 20.000 filas / 90 días en movimientos-alertas.
- Hook `acotar_por_alcance` vacío (extensión futura para decano/coordinador).
- Facultad en ORM = `Decanatura`.
- Fase 2 documentada: Celery/RQ, archivos temporales 24h, correo.
