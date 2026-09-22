import qrcode
from io import BytesIO
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.db.models import Q
from accounts.alcance import areas_visibles, equipos_visibles, personas_visibles, puede_ver_objeto
from accounts.decorators import requiere_permiso
from config.pagination import paginate_queryset
from .models import Equipo
from .services import asignacion_activa, nombre_unidad, vigencia_asignacion
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
        if request.user.tiene_permiso("equipos.ver_todos"):
            return redirect("equipos:equipos_list")
        messages.warning(
            request,
            "Su usuario no tiene vinculada una ficha de persona de la comunidad académica."
        )
        equipos = Equipo.objects.none()
        equipos_baja = Equipo.objects.none()
    else:
        equipos = Equipo.objects.filter(persona=persona, activo=True)
        equipos_baja = Equipo.objects.filter(
            persona=persona,
            propiedad=Equipo.PROPIEDAD_PERSONAL,
            activo=False,
        ).order_by("-updated_at")

    equipos_ctx = []
    for e in equipos:
        unidad_nombre = ""
        vigencia = ""
        if e.propiedad == Equipo.PROPIEDAD_INSTITUCIONAL:
            from equipos.services import unidad_de_equipo

            ut, uid = unidad_de_equipo(e)
            unidad_nombre = nombre_unidad(ut, uid)
            asig = asignacion_activa(e)
            if asig:
                vigencia = vigencia_asignacion(asig)
            elif e.estado_inventario == Equipo.ESTADO_DISPONIBLE:
                vigencia = "disponible"
        equipos_ctx.append(
            {
                "equipo": e,
                "unidad_nombre": unidad_nombre,
                "vigencia": vigencia,
            }
        )

    context = {
        "persona": persona,
        "equipos": equipos,
        "equipos_ctx": equipos_ctx,
        "equipos_baja": equipos_baja,
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

    equipos = equipos_visibles(request.user).select_related(
        "persona", "persona__sede", "dependencia"
    )

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

    page = paginate_queryset(request, equipos)

    context = {
        "equipos": page,
        "page_obj": page,
        "query": query,
        "tipo_filtro": tipo_filtro,
        "propiedad_filtro": propiedad_filtro,
        "dependencia_filtro": dependencia_filtro,
        "activo_filtro": activo_filtro,
        "tipos_equipo": Equipo.OPCIONES_TIPO,
        "propiedades": Equipo.OPCIONES_PROPIEDAD,
        "areas": areas_visibles(request.user).order_by("nombre"),
    }
    return render(request, "equipos/equipo_list.html", context)


@login_required
def equipo_detail(request, pk):
    """Detalle de un equipo y vista para mostrar su pase QR."""
    equipo = get_object_or_404(
        Equipo.objects.select_related(
            "persona", "persona__sede", "persona__programa", "dependencia"
        ),
        pk=pk,
    )
    persona_usuario = getattr(request.user, "persona", None)
    es_dueno = bool(persona_usuario and equipo.persona_id == persona_usuario.pk)
    es_admin_con_alcance = request.user.tiene_permiso(
        "equipos.ver_todos"
    ) and puede_ver_objeto(request.user, equipo)
    if not es_dueno and not es_admin_con_alcance:
        messages.error(request, "No tiene permiso para ver este equipo.")
        if request.user.tiene_permiso("equipos.ver_todos"):
            return redirect("equipos:equipos_list")
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
    """Autoregistro de equipos personales únicamente (doc 14: R1/R5)."""
    persona_usuario = getattr(request.user, "persona", None)
    es_admin_inventario = request.user.tiene_permiso("equipos.ver_todos")

    # Los institucionales solo se crean desde el panel de asignación
    if es_admin_inventario and request.method == "GET":
        messages.info(
            request,
            "Los equipos institucionales se asignan desde el panel: "
            "Asignar equipo institucional.",
        )

    if request.method == "POST":
        propiedad = request.POST.get("propiedad", Equipo.PROPIEDAD_PERSONAL)
        if propiedad == Equipo.PROPIEDAD_INSTITUCIONAL:
            messages.error(
                request,
                "No puede registrar un equipo institucional desde este formulario. "
                "Use la asignación por dependencia en el panel.",
            )
            return redirect("equipos:equipo_create")

        if es_admin_inventario:
            persona_id = request.POST.get("persona")
            persona = get_object_or_404(personas_visibles(request.user), id=persona_id)
        else:
            if not persona_usuario:
                messages.error(request, "No tiene un perfil de persona asociado para registrar equipos.")
                return redirect("equipos:mis_equipos")
            persona = persona_usuario

        tipo = request.POST.get("tipo", Equipo.TIPO_PORTATIL)
        marca = request.POST.get("marca", "").strip()
        modelo = request.POST.get("modelo", "").strip()
        serial = request.POST.get("serial", "").strip()

        if not (marca and modelo and serial):
            messages.error(request, "Por favor diligencie todos los campos obligatorios.")
        elif Equipo.objects.filter(serial__iexact=serial).exists():
            messages.error(request, f"Ya existe un equipo registrado con el serial {serial}.")
        else:
            equipo = Equipo(
                persona=persona,
                tipo=tipo,
                marca=marca,
                modelo=modelo,
                serial=serial,
                propiedad=Equipo.PROPIEDAD_PERSONAL,
                activo=True,
            )
            try:
                equipo.save()
            except ValidationError as exc:
                msgs = getattr(exc, "messages", None) or [str(exc)]
                for err in msgs:
                    messages.error(request, err)
            else:
                messages.success(request, f"Equipo {marca} {modelo} registrado exitosamente.")
                return redirect("equipos:equipo_detail", pk=equipo.pk)

    personas = (
        personas_visibles(request.user).filter(activo=True).select_related("sede")
        if es_admin_inventario
        else []
    )

    context = {
        "persona_usuario": persona_usuario,
        "personas": personas,
        "tipos_equipo": Equipo.OPCIONES_TIPO,
        "propiedades": [(Equipo.PROPIEDAD_PERSONAL, "Personal (Propiedad del Miembro)")],
        "areas": [],
        "es_admin": es_admin_inventario,
        "solo_personal": True,
    }
    return render(request, "equipos/equipo_form.html", context)


def _usuario_puede_ver_qr(user, equipo) -> bool:
    if user.tiene_permiso("equipos.ver_todos"):
        return True
    persona = getattr(user, "persona", None)
    return bool(persona and equipo.persona_id == persona.id)


@login_required
def ver_qr_pantalla(request, token_qr):
    """
    Vista optimizada para celular para mostrar el QR en pantalla completa
    al salir por la portería. Solo dueño o quien tenga equipos.ver_todos.
    """
    equipo = get_object_or_404(
        Equipo.objects.select_related("persona", "persona__sede"),
        token_qr=token_qr,
    )
    if not _usuario_puede_ver_qr(request.user, equipo):
        messages.error(request, "No tiene permiso para ver el QR de este equipo.")
        return redirect("equipos:mis_equipos")

    if not equipo.activo or not equipo.persona.activo:
        messages.error(
            request,
            "El equipo o el titular se encuentra inactivo. Presente su documento en portería.",
        )

    context = {
        "equipo": equipo,
        "persona": equipo.persona,
        "qr_base64": equipo.generar_qr_base64(),
    }
    return render(request, "equipos/mostrar_qr_pantalla.html", context)


@login_required
def render_qr_image(request, token_qr):
    """
    Genera el PNG del QR al vuelo (token de exhibición firmado).
    Requiere autenticación y ser dueño o admin de equipos.
    """
    equipo = get_object_or_404(Equipo, token_qr=token_qr)
    if not _usuario_puede_ver_qr(request.user, equipo):
        raise Http404()

    payload = equipo.generar_token_exhibicion()
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return HttpResponse(buffer.getvalue(), content_type="image/png")
