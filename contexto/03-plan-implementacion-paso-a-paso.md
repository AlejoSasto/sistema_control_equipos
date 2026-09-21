# 03 — Plan de Implementación Paso a Paso (Antigravity)

> Prerrequisitos: leer `00-arquitectura-general.md`, `01-modelo-negocio-roles-permisos.md` y `02-modelo-datos-diccionario.md` antes de ejecutar cualquier tarea de este plan.

## Fase 0 — Setup del proyecto (Día 1, mañana)

1. Crear proyecto Django (`config`) y las apps vacías: `accounts`, `organizacion`, `personas`, `equipos`, `control_acceso`.
2. Configurar conexión a PostgreSQL en `settings.py` (variables de entorno para credenciales).
3. Configurar `AUTH_USER_MODEL` si se decide extender el usuario de Django, o dejar el `User` estándar y añadir `Usuario` como perfil extendido (ver nota en `02`).
4. Verificar que el proyecto corre localmente (`runserver`) y conecta a la base de datos.

**Entregable:** proyecto Django corriendo, migraciones iniciales aplicadas, conexión a Postgres verificada.

---

## Fase 1 — Módulo `organizacion` (Día 1, tarde)

1. Crear modelos `Sede`, `Decanatura`, `Programa` según el diccionario de datos (`02`, secciones 2.1–2.3).
2. Generar y aplicar migraciones.
3. Registrar los tres modelos en Django Admin para poder cargarlos manualmente.
4. Cargar datos de prueba (al menos 1 sede, 1 decanatura, 1 programa) vía Admin o fixture.

**Entregable:** catálogos institucionales gestionables desde Django Admin.

---

## Fase 2 — Módulo `accounts` (Día 2, mañana)

1. Crear modelos `Rol`, `Permiso`, `RolPermiso`, `Usuario`, `UsuarioRol` (sección 2.5–2.9 de `02`).
2. Registrar en Django Admin.
3. Cargar los roles y permisos iniciales del documento `01` (sección 4 y 5): `miembro_comunidad`, `celador`, `admin_sistema` y sus permisos asociados.
4. Implementar login básico (puede usarse el sistema de auth de Django directamente, extendido con el modelo `Usuario`/`Rol`).
5. Implementar un decorador o mixin de verificación de permisos (ej. `@requiere_permiso('control.escanear')`) reutilizable en las vistas de los demás módulos.

**Entregable:** login funcional, roles y permisos cargados, mecanismo de verificación de permisos listo para usar en otras apps.

---

## Fase 3 — Módulo `personas` (Día 2, tarde)

1. Crear modelo `Persona` (sección 2.4 de `02`), con FK a `Sede` y `Programa`.
2. Vincular `Persona` con `Usuario` (relación 1:1 opcional, ver sección 2.8).
3. Registrar en Django Admin.
4. Formulario simple de autorregistro (opcional para el MVP) o registro por el admin.

**Entregable:** una persona puede quedar registrada y vinculada a su sede/programa.

---

## Fase 4 — Módulo `equipos` (Día 3)

1. Crear modelo `Equipo` (sección 2.10 de `02`), con `token_qr` generado automáticamente al crear el registro (`UUID`).
2. Vista para que la persona registre sus equipos (marca, modelo, serial, tipo, propiedad).
3. Vista "Mi(s) equipo(s)" donde la persona ve su lista de equipos y un botón "Mostrar QR" por cada uno.
4. Generación del QR en tiempo real a partir del `token_qr` (librería `qrcode`), renderizado como imagen en la página (no se guarda como archivo estático, se genera al vuelo).

**Entregable:** una persona autenticada puede registrar equipos y visualizar su QR en pantalla.

---

## Fase 5 — Módulo `control_acceso` (Día 4)

1. Crear modelo `Movimiento` (sección 2.11 de `02`).
2. Pantalla de "control de salida" (protegida por el permiso `control.escanear`):
   - Input de texto con autofocus permanente (para recibir la entrada del lector de código de barras/QR, que actúa como teclado + Enter).
   - Al recibir el `token_qr`, resolver el `Equipo` y su `Persona` dueño.
   - Mostrar en pantalla grande: foto, nombre, tipo de vínculo, marca/modelo del equipo, y un indicador visual claro (verde = coincide, rojo = alerta).
   - Si el token no existe o el equipo/persona está inactivo → resultado `no_encontrado` o `alerta`.
3. Registrar cada escaneo en `Movimiento`, sin excepción.
4. Vista de histórico de movimientos filtrable por fecha/resultado (protegida por `control.ver_alertas`).

**Entregable:** flujo completo de escaneo en portería funcionando de extremo a extremo.

---

## Fase 6 — Pruebas con hardware real (Día 5)

1. Conectar el lector de código de barras/QR USB o Bluetooth a la máquina de portería.
2. Probar el flujo completo: persona muestra QR en celular → celador escanea → pantalla de control responde.
3. Ajustar tamaño de fuente, colores de alerta y tiempos de respuesta según feedback del celador.
4. Probar casos borde: equipo inactivo, persona inactiva, QR inexistente, doble escaneo del mismo equipo en el mismo día.

**Entregable:** sistema probado con hardware real, casos borde cubiertos.

---

## Fase 7 — Piloto y ajustes finales (Día 6–7)

1. Ejecutar un piloto de un día completo en paralelo con la minuta en papel actual.
2. Comparar resultados: ¿el sistema detectó todos los movimientos? ¿hubo falsos positivos/negativos?
3. Capacitar al personal de portería (10–15 minutos, flujo simple: pedir QR, escanear, verificar en pantalla).
4. Ajustes finales de UI/UX según feedback del piloto.
5. Desplegar en Render con Docker (`render.yaml` + instructivo en `contexto/operaciones/despliegue-render.md`).

**Entregable:** MVP desplegado y validado con uso real, listo para reemplazar el proceso en papel.

---

## Checklist de buenas prácticas a verificar antes de cerrar el MVP

- [ ] Todas las tablas de negocio tienen `created_at`/`updated_at`.
- [ ] Ninguna tabla de catálogo permite borrado físico (solo `activo = false`).
- [ ] `serial` y `token_qr` tienen restricción `UNIQUE` a nivel de base de datos, no solo a nivel de aplicación.
- [ ] Las vistas sensibles (`control_acceso`, `accounts`) verifican permisos, no solo autenticación.
- [ ] Los permisos y roles están cargados como datos (fixture o migración de datos), no hardcodeados en el código de las vistas.
- [ ] El `token_qr` nunca aparece en logs de texto plano ni en URLs indexables.
