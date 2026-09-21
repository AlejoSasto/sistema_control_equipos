"""
Django settings for Sistema de Control de Ingreso/Salida de Equipos.
Universidad de Cundinamarca
"""

from pathlib import Path
import os
import sys
from urllib.parse import parse_qs, unquote, urlparse

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

sys.path.insert(0, str(BASE_DIR / "apps"))


def _database_from_url(url: str) -> dict:
    """Convierte DATABASE_URL (Render/Docker) al dict de Django."""
    parsed = urlparse(url)
    name = unquote(parsed.path.lstrip("/"))
    if not name:
        raise RuntimeError("DATABASE_URL no incluye nombre de base de datos.")
    config = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": name,
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or "5432"),
    }
    query = parse_qs(parsed.query)
    sslmode = (query.get("sslmode") or [None])[0]
    if sslmode:
        config["OPTIONS"] = {"sslmode": sslmode}
    return config


DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "t")

_INSECURE_DEV_KEY = "django-insecure-ucundinamarca-sistema-control-secret-key-2026"
SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = _INSECURE_DEV_KEY
    else:
        raise RuntimeError(
            "SECRET_KEY es obligatorio cuando DEBUG=False. "
            "Defínalo en variables de entorno o en el archivo .env."
        )
elif not DEBUG and SECRET_KEY.startswith("django-insecure-"):
    raise RuntimeError("No use una SECRET_KEY insegura en producción (DEBUG=False).")

_allowed_raw = os.environ.get("ALLOWED_HOSTS", "").strip()
if _allowed_raw:
    ALLOWED_HOSTS = [h.strip() for h in _allowed_raw.split(",") if h.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
else:
    raise RuntimeError(
        "ALLOWED_HOSTS es obligatorio cuando DEBUG=False. "
        "Ejemplo: ALLOWED_HOSTS=sistema-control-web.onrender.com"
    )
if DEBUG and "testserver" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("testserver")

_csrf_raw = os.environ.get("CSRF_TRUSTED_ORIGINS", "").strip()
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_raw.split(",") if o.strip()]

ADMIN_URL = os.environ.get("ADMIN_URL", "admin/").strip().strip("/") + "/"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "axes",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "accounts",
    "organizacion",
    "personas",
    "equipos",
    "control_acceso",
    "panel",
    "auditoria",
    "reportes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "axes.middleware.AxesMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "config.middleware.ContentSecurityPolicyMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

_database_url = os.environ.get("DATABASE_URL", "").strip()
if _database_url:
    DATABASES = {"default": _database_from_url(_database_url)}
else:
    _db_password = os.environ.get("DB_PASSWORD", "")
    if not DEBUG and not _db_password:
        raise RuntimeError(
            "Defina DATABASE_URL o DB_PASSWORD cuando DEBUG=False."
        )
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "sistema_control"),
            "USER": os.environ.get("DB_USER", "postgres"),
            "PASSWORD": _db_password if _db_password else ("12345678" if DEBUG else ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }

AUTH_USER_MODEL = "accounts.Usuario"

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

if not DEBUG:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "control_acceso:escanear"
LOGOUT_REDIRECT_URL = "accounts:login"

SESSION_COOKIE_AGE = 7200
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = True
CSRF_COOKIE_HTTPONLY = False
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True

# Token de exhibición QR (segundos)
QR_DISPLAY_TOKEN_MAX_AGE = int(os.environ.get("QR_DISPLAY_TOKEN_MAX_AGE", "300"))

# Dashboard administrador (doc 13)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "sistema-control-dashboard",
    }
}
DASHBOARD_ALERTA_UMBRAL = float(os.environ.get("DASHBOARD_ALERTA_UMBRAL", "0.05"))
DASHBOARD_CACHE_TTL = int(os.environ.get("DASHBOARD_CACHE_TTL", "45"))
DASHBOARD_CACHE_TTL_ESTRUCTURAL = int(os.environ.get("DASHBOARD_CACHE_TTL_ESTRUCTURAL", "300"))

# Rate limiting / Axes
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # horas
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_RESET_ON_SUCCESS = True

RATELIMIT_ENABLE = True
RATELIMIT_VIEW = "config.ratelimit.ratelimited_view"

# Contacto ARCO (Ley 1581)
DATOS_PERSONALES_CONTACTO = os.environ.get(
    "DATOS_PERSONALES_CONTACTO",
    "protecciondatos@ucundinamarca.edu.co",
)

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.security": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "axes": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "auditoria": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "accounts.auth": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# Evitar flaky tests por Axes/ratelimit en suite unitaria
if "test" in sys.argv:
    AXES_ENABLED = False
    RATELIMIT_ENABLE = False
