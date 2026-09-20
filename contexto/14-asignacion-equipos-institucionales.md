# 14 — Asignación de Equipos Institucionales por Dependencia

**Formato:** plan estructurado para Cursor — sin código, solo especificación accionable paso a paso.
**Depende de:** `contexto-completo-sistema.md` (canónico), `02` (modelo de datos), `07` (panel interno), `09` (diseño kiosco).

---

## 1. Objetivo del feature

Hoy, todo equipo se registra desde "Mis equipos" por la propia persona, sin distinguir quién tiene autoridad para declarar un equipo como institucional. Este feature cambia eso:

- **Una Facultad, un Programa o un Área (dependencia)** es quien asigna un equipo institucional a una persona — la persona nunca se autoasigna un equipo institucional.
- **Al salir por portería**, si el equipo es institucional, el kiosco debe mostrarlo con una señal distinta a la del semáforo ok/alerta normal, para que el celador (o el admin que opera el kiosco hoy) le dé la atención adicional que un activo institucional merece.

---

## 2. Regla de negocio central (no negociable)

> **Una persona nunca puede registrar o marcar un equipo propio como `institucional`. Solo una dependencia (Facultad, Programa o Área), a través de un usuario responsable de esa dependencia, puede crear y asignar un equipo institucional a una persona.**

De aquí se derivan las reglas concretas:

| # | Regla |
|---|---|
| R1 | El flujo de autoregistro de equipos (`Mis equipos → Registrar`) **elimina la opción `institucional`** del selector de propiedad — solo permite `personal`. |
| R2 | Un equipo `institucional` **solo puede crearse** desde el nuevo flujo de asignación por dependencia (sección 4). |
| R3 | Un usuario responsable de una dependencia **solo puede asignar equipos a personas que pertenezcan a esa dependencia** (su Facultad, su Programa, o su Área) — nunca a personas de otra unidad, salvo `admin_sistema`. |
| R4 | Solo la dependencia asignadora (o `admin_sistema`) puede **reasignar o dar de baja** un equipo institucional — el dueño (persona) no puede inactivarlo ni editarlo por su cuenta. |
| R5 | Backend valida R1–R4 **en el servidor**, no solo ocultando opciones en el formulario — un intento directo a la API/endpoint con `propiedad=institucional` desde el flujo de autoregistro debe rechazarse igual. |

---

## 3. Cambios al modelo de datos

### 3.1 Nueva tabla: `responsable_dependencia`

Define qué usuario puede asignar equipos en nombre de qué unidad organizacional.

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| id | BIGSERIAL | PK | |
| usuario_id | BIGINT | FK → usuario.id, NOT NULL | Usuario responsable |
| unidad_tipo | VARCHAR(20) | CHECK IN ('facultad','programa','area') | Tipo de unidad que administra |
| unidad_id | BIGINT | NOT NULL | ID de la Facultad, Programa o Área (según `unidad_tipo`) |
| activo | BOOLEAN | DEFAULT true | Borrado lógico |
| created_at | TIMESTAMP | DEFAULT now() | Auditoría |

Un mismo usuario puede tener varias filas (ej. responsable de dos programas). `admin_sistema` no necesita filas aquí — su permiso ya es global.

### 3.2 Ajustes a `equipo` (definida en `02`)

| Campo nuevo | Tipo | Descripción |
|---|---|---|
| unidad_tipo | VARCHAR(20) | NULLABLE; CHECK IN ('facultad','programa','area'); solo se llena si `propiedad = 'institucional'` |
| unidad_id | BIGINT | NULLABLE; ID de la unidad responsable (Facultad, Programa o Área) |
| asignado_por_usuario_id | BIGINT | FK → usuario.id, NULLABLE; quién hizo la asignación |
| fecha_asignacion | TIMESTAMP | NULLABLE; cuándo se asignó |

**Restricción de integridad a nivel de aplicación:** si `propiedad = 'personal'`, los 4 campos anteriores deben quedar `NULL`. Si `propiedad = 'institucional'`, los 4 campos son obligatorios.

---

## 4. Flujo funcional: asignar un equipo institucional

1. Un usuario con permiso `equipos.asignar_institucional` entra a `/panel/equipos/asignar-institucional/`.
2. El sistema resuelve, vía `responsable_dependencia`, a qué unidad(es) representa ese usuario. Si administra más de una, elige en un selector; si es `admin_sistema`, puede elegir cualquier unidad del sistema.
3. Busca la **Persona destino** (por documento). El buscador **solo devuelve personas que pertenecen a la unidad seleccionada** (ej. si es responsable del Programa de Ingeniería de Sistemas, solo aparecen personas de ese programa).
4. Completa los datos del equipo: marca, modelo, serial, tipo.
5. El sistema crea el `Equipo` con:
   - `propiedad = 'institucional'`
   - `persona_id` = persona destino
   - `unidad_tipo` / `unidad_id` = la unidad del usuario que asigna
   - `asignado_por_usuario_id` = usuario actual
   - `token_qr` generado igual que en el flujo normal
6. La persona ve el equipo en "Mis equipos", **marcado visualmente como institucional** (badge turquesa `--color-info`, coherente con `05`/`09`), sin botones de "editar" ni "dar de baja" — solo puede mostrar su QR.

### 4.1 Reasignar o dar de baja

- `/panel/equipos/<id>/reasignar/`: cambia la `persona_id` dueña, manteniendo `unidad_tipo`/`unidad_id`. Solo accesible por el responsable de esa unidad o `admin_sistema`.
- `/panel/equipos/<id>/dar-de-baja/` (ya existente para equipos personales en general): para institucionales, el mismo endpoint valida que quien lo ejecuta sea responsable de la unidad correspondiente.

---

## 5. Kiosco: señal diferenciada para equipo institucional

Esto es aparte del semáforo ok/alerta/no_encontrado ya definido — es una **capa adicional de información**, no un cuarto estado de `Movimiento.resultado`.

### 5.1 Comportamiento visual

| Situación | Qué ve el celador |
|---|---|
| Equipo **personal**, resultado `ok` | Pantalla verde estándar, sin cambios respecto al diseño actual |
| Equipo **institucional**, resultado `ok` | Pantalla verde + **badge turquesa "🏫 Equipo institucional — [Nombre de la unidad]"** visible junto al nombre de la persona |
| Equipo **institucional**, resultado `alerta` | Pantalla roja + mensaje reforzado: **"Alerta — Equipo institucional de [Unidad]"**, para que quede claro que la anomalía involucra un activo institucional, no uno personal |
| Equipo **personal**, resultado `alerta` | Pantalla roja estándar, sin el badge institucional |

### 5.2 Por qué es una capa aparte y no un nuevo `resultado`

`Movimiento.resultado` sigue siendo `ok` / `alerta` / `no_encontrado` — eso no cambia, porque esos valores describen si la verificación fue exitosa. Si a un equipo institucional en `ok` se le diera su propio valor de `resultado`, se perdería la semántica simple de "coincide o no coincide". En vez de eso, el dato `equipo.propiedad == 'institucional'` se resuelve en la misma consulta que arma la pantalla del kiosco y se muestra como un elemento visual adicional.

### 5.3 Ajuste al dashboard (`13`) y reportes (`12`) — opcional, no bloqueante

- Dashboard: tarjeta opcional "Alertas en equipos institucionales" (subconjunto de la tarjeta de alertas general), útil porque son el activo de mayor valor a proteger — justamente el problema original que motivó todo el sistema.
- Reporte de Alertas (`12`): columna adicional `¿Institucional?` + filtro para aislar solo alertas de equipos institucionales.

---

## 6. Permisos nuevos

| Código | Descripción |
|---|---|
| `equipos.asignar_institucional` | Asignar, reasignar o dar de baja equipos institucionales, limitado a las unidades donde el usuario es responsable (`responsable_dependencia`) |
| `equipos.gestionar_responsables` | CRUD de la tabla `responsable_dependencia` — quién administra qué unidad. Reservado a `admin_sistema` en el MVP de este feature. |

---

## 7. Vistas y rutas

| Ruta | Permiso | Descripción |
|---|---|---|
| `/panel/equipos/asignar-institucional/` | `equipos.asignar_institucional` | Formulario de asignación (sección 4) |
| `/panel/equipos/institucionales/` | `equipos.asignar_institucional` (filtrado a su unidad) o `equipos.ver_todos` (global) | Listado de equipos institucionales bajo su alcance |
| `/panel/equipos/<id>/reasignar/` | `equipos.asignar_institucional` (validando unidad) | Cambiar el dueño de un equipo institucional |
| `/panel/responsables-dependencia/` | `equipos.gestionar_responsables` | CRUD de qué usuario administra qué Facultad/Programa/Área |

---

## 8. Validaciones críticas a implementar (checklist de backend)

- [ ] El endpoint de autoregistro de equipos rechaza `propiedad = 'institucional'` aunque se envíe manualmente en la petición (no solo se oculta en el formulario).
- [ ] Al asignar, el sistema verifica que la persona destino pertenezca a la unidad del usuario asignador (comparando `persona.programa_id`/`persona.area_id`/facultad derivada, según `unidad_tipo`).
- [ ] Un usuario sin fila en `responsable_dependencia` (y sin `admin_sistema`) no puede acceder a `/panel/equipos/asignar-institucional/` aunque tenga el permiso base — se valida además que tenga al menos una unidad asignada.
- [ ] La persona dueña de un equipo institucional no ve botones de edición/baja en "Mis equipos" para ese equipo específico (verificado también en el backend del endpoint de edición, no solo ocultando el botón).
- [ ] El kiosco muestra el badge institucional en el 100% de los escaneos donde `equipo.propiedad = 'institucional'`, en `ok` y en `alerta`.

---

## 9. Plan de implementación (para Cursor, paso a paso)

1. **Modelo de datos:** crear `ResponsableDependencia` y los 4 campos nuevos en `Equipo` (sección 3). Migración.
2. **Backend — bloqueo de autoasignación:** modificar el formulario/endpoint de autoregistro de equipos para rechazar `institucional` (R1, R5).
3. **Backend — flujo de asignación:** construir `/panel/equipos/asignar-institucional/`, con la validación de alcance por unidad (R3) y el buscador de personas filtrado.
4. **Backend — reasignar/dar de baja:** ajustar el endpoint existente de baja para validar responsabilidad de unidad quando el equipo es institucional (R4).
5. **Frontend — "Mis equipos":** ocultar acciones de edición/baja para equipos con `propiedad = 'institucional'`, mostrar badge turquesa con el nombre de la unidad.
6. **Frontend — kiosco:** agregar el badge institucional en la pantalla de resultado (`ok` y `alerta`), sin tocar la lógica del semáforo existente.
7. **Permisos:** cargar `equipos.asignar_institucional` y `equipos.gestionar_responsables` en el seed, junto con el nuevo rol `responsable_dependencia` (con `equipos.asignar_institucional` asignado por defecto).
8. **Panel de responsables:** CRUD simple de `responsable_dependencia` para que `admin_sistema` designe quién administra cada unidad.
9. **(Opcional) Dashboard/Reportes:** agregar el filtro/tarjeta de alertas institucionales (sección 5.3).

---

## 10. Decisiones confirmadas (antes eran preguntas abiertas)

- **Rol nuevo `responsable_dependencia`**, cargado en el seed junto con los demás roles y permisos (`accounts/management/commands/seed_data.py`), con el permiso `equipos.asignar_institucional` asignado por defecto. No hereda el resto de permisos de `admin_sistema` — así un decano o director de programa puede asignar equipos institucionales de su unidad sin tener acceso a roles, usuarios ni catálogos globales.
- **Una persona puede tener equipos institucionales de más de una unidad a la vez** (ej. uno de su Programa y otro de un Área administrativa por una función adicional) — queda confirmado como regla de negocio explícita. El modelo de la sección 3 ya lo soporta sin cambios: cada `Equipo` institucional lleva su propia `unidad_tipo`/`unidad_id`, independiente de los demás equipos de la misma persona.
