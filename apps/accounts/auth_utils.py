"""Helpers de autenticación: username institucional y resolución de identificador."""

from __future__ import annotations

from accounts.models import Usuario

DOMINIO_INSTITUCIONAL = "@ucundinamarca.edu.co"


def username_desde_correo(correo: str, tipo_vinculo=None) -> str:
    """
    Deriva el username a partir del correo.

    - Si el vínculo exige dominio institucional y el correo lo cumple → parte local.
    - Si no hay vínculo pero el correo termina en @ucundinamarca.edu.co (panel) → parte local.
    - En cualquier otro caso → correo completo.
    """
    correo = (correo or "").strip().lower()
    if not correo or "@" not in correo:
        return correo

    local, _, dominio = correo.partition("@")
    dominio_con_arroba = f"@{dominio}"

    if tipo_vinculo is not None:
        requerido = (getattr(tipo_vinculo, "dominio_correo_requerido", None) or "").strip().lower()
        if requerido and correo.endswith(requerido):
            return local
        return correo

    if dominio_con_arroba == DOMINIO_INSTITUCIONAL or correo.endswith(DOMINIO_INSTITUCIONAL):
        return local
    return correo


def resolver_usuario_por_identificador(identificador: str) -> Usuario | None:
    """
    Resuelve un Usuario activo por username, email o número de documento (cédula).
    Orden: username → email → Persona.numero_documento → persona.usuario.
    """
    valor = (identificador or "").strip()
    if not valor:
        return None

    qs = Usuario.objects.filter(activo=True, is_active=True)

    user = qs.filter(username__iexact=valor).first()
    if user:
        return user

    user = qs.filter(email__iexact=valor).first()
    if user:
        return user

    from personas.models import Persona

    persona = (
        Persona.objects.filter(numero_documento=valor, activo=True)
        .select_related("usuario")
        .first()
    )
    if persona is None:
        return None
    usuario = getattr(persona, "usuario", None)
    if usuario and usuario.activo and usuario.is_active:
        return usuario
    return None
