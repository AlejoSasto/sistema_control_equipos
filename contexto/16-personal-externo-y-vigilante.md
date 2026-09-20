# 16 — Personal externo y vigilante (lógica unificada)

**Formato:** plan estructurado para Cursor, sin código. Complementa `06` (registro / TipoVinculo), `14`/`15` (dependencias y vigencia) y el kiosco de control de salida.

**Motivo:** el personal externo (contratistas, proveedores, visitantes) y el vigilante de portería rompen supuestos del modelo actual: no usan correo institucional obligatorio, y el externo tiene una relación con fechas de caducidad naturales (visita), no un vínculo permanente como docente/estudiante.

---

## 0. Idea central

1. **Separar cuenta y visita** para `personal_externo` (simetría con “crear equipo” vs “asignar equipo” en `15`):
   - La cuenta (`Persona` + `Usuario`) se crea **una sola vez**.
   - Cada llegada genera un registro `VisitaExterno` con sede, dependencia y vigencia propias.
2. **Vigilante** es un `TipoVinculo` de **alta interna** (sin autorregistro), con correo libre y **una sola sede**.
3. En el kiosco, para externos se valida la visita (no se inactiva la Persona). Para cualquier vínculo, si la sede de la persona no coincide con la del vigilante, la salida sigue siendo `ok` con badge “Otra sede”.

**Decisiones cerradas**
- VisitaExterno: **autodeclaración** (sin aprobación de `responsable_dependencia`).
- Otra sede: salida **`ok`** + badge visible, **sin** confirmación extra del vigilante.
- Una visita = **una sede** (moverse entre sedes = visitas distintas).

---

## 1. Catálogo `TipoVinculo`

| codigo | Autoregistro | `dominio_correo_requerido` | `rol_asignado` | Quién lo crea |
|--------|--------------|----------------------------|----------------|---------------|
| 4 canónicos (`gestor_*`, `egresado`) | sí | `@ucundinamarca.edu.co` | `miembro_comunidad` | `/registro/` |
| `personal_externo` | **sí** | **NULL** (cualquier correo) | `miembro_comunidad` | `/registro/` |
| `vigilante` | **no** | **NULL** | rol `vigilante` | solo panel/admin interno |

- Rol `vigilante` activo con `control.escanear` y `control.ver_alertas` (reemplaza el legado `celador` inactivo).
- Si `dominio_correo_requerido` es NULL, el registro **no** exige dominio institucional.

---

## 2. Modelo `VisitaExterno`

No se agregan `fecha_inicio_vinculo` / `fecha_fin_vinculo` a `Persona` (solo aplican a un tipo).

| Campo | Tipo | Descripción |
|---|---|---|
| id | BIGSERIAL | PK |
| persona_id | FK → persona | Debe ser `tipo_vinculo=personal_externo` |
| sede_id | FK → sede | Destino de esta llegada |
| unidad_tipo | facultad \| programa \| area | Dependencia autodeclarada |
| unidad_id | BIGINT | |
| fecha_inicio / fecha_fin | DATE NOT NULL | Vigencia; `fecha_fin >= fecha_inicio` |
| estado | activa \| finalizada \| cancelada | Default `activa` |
| created_at | TIMESTAMP | |

**Integridad**
- Solo una visita `activa` por persona. Al crear otra, se finaliza la activa previa.
- Al vencer: cierre automático (escaneo + job diario). **La Persona no se inactiva.**

---

## 3. Flujos

### 3.1 Primera vez — `/registro/`

Con `tipo_vinculo=personal_externo`: datos personales + correo libre + sede destino + dependencia + fechas → crea Persona + Usuario + primera `VisitaExterno`.  
Si el documento ya existe como externo: no duplicar; indicar login + “Registrar nueva visita”.

### 3.2 Visitas siguientes

Usuario autenticado externo → pantalla “Registrar nueva visita” (sede / dependencia / fechas). Actualiza `Persona.sede` a la sede de la visita actual.

### 3.3 Vigilante — alta interna

Panel: Persona + Usuario con `tipo_vinculo=vigilante`, una sede, correo libre. No usa `VisitaExterno`. No aparece en `/registro/`.

### 3.4 Equipos del externo

- Portátil propio: `equipos.registrar` (personal).
- Equipo institucional prestado: flujo `15` (asignación con vigencia, idealmente alineada a la visita).

---

## 4. Kiosco

Tras validaciones de equipo / asignación institucional (`15`) y persona activa:

### 4.1 Personal externo

1. Cerrar visita vencida si `fecha_fin < hoy`.
2. Sin visita activa que cubra hoy → `motivo_alerta='sin_visita_activa'`.
3. Tras cierre por vencimiento → `motivo_alerta='visita_vencida'`.
4. Visita vigente → `ok` + badge `Visitante externo — [Dependencia], hasta [fecha]`.

### 4.2 Otra sede (todos los vínculos)

- Sede vigilante = `request.user.persona.sede`.
- Sede escaneado = `persona.sede`.
- Si distinta: `resultado=ok` + badge `Otra sede — [nombre]`. No es alerta. Se puede anotar en `Movimiento.observacion` / flag `otra_sede`.

### 4.3 Motivos nuevos en `Movimiento`

`visita_vencida`, `sin_visita_activa` (además de los de `15`).

---

## 5. Tarea programada

`cerrar_visitas_vencidas`: finaliza visitas `activa` con `fecha_fin < hoy` (espejo de `cerrar_asignaciones_vencidas`).

---

## 6. Validaciones críticas (checklist)

- [x] `personal_externo` y `vigilante` en seed; dominio NULL; vigilante sin autorregistro.
- [x] Rol `vigilante` activo; `celador` legado inactivo o migrado.
- [x] Registro externo crea Persona + Usuario + VisitaExterno; correo no institucional permitido.
- [x] Documento duplicado externo → hint de login, sin segunda cuenta.
- [x] Nueva visita cierra la activa previa; actualiza `Persona.sede`.
- [x] Kiosco: vigente / vencida / sin visita; badge externo; badge otra sede con `ok`.
- [x] Job diario cierra visitas vencidas sin inactivar Persona.
- [x] Alta interna de vigilante con una sola sede.

---

## 7. Fuera de alcance

- Aprobación de visitas por dependencia.
- Confirmación extra en kiosco por otra sede.
- Multi-sede en una sola `VisitaExterno`.
- Inactivar Persona al vencer visita.
