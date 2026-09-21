# 00 — Arquitectura General del Sistema

**Proyecto:** Sistema de Control de Ingreso/Salida de Equipos de Cómputo
**Tipo:** Monolito modular
**Base de datos:** PostgreSQL
**Backend/Frontend:** Django (templates + htmx para interacciones dinámicas sin separar frontend)
**Objetivo de esta fase:** MVP funcional en 1 semana, con base sólida para escalar (multi-sede, roles dinámicos, auditoría)

---

## 1. Filosofía de diseño

- **Monolito modular**, no microservicios: un solo despliegue, pero código organizado por dominios de negocio independientes (apps de Django). Esto da velocidad de desarrollo ahora y permite extraer un módulo a microservicio en el futuro si el crecimiento lo exige.
- **Roles y permisos dinámicos**: no se hardcodean roles en el código. Se modelan como datos (tablas `Rol`, `Permiso`) para que la universidad pueda crear nuevos roles sin tocar código.
- **Multi-sede desde el día 1**: aunque el MVP arranque en una sede, el modelo de datos ya soporta `Sede → Decanatura → Programa` para no rehacer el esquema después.
- **Buenas prácticas transversales**: timestamps de auditoría (`created_at`, `updated_at`), borrado lógico (`activo`) en vez de borrado físico, identificadores públicos (QR) separados de las llaves primarias internas, nomenclatura consistente en `snake_case`.

---

## 2. Estructura modular (apps de Django)

```
proyecto_control_equipos/
├── config/                     # settings, urls raíz, wsgi/asgi
├── apps/
│   ├── accounts/                # Usuario, Rol, Permiso, autenticación
│   ├── organizacion/             # Sede, Decanatura, Programa
│   ├── personas/                # Persona (comunidad académica) y su vínculo con organización
│   ├── equipos/                 # Equipo, generación de token/QR
│   ├── control_acceso/           # Movimiento (registro de salidas), pantalla de control
│   └── auditoria/                # (opcional fase 2) bitácora de cambios sensibles
├── templates/
├── static/
└── manage.py
```

### Responsabilidad de cada módulo

| App | Responsabilidad | Depende de |
|---|---|---|
| `accounts` | Login, `Usuario`, `Rol`, `Permiso`, asignación de roles a usuarios | — |
| `organizacion` | Catálogos institucionales: `Sede`, `Decanatura`, `Programa` | — |
| `personas` | Ficha de cada miembro de la comunidad académica y su vínculo con `organizacion` | `organizacion` |
| `equipos` | Registro de equipos por persona, generación de `token_qr` | `personas` |
| `control_acceso` | Pantalla de escaneo en portería, registro de `Movimiento`, resolución de alertas | `equipos`, `accounts` |
| `auditoria` | Registro de quién cambió qué y cuándo (fase 2, no bloquea el MVP) | todas |

Esta separación permite que, si mañana se decide manejar la lógica de `equipos` como microservicio aparte, el límite ya está claro en el código.

---

## 3. Flujo de trabajo recomendado con Antigravity

Los documentos `01`, `02` y `03` están pensados para alimentarse a Antigravity **en este orden**, uno por tarea:

1. `01-modelo-negocio-roles-permisos.md` → para que Antigravity entienda las reglas de negocio antes de tocar código.
2. `02-modelo-datos-diccionario.md` → para generar los modelos de Django (`models.py`) y las migraciones.
3. `03-plan-implementacion-paso-a-paso.md` → para ejecutar la construcción día a día, app por app.

Cada documento es autocontenido: se puede pegar en una tarea nueva de Antigravity sin necesitar el resto del historial de la conversación.

---

## 4. Stack técnico resumido

| Capa | Tecnología | Motivo |
|---|---|---|
| Lenguaje/Framework | Python + Django | Admin gratis, ORM maduro, auth integrada, ideal para monolito rápido |
| Base de datos | PostgreSQL | Relacional, soporta bien FKs múltiples (sede→decanatura→programa), UUIDs nativos |
| Frontend | Django templates + htmx | Evita levantar un frontend SPA separado; interacciones dinámicas (escaneo, alertas) sin JS pesado |
| QR | librería `qrcode` (Python) | Generación server-side desde `token_qr` |
| Despliegue | Render (Docker + Gunicorn) | Postgres + app monolito; Blueprint en `render.yaml`; guía en `contexto/operaciones/despliegue-render.md` |
