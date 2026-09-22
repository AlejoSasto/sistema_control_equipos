from django.db import migrations


def cargar_permiso_gestionar_alcance(apps, schema_editor):
    Permiso = apps.get_model("accounts", "Permiso")
    Rol = apps.get_model("accounts", "Rol")
    RolPermiso = apps.get_model("accounts", "RolPermiso")

    permiso, _ = Permiso.objects.get_or_create(
        codigo="usuarios.gestionar_alcance",
        defaults={
            "descripcion": "Asignar y administrar el alcance jerárquico de otros usuarios",
        },
    )
    rol_admin = Rol.objects.filter(nombre="admin_sistema").first()
    if rol_admin:
        RolPermiso.objects.get_or_create(rol=rol_admin, permiso=permiso)


def reverse_permiso(apps, schema_editor):
    apps.get_model("accounts", "Permiso").objects.filter(
        codigo="usuarios.gestionar_alcance"
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0010_usuarios_desbloquear_permission"),
        ("organizacion", "0005_alcance_usuario"),
    ]

    operations = [
        migrations.RunPython(cargar_permiso_gestionar_alcance, reverse_permiso),
    ]
