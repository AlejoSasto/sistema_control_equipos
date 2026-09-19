import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizacion", "0002_reestructurar_organizacion"),
        ("personas", "0002_tipovinculo_alter_persona_tipo_vinculo"),
    ]

    operations = [
        migrations.AddField(
            model_name="persona",
            name="area",
            field=models.ForeignKey(
                blank=True,
                help_text="Área/dependencia (aplica a personal administrativo)",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="personas",
                to="organizacion.area",
            ),
        ),
    ]
