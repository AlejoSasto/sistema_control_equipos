# Generated manually — Area.sede obligatorio + unicidad (sede, codigo)

from django.db import migrations, models
import django.db.models.deletion


def backfill_area_sede(apps, schema_editor):
    Area = apps.get_model("organizacion", "Area")
    Sede = apps.get_model("organizacion", "Sede")
    Persona = apps.get_model("personas", "Persona")
    Equipo = apps.get_model("equipos", "Equipo")
    ResponsableDependencia = apps.get_model("organizacion", "ResponsableDependencia")
    AlcanceUsuario = apps.get_model("organizacion", "AlcanceUsuario")
    VisitaExterno = apps.get_model("personas", "VisitaExterno")

    sedes = list(Sede.objects.order_by("pk"))
    if not sedes:
        return

    areas_orig = list(Area.objects.all())
    # codigo -> {sede_id -> area_id}
    mapa: dict[str, dict[int, int]] = {}

    for area in areas_orig:
        codigo = area.codigo
        mapa.setdefault(codigo, {})
        # Asignar original a la primera sede
        primera = sedes[0]
        area.sede_id = primera.pk
        area.save(update_fields=["sede_id"])
        mapa[codigo][primera.pk] = area.pk

        for sede in sedes[1:]:
            clone = Area.objects.create(
                sede_id=sede.pk,
                codigo=codigo,
                nombre=area.nombre,
                activo=area.activo,
            )
            mapa[codigo][sede.pk] = clone.pk

    def area_para(codigo: str, sede_id: int | None) -> int | None:
        if not codigo:
            return None
        por_sede = mapa.get(codigo) or {}
        if sede_id and sede_id in por_sede:
            return por_sede[sede_id]
        if por_sede:
            return next(iter(por_sede.values()))
        return None

    # Remap Persona.area
    for persona in Persona.objects.exclude(area_id=None).select_related("area"):
        old = Area.objects.filter(pk=persona.area_id).first()
        if not old:
            continue
        nuevo_id = area_para(old.codigo, persona.sede_id)
        if nuevo_id and nuevo_id != persona.area_id:
            persona.area_id = nuevo_id
            persona.save(update_fields=["area_id"])

    # Remap Equipo.dependencia
    for equipo in Equipo.objects.exclude(dependencia_id=None):
        old = Area.objects.filter(pk=equipo.dependencia_id).first()
        if not old:
            continue
        sede_id = None
        if equipo.persona_id:
            p = Persona.objects.filter(pk=equipo.persona_id).first()
            if p:
                sede_id = p.sede_id
        nuevo_id = area_para(old.codigo, sede_id)
        if nuevo_id and nuevo_id != equipo.dependencia_id:
            equipo.dependencia_id = nuevo_id
            if equipo.unidad_tipo == "area":
                equipo.unidad_id = nuevo_id
            equipo.save(update_fields=["dependencia_id", "unidad_id"] if equipo.unidad_tipo == "area" else ["dependencia_id"])

    # Remap Equipo.unidad_id cuando unidad_tipo=area sin dependencia
    for equipo in Equipo.objects.filter(unidad_tipo="area").exclude(unidad_id=None):
        old = Area.objects.filter(pk=equipo.unidad_id).first()
        if not old:
            continue
        sede_id = None
        if equipo.persona_id:
            p = Persona.objects.filter(pk=equipo.persona_id).first()
            if p:
                sede_id = p.sede_id
        nuevo_id = area_para(old.codigo, sede_id)
        if nuevo_id and nuevo_id != equipo.unidad_id:
            equipo.unidad_id = nuevo_id
            equipo.dependencia_id = nuevo_id
            equipo.save(update_fields=["unidad_id", "dependencia_id"])

    # ResponsableDependencia unidad_tipo=area
    Usuario = apps.get_model("accounts", "Usuario")
    for fila in ResponsableDependencia.objects.filter(unidad_tipo="area"):
        old = Area.objects.filter(pk=fila.unidad_id).first()
        if not old:
            continue
        user = Usuario.objects.filter(pk=fila.usuario_id).first()
        sede_id = None
        if user and user.persona_id:
            p = Persona.objects.filter(pk=user.persona_id).first()
            if p:
                sede_id = p.sede_id
        nuevo_id = area_para(old.codigo, sede_id)
        if nuevo_id and nuevo_id != fila.unidad_id:
            if ResponsableDependencia.objects.filter(
                usuario_id=fila.usuario_id,
                unidad_tipo="area",
                unidad_id=nuevo_id,
            ).exclude(pk=fila.pk).exists():
                fila.activo = False
                fila.save(update_fields=["activo"])
            else:
                fila.unidad_id = nuevo_id
                fila.save(update_fields=["unidad_id"])

    # AlcanceUsuario nivel=area
    for fila in AlcanceUsuario.objects.filter(nivel="area"):
        if not fila.objeto_id:
            continue
        old = Area.objects.filter(pk=fila.objeto_id).first()
        if not old:
            continue
        user = Usuario.objects.filter(pk=fila.usuario_id).first()
        sede_id = None
        if user and user.persona_id:
            p = Persona.objects.filter(pk=user.persona_id).first()
            if p:
                sede_id = p.sede_id
        nuevo_id = area_para(old.codigo, sede_id)
        if nuevo_id and nuevo_id != fila.objeto_id:
            if AlcanceUsuario.objects.filter(
                usuario_id=fila.usuario_id,
                nivel="area",
                objeto_id=nuevo_id,
            ).exclude(pk=fila.pk).exists():
                fila.activo = False
                fila.save(update_fields=["activo"])
            else:
                fila.objeto_id = nuevo_id
                fila.save(update_fields=["objeto_id"])

    # VisitaExterno unidad_tipo=area
    for visita in VisitaExterno.objects.filter(unidad_tipo="area"):
        old = Area.objects.filter(pk=visita.unidad_id).first()
        if not old:
            continue
        nuevo_id = area_para(old.codigo, visita.sede_id)
        if nuevo_id and nuevo_id != visita.unidad_id:
            visita.unidad_id = nuevo_id
            visita.save(update_fields=["unidad_id"])


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("organizacion", "0006_alcance_usuario_indexes"),
        ("personas", "0005_personal_externo_vigilante"),
        ("equipos", "0008_rename_equipo_unidad_prop_idx_equipo_unidad__847342_idx_and_more"),
        ("accounts", "0011_usuarios_gestionar_alcance_permission"),
    ]

    operations = [
        migrations.AddField(
            model_name="area",
            name="sede",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="areas",
                to="organizacion.sede",
                help_text="Sede a la que pertenece esta dependencia",
            ),
        ),
        migrations.AlterField(
            model_name="area",
            name="codigo",
            field=models.CharField(
                help_text="Código corto (ej. CGCA, ISU, CTeI)",
                max_length=20,
            ),
        ),
        migrations.RunPython(backfill_area_sede, reverse_noop),
        migrations.AlterField(
            model_name="area",
            name="sede",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="areas",
                to="organizacion.sede",
                help_text="Sede a la que pertenece esta dependencia",
            ),
        ),
        migrations.AddIndex(
            model_name="area",
            index=models.Index(fields=["sede", "activo"], name="area_sede_id_activo_idx"),
        ),
        migrations.AddConstraint(
            model_name="area",
            constraint=models.UniqueConstraint(
                fields=("sede", "codigo"),
                name="uniq_area_sede_codigo",
            ),
        ),
        migrations.AlterModelOptions(
            name="area",
            options={
                "ordering": ["sede__nombre", "nombre"],
                "verbose_name": "Área / Dependencia",
                "verbose_name_plural": "Áreas / Dependencias",
            },
        ),
    ]
