import qrcode
from io import BytesIO
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.db.models import Q
from accounts.decorators import requiere_permiso
from organizacion.models import Area
from .models import Equipo
from personas.models import Persona


@login_required
@requiere_permiso("equipos.ver_propios")
def mis_equipos(request):
    """
    Vista para que el miembro de la comunidad académica vea sus propios equipos
    y pueda mostrar el QR desde su celular/pantalla al salir del campus.
    """
    persona = getattr(request.user, "persona", None)
    if not persona:
        # Si el usuario es administrador sin ficha de persona, mostrar listado general
        if request.user.tiene_permiso("equipos.ver_todos"):
            return redirect("equipos:equipos_list")
        messages.warning(
            request,
            "Su usuario no tiene vinculada una ficha de persona de la comunidad académica."
        )
        equipos = Equipo.objects.none()
    else:
        equipos = Equipo.objects.filter(persona=persona, activo=True)

    context = {
        "persona": persona,
        "equipos": equipos,
    }
    return render(request, "equipos/mis_equipos.html", context)


@login_required
@requiere_permiso("equipos.ver_todos")
def equipo_list(request):
    """Listado del inventario de todos los equipos registrados (uso administrativo)."""
    query = request.GET.get("q", "").strip()
    tipo_filtro = request.GET.get("tipo", "")
    propiedad_filtro = request.GET.get("propiedad", "")
    activo_filtro = request.GET.get("activo", "")

    dependencia_filtro = request.GET.get("dependencia", "")

    equipos = Equipo.objects.select_related("persona", "persona__sede", "dependencia").all()

    if query:
        equipos = equipos.filter(
            Q(serial__icontains=query)
            | Q(marca__icontains=query)
            | Q(modelo__icontains=query)
            | Q(persona__nombres__icontains=query)
            | Q(persona__apellidos__icontains=query)
            | Q(persona__numero_documento__icontains=query)
        )

    if tipo_filtro:
        equipos = equipos.filter(tipo=tipo_filtro)

    if propiedad_filtro:
        equipos = equipos.filter(propiedad=propiedad_filtro)

    if dependencia_filtro:
        equipos = equipos.filter(dependencia_id=dependencia_filtro)

    if activo_filtro != "":
        equipos = equipos.filter(activo=(activo_filtro == "1"))

    context = {
        "equipos": equipos,
        "query": query,
        "tipo_filtro": tipo_filtro,
        "propiedad_filtro": propiedad_filtro,
        "dependencia_filtro": dependencia_filtro,
        "activo_filtro": activo_filtro,
        "tipos_equipo": Equipo.OPCIONES_TIPO,
        "propiedades": Equipo.OPCIONES_PROPIEDAD,
        "areas": Area.objects.filter(activo=True).order_by("nombre"),
    }
    return render(request, "equipos/equipo_list.html", context)


@login_required
def equipo_detail(request, pk):
    """Detalle de un equipo y vista para mostrar su pase QR."""
    equipo = get_object_or_404(
        Equipo.objects.select_related("persona", "persona__sede", "persona__programa", "dependencia"),
        pk=pk,
    )
    # Validar que el usuario sea el dueño o tenga permiso administrativo
    if not request.user.tiene_permiso("equipos.ver_todos"):
        if not getattr(request.user, "persona", None) or equipo.persona != request.user.persona:
            messages.error(request, "No tiene permiso para ver este equipo.")
            return redirect("equipos:mis_equipos")

    movimientos = equipo.movimientos.select_related("usuario_control").all()[:10]

    context = {
        "equipo": equipo,
        "persona": equipo.persona,
        "movimientos": movimientos,
        "qr_base64": equipo.generar_qr_base64(),
    }
    return render(request, "equipos/equipo_detail.html", context)


@login_required
@requiere_permiso("equipos.registrar")
def equipo_create(request):
    """Vista para registrar equipos personales o institucionales."""
    persona_usuario = getattr(request.user, "persona", None)

    if request.method == "POST":
        # Si es admin, puede elegir la persona; si no, es su propia persona
        if request.user.tiene_permiso("equipos.ver_todos"):
            persona_id = request.POST.get("persona")
            persona = get_object_or_404(Persona, id=persona_id)
        else:
            if not persona_usuario:
                messages.error(request, "No tiene un perfil de persona asociado para registrar equipos.")
                return redirect("equipos:mis_equipos")
            persona = persona_usuario

        tipo = request.POST.get("tipo", Equipo.TIPO_PORTATIL)
        marca = request.POST.get("marca", "").strip()
        modelo = request.POST.get("modelo", "").strip()
        serial = request.POST.get("serial", "").strip()
        propiedad = request.POST.get("propiedad", Equipo.PROPIEDAD_PERSONAL)
        dependencia_id = request.POST.get("dependencia", "").strip()

        if not (marca and modelo and serial):
            messages.error(request, "Por favor diligencie todos los campos obligatorios.")
        elif Equipo.objects.filter(serial__iexact=serial).exists():
            messages.error(request, f"Ya existe un equipo registrado con el serial {serial}.")
        elif propiedad == Equipo.PROPIEDAD_INSTITUCIONAL and not dependencia_id:
            messages.error(request, "Debe seleccionar la dependencia que asigna el equipo institucional.")
        else:
            dependencia = (
                get_object_or_404(Area, id=dependencia_id, activo=True)
                if propiedad == Equipo.PROPIEDAD_INSTITUCIONAL
                else None
            )
            equipo = Equipo(
                persona=persona,
                tipo=tipo,
                marca=marca,
                modelo=modelo,
                serial=serial,
                propiedad=propiedad,
                dependencia=dependencia,
                activo=True,
            )
            try:
                equipo.save()
            except ValidationError as exc:
                for err in exc.message_dict.get("dependencia", exc.messages):
                    messages.error(request, err)
                return render(
                    request,
                    "equipos/equipo_form.html",
                    {
                        "persona_usuario": persona_usuario,
                        "personas": Persona.objects.filter(activo=True).select_related("sede")
                        if request.user.tiene_permiso("equipos.ver_todos")
                        else [],
                        "tipos_equipo": Equipo.OPCIONES_TIPO,
                        "propiedades": Equipo.OPCIONES_PROPIEDAD,
                        "areas": Area.objects.filter(activo=True).order_by("nombre"),
                        "es_admin": request.user.tiene_permiso("equipos.ver_todos"),
                    },
                )
            messages.success(request, f"Equipo {marca} {modelo} registrado exitosamente.")
            return redirect("equipos:equipo_detail", pk=equipo.pk)

    personas = Persona.objects.filter(activo=True).select_related("sede") if request.user.tiene_permiso("equipos.ver_todos") else []

    context = {
        "persona_usuario": persona_usuario,
        "personas": personas,
        "tipos_equipo": Equipo.OPCIONES_TIPO,
        "propiedades": Equipo.OPCIONES_PROPIEDAD,
        "areas": Area.objects.filter(activo=True).order_by("nombre"),
        "es_admin": request.user.tiene_permiso("equipos.ver_todos"),
    }
    return render(request, "equipos/equipo_form.html", context)


@login_required
def ver_qr_pantalla(request, token_qr):
    """
    Vista optimizada para celular para mostrar el QR en pantalla completa
    al salir por la portería.
    """
    equipo = get_object_or_404(
        Equipo.objects.select_related("persona", "persona__sede"),
        token_qr=token_qr,
    )
    # Regla 7 del Doc 01: Si persona está inactiva o equipo inactivo, no muestra QR válido
    if not equipo.activo or not equipo.persona.activo:
        messages.error(request, "El equipo o el titular se encuentra inactivo. Presente su documento en portería.")

    context = {
        "equipo": equipo,
        "persona": equipo.persona,
        "qr_base64": equipo.generar_qr_base64(),
    }
    return render(request, "equipos/mostrar_qr_pantalla.html", context)


def render_qr_image(request, token_qr):
    """
    Genera el PNG del código QR al vuelo a partir del token_qr
    sin guardar archivos en disco.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(str(token_qr))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return HttpResponse(buffer.getvalue(), content_type="image/png")
