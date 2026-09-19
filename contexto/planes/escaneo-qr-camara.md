# Plan: Escaneo QR por cámara en portería

**Estado:** Completado  
**Fecha:** 2026-09-19

## Objetivo

Permitir que el celador verifique el QR del titular con **pistola**, **cámara del dispositivo** o **teclado**, reutilizando el mismo endpoint HTMX de verificación.

## Entregado

- [x] UI: botón «Usar cámara», panel `#qr-reader`, copy actualizado en `scanner.html`
- [x] CSS kiosco (`.kiosk-camera-*`) en `static/css/custom.css`
- [x] `static/js/kiosk-camera.js` + CDN `html5-qrcode@2.3.8`
- [x] Sin cambios de lógica en `escanear_qr_salida` (mismo `codigo` POST)
- [x] Documentación en `contexto/08` e índices de planes

## Notas

- La cámara requiere **HTTPS** (o localhost). En HTTP se muestra aviso y el teclado/pistola siguen disponibles.
- Debounce de 2 s del kiosco + pausa de cámara tras lectura evitan movimientos duplicados.
