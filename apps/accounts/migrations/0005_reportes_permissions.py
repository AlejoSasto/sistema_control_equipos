# Permisos del módulo de reportes Excel

from django.db import migrations


def crear_permisos_reportes(apps, schema_editor):
    Permiso = apps.get_model("accounts", "Permiso")
    Rol = apps.get_model("accounts", "Rol")
    RolPermiso = apps.get_model("accounts", "RolPermiso")

    nuevos = [
        ("reportes.ver", "Acceder al módulo de reportes y configurar filtros"),
        ("reportes.exportar", "Generar y descargar reportes Excel"),
    ]
    permisos_objs = {}
    for codigo, descripcion in nuevos:
        permiso, _ = Permiso.objects.get_or_create(
            codigo=codigo, defaults={"descripcion": descripcion}
        )
        permisos_objs[codigo] = permiso

    rol_admin = Rol.objects.filter(nombre="admin_sistema").first()
    if rol_admin:
        for permiso in permisos_objs.values():
            RolPermiso.objects.get_or_create(rol=rol_admin, permiso=permiso)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_perfil_ver_propio"),
    ]

    operations = [
        migrations.RunPython(crear_permisos_reportes, reverse_code=migrations.RunPython.noop),
    ]
