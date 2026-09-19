"""Validación y normalización de fotos de persona."""

from __future__ import annotations

from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, UnidentifiedImageError

MAX_FOTO_BYTES = 2 * 1024 * 1024  # 2 MB
MAX_DIMENSION = 1200
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def validar_y_procesar_foto(archivo):
    """
    Verifica tamaño y tipo real de imagen; redimensiona/recomprime a JPEG.
    Devuelve ContentFile listo para ImageField, o None si archivo vacío.
    """
    if not archivo:
        return None

    if getattr(archivo, "size", 0) and archivo.size > MAX_FOTO_BYTES:
        raise ValidationError("La foto no puede superar 2 MB.")

    try:
        archivo.seek(0)
    except Exception:
        pass

    try:
        imagen = Image.open(archivo)
        imagen.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError("El archivo no es una imagen válida.") from exc

    if imagen.format not in ALLOWED_FORMATS:
        raise ValidationError("Formato de imagen no permitido. Use JPEG, PNG o WEBP.")

    if imagen.mode not in ("RGB", "L"):
        imagen = imagen.convert("RGB")
    elif imagen.mode == "L":
        imagen = imagen.convert("RGB")

    imagen.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

    buffer = BytesIO()
    imagen.save(buffer, format="JPEG", quality=85, optimize=True)
    buffer.seek(0)

    nombre = getattr(archivo, "name", "foto.jpg")
    base = nombre.rsplit(".", 1)[0] if nombre else "foto"
    return ContentFile(buffer.read(), name=f"{base}.jpg")
