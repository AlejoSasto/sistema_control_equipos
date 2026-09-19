import re
import uuid


def normalizar_codigo_escaneado(raw: str) -> str:
    """
    Limpia el código tipificado por pistola HID (p. ej. Zebra DS22).

    - Quita espacios y CR/LF del Enter de la pistola.
    - Corrige apóstrofos por guiones (layout teclado US frente a SO en español).
    - Si hay exactamente 32 hex, reconstruye el UUID canónico.
    """
    if not raw:
        return ""

    codigo = raw.strip().strip("\r\n")
    codigo = codigo.replace("'", "-")

    try:
        return str(uuid.UUID(codigo))
    except (ValueError, AttributeError):
        pass

    hex_only = re.sub(r"[^0-9a-fA-F]", "", codigo)
    if len(hex_only) == 32:
        try:
            return str(uuid.UUID(hex_only))
        except (ValueError, AttributeError):
            pass

    return codigo
