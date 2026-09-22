# Despliegue en Render (paso a paso)

**Estado:** Vigente  
**Fecha:** 2026-09-21  
**Repo:** [https://github.com/AlejoSasto/sistema_control_equipos](https://github.com/AlejoSasto/sistema_control_equipos)  
**Arquitectura:** monolito Django (Gunicorn + WhiteNoise) + PostgreSQL

Este instructivo asume que **nunca has usado Render**. Al terminar tendrás una URL pública `https://….onrender.com` con la base de datos migrada.

---

## Qué vas a lograr

```text
GitHub (rama main)
        │
        ▼
Render Blueprint (render.yaml)
   ┌────────────────┐
   │ PostgreSQL     │  ← se crea primero
   └────────┬───────┘
            │ DATABASE_URL
            ▼
   ┌────────────────┐
   │ Web (Docker)   │  ← migrate + collectstatic + gunicorn
   └────────────────┘
            │
            ▼
   https://sistema-control-web.onrender.com
```

Archivos del repo que hacen posible el deploy (ya deben estar en `main`):

| Archivo | Función |
|---------|---------|
| `Dockerfile` | Imagen de producción |
| `entrypoint.sh` | Migraciones, estáticos y Gunicorn |
| `render.yaml` | Blueprint: DB + Web |
| `docker-compose.yml` | Prueba local opcional |
| `config/settings.py` | `DATABASE_URL`, HTTPS, CSRF, WhiteNoise |

---

## Prerrequisitos

1. Cuenta en [GitHub](https://github.com) con acceso al repo `AlejoSasto/sistema_control_equipos`.
2. Los cambios de despliegue **ya subidos** a la rama `main` (si acabas de generarlos en local: `git push origin main`).
3. Cuenta en [Render](https://render.com) (plan Free alcanza para probar).
4. *(Opcional)* [Docker Desktop](https://www.docker.com/products/docker-desktop/) si quieres probar el mismo contenedor en tu PC antes de la nube.

---

## Paso 1 — Cuenta y login en Render

1. Abre [https://dashboard.render.com](https://dashboard.render.com).
2. Elige **Sign Up** (o **Log In** si ya tienes cuenta).
3. Recomendado: **Continue with GitHub** (así conectas el repo más fácil).
4. Acepta permisos básicos de Render sobre tu cuenta GitHub.

Quedas en el **Dashboard** de Render (lista de servicios, al inicio vacía).

---

## Paso 2 — Conectar el repositorio de GitHub

1. En el dashboard, ve a **Account Settings** → **Git** (o, al crear el Blueprint, Render te pedirá autorizar).
2. Autoriza a Render para ver repositorios de tu usuario/organización.
3. Asegúrate de que `sistema_control_equipos` aparezca en la lista de repos permitidos.
   - Si el repo es privado, concede acceso explícito a ese repositorio en la app de GitHub de Render.

---

## Paso 3 — Empezar por la base de datos (Blueprint)

La forma más simple es usar el archivo `render.yaml` del repo. Render crea **primero PostgreSQL** y luego el servicio Web, inyectando `DATABASE_URL` automáticamente.

1. En el dashboard: **New +** → **Blueprint**.
2. Conecta / selecciona el repo **`AlejoSasto/sistema_control_equipos`**.
3. Rama: **`main`**.
4. Render detecta `render.yaml`. Revisa el resumen:
   - Base de datos: `sistema-control-db`
   - Servicio web: `sistema-control-web` (Docker)
5. Pulsa **Apply** (o equivalente para crear los recursos).

> **Nota sobre planes:** si Render ya no ofrece PostgreSQL Free en tu cuenta, elige el plan de pago más bajo al crear la DB. El plan Free del Web Service suele seguir existiendo, con la limitación de que el servicio puede “dormir” tras inactividad.

### Variables que te pedirá al aplicar (`sync: false`)

Render generará `SECRET_KEY` solo. Tú debes completar:

| Variable | Valor a pegar (con el nombre del servicio del YAML) |
|----------|------------------------------------------------------|
| `ALLOWED_HOSTS` | `sistema-control-web.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://sistema-control-web.onrender.com` |

> Si más adelante cambias el nombre del servicio en Render, actualiza estas dos variables al nuevo hostname.

`DATABASE_URL` y `DEBUG=False` ya vienen del Blueprint; no las inventes a mano.

### Alternativa manual (si no usas Blueprint)

1. **New +** → **PostgreSQL** → crea `sistema-control-db` (anota el *Internal Database URL*).
2. **New +** → **Web Service** → repo → **Docker** → Dockerfile en la raíz.
3. En **Environment** pega `DATABASE_URL` = Internal Database URL, más `DEBUG=False`, `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` como arriba.

---

## Paso 4 — Primer deploy

1. Abre el servicio **`sistema-control-web`**.
2. Pestaña **Events** / **Logs**:
   - Build de la imagen Docker.
   - `Aplicando migraciones...`
   - `Recolectando estáticos...`
   - `Iniciando Gunicorn...`
3. Cuando el estado sea **Live**, abre la URL pública:
   - `https://sistema-control-web.onrender.com`
4. Deberías ver la pantalla de login (o redirección al kiosco → login).

### Si el health check falla

- Confirma `ALLOWED_HOSTS` exactamente sin `https://` ni barra final.
- Confirma `CSRF_TRUSTED_ORIGINS` **con** `https://` y sin barra final.
- Revisa logs por errores de conexión a Postgres (`DATABASE_URL`).

---

## Paso 5 — Datos iniciales (`seed_data`)

El `entrypoint` del contenedor ejecuta automáticamente, en cada arranque:

1. `migrate`
2. **`seed_data`** (catálogos, roles, vínculos canónicos, sedes, **áreas por sede**, admin)
3. `collectstatic`
4. Gunicorn

No hace falta Shell para el primer login. Tras un deploy **Live**:

1. Abre la URL del servicio.
2. Entra con:
   - Usuario: `admin`
   - Contraseña: `Udec2026!Admin` (solo la primera vez que se crea el admin; re-deploys posteriores **no** la resetean).
3. En un entorno real, **cambia la contraseña** del administrador desde el panel.

El seed desactiva tipos de vínculo legado de migraciones antiguas (`estudiante`, `graduado`, `administrativo`, `docente`) y deja solo el catálogo canónico.

**Áreas:** cada código del catálogo se upserta **por sede** (`update_or_create(sede, codigo)`). Tras `organizacion.0007` hay una fila de área por sede (p. ej. CGCA en Ubaté y en Fusa). En logs debe aparecer algo como `56 áreas upsert (7 sedes × 8 códigos…)` — **no** el error `MultipleObjectsReturned`. Detalle: [`../planes/area-pertenece-sede.md`](../planes/area-pertenece-sede.md).

Si necesitas forzar el seed a mano (Shell o local):

```bash
python manage.py seed_data
```

---

## Paso 6 — Deploys siguientes

1. Haz cambios en local y súbelos:

```bash
git add .
git commit -m "tu mensaje"
git push origin main
```

2. Render detecta el push a `main` y vuelve a construir el Docker (auto-deploy).
3. Para forzar: servicio → **Manual Deploy** → **Deploy latest commit**.

Cada arranque vuelve a ejecutar `migrate`, `seed_data` y `collectstatic`.

**Seed seguro en producción:**

- Upsert de catálogos (sedes, facultades, programas, áreas, permisos, roles, vínculos canónicos).
- **No** resetea la contraseña de `admin` si ya existe.
- **No** desactiva sedes/programas/áreas/vínculos creados fuera del seed.
- Solo borra filas de **demo MVP** (listas fijas de username/documento/serial).
- Asegura alcance `GLOBAL` y permisos nuevos (p. ej. `usuarios.gestionar_alcance`) para `admin`.

Migraciones de alcance (`organizacion.0005`–`0006`, `accounts.0011`) son aditivas: crean tablas/permisos y asignan GLOBAL a admins existentes; no eliminan personas, equipos ni movimientos.

Migración `organizacion.0007_area_sede`: hace obligatoria la sede en `Area`, clona códigos por sede y remapea FKs. Idempotente una vez aplicada; el seed posterior upserta por `(sede, codigo)`.

### Blueprint (`render.yaml`) — MVP web + Resend sync

El blueprint MVP incluye **Postgres + web Docker**. Los correos se envían **en el mismo request** (`EMAIL_USE_CELERY=False`). **No** se crea Redis ni worker Celery en este modo.

**Variables de correo** (servicio web; Sensitive donde aplique):

| Variable | Valor |
|----------|--------|
| `RESEND_MOCK_MODE` | `False` |
| `EMAIL_USE_CELERY` | `False` |
| `CELERY_TASK_ALWAYS_EAGER` | `True` |
| `RESEND_API_KEY` | API key `re_...` |
| `RESEND_FROM_EMAIL` | Remitente con dominio verificado |
| `RESEND_FROM_NAME` | p. ej. `Control de Equipos UCundinamarca` |
| `RESEND_WEBHOOK_SECRET` | `whsec_...` (opcional pero recomendado) |
| `PUBLIC_BASE_URL` | `https://sistema-control-web.onrender.com` (sin `/` final) |

**Fase 2 (opcional):** Key Value + worker Celery + `EMAIL_USE_CELERY=True` + `CELERY_TASK_ALWAYS_EAGER=False`. Ver [17-integracion-resend.md](../17-integracion-resend.md).

**Webhook post-deploy (opcional; no bloquea el envío):**

1. Resend → Webhooks → URL `https://<servicio>.onrender.com/webhooks/resend/`
2. Eventos: `email.delivered`, `email.bounced`, `email.complained`
3. Copiar signing secret a `RESEND_WEBHOOK_SECRET`

---

## Paso 7 — Checklist post-deploy

- [ ] La URL responde por **HTTPS**
- [ ] Login funciona (CSRF y `ALLOWED_HOSTS` correctos)
- [ ] Estáticos (CSS) se ven bien (WhiteNoise)
- [ ] Login `admin` / `Udec2026!Admin` OK (seed automático en entrypoint); cambiar contraseña en entorno real
- [ ] Topbar muestra badge «Alcance: Global» para `admin`
- [ ] Ficha de usuario: sección Alcance visible con `usuarios.gestionar_alcance`
- [ ] Registro muestra sedes y tipos canónicos (no Estudiante/Graduado legado)
- [ ] En logs del seed: `áreas upsert (… sedes × … códigos…)` sin `MultipleObjectsReturned`
- [ ] Panel Organización → Áreas: columna Sede; mismo código puede repetirse en sedes distintas
- [ ] Backups: ver [checklist-backup-restauracion.md](checklist-backup-restauracion.md)
- [ ] Incidentes: ver [procedimiento-incidentes-seguridad.md](procedimiento-incidentes-seguridad.md)
- [ ] Env correo: `EMAIL_USE_CELERY=False`, `CELERY_TASK_ALWAYS_EAGER=True`, Resend real, `PUBLIC_BASE_URL`
- [ ] Prueba: registro envía bienvenida; “Olvidé mi contraseña” entrega enlace usable
- [ ] (Opcional) Webhook Resend → `/webhooks/resend/` responde 200

---

## Opcional — Probar el mismo stack en local con Docker

Útil antes de subir a la nube o para depurar el Dockerfile.

1. Instala y arranca **Docker Desktop**.
2. En la raíz del proyecto:

```bash
docker compose up --build
```

3. Abre [http://localhost:8000](http://localhost:8000).
4. Postgres local queda en el puerto `5432` (usuario/clave `postgres` / `postgres` según `docker-compose.yml`).
5. Con `EMAIL_USE_CELERY=False` los correos salen en el proceso web (mock si `RESEND_MOCK_MODE=True`). Redis/worker del compose son opcionales (fase 2).
6. El seed ya corre en el `entrypoint` al subir el contenedor. Si quieres repetirlo:

```bash
docker compose exec web python manage.py seed_data
```

7. Detener: `Ctrl+C` y luego `docker compose down` (añade `-v` solo si quieres borrar el volumen de la DB).

> En compose local `DEBUG=True` para evitar redirección HTTPS forzada. En Render `DEBUG=False`.

---

## Problemas frecuentes

| Síntoma | Qué revisar |
|---------|-------------|
| `DisallowedHost` | `ALLOWED_HOSTS` debe ser el hostname sin esquema (`sistema-control-web.onrender.com`) |
| Error CSRF al login | `CSRF_TRUSTED_ORIGINS=https://sistema-control-web.onrender.com` |
| Build falla en `pip install` | Logs del build; confirma que `requirements.txt` está en la raíz |
| App no arranca / migrate error | `DATABASE_URL` enlazada a la DB del Blueprint; DB en estado Available |
| Estáticos 404 / sin CSS | Logs de `collectstatic`; WhiteNoise activo con `DEBUG=False` |
| Tarda mucho o “duerme” | Plan Free: el servicio puede dormir tras inactividad; la primera petición despierta (frío) |
| Login falla / sedes vacías / tipos "Estudiante" | Redeploy con seed en entrypoint; en logs debe aparecer `Cargando catálogos institucionales` |
| Seed cae con `MultipleObjectsReturned` en Area | Código antiguo upsertaba solo por `codigo`; debe upsertar por `(sede, codigo)`. Ver plan área-sede |
| Admin no ve datos / listados vacíos | Verificar alcance GLOBAL (`migrate` 0005 + seed); en ficha de usuario o shell: `admin.alcances` |
| Avisos CSP de `*.map` en consola | Cosmético (source maps); no bloquean login. `connect-src` ya incluye jsdelivr |

---

## Dominio institucional (opcional)

En el servicio web → **Settings** → **Custom Domains**, añade el dominio de la universidad y apunta el DNS según indique Render. Después actualiza `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` con ese dominio.

---

## Referencias

- Blueprint: [`render.yaml`](../../render.yaml) en la raíz del repo
- Variables de ejemplo: [`.env.example`](../../.env.example)
- Contexto del sistema: [`../contexto-completo-sistema.md`](../contexto-completo-sistema.md)
