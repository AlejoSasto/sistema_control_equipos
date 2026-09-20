from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("control_acceso", "0002_motivo_alerta"),
    ]

    operations = [
        migrations.AlterField(
            model_name="movimiento",
            name="motivo_alerta",
            field=models.CharField(
                blank=True,
                choices=[
                    ("equipo_inactivo", "Equipo inactivo"),
                    ("persona_inactiva", "Persona inactiva"),
                    ("no_coincide", "No coincide"),
                    ("asignacion_vencida", "Asignación institucional vencida"),
                    ("asignacion_no_vigente", "Asignación institucional no vigente"),
                    (
                        "sin_asignacion_activa",
                        "Sin asignación activa (disponible en inventario)",
                    ),
                ],
                db_index=True,
                help_text="Motivo tipificado cuando resultado=alerta",
                max_length=40,
                null=True,
            ),
        ),
    ]
