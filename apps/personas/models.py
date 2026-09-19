from django.core.exceptions import ValidationError
from django.db import models

CODIGO_VINCULO_ADMINISTRATIVO = "gestor_administrativo"


class TipoVinculo(models.Model):
    codigo = models.CharField(
        max_length=30,
        unique=True,
        help_text="Código único (ej. gestor_administrativo, creador_oportunidades, gestor_conocimiento, egresado)",
    )
    nombre = models.CharField(max_length=80)
    permite_autoregistro = models.BooleanField(
        default=False,
        help_text="Si un usuario externo puede crear su cuenta eligiendo este tipo",
    )
    dominio_correo_requerido = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="ej. @ucundinamarca.edu.co; si es nulo, no se exige dominio específico",
    )
    rol_asignado = models.ForeignKey(
        "accounts.Rol",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tipos_vinculo",
        help_text="Rol que se asigna automáticamente al autorregistrarse con este tipo",
    )
    activo = models.BooleanField(default=True, help_text="Borrado lógico")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tipo_vinculo"
        verbose_name = "Tipo de Vínculo"
        verbose_name_plural = "Tipos de Vínculo"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Persona(models.Model):
    TIPO_DOC_CC = "CC"
    TIPO_DOC_CE = "CE"
    TIPO_DOC_TI = "TI"
    TIPO_DOC_PAS = "PAS"

    OPCIONES_TIPO_DOC = [
        (TIPO_DOC_CC, "Cédula de Ciudadanía"),
        (TIPO_DOC_CE, "Cédula de Extranjería"),
        (TIPO_DOC_TI, "Tarjeta de Identidad"),
        (TIPO_DOC_PAS, "Pasaporte"),
    ]

    tipo_documento = models.CharField(max_length=5, choices=OPCIONES_TIPO_DOC, default=TIPO_DOC_CC)
    numero_documento = models.CharField(max_length=20, unique=True, db_index=True)
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    tipo_vinculo = models.ForeignKey(
        TipoVinculo,
        on_delete=models.RESTRICT,
        related_name="personas",
        help_text="Rol funcional dentro de la comunidad académica (Docente, Administrativo, Gestor...)",
    )
    sede = models.ForeignKey(
        "organizacion.Sede",
        on_delete=models.RESTRICT,
        related_name="personas",
        help_text="Sede a la que está vinculado",
    )
    programa = models.ForeignKey(
        "organizacion.Programa",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="personas",
        help_text="Programa asociado (aplica a perfiles académicos)",
    )
    area = models.ForeignKey(
        "organizacion.Area",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="personas",
        help_text="Área/dependencia (aplica a personal administrativo)",
    )
    foto_url = models.CharField(max_length=255, null=True, blank=True, help_text="URL o ruta de la foto institucional")
    foto = models.ImageField(upload_to="personas/", null=True, blank=True)
    activo = models.BooleanField(default=True, help_text="Borrado lógico")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "persona"
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.tipo_vinculo.nombre if self.tipo_vinculo else ''})"

    def get_tipo_vinculo_display(self):
        return self.tipo_vinculo.nombre if self.tipo_vinculo else ""

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def imagen_url(self):
        if self.foto:
            return self.foto.url
        if self.foto_url:
            return self.foto_url
        return None

    @property
    def es_administrativo(self):
        return self.tipo_vinculo and self.tipo_vinculo.codigo == CODIGO_VINCULO_ADMINISTRATIVO

    def clean(self):
        super().clean()
        if not self.tipo_vinculo_id:
            return
        if self.es_administrativo:
            if self.programa_id:
                raise ValidationError({"programa": "El personal administrativo no debe tener programa asignado."})
            if not self.area_id:
                raise ValidationError({"area": "El personal administrativo debe tener un área asignada."})
        else:
            if self.area_id:
                raise ValidationError({"area": "Solo el personal administrativo puede tener un área asignada."})
            if self.programa_id and self.sede_id and self.programa.sede_id != self.sede_id:
                raise ValidationError({"programa": "El programa debe pertenecer a la sede seleccionada."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
