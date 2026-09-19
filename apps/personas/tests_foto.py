from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from PIL import Image
from io import BytesIO

from personas.validators import validar_y_procesar_foto, MAX_FOTO_BYTES


def _jpeg_bytes(size=(100, 100), color=(10, 20, 30)):
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, format="JPEG")
    return buf.getvalue()


class FotoValidatorTestCase(TestCase):
    def test_foto_jpeg_valida(self):
        archivo = SimpleUploadedFile("cara.jpg", _jpeg_bytes(), content_type="image/jpeg")
        result = validar_y_procesar_foto(archivo)
        self.assertIsNotNone(result)
        self.assertTrue(result.name.endswith(".jpg"))

    def test_foto_no_imagen_rechazada(self):
        archivo = SimpleUploadedFile("malo.txt", b"no es imagen", content_type="text/plain")
        with self.assertRaises(ValidationError):
            validar_y_procesar_foto(archivo)

    def test_foto_demasiado_grande(self):
        # Forzar size attribute > límite sin generar 2MB reales de imagen comprimida
        archivo = SimpleUploadedFile("grande.jpg", _jpeg_bytes(), content_type="image/jpeg")
        archivo.size = MAX_FOTO_BYTES + 1
        with self.assertRaises(ValidationError):
            validar_y_procesar_foto(archivo)
