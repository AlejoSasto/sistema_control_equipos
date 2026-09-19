import uuid
import base64
from io import BytesIO
import qrcode
from django.conf import settings
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import models


class Equipo(models.Model):
    TIPO_PORTATIL = "portatil"
    TIPO_DESKTOP = "desktop"
    TIPO_TABLET = "tablet"

    OPCIONES_TIPO = [
        (TIPO_PORTATIL, "Portátil (Laptop)"),
        (TIPO_DESKTOP, "Computador de Escritorio (Desktop)"),
        (TIPO_TABLET, "Tablet / iPad"),
    ]

    PROPIEDAD_INSTITUCIONAL = "institucional"
    PROPIEDAD_PERSONAL = "personal"

    OPCIONES_PROPIEDAD = [
        (PROPIEDAD_INSTITUCIONAL, "De dependencia (institucional)"),
        (PROPIEDAD_PERSONAL, "Personal (Propiedad del Miembro)"),
    ]

    persona = models.ForeignKey(
        "personas.Persona",
        on_delete=models.RESTRICT,
        related_name="equipos",
        help_text="Dueño del equipo (comunidad académica)",
    )
    tipo = models.CharField(max_length=20, choices=OPCIONES_TIPO, default=TIPO_PORTATIL)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=80)
    serial = models.CharField(max_length=80, unique=True, db_index=True)
    propiedad = models.CharField(
        max_length=20,
        choices=OPCIONES_PROPIEDAD,
        default=PROPIEDAD_PERSONAL,
        help_text="Tipo de propiedad del equipo",
    )
    dependencia = models.ForeignKey(
        "organizacion.Area",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="equipos",
        help_text="Dependencia que asigna el equipo (obligatorio si es institucional)",
    )
    token_qr = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        help_text="Identificador interno permanente del equipo (no se exhibe crudo en el QR)",
    )
    activo = models.BooleanField(default=True, help_text="Borrado lógico (baja de equipo)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "equipo"
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["serial"]),
            models.Index(fields=["token_qr"]),
            models.Index(fields=["persona"]),
        ]

    def __str__(self):
        return f"{self.marca} {self.modelo} - Serial: {self.serial} ({self.persona.nombre_completo})"

    def clean(self):
        super().clean()
        if self.propiedad == self.PROPIEDAD_PERSONAL and self.dependencia_id:
            raise ValidationError({"dependencia": "Los equipos personales no pueden tener dependencia asignada."})
        if self.propiedad == self.PROPIEDAD_INSTITUCIONAL and not self.dependencia_id:
            raise ValidationError({"dependencia": "Los equipos de dependencia deben indicar el área institucional."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def generar_token_exhibicion(self) -> str:
        """Token firmado de corta duración codificado en el QR mostrado en pantalla."""
        max_age = getattr(settings, "QR_DISPLAY_TOKEN_MAX_AGE", 300)
        signer = signing.TimestampSigner(salt="equipo-qr-exhibicion")
        # max_age se valida al unsign; el sign solo marca el timestamp
        return signer.sign(str(self.token_qr))

    @classmethod
    def resolver_token_escaneado(cls, codigo: str):
        """
        Resuelve un código escaneado a Equipo.
        Acepta token de exhibición firmado (preferido) o UUID permanente (legado).
        """
        codigo = (codigo or "").strip()
        if not codigo:
            return None

        qs = cls.objects.select_related(
            "persona", "persona__sede", "persona__programa", "dependencia"
        )

        # 1) Token firmado de exhibición
        try:
            max_age = getattr(settings, "QR_DISPLAY_TOKEN_MAX_AGE", 300)
            signer = signing.TimestampSigner(salt="equipo-qr-exhibicion")
            token_uuid = signer.unsign(codigo, max_age=max_age)
            return qs.filter(token_qr=token_uuid).first()
        except signing.SignatureExpired:
            return None
        except signing.BadSignature:
            pass

        # 2) UUID permanente (transición / pistola con valor legado)
        try:
            token_uuid = uuid.UUID(codigo)
            return qs.filter(token_qr=token_uuid).first()
        except (ValueError, AttributeError, TypeError):
            pass

        # 3) Serial físico
        return qs.filter(serial__iexact=codigo).first()

    def generar_qr_base64(self) -> str:
        """QR al vuelo con token de exhibición firmado (Data URI base64)."""
        payload = self.generar_token_exhibicion()
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
