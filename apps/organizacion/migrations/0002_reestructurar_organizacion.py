import re

import django.db.models.deletion
from django.db import migrations, models


def _canonical_codigo(codigo):
    """FAC-ING-UBATE -> FAC-ING"""
    return re.sub(r"-(UBATE|FUSA|GIR|CHIA|FAC)$", "", codigo, flags=re.IGNORECASE)


def populate_sede_and_consolidate_facultades(apps, schema_editor):
    Decanatura = apps.get_model("organizacion", "Decanatura")
    Programa = apps.get_model("organizacion", "Programa")

    canonical_by_nombre = {}
    id_map = {}

    for dec in Decanatura.objects.select_related("sede").order_by("id"):
        key = dec.nombre.strip().lower()
        if key not in canonical_by_nombre:
            new_codigo = _canonical_codigo(dec.codigo)
            if Decanatura.objects.filter(codigo=new_codigo).exclude(pk=dec.pk).exists():
                new_codigo = dec.codigo
            elif new_codigo != dec.codigo:
                dec.codigo = new_codigo
                dec.save(update_fields=["codigo"])
            canonical_by_nombre[key] = dec
            id_map[dec.pk] = dec.pk
        else:
            canonical = canonical_by_nombre[key]
            id_map[dec.pk] = canonical.pk
            dec.activo = False
            dec.save(update_fields=["activo"])

    for prog in Programa.objects.select_related("decanatura").all():
        old_dec = prog.decanatura
        prog.sede_id = old_dec.sede_id
        prog.decanatura_id = id_map.get(old_dec.pk, old_dec.pk)
        prog.save(update_fields=["sede_id", "decanatura_id"])


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("organizacion", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Area",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "codigo",
                    models.CharField(
                        help_text="Código corto (ej. CGCA, ISU, CTeI)",
                        max_length=20,
                        unique=True,
                    ),
                ),
                (
                    "nombre",
                    models.CharField(help_text="Nombre descriptivo de la dependencia", max_length=150),
                ),
                ("activo", models.BooleanField(default=True, help_text="Borrado lógico")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Área / Dependencia",
                "verbose_name_plural": "Áreas / Dependencias",
                "db_table": "area",
                "ordering": ["nombre"],
            },
        ),
        migrations.AddField(
            model_name="programa",
            name="sede",
            field=models.ForeignKey(
                help_text="Sede donde se ofrece el programa",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="programas",
                to="organizacion.sede",
            ),
        ),
        migrations.RunPython(populate_sede_and_consolidate_facultades, reverse_noop),
        migrations.AlterField(
            model_name="programa",
            name="sede",
            field=models.ForeignKey(
                help_text="Sede donde se ofrece el programa",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="programas",
                to="organizacion.sede",
            ),
        ),
        migrations.RemoveField(
            model_name="decanatura",
            name="sede",
        ),
        migrations.RenameField(
            model_name="programa",
            old_name="decanatura",
            new_name="facultad",
        ),
        migrations.AlterField(
            model_name="programa",
            name="facultad",
            field=models.ForeignKey(
                db_column="decanatura_id",
                help_text="Facultad a la que pertenece el programa",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="programas",
                to="organizacion.decanatura",
            ),
        ),
        migrations.AlterModelOptions(
            name="decanatura",
            options={
                "ordering": ["nombre"],
                "verbose_name": "Facultad",
                "verbose_name_plural": "Facultades",
            },
        ),
        migrations.AddIndex(
            model_name="programa",
            index=models.Index(fields=["sede", "facultad"], name="programa_sede_fac_idx"),
        ),
    ]
