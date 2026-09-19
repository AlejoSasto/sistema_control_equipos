# Permiso perfil.ver_propio para miembros de comunidad

from django.db import migrations


def crear_permiso_perfil(apps, schema_editor):
    Permiso = apps.get_model("accounts", "Permiso")
    Rol = apps.get_model("accounts", "Rol")
    RolPermiso = apps.get_model("accounts", "RolPermiso")

    permiso, _ = Permiso.objects.get_or_create(
        codigo="perfil.ver_propio",
        defaults={"descripcion": "Ver información personal, equipos y métricas propias"},
    )

    rol_miembro = Rol.objects.filter(nombre="miembro_comunidad").first()
    if rol_miembro:
        RolPermiso.objects.get_or_create(rol=rol_miembro, permiso=permiso)

    rol_admin = Rol.objects.filter(nombre="admin_sistema").first()
    if rol_admin:
        RolPermiso.objects.get_or_create(rol=rol_admin, permiso=permiso)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_panel_permissions"),
    ]

    operations = [
        migrations.RunPython(crear_permiso_perfil, reverse_code=migrations.RunPython.noop),
    ]
