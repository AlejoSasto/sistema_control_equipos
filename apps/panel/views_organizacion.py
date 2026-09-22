"""CRUD de Sedes, Facultades, Programas y Áreas — solo administradores."""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.alcance import (
    alcance_es_global,
    areas_visibles,
    facultades_visibles,
    programas_visibles,
    sedes_visibles,
)
from accounts.decorators import requiere_permiso
from organizacion.models import Area, Decanatura, Programa, Sede


@requiere_permiso("catalogos.administrar")
def organizacion_list(request):
    context = {
        "sedes": sedes_visibles(request.user).order_by("nombre"),
        "facultades": facultades_visibles(request.user).order_by("nombre"),
        "programas": programas_visibles(request.user).order_by("nombre"),
        "areas": areas_visibles(request.user).order_by("nombre"),
        "alcance_global": alcance_es_global(request.user),
    }
    return render(request, "panel/organizacion_list.html", context)


@requiere_permiso("catalogos.administrar")
def sede_form(request, pk=None):
    if pk:
        sede = get_object_or_404(sedes_visibles(request.user), pk=pk)
    else:
        if not alcance_es_global(request.user):
            messages.error(request, "Solo usuarios con alcance global pueden crear sedes.")
            return redirect("panel:organizacion_list")
        sede = None
    data = {
        "codigo": sede.codigo if sede else "",
        "nombre": sede.nombre if sede else "",
        "ciudad": sede.ciudad if sede else "",
        "activo": sede.activo if sede else True,
    }
    if request.method == "POST":
        codigo = request.POST.get("codigo", "").strip().upper()
        nombre = request.POST.get("nombre", "").strip()
        ciudad = request.POST.get("ciudad", "").strip()
        activo = request.POST.get("activo") in ("on", "true", "1")
        data = {"codigo": codigo, "nombre": nombre, "ciudad": ciudad, "activo": activo}
        if not (codigo and nombre and ciudad):
            messages.error(request, "Código, nombre y ciudad son obligatorios.")
        elif Sede.objects.filter(codigo=codigo).exclude(pk=pk).exists():
            messages.error(request, f"Ya existe una sede con el código '{codigo}'.")
        else:
            if sede:
                sede.codigo, sede.nombre, sede.ciudad, sede.activo = codigo, nombre, ciudad, activo
                sede.save()
                messages.success(request, f"Sede '{sede.nombre}' actualizada.")
            else:
                Sede.objects.create(codigo=codigo, nombre=nombre, ciudad=ciudad, activo=activo)
                messages.success(request, f"Sede '{nombre}' creada exitosamente.")
            return redirect("panel:organizacion_list")
    return render(request, "panel/sede_form.html", {"sede": sede, "data": data})


@require_POST
@requiere_permiso("catalogos.administrar")
def sede_toggle(request, pk):
    sede = get_object_or_404(sedes_visibles(request.user), pk=pk)
    sede.activo = not sede.activo
    sede.save()
    estado = "activada" if sede.activo else "inactivada"
    messages.success(request, f"Sede '{sede.nombre}' {estado}.")
    return redirect("panel:organizacion_list")


@requiere_permiso("catalogos.administrar")
def decanatura_form(request, pk=None):
    if pk:
        facultad = get_object_or_404(facultades_visibles(request.user), pk=pk)
    else:
        if not alcance_es_global(request.user):
            messages.error(request, "Solo usuarios con alcance global pueden crear facultades.")
            return redirect("panel:organizacion_list")
        facultad = None
    data = {
        "codigo": facultad.codigo if facultad else "",
        "nombre": facultad.nombre if facultad else "",
        "activo": facultad.activo if facultad else True,
    }
    if request.method == "POST":
        codigo = request.POST.get("codigo", "").strip().upper()
        nombre = request.POST.get("nombre", "").strip()
        activo = request.POST.get("activo") in ("on", "true", "1")
        data = {"codigo": codigo, "nombre": nombre, "activo": activo}
        if not (codigo and nombre):
            messages.error(request, "Código y nombre son obligatorios.")
        elif Decanatura.objects.filter(codigo=codigo).exclude(pk=pk).exists():
            messages.error(request, f"Ya existe una facultad con el código '{codigo}'.")
        else:
            if facultad:
                facultad.codigo, facultad.nombre, facultad.activo = codigo, nombre, activo
                facultad.save()
                messages.success(request, f"Facultad '{facultad.nombre}' actualizada.")
            else:
                Decanatura.objects.create(codigo=codigo, nombre=nombre, activo=activo)
                messages.success(request, f"Facultad '{nombre}' creada exitosamente.")
            return redirect("panel:organizacion_list")
    return render(
        request,
        "panel/decanatura_form.html",
        {"decanatura": facultad, "data": data},
    )


@require_POST
@requiere_permiso("catalogos.administrar")
def decanatura_toggle(request, pk):
    dec = get_object_or_404(facultades_visibles(request.user), pk=pk)
    dec.activo = not dec.activo
    dec.save()
    estado = "activada" if dec.activo else "inactivada"
    messages.success(request, f"Facultad '{dec.nombre}' {estado}.")
    return redirect("panel:organizacion_list")


@requiere_permiso("catalogos.administrar")
def programa_form(request, pk=None):
    if pk:
        programa = get_object_or_404(
            programas_visibles(request.user).select_related("sede", "facultad"), pk=pk
        )
    else:
        if not alcance_es_global(request.user):
            messages.error(request, "Solo usuarios con alcance global pueden crear programas.")
            return redirect("panel:organizacion_list")
        programa = None
    data = {
        "codigo": programa.codigo if programa else "",
        "nombre": programa.nombre if programa else "",
        "sede": str(programa.sede_id) if programa else "",
        "facultad": str(programa.facultad_id) if programa else "",
        "nivel": programa.nivel if programa else Programa.NIVEL_PREGRADO,
        "activo": programa.activo if programa else True,
    }
    if request.method == "POST":
        codigo = request.POST.get("codigo", "").strip().upper()
        nombre = request.POST.get("nombre", "").strip()
        sede_id = request.POST.get("sede", "").strip()
        fac_id = request.POST.get("facultad", "").strip()
        nivel = request.POST.get("nivel", Programa.NIVEL_PREGRADO)
        activo = request.POST.get("activo") in ("on", "true", "1")
        data = {
            "codigo": codigo,
            "nombre": nombre,
            "sede": sede_id,
            "facultad": fac_id,
            "nivel": nivel,
            "activo": activo,
        }
        if not (codigo and nombre and sede_id and fac_id):
            messages.error(request, "Código, nombre, sede y facultad son obligatorios.")
        elif Programa.objects.filter(codigo=codigo).exclude(pk=pk).exists():
            messages.error(request, f"Ya existe un programa con el código '{codigo}'.")
        else:
            sede = get_object_or_404(sedes_visibles(request.user), id=sede_id)
            facultad = get_object_or_404(facultades_visibles(request.user), id=fac_id)
            if programa:
                programa.codigo = codigo
                programa.nombre = nombre
                programa.sede = sede
                programa.facultad = facultad
                programa.nivel = nivel
                programa.activo = activo
                programa.save()
                messages.success(request, f"Programa '{programa.nombre}' actualizado.")
            else:
                Programa.objects.create(
                    codigo=codigo,
                    nombre=nombre,
                    sede=sede,
                    facultad=facultad,
                    nivel=nivel,
                    activo=activo,
                )
                messages.success(request, f"Programa '{nombre}' creado exitosamente.")
            return redirect("panel:organizacion_list")
    return render(
        request,
        "panel/programa_form.html",
        {
            "programa": programa,
            "data": data,
            "sedes": sedes_visibles(request.user).order_by("nombre"),
            "facultades": facultades_visibles(request.user).order_by("nombre"),
            "niveles": Programa.OPCIONES_NIVEL,
        },
    )


@require_POST
@requiere_permiso("catalogos.administrar")
def programa_toggle(request, pk):
    prog = get_object_or_404(programas_visibles(request.user), pk=pk)
    prog.activo = not prog.activo
    prog.save()
    estado = "activado" if prog.activo else "inactivado"
    messages.success(request, f"Programa '{prog.nombre}' {estado}.")
    return redirect("panel:organizacion_list")


@requiere_permiso("catalogos.administrar")
def area_form(request, pk=None):
    if pk:
        area = get_object_or_404(areas_visibles(request.user), pk=pk)
    else:
        if not alcance_es_global(request.user):
            messages.error(request, "Solo usuarios con alcance global pueden crear áreas.")
            return redirect("panel:organizacion_list")
        area = None
    data = {
        "codigo": area.codigo if area else "",
        "nombre": area.nombre if area else "",
        "activo": area.activo if area else True,
    }
    if request.method == "POST":
        codigo = request.POST.get("codigo", "").strip().upper()
        nombre = request.POST.get("nombre", "").strip()
        activo = request.POST.get("activo") in ("on", "true", "1")
        data = {"codigo": codigo, "nombre": nombre, "activo": activo}
        if not (codigo and nombre):
            messages.error(request, "Código y nombre son obligatorios.")
        elif Area.objects.filter(codigo=codigo).exclude(pk=pk).exists():
            messages.error(request, f"Ya existe un área con el código '{codigo}'.")
        else:
            if area:
                area.codigo, area.nombre, area.activo = codigo, nombre, activo
                area.save()
                messages.success(request, f"Área '{area.codigo}' actualizada.")
            else:
                Area.objects.create(codigo=codigo, nombre=nombre, activo=activo)
                messages.success(request, f"Área '{codigo}' creada exitosamente.")
            return redirect("panel:organizacion_list")
    return render(request, "panel/area_form.html", {"area": area, "data": data})


@require_POST
@requiere_permiso("catalogos.administrar")
def area_toggle(request, pk):
    area = get_object_or_404(areas_visibles(request.user), pk=pk)
    area.activo = not area.activo
    area.save()
    estado = "activada" if area.activo else "inactivada"
    messages.success(request, f"Área '{area.codigo}' {estado}.")
    return redirect("panel:organizacion_list")
