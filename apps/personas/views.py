from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q

from .models import Persona, TipoVinculo
from organizacion.models import Sede, Programa
from accounts.models import Rol
from accounts.decorators import requiere_permiso


@requiere_permiso("personas.administrar")
def persona_list(request):
    """Listado de la comunidad académica registrada."""
    query = request.GET.get("q", "").strip()
    vinculo_filtro = request.GET.get("vinculo", "").strip()
    sede_filtro = request.GET.get("sede", "").strip()

    personas = Persona.objects.select_related("sede", "programa", "tipo_vinculo").all()

    if query:
        personas = personas.filter(
            Q(numero_documento__icontains=query)
            | Q(nombres__icontains=query)
            | Q(apellidos__icontains=query)
        )

    if vinculo_filtro:
        personas = personas.filter(tipo_vinculo__codigo=vinculo_filtro)

    if sede_filtro:
        personas = personas.filter(sede__codigo=sede_filtro)

    sedes = Sede.objects.filter(activo=True)
    tipos_vinculo = TipoVinculo.objects.filter(activo=True).order_by("nombre")

    context = {
        "personas": personas,
        "query": query,
        "vinculo_filtro": vinculo_filtro,
        "sede_filtro": sede_filtro,
        "tipos_vinculo": tipos_vinculo,
        "sedes": sedes,
    }
    return render(request, "personas/persona_list.html", context)


@requiere_permiso("personas.administrar")
def persona_detail(request, pk):
    """Detalle de una persona y listado de todos sus equipos."""
    persona = get_object_or_404(
        Persona.objects.select_related("sede", "programa", "tipo_vinculo"),
        pk=pk,
    )
    equipos = persona.equipos.filter(activo=True)

    context = {
        "persona": persona,
        "equipos": equipos,
    }
    return render(request, "personas/persona_detail.html", context)


@requiere_permiso("personas.administrar")
def persona_create(request):
    """Formulario para registrar un nuevo integrante de la comunidad (Administrativo)."""
    if request.method == "POST":
        tipo_doc = request.POST.get("tipo_documento", "CC")
        num_doc = request.POST.get("numero_documento", "").strip()
        nombres = request.POST.get("nombres", "").strip()
        apellidos = request.POST.get("apellidos", "").strip()
        tipo_vinculo_id = request.POST.get("tipo_vinculo")
        sede_id = request.POST.get("sede")
        programa_id = request.POST.get("programa") or None

        if not (num_doc and nombres and apellidos and tipo_vinculo_id and sede_id):
            messages.error(request, "Por favor complete todos los campos requeridos.")
        elif Persona.objects.filter(numero_documento=num_doc).exists():
            messages.error(request, f"Ya existe una persona con el documento {num_doc}.")
        else:
            sede = get_object_or_404(Sede, id=sede_id)
            tipo_vinculo = get_object_or_404(TipoVinculo, id=tipo_vinculo_id)
            programa = get_object_or_404(Programa, id=programa_id) if programa_id else None

            persona = Persona.objects.create(
                tipo_documento=tipo_doc,
                numero_documento=num_doc,
                nombres=nombres,
                apellidos=apellidos,
                tipo_vinculo=tipo_vinculo,
                sede=sede,
                programa=programa,
                activo=True,
            )
            messages.success(request, f"Persona {persona.nombre_completo} registrada exitosamente.")
            return redirect("personas:persona_detail", pk=persona.pk)

    sedes = Sede.objects.filter(activo=True)
    programas = Programa.objects.filter(activo=True).select_related("sede", "facultad")
    tipos_vinculo = TipoVinculo.objects.filter(activo=True).order_by("nombre")

    context = {
        "tipos_vinculo": tipos_vinculo,
        "sedes": sedes,
        "programas": programas,
    }
    return render(request, "personas/persona_form.html", context)


# -------------------------------------------------------------------------
# Administración del Catálogo Dinámico de Tipos de Vínculo (Documento 06)
# -------------------------------------------------------------------------

@requiere_permiso("catalogos.administrar")
def tipo_vinculo_list(request):
    """Listado y gestión administrativa de tipos de vínculo."""
    tipos = TipoVinculo.objects.select_related("rol_asignado").all().order_by("nombre")
    return render(request, "personas/tipo_vinculo_list.html", {"tipos": tipos})


@requiere_permiso("catalogos.administrar")
def tipo_vinculo_form(request, pk=None):
    """Creación o edición de un tipo de vínculo institucional."""
    tipo = get_object_or_404(TipoVinculo, pk=pk) if pk else None

    data = {
        "codigo": tipo.codigo if tipo else "",
        "nombre": tipo.nombre if tipo else "",
        "permite_autoregistro": tipo.permite_autoregistro if tipo else False,
        "dominio_correo_requerido": tipo.dominio_correo_requerido or "" if tipo else "",
        "rol_asignado": str(tipo.rol_asignado_id) if (tipo and tipo.rol_asignado_id) else "",
        "activo": tipo.activo if tipo else True,
    }

    if request.method == "POST":
        codigo = request.POST.get("codigo", "").strip().lower()
        nombre = request.POST.get("nombre", "").strip()
        permite_autoregistro = request.POST.get("permite_autoregistro") in ("on", "true", "1")
        dominio = request.POST.get("dominio_correo_requerido", "").strip() or None
        rol_id = request.POST.get("rol_asignado") or None
        activo = request.POST.get("activo") in ("on", "true", "1")

        data = {
            "codigo": codigo,
            "nombre": nombre,
            "permite_autoregistro": permite_autoregistro,
            "dominio_correo_requerido": dominio or "",
            "rol_asignado": str(rol_id) if rol_id else "",
            "activo": activo,
        }

        rol_asignado = None
        if rol_id:
            rol_asignado = get_object_or_404(Rol, id=rol_id)
            # Regla 3.2: no permitir roles sensibles en autorregistro
            if permite_autoregistro and rol_asignado.nombre in ("admin_sistema", "celador"):
                messages.error(
                    request,
                    "Por motivos de seguridad institucional, los roles de 'admin_sistema' y 'celador' no pueden asignarse a vínculos con autorregistro público."
                )
                roles = Rol.objects.filter(activo=True).order_by("nombre")
                return render(
                    request,
                    "personas/tipo_vinculo_form.html",
                    {"tipo": tipo, "roles": roles, "data": data},
                )

        if not (codigo and nombre):
            messages.error(request, "El código y el nombre son campos obligatorios.")
        elif TipoVinculo.objects.filter(codigo=codigo).exclude(pk=pk).exists():
            messages.error(request, f"Ya existe un tipo de vínculo con el código '{codigo}'.")
        else:
            if tipo:
                tipo.codigo = codigo
                tipo.nombre = nombre
                tipo.permite_autoregistro = permite_autoregistro
                tipo.dominio_correo_requerido = dominio
                tipo.rol_asignado = rol_asignado
                tipo.activo = activo
                tipo.save()
                messages.success(request, f"Tipo de vínculo '{tipo.nombre}' actualizado correctamente.")
            else:
                tipo = TipoVinculo.objects.create(
                    codigo=codigo,
                    nombre=nombre,
                    permite_autoregistro=permite_autoregistro,
                    dominio_correo_requerido=dominio,
                    rol_asignado=rol_asignado,
                    activo=activo,
                )
                messages.success(request, f"Tipo de vínculo '{tipo.nombre}' creado exitosamente.")
            return redirect("personas:tipo_vinculo_list")

    roles = Rol.objects.filter(activo=True).order_by("nombre")
    return render(
        request,
        "personas/tipo_vinculo_form.html",
        {"tipo": tipo, "roles": roles, "data": data},
    )


@require_POST
@requiere_permiso("catalogos.administrar")
def tipo_vinculo_toggle(request, pk):
    """Activar o desactivar un tipo de vínculo institucional."""
    tipo = get_object_or_404(TipoVinculo, pk=pk)
    tipo.activo = not tipo.activo
    tipo.save()
    estado = "activado" if tipo.activo else "desactivado"
    messages.success(request, f"Tipo de vínculo '{tipo.nombre}' {estado} exitosamente.")
    return redirect("personas:tipo_vinculo_list")

