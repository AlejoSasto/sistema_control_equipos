from django.db import migrations


def cargar_permiso_desbloquear(apps, schema_editor):
    Permiso = apps.get_model("accounts", "Permiso")
    Rol = apps.get_model("accounts", "Rol")
    RolPermiso = apps.get_model("accounts", "RolPermiso")

    permiso, _ = Permiso.objects.get_or_create(
        codigo="usuarios.desbloquear",
        defaults={
            "descripcion": "Desbloquear cuentas bloqueadas por intentos fallidos de login",
        },
    )
    rol_admin = Rol.objects.filter(nombre="admin_sistema").first()
    if rol_admin:
        RolPermiso.objects.get_or_create(rol=rol_admin, permiso=permiso)


def reverse_permiso(apps, schema_editor):
    Permiso = apps.get_model("accounts", "Permiso")
    Permiso.objects.filter(codigo="usuarios.desbloquear").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0009_personal_externo_vigilante_catalogo"),
    ]

    operations = [
        migrations.RunPython(cargar_permiso_desbloquear, reverse_permiso),
    ]
