# Normalizar lectura QR de pistola Zebra DS22

**Estado:** Completado  
**Fecha:** 2026-09-19

## Problema

En portería, la Zebra DS22 (modo teclado HID) tipifica apóstrofos (`'`) donde el UUID del QR tiene guiones (`-`) cuando el layout del escáner es US y el del SO es español. El backend rechazaba el código como UUID inválido y caía a búsqueda por serial → **QR NO RECONOCIDO**.

Ejemplo leído: `ea6bbf3c'e51a'418e'a23c'b4702b96f450`  
Esperado: `ea6bbf3c-e51a-418e-a23c-b4702b96f450`

## Solución

Normalización en servidor antes de resolver el equipo:

1. Strip de espacios y CR/LF del Enter de la pistola.
2. Sustitución `'` → `-`.
3. Si tras limpiar hay 32 hex, reconstruir UUID canónico.

Archivos:

- `apps/control_acceso/utils.py` — `normalizar_codigo_escaneado`
- `apps/control_acceso/views.py` — uso en `escanear_qr_salida`
- `apps/control_acceso/tests.py` — apostrofos, hex puro, serial

## Checklist

- [x] Helper `normalizar_codigo_escaneado`
- [x] Cablear en `escanear_qr_salida`
- [x] Tests de apostrofos, hex sin separadores y serial
- [x] Índices en `contexto/planes/README.md` y `contexto/README.md`

## Refuerzo opcional (hardware)

En la Zebra DS22, configurar **Country Keyboard / Host keyboard** igual al layout de Windows (Spanish / Latin America). La normalización en software cubre el caso aunque la pistola quede en US.
