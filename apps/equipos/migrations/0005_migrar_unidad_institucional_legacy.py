# Migración de datos: equipos institucionales legacy → unidad_tipo=area

from django.db import migrations


def migrar_equipos_institucionales_legacy(apps, schema_editor):
    Equipo = apps.get_model("equipos", "Equipo")
    for equipo in Equipo.objects.filter(
        propiedad="institucional",
        dependencia_id__isnull=False,
        unidad_tipo__isnull=True,
    ):
        Equipo.objects.filter(pk=equipo.pk).update(
            unidad_tipo="area",
            unidad_id=equipo.dependencia_id,
            fecha_asignacion=equipo.created_at,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("equipos", "0004_responsable_y_unidad_equipo"),
    ]

    operations = [
        migrations.RunPython(migrar_equipos_institucionales_legacy, migrations.RunPython.noop),
    ]
