# 02 — Modelo de Datos y Diccionario de Datos

## 1. Diagrama entidad-relación (conceptual)

```
Sede 1───N Decanatura 1───N Programa
  │                              │
  │                              │
  └────────── N Persona N────────┘
                  │
                  │ 1
                  N
               Equipo
                  │ 1
                  N
             Movimiento N───1 Usuario (celador)

Usuario N───N Rol N───N Permiso
Usuario 1───1 Persona (opcional, no todo usuario es "persona" de la comunidad académica)
```

**Notas de diseño:**
- `Persona` y `Usuario` están separados a propósito: `Persona` es un dato de negocio (alguien de la comunidad académica), `Usuario` es una credencial de acceso al sistema. Un celador o un administrador puede ser `Usuario` sin ser `Persona`.
- Todas las tablas de negocio incluyen `created_at`, `updated_at` y `activo` (borrado lógico) salvo que se indique lo contrario.
- Las llaves primarias son `id` autoincremental (`BIGSERIAL`) para uso interno; los identificadores expuestos externamente (como el QR) usan `UUID` aparte.

---

## 2. Diccionario de datos

### 2.1 `sede`

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| id | BIGSERIAL | PK | Identificador interno |
| nombre | VARCHAR(150) | NOT NULL | Nombre de la sede |
| codigo | VARCHAR(20) | UNIQUE, NOT NULL | Código corto institucional |
| ciudad | VARCHAR(100) | NOT NULL | Ciudad de la sede |
| activo | BOOLEAN | DEFAULT true | Borrado lógico |
| created_at | TIMESTAMP | DEFAULT now() | Auditoría |
| updated_at | TIMESTAMP | DEFAULT now() | Auditoría |

### 2.2 `decanatura`

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| id | BIGSERIAL | PK | Identificador interno |
| sede_id | BIGINT | FK → sede.id, NOT NULL | Sede a la que pertenece |
| nombre | VARCHAR(150) | NOT NULL | Nombre de la decanatura/facultad |
| codigo | VARCHAR(20) | UNIQUE, NOT NULL | Código corto institucional |
| activo | BOOLEAN | DEFAULT true | Borrado lógico |
| created_at | TIMESTAMP | DEFAULT now() | Auditoría |
| updated_at | TIMESTAMP | DEFAULT now() | Auditoría |

### 2.3 `programa`

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| id | BIGSERIAL | PK | Identificador interno |
| decanatura_id | BIGINT | FK → decanatura.id, NOT NULL | Decanatura a la que pertenece |
| nombre | VARCHAR(150) | NOT NULL | Nombre del programa académico |
| codigo | VARCHAR(20) | UNIQUE, NOT NULL | Código SNIES o interno |
| nivel | VARCHAR(20) | CHECK IN ('pregrado','posgrado') | Nivel académico |
| activo | BOOLEAN | DEFAULT true | Borrado lógico |
| created_at | TIMESTAMP | DEFAULT now() | Auditoría |
| updated_at | TIMESTAMP | DEFAULT now() | Auditoría |

### 2.4 `persona`

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| id | BIGSERIAL | PK | Identificador interno |
| tipo_documento | VARCHAR(5) | NOT NULL | CC, CE, TI, PAS |
| numero_documento | VARCHAR(20) | UNIQUE, NOT NULL | Documento de identidad |
| nombres | VARCHAR(150) | NOT NULL | Nombres |
| apellidos | VARCHAR(150) | NOT NULL | Apellidos |
| tipo_vinculo | VARCHAR(30) | CHECK IN ('docente','administrativo','gestor_conocimiento','creador_oportunidades','graduado') | Rol funcional dentro de la comunidad académica |
| sede_id | BIGINT | FK → sede.id, NOT NULL | Sede a la que está vinculado |
| programa_id | BIGINT | FK → programa.id, NULLABLE | Programa asociado (aplica a docentes/graduados) |
| foto_url | VARCHAR(255) | NULLABLE | Foto para verificación visual en control |
| activo | BOOLEAN | DEFAULT true | Borrado lógico |
| created_at | TIMESTAMP | DEFAULT now() | Auditoría |
| updated_at | TIMESTAMP | DEFAULT now() | Auditoría |

### 2.5 `rol`

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| id | BIGSERIAL | PK | Identificador interno |
| nombre | VARCHAR(50) | UNIQUE, NOT NULL | Nombre del rol (ej. `miembro_comunidad`, `celador`, `admin_sistema`) |
| descripcion | VARCHAR(255) | NULLABLE | Descripción del rol |
| activo | BOOLEAN | DEFAULT true | Borrado lógico |
| created_at | TIMESTAMP | DEFAULT now() | Auditoría |

### 2.6 `permiso`

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| id | BIGSERIAL | PK | Identificador interno |
| codigo | VARCHAR(60) | UNIQUE, NOT NULL | Código del permiso (ej. `equipos.registrar`) |
| descripcion | VARCHAR(255) | NOT NULL | Descripción legible del permiso |
| created_at | TIMESTAMP | DEFAULT now() | Auditoría |

### 2.7 `rol_permiso` (tabla intermedia N:N)

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| rol_id | BIGINT | FK → rol.id | Parte de PK compuesta |
| permiso_id | BIGINT | FK → permiso.id | Parte de PK compuesta |

PK compuesta: (`rol_id`, `permiso_id`)

### 2.8 `usuario`

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| id | BIGSERIAL | PK | Identificador interno |
| persona_id | BIGINT | FK → persona.id, NULLABLE, UNIQUE | Vínculo opcional a una persona de la comunidad académica |
| username | VARCHAR(50) | UNIQUE, NOT NULL | Usuario de acceso |
| password_hash | VARCHAR(255) | NOT NULL | Contraseña (hash, manejado por Django auth) |
| activo | BOOLEAN | DEFAULT true | Borrado lógico |
| ultimo_login | TIMESTAMP | NULLABLE | Auditoría de acceso |
| created_at | TIMESTAMP | DEFAULT now() | Auditoría |

### 2.9 `usuario_rol` (tabla intermedia N:N)

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| usuario_id | BIGINT | FK → usuario.id | Parte de PK compuesta |
| rol_id | BIGINT | FK → rol.id | Parte de PK compuesta |

PK compuesta: (`usuario_id`, `rol_id`)

### 2.10 `equipo`

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| id | BIGSERIAL | PK | Identificador interno |
| persona_id | BIGINT | FK → persona.id, NOT NULL | Dueño del equipo |
| tipo | VARCHAR(20) | CHECK IN ('portatil','desktop','tablet') | Tipo de equipo |
| marca | VARCHAR(50) | NOT NULL | Marca |
| modelo | VARCHAR(80) | NOT NULL | Modelo |
| serial | VARCHAR(80) | UNIQUE, NOT NULL | Serial físico del fabricante |
| propiedad | VARCHAR(20) | CHECK IN ('institucional','personal') | Tipo de propiedad del equipo |
| token_qr | UUID | UNIQUE, NOT NULL, DEFAULT gen_random_uuid() | Identificador interno codificado en el QR |
| activo | BOOLEAN | DEFAULT true | Borrado lógico (baja de equipo) |
| created_at | TIMESTAMP | DEFAULT now() | Auditoría |
| updated_at | TIMESTAMP | DEFAULT now() | Auditoría |

**Índices recomendados:** `UNIQUE(serial)`, `UNIQUE(token_qr)`, índice sobre `persona_id`.

### 2.11 `movimiento`

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| id | BIGSERIAL | PK | Identificador interno |
| equipo_id | BIGINT | FK → equipo.id, NOT NULL | Equipo escaneado |
| usuario_control_id | BIGINT | FK → usuario.id, NOT NULL | Celador que realizó el escaneo |
| timestamp | TIMESTAMP | DEFAULT now() | Momento del escaneo |
| resultado | VARCHAR(20) | CHECK IN ('ok','alerta','no_encontrado') | Resultado de la verificación |
| observacion | VARCHAR(255) | NULLABLE | Notas del celador si aplica |

**Índices recomendados:** índice sobre `timestamp` (consultas de reportes diarios), índice sobre `equipo_id`.

---

## 3. Convenciones y buenas prácticas aplicadas

- **Nomenclatura:** tablas y campos en `snake_case`, en singular (`persona`, no `personas`).
- **Borrado lógico:** ninguna tabla de catálogo o negocio se borra físicamente; se usa `activo = false`.
- **Auditoría mínima:** `created_at`/`updated_at` en todas las tablas de negocio.
- **Separación identidad interna vs. pública:** `id` (BIGSERIAL) nunca se expone en el QR ni en URLs; `token_qr` (UUID) es el único identificador expuesto.
- **Integridad referencial:** todas las relaciones usan FK con `ON DELETE RESTRICT` por defecto (no se permite borrar una sede con decanaturas activas, por ejemplo), salvo que el negocio pida lo contrario.
- **Extensibilidad:** la relación `rol_permiso` y `usuario_rol` como tablas N:N permite agregar roles/permisos sin cambios de esquema.

## 4. Siguientes pasos posibles (fuera del alcance del MVP, no bloquean la semana 1)

- Tabla `auditoria_cambio` para registrar quién modificó qué registro y cuándo (además de `updated_at`).
- Expiración/rotación del `token_qr` para mitigar capturas de pantalla compartidas.
- Tabla `sesion_qr` si se decide implementar tokens de un solo uso o de corta duración.
