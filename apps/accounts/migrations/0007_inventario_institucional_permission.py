from django.db import migrations


def cargar_permiso_inventario(apps, schema_editor):
    Permiso = apps.get_model("accounts", "Permiso")
    Rol = apps.get_model("accounts", "Rol")
    RolPermiso = apps.get_model("accounts", "RolPermiso")

    permiso, _ = Permiso.objects.get_or_create(
        codigo="equipos.inventario_institucional",
        defaults={
            "descripcion": "Dar de alta equipos institucionales en inventario de su dependencia (sin asignar persona)",
        },
    )
    for nombre in ("admin_sistema", "responsable_dependencia"):
        rol = Rol.objects.filter(nombre=nombre).first()
        if not rol:
            continue
        RolPermiso.objects.get_or_create(rol=rol, permiso=permiso)


def reverse_permiso(apps, schema_editor):
    Permiso = apps.get_model("accounts", "Permiso")
    Permiso.objects.filter(codigo="equipos.inventario_institucional").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_asignacion_institucional_permissions"),
    ]

    operations = [
        migrations.RunPython(cargar_permiso_inventario, reverse_permiso),
    ]
