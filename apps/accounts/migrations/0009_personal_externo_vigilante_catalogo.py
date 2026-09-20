# Catálogo doc 16: rol vigilante + TipoVinculo personal_externo / vigilante
# Equivalente a lo que carga seed_data, sin necesidad de correr el comando.

from django.db import migrations


def cargar_catalogo_doc16(apps, schema_editor):
    Permiso = apps.get_model("accounts", "Permiso")
    Rol = apps.get_model("accounts", "Rol")
    RolPermiso = apps.get_model("accounts", "RolPermiso")
    TipoVinculo = apps.get_model("personas", "TipoVinculo")

    perm_escanear, _ = Permiso.objects.get_or_create(
        codigo="control.escanear",
        defaults={"descripcion": "Usar el puesto de control de salida (escaneo QR)"},
    )
    perm_alertas, _ = Permiso.objects.get_or_create(
        codigo="control.ver_alertas",
        defaults={"descripcion": "Consultar el historial de salidas y alertas"},
    )

    rol_vigilante, _ = Rol.objects.update_or_create(
        nombre="vigilante",
        defaults={
            "descripcion": "Personal de portería: control de salida en su sede",
            "activo": True,
        },
    )
    for permiso in (perm_escanear, perm_alertas):
        RolPermiso.objects.get_or_create(rol=rol_vigilante, permiso=permiso)

    Rol.objects.filter(nombre="celador").update(
        descripcion="Personal de portería (legado; usar rol vigilante)",
        activo=False,
    )

    rol_miembro = Rol.objects.filter(nombre="miembro_comunidad").first()
    if rol_miembro is None:
        rol_miembro = Rol.objects.create(
            nombre="miembro_comunidad",
            descripcion="Miembro de la comunidad académica: acceso solo a perfil y equipos propios",
            activo=True,
        )

    TipoVinculo.objects.update_or_create(
        codigo="personal_externo",
        defaults={
            "nombre": "Personal Externo",
            "permite_autoregistro": True,
            "dominio_correo_requerido": None,
            "rol_asignado_id": rol_miembro.pk,
            "activo": True,
        },
    )
    TipoVinculo.objects.update_or_create(
        codigo="vigilante",
        defaults={
            "nombre": "Vigilante",
            "permite_autoregistro": False,
            "dominio_correo_requerido": None,
            "rol_asignado_id": rol_vigilante.pk,
            "activo": True,
        },
    )


def revertir_catalogo_doc16(apps, schema_editor):
    TipoVinculo = apps.get_model("personas", "TipoVinculo")
    Rol = apps.get_model("accounts", "Rol")
    TipoVinculo.objects.filter(codigo__in=["personal_externo", "vigilante"]).delete()
    Rol.objects.filter(nombre="vigilante").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0008_rol_help_text_vigilante"),
        ("personas", "0005_personal_externo_vigilante"),
    ]

    operations = [
        migrations.RunPython(cargar_catalogo_doc16, revertir_catalogo_doc16),
    ]
