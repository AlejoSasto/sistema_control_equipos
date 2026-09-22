# Brief para Claude — Manual de usuario (Word) completo

**Propósito de este archivo:** ser el **prompt maestro** que le das a Claude (u otro LLM) para que redacte el **Manual de usuario** del *Sistema de Control de Salida de Equipos de Cómputo* (Universidad de Cundinamarca) listo para pegar/exportar a **Microsoft Word**.

**Fuente de verdad del producto:** [`contexto-completo-sistema.md`](contexto-completo-sistema.md) (vigente 2026-09-22, incluye correos de bienvenida / recuperación de contraseña / aviso de desbloqueo). Si hay conflicto con docs antiguos, gana ese archivo.

**Cómo usar:** copia desde la sección «PROMPT PARA CLAUDE» hasta el final y pégalo en Claude. Adjunta también (si puedes) el archivo `contexto-completo-sistema.md` completo como contexto adicional.

---

## PROMPT PARA CLAUDE

```
Eres un redactor técnico experto en manuales de usuario institucionales en español (Colombia).

Tu tarea: redactar un MANUAL DE USUARIO COMPLETO del sistema web
«Sistema de Control de Salida de Equipos de Cómputo» de la Universidad de Cundinamarca,
listo para copiar a Microsoft Word (.docx).

============================================================
1. OBJETIVO DEL DOCUMENTO
============================================================

- Público: usuarios finales (no desarrolladores).
- Lenguaje: claro, formal-institucional colombiano, segunda persona («usted» o «tú» consistente; prefiera «usted»).
- Incluir: portada, control de versiones, índice, glosario, capítulos por perfil, FAQ, solución de problemas, anexos.
- Excluir: código fuente, migraciones, Docker, stack técnico (Django, PostgreSQL, Resend, Celery, Redis, webhooks, etc.),
  rutas internas de archivos, nombres de tablas de BD, nombres de proveedores de correo.
- Sí puede mencionar rutas de pantalla en lenguaje de usuario (p. ej. «Menú → Mis equipos») y URLs relativas legibles
  (/registro/, /accounts/password-reset/, /panel/, etc.) cuando ayuden.
- Marcar capturas con placeholders: [CAPTURA: descripción de lo que debe verse].
- No inventar funciones que no estén en la fuente de verdad. Si algo no está documentado, indíquelo como
  «consultar con el administrador del sistema».

============================================================
2. IDENTIDAD DEL PRODUCTO (resumen obligatorio)
============================================================

Nombre: Sistema de Control de Salida de Equipos de Cómputo
Institución: Universidad de Cundinamarca

Qué hace (solo salida, no ingreso):
1. El miembro registra sus equipos de cómputo (una vez).
2. Al salir del campus muestra un código QR (celular o pantalla).
3. En portería el vigilante escanea el QR y el sistema confirma si persona y equipo coinciden.
4. Cada escaneo deja un registro de movimiento (incluso si hay alerta).

No controla el ingreso al campus.

Correos que el sistema puede enviar al usuario (lenguaje de negocio, sin nombrar proveedores):
- Bienvenida tras un registro exitoso (la cuenta ya se puede usar; no hay que «activar» el correo para entrar).
- Enlace para restablecer la contraseña («¿Olvidó su contraseña?»).
- Aviso cuando un administrador desbloquea una cuenta bloqueada por intentos fallidos.

============================================================
3. PERFILES DE USUARIO (capítulos separados)
============================================================

Organice el manual por perfiles. Cada perfil debe tener: propósito, cómo entra, menús típicos, tareas paso a paso, errores frecuentes.

A) Miembro de la comunidad (autorregistro)
   Vínculos típicos (nombres visibles):
   - Gestor Administrativo
   - Creador de Oportunidades
   - Gestor del Conocimiento
   - Egresado
   Correo: deben usar @ucundinamarca.edu.co
   Al registrarse reciben rol de miembro (no eligen su rol).
   Username institucional = parte local del correo
   (ej. juan.perez@ucundinamarca.edu.co → usuario juan.perez).
   Pueden iniciar sesión con: usuario, correo completo o número de documento (cédula).
   Tras registrarse reciben un correo de bienvenida (revisar bandeja y spam); pueden entrar de inmediato.

   Gestor Administrativo: en el registro NO elige área ni programa.
   El área la asigna después un administrador. Puede usar el sistema con área pendiente.

   Resto de comunidad: programa opcional (filtrado por la sede elegida); sin área.

B) Personal externo (visitante)
   Correo: cualquiera (no exige dominio institucional).
   Username = correo completo.
   En el registro declara: sede destino, tipo de dependencia (facultad / programa / área),
   dependencia, fecha inicio y fecha fin de la visita.
   Si elige «área», solo aparecen áreas de la sede seleccionada.
   También reciben correo de bienvenida tras el registro.
   Puede registrar visitas nuevas después en «Registrar visita».
   Una visita nueva cierra la visita activa anterior.
   Al vencer la visita, la cuenta sigue activa; debe registrar una nueva visita.

C) Vigilante (portería)
   NO se autoregistra. Lo crea un administrador.
   Opera el kiosco de control de salida.
   Pertenece a una sola sede.
   Si la persona es de otra sede: la salida puede ser OK con aviso «Otra sede».

D) Responsable de dependencia
   Inventaria y asigna equipos institucionales de su unidad
   (facultad, programa o área).
   No es lo mismo que «alcance» administrativo global.

E) Administrador del sistema
   Panel interno, catálogos, personas, usuarios, roles, alcance,
   dashboard, reportes Excel, desbloqueo de cuentas, alta de vigilantes,
   organización (sedes, facultades, programas, áreas).
   MFA (aplicación autenticadora) obligatorio.
   Login bloqueado tras varios intentos fallidos (aprox. 5); espera ~1 hora
   o un admin con permiso de desbloqueo puede liberar la cuenta.
   Al desbloquear desde el panel, el usuario puede recibir un correo avisando que ya puede entrar.
   Puede restablecer la contraseña de un usuario desde la ficha (acción de panel) además del
   flujo de «Olvidé mi contraseña» que usa el propio usuario.

============================================================
4. CONCEPTOS CLAVE (glosario obligatorio)
============================================================

Explique en lenguaje no técnico:

- Persona vs Usuario (identidad institucional vs acceso a la aplicación).
- Tipo de vínculo (perfil universitario: estudiante/docente/etc. con nombres institucionales).
- Sede, Facultad, Programa, Área/Dependencia.
  IMPORTANTE: cada Área pertenece a UNA sede. El mismo código (ej. CGCA) puede existir
  en Ubaté y en Fusagasugá como dependencias distintas. Al asignar área a una persona
  o visita, el área debe ser de la misma sede.
- Equipo personal vs equipo institucional.
- Código QR (se renueva / tiene vigencia corta al mostrarlo; explicar que debe mostrarse
  la pantalla de QR al salir, no una foto vieja impresa si el sistema exige QR vivo).
- Movimiento / resultado del escaneo: OK (verde), Alerta (rojo), No encontrado (gris).
- Asignación institucional con vigencia (fechas inicio/fin).
- Visita externa con vigencia.
- Alcance (qué sedes/unidades puede ver un administrador u operador): Global, Sede,
  Facultad, Programa, Área. Los permisos dicen QUÉ puede hacer; el alcance dice
  SOBRE QUÉ datos. Un usuario sin alcance adecuado verá listados vacíos.
- MFA / autenticación en dos pasos (solo administradores).
- Bloqueo por intentos fallidos de login.
- Correo de bienvenida (informativo; no bloquea el acceso).
- Restablecimiento de contraseña por correo (enlace de un solo uso / tiempo limitado;
  si expiró, solicitar uno nuevo). Diferenciar de «cuenta bloqueada por intentos fallidos».

============================================================
5. ESTRUCTURA OBLIGATORIA DEL MANUAL (Word)
============================================================

PORTADA
- Título: Manual de usuario — Sistema de Control de Salida de Equipos de Cómputo
- Subtítulo: Universidad de Cundinamarca
- Versión del documento: 1.1
- Fecha: [usar fecha actual al generar]
- Clasificación: Uso interno / comunidad universitaria

CONTROL DE CAMBIOS
| Versión | Fecha | Descripción |
| 1.0 | … | Versión inicial del manual |
| 1.1 | … | Correo de bienvenida; olvidé / restablecer contraseña; aviso al desbloquear cuenta |

ÍNDICE (generable en Word)

1. Introducción
   1.1 Propósito del sistema
   1.2 Alcance del manual (qué cubre / qué no)
   1.3 Requisitos (navegador actualizado, internet; kiosco: HTTPS o localhost para cámara;
       acceso al correo institucional o personal registrado para recuperación de contraseña)
   1.4 Política de datos (mencionar que existe página de política de datos personales)

2. Glosario

3. Primeros pasos comunes
   3.1 Cómo acceder a la aplicación (URL institucional — placeholder [URL_PRODUCCION])
   3.2 Autorregistro (y qué esperar del correo de bienvenida)
   3.3 Inicio de sesión (usuario / correo / cédula)
   3.4 Cerrar sesión
   3.5 Olvidé mi contraseña (solicitar enlace → correo → definir nueva contraseña)
   3.6 Cuenta bloqueada por intentos fallidos (esperar / pedir desbloqueo a un admin)
   3.7 Mi perfil

4. Guía para miembros de la comunidad
   4.1 Registro según tipo de vínculo
   4.2 Caso especial: Gestor Administrativo (área pendiente)
   4.3 Mis equipos — registrar equipo personal
   4.4 Mostrar QR al salir
   4.5 Dar de baja / dar de alta un equipo personal
   4.6 Equipos institucionales asignados (solo ver QR; no editar)

5. Guía para personal externo
   5.1 Registro inicial y primera visita
   5.2 Registrar una nueva visita
   5.3 Qué pasa cuando vence la visita
   5.4 Salida por portería (qué debe mostrar)

6. Guía para vigilante (kiosco)
   6.1 Acceso al puesto de control
   6.2 Tres formas de escanear: pistola/lector, cámara, manual
   6.3 Interpretar el semáforo (OK / Alerta / No encontrado)
   6.4 Badges: visitante externo, otra sede, unidad institucional
   6.5 Casos de alerta frecuentes (equipo inactivo, sin asignación, visita vencida, etc.)
   6.6 Histórico / alertas (si tiene permiso)

7. Guía para responsable de dependencia
   7.1 Rol y límites
   7.2 Alta de equipo institucional al inventario (sin persona)
   7.3 Asignar a una persona (fechas de vigencia)
   7.4 Renovar, reasignar, devolver al inventario, dar de baja
   7.5 Filtros de inventario y vigencia (vigente / por vencer / vencida)

8. Guía para administrador
   8.1 Panel interno y dashboard (KPIs y gráficos — solo agregados)
   8.2 Personas (crear, editar, filtrar sin área, asignar área de la misma sede)
   8.3 Alta de vigilante
   8.4 Usuarios: roles, restablecer contraseña (panel), desbloquear login
       (el usuario puede recibir aviso por correo), gestionar alcance
   8.5 Organización: sedes, facultades, programas, áreas (área exige sede; código único por sede)
   8.6 Responsables de dependencia
   8.7 Reportes Excel (5 tipos: movimientos, equipos, personas, alertas, ejecutivo)
       — ver vs exportar (permisos distintos)
   8.8 MFA obligatorio
   8.9 Buenas prácticas de seguridad y privacidad
       (incluir: no compartir enlaces de restablecimiento; revisar spam si no llega el correo)

9. Preguntas frecuentes (FAQ) — mínimo 18 preguntas
    Incluir al menos:
    - ¿Debo confirmar mi correo para poder entrar? (No; la cuenta queda usable al registrarse.)
    - No me llegó el correo de bienvenida / de restablecer contraseña (spam, correo mal escrito, esperar unos minutos, contactar admin).
    - ¿Cómo restablezco mi contraseña sin un administrador?
    - ¿Cuál es la diferencia entre «olvidé mi contraseña» y «cuenta bloqueada»?
    - El enlace del correo dice que expiró o no es válido.

10. Solución de problemas
    - No puedo iniciar sesión / cuenta bloqueada
    - Olvidé mi contraseña y no llega el correo
    - El enlace de restablecimiento no funciona o ya se usó
    - No veo mis áreas o programas al registrarme
    - El QR no es válido en portería
    - Listados vacíos en el panel
    - Cámara del kiosco no inicia
    - No puedo asignar un área a una persona
    - Personal externo: no me deja elegir área

11. Anexos
    A. Tabla de tipos de vínculo y requisitos de correo
    B. Tabla de resultados del kiosco (semáforo)
    C. Matriz resumida «quién puede hacer qué» (lenguaje de negocio, no códigos de permiso)
    D. Correos que puede recibir el usuario (bienvenida, restablecer contraseña, cuenta desbloqueada)
    E. Contacto de soporte [PLACEHOLDER]
    F. Lista de capturas recomendadas para el equipo de documentación
        (incluir: login con enlace «¿Olvidó su contraseña?», formulario de solicitud,
         correo de ejemplo / pantalla de confirmación, pantalla de nueva contraseña)

============================================================
6. CONTENIDO DETALLADO QUE DEBE REFLEJARSE (hechos del sistema)
============================================================

### Login
- Identificadores válidos: nombre de usuario, correo electrónico o número de documento.
- Comunidad institucional: username = parte antes de @ucundinamarca.edu.co.
- Externo y vigilante: username = correo completo.
- Administradores: autenticación en dos pasos (TOTP) obligatoria.
- Tras varios fallos (~5), bloqueo ~1 hora; mensaje en pantalla; admin puede desbloquear.
- En la pantalla de inicio de sesión hay el enlace «¿Olvidó su contraseña?».

### Olvidé / restablecer contraseña (flujo del usuario)
- Ruta: /accounts/password-reset/ (desde el enlace del login).
- El usuario indica usuario, correo o documento.
- El sistema muestra un mensaje genérico de éxito (por seguridad no confirma si la cuenta existe).
- Si hay cuenta activa con correo, se envía un mensaje con un enlace para definir nueva contraseña.
- El enlace lleva a /accounts/password-reset/confirmar/ (con token); el usuario escribe y confirma la nueva contraseña.
- El enlace tiene tiempo limitado (del orden de horas); si expiró o ya se usó, debe solicitar uno nuevo.
- Hay límite de intentos por minuto en la solicitud (evitar abuso); si bloquea, esperar e intentar de nuevo.
- Tras cambiar la contraseña, vuelve al login.

### Correo de bienvenida
- Se envía automáticamente tras un autorregistro exitoso.
- NO es una confirmación obligatoria: el usuario puede iniciar sesión de inmediato aunque aún no abra el correo.
- Revisar carpeta de spam / correo no deseado.

### Desbloqueo por administrador
- Desde la ficha del usuario en el panel: acción de desbloquear (tras bloqueo por intentos fallidos).
- El usuario puede recibir un correo corto avisando que la cuenta quedó desbloqueada y puede entrar.
- Distinto del restablecimiento de contraseña: desbloquear no cambia la clave; solo libera el bloqueo temporal.

### Autorregistro
- Ruta pública /registro/
- El usuario NO elige rol de sistema; el tipo de vínculo define el acceso.
- Gestor administrativo: sin área/programa en el formulario.
- Personal externo: sede + dependencia + vigencia; crea primera visita.
- Tras éxito: correo de bienvenida + acceso inmediato.

### Mis equipos y QR
- Registrar equipo personal (marca, modelo, serial, tipo, etc. — describir campos genéricos).
- Mostrar QR al salir; el QR de pantalla tiene vigencia corta (no reutilizar captura antigua).
- Institucional asignado: aparece para mostrar QR, sin editar/baja por el miembro.
- Personal dado de baja: no sirve en kiosco; el dueño puede reactivarlo (dar de alta).

### Kiosco
- Ruta típica de control de salida.
- Entradas: lector USB (teclado + Enter), cámara web, digitación manual.
- Semáforo verde/rojo/gris.
- Institucional sin asignación activa → alerta.
- Asignación vencida → el sistema cierra la asignación y alerta.
- Externo sin visita o visita vencida → alerta.
- Persona de otra sede → OK + aviso «Otra sede».

### Institucionales (responsable / admin)
- Flujo: designar responsable → alta inventario (disponible, sin persona) → asignar con fechas →
  renovar / reasignar / devolver / baja.
- Devolver = vuelve a inventario disponible.
- Vencimiento automático al escanear o por proceso programado (explicar en lenguaje de usuario:
  «al vencer la fecha, el equipo deja de ser válido para salida hasta nueva asignación»).

### Organización (admin)
- Área siempre asociada a una sede.
- Mismo código de área en dos sedes = dos registros distintos.
- Al crear área: código, nombre y sede obligatorios.
- Persona y visita: área de la misma sede.

### Panel y reportes
- Dashboard: indicadores y gráficos agregados (no descarga datos personales crudos).
- Excel: requiere permiso de exportación; deja traza de auditoría.
- Todo lo que ve el admin está limitado por su alcance.

### Alcance (admin)
- Global: ve todo.
- Sede: ve su sede (incluidas áreas de esa sede).
- Facultad / Programa / Área: más restringido.
- Quien gestiona alcance no puede ampliarse a sí mismo ni otorgar un nivel superior al propio.

============================================================
7. ESTILO DE REDACCIÓN PARA WORD
============================================================

- Títulos H1 / H2 / H3 claros (en Word: Título 1, Título 2, Título 3).
- Procedimientos numerados: 1., 2., 3.
- Usar tablas para comparaciones (tipos de usuario, semáforo, FAQ corta, correos que puede recibir).
- Recuadros «Importante», «Nota», «Advertencia» (puede marcarlos con negrita o texto [IMPORTANTE]).
- Longitud objetivo: manual completo, no un resumen de 3 páginas. Cada perfil con pasos suficientes
  para un usuario nuevo sin ayuda.
- No usar emojis.
- No usar jerga de desarrollo (FK, queryset, seed, migrate, HTMX, webhook, cola, API key, etc.).
- Tono: cercano, preciso, institucional.

============================================================
8. SALIDA ESPERADA
============================================================

1) Entregue el manual completo en Markdown bien estructurado (fácil de pegar a Word),
   con marcadores [CAPTURA: …] donde corresponda.
2) Al final, una lista «Instrucciones para diagramación en Word»:
   - Estilos de título
   - Numeración de páginas
   - Tabla de contenido automática
   - Formato de portada sugerido (márgenes, logo institucional placeholder)
3) Lista de capturas pendientes numerada (para el equipo que documenta la UI real).

Empiece por la portada y continúe en orden hasta los anexos. Sea exhaustivo.
```

---

## Notas para quien genera el Word (equipo del proyecto)

1. Pegue el bloque «PROMPT PARA CLAUDE» en Claude.
2. Adjunte [`contexto-completo-sistema.md`](contexto-completo-sistema.md) si Claude lo permite.
3. Revise que no invente pantallas; valide contra el entorno real / staging.
4. Reemplace `[URL_PRODUCCION]`, contactos y logo.
5. Inserte capturas reales donde diga `[CAPTURA: …]` (prioridad nuevas: login + olvidé contraseña + confirmar nueva clave).
6. Exporte a `.docx` (Copiar desde Claude → Word, o pantalla Markdown → «Abrir con Word»).
7. En producción, confirme que los correos llegan (dominio/remitente configurados); el manual no debe mencionar proveedores.

## Relación con la documentación técnica

| Documento | Uso |
|-----------|-----|
| Este brief | Prompt para **manual de usuario** |
| [`contexto-completo-sistema.md`](contexto-completo-sistema.md) | Fuente de verdad del producto |
| [`17-integracion-resend.md`](17-integracion-resend.md) | Detalle técnico de correos (no pegar al usuario final) |
| `00`–`16`, `planes/` | Detalle técnico; **no** pegar crudo al usuario final |

**Versión del brief:** 1.1 — 2026-09-22  
**Basado en:** contexto completo (Área→Sede, alcance, login por cédula, institucionales, externo/vigilante, **correos: bienvenida / restablecer contraseña / desbloqueo**).
