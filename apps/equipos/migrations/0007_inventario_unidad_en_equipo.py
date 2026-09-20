# Migración doc 15 v2: unidad propietaria en Equipo, inventario, AsignacionEquipo sin unidad

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def migrar_unidad_y_estado(apps, schema_editor):
    Equipo = apps.get_model("equipos", "Equipo")
    AsignacionEquipo = apps.get_model("equipos", "AsignacionEquipo")

    for equipo in Equipo.objects.filter(propiedad="institucional"):
        asig = (
            AsignacionEquipo.objects.filter(equipo_id=equipo.id, estado="activa")
            .order_by("-created_at")
            .first()
        )
        if not asig:
            asig = (
                AsignacionEquipo.objects.filter(equipo_id=equipo.id)
                .order_by("-created_at")
                .first()
            )
        unidad_tipo = getattr(asig, "unidad_tipo", None) if asig else None
        unidad_id = getattr(asig, "unidad_id", None) if asig else None
        if not unidad_tipo or not unidad_id:
            # Sin historial: dejar nullable; se corregirá manualmente si hace falta
            Equipo.objects.filter(pk=equipo.pk).update(
                estado_inventario="disponible" if not equipo.persona_id else "asignado",
                activo=equipo.activo,
            )
            continue

        dependencia_id = unidad_id if unidad_tipo == "area" else None
        if not equipo.activo:
            estado = "de_baja"
            persona_id = None
        elif asig and asig.estado == "activa":
            estado = "asignado"
            persona_id = asig.persona_id
        else:
            estado = "disponible"
            persona_id = None

        Equipo.objects.filter(pk=equipo.pk).update(
            unidad_tipo=unidad_tipo,
            unidad_id=unidad_id,
            dependencia_id=dependencia_id,
            estado_inventario=estado,
            persona_id=persona_id,
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("equipos", "0006_asignacion_equipo_y_motivo_alerta"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="equipo",
            name="unidad_tipo",
            field=models.CharField(
                blank=True,
                choices=[
                    ("facultad", "Facultad"),
                    ("programa", "Programa"),
                    ("area", "Área / Dependencia"),
                ],
                help_text="Unidad propietaria permanente (solo institucional)",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="equipo",
            name="unidad_id",
            field=models.PositiveBigIntegerField(
                blank=True,
                help_text="ID de facultad/programa/área propietaria",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="equipo",
            name="estado_inventario",
            field=models.CharField(
                blank=True,
                choices=[
                    ("disponible", "Disponible"),
                    ("asignado", "Asignado"),
                    ("de_baja", "De baja"),
                ],
                db_index=True,
                help_text="Solo institucionales: disponible / asignado / de_baja",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="equipo",
            name="creado_por_usuario",
            field=models.ForeignKey(
                blank=True,
                help_text="Quién dio de alta el equipo en inventario",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="equipos_creados",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="equipo",
            name="persona",
            field=models.ForeignKey(
                blank=True,
                help_text="Dueño/usuario actual. NULL si institucional está disponible en inventario.",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="equipos",
                to="personas.persona",
            ),
        ),
        migrations.RunPython(migrar_unidad_y_estado, noop_reverse),
        migrations.RemoveIndex(
            model_name="asignacionequipo",
            name="asignacion__unidad__dd2361_idx",
        ),
        migrations.RemoveField(
            model_name="asignacionequipo",
            name="unidad_tipo",
        ),
        migrations.RemoveField(
            model_name="asignacionequipo",
            name="unidad_id",
        ),
        migrations.AddIndex(
            model_name="equipo",
            index=models.Index(
                fields=["unidad_tipo", "unidad_id"],
                name="equipo_unidad_prop_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="equipo",
            index=models.Index(
                fields=["estado_inventario"],
                name="equipo_estado_inv_idx",
            ),
        ),
    ]
