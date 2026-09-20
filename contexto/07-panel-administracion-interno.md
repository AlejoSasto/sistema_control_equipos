# 07 — Panel de Administración Interno (Personas, Usuarios, Roles, Permisos)

> Complementa `01`, `02`, `03` y `06`. Django Admin queda reservado para uso técnico/soporte del equipo de desarrollo; este documento define el **panel propio**, dentro de la aplicación, con el sistema de diseño de `05`, para que el administrador funcional de la universidad gestione todo sin tocar `/admin/`.

## 1. Por qué un panel propio y no solo Django Admin

Django Admin es rápido para el desarrollo, pero no está pensado para un usuario funcional final:

- No sigue el sistema de diseño institucional (`05`).
- Expone campos técnicos (IDs, claves foráneas crudas) que no aportan al administrador de la universidad.
- No permite controlar con precisión qué puede hacer cada administrador (Django Admin es casi todo-o-nada si no se configura mucho más).
- No permite construir flujos de negocio guiados (ej. "crear persona y su usuario en un solo paso", validado con las reglas de `06`).

**Regla de uso:** Django Admin se mantiene activo solo para el equipo técnico (debugging, correcciones puntuales de datos). El panel interno (`/panel/`) es la única vía de uso para el administrador funcional de la universidad.

## 2. Alcance funcional del panel

| Entidad | Acciones permitidas |
|---|---|
| Persona | Crear, editar, inactivar (no borrar), ver equipos asociados |
| Usuario | Crear cuenta asociada a una persona (o standalone para celador/admin), resetear contraseña, activar/inactivar, ver roles asignados |
| Rol | Crear, editar nombre/descripción, asignar/quitar permisos, inactivar |
| Permiso | Solo lectura — ver catálogo y a qué roles está asignado |
| Organización | CRUD de sedes, facultades, programas y áreas/dependencias (`catalogos.administrar`) |
| Tipo de Vínculo | CRUD del catálogo dinámico de perfiles institucionales (`catalogos.administrar`) |

### 2.1 Por qué `Permiso` es de solo lectura para el administrador

Un permiso (`equipos.registrar`, `control.escanear`, etc.) solo tiene sentido si existe una verificación real en el código que lo consulte. Permitir que el administrador cree permisos libremente generaría entradas "fantasma" sin efecto real. Por eso:

- Los **permisos** se crean únicamente vía migración/fixture, junto con el desarrollo de cada funcionalidad que los requiere.
- Los **roles** y su asignación de permisos sí son 100% gestionables por el administrador — ahí está la flexibilidad real que necesita.

## 3. Permisos nuevos requeridos (ajuste a `01`)

El permiso genérico `usuarios.administrar` definido en `01` se separa en permisos más granulares, para poder dar acceso parcial (ej. alguien que solo gestiona personas, sin poder tocar roles):

| Código | Descripción |
|---|---|
| `personas.administrar` | Crear/editar/inactivar personas |
| `usuarios.administrar` | Crear/editar/inactivar usuarios, resetear contraseñas |
| `roles.administrar` | Crear/editar roles y su asignación de permisos |
| `permisos.ver` | Ver el catálogo de permisos (solo lectura) |

`usuarios.administrar` en `01` queda como alias general que se reemplaza por estos cuatro en el fixture de carga inicial.

## 4. Reglas de negocio del panel

1. **Un administrador no puede quitarse a sí mismo el rol `admin_sistema`.** Evita bloqueos accidentales del único usuario con acceso administrativo.
2. **No se puede inactivar el último usuario activo con rol `admin_sistema`.** El sistema debe validar esto antes de guardar.
3. **No se puede eliminar (borrado físico) ningún registro de Persona, Usuario o Rol** — solo `activo = false`, consistente con la regla general de `02`.
4. **Crear un Usuario para una Persona existente** es el flujo principal (ej. una persona ya registrada por autorregistro o por un docente que se vincula después). También debe existir un flujo para **crear un Usuario sin Persona asociada** (celador, personal de soporte del sistema).
5. **Un Rol no se puede inactivar si tiene usuarios activos asignados** — el sistema debe advertir y pedir reasignar esos usuarios primero.
6. **Todo cambio de rol o de permisos de un rol debe quedar registrado** (quién hizo el cambio, cuándo, qué cambió) — mínimo como texto plano en un log, idealmente en la tabla `auditoria_cambio` ya sugerida como mejora futura en `02`.
7. **Las facultades son transversales** — no dependen de una sede. Se gestionan como catálogo independiente.
8. **Un programa académico requiere sede y facultad** — representa la oferta de una carrera en una sede concreta bajo una facultad.
9. **Persona administrativa:** sede obligatoria + área/dependencia **opcional** (puede quedar pendiente tras autorregistro; la asigna quien tenga `personas.administrar`); **sin programa**.
10. **Persona académica** (docente, estudiante, egresado): sede obligatoria + programa opcional según perfil; **sin área**.
11. **Equipo institucional** (de dependencia) requiere indicar el **Área** que lo asigna al responsable.

## 5. Vistas y rutas

| Ruta | Permiso requerido | Descripción |
|---|---|---|
| `/panel/personas` | `personas.administrar` | Listado con filtros (sede, programa, tipo de vínculo, estado) |
| `/panel/personas/nueva` | `personas.administrar` | Formulario de creación |
| `/panel/personas/<id>/editar` | `personas.administrar` | Edición / inactivar |
| `/panel/usuarios` | `usuarios.administrar` | Listado con filtros (rol, estado, con/sin persona asociada) |
| `/panel/usuarios/nuevo` | `usuarios.administrar` | Formulario: seleccionar persona existente (o marcar "sin persona"), definir username, contraseña temporal |
| `/panel/usuarios/<id>` | `usuarios.administrar` | Detalle: roles asignados, resetear contraseña, activar/inactivar |
| `/panel/roles` | `roles.administrar` | Listado de roles con conteo de usuarios y permisos asignados |
| `/panel/roles/nuevo` | `roles.administrar` | Crear rol (nombre, descripción) |
| `/panel/roles/<id>/permisos` | `roles.administrar` | Matriz de checkboxes: permisos disponibles vs. asignados a este rol |
| `/panel/permisos` | `permisos.ver` | Catálogo de permisos, solo lectura, con los roles que lo usan |
| `/panel/organizacion/` | `catalogos.administrar` | Listado de sedes, facultades, programas y áreas |
| `/panel/organizacion/sedes/nueva/` | `catalogos.administrar` | Crear sede |
| `/panel/organizacion/sedes/<id>/editar/` | `catalogos.administrar` | Editar sede |
| `/panel/organizacion/decanaturas/nueva/` | `catalogos.administrar` | Crear facultad (sin sede) |
| `/panel/organizacion/decanaturas/<id>/editar/` | `catalogos.administrar` | Editar facultad |
| `/panel/organizacion/programas/nuevo/` | `catalogos.administrar` | Crear programa (sede + facultad) |
| `/panel/organizacion/programas/<id>/editar/` | `catalogos.administrar` | Editar programa |
| `/panel/organizacion/areas/nueva/` | `catalogos.administrar` | Crear área/dependencia (CGCA, ISU, CTeI…) |
| `/panel/organizacion/areas/<id>/editar/` | `catalogos.administrar` | Editar área |
| `/personas/tipos-vinculo/` | `catalogos.administrar` | CRUD tipos de vínculo |

## 6. Diseño de las pantallas clave

Siguiendo `05` (Inter, espaciado Bootstrap, verde institucional como único color de marca):

### 6.1 Listado (Personas, Usuarios, Roles)

- Tabla dentro de una card (padding 24px, borde sutil).
- Filtros arriba de la tabla, en una fila con `gap-3`.
- Badge de estado (activo/inactivo) usando los colores funcionales definidos en `05` (verde/gris, nunca amarillo).
- Botón primario "+ Nuevo" alineado a la derecha del título de sección.

### 6.2 Formulario de creación/edición

- Layout de una sola columna en móvil, dos columnas en desktop para campos cortos (ej. tipo de documento + número).
- Labels siempre visibles, 14px peso 500, separación de 8px al input.
- Botón primario "Guardar" + botón secundario "Cancelar", alineados a la derecha.

### 6.3 Matriz de permisos por rol (`/panel/roles/<id>/permisos`)

- Tabla con permisos agrupados por módulo (ej. "Equipos", "Control de acceso", "Catálogos", "Administración") como subtítulos de sección.
- Cada fila: nombre del permiso + checkbox. Guardado explícito con botón "Guardar cambios" (no autoguardado, para evitar cambios accidentales en algo tan sensible).
- Confirmación modal si se están quitando permisos que afectan a usuarios actualmente activos con ese rol.

## 7. Ajuste al plan de implementación (`03`)

Se inserta como **Fase 3.5 — Panel de administración interno**, después de la Fase 3 (`personas`) y antes de la Fase 4 (`equipos`), ya que requiere que `Persona`, `Usuario`, `Rol` y `Permiso` existan:

1. Crear los permisos granulares de la sección 3 (fixture/migración de datos).
2. Construir las vistas de listado y CRUD de Personas (`/panel/personas`).
3. Construir las vistas de listado y CRUD de Usuarios, incluyendo el flujo "crear usuario para persona existente" y "crear usuario sin persona".
4. Construir el CRUD de Roles y la matriz de asignación de permisos.
5. Construir la vista de solo lectura de Permisos.
6. Aplicar las reglas de negocio de la sección 4 (validaciones de auto-bloqueo, último admin, rol en uso).
7. (Opcional, recomendado) Registrar los cambios de rol/permisos en un log básico, aunque sea una tabla simple `log_cambio_rol` con `usuario_que_modifico`, `descripcion`, `timestamp`, como versión mínima de la auditoría completa sugerida en `02`.

## 8. Checklist antes de cerrar esta fase

- [ ] Ningún endpoint del panel es accesible sin el permiso correspondiente (verificado con un usuario sin ese permiso, no solo revisando el código).
- [ ] Probado el caso "intentar quitarme mi propio rol admin_sistema" → debe bloquearse.
- [ ] Probado el caso "inactivar el último usuario admin_sistema" → debe bloquearse.
- [ ] Probado el caso "inactivar un rol con usuarios activos asignados" → debe pedir reasignación primero.
- [ ] Los permisos no se pueden crear ni editar desde el panel, solo consultar.
- [ ] CRUD de áreas/dependencias funcional desde `/panel/organizacion/`.
- [ ] Facultades se crean sin sede; programas exigen sede + facultad.
- [ ] Persona administrativa: validación sede + área opcional, sin programa.
- [ ] Equipo institucional: validación de dependencia (Área) obligatoria al registrar.
