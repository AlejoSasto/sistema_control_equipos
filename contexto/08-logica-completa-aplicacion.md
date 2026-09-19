# 08 — Lógica completa de la aplicación

> Documento de referencia único que explica **cómo funciona el sistema hoy**, integrando los documentos `00`–`07` y el estado actual del código.

---

## 1. Propósito del sistema

La **Universidad de Cundinamarca** necesita controlar la salida de equipos de cómputo (personales e institucionales) del campus. El control se hace **únicamente en la portería al salir**:

1. Cada miembro de la comunidad registra sus equipos una vez.
2. Al salir, muestra un **código QR** desde su celular o pantalla.
3. Un **celador** escanea el QR y el sistema confirma si la persona y el equipo coinciden con lo registrado.

No hay control de ingreso. Cada escaneo genera un registro de auditoría (`Movimiento`), incluso si hay alerta.

---

## 2. Arquitectura técnica

| Aspecto | Decisión |
|---|---|
| Tipo | Monolito modular Django |
| Base de datos | PostgreSQL |
| Frontend | Templates Django + HTMX (sin SPA separado) |
| Autenticación | `Usuario` personalizado (`AbstractUser`) |
| Autorización | Roles y permisos dinámicos en BD (no hardcodeados) |
| Panel funcional | `/panel/` (administrador universitario) |
| Panel técnico | `/admin/` Django (solo superuser / soporte dev) |

### Apps y responsabilidad

```
config/           → settings, urls raíz
apps/
  accounts/       → Usuario, Rol, Permiso, login, registro, mi perfil
  organizacion/   → Sede, Facultad (Decanatura), Programa, Área
  personas/       → Persona, TipoVinculo (catálogo dinámico)
  equipos/        → Equipo, generación de QR
  control_acceso/ → Escaneo en portería, Movimiento
  panel/          → Panel de administración interno (Doc 07)
templates/        → HTML con sistema de diseño v2 (Doc 05)
```

---

## 3. Modelo de datos — entidades y relaciones

### 3.1 Organización institucional

```
Sede ──────────────┐
Facultad (indep.) ─┼──► Programa (sede + facultad)
Área (indep.) ─────┤
                   ├──► Persona (sede + programa | área)
                   └──► Equipo (persona + dependencia opcional)
```

| Entidad | Descripción | Ejemplo |
|---|---|---|
| **Sede** | Ubicación física de la universidad | Seccional Ubaté, Fusagasugá |
| **Facultad** (`Decanatura`) | Unidad académica transversal (no depende de sede) | Facultad de Ingeniería |
| **Programa** | Carrera ofrecida en una sede bajo una facultad | Ing. de Sistemas en Ubaté |
| **Área** | Dependencia administrativa institucional | CGCA (Biblioteca), ISU, CTeI |

Cada **Persona** se vincula obligatoriamente a una **Sede**. Los perfiles académicos pueden tener **Programa**; el personal **Administrativo** tiene **Área** (sin programa).

### 3.2 Identidad vs acceso — la distinción central

El sistema separa dos conceptos que no deben confundirse:

| Concepto | Pregunta que responde | Entidades |
|---|---|---|
| **Identidad institucional** | ¿Quién es esta persona en la universidad? | `Persona` + `TipoVinculo` |
| **Acceso al sistema** | ¿Qué puede hacer dentro de la aplicación? | `Usuario` + `Rol` + `Permiso` |

```
┌─────────────────────────────────────────────────────────────────┐
│                    IDENTIDAD INSTITUCIONAL                     │
│                                                                 │
│  TipoVinculo ──FK──► Persona ──1:1──► Usuario                  │
│  (perfil univ.)      (datos reales)   (login)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ACCESO AL SISTEMA                          │
│                                                                 │
│  Usuario ──M2M──► Rol ──M2M──► Permiso                         │
│           (UsuarioRol)    (RolPermiso)                          │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 TipoVinculo — perfil que usa la universidad

Catálogo **dinámico** configurable desde el panel (permiso `catalogos.administrar`). No es un rol de acceso: es la etiqueta institucional de la persona.

| Nombre visible (universidad) | Código técnico interno |
|---|---|
| Gestor del Conocimiento | `docente` |
| Creador de Oportunidades | `estudiante` |
| Administrativo | `gestor_administrativo` |
| Graduado | `egresado` |

Campos clave:

| Campo | Función |
|---|---|
| `nombre` | Lo que ve el usuario en formularios |
| `codigo` | Identificador interno del sistema |
| `permite_autoregistro` | Si aparece en `/registro/` |
| `dominio_correo_requerido` | Validación de correo institucional |
| `rol_asignado` | Rol que recibe automáticamente al registrarse |

### 3.4 Persona — ficha de la comunidad académica

Registro de una persona física. **No inicia sesión por sí sola.**

- Documento (tipo + número, único)
- Nombres, apellidos
- `tipo_vinculo` → FK a `TipoVinculo`
- `sede` (obligatoria)
- `programa` (opcional, perfiles académicos)
- `area` (opcional, solo administrativo — obligatoria si es `gestor_administrativo`)
- `activo` (borrado lógico)

Relación: **1 Persona → N Equipos**.

| Perfil | Sede | Programa | Área |
|---|---|---|---|
| Docente / Estudiante / Graduado | ✅ | Opcional | ❌ |
| Administrativo | ✅ | ❌ | ✅ |

### 3.5 Usuario — cuenta de login

Extiende `AbstractUser` de Django.

- `username`, `email` (único), contraseña
- `persona` → OneToOne opcional (celadores/admins pueden no tener persona)
- `roles` → M2M vía `UsuarioRol`
- `activo` (borrado lógico)

Método central:

```python
usuario.tiene_permiso("equipos.registrar")  # consulta roles activos → permisos
```

### 3.6 Rol y Permiso — control de acceso

**Permiso** = acción atómica verificada en código (`equipos.registrar`, `control.escanear`, etc.).

**Rol** = agrupación de permisos asignable a usuarios.

Los permisos **no se crean desde el panel** — se cargan con migraciones/seed junto al desarrollo de cada funcionalidad. Desde el panel solo se consultan (`permisos.ver`) y se asignan a roles (`roles.administrar`).

### 3.7 Equipo — dispositivo registrado

| Campo | Restricción |
|---|---|
| `serial` | Único en todo el sistema |
| `token_qr` | UUID único, codificado en el QR |
| `persona` | Responsable único (FK) |
| `propiedad` | `personal` o `institucional` (de dependencia) |
| `dependencia` | FK a `Area` — obligatoria si `propiedad=institucional` |
| `activo` | Si es `false`, el escaneo genera alerta |

**Tipos de equipo:**
- **Personal:** propiedad del miembro; sin dependencia.
- **De dependencia (institucional):** asignado por un Área (ej. CGCA) a una persona responsable.

Cada equipo genera su QR al vuelo (Base64 PNG) a partir de `token_qr`.

### 3.8 Movimiento — registro de cada escaneo

Cada escaneo en portería crea un `Movimiento`, sin excepción:

| Resultado | Significado |
|---|---|
| `ok` | Persona activa + equipo activo + coincidencia |
| `alerta` | Equipo inactivo, persona inactiva u otra anomalía |
| `no_encontrado` | QR/serial no existe en la base de datos |

---

## 4. Roles del sistema y qué puede hacer cada uno

### 4.1 Los tres roles de acceso

| Rol | Actor real | Permisos |
|---|---|---|
| **`miembro_comunidad`** | Gestor del Conocimiento, Creador de Oportunidades, Administrativo, Graduado | Solo lo propio (ver abajo) |
| **`celador`** | Personal de portería / guarda | Escanear QR, ver alertas e historial |
| **`admin_sistema`** | Coordinador institucional | Panel completo + catálogos + inventario |

> **Regla clave:** los cuatro perfiles universitarios comparten el **mismo rol** (`miembro_comunidad`) porque en el sistema hacen exactamente lo mismo. La diferencia entre ellos es solo descriptiva (`TipoVinculo`), no de acceso.

### 4.2 Permisos por rol

| Permiso | miembro_comunidad | celador | admin_sistema |
|---|:---:|:---:|:---:|
| `perfil.ver_propio` | ✅ | — | ✅ |
| `equipos.registrar` | ✅ | — | ✅ |
| `equipos.ver_propios` | ✅ | — | ✅ |
| `equipos.ver_todos` | — | — | ✅ |
| `control.escanear` | — | ✅ | ✅ |
| `control.ver_alertas` | — | ✅ | ✅ |
| `catalogos.administrar` | — | — | ✅ |
| `personas.administrar` | — | — | ✅ |
| `usuarios.administrar` | — | — | ✅ |
| `roles.administrar` | — | — | ✅ |
| `permisos.ver` | — | — | ✅ |

### 4.3 Qué ve cada actor en el menú

| Actor | Sección del menú | Rutas principales |
|---|---|---|
| **Miembro comunidad** | Mi Espacio | `/accounts/mi-perfil/`, `/equipos/mis-equipos/`, `/equipos/nuevo/` |
| **Celador** | Portería | `/acceso/control-salida/`, `/acceso/historico/` |
| **Administrador** | Panel + Catálogos | `/panel/*`, inventario de equipos, tipos de vínculo |

---

## 5. Flujos de negocio

### 5.1 Autorregistro externo (`/registro/`)

Flujo público (sin autenticación):

```
Usuario elige TipoVinculo (solo los con permite_autoregistro=true)
    ↓
Completa: documento, nombres, correo institucional, sede, contraseña
    ↓
Validaciones backend:
  • Dominio de correo (@ucundinamarca.edu.co)
  • Documento y correo únicos
  • Contraseña ≥ 8 caracteres, ≠ documento
    ↓
Transacción atómica:
  1. Crear Persona
  2. Crear Usuario (username = correo)
  3. Asignar Rol = TipoVinculo.rol_asignado (miembro_comunidad)
    ↓
Redirige a login
```

El usuario **nunca elige su rol** — lo determina el catálogo `TipoVinculo`.

### 5.2 Uso diario del miembro de comunidad

```
Login → Mi Perfil (datos + métricas propias)
      → Mis Equipos (lista con QR)
      → Registrar Equipo (marca, modelo, serial, propiedad, dependencia si institucional)
      → Al salir: mostrar QR en celular al celador
```

**Mi Perfil** (`/accounts/mi-perfil/`) muestra:
- Datos de Persona (documento, sede, tipo de vínculo)
- Datos de Usuario (username, correo, rol)
- Equipos activos propios
- Métricas: total equipos, salidas OK, alertas

### 5.3 Control de salida en portería

El kiosco acepta el `token_qr` por **tres vías** (mismo endpoint HTMX):

1. **Pistola / lector óptico** — actúa como teclado + Enter sobre el input.
2. **Cámara del dispositivo** — botón «Usar cámara» (`html5-qrcode`); al leer, rellena el input y verifica. Requiere HTTPS (o localhost).
3. **Teclado** — escribir o pegar el código y pulsar «Verificar».

```
Celador abre pantalla de escaneo (autofocus permanente)
    ↓
Persona presenta QR → pistola / cámara / teclado envía token_qr
    ↓
Sistema busca Equipo por token_qr (o serial como fallback)
    ↓
┌─ No existe ──────────────────► Movimiento: no_encontrado (pantalla gris)
├─ Equipo/persona inactivo ───► Movimiento: alerta (pantalla roja)
└─ Todo coincide y activo ─────► Movimiento: ok (pantalla verde)
    ↓
Tabla del turno se actualiza vía HTMX sin recargar página
```

### 5.4 Administración interna (`/panel/`)

Panel propio con diseño institucional (Doc 07). Django Admin queda reservado para soporte técnico.

| Módulo | Permiso | Operaciones |
|---|---|---|
| Personas | `personas.administrar` | Crear, editar, inactivar, ver equipos asociados |
| Usuarios | `usuarios.administrar` | Crear (con/sin persona), roles, reset password, inactivar |
| Roles | `roles.administrar` | CRUD + matriz de permisos |
| Permisos | `permisos.ver` | Solo lectura del catálogo |
| Organización | `catalogos.administrar` | CRUD sedes, facultades, programas y áreas |
| Tipos de Vínculo | `catalogos.administrar` | CRUD catálogo dinámico de perfiles |

#### Reglas de seguridad del panel

1. Un admin **no puede quitarse** su propio rol `admin_sistema` si es el único activo.
2. **No se inactiva** el último usuario con rol `admin_sistema`.
3. **No se inactiva** un rol que tenga usuarios activos asignados.
4. **No hay borrado físico** — solo `activo = false`.
5. Cambios de roles/permisos quedan en `log_cambio_rol` (auditoría mínima).

### 5.5 Creación de usuario por administrador

Dos flujos:

| Flujo | Caso | Ejemplo |
|---|---|---|
| **Con persona** | Miembro que ya tiene ficha o se registró antes | Docente con Persona existente |
| **Sin persona** | Operador del sistema sin ficha institucional | Celador, soporte |

---

## 6. Mapa de rutas

### Públicas (sin login)

| Ruta | Descripción |
|---|---|
| `/registro/` | Autorregistro externo |
| `/accounts/login/` | Inicio de sesión |

### Miembro de comunidad

| Ruta | Permiso |
|---|---|
| `/accounts/mi-perfil/` | `perfil.ver_propio` |
| `/equipos/mis-equipos/` | `equipos.ver_propios` |
| `/equipos/nuevo/` | `equipos.registrar` |
| `/equipos/<id>/` | Propio o admin |
| `/equipos/qr/<token>/` | Pantalla QR para portería |

### Celador

| Ruta | Permiso |
|---|---|
| `/acceso/control-salida/` | `control.escanear` |
| `/acceso/historico/` | `control.ver_alertas` |

### Panel administrativo

| Ruta | Permiso |
|---|---|
| `/panel/personas/` | `personas.administrar` |
| `/panel/usuarios/` | `usuarios.administrar` |
| `/panel/roles/` | `roles.administrar` |
| `/panel/permisos/` | `permisos.ver` |
| `/panel/organizacion/` | `catalogos.administrar` |
| `/personas/tipos-vinculo/` | `catalogos.administrar` |
| `/equipos/inventario/` | `equipos.ver_todos` |

### Redirección post-login

| Permiso detectado | Destino |
|---|---|
| `control.escanear` | Pantalla de portería |
| `perfil.ver_propio` | Mi Perfil |
| `catalogos.administrar` | Panel Organización |
| `personas.administrar` | Panel Personas |
| `usuarios.administrar` | Panel Usuarios |

---

## 7. Reglas de negocio transversales

| # | Regla |
|---|---|
| R1 | Un equipo tiene un único dueño (`Persona`) |
| R2 | El `serial` es único en todo el sistema |
| R3 | El `token_qr` es único y no se expone en URLs públicas legibles |
| R4 | Solo usuarios con `control.escanear` acceden a la pantalla de portería |
| R5 | **Todo escaneo** genera un `Movimiento`, incluso alertas |
| R6 | Equipo inactivo → escaneo = alerta |
| R7 | Persona inactiva → no puede mostrar QR válido → escaneo = alerta |
| R8 | Borrado lógico (`activo=false`) en todas las entidades principales |
| R9 | Permisos se crean con código, no desde el panel |
| R10 | Tipo de vínculo ≠ rol de acceso (son capas distintas) |
| R11 | Facultad no depende de sede — es catálogo transversal |
| R12 | Programa requiere sede + facultad; debe coincidir con la sede de la persona |
| R13 | Persona administrativa: sede + área, sin programa |
| R14 | Equipo institucional requiere dependencia (Área) asignada |

---

## 8. Datos de prueba (seed)

Comando: `python manage.py seed_data`

| Usuario | Contraseña | Rol | Uso |
|---|---|---|---|
| `admin` | `admin123` | admin_sistema | Panel completo |
| `celador1` | `celador123` | celador | Portería |
| `docente1` | `docente123` | miembro_comunidad | Mi perfil + equipos |

---

## 9. Diagrama general del flujo de vida

```
                    ┌──────────────┐
                    │  /registro/  │ (público)
                    └──────┬───────┘
                           │ crea Persona + Usuario + Rol
                           ▼
              ┌────────────────────────┐
              │   miembro_comunidad    │
              │                        │
              │  Mi Perfil ──────────► │ datos personales + métricas
              │  Mis Equipos ────────► │ lista + QR
              │  Registrar Equipo ───► │ serial único + token_qr
              └───────────┬────────────┘
                          │ al salir del campus
                          ▼
              ┌────────────────────────┐
              │       celador          │
              │  Escanea QR ─────────► │ Movimiento (ok/alerta/no_encontrado)
              └────────────────────────┘

              ┌────────────────────────┐
              │    admin_sistema       │
              │  /panel/ ────────────► │ personas, usuarios, roles
              │  /panel/organizacion/ ►│ sedes, facultades, programas, áreas
              │  Inventario equipos ──►│ todos los equipos del sistema
              └────────────────────────┘
```

---

## 10. Documentos relacionados

| Doc | Contenido |
|---|---|
| `00-arquitectura-general.md` | Filosofía y estructura modular |
| `01-modelo-negocio-roles-permisos.md` | Reglas de negocio originales |
| `02-modelo-datos-diccionario.md` | Diccionario de datos PostgreSQL |
| `03-plan-implementacion-paso-a-paso.md` | Fases de construcción |
| `05-sistema-diseno-v2.md` | Sistema de diseño visual |
| `06-registro-externo-roles-permisos.md` | Autorregistro y TipoVinculo |
| `07-panel-administracion-interno.md` | Panel `/panel/` |

Este documento (`08`) es la **síntesis operativa**: cómo encajan todas las piezas en la aplicación desplegada.
