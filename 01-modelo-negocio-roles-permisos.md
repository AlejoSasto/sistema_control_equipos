# 01 — Modelo de Negocio, Roles y Permisos

## 1. Contexto del negocio

La universidad necesita evitar la pérdida de equipos de cómputo (institucionales y personales) que circulan dentro del campus, manejados por distintos perfiles de la comunidad académica: docentes, administrativos, gestores de conocimiento, creadores de oportunidades y graduados.

El control se hace **únicamente a la salida**: cada persona registra sus equipos una vez, y al salir del campus presenta un QR (desde su celular/app web) que un celador escanea para verificar que la persona y el equipo coinciden con lo registrado.

## 2. Actores del sistema

| Actor | Descripción | Interacción principal |
|---|---|---|
| Miembro de comunidad académica | Docente, administrativo, gestor de conocimiento, creador de oportunidades, graduado | Se registra, registra sus equipos, muestra su QR al salir |
| Celador / personal de control | Vigilancia en punto de salida | Escanea el QR, ve el resultado (coincide / alerta) |
| Administrador del sistema | Coordina el proceso a nivel institucional | Gestiona catálogos (sedes, decanaturas, programas), roles, permisos, y resuelve alertas |

Estos actores **no son roles fijos en el código**: se modelan como registros en la tabla `Rol`, para poder agregar nuevos perfiles sin desplegar cambios de código (ej. si mañana aparece el rol "estudiante" o "visitante").

## 3. Entidades organizacionales

La estructura institucional sigue esta jerarquía:

```
Sede
 └── Decanatura
      └── Programa
```

- Una **Sede** es una ubicación física de la universidad (ej. "Seccional Ubaté").
- Una **Decanatura** pertenece a una sede (ej. "Facultad de Ingeniería").
- Un **Programa** pertenece a una decanatura (ej. "Ingeniería de Sistemas y Computación").

Cada **Persona** se vincula a una sede (obligatorio) y, cuando aplica, a un programa (ej. docentes de un programa específico, graduados de un programa). Los perfiles administrativos pueden no tener programa asociado.

## 4. Roles y permisos — filosofía dinámica

En vez de codificar reglas como "si es docente puede X", el sistema usa dos tablas:

- **Rol**: agrupa un conjunto de permisos (ej. `docente`, `administrativo`, `celador`, `admin_sistema`).
- **Permiso**: una acción concreta del sistema, identificada por un código único (ej. `equipos.registrar`, `equipos.ver_propios`, `control.escanear`, `catalogos.administrar`).

Un **Usuario** puede tener uno o varios roles. Cada rol agrupa varios permisos. Esto permite:

- Crear un nuevo rol sin escribir código (solo se crean registros).
- Que una persona tenga más de un rol simultáneamente (ej. un docente que también es gestor de conocimiento).
- Auditar con precisión qué puede hacer cada usuario en un momento dado.

### Permisos sugeridos para el MVP

| Código de permiso | Descripción |
|---|---|
| `equipos.registrar` | Registrar equipos propios |
| `equipos.ver_propios` | Ver y mostrar el QR de los equipos propios |
| `equipos.ver_todos` | Ver todos los equipos registrados (uso administrativo) |
| `control.escanear` | Acceder a la pantalla de control de salida (rol celador) |
| `control.ver_alertas` | Ver el histórico de alertas generadas |
| `catalogos.administrar` | Crear/editar sedes, decanaturas, programas |
| `usuarios.administrar` | Crear/editar usuarios, roles y asignaciones |

### Roles sugeridos para el MVP

| Rol | Permisos asociados |
|---|---|
| `miembro_comunidad` | `equipos.registrar`, `equipos.ver_propios` |
| `celador` | `control.escanear` |
| `admin_sistema` | todos los permisos |

> Nota: `docente`, `administrativo`, `gestor_conocimiento`, `creador_oportunidades` y `graduado` pueden modelarse como **tipo de vínculo de la Persona** (un dato descriptivo) y no necesariamente como roles de acceso al sistema, ya que todos comparten los mismos permisos funcionales (`equipos.registrar`, `equipos.ver_propios`). Esto evita crear roles de acceso redundantes. El detalle de esta distinción está en el documento `02` (campo `tipo_vinculo` en `Persona`).

## 5. Reglas de negocio clave

1. Una persona puede tener **varios equipos** registrados, pero cada equipo tiene **un único dueño**.
2. El `serial` de un equipo es único en todo el sistema (no puede haber dos equipos con el mismo serial).
3. El `token_qr` de un equipo es único, interno, y no debe exponerse en URLs públicas ni en logs legibles por terceros.
4. Solo un usuario con permiso `control.escanear` puede acceder a la pantalla de control de salida.
5. Cada escaneo genera un registro en `Movimiento`, sin excepción, incluso si el resultado es una alerta (no se descarta ningún intento).
6. Un equipo inactivo (`activo = false`, ej. dado de baja) no debe generar un QR válido para salida; el escaneo debe resultar en alerta.
7. Una persona inactiva (ej. graduado que perdió su vínculo) no debe poder generar ni mostrar QR de sus equipos.

## 6. Flujo funcional resumido

1. **Alta de catálogos** (una vez, por el admin): sedes, decanaturas, programas.
2. **Registro de persona**: el admin o la propia persona crea su ficha, vinculada a sede/programa.
3. **Registro de equipos**: la persona registra sus equipos; el sistema genera un `token_qr` único por equipo.
4. **Consulta de QR**: la persona inicia sesión y visualiza el QR de cada equipo cuando lo necesita.
5. **Control de salida**: el celador escanea el QR → el sistema resuelve el equipo y su dueño → muestra en pantalla nombre, foto y datos del equipo → el celador compara visualmente → se registra el `Movimiento`.
6. **Gestión de alertas**: el administrador revisa periódicamente los movimientos marcados como alerta.
