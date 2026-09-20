# Plan: Personal externo y vigilante (doc 16)

**Estado:** Completado  
**Fecha:** 2026-09-20  
**Documento rector:** [`../16-personal-externo-y-vigilante.md`](../16-personal-externo-y-vigilante.md)

## Objetivo

Separar **cuenta** de **visita** para personal externo (autodeclaración); alta interna de **vigilante** (una sede, correo libre); validar visitas y badge de otra sede en el kiosco.

## Checklist

- [x] Documento `16` + índices `contexto/README.md` / `planes/README.md`
- [x] Seed: `personal_externo`, `vigilante`; rol `vigilante` activo; dominio NULL
- [x] Modelo `VisitaExterno` + services + `cerrar_visitas_vencidas` + motivos alerta
- [x] `/registro/` extendido + pantalla “Registrar nueva visita” + anti-duplicado
- [x] Alta interna de vigilante en panel
- [x] Kiosco: visita + badges externo / otra sede; reportes motivos
- [x] Tests + `contexto-completo-sistema.md`
