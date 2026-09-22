# Sistema de Control de Salida de Equipos de Cómputo

**Universidad de Cundinamarca** — Proyecto académico 2026-II

Aplicación web para registrar equipos de cómputo de la comunidad académica, generar pases QR y verificar salidas en portería, con roles y permisos dinámicos, multi-sede y panel de administración interno.

---

## Stack

| Capa | Tecnología |
|------|------------|
| Backend / UI | Django 5.1 (templates) + HTMX |
| Base de datos | PostgreSQL |
| Estilos | CSS propio (sistema de diseño institucional v2) |
| QR | `qrcode` + Pillow |
| Reportes Excel | XlsxWriter (gráficos nativos) |
| Estáticos en producción | WhiteNoise |
| Despliegue | Render (Docker + Gunicorn) — [instructivo](contexto/operaciones/despliegue-render.md) |

---

## Requisitos

- Python 3.11+
- PostgreSQL 14+ (recomendado 17)
- Cuenta con privilegios para crear la base `sistema_control` (o el nombre definido en `.env`)

---

## Instalación rápida

```bash
# 1. Clonar / entrar al proyecto
cd "sistema de control"

# 2. Entorno virtual
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# Linux / macOS
# source .venv/bin/activate

# 3. Dependencias
pip install -r requirements.txt

# 4. Variables de entorno
copy .env.example .env   # o crear .env manualmente (ver abajo)
# Editar DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

# 5. Migraciones y datos iniciales
python manage.py migrate
python manage.py seed_data

# 6. Servidor de desarrollo
python manage.py runserver
```

Abrir: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## Variables de entorno (`.env`)

Crear un archivo `.env` en la raíz (no se versiona). Ejemplo:

```env
DEBUG=True
SECRET_KEY=cambiar-en-produccion
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=sistema_control
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
```

---

## Acceso inicial (seed MVP)

Tras `python manage.py seed_data`:

| Perfil | Usuario | Contraseña | Uso |
|--------|---------|------------|-----|
| Administrador | `admin` | `Udec2026!Admin` | Panel, catálogos, inventario y control de salida |

### Catálogos cargados

- **Sedes (7):** Fusagasugá, Girardot, Ubaté, Chía, Facatativá, Soacha, Zipaquirá  
- **Facultades (7)** y **programas (45)** según catálogo institucional  
- **Áreas (8):** CGCA, Tesorería, ISU, CTeI, Internacionalización, Bienestar, Dir. Administrativa, Admisiones  
- **Tipos de vínculo (todos activos):** gestor_administrativo, creador_oportunidades, gestor_conocimiento, egresado  
- **Roles activos:** Administrador del sistema, Miembro de la comunidad académica  

> Fuente: `apps/accounts/management/commands/seed_organizacion_data.py` (Excel en `data/`). No se cargan usuarios/equipos de demostración.

---

## Módulos (apps)

| App | Responsabilidad |
|-----|-----------------|
| `accounts` | Usuario, roles, permisos, login, registro, perfil |
| `organizacion` | Sedes, facultades, programas, áreas |
| `personas` | Personas y tipos de vínculo |
| `equipos` | Inventario, QR, mis equipos |
| `control_acceso` | Escaneo en portería, movimientos, alertas |
| `panel` | Administración interna (personas, usuarios, roles) |

---

## Estructura del repositorio

```
sistema de control/
├── apps/                 # Dominios de negocio
├── config/               # settings, urls, wsgi
├── templates/            # Plantillas Django
├── static/               # CSS / JS fuente
├── contexto/             # Documentación y planes del proyecto
├── Dockerfile            # Imagen de producción
├── docker-compose.yml    # Prod / web (canónico servidor; sync Resend)
├── docker-compose.prod.yml  # Local: web + Postgres + Redis + worker
├── render.yaml           # Blueprint Render (DB + Redis + web + worker)
├── manage.py
├── requirements.txt
└── README.md
```

La documentación de arquitectura, negocio, diseño e implementación vive en **[`contexto/`](contexto/README.md)**.

---

## Comandos útiles

```bash
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py collectstatic
python manage.py test
docker compose up --build   # prueba local del stack de producción
```

---

## Despliegue (Render)

Guía paso a paso (cuenta, GitHub, Blueprint, base de datos, variables, seed):

**[`contexto/operaciones/despliegue-render.md`](contexto/operaciones/despliegue-render.md)**

---

## UI responsive

La interfaz incluye navegación offcanvas en móvil (≤1023px), grids adaptativos en listados/formularios/detalles y tablas con scroll horizontal. Detalle del plan: [`contexto/planes/sistema-responsive-completo.md`](contexto/planes/sistema-responsive-completo.md).

---

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [`contexto/contexto-completo-sistema.md`](contexto/contexto-completo-sistema.md) | **Contexto completo vigente** (punto de entrada) |
| [contexto/README.md](contexto/README.md) | Índice maestro: rectores, planes y operaciones |
| [`09-guia-diseno-ux-ui.md`](contexto/09-guia-diseno-ux-ui.md) | Guía completa de diseño: colores, tipografía, layout, responsive |
| `contexto/00`–`12` | Arquitectura, negocio, datos, UX, registro, panel, lógica, seguridad, reportes |
| `contexto/walkthrough.md` | Resumen de implementación |
| [`contexto/planes/`](contexto/planes/) | Planes de ejecución (features / refactors) |
| [`contexto/operaciones/`](contexto/operaciones/) | Procedimientos (incidentes), backups y [despliegue Render](contexto/operaciones/despliegue-render.md) |

---

## Licencia y uso

Proyecto académico de la Universidad de Cundinamarca. Uso interno / educativo según las políticas de la institución.
