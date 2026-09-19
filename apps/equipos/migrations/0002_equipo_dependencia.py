import django.db.models.deletion
from django.db import migrations, models


def assign_default_dependencia(apps, schema_editor):
    Equipo = apps.get_model("equipos", "Equipo")
    Area = apps.get_model("organizacion", "Area")
    area, _ = Area.objects.get_or_create(
        codigo="CGCA",
        defaults={"nombre": "Biblioteca", "activo": True},
    )
    Equipo.objects.filter(propiedad="institucional", dependencia__isnull=True).update(dependencia=area)


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("organizacion", "0002_reestructurar_organizacion"),
        ("equipos", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="equipo",
            name="dependencia",
            field=models.ForeignKey(
                blank=True,
                help_text="Dependencia que asigna el equipo (obligatorio si es institucional)",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="equipos",
                to="organizacion.area",
            ),
        ),
        migrations.RunPython(assign_default_dependencia, reverse_noop),
    ]
