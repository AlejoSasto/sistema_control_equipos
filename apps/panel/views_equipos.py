"""Vistas del panel: inventario y asignación institucional (docs 14–15)."""

from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.alcance import equipos_visibles, personas_visibles
from accounts.decorators import requiere_permiso
from accounts.models import Usuario
from config.pagination import paginate_queryset
from equipos.models import Equipo
from equipos.services import (
    POR_VENCER,
    VENCIDA,
    VIGENTE,
    asignacion_activa,
    crear_asignacion,
    crear_equipo_inventario,
    dar_de_baja_institucional,
    devolver_al_inventario,
    es_admin_global,
    estado_listado_equipo,
    filtro_equipos_institucionales_alcance,
    nombre_unidad,
    persona_pertenece_a,
    personas_de_unidad,
    puede_gestionar_equipo_institucional,
    puede_gestionar_unidad,
    sugerir_fecha_fin,
    tiene_alcance_asignacion,
    tiene_alcance_inventario,
    unidad_de_equipo,
    unidades_de,
)
from organizacion.models import (
    OPCIONES_UNIDAD_TIPO,
    UNIDAD_AREA,
    UNIDAD_FACULTAD,
    UNIDAD_PROGRAMA,
    Area,
    Decanatura,
    Programa,
    ResponsableDependencia,
)
from personas.models import Persona


def _parse_unidad_clave(clave: str):
    if not clave or ":" not in clave:
        return None, None
    tipo, raw_id = clave.split(":", 1)
    try:
        return tipo, int(raw_id)
    except (TypeError, ValueError):
        return None, None


def _parse_fecha(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


@login_required
@requiere_permiso("equipos.inventario_institucional")
def equipos_inventario_nuevo(request):
    """Alta de inventario: crea equipo institucional sin persona."""
    if not tiene_alcance_inventario(request.user):
        messages.error(
            request,
            "No tiene unidades asignadas como responsable de dependencia.",
        )
        return redirect("panel:index")

    unidades = unidades_de(request.user)
    unidad_clave = request.POST.get("unidad") or request.GET.get("unidad") or ""
    if not unidad_clave and len(unidades) == 1:
        unidad_clave = unidades[0].clave

    unidad_tipo, unidad_id = _parse_unidad_clave(unidad_clave)
    unidad_valida = (
        unidad_tipo
        and unidad_id
        and puede_gestionar_unidad(request.user, unidad_tipo, unidad_id)
    )

    if request.method == "POST":
        if not unidad_valida:
            messages.error(request, "Debe seleccionar una unidad válida de su alcance.")
        else:
            tipo = request.POST.get("tipo", Equipo.TIPO_PORTATIL)
            marca = request.POST.get("marca", "").strip()
            modelo = request.POST.get("modelo", "").strip()
            serial = request.POST.get("serial", "").strip()
            if not (marca and modelo and serial):
                messages.error(request, "Complete marca, modelo y serial.")
            else:
                try:
                    equipo = crear_equipo_inventario(
                        tipo=tipo,
                        marca=marca,
                        modelo=modelo,
                        serial=serial,
                        unidad_tipo=unidad_tipo,
                        unidad_id=unidad_id,
                        creado_por_usuario=request.user,
                    )
                except ValidationError as exc:
                    for msgs in (
                        exc.message_dict.values() if hasattr(exc, "message_dict") else [exc.messages]
                    ):
                        for err in msgs:
                            messages.error(request, err)
                else:
                    messages.success(
                        request,
                        f"Equipo {equipo.serial} dado de alta en inventario (disponible).",
                    )
                    return redirect("panel:equipos_institucionales")

    return render(
        request,
        "panel/equipos_inventario_nuevo.html",
        {
            "unidades": unidades,
            "unidad_clave": unidad_clave if unidad_valida else "",
            "tipos_equipo": Equipo.OPCIONES_TIPO,
        },
    )


@login_required
@requiere_permiso("equipos.asignar_institucional")
def equipos_asignar_institucional(request):
    """Asigna un equipo disponible a una persona con fechas de vigencia."""
    if not tiene_alcance_asignacion(request.user):
        messages.error(
            request,
            "No tiene unidades asignadas como responsable de dependencia.",
        )
        return redirect("panel:index")

    unidades = unidades_de(request.user)
    unidad_clave = request.POST.get("unidad") or request.GET.get("unidad") or ""
    if not unidad_clave and len(unidades) == 1:
        unidad_clave = unidades[0].clave

    unidad_tipo, unidad_id = _parse_unidad_clave(unidad_clave)
    unidad_valida = (
        unidad_tipo
        and unidad_id
        and puede_gestionar_unidad(request.user, unidad_tipo, unidad_id)
    )

    hoy = timezone.localdate()
    fecha_inicio = hoy
    fecha_fin = hoy
    equipo_pre = request.GET.get("equipo") or request.POST.get("equipo") or ""

    disponibles = Equipo.objects.none()
    if unidad_valida:
        disponibles = Equipo.objects.filter(
            propiedad=Equipo.PROPIEDAD_INSTITUCIONAL,
            unidad_tipo=unidad_tipo,
            unidad_id=unidad_id,
            estado_inventario=Equipo.ESTADO_DISPONIBLE,
            activo=True,
        ).order_by("marca", "modelo", "serial")

    if request.method == "POST":
        if not unidad_valida:
            messages.error(request, "Debe seleccionar una unidad válida de su alcance.")
        else:
            persona_id = request.POST.get("persona")
            equipo_id = request.POST.get("equipo")
            fecha_inicio = _parse_fecha(request.POST.get("fecha_inicio")) or hoy
            fecha_fin = _parse_fecha(request.POST.get("fecha_fin"))

            persona = personas_visibles(request.user).filter(
                pk=persona_id, activo=True
            ).select_related("programa", "area", "tipo_vinculo").first()
            equipo = disponibles.filter(pk=equipo_id).first()

            if not (persona and equipo and fecha_fin):
                messages.error(
                    request,
                    "Seleccione equipo disponible, persona y fechas obligatorias.",
                )
            elif fecha_fin < fecha_inicio:
                messages.error(request, "La fecha fin no puede ser anterior a la fecha inicio.")
            elif not persona_pertenece_a(persona, unidad_tipo, unidad_id):
                messages.error(
                    request,
                    "La persona seleccionada no pertenece a la unidad elegida.",
                )
            else:
                try:
                    crear_asignacion(
                        equipo=equipo,
                        persona=persona,
                        fecha_inicio=fecha_inicio,
                        fecha_fin=fecha_fin,
                        asignado_por_usuario=request.user,
                    )
                except ValidationError as exc:
                    messages.error(request, str(exc))
                else:
                    messages.success(
                        request,
                        f"Equipo {equipo.serial} asignado a {persona.nombre_completo}.",
                    )
                    return redirect("panel:equipos_institucionales")

    personas = []
    if unidad_valida:
        personas = list(
            personas_de_unidad(unidad_tipo, unidad_id).order_by("apellidos", "nombres")[:500]
        )

    return render(
        request,
        "panel/equipos_asignar_institucional.html",
        {
            "unidades": unidades,
            "unidad_clave": unidad_clave if unidad_valida else "",
            "personas": personas,
            "equipos_disponibles": list(disponibles),
            "equipo_pre": equipo_pre,
            "fecha_inicio": fecha_inicio.isoformat(),
            "fecha_fin": fecha_fin.isoformat(),
            "hoy": hoy.isoformat(),
        },
    )


@login_required
@requiere_permiso("equipos.asignar_institucional")
def sugerir_fecha_fin_persona(request):
    persona = personas_visibles(request.user).filter(
        pk=request.GET.get("persona")
    ).select_related("tipo_vinculo").first()
    inicio = _parse_fecha(request.GET.get("fecha_inicio")) or timezone.localdate()
    if not persona:
        return JsonResponse({"fecha_fin": inicio.isoformat()})
    return JsonResponse({"fecha_fin": sugerir_fecha_fin(persona, inicio).isoformat()})


@login_required
def equipos_institucionales_list(request):
    puede_listar = (
        request.user.tiene_permiso("equipos.asignar_institucional")
        or request.user.tiene_permiso("equipos.inventario_institucional")
        or request.user.tiene_permiso("equipos.ver_todos")
        or es_admin_global(request.user)
    )
    if not puede_listar:
        return HttpResponseForbidden("Sin permiso para ver equipos institucionales.")

    query = request.GET.get("q", "").strip()
    filtro_vigencia = request.GET.get("vigencia", "").strip()
    filtro_estado = request.GET.get("estado", "").strip()
    equipos = equipos_visibles(request.user).filter(
        filtro_equipos_institucionales_alcance(request.user)
    ).select_related("persona", "persona__sede", "dependencia")

    if filtro_estado == "disponible":
        equipos = equipos.filter(estado_inventario=Equipo.ESTADO_DISPONIBLE, activo=True)
    elif filtro_estado == "asignado":
        equipos = equipos.filter(estado_inventario=Equipo.ESTADO_ASIGNADO, activo=True)
    elif filtro_estado == "de_baja":
        equipos = equipos.filter(
            Q(estado_inventario=Equipo.ESTADO_DE_BAJA) | Q(activo=False)
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

    page = paginate_queryset(request, equipos)
    filas = []
    hoy = timezone.localdate()
    puede_asignar = (
        request.user.tiene_permiso("equipos.asignar_institucional")
        and tiene_alcance_asignacion(request.user)
    )
    for e in page:
        asig = asignacion_activa(e)
        estado = estado_listado_equipo(e, asig, hoy)
        if filtro_vigencia == "por_vencer" and estado != POR_VENCER:
            continue
        if filtro_vigencia == "vencida" and estado != VENCIDA:
            continue
        if filtro_vigencia == "vigente" and estado not in (VIGENTE, POR_VENCER):
            continue
        if filtro_vigencia == "disponible" and estado != "disponible":
            continue
        ut, uid = unidad_de_equipo(e)
        filas.append(
            {
                "equipo": e,
                "asignacion": asig,
                "unidad_nombre": nombre_unidad(ut, uid),
                "estado": estado,
                "puede_gestionar": puede_gestionar_equipo_institucional(request.user, e),
                "puede_asignar": puede_asignar,
            }
        )

    return render(
        request,
        "panel/equipos_institucionales_list.html",
        {
            "filas": filas,
            "page_obj": page,
            "query": query,
            "filtro_vigencia": filtro_vigencia,
            "filtro_estado": filtro_estado,
            "puede_asignar": puede_asignar,
            "puede_inventario": request.user.tiene_permiso("equipos.inventario_institucional")
            and tiene_alcance_inventario(request.user),
        },
    )


def _contexto_form_fechas(equipo, persona, request):
    hoy = timezone.localdate()
    fecha_inicio = _parse_fecha(request.POST.get("fecha_inicio")) if request.method == "POST" else hoy
    if not fecha_inicio:
        fecha_inicio = hoy
    fecha_fin = (
        _parse_fecha(request.POST.get("fecha_fin"))
        if request.method == "POST"
        else (sugerir_fecha_fin(persona, fecha_inicio) if persona else hoy)
    )
    ut, uid = unidad_de_equipo(equipo)
    return {
        "equipo": equipo,
        "unidad_nombre": nombre_unidad(ut, uid),
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": (fecha_fin or hoy).isoformat(),
        "hoy": hoy.isoformat(),
        "unidad_tipo": ut,
        "unidad_id": uid,
    }


@login_required
@requiere_permiso("equipos.asignar_institucional")
def equipo_reasignar(request, pk):
    equipo = get_object_or_404(
        equipos_visibles(request.user),
        pk=pk,
        propiedad=Equipo.PROPIEDAD_INSTITUCIONAL,
    )
    if not puede_gestionar_equipo_institucional(request.user, equipo):
        messages.error(request, "No puede reasignar un equipo fuera de su unidad.")
        return redirect("panel:equipos_institucionales")

    ut, uid = unidad_de_equipo(equipo)
    if not ut or not uid:
        messages.error(request, "El equipo no tiene unidad propietaria.")
        return redirect("panel:equipos_institucionales")

    personas = list(
        personas_visibles(request.user)
        .filter(pk__in=personas_de_unidad(ut, uid).values_list("pk", flat=True))
        .order_by("apellidos", "nombres")[:500]
    )

    if request.method == "POST":
        persona = get_object_or_404(
            personas_visibles(request.user).select_related("tipo_vinculo"),
            pk=request.POST.get("persona"),
            activo=True,
        )
        fecha_inicio = _parse_fecha(request.POST.get("fecha_inicio")) or timezone.localdate()
        fecha_fin = _parse_fecha(request.POST.get("fecha_fin"))
        if not fecha_fin:
            messages.error(request, "La fecha fin es obligatoria.")
        elif fecha_fin < fecha_inicio:
            messages.error(request, "La fecha fin no puede ser anterior a la fecha inicio.")
        elif not persona_pertenece_a(persona, ut, uid):
            messages.error(request, "La persona no pertenece a la unidad del equipo.")
        else:
            try:
                crear_asignacion(
                    equipo=equipo,
                    persona=persona,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    asignado_por_usuario=request.user,
                )
            except ValidationError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, f"Equipo reasignado a {persona.nombre_completo}.")
                return redirect("panel:equipos_institucionales")

    ctx = _contexto_form_fechas(equipo, equipo.persona, request)
    ctx["personas"] = personas
    ctx["modo"] = "reasignar"
    return render(request, "panel/equipo_reasignar.html", ctx)


@login_required
@requiere_permiso("equipos.asignar_institucional")
def equipo_renovar(request, pk):
    equipo = get_object_or_404(
        equipos_visibles(request.user),
        pk=pk,
        propiedad=Equipo.PROPIEDAD_INSTITUCIONAL,
    )
    if not puede_gestionar_equipo_institucional(request.user, equipo):
        messages.error(request, "No puede renovar un equipo fuera de su unidad.")
        return redirect("panel:equipos_institucionales")

    persona = equipo.persona
    if not persona:
        messages.error(request, "El equipo no tiene titular; use Asignar.")
        return redirect("panel:equipos_asignar_institucional")

    if request.method == "POST":
        fecha_inicio = _parse_fecha(request.POST.get("fecha_inicio")) or timezone.localdate()
        fecha_fin = _parse_fecha(request.POST.get("fecha_fin"))
        if not fecha_fin:
            messages.error(request, "La fecha fin es obligatoria.")
        elif fecha_fin < fecha_inicio:
            messages.error(request, "La fecha fin no puede ser anterior a la fecha inicio.")
        else:
            try:
                crear_asignacion(
                    equipo=equipo,
                    persona=persona,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    asignado_por_usuario=request.user,
                )
            except ValidationError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(
                    request,
                    f"Asignación renovada para {persona.nombre_completo}.",
                )
                return redirect("panel:equipos_institucionales")

    ctx = _contexto_form_fechas(equipo, persona, request)
    ctx["modo"] = "renovar"
    ctx["persona"] = persona
    return render(request, "panel/equipo_renovar.html", ctx)


@login_required
@requiere_permiso("equipos.asignar_institucional")
@require_POST
def equipo_devolver_inventario(request, pk):
    equipo = get_object_or_404(
        equipos_visibles(request.user),
        pk=pk,
        propiedad=Equipo.PROPIEDAD_INSTITUCIONAL,
    )
    if not puede_gestionar_equipo_institucional(request.user, equipo):
        messages.error(request, "No puede devolver un equipo fuera de su unidad.")
        return redirect("panel:equipos_institucionales")
    try:
        devolver_al_inventario(equipo)
    except ValidationError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"Equipo {equipo.serial} devuelto al inventario (disponible).")
    return redirect("panel:equipos_institucionales")


@login_required
@require_POST
def equipo_dar_de_baja(request, pk):
    equipo = get_object_or_404(Equipo, pk=pk)
    user = request.user
    permitido = False

    if equipo.propiedad == Equipo.PROPIEDAD_INSTITUCIONAL:
        permitido = (
            puede_gestionar_equipo_institucional(user, equipo)
            and (
                user.tiene_permiso("equipos.inventario_institucional")
                or user.tiene_permiso("equipos.asignar_institucional")
                or es_admin_global(user)
            )
        )
    else:
        persona = getattr(user, "persona", None)
        permitido = bool(
            (persona and equipo.persona_id == persona.id)
            or user.tiene_permiso("equipos.ver_todos")
            or es_admin_global(user)
        )

    if not permitido:
        messages.error(request, "No tiene permiso para dar de baja este equipo.")
        if equipo.propiedad == Equipo.PROPIEDAD_INSTITUCIONAL:
            return redirect("panel:equipos_institucionales")
        return redirect("equipos:mis_equipos")

    if not equipo.activo or equipo.estado_inventario == Equipo.ESTADO_DE_BAJA:
        messages.info(request, "El equipo ya estaba de baja.")
    else:
        if equipo.propiedad == Equipo.PROPIEDAD_INSTITUCIONAL:
            dar_de_baja_institucional(equipo)
        else:
            Equipo.objects.filter(pk=equipo.pk).update(activo=False)
        messages.success(request, f"Equipo {equipo.serial} dado de baja.")

    if equipo.propiedad == Equipo.PROPIEDAD_INSTITUCIONAL:
        return redirect("panel:equipos_institucionales")
    return redirect("equipos:mis_equipos")


@login_required
@require_POST
def equipo_dar_de_alta(request, pk):
    """Reactiva un equipo personal dado de baja (activo=True). No aplica a institucionales."""
    equipo = get_object_or_404(Equipo, pk=pk)
    user = request.user

    if equipo.propiedad != Equipo.PROPIEDAD_PERSONAL:
        messages.error(
            request,
            "Solo se puede dar de alta un equipo personal. Los institucionales se gestionan en inventario.",
        )
        return redirect("equipos:mis_equipos")

    persona = getattr(user, "persona", None)
    permitido = bool(
        (persona and equipo.persona_id == persona.id)
        or user.tiene_permiso("equipos.ver_todos")
        or es_admin_global(user)
    )
    if not permitido:
        messages.error(request, "No tiene permiso para dar de alta este equipo.")
        return redirect("equipos:mis_equipos")

    if equipo.activo:
        messages.info(request, "El equipo ya estaba activo.")
    else:
        Equipo.objects.filter(pk=equipo.pk).update(activo=True)
        messages.success(
            request,
            f"Equipo {equipo.serial} dado de alta. El QR vuelve a ser válido en portería.",
        )
    return redirect("equipos:mis_equipos")


def _etiqueta_unidad_responsable(fila: ResponsableDependencia) -> str:
    return nombre_unidad(fila.unidad_tipo, fila.unidad_id) or f"{fila.unidad_tipo}:{fila.unidad_id}"


@login_required
@requiere_permiso("equipos.gestionar_responsables")
def responsables_list(request):
    filas = ResponsableDependencia.objects.select_related("usuario").order_by(
        "-activo", "unidad_tipo", "unidad_id"
    )
    page = paginate_queryset(request, filas)
    items = [
        {"fila": f, "unidad_nombre": _etiqueta_unidad_responsable(f)} for f in page
    ]
    return render(
        request,
        "panel/responsables_list.html",
        {"items": items, "page_obj": page},
    )


@login_required
@requiere_permiso("equipos.gestionar_responsables")
def responsable_form(request, pk=None):
    instancia = get_object_or_404(ResponsableDependencia, pk=pk) if pk else None

    if request.method == "POST":
        usuario_id = request.POST.get("usuario")
        unidad_tipo = request.POST.get("unidad_tipo", "").strip()
        unidad_id_raw = request.POST.get("unidad_id", "").strip()
        activo = request.POST.get("activo") == "1"

        try:
            unidad_id = int(unidad_id_raw)
        except (TypeError, ValueError):
            unidad_id = None

        usuario = Usuario.objects.filter(pk=usuario_id, activo=True).first()
        unidad_ok = False
        if unidad_tipo == UNIDAD_FACULTAD:
            unidad_ok = Decanatura.objects.filter(pk=unidad_id, activo=True).exists()
        elif unidad_tipo == UNIDAD_PROGRAMA:
            unidad_ok = Programa.objects.filter(pk=unidad_id, activo=True).exists()
        elif unidad_tipo == UNIDAD_AREA:
            unidad_ok = Area.objects.filter(pk=unidad_id, activo=True).exists()

        if not usuario or not unidad_ok:
            messages.error(request, "Usuario o unidad inválidos.")
        else:
            if instancia:
                instancia.usuario = usuario
                instancia.unidad_tipo = unidad_tipo
                instancia.unidad_id = unidad_id
                instancia.activo = activo
                instancia.save()
                messages.success(request, "Responsable actualizado.")
            else:
                obj, created = ResponsableDependencia.objects.update_or_create(
                    usuario=usuario,
                    unidad_tipo=unidad_tipo,
                    unidad_id=unidad_id,
                    defaults={"activo": activo},
                )
                messages.success(
                    request,
                    "Responsable creado." if created else "Responsable reactivado/actualizado.",
                )
            return redirect("panel:responsables_list")

    return render(
        request,
        "panel/responsable_form.html",
        {
            "instancia": instancia,
            "usuarios": Usuario.objects.filter(activo=True).order_by("username"),
            "opciones_unidad_tipo": OPCIONES_UNIDAD_TIPO,
            "facultades": Decanatura.objects.filter(activo=True).order_by("nombre"),
            "programas": Programa.objects.filter(activo=True).select_related("sede").order_by("nombre"),
            "areas": Area.objects.filter(activo=True).order_by("nombre"),
        },
    )


@login_required
@requiere_permiso("equipos.gestionar_responsables")
@require_POST
def responsable_toggle(request, pk):
    fila = get_object_or_404(ResponsableDependencia, pk=pk)
    fila.activo = not fila.activo
    fila.save(update_fields=["activo"])
    estado = "activado" if fila.activo else "desactivado"
    messages.success(request, f"Responsable {estado}.")
    return redirect("panel:responsables_list")


@login_required
@requiere_permiso("equipos.asignar_institucional")
def buscar_personas_unidad(request):
    unidad_tipo, unidad_id = _parse_unidad_clave(request.GET.get("unidad", ""))
    q = request.GET.get("q", "").strip()
    if not unidad_tipo or not unidad_id or not puede_gestionar_unidad(request.user, unidad_tipo, unidad_id):
        return render(request, "panel/partials/personas_unidad_options.html", {"personas": []})

    qs = personas_de_unidad(unidad_tipo, unidad_id)
    if q:
        qs = qs.filter(
            Q(numero_documento__icontains=q)
            | Q(nombres__icontains=q)
            | Q(apellidos__icontains=q)
        )
    return render(
        request,
        "panel/partials/personas_unidad_options.html",
        {"personas": qs.order_by("apellidos", "nombres")[:50]},
    )
