# 06 — Roles/Permisos primero, luego Registro Externo (correo institucional)

> Complementa `01` (roles/permisos) y `02` (modelo de datos). Ajusta el campo `tipo_vinculo` de `persona` para que sea un catálogo dinámico en vez de un valor fijo, y añade la lógica de autorregistro externo.

## 0. Equivalencia de terminología institucional (resuelto)

Las dos listas de perfiles que se dieron en distintos momentos eran la misma lista, con nombres distintos:

| Término institucional | Nombre técnico interno |
|---|---|
| Gestor del conocimiento | Docente |
| Creador de oportunidades | Estudiante |
| Administrativo | Gestor administrativo |
| Graduado | Egresado |

Los **4 tipos de vínculo permiten autorregistro externo**: docente (gestor del conocimiento), estudiante (creador de oportunidades), administrativo, graduado. El catálogo `TipoVinculo` (sección 2) guarda ambos nombres — `codigo`/`nombre` con el término técnico, y un campo adicional `nombre_institucional` para mostrar el término que usa la universidad en el formulario público.

## 1. Regla de secuencia (la que marcaste como crítica)

El orden de construcción **no es negociable** en este módulo:

1. **Rol** y **Permiso** deben existir y estar cargados (fixture/migración de datos) — ya definido en `01`.
2. **TipoVinculo** (catálogo nuevo, ver sección 2) debe existir y estar configurado — define qué perfiles pueden autorregistrarse y con qué dominio de correo.
3. Solo entonces se habilita el endpoint/vista de **registro externo**.

Si el registro externo se construye antes que el catálogo de roles/tipos de vínculo, no hay a qué rol asignar al usuario nuevo ni qué regla de correo aplicar — quedaría hardcodeado, justo lo que se quiere evitar.

## 2. Cambio al modelo de datos: `tipo_vinculo` pasa a ser catálogo dinámico

En `02` el campo `persona.tipo_vinculo` era un `CHECK` con valores fijos. Se reemplaza por una tabla, para que el administrador controle todo desde el panel sin despliegues de código.

### 2.1 Nueva tabla `tipo_vinculo`

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| id | BIGSERIAL | PK | Identificador interno |
| codigo | VARCHAR(30) | UNIQUE, NOT NULL | ej. `docente`, `administrativo`, `gestor_conocimiento`, `creador_oportunidades`, `graduado`, `estudiante` |
| nombre | VARCHAR(80) | NOT NULL | Nombre legible |
| permite_autoregistro | BOOLEAN | DEFAULT false | Si un externo puede crear su cuenta eligiendo este tipo |
| dominio_correo_requerido | VARCHAR(50) | NULLABLE | ej. `@ucundinamarca.edu.co`; si es NULL, no se exige dominio específico |
| rol_asignado_id | BIGINT | FK → rol.id, NULLABLE | Rol que se asigna automáticamente al autorregistrarse con este tipo (evita que el usuario elija su propio rol) |
| activo | BOOLEAN | DEFAULT true | Borrado lógico |
| created_at | TIMESTAMP | DEFAULT now() | Auditoría |
| updated_at | TIMESTAMP | DEFAULT now() | Auditoría |

### 2.2 Ajuste a `persona` (de `02`)

| Campo | Cambio |
|---|---|
| tipo_vinculo | Se elimina el `CHECK`. Pasa a `tipo_vinculo_id BIGINT FK → tipo_vinculo.id, NOT NULL` |

### 2.3 Carga inicial recomendada (fixture)

| codigo | permite_autoregistro | dominio_correo_requerido | rol_asignado |
|---|---|---|---|
| docente | false | — | miembro_comunidad |
| administrativo | true (a confirmar) | @ucundinamarca.edu.co | miembro_comunidad |
| gestor_conocimiento | true | @ucundinamarca.edu.co | miembro_comunidad |
| creador_oportunidades | true (a confirmar) | @ucundinamarca.edu.co | miembro_comunidad |
| graduado | true | @ucundinamarca.edu.co | miembro_comunidad |
| estudiante | a confirmar | @ucundinamarca.edu.co | miembro_comunidad |

Los marcados "a confirmar" son justamente los que la lista ambigua de la sección 0 no resuelve — se cargan con el valor que definas y se pueden cambiar después sin tocar código, desde el panel admin.

## 3. Lógica de negocio del registro externo

### 3.1 Flujo

1. La persona entra a una vista **pública** `/registro` (sin autenticación).
2. El formulario muestra únicamente los `TipoVinculo` con `permite_autoregistro = true` y `activo = true` (carga dinámica desde la base de datos, nunca hardcodeada en el template).
3. Persona completa: tipo de vínculo (select), tipo y número de documento, nombres, apellidos, correo institucional, contraseña.
4. **Validación de dominio de correo:** si el `TipoVinculo` elegido tiene `dominio_correo_requerido` definido, el correo ingresado debe terminar exactamente en ese dominio (ej. `@ucundinamarca.edu.co`). Si no coincide, se rechaza con mensaje claro ("Debes usar tu correo institucional @ucundinamarca.edu.co").
5. **Validaciones adicionales:**
   - Documento único (no debe existir ya en `persona`).
   - Correo único (no debe existir ya en `usuario`).
   - Contraseña con política mínima (longitud, no igual al documento).
6. Al validarse correctamente, el sistema crea en una sola transacción:
   - Un registro en `persona` (con el `tipo_vinculo_id` elegido).
   - Un registro en `usuario` vinculado (1:1) a esa persona, con `username = correo`.
   - Una asignación en `usuario_rol` con el `rol_asignado_id` que trae el `TipoVinculo` (el usuario **nunca elige su propio rol**, ese campo ni siquiera se muestra en el formulario público).
7. **Recomendado (fuera del bloqueo estricto del MVP, pero de bajo costo):** enviar un correo de verificación al correo institucional antes de activar la cuenta (`persona.activo = false` hasta confirmar). Esto evita registros con correos mal escritos o de personas que no controlan esa casilla.

### 3.2 Qué NO debe pasar (reglas de seguridad)

- Un formulario de registro externo **nunca** debe listar roles administrativos (`admin_sistema`, `celador`) como opción — esos usuarios se crean únicamente desde el panel interno.
- El dominio de correo se valida **en el backend**, nunca solo en el frontend (un `required pattern` de HTML no es suficiente).
- Si `dominio_correo_requerido` está vacío para un tipo de vínculo, se documenta explícitamente como una decisión consciente (ej. para un tipo de vínculo externo a la universidad), no como un descuido.

## 4. Lo que debe ser configurable desde el panel de administrador

Esta es la parte "completamente dinámica" que pediste:

| Qué configura el admin | Dónde |
|---|---|
| Qué tipos de vínculo existen | CRUD sobre `TipoVinculo` |
| Si un tipo de vínculo permite autorregistro | Toggle `permite_autoregistro` en el mismo CRUD |
| Qué dominio de correo exige cada tipo | Campo `dominio_correo_requerido` editable |
| Qué rol se asigna automáticamente al autorregistrarse | Selector `rol_asignado_id` (de la lista de `Rol` ya existente) |
| Activar/desactivar un tipo de vínculo por completo | Toggle `activo` |

Ningún valor de estos debe quedar escrito en el código de las vistas (nada de `if tipo == "graduado"` en Python) — todo se resuelve consultando la tabla `TipoVinculo` en tiempo de ejecución.

## 5. Vistas nuevas a construir

| Vista | Tipo | Descripción |
|---|---|---|
| `/registro` | Pública | Formulario de autorregistro externo (sección 3.1) |
| `/admin/tipos-vinculo` | Interna (permiso `catalogos.administrar`) | CRUD de `TipoVinculo` con los toggles de la sección 4 |
| `/admin/solicitudes-registro` | Interna (opcional, si se activa verificación por correo) | Listado de cuentas pendientes de verificación |

## 6. Ajuste al plan de implementación (`03`)

Este módulo se inserta **entre la Fase 2 (`accounts`) y la Fase 3 (`personas`)** del plan original:

- **Fase 2.5 — Catálogo `TipoVinculo` y registro externo:**
  1. Crear modelo `TipoVinculo`, migrar y cargar el fixture inicial (sección 2.3).
  2. Actualizar `Persona` para usar `tipo_vinculo_id` en vez del `CHECK` fijo.
  3. Construir la vista pública `/registro` con validación de dominio de correo en backend.
  4. Construir el CRUD admin de `TipoVinculo`.
  5. (Opcional) Verificación de correo antes de activar la cuenta.

Esto respeta exactamente la secuencia que marcaste: roles/permisos (Fase 2) → catálogo de tipos de vínculo → recién ahí, registro externo.

## 7. Checklist antes de activar el registro externo en producción

- [ ] `Rol` y `Permiso` cargados y verificados (Fase 2 completa).
- [ ] `TipoVinculo` cargado con la lista definitiva confirmada por ti (resolviendo la discrepancia de la sección 0).
- [ ] Validación de dominio de correo probada con casos negativos (correo de Gmail, correo institucional mal escrito, dominio parcial).
- [ ] Ningún tipo de vínculo con rol administrativo tiene `permite_autoregistro = true`.
- [ ] Documento y correo con restricción `UNIQUE` a nivel de base de datos, no solo de formulario.