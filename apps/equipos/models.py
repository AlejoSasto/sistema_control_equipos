import uuid
import base64
from io import BytesIO
import qrcode
from django.conf import settings
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from organizacion.models import OPCIONES_UNIDAD_TIPO, UNIDAD_AREA


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

    ESTADO_DISPONIBLE = "disponible"
    ESTADO_ASIGNADO = "asignado"
    ESTADO_DE_BAJA = "de_baja"

    OPCIONES_ESTADO_INVENTARIO = [
        (ESTADO_DISPONIBLE, "Disponible"),
        (ESTADO_ASIGNADO, "Asignado"),
        (ESTADO_DE_BAJA, "De baja"),
    ]

    persona = models.ForeignKey(
        "personas.Persona",
        on_delete=models.RESTRICT,
        related_name="equipos",
        null=True,
        blank=True,
        help_text="Dueño/usuario actual. NULL si institucional está disponible en inventario.",
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
    unidad_tipo = models.CharField(
        max_length=20,
        choices=OPCIONES_UNIDAD_TIPO,
        null=True,
        blank=True,
        help_text="Unidad propietaria permanente (solo institucional)",
    )
    unidad_id = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        help_text="ID de facultad/programa/área propietaria",
    )
    estado_inventario = models.CharField(
        max_length=20,
        choices=OPCIONES_ESTADO_INVENTARIO,
        null=True,
        blank=True,
        db_index=True,
        help_text="Solo institucionales: disponible / asignado / de_baja",
    )
    creado_por_usuario = models.ForeignKey(
        "accounts.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equipos_creados",
        help_text="Quién dio de alta el equipo en inventario",
    )
    dependencia = models.ForeignKey(
        "organizacion.Area",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="equipos",
        help_text="Área si unidad_tipo=area (compatibilidad inventario)",
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
            models.Index(fields=["unidad_tipo", "unidad_id"]),
            models.Index(fields=["estado_inventario"]),
        ]

    def __str__(self):
        dueño = self.persona.nombre_completo if self.persona_id else "sin asignar"
        return f"{self.marca} {self.modelo} - Serial: {self.serial} ({dueño})"

    def clean(self):
        super().clean()
        if self.propiedad == self.PROPIEDAD_PERSONAL:
            if not self.persona_id:
                raise ValidationError({"persona": "Un equipo personal requiere titular."})
            self.unidad_tipo = None
            self.unidad_id = None
            self.estado_inventario = None
            self.dependencia = None
        elif self.propiedad == self.PROPIEDAD_INSTITUCIONAL:
            if not self.unidad_tipo or not self.unidad_id:
                raise ValidationError(
                    {"unidad_tipo": "Un equipo institucional requiere unidad propietaria."}
                )
            if self.estado_inventario == self.ESTADO_ASIGNADO and not self.persona_id:
                raise ValidationError(
                    {"persona": "Un equipo asignado debe tener persona titular."}
                )
            if self.estado_inventario == self.ESTADO_DISPONIBLE:
                self.persona = None
            if self.unidad_tipo == UNIDAD_AREA:
                self.dependencia_id = self.unidad_id
            else:
                self.dependencia = None

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def generar_token_exhibicion(self) -> str:
        """Token firmado de corta duración codificado en el QR mostrado en pantalla."""
        max_age = getattr(settings, "QR_DISPLAY_TOKEN_MAX_AGE", 300)
        signer = signing.TimestampSigner(salt="equipo-qr-exhibicion")
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
            "persona", "persona__sede", "persona__programa", "persona__tipo_vinculo", "dependencia"
        )

        try:
            max_age = getattr(settings, "QR_DISPLAY_TOKEN_MAX_AGE", 300)
            signer = signing.TimestampSigner(salt="equipo-qr-exhibicion")
            token_uuid = signer.unsign(codigo, max_age=max_age)
            return qs.filter(token_qr=token_uuid).first()
        except (signing.SignatureExpired, signing.BadSignature):
            pass

        candidatos = [codigo]
        if ":" in codigo:
            candidatos.append(codigo.split(":", 1)[0])
        for candidato in candidatos:
            try:
                token_uuid = uuid.UUID(candidato)
            except (ValueError, AttributeError, TypeError):
                continue
            equipo = qs.filter(token_qr=token_uuid).first()
            if equipo is not None:
                return equipo

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


class AsignacionEquipo(models.Model):
    """Historial de asignación de un equipo institucional a una persona (doc 15)."""

    ESTADO_ACTIVA = "activa"
    ESTADO_FINALIZADA = "finalizada"
    ESTADO_REVOCADA = "revocada"

    OPCIONES_ESTADO = [
        (ESTADO_ACTIVA, "Activa"),
        (ESTADO_FINALIZADA, "Finalizada"),
        (ESTADO_REVOCADA, "Revocada"),
    ]

    equipo = models.ForeignKey(
        Equipo,
        on_delete=models.CASCADE,
        related_name="asignaciones",
    )
    persona = models.ForeignKey(
        "personas.Persona",
        on_delete=models.RESTRICT,
        related_name="asignaciones_equipo",
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(
        max_length=20,
        choices=OPCIONES_ESTADO,
        default=ESTADO_ACTIVA,
        db_index=True,
    )
    asignado_por_usuario = models.ForeignKey(
        "accounts.Usuario",
        on_delete=models.RESTRICT,
        related_name="asignaciones_realizadas",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "asignacion_equipo"
        verbose_name = "Asignación de equipo"
        verbose_name_plural = "Asignaciones de equipo"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["equipo", "estado"]),
            models.Index(fields=["fecha_fin"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(fecha_fin__gte=models.F("fecha_inicio")),
                name="asignacion_fecha_fin_gte_inicio",
            ),
            models.UniqueConstraint(
                fields=["equipo"],
                condition=Q(estado="activa"),
                name="uniq_asignacion_activa_por_equipo",
            ),
        ]

    def __str__(self):
        return f"{self.equipo_id} → {self.persona_id} [{self.estado}] {self.fecha_inicio}:{self.fecha_fin}"

    def clean(self):
        super().clean()
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValidationError({"fecha_fin": "La fecha fin no puede ser anterior a la fecha inicio."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
