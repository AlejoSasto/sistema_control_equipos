# Permisos granulares del panel de administración (Documento 07)

from django.db import migrations


def crear_permisos_panel(apps, schema_editor):
    Permiso = apps.get_model("accounts", "Permiso")
    Rol = apps.get_model("accounts", "Rol")
    RolPermiso = apps.get_model("accounts", "RolPermiso")

    nuevos = [
        ("personas.administrar", "Crear/editar/inactivar personas de la comunidad académica"),
        ("usuarios.administrar", "Crear/editar/inactivar usuarios y resetear contraseñas"),
        ("roles.administrar", "Crear/editar roles y asignar permisos"),
        ("permisos.ver", "Ver el catálogo de permisos (solo lectura)"),
    ]

    permisos_objs = {}
    for codigo, descripcion in nuevos:
        permiso, _ = Permiso.objects.get_or_create(codigo=codigo, defaults={"descripcion": descripcion})
        permisos_objs[codigo] = permiso

    # Actualizar descripción del permiso usuarios.administrar si ya existía con texto genérico
    Permiso.objects.filter(codigo="usuarios.administrar").update(
        descripcion="Crear/editar/inactivar usuarios y resetear contraseñas"
    )

    rol_admin = Rol.objects.filter(nombre="admin_sistema").first()
    if rol_admin:
        for permiso in permisos_objs.values():
            RolPermiso.objects.get_or_create(rol=rol_admin, permiso=permiso)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_alter_usuario_email_unique"),
    ]

    operations = [
        migrations.RunPython(crear_permisos_panel, reverse_code=migrations.RunPython.noop),
    ]
