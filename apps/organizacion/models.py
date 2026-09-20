from django.db import models


class Sede(models.Model):
    nombre = models.CharField(max_length=150)
    codigo = models.CharField(max_length=20, unique=True, help_text="Código corto institucional (ej. UBATE, FUSA, GIR)")
    ciudad = models.CharField(max_length=100)
    activo = models.BooleanField(default=True, help_text="Borrado lógico")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sede"
        verbose_name = "Sede"
        verbose_name_plural = "Sedes"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    @property
    def programas(self):
        return Programa.objects.filter(sede=self, activo=True)


class Decanatura(models.Model):
    """Facultad institucional — independiente de sede."""

    nombre = models.CharField(max_length=150)
    codigo = models.CharField(max_length=20, unique=True, help_text="Código corto institucional (ej. FAC-ING)")
    activo = models.BooleanField(default=True, help_text="Borrado lógico")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "decanatura"
        verbose_name = "Facultad"
        verbose_name_plural = "Facultades"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class Area(models.Model):
    """Dependencia administrativa (CGCA, ISU, CTeI, etc.)."""

    codigo = models.CharField(max_length=20, unique=True, help_text="Código corto (ej. CGCA, ISU, CTeI)")
    nombre = models.CharField(max_length=150, help_text="Nombre descriptivo de la dependencia")
    activo = models.BooleanField(default=True, help_text="Borrado lógico")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "area"
        verbose_name = "Área / Dependencia"
        verbose_name_plural = "Áreas / Dependencias"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.codigo} — {self.nombre}"


class Programa(models.Model):
    NIVEL_PREGRADO = "pregrado"
    NIVEL_POSGRADO = "posgrado"

    OPCIONES_NIVEL = [
        (NIVEL_PREGRADO, "Pregrado"),
        (NIVEL_POSGRADO, "Posgrado"),
    ]

    sede = models.ForeignKey(
        Sede,
        on_delete=models.RESTRICT,
        related_name="programas",
        help_text="Sede donde se ofrece el programa",
    )
    facultad = models.ForeignKey(
        Decanatura,
        on_delete=models.RESTRICT,
        related_name="programas",
        db_column="decanatura_id",
        help_text="Facultad a la que pertenece el programa",
    )
    nombre = models.CharField(max_length=150)
    codigo = models.CharField(max_length=20, unique=True, help_text="Código SNIES o institucional")
    nivel = models.CharField(max_length=20, choices=OPCIONES_NIVEL, default=NIVEL_PREGRADO)
    activo = models.BooleanField(default=True, help_text="Borrado lógico")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "programa"
        verbose_name = "Programa Académico"
        verbose_name_plural = "Programas Académicos"
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["sede", "facultad"]),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.sede.codigo} / {self.facultad.codigo})"


UNIDAD_FACULTAD = "facultad"
UNIDAD_PROGRAMA = "programa"
UNIDAD_AREA = "area"

OPCIONES_UNIDAD_TIPO = [
    (UNIDAD_FACULTAD, "Facultad"),
    (UNIDAD_PROGRAMA, "Programa"),
    (UNIDAD_AREA, "Área / Dependencia"),
]


class ResponsableDependencia(models.Model):
    """Usuario autorizado a asignar equipos institucionales en nombre de una unidad."""

    usuario = models.ForeignKey(
        "accounts.Usuario",
        on_delete=models.CASCADE,
        related_name="responsabilidades_dependencia",
    )
    unidad_tipo = models.CharField(max_length=20, choices=OPCIONES_UNIDAD_TIPO)
    unidad_id = models.PositiveBigIntegerField(
        help_text="ID de la Facultad, Programa o Área según unidad_tipo",
    )
    activo = models.BooleanField(default=True, help_text="Borrado lógico")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "responsable_dependencia"
        verbose_name = "Responsable de dependencia"
        verbose_name_plural = "Responsables de dependencia"
        ordering = ["unidad_tipo", "unidad_id"]
        indexes = [
            models.Index(fields=["usuario", "activo"]),
            models.Index(fields=["unidad_tipo", "unidad_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "unidad_tipo", "unidad_id"],
                name="uniq_responsable_usuario_unidad",
            ),
        ]

    def __str__(self):
        return f"{self.usuario_id} → {self.unidad_tipo}:{self.unidad_id}"
