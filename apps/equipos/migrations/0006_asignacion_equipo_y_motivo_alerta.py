# Migración: AsignacionEquipo + historial desde campos planos de Equipo (doc 15)

import datetime

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def migrar_asignaciones_desde_equipo(apps, schema_editor):
    Equipo = apps.get_model("equipos", "Equipo")
    AsignacionEquipo = apps.get_model("equipos", "AsignacionEquipo")
    Usuario = apps.get_model("accounts", "Usuario")

    fallback_user = (
        Usuario.objects.filter(username="admin").first()
        or Usuario.objects.filter(is_superuser=True).first()
        or Usuario.objects.order_by("id").first()
    )
    if not fallback_user:
        return

    for equipo in Equipo.objects.filter(propiedad="institucional").exclude(
        unidad_tipo__isnull=True
    ).exclude(unidad_id__isnull=True):
        inicio = None
        if equipo.fecha_asignacion:
            inicio = equipo.fecha_asignacion.date()
        elif equipo.created_at:
            inicio = equipo.created_at.date()
        else:
            inicio = datetime.date.today()
        fin = inicio + datetime.timedelta(days=365)
        asignado_por_id = equipo.asignado_por_usuario_id or fallback_user.id
        AsignacionEquipo.objects.create(
            equipo_id=equipo.id,
            persona_id=equipo.persona_id,
            unidad_tipo=equipo.unidad_tipo,
            unidad_id=equipo.unidad_id,
            fecha_inicio=inicio,
            fecha_fin=fin,
            estado="activa",
            asignado_por_usuario_id=asignado_por_id,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("equipos", "0005_migrar_unidad_institucional_legacy"),
        ("organizacion", "0004_responsable_y_unidad_equipo"),
        ("personas", "0004_alter_persona_programa_alter_tipovinculo_codigo"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AsignacionEquipo",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "unidad_tipo",
                    models.CharField(
                        choices=[
                            ("facultad", "Facultad"),
                            ("programa", "Programa"),
                            ("area", "Área / Dependencia"),
                        ],
                        max_length=20,
                    ),
                ),
                ("unidad_id", models.PositiveBigIntegerField()),
                ("fecha_inicio", models.DateField()),
                ("fecha_fin", models.DateField()),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("activa", "Activa"),
                            ("finalizada", "Finalizada"),
                            ("revocada", "Revocada"),
                        ],
                        db_index=True,
                        default="activa",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "asignado_por_usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="asignaciones_realizadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "equipo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="asignaciones",
                        to="equipos.equipo",
                    ),
                ),
                (
                    "persona",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="asignaciones_equipo",
                        to="personas.persona",
                    ),
                ),
            ],
            options={
                "verbose_name": "Asignación de equipo",
                "verbose_name_plural": "Asignaciones de equipo",
                "db_table": "asignacion_equipo",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="asignacionequipo",
            index=models.Index(
                fields=["equipo", "estado"], name="asignacion__equipo__f93f83_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="asignacionequipo",
            index=models.Index(
                fields=["unidad_tipo", "unidad_id"],
                name="asignacion__unidad__dd2361_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="asignacionequipo",
            index=models.Index(
                fields=["fecha_fin"], name="asignacion__fecha_f_b41c65_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="asignacionequipo",
            constraint=models.CheckConstraint(
                condition=models.Q(("fecha_fin__gte", models.F("fecha_inicio"))),
                name="asignacion_fecha_fin_gte_inicio",
            ),
        ),
        migrations.AddConstraint(
            model_name="asignacionequipo",
            constraint=models.UniqueConstraint(
                condition=models.Q(("estado", "activa")),
                fields=("equipo",),
                name="uniq_asignacion_activa_por_equipo",
            ),
        ),
        migrations.RunPython(migrar_asignaciones_desde_equipo, migrations.RunPython.noop),
        migrations.RemoveIndex(
            model_name="equipo",
            name="equipo_unidad__847342_idx",
        ),
        migrations.RemoveField(
            model_name="equipo",
            name="asignado_por_usuario",
        ),
        migrations.RemoveField(
            model_name="equipo",
            name="fecha_asignacion",
        ),
        migrations.RemoveField(
            model_name="equipo",
            name="unidad_id",
        ),
        migrations.RemoveField(
            model_name="equipo",
            name="unidad_tipo",
        ),
        migrations.AlterField(
            model_name="equipo",
            name="dependencia",
            field=models.ForeignKey(
                blank=True,
                help_text="Área si la asignación activa es de tipo area (compatibilidad inventario)",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="equipos",
                to="organizacion.area",
            ),
        ),
        migrations.AlterField(
            model_name="equipo",
            name="persona",
            field=models.ForeignKey(
                help_text="Dueño actual del equipo (comunidad académica)",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="equipos",
                to="personas.persona",
            ),
        ),
    ]
