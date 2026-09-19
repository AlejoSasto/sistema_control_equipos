# 11 — Plan de Seguridad (ISO/IEC 27001 + OWASP)

> Aplica sobre la arquitectura ya definida en `00`–`10`: monolito Django/PostgreSQL, roles/permisos dinámicos, QR interno, kiosco de portería, panel admin, y una proyección de 20.000 usuarios. Este documento asume que el sistema maneja **datos personales** (documento, nombre, correo, foto) de personas naturales en Colombia, por lo que también se referencia la Ley 1581 de 2012 (Habeas Data) donde aplica.

## 1. Alcance y activos a proteger

| Activo | Por qué es crítico |
|---|---|
| Datos personales de `Persona` (documento, foto, correo) | Sujeto a Ley 1581 de 2012; su fuga es un incidente reportable |
| `token_qr` de cada equipo | Es la credencial de verificación física — su compromiso permite suplantar la salida de un equipo |
| Credenciales de `Usuario` (especialmente `admin_sistema`) | Compromiso total del sistema si se vulnera una cuenta administrativa |
| Base de datos PostgreSQL | Contiene todo lo anterior; su disponibilidad es tan crítica como su confidencialidad |
| Kiosco de portería | Es un endpoint físico de alto tráfico; su indisponibilidad detiene el control real de salida |
| Repositorio de código y variables de entorno (`.env`, `SECRET_KEY`) | Su fuga compromete el sistema completo, incluida la firma de sesiones |

## 2. Marco de referencia aplicado

- **ISO/IEC 27001:2022**, Anexo A, para la gestión del riesgo y los controles organizacionales, de personas, físicos y tecnológicos.
- **OWASP Top 10 (2021)** como checklist técnico de vulnerabilidades web.
- **OWASP ASVS** (Application Security Verification Standard) como referencia de nivel de rigor esperado — para un sistema con datos personales de 20.000 personas, se apunta como mínimo a **ASVS Nivel 2**.
- **Ley 1581 de 2012 / Decreto 1377 de 2013 (Colombia)** para el tratamiento de datos personales.

## 3. Modelo de amenazas específico del sistema

| Amenaza | Vector | Mitigación principal |
|---|---|---|
| Suplantación vía captura de pantalla del QR | Alguien fotografía el QR de otra persona y lo reenvía | Verificación visual foto+nombre en kiosco (ya diseñada) + expiración/rotación del `token_qr` (ver sección 6.1) |
| IDOR (Insecure Direct Object Reference) | Un usuario autenticado cambia el `id` en la URL (`/panel/personas/57/editar`) y accede a datos de otra persona | Toda vista debe verificar propiedad/permiso, nunca confiar solo en que el `id` "se ve válido" |
| Escalado de privilegios | Un usuario con rol `miembro_comunidad` intenta acceder a `/panel/roles/` manipulando la URL directamente | Verificación de permiso en el servidor en cada vista, no solo ocultar el enlace en el menú |
| Fuerza bruta sobre login | Intentos masivos de contraseña sobre cuentas conocidas (ej. `admin`) | Rate limiting + bloqueo temporal tras N intentos fallidos |
| Inyección SQL | Consultas construidas con strings concatenados en vez del ORM | Uso exclusivo del ORM de Django; prohibir SQL crudo sin parametrización |
| XSS almacenado | Un campo de texto libre (ej. `observacion` en `Movimiento`) contiene un script | Autoescape de Django (activo por defecto) + `Content-Security-Policy` como capa adicional |
| CSRF | Formulario malicioso en otro sitio que envía una acción autenticada | `{% csrf_token %}` en todos los formularios (verificar que ninguna vista lo desactive) |
| Fuga de secretos | `SECRET_KEY` o credenciales de base de datos expuestas en el repositorio | Variables de entorno (`.env` fuera de git), rotación de secretos si se detecta exposición |
| Denegación de servicio en el kiosco | Ráfaga de peticiones (accidental o maliciosa) al endpoint de escaneo | Rate limiting específico en esa ruta, con margen suficiente para uso legítimo en horas pico |
| Carga de archivos maliciosos | Foto de persona subida con extensión/contenido manipulado | Validación de tipo MIME real (no solo extensión), límite de tamaño, almacenamiento fuera de la raíz ejecutable |
| Ataques a dependencias desactualizadas | Una librería de Python o de Bootstrap con CVE conocido | Escaneo automático de dependencias en CI (sección 7) |

## 4. Mapeo a OWASP Top 10 (2021)

| Categoría OWASP | Aplicación al sistema | Acción concreta |
|---|---|---|
| A01 – Broken Access Control | Riesgo más alto dado el modelo de roles dinámico | Middleware/decorador de verificación de permiso en **cada** vista sensible; pruebas automatizadas que confirmen 403 para roles sin permiso |
| A02 – Cryptographic Failures | Contraseñas, `token_qr`, cookies de sesión | Hasher `Argon2` para contraseñas (mejor que PBKDF2 por defecto), HTTPS obligatorio, cookies `Secure`+`HttpOnly` |
| A03 – Injection | Formularios de registro, filtros de búsqueda | ORM de Django exclusivamente; sanitización de inputs de búsqueda |
| A04 – Insecure Design | Flujo de autorregistro externo (`06`) | Validación de dominio de correo en backend (ya definida), límite de intentos de registro por IP |
| A05 – Security Misconfiguration | Configuración de producción de Django | `DEBUG=False`, `ALLOWED_HOSTS` explícito, cabeceras de seguridad (sección 6.2), Django Admin restringido |
| A06 – Vulnerable and Outdated Components | Dependencias Python/JS | `pip-audit` / `safety` en CI, actualización periódica programada |
| A07 – Identification and Authentication Failures | Login, gestión de sesión | Política de contraseñas, bloqueo tras intentos fallidos, MFA para `admin_sistema` (sección 6.3), expiración de sesión por inactividad |
| A08 – Software and Data Integrity Failures | CDN de Bootstrap/fuentes, pipeline de despliegue | Atributos `integrity`/`crossorigin` en scripts CDN (ya previsto en `10`), control de acceso al pipeline de CI/CD |
| A09 – Security Logging and Monitoring Failures | Sin auditoría formal aún (pendiente desde `02`) | Tabla `auditoria_cambio` pasa de "mejora futura" a **requisito de esta fase** (sección 6.4); alertas ante patrones anómalos |
| A10 – Server-Side Request Forgery | Bajo riesgo actual (no hay llamadas salientes a URLs definidas por el usuario) | Revisar si se agregan integraciones futuras (ej. verificación de correo) que acepten URLs externas |

## 5. Mapeo a ISO/IEC 27001 — Anexo A (controles relevantes)

| Cláusula | Control | Aplicación concreta |
|---|---|---|
| A.5.1 | Políticas de seguridad de la información | Redactar una política breve de seguridad y tratamiento de datos, aprobada por la universidad |
| A.5.9 | Inventario de activos | El propio sistema ya es un inventario de activos físicos (equipos); se extiende a activos de información (bases de datos, backups, credenciales) |
| A.5.15 | Control de acceso | Ya cubierto por el modelo Rol/Permiso (`01`), pero debe documentarse formalmente como política |
| A.5.23 | Seguridad en servicios en la nube | Revisar el acuerdo de nivel de servicio y las prácticas de seguridad del proveedor de hosting (Railway/Render) |
| A.5.24–A.5.28 | Gestión de incidentes | Definir un procedimiento mínimo: quién se entera, cómo se contiene, cómo se notifica (relevante si hay fuga de datos personales, por la Ley 1581) |
| A.5.34 | Privacidad y protección de datos personales | Política de tratamiento de datos personales, consentimiento informado en el registro externo, derechos ARCO (acceso, rectificación, cancelación, oposición) |
| A.6.3 | Concienciación y formación | Capacitación breve a celadores y administradores sobre manejo de credenciales y datos personales |
| A.7.8 / A.7.9 | Seguridad de equipos y activos fuera de las instalaciones | Relevante para los propios equipos institucionales que el sistema controla — política de uso aceptable |
| A.8.3 | Restricción de acceso a la información | Aplicado vía roles/permisos + principio de mínimo privilegio (ej. `permisos.ver` de solo lectura ya diseñado en `07`) |
| A.8.8 | Gestión de vulnerabilidades técnicas | Escaneo periódico de dependencias y del código (sección 7) |
| A.8.12 | Prevención de fuga de datos | Enmascarado de datos sensibles en logs (nunca loguear contraseñas, `token_qr` completo, ni documento completo) |
| A.8.13 | Copias de seguridad | Backups automáticos de PostgreSQL, cifrados, con prueba periódica de restauración |
| A.8.15 | Registro (logging) | Tabla de auditoría (sección 6.4) + logs de acceso/autenticación con retención definida |
| A.8.24 | Uso de criptografía | HTTPS en todo el sistema, hash de contraseñas con Argon2, `token_qr` como UUID criptográficamente aleatorio |
| A.8.28 | Codificación segura | Revisión de código orientada a OWASP antes de cada release; uso exclusivo del ORM |

## 6. Controles técnicos concretos a implementar en Django

### 6.1 Endurecer el `token_qr` (ajuste de seguridad sobre `02`/`06`)

- Mantener el `token_qr` como UUID4 permanente para identificar el equipo, pero **añadir un token de exhibición de corta duración** que es lo que realmente se codifica en el QR mostrado en pantalla (ej. válido 2-5 minutos, firmado con `itsdangerous`/`django.core.signing`). Esto neutraliza gran parte del riesgo de captura de pantalla reenviada, sin necesitar regenerar el QR base del equipo.
- El escaneo valida: (a) que el token de exhibición no haya expirado, (b) que corresponda a un equipo activo, (c) que la persona esté activa.

### 6.2 Cabeceras y configuración de producción (`settings.py`)

```python
DEBUG = False
ALLOWED_HOSTS = ["dominio-real-de-la-universidad.edu.co"]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
```

Además: `Content-Security-Policy` restrictiva (solo permitir los CDN ya definidos en `10` para Bootstrap/Inter/JetBrains Mono), y Django Admin (`/admin/`) restringido por IP o movido a una ruta no predecible, ya que en `07` quedó reservado solo para soporte técnico.

### 6.3 Autenticación reforzada

- **Rate limiting** en `/login` y en el endpoint de escaneo del kiosco (ej. con `django-ratelimit`): máximo N intentos por IP/usuario en una ventana de tiempo.
- **Bloqueo temporal de cuenta** tras intentos fallidos repetidos (ej. `django-axes`).
- **MFA obligatorio para el rol `admin_sistema`** — es el rol de mayor impacto si se compromete; no es necesario para `miembro_comunidad` en el MVP, pero sí debe quedar como requisito antes de escalar a 20.000 usuarios.
- **Expiración de sesión por inactividad** (`SESSION_COOKIE_AGE` razonable, ej. 2 horas para el kiosco, más largo para el resto).

### 6.4 Auditoría (pasa de "futuro" a obligatorio en esta fase)

Se formaliza la tabla `auditoria_cambio` sugerida en `02`:

| Campo | Tipo | Descripción |
|---|---|---|
| id | BIGSERIAL | PK |
| usuario_id | BIGINT FK | Quién hizo el cambio |
| entidad | VARCHAR(50) | Tabla afectada (`persona`, `rol`, `equipo`, etc.) |
| entidad_id | BIGINT | Registro afectado |
| accion | VARCHAR(20) | `crear` / `editar` / `inactivar` |
| detalle | JSONB | Qué campos cambiaron (antes/después) |
| ip_origen | VARCHAR(45) | Trazabilidad |
| timestamp | TIMESTAMP | Cuándo |

Se registran como mínimo: cambios de rol/permiso, creación/inactivación de usuarios, y cualquier acceso al panel administrativo con permiso `usuarios.administrar` o `roles.administrar`.

### 6.5 Validación de archivos (foto de persona)

- Verificar el tipo MIME real del archivo (no solo la extensión), límite de tamaño (ej. 2MB), redimensionar/recomprimir en el servidor antes de guardar.
- Almacenar fuera del directorio servido directamente por el servidor web, o en almacenamiento de objetos (S3-compatible) con URLs firmadas de corta duración.

## 7. Integración en el pipeline (CI/CD)

| Herramienta | Qué revisa | Cuándo corre |
|---|---|---|
| `bandit` | Análisis estático de código Python en busca de patrones inseguros | En cada pull request |
| `pip-audit` / `safety` | Vulnerabilidades conocidas (CVE) en dependencias de Python | En cada pull request y semanalmente |
| `npm audit` (si aplica a assets JS) | Vulnerabilidades en dependencias front-end | En cada pull request |
| OWASP ZAP (baseline scan) | Escaneo dinámico básico contra un entorno de staging | Antes de cada release a producción |
| Revisión manual de permisos | Confirmar que toda vista nueva tiene su decorador de permiso | Checklist de pull request |

## 8. Cumplimiento de datos personales (Ley 1581 de 2012)

- Publicar una **política de tratamiento de datos personales**, enlazada desde el formulario de registro externo (`06`), explicando qué datos se recogen, para qué, y por cuánto tiempo.
- Incluir **casilla de aceptación explícita** en el registro (no puede estar premarcada).
- Habilitar un mecanismo para que la persona ejerza sus **derechos ARCO** (acceso, rectificación, cancelación, oposición) — puede ser tan simple como un correo de contacto documentado, para el MVP.
- Evaluar si el volumen de datos (20.000 personas) obliga a inscribir la base de datos en el **Registro Nacional de Bases de Datos (RNBD)** de la SIC — recomendable validarlo con la oficina jurídica de la universidad.

## 9. Plan de implementación por fases

### Fase S1 — Antes de ir a producción (bloqueante)

1. Configuración de producción endurecida (sección 6.2).
2. Gestión de secretos vía variables de entorno, `.env` fuera del control de versiones.
3. HTTPS obligatorio en todo el sistema.
4. Validación de permisos en servidor confirmada con pruebas automatizadas (no solo revisión visual del menú).
5. Política de tratamiento de datos personales publicada y enlazada en el registro externo.

### Fase S2 — Corto plazo (primeras semanas de operación)

1. Rate limiting en login y en el endpoint de escaneo del kiosco.
2. Tabla de auditoría (`auditoria_cambio`) implementada y poblándose.
3. Validación reforzada de archivos subidos (fotos).
4. Escaneo de dependencias automatizado en CI (`pip-audit`/`safety`).

### Fase S3 — Antes de escalar a 20.000 usuarios

1. MFA obligatorio para `admin_sistema`.
2. Token de exhibición de corta duración para el QR (sección 6.1).
3. Prueba de penetración externa (pentest) contratada, al menos sobre login, panel admin y kiosco.
4. Prueba de restauración de backup documentada y ejecutada al menos una vez.
5. Procedimiento de gestión de incidentes documentado y socializado con el equipo.

## 10. Checklist final (resumen ejecutable)

- [x] `DEBUG=False`, `ALLOWED_HOSTS` configurado, HTTPS forzado.
- [x] Contraseñas con Argon2, MFA activo para `admin_sistema`.
- [x] Rate limiting en login y en escaneo del kiosco.
- [x] Cada vista sensible verificada por permiso, con prueba automatizada de acceso denegado.
- [x] `token_qr` de exhibición con expiración corta implementado.
- [x] Tabla `auditoria_cambio` registrando cambios de rol/permiso y acciones administrativas.
- [ ] Backups cifrados con restauración probada al menos una vez. *(checklist operativo en [`operaciones/checklist-backup-restauracion.md`](operaciones/checklist-backup-restauracion.md))*
- [x] Escaneo de dependencias y análisis estático integrados en CI.
- [x] Política de tratamiento de datos personales publicada, con casilla de consentimiento explícita.
- [x] Procedimiento de gestión de incidentes documentado. *([`operaciones/procedimiento-incidentes-seguridad.md`](operaciones/procedimiento-incidentes-seguridad.md))*
