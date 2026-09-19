from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import requiere_permiso
from accounts.models import Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from config.pagination import paginate_queryset
from organizacion.models import Area, Programa, Sede
from personas.models import CODIGO_VINCULO_ADMINISTRATIVO, Persona, TipoVinculo

from .services import (
    permisos_agrupados,
    registrar_cambio,
    validate_role_assignment_change,
    validate_rol_deactivation,
    validate_self_admin_removal,
    validate_user_deactivation,
)


@login_required
def panel_index(request):
    """Redirige al primer módulo del panel al que el usuario tenga acceso."""
    if request.user.tiene_permiso("catalogos.administrar"):
        return redirect("panel:organizacion_list")
    if request.user.tiene_permiso("personas.administrar"):
        return redirect("panel:personas_list")
    if request.user.tiene_permiso("usuarios.administrar"):
        return redirect("panel:usuarios_list")
    if request.user.tiene_permiso("roles.administrar"):
        return redirect("panel:roles_list")
    if request.user.tiene_permiso("permisos.ver"):
        return redirect("panel:permisos_list")
    messages.error(request, "No cuenta con permisos para acceder al panel de administración.")
    return redirect("equipos:mis_equipos")


# -------------------------------------------------------------------------
# Personas
# -------------------------------------------------------------------------

@requiere_permiso("personas.administrar")
def personas_list(request):
    query = request.GET.get("q", "").strip()
    vinculo_filtro = request.GET.get("vinculo", "").strip()
    sede_filtro = request.GET.get("sede", "").strip()
    estado_filtro = request.GET.get("estado", "").strip()
    programa_filtro = request.GET.get("programa", "").strip()

    personas = Persona.objects.select_related("sede", "programa", "area", "tipo_vinculo").annotate(
        equipos_count=Count("equipos")
    )

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
    if programa_filtro:
        personas = personas.filter(programa_id=programa_filtro)
    if estado_filtro == "activo":
        personas = personas.filter(activo=True)
    elif estado_filtro == "inactivo":
        personas = personas.filter(activo=False)

    page = paginate_queryset(request, personas.order_by("apellidos", "nombres"))

    context = {
        "personas": page,
        "page_obj": page,
        "query": query,
        "vinculo_filtro": vinculo_filtro,
        "sede_filtro": sede_filtro,
        "estado_filtro": estado_filtro,
        "programa_filtro": programa_filtro,
        "tipos_vinculo": TipoVinculo.objects.filter(activo=True).order_by("nombre"),
        "sedes": Sede.objects.filter(activo=True).order_by("nombre"),
        "programas": Programa.objects.filter(activo=True).select_related("sede", "facultad").order_by("nombre"),
        "areas": Area.objects.filter(activo=True).order_by("nombre"),
    }
    return render(request, "panel/personas_list.html", context)


def _persona_form_context(persona=None, data=None):
    return {
        "persona": persona,
        "data": data or {},
        "tipos_vinculo": TipoVinculo.objects.filter(activo=True).order_by("nombre"),
        "sedes": Sede.objects.filter(activo=True).order_by("nombre"),
        "programas": Programa.objects.filter(activo=True).select_related("sede", "facultad").order_by("nombre"),
        "areas": Area.objects.filter(activo=True).order_by("nombre"),
        "codigo_vinculo_admin": CODIGO_VINCULO_ADMINISTRATIVO,
    }


def _persona_data_from_post(request, persona=None):
    return {
        "tipo_documento": request.POST.get("tipo_documento", persona.tipo_documento if persona else "CC"),
        "numero_documento": request.POST.get("numero_documento", persona.numero_documento if persona else "").strip(),
        "nombres": request.POST.get("nombres", persona.nombres if persona else "").strip(),
        "apellidos": request.POST.get("apellidos", persona.apellidos if persona else "").strip(),
        "tipo_vinculo": request.POST.get("tipo_vinculo", str(persona.tipo_vinculo_id) if persona else ""),
        "sede": request.POST.get("sede", str(persona.sede_id) if persona else ""),
        "programa": request.POST.get("programa", str(persona.programa_id) if persona and persona.programa_id else ""),
        "area": request.POST.get("area", str(persona.area_id) if persona and persona.area_id else ""),
        "activo": request.POST.get("activo") in ("on", "true", "1") if request.method == "POST" else (persona.activo if persona else True),
    }


def _apply_persona_fields(persona, data):
    tipo_vinculo = get_object_or_404(TipoVinculo, id=data["tipo_vinculo"])
    persona.tipo_documento = data["tipo_documento"]
    persona.numero_documento = data["numero_documento"]
    persona.nombres = data["nombres"]
    persona.apellidos = data["apellidos"]
    persona.tipo_vinculo = tipo_vinculo
    persona.sede = get_object_or_404(Sede, id=data["sede"])
    if tipo_vinculo.codigo == CODIGO_VINCULO_ADMINISTRATIVO:
        persona.programa = None
        persona.area = get_object_or_404(Area, id=data["area"]) if data["area"] else None
    else:
        persona.area = None
        persona.programa = get_object_or_404(Programa, id=data["programa"]) if data["programa"] else None
    persona.activo = data["activo"]


@requiere_permiso("personas.administrar")
def persona_create(request):
    if request.method == "POST":
        data = _persona_data_from_post(request)
        num_doc = data["numero_documento"]
        if not all([num_doc, data["nombres"], data["apellidos"], data["tipo_vinculo"], data["sede"]]):
            messages.error(request, "Por favor complete todos los campos obligatorios.")
        elif Persona.objects.filter(numero_documento=num_doc).exists():
            messages.error(request, f"Ya existe una persona con el documento {num_doc}.")
        else:
            persona = Persona(activo=data["activo"])
            _apply_persona_fields(persona, data)
            try:
                persona.save()
            except ValidationError as exc:
                for field, errs in exc.message_dict.items():
                    for err in errs:
                        messages.error(request, err)
                return render(request, "panel/persona_form.html", _persona_form_context(data=data))
            messages.success(request, f"Persona {persona.nombre_completo} registrada exitosamente.")
            return redirect("panel:persona_edit", pk=persona.pk)
        return render(request, "panel/persona_form.html", _persona_form_context(data=data))

    return render(request, "panel/persona_form.html", _persona_form_context())


@requiere_permiso("personas.administrar")
def persona_edit(request, pk):
    persona = get_object_or_404(
        Persona.objects.select_related("sede", "programa", "area", "tipo_vinculo"),
        pk=pk,
    )
    equipos = persona.equipos.filter(activo=True)

    if request.method == "POST":
        data = _persona_data_from_post(request, persona)
        num_doc = data["numero_documento"]
        if not all([num_doc, data["nombres"], data["apellidos"], data["tipo_vinculo"], data["sede"]]):
            messages.error(request, "Por favor complete todos los campos obligatorios.")
        elif Persona.objects.filter(numero_documento=num_doc).exclude(pk=pk).exists():
            messages.error(request, f"Ya existe otra persona con el documento {num_doc}.")
        else:
            _apply_persona_fields(persona, data)
            try:
                persona.save()
            except ValidationError as exc:
                for field, errs in exc.message_dict.items():
                    for err in errs:
                        messages.error(request, err)
                return render(
                    request,
                    "panel/persona_form.html",
                    {**_persona_form_context(persona=persona, data=data), "equipos": equipos},
                )
            messages.success(request, f"Persona {persona.nombre_completo} actualizada correctamente.")
            return redirect("panel:persona_edit", pk=persona.pk)
        return render(
            request,
            "panel/persona_form.html",
            {**_persona_form_context(persona=persona, data=data), "equipos": equipos},
        )

    data = _persona_data_from_post(request, persona)
    return render(
        request,
        "panel/persona_form.html",
        {**_persona_form_context(persona=persona, data=data), "equipos": equipos},
    )


@require_POST
@requiere_permiso("personas.administrar")
def persona_toggle(request, pk):
    persona = get_object_or_404(Persona, pk=pk)
    persona.activo = not persona.activo
    persona.save()
    estado = "activada" if persona.activo else "inactivada"
    messages.success(request, f"Persona {persona.nombre_completo} {estado} exitosamente.")
    return redirect("panel:persona_edit", pk=persona.pk)


# -------------------------------------------------------------------------
# Usuarios
# -------------------------------------------------------------------------

@requiere_permiso("usuarios.administrar")
def usuarios_list(request):
    query = request.GET.get("q", "").strip()
    rol_filtro = request.GET.get("rol", "").strip()
    estado_filtro = request.GET.get("estado", "").strip()
    persona_filtro = request.GET.get("persona", "").strip()

    usuarios = Usuario.objects.select_related("persona").prefetch_related("roles").annotate(
        roles_count=Count("roles", distinct=True),
    )

    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(persona__numero_documento__icontains=query)
        )
    if rol_filtro:
        usuarios = usuarios.filter(roles__nombre=rol_filtro)
    if estado_filtro == "activo":
        usuarios = usuarios.filter(activo=True, is_active=True)
    elif estado_filtro == "inactivo":
        usuarios = usuarios.filter(Q(activo=False) | Q(is_active=False))
    if persona_filtro == "con":
        usuarios = usuarios.filter(persona__isnull=False)
    elif persona_filtro == "sin":
        usuarios = usuarios.filter(persona__isnull=True)

    page = paginate_queryset(request, usuarios.order_by("username").distinct())

    context = {
        "usuarios": page,
        "page_obj": page,
        "query": query,
        "rol_filtro": rol_filtro,
        "estado_filtro": estado_filtro,
        "persona_filtro": persona_filtro,
        "roles": Rol.objects.filter(activo=True).order_by("nombre"),
    }
    return render(request, "panel/usuarios_list.html", context)


def _usuario_form_context(data=None, personas_disponibles=None):
    return {
        "data": data or {},
        "roles": Rol.objects.filter(activo=True).order_by("nombre"),
        "personas_disponibles": personas_disponibles
        or Persona.objects.filter(activo=True, usuario__isnull=True).order_by("apellidos", "nombres"),
    }


@requiere_permiso("usuarios.administrar")
def usuario_create(request):
    if request.method == "POST":
        sin_persona = request.POST.get("sin_persona") in ("on", "true", "1")
        persona_id = request.POST.get("persona") or None
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")
        rol_ids = request.POST.getlist("roles")
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()

        data = {
            "sin_persona": sin_persona,
            "persona": persona_id or "",
            "username": username,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "roles": rol_ids,
        }

        errors = []
        if not username or not password:
            errors.append("Usuario y contraseña son obligatorios.")
        if password != password_confirm:
            errors.append("Las contraseñas no coinciden.")
        elif len(password) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres.")
        if Usuario.objects.filter(username__iexact=username).exists():
            errors.append(f"Ya existe un usuario con el nombre '{username}'.")
        if email and Usuario.objects.filter(email__iexact=email).exists():
            errors.append(f"Ya existe un usuario con el correo '{email}'.")

        persona = None
        if not sin_persona:
            if not persona_id:
                errors.append("Debe seleccionar una persona o marcar 'Usuario sin persona asociada'.")
            else:
                persona = Persona.objects.filter(id=persona_id, activo=True).first()
                if not persona:
                    errors.append("La persona seleccionada no es válida.")
                elif hasattr(persona, "usuario") and persona.usuario:
                    errors.append("La persona seleccionada ya tiene una cuenta de usuario asociada.")

        new_role_ids = {int(r) for r in rol_ids if r.isdigit()}

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, "panel/usuario_form.html", _usuario_form_context(data=data))

        with transaction.atomic():
            usuario = Usuario.objects.create_user(
                username=username,
                email=email or f"{username}@sin-correo.local",
                password=password,
                first_name=first_name or (persona.nombres if persona else ""),
                last_name=last_name or (persona.apellidos if persona else ""),
                persona=persona,
                activo=True,
            )
            for rol_id in new_role_ids:
                rol = Rol.objects.filter(id=rol_id, activo=True).first()
                if rol:
                    UsuarioRol.objects.create(usuario=usuario, rol=rol)

        registrar_cambio(
            request.user,
            f"Creó usuario '{usuario.username}' con roles: {', '.join(usuario.roles.values_list('nombre', flat=True))}",
        )
        messages.success(request, f"Usuario '{usuario.username}' creado exitosamente.")
        return redirect("panel:usuario_detail", pk=usuario.pk)

    return render(request, "panel/usuario_form.html", _usuario_form_context())


@requiere_permiso("usuarios.administrar")
def usuario_detail(request, pk):
    usuario = get_object_or_404(
        Usuario.objects.select_related("persona").prefetch_related("roles"),
        pk=pk,
    )
    roles_disponibles = Rol.objects.filter(activo=True).order_by("nombre")

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "reset_password":
            password = request.POST.get("password", "")
            password_confirm = request.POST.get("password_confirm", "")
            if password != password_confirm:
                messages.error(request, "Las contraseñas no coinciden.")
            elif len(password) < 8:
                messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
            else:
                usuario.set_password(password)
                usuario.save()
                registrar_cambio(request.user, f"Restableció la contraseña del usuario '{usuario.username}'.")
                messages.success(request, f"Contraseña de '{usuario.username}' actualizada correctamente.")

        elif action == "update_roles":
            rol_ids = {int(r) for r in request.POST.getlist("roles") if r.isdigit()}
            err = validate_role_assignment_change(request.user, usuario, rol_ids)
            if err:
                messages.error(request, err)
            else:
                roles_anteriores = set(usuario.roles.values_list("nombre", flat=True))
                UsuarioRol.objects.filter(usuario=usuario).delete()
                for rol_id in rol_ids:
                    rol = Rol.objects.filter(id=rol_id, activo=True).first()
                    if rol:
                        UsuarioRol.objects.create(usuario=usuario, rol=rol)
                roles_nuevos = set(usuario.roles.values_list("nombre", flat=True))
                registrar_cambio(
                    request.user,
                    f"Actualizó roles de '{usuario.username}': {roles_anteriores} → {roles_nuevos}",
                )
                messages.success(request, "Roles del usuario actualizados correctamente.")

        return redirect("panel:usuario_detail", pk=usuario.pk)

    context = {
        "usuario_obj": usuario,
        "roles_disponibles": roles_disponibles,
        "roles_asignados": set(usuario.roles.values_list("id", flat=True)),
    }
    return render(request, "panel/usuario_detail.html", context)


@require_POST
@requiere_permiso("usuarios.administrar")
def usuario_toggle(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if usuario.activo and usuario.is_active:
        err = validate_user_deactivation(usuario)
        if err:
            messages.error(request, err)
            return redirect("panel:usuario_detail", pk=usuario.pk)

    usuario.activo = not usuario.activo
    usuario.is_active = usuario.activo
    usuario.save()
    estado = "activado" if usuario.activo else "inactivado"
    registrar_cambio(request.user, f"{estado.capitalize()} usuario '{usuario.username}'.")
    messages.success(request, f"Usuario '{usuario.username}' {estado} exitosamente.")
    return redirect("panel:usuario_detail", pk=usuario.pk)


# -------------------------------------------------------------------------
# Roles y Permisos
# -------------------------------------------------------------------------

@requiere_permiso("roles.administrar")
def roles_list(request):
    roles = Rol.objects.annotate(
        usuarios_count=Count("usuarios", distinct=True),
        permisos_count=Count("permisos", distinct=True),
    ).order_by("nombre")
    return render(request, "panel/roles_list.html", {"roles": roles})


@requiere_permiso("roles.administrar")
def rol_form(request, pk=None):
    rol = get_object_or_404(Rol, pk=pk) if pk else None
    data = {
        "nombre": rol.nombre if rol else "",
        "descripcion": rol.descripcion or "" if rol else "",
        "activo": rol.activo if rol else True,
    }

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        descripcion = request.POST.get("descripcion", "").strip() or None
        activo = request.POST.get("activo") in ("on", "true", "1")
        data = {"nombre": nombre, "descripcion": descripcion or "", "activo": activo}

        if not nombre:
            messages.error(request, "El nombre del rol es obligatorio.")
        elif Rol.objects.filter(nombre=nombre).exclude(pk=pk).exists():
            messages.error(request, f"Ya existe un rol con el nombre '{nombre}'.")
        elif rol and rol.activo and not activo:
            err = validate_rol_deactivation(rol)
            if err:
                messages.error(request, err)
                return render(request, "panel/rol_form.html", {"rol": rol, "data": data})
        else:
            if rol:
                rol.nombre = nombre
                rol.descripcion = descripcion
                rol.activo = activo
                rol.save()
                registrar_cambio(request.user, f"Actualizó rol '{rol.nombre}'.")
                messages.success(request, f"Rol '{rol.nombre}' actualizado correctamente.")
            else:
                rol = Rol.objects.create(nombre=nombre, descripcion=descripcion, activo=activo)
                registrar_cambio(request.user, f"Creó rol '{rol.nombre}'.")
                messages.success(request, f"Rol '{rol.nombre}' creado exitosamente.")
            return redirect("panel:rol_permisos", pk=rol.pk)

    return render(request, "panel/rol_form.html", {"rol": rol, "data": data})


@requiere_permiso("roles.administrar")
def rol_permisos(request, pk):
    rol = get_object_or_404(Rol.objects.prefetch_related("permisos"), pk=pk)
    permisos_asignados = set(rol.permisos.values_list("id", flat=True))
    usuarios_activos = rol.usuarios.filter(activo=True, is_active=True).distinct().count()

    if request.method == "POST":
        confirmado = request.POST.get("confirmar_cambios") == "1"
        nuevos_ids = {int(p) for p in request.POST.getlist("permisos") if p.isdigit()}
        removidos = permisos_asignados - nuevos_ids

        if removidos and usuarios_activos and not confirmado:
            messages.warning(
                request,
                f"Está quitando permisos a un rol con {usuarios_activos} usuario(s) activo(s). "
                "Confirme el cambio marcando la casilla de confirmación.",
            )
            return render(
                request,
                "panel/rol_permisos.html",
                {
                    "rol": rol,
                    "grupos": permisos_agrupados(),
                    "permisos_asignados": nuevos_ids,
                    "usuarios_activos": usuarios_activos,
                    "requiere_confirmacion": True,
                },
            )

        permisos_anteriores = set(rol.permisos.values_list("codigo", flat=True))
        RolPermiso.objects.filter(rol=rol).delete()
        for permiso_id in nuevos_ids:
            permiso = Permiso.objects.filter(id=permiso_id).first()
            if permiso:
                RolPermiso.objects.create(rol=rol, permiso=permiso)
        permisos_nuevos = set(rol.permisos.values_list("codigo", flat=True))
        registrar_cambio(
            request.user,
            f"Actualizó permisos del rol '{rol.nombre}': {permisos_anteriores} → {permisos_nuevos}",
        )
        messages.success(request, f"Permisos del rol '{rol.nombre}' guardados correctamente.")
        return redirect("panel:rol_permisos", pk=rol.pk)

    return render(
        request,
        "panel/rol_permisos.html",
        {
            "rol": rol,
            "grupos": permisos_agrupados(),
            "permisos_asignados": permisos_asignados,
            "usuarios_activos": usuarios_activos,
            "requiere_confirmacion": False,
        },
    )


@requiere_permiso("permisos.ver")
def permisos_list(request):
    permisos = Permiso.objects.prefetch_related("roles").annotate(
        roles_count=Count("roles", distinct=True),
    ).order_by("codigo")
    return render(
        request,
        "panel/permisos_list.html",
        {"grupos": permisos_agrupados(), "permisos": permisos},
    )
