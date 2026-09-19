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
| Estáticos en producción | WhiteNoise |

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

## Accesos de demostración (seed)

Tras `python manage.py seed_data`:

| Perfil | Usuario | Contraseña | Uso |
|--------|---------|------------|-----|
| Administrador | `admin` | `admin123` | Panel, catálogos, inventario |
| Celador | `celador1` | `celador123` | Kiosco de escaneo QR |
| Docente | `docente1` | `docente123` | Mi perfil / mis equipos |

> Estas credenciales son solo para entorno local de desarrollo. No usarlas en producción.

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
```

---

## UI responsive

La interfaz incluye navegación offcanvas en móvil (≤1023px), grids adaptativos en listados/formularios/detalles y tablas con scroll horizontal. Detalle del plan: [`contexto/planes/sistema-responsive-completo.md`](contexto/planes/sistema-responsive-completo.md).

---

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [contexto/README.md](contexto/README.md) | Índice y estado de todos los planes |
| `00`–`08` | Arquitectura, negocio, datos, UX, registro, panel, lógica |
| `walkthrough.md` | Resumen de implementación |
| `planes/` | Planes de ejecución (responsive, etc.) |

---

## Licencia y uso

Proyecto académico de la Universidad de Cundinamarca. Uso interno / educativo según las políticas de la institución.
