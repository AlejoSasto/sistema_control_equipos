from django.db import migrations, models
import django.db.models.deletion


def migrar_alcances_iniciales(apps, schema_editor):
    AlcanceUsuario = apps.get_model("organizacion", "AlcanceUsuario")
    ResponsableDependencia = apps.get_model("organizacion", "ResponsableDependencia")
    Usuario = apps.get_model("accounts", "Usuario")
    Rol = apps.get_model("accounts", "Rol")
    Persona = apps.get_model("personas", "Persona")

    nivel_map = {
        "facultad": "facultad",
        "programa": "programa",
        "area": "area",
    }

    rol_admin = Rol.objects.filter(nombre="admin_sistema").first()
    if rol_admin:
        for usuario in Usuario.objects.filter(roles=rol_admin).distinct():
            AlcanceUsuario.objects.get_or_create(
                usuario=usuario,
                nivel="global",
                objeto_id=None,
                defaults={"activo": True},
            )

    for fila in ResponsableDependencia.objects.filter(activo=True):
        nivel = nivel_map.get(fila.unidad_tipo)
        if not nivel:
            continue
        AlcanceUsuario.objects.get_or_create(
            usuario_id=fila.usuario_id,
            nivel=nivel,
            objeto_id=fila.unidad_id,
            defaults={"activo": True},
        )

    rol_vigilante = Rol.objects.filter(nombre="vigilante").first()
    if rol_vigilante:
        for usuario in Usuario.objects.filter(roles=rol_vigilante).select_related("persona"):
            persona = Persona.objects.filter(pk=getattr(usuario, "persona_id", None)).first()
            if persona and persona.sede_id:
                AlcanceUsuario.objects.get_or_create(
                    usuario=usuario,
                    nivel="sede",
                    objeto_id=persona.sede_id,
                    defaults={"activo": True},
                )


def reverse_alcances(apps, schema_editor):
    apps.get_model("organizacion", "AlcanceUsuario").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("organizacion", "0004_responsable_y_unidad_equipo"),
        ("accounts", "0010_usuarios_desbloquear_permission"),
        ("personas", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AlcanceUsuario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "nivel",
                    models.CharField(
                        choices=[
                            ("global", "Global (todas las sedes)"),
                            ("sede", "Sede / seccional"),
                            ("facultad", "Facultad"),
                            ("programa", "Programa académico"),
                            ("area", "Dependencia / área"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "objeto_id",
                    models.PositiveBigIntegerField(
                        blank=True,
                        help_text="Null solo cuando nivel=global",
                        null=True,
                    ),
                ),
                ("activo", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alcances",
                        to="accounts.usuario",
                    ),
                ),
            ],
            options={
                "verbose_name": "Alcance de usuario",
                "verbose_name_plural": "Alcances de usuario",
                "db_table": "alcance_usuario",
                "ordering": ["usuario_id", "nivel"],
                "indexes": [
                    models.Index(fields=["usuario", "activo"], name="alcance_usuario_usuario_activo_idx"),
                    models.Index(fields=["nivel", "objeto_id"], name="alcance_usuario_nivel_obj_idx"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="alcanceusuario",
            constraint=models.UniqueConstraint(
                fields=("usuario", "nivel", "objeto_id"),
                name="uniq_alcance_usuario_nivel_objeto",
            ),
        ),
        migrations.RunPython(migrar_alcances_iniciales, reverse_alcances),
    ]
