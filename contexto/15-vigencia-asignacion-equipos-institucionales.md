# 15 — Inventario y Vigencia de Equipos Institucionales

**Formato:** plan estructurado para Cursor, sin código. Reemplaza la versión anterior de este documento (que solo cubría vigencia) y ajusta partes de `14`.

**Motivo:** dos correcciones a la lógica de negocio original de `14`:
1. Una asignación institucional **no es indefinida** — necesita `fecha_inicio`/`fecha_fin`, y el kiosco debe alertar si venció.
2. **Crear** un equipo institucional y **asignarlo** a una persona son dos acciones distintas, hechas por permisos distintos, en momentos distintos — no un solo paso como se planteó inicialmente en `14`.

---

## 0. La lógica correcta (idea central)

Separar completamente dos operaciones que antes estaban mezcladas en un solo formulario:

1. **Alta de inventario** — un usuario con permiso de inventario registra un equipo como institucional, indicando de qué dependencia (Facultad, Programa o Área) es propiedad. **No se elige ninguna persona en este paso.** El equipo queda "disponible" en el inventario de esa unidad.
2. **Asignación** — en un momento posterior (y las veces que haga falta a lo largo de la vida del equipo), alguien con permiso de asignación toma un equipo `disponible` y lo entrega a una persona concreta, con `fecha_inicio`/`fecha_fin`.

Esto refleja mejor la realidad: la universidad registra un equipo primero (al comprarlo o inventariarlo), y decide después a quién se lo presta. El mismo equipo puede pasar por varias personas a lo largo de su vida útil, con periodos en los que simplemente está guardado sin asignar — el modelo debe soportar eso sin fricción.

**Y sigue intacta la regla de `14`:** una persona nunca se autoasigna un equipo institucional. El autoregistro (`equipos.registrar`) sigue existiendo exactamente igual, solo para equipos `personales`.

---

## 1. Modelo de datos

### 1.1 `Equipo` (ajustes sobre `02`)

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| persona_id | BIGINT | FK → persona.id, **NULLABLE** | Dueño/usuario actual. `NULL` si el equipo institucional está en inventario sin asignar. Para equipos `personales` sigue siendo obligatorio. |
| propiedad | VARCHAR(20) | CHECK IN ('personal','institucional') | Sin cambios respecto a `02` |
| unidad_tipo | VARCHAR(20) | CHECK IN ('facultad','programa','area'), NULLABLE | Unidad **propietaria permanente** del equipo — no cambia aunque el equipo pase de persona en persona. Obligatorio si `propiedad='institucional'`; siempre `NULL` si es personal |
| unidad_id | BIGINT | NULLABLE | Igual que arriba |
| estado_inventario | VARCHAR(20) | CHECK IN ('disponible','asignado','de_baja'), NULLABLE | Solo aplica a institucionales. `disponible` = en la dependencia, sin persona; `asignado` = tiene una `AsignacionEquipo` activa; `de_baja` = fuera de servicio |
| creado_por_usuario_id | BIGINT | FK → usuario.id, NULLABLE | Quién dio de alta el equipo en el inventario (puede ser distinto de quién luego lo asigna) |

### 1.2 `AsignacionEquipo` (nueva tabla — historial de asignaciones)

La unidad propietaria vive en `Equipo` (no se repite aquí, porque no cambia entre asignaciones — solo cambia la persona que lo usa):

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| id | BIGSERIAL | PK | |
| equipo_id | BIGINT | FK → equipo.id, NOT NULL | |
| persona_id | BIGINT | FK → persona.id, NOT NULL | Quién tuvo el equipo durante este periodo |
| fecha_inicio | DATE | NOT NULL | Desde cuándo es válida esta asignación |
| fecha_fin | DATE | NOT NULL | Hasta cuándo — **obligatoria, nunca indefinida** |
| estado | VARCHAR(20) | CHECK IN ('activa','finalizada','revocada'), DEFAULT 'activa' | |
| asignado_por_usuario_id | BIGINT | FK → usuario.id, NOT NULL | Quién ejecutó la asignación |
| created_at | TIMESTAMP | DEFAULT now() | |

**Reglas de integridad:**
- `fecha_fin >= fecha_inicio` (validado en backend).
- Solo una fila por `equipo_id` puede tener `estado='activa'` a la vez.
- Nunca se edita `fecha_fin` de una fila ya cerrada — cerrar y crear una nueva fila.

### 1.3 `Movimiento` (ajuste sobre `02`/`12`/`13`)

| Campo nuevo | Tipo | Descripción |
|---|---|---|
| motivo_alerta | VARCHAR(40) | NULLABLE; valores: `equipo_inactivo`, `persona_inactiva`, `no_coincide`, `asignacion_vencida`, `asignacion_no_vigente`, `sin_asignacion_activa` |

Permite que el Reporte de Alertas (`12`) y el dashboard (`13`) desglosen **por qué** se generó cada alerta, no solo que hubo una.

---

## 2. Permisos (dos permisos separados, no uno solo)

| Código | Qué permite | Rol que lo tiene por defecto |
|---|---|---|
| `equipos.inventario_institucional` | **Crear** equipos institucionales para una dependencia, sin asignarlos a nadie; editar sus datos; darlos de baja del inventario | `responsable_dependencia` |
| `equipos.asignar_institucional` | **Asignar** un equipo `disponible` a una persona con vigencia; renovar, reasignar, devolver al inventario | `responsable_dependencia` |
| `equipos.registrar` | Sin cambios — autoregistro de equipo **personal** por la propia persona | `miembro_comunidad` |

**Por qué van separados aunque el mismo rol tenga ambos en el MVP:** una universidad más grande podría querer que quien da de alta el inventario (compras/almacén) no sea quien decide a quién se le presta cada equipo. Separar los permisos deja esa puerta abierta sin forzarla ahora.

**Independencia total de `equipos.registrar`:** este es el punto que no debe romperse — una persona (docente, estudiante, etc.) sigue registrando su propio equipo personal exactamente igual que siempre. Los permisos de inventario/asignación institucional son exclusivos de quien administra una dependencia y nunca se mezclan con el flujo de autoregistro.

---

## 3. Flujo 1: Alta de inventario (nuevo, separado de la asignación)

1. Usuario con `equipos.inventario_institucional` entra a `/panel/equipos/institucionales/nuevo/`.
2. El sistema resuelve (vía `responsable_dependencia`, definida en `14`) qué unidad(es) puede usar; si administra varias, elige una.
3. Completa marca, modelo, serial, tipo. **No hay campo de persona en este formulario.**
4. El sistema crea el `Equipo` con `propiedad='institucional'`, `unidad_tipo`/`unidad_id` = la unidad elegida, `persona_id = NULL`, `estado_inventario = 'disponible'`, `creado_por_usuario_id` = usuario actual.

> Un equipo `disponible` sin persona no tiene quién le muestre el QR en portería — eso es esperado. Mientras está en inventario es solo un registro administrativo; el QR cobra sentido operativo únicamente cuando alguien lo tiene asignado.

---

## 4. Flujo 2: Asignación (con vigencia obligatoria)

1. Usuario con `equipos.asignar_institucional` entra a `/panel/equipos/institucionales/` y filtra por `estado_inventario = 'disponible'` dentro de su unidad.
2. Elige un equipo disponible y busca la persona destino — **solo puede asignar a personas de su propia unidad** (misma validación de alcance de `14`).
3. Define `fecha_inicio` (por defecto hoy) y `fecha_fin` (obligatoria; puede sugerirse según el tipo de vínculo de la persona — ej. fin de semestre para estudiante/creador de oportunidades — pero siempre editable).
4. El sistema crea la `AsignacionEquipo` (`estado='activa'`) y actualiza `Equipo.persona_id` = esa persona, `Equipo.estado_inventario = 'asignado'`.

### 4.1 Devolver al inventario (distinto de reasignar)

Cuando la persona deja de necesitar el equipo y **no** se entrega de inmediato a otra persona (ej. un estudiante se gradúa):

- Se cierra la `AsignacionEquipo` activa (`estado='finalizada'`).
- `Equipo.persona_id` vuelve a `NULL`, `estado_inventario` vuelve a `'disponible'`.
- El equipo queda listo para una futura asignación sin pasar por otra persona intermedia.

### 4.2 Reasignar (a otra persona directamente)

Cierra la asignación activa (`'finalizada'` si venció naturalmente, `'revocada'` si se corta antes de tiempo) y crea una nueva `AsignacionEquipo` con otra persona, sin pasar por el estado `disponible` intermedio.

### 4.3 Renovar (misma persona, nuevas fechas)

Igual que reasignar, pero con la misma `persona_id` — típicamente cuando alguien continúa con el equipo un periodo más (ej. estudiante que sigue matriculado).

---

## 5. Kiosco: validación de vigencia y del estado de inventario

Se suma a la validación ya existente (equipo activo, persona activa, coincidencia) y al badge institucional de `14`:

1. ¿El equipo está activo? → si no, `alerta` / `motivo_alerta='equipo_inactivo'`.
2. ¿La persona está activa? → si no, `alerta` / `motivo_alerta='persona_inactiva'`.
3. Si el equipo es institucional:
   - ¿`estado_inventario = 'disponible'` (sin asignación, no debería estar circulando)? → `alerta` / `motivo_alerta='sin_asignacion_activa'` (caso límite defensivo, no debería ocurrir en la práctica).
   - ¿Existe una `AsignacionEquipo` activa cuyo rango `[fecha_inicio, fecha_fin]` incluya hoy? → `ok` + badge institucional.
   - ¿La asignación activa tiene `fecha_fin < hoy`? → `alerta` / `motivo_alerta='asignacion_vencida'`, mensaje: *"Asignación institucional vencida — contactar a [Unidad]"*.
   - ¿Hoy es anterior a `fecha_inicio`? → `alerta` / `motivo_alerta='asignacion_no_vigente'`, mensaje: *"Asignación institucional no vigente todavía"*.

**Por qué no es un cuarto valor de `Movimiento.resultado`:** el resultado sigue siendo solo `ok`/`alerta`/`no_encontrado` (simplicidad del semáforo); `motivo_alerta` es el detalle de *por qué*, útil para reportes y para el mensaje en pantalla, sin complicar la lógica principal del kiosco.

---

## 6. Vista de alerta temprana para las dependencias (recomendado, no bloqueante)

En `/panel/equipos/institucionales/`, agregar un indicador de **"por vencer en los próximos 15 días"**, para que la unidad se anticipe (renueve, reasigne o devuelva al inventario) antes de que el equipo empiece a generar alertas reales en portería.

---

## 7. Validaciones críticas (checklist de backend)

- [x] Un usuario con `equipos.inventario_institucional` pero sin `equipos.asignar_institucional` puede crear equipos institucionales pero no asignarlos a nadie.
- [x] Un equipo institucional recién creado queda con `persona_id = NULL` y `estado_inventario = 'disponible'`.
- [x] La vista de asignación solo permite elegir equipos en estado `disponible`, dentro de la unidad del usuario.
- [x] "Devolver al inventario", "Reasignar" y "Renovar" son tres acciones distintas y claramente etiquetadas — nunca se confunden en la interfaz.
- [x] Ninguna `AsignacionEquipo` se crea sin `fecha_inicio`/`fecha_fin`; `fecha_fin >= fecha_inicio` validado en backend.
- [x] Solo una `AsignacionEquipo` por equipo puede estar `activa` a la vez.
- [x] El autoregistro de equipo personal (`equipos.registrar`) no se ve afectado en absoluto por este cambio.
- [x] El kiosco evalúa la vigencia y el estado de inventario en tiempo real en cada escaneo (no depende de un job programado).
- [x] `Movimiento.motivo_alerta` se completa correctamente en los 6 casos posibles.

---

## 8. Plan de implementación (para Cursor, paso a paso)

1. **Modelo de datos:** agregar a `Equipo` los campos `unidad_tipo`, `unidad_id`, `estado_inventario`, `creado_por_usuario_id`; hacer `persona_id` nullable. Crear `AsignacionEquipo`. Agregar `motivo_alerta` a `Movimiento`.
2. **Permisos:** cargar `equipos.inventario_institucional` y `equipos.asignar_institucional` por separado en el seed, ambos asignados al rol `responsable_dependencia`.
3. **Backend — alta de inventario:** construir `/panel/equipos/institucionales/nuevo/` (sección 3), sin campo de persona.
4. **Backend — asignación:** construir/ajustar `/panel/equipos/institucionales/` con filtro por `estado_inventario`, y el formulario de asignación con fechas obligatorias (sección 4).
5. **Backend — devolver/reasignar/renovar:** implementar las tres acciones como endpoints distintos (secciones 4.1–4.3).
6. **Backend — kiosco:** implementar la validación completa de la sección 5, incluido el llenado de `motivo_alerta`.
7. **Frontend — kiosco:** agregar los mensajes de alerta correspondientes a cada `motivo_alerta`, reutilizando el estilo rojo ya existente.
8. **Frontend — panel:** vista de inventario con badges de estado (`disponible`/`asignado`/`de_baja`) y el indicador de "por vencer" (sección 6).
9. **Reportes/Dashboard:** actualizar `12`/`13` para desglosar alertas por `motivo_alerta` y, opcionalmente, mostrar "equipos institucionales disponibles vs. asignados" como métrica adicional.
10. **Tarea programada:** implementar el job diario (sección 9.1.2) que cierra `AsignacionEquipo` vencidas y libera los equipos al inventario, independiente de si hay escaneos ese día.

---

## 9. Decisión confirmada: cierre automático de asignaciones vencidas

Cuando una `AsignacionEquipo` vence y nadie la renovó ni la devolvió manualmente, el sistema la cierra **automáticamente** (no queda esperando a que un humano actúe): la asignación pasa a `estado='finalizada'`, `Equipo.persona_id` vuelve a `NULL` y `estado_inventario` vuelve a `'disponible'` — el equipo queda listo para asignarse de nuevo, a la misma persona o a otra.

### 9.1 Dos mecanismos que hacen el cierre (se complementan)

1. **En el momento del escaneo (tiempo real):** si el kiosco detecta que la asignación activa tiene `fecha_fin < hoy`, el sistema la cierra automáticamente en ese mismo instante (regla del paso 3 de la sección 5), *antes* de registrar el resultado del movimiento. El `Movimiento` queda con `resultado='alerta'` y `motivo_alerta='asignacion_vencida'`, con el mensaje aclarando que la asignación **acaba de liberarse automáticamente** por vencimiento — no que "sigue vencida esperando acción".
2. **Tarea programada diaria (batch):** recorre todas las `AsignacionEquipo` con `estado='activa'` y `fecha_fin < hoy`, y las cierra de la misma forma. Esto es necesario porque un equipo vencido que nadie escanea (ej. quedó guardado, no volvió a salir) debe reflejarse como `disponible` en el inventario del panel **sin depender de que ocurra un escaneo** — de lo contrario, la unidad vería el equipo como "asignado" indefinidamente aunque ya venció.

### 9.2 Ajuste a la sección 5 (kiosco)

El paso "¿la asignación activa tiene `fecha_fin < hoy`?" ya no es solo una lectura — es un **disparador de cierre**: al detectarlo, el sistema ejecuta el cierre automático (9.1.1) y *después* genera la alerta. El resultado para el celador es el mismo (`alerta` / `asignacion_vencida`), pero el estado del equipo en la base de datos ya queda consistente (`disponible`) desde ese mismo escaneo, sin esperar al batch nocturno.

### 9.3 Checklist adicional

- [x] El escaneo de un equipo con asignación vencida cierra la `AsignacionEquipo` automáticamente antes de responder al kiosco.
- [x] Existe una tarea programada diaria que cierra asignaciones vencidas aunque el equipo no se escanee ese día.
- [x] Después del cierre automático (por cualquiera de los dos mecanismos), el equipo aparece como `disponible` en `/panel/equipos/institucionales/` sin intervención manual.
- [x] El cierre automático nunca borra el historial — la fila de `AsignacionEquipo` queda con `estado='finalizada'`, visible como parte del historial del equipo.