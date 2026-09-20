# Permisos y rol para asignación de equipos institucionales (doc 14)

from django.db import migrations


def cargar_permisos_asignacion(apps, schema_editor):
    Permiso = apps.get_model("accounts", "Permiso")
    Rol = apps.get_model("accounts", "Rol")
    RolPermiso = apps.get_model("accounts", "RolPermiso")

    nuevos = [
        (
            "equipos.asignar_institucional",
            "Asignar, reasignar o dar de baja equipos institucionales de su dependencia",
        ),
        (
            "equipos.gestionar_responsables",
            "Administrar responsables de dependencia (quién asigna equipos por unidad)",
        ),
    ]
    permisos = {}
    for codigo, descripcion in nuevos:
        permiso, _ = Permiso.objects.get_or_create(
            codigo=codigo, defaults={"descripcion": descripcion}
        )
        if permiso.descripcion != descripcion:
            permiso.descripcion = descripcion
            permiso.save(update_fields=["descripcion"])
        permisos[codigo] = permiso

    rol_resp, _ = Rol.objects.update_or_create(
        nombre="responsable_dependencia",
        defaults={
            "descripcion": (
                "Responsable de dependencia: asigna equipos institucionales "
                "solo en las unidades donde está designado"
            ),
            "activo": True,
        },
    )
    RolPermiso.objects.get_or_create(
        rol=rol_resp, permiso=permisos["equipos.asignar_institucional"]
    )

    rol_admin = Rol.objects.filter(nombre="admin_sistema").first()
    if rol_admin:
        for permiso in permisos.values():
            RolPermiso.objects.get_or_create(rol=rol_admin, permiso=permiso)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_reportes_permissions"),
    ]

    operations = [
        migrations.RunPython(cargar_permisos_asignacion, migrations.RunPython.noop),
    ]
