# Normalizar lectura QR de pistola Zebra DS22

**Estado:** Completado  
**Fecha:** 2026-09-19

## Problema

En portería, la Zebra DS22 (modo teclado HID) tipifica caracteres distintos cuando el layout del escáner es US y el del SO es español:

| Carácter en el QR | Lo que tipifica la pistola |
|-------------------|----------------------------|
| `-` | `'` |
| `:` | `ñ` / `Ñ` |

### Caso UUID legado

Ejemplo leído: `ea6bbf3c'e51a'418e'a23c'b4702b96f450`  
Esperado: `ea6bbf3c-e51a-418e-a23c-b4702b96f450`

### Caso token de exhibición firmado (actual)

El QR de pantalla codifica `TimestampSigner`: `{uuid}:{timestamp}:{firma}`.

Ejemplo leído:

```text
62938F98'F9F6'4ED7'8DF9'A73FC7D6F1A9ñ1X857Jñs7'51PY69Mf8jaRTUslPrhT5LrOWDINoTBe8JUzvD1K
```

Esperado:

```text
62938f98-f9f6-4ed7-8df9-a73fc7d6f1a9:1X857J:s7-51PY69Mf8jaRTUslPrhT5LrOWDINoTBe8JUzvD1K
```

Sin normalizar `ñ`→`:`, `unsign` falla (`BadSignature`) → **QR NO RECONOCIDO**. Si el UUID llega en mayúsculas, la firma HMAC también falla.

Además, la pistola puede alterar letras de timestamp/firma (base64). Aunque los separadores queden bien, `unsign` sigue en `BadSignature`. En ese caso se resuelve por el **UUID del primer segmento** (mismo nivel que el UUID legado ya aceptado).

## Solución

Normalización en servidor antes de resolver el equipo (`normalizar_codigo_escaneado`):

1. Strip de espacios y CR/LF del Enter de la pistola.
2. Sustitución `'` → `-`.
3. Sustitución `ñ` / `Ñ` → `:`.
4. En tokens firmados (`uuid:ts:firma`), pasar a minúsculas solo el primer segmento (UUID); no tocar timestamp ni firma (base64 case-sensitive).
5. Si tras limpiar hay 32 hex, reconstruir UUID canónico.

Resolución (`Equipo.resolver_token_escaneado`):

6. Si `unsign` falla (`BadSignature` / `SignatureExpired`), intentar UUID del primer segmento antes de serial.

Archivos:

- `apps/control_acceso/utils.py` — `normalizar_codigo_escaneado`
- `apps/control_acceso/views.py` — uso en `escanear_qr_salida`
- `apps/equipos/models.py` — fallback UUID del primer segmento
- `apps/control_acceso/tests.py` — apostrofos, hex, serial, `ñ`/`'`, firma corrupta

## Checklist

- [x] Helper `normalizar_codigo_escaneado`
- [x] Cablear en `escanear_qr_salida`
- [x] Tests de apostrofos, hex sin separadores y serial
- [x] Ampliar normalización: `ñ`/`Ñ` → `:` y lowercase del UUID en token firmado
- [x] Tests token firmado corrupto por Zebra (`'` + `ñ`, UUID mayúsculas)
- [x] Fallback UUID tras BadSignature / SignatureExpired (firma corrupta por HID)
- [x] Índices en `contexto/planes/README.md` y `contexto/README.md`

## Refuerzo opcional (hardware)

En la Zebra DS22, configurar **Country Keyboard / Host keyboard** igual al layout de Windows (Spanish / Latin America). La normalización en software cubre el caso aunque la pistola quede en US.
