from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auditoria", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditoriacambio",
            name="accion",
            field=models.CharField(
                choices=[
                    ("crear", "Crear"),
                    ("editar", "Editar"),
                    ("inactivar", "Inactivar"),
                    ("exportar", "Exportar"),
                ],
                max_length=20,
            ),
        ),
    ]
