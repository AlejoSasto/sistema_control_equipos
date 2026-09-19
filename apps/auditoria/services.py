"""Helpers para registrar cambios sensibles sin filtrar secretos en logs."""

from __future__ import annotations

import logging
from typing import Any

from .models import AuditoriaCambio

logger = logging.getLogger("auditoria")

CAMPOS_SENSIBLES = frozenset(
    {
        "password",
        "password1",
        "password2",
        "token_qr",
        "secret",
        "token",
    }
)


def _sanitizar(valor: Any) -> Any:
    if isinstance(valor, dict):
        return {
            k: ("***" if k.lower() in CAMPOS_SENSIBLES else _sanitizar(v))
            for k, v in valor.items()
        }
    if isinstance(valor, list):
        return [_sanitizar(v) for v in valor]
    return valor


def _client_ip(request) -> str:
    if request is None:
        return ""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45]
    return (request.META.get("REMOTE_ADDR") or "")[:45]


def registrar_cambio(
    *,
    usuario=None,
    entidad: str,
    entidad_id=None,
    accion: str,
    detalle: dict | None = None,
    request=None,
    ip_origen: str = "",
) -> AuditoriaCambio:
    """Persiste un registro en auditoria_cambio con detalle sanitizado."""
    detalle_limpio = _sanitizar(detalle or {})
    ip = ip_origen or _client_ip(request)
    registro = AuditoriaCambio.objects.create(
        usuario=usuario,
        entidad=entidad,
        entidad_id=entidad_id,
        accion=accion,
        detalle=detalle_limpio,
        ip_origen=ip,
    )
    logger.info(
        "cambio entidad=%s id=%s accion=%s usuario=%s",
        entidad,
        entidad_id,
        accion,
        getattr(usuario, "pk", None),
    )
    return registro
