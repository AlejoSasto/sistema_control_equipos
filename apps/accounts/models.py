from django.contrib.auth.models import AbstractUser
from django.db import models


class Permiso(models.Model):
    codigo = models.CharField(
        max_length=60,
        unique=True,
        help_text="Código único del permiso (ej. equipos.registrar, control.escanear)",
    )
    descripcion = models.CharField(max_length=255, help_text="Descripción legible del permiso")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "permiso"
        verbose_name = "Permiso"
        verbose_name_plural = "Permisos"
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} — {self.descripcion}"


class Rol(models.Model):
    nombre = models.CharField(
        max_length=50,
        unique=True,
        help_text="Nombre del rol (ej. miembro_comunidad, celador, admin_sistema)",
    )
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    permisos = models.ManyToManyField(
        Permiso,
        through="RolPermiso",
        related_name="roles",
        blank=True,
    )
    activo = models.BooleanField(default=True, help_text="Borrado lógico")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rol"
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class RolPermiso(models.Model):
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE)

    class Meta:
        db_table = "rol_permiso"
        unique_together = ("rol", "permiso")
        verbose_name = "Asignación Rol-Permiso"
        verbose_name_plural = "Asignaciones Rol-Permiso"

    def __str__(self):
        return f"{self.rol.nombre} -> {self.permiso.codigo}"


class Usuario(AbstractUser):
    email = models.EmailField(
        "correo electrónico",
        max_length=254,
        unique=True,
        blank=True,
    )
    persona = models.OneToOneField(
        "personas.Persona",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuario",
        help_text="Vínculo opcional a una persona de la comunidad académica",
    )
    roles = models.ManyToManyField(
        Rol,
        through="UsuarioRol",
        related_name="usuarios",
        blank=True,
    )
    activo = models.BooleanField(default=True, help_text="Borrado lógico")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "usuario"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        if self.persona:
            return f"{self.username} ({self.persona.nombre_completo})"
        return self.username

    def tiene_permiso(self, codigo_permiso: str) -> bool:
        """Verifica si el usuario tiene un permiso específico a través de sus roles activos."""
        if self.is_superuser:
            return True
        if not self.is_active or not self.activo:
            return False
        return self.roles.filter(
            activo=True,
            permisos__codigo=codigo_permiso
        ).exists()

    @property
    def es_celador(self) -> bool:
        return self.tiene_permiso("control.escanear")

    @property
    def es_admin(self) -> bool:
        return self.is_superuser or any(
            self.tiene_permiso(c)
            for c in (
                "catalogos.administrar",
                "personas.administrar",
                "usuarios.administrar",
                "roles.administrar",
                "permisos.ver",
            )
        )

    @property
    def puede_administrar_personas(self) -> bool:
        return self.is_superuser or self.tiene_permiso("personas.administrar")

    @property
    def puede_administrar_usuarios(self) -> bool:
        return self.is_superuser or self.tiene_permiso("usuarios.administrar")

    @property
    def puede_administrar_roles(self) -> bool:
        return self.is_superuser or self.tiene_permiso("roles.administrar")

    @property
    def puede_ver_permisos(self) -> bool:
        return self.is_superuser or self.tiene_permiso("permisos.ver")

    @property
    def puede_administrar_catalogos(self) -> bool:
        return self.is_superuser or self.tiene_permiso("catalogos.administrar")

    @property
    def puede_ver_propio(self) -> bool:
        return self.is_superuser or self.tiene_permiso("perfil.ver_propio")

    @property
    def es_miembro_comunidad(self) -> bool:
        return self.tiene_permiso("perfil.ver_propio") and not self.es_admin and not self.es_celador


class UsuarioRol(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)

    class Meta:
        db_table = "usuario_rol"
        unique_together = ("usuario", "rol")
        verbose_name = "Asignación Usuario-Rol"
        verbose_name_plural = "Asignaciones Usuario-Rol"

    def __str__(self):
        return f"{self.usuario.username} -> {self.rol.nombre}"
