from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.contrib import messages
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp import match_token
from datetime import datetime
import base64
from io import BytesIO
import qrcode

from .models import Usuario, UsuarioRol
from .decorators import requiere_permiso
from .auth_utils import username_desde_correo
from personas.models import (
    Persona,
    TipoVinculo,
    CODIGO_VINCULO_ADMINISTRATIVO,
    CODIGO_VINCULO_EXTERNO,
)
from personas.services import registrar_visita, visita_activa, nombre_dependencia_visita
from organizacion.models import Sede, Programa, Area, Decanatura
from equipos.models import Equipo
from control_acceso.models import Movimiento

SESSION_MFA_USER_ID = "mfa_user_id"
SESSION_MFA_BACKEND = "mfa_backend"


def _usuario_requiere_mfa(usuario) -> bool:
    return usuario.roles.filter(nombre="admin_sistema", activo=True).exists()


def _post_login_redirect(user):
    if user.tiene_permiso("control.escanear"):
        return reverse("control_acceso:escanear")
    if user.tiene_permiso("equipos.ver_propios"):
        return reverse("equipos:mis_equipos")
    if user.tiene_permiso("perfil.ver_propio"):
        return reverse("accounts:mi_perfil")
    if user.tiene_permiso("personas.administrar"):
        return reverse("panel:personas_list")
    if user.tiene_permiso("usuarios.administrar"):
        return reverse("panel:usuarios_list")
    if user.tiene_permiso("catalogos.administrar"):
        return reverse("panel:organizacion_list")
    return reverse("equipos:mis_equipos")


@method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True), name="dispatch")
class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if _usuario_requiere_mfa(user):
            self.request.session[SESSION_MFA_USER_ID] = user.pk
            self.request.session[SESSION_MFA_BACKEND] = user.backend
            if not TOTPDevice.objects.filter(user=user, confirmed=True).exists():
                messages.info(
                    self.request,
                    "Como administrador del sistema debe configurar la autenticación en dos pasos (MFA).",
                )
                return redirect("accounts:mfa_setup")
            return redirect("accounts:mfa_verify")
        login(self.request, user)
        return redirect(self.get_success_url())

    def get_success_url(self):
        return _post_login_redirect(self.request.user)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


def _contexto_registro(form_data=None):
    return {
        "tipos_vinculo": TipoVinculo.objects.filter(activo=True, permite_autoregistro=True).order_by("nombre"),
        "sedes": Sede.objects.filter(activo=True).order_by("nombre"),
        "programas": Programa.objects.filter(activo=True).select_related("sede", "facultad").order_by("nombre"),
        "areas": Area.objects.filter(activo=True).select_related("sede").order_by("sede__nombre", "nombre"),
        "facultades": Decanatura.objects.filter(activo=True).order_by("nombre"),
        "form_data": form_data or {},
        "contacto_arco": settings.DATOS_PERSONALES_CONTACTO,
        "codigo_vinculo_externo": CODIGO_VINCULO_EXTERNO,
        "codigo_vinculo_admin": CODIGO_VINCULO_ADMINISTRATIVO,
    }


def _parse_fecha(valor: str):
    valor = (valor or "").strip()
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError:
        return None


def registro_externo_view(request):
    """Autorregistro (docs 06 + 16). Personal externo crea también la primera VisitaExterno."""
    if request.user.is_authenticated:
        return redirect("accounts:mi_perfil")

    if request.method == "POST":
        nombres = request.POST.get("nombres", "").strip()
        apellidos = request.POST.get("apellidos", "").strip()
        tipo_documento = request.POST.get("tipo_documento", "CC").strip()
        numero_documento = request.POST.get("numero_documento", "").strip()
        tipo_vinculo_id = request.POST.get("tipo_vinculo", "").strip()
        correo = request.POST.get("correo", "").strip().lower()
        sede_id = request.POST.get("sede", "").strip()
        programa_id = request.POST.get("programa", "").strip() or None
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")
        acepta_tratamiento = request.POST.get("acepta_tratamiento") in ("on", "true", "1")
        unidad_tipo = request.POST.get("unidad_tipo", "").strip()
        unidad_id = request.POST.get("unidad_id", "").strip()
        fecha_inicio = _parse_fecha(request.POST.get("fecha_inicio", ""))
        fecha_fin = _parse_fecha(request.POST.get("fecha_fin", ""))

        errors = []

        if not all([nombres, apellidos, tipo_documento, numero_documento, tipo_vinculo_id, correo, sede_id, password, password_confirm]):
            errors.append("Por favor complete todos los campos obligatorios (*).")

        if not acepta_tratamiento:
            errors.append(
                "Debe aceptar la política de tratamiento de datos personales para continuar con el registro."
            )

        if password != password_confirm:
            errors.append("Las contraseñas no coinciden.")
        elif numero_documento and password == numero_documento:
            errors.append("La contraseña no puede ser igual al número de documento.")
        elif password:
            try:
                validate_password(password)
            except ValidationError as exc:
                errors.extend(exc.messages)

        if numero_documento:
            persona_existente = (
                Persona.objects.filter(numero_documento=numero_documento)
                .select_related("tipo_vinculo")
                .first()
            )
            if persona_existente:
                if (
                    persona_existente.tipo_vinculo
                    and persona_existente.tipo_vinculo.codigo == CODIGO_VINCULO_EXTERNO
                ):
                    errors.append(
                        "Ya tiene una cuenta como personal externo. Inicie sesión y use "
                        "«Registrar nueva visita» para declarar esta llegada."
                    )
                else:
                    errors.append(
                        f"Ya existe una persona registrada con el documento de identidad {numero_documento}."
                    )

        if correo:
            if Usuario.objects.filter(email__iexact=correo).exists():
                errors.append(f"Ya existe una cuenta registrada con el correo {correo}.")

        tipo_vinculo = None
        es_externo = False
        if tipo_vinculo_id:
            tipo_vinculo = (
                TipoVinculo.objects.filter(id=tipo_vinculo_id, activo=True, permite_autoregistro=True)
                .select_related("rol_asignado")
                .first()
            )
            if not tipo_vinculo:
                errors.append("El tipo de vínculo seleccionado no es válido o no permite autorregistro público.")
            else:
                es_externo = tipo_vinculo.codigo == CODIGO_VINCULO_EXTERNO
                if tipo_vinculo.dominio_correo_requerido:
                    dominio = tipo_vinculo.dominio_correo_requerido.strip().lower()
                    if not correo.endswith(dominio):
                        errors.append(
                            f"Para el perfil '{tipo_vinculo.nombre}', el correo electrónico debe pertenecer al dominio institucional ({dominio})."
                        )

        username_candidato = ""
        if correo and tipo_vinculo and not any(
            e.startswith("Ya existe una cuenta") for e in errors
        ):
            username_candidato = username_desde_correo(correo, tipo_vinculo)
            if Usuario.objects.filter(username__iexact=username_candidato).exists():
                errors.append(
                    f"Ya existe una cuenta registrada con el usuario '{username_candidato}'."
                )

        sede = None
        if sede_id:
            sede = Sede.objects.filter(id=sede_id, activo=True).first()
            if not sede:
                errors.append("La sede seleccionada no es válida.")

        es_administrativo = bool(
            tipo_vinculo and tipo_vinculo.codigo == CODIGO_VINCULO_ADMINISTRATIVO
        )

        programa = None
        area = None
        if es_externo:
            programa = None
            area = None
            if not unidad_tipo or not unidad_id:
                errors.append(
                    "Como personal externo debe indicar la dependencia destino (facultad, programa o área)."
                )
            if not fecha_inicio or not fecha_fin:
                errors.append(
                    "Como personal externo debe indicar la vigencia de la visita (fecha inicio y fin)."
                )
            elif fecha_fin < fecha_inicio:
                errors.append("La fecha fin de la visita debe ser mayor o igual a la fecha inicio.")
        elif es_administrativo:
            # Área la asigna después un admin con personas.administrar
            programa = None
            area = None
        else:
            if programa_id:
                programa = Programa.objects.filter(id=programa_id, activo=True).first()
                if programa and sede and programa.sede_id != sede.id:
                    errors.append("El programa seleccionado no pertenece a la sede indicada.")
            area = None

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, "accounts/registro.html", _contexto_registro(request.POST))

        try:
            with transaction.atomic():
                persona = Persona.objects.create(
                    tipo_documento=tipo_documento,
                    numero_documento=numero_documento,
                    nombres=nombres,
                    apellidos=apellidos,
                    tipo_vinculo=tipo_vinculo,
                    sede=sede,
                    programa=programa,
                    area=area,
                    activo=True,
                )

                username = username_desde_correo(correo, tipo_vinculo)
                usuario = Usuario.objects.create_user(
                    username=username,
                    email=correo,
                    first_name=nombres,
                    last_name=apellidos,
                    password=password,
                    persona=persona,
                    activo=True,
                )

                if tipo_vinculo.rol_asignado:
                    UsuarioRol.objects.create(usuario=usuario, rol=tipo_vinculo.rol_asignado)

                if es_externo:
                    registrar_visita(
                        persona=persona,
                        sede=sede,
                        unidad_tipo=unidad_tipo,
                        unidad_id=int(unidad_id),
                        fecha_inicio=fecha_inicio,
                        fecha_fin=fecha_fin,
                    )
        except (ValidationError, ValueError) as exc:
            if hasattr(exc, "messages"):
                for msg in exc.messages:
                    messages.error(request, msg)
            elif hasattr(exc, "message_dict"):
                for errs in exc.message_dict.values():
                    for msg in errs:
                        messages.error(request, msg)
            else:
                messages.error(request, str(exc))
            return render(request, "accounts/registro.html", _contexto_registro(request.POST))

        try:
            from notifications.services.email_service import EmailService

            EmailService.send_welcome(usuario)
        except Exception:
            import logging

            logging.getLogger(__name__).exception(
                "Fallo al encolar/enviar correo welcome user_id=%s",
                getattr(usuario, "pk", None),
            )

        if tipo_vinculo and tipo_vinculo.dominio_correo_requerido:
            messages.success(
                request,
                f"¡Registro exitoso, {nombres}! Su cuenta ha sido creada correctamente. "
                f"Ya puede iniciar sesión con su documento, usuario institucional "
                f"({username_desde_correo(correo, tipo_vinculo)}) o correo.",
            )
        else:
            messages.success(
                request,
                f"¡Registro exitoso, {nombres}! Su cuenta ha sido creada correctamente. "
                f"Ya puede iniciar sesión con su documento o correo.",
            )
        return redirect("accounts:login")

    return render(request, "accounts/registro.html", _contexto_registro())


@login_required
@requiere_permiso("perfil.ver_propio")
def registrar_visita_view(request):
    """Nueva VisitaExterno para personal externo ya autenticado (doc 16)."""
    persona = getattr(request.user, "persona", None)
    if not persona or not persona.es_personal_externo:
        messages.error(request, "Solo el personal externo puede registrar visitas.")
        return redirect("accounts:mi_perfil")

    if request.method == "POST":
        sede_id = request.POST.get("sede", "").strip()
        unidad_tipo = request.POST.get("unidad_tipo", "").strip()
        unidad_id = request.POST.get("unidad_id", "").strip()
        fecha_inicio = _parse_fecha(request.POST.get("fecha_inicio", ""))
        fecha_fin = _parse_fecha(request.POST.get("fecha_fin", ""))
        errors = []

        sede = Sede.objects.filter(id=sede_id, activo=True).first() if sede_id else None
        if not sede:
            errors.append("Seleccione una sede destino válida.")
        if not unidad_tipo or not unidad_id:
            errors.append("Indique la dependencia destino.")
        if not fecha_inicio or not fecha_fin:
            errors.append("Indique la vigencia de la visita.")
        elif fecha_fin < fecha_inicio:
            errors.append("La fecha fin debe ser mayor o igual a la fecha inicio.")

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            try:
                visita = registrar_visita(
                    persona=persona,
                    sede=sede,
                    unidad_tipo=unidad_tipo,
                    unidad_id=int(unidad_id),
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                )
                messages.success(
                    request,
                    f"Visita registrada: {visita.sede.nombre} hasta {visita.fecha_fin.isoformat()}.",
                )
                return redirect("accounts:mi_perfil")
            except (ValidationError, ValueError) as exc:
                messages.error(request, str(exc))

    visita = visita_activa(persona)
    return render(
        request,
        "accounts/registrar_visita.html",
        {
            "persona": persona,
            "visita_actual": visita,
            "nombre_dependencia": nombre_dependencia_visita(visita) if visita else "",
            "sedes": Sede.objects.filter(activo=True).order_by("nombre"),
            "programas": Programa.objects.filter(activo=True).select_related("sede", "facultad").order_by("nombre"),
            "areas": Area.objects.filter(activo=True).select_related("sede").order_by("sede__nombre", "nombre"),
            "facultades": Decanatura.objects.filter(activo=True).order_by("nombre"),
            "form_data": request.POST if request.method == "POST" else {},
        },
    )


@login_required
@requiere_permiso("perfil.ver_propio")
def mi_perfil_view(request):
    persona = getattr(request.user, "persona", None)
    equipos = Equipo.objects.filter(persona=persona).order_by("-created_at") if persona else Equipo.objects.none()
    equipos_activos = equipos.filter(activo=True).count()

    movimientos = (
        Movimiento.objects.filter(equipo__persona=persona)
        .select_related("equipo", "usuario_control")
        .order_by("-timestamp")[:10]
        if persona
        else Movimiento.objects.none()
    )
    metricas = {
        "total_equipos": equipos.count(),
        "equipos_activos": equipos_activos,
        "salidas_ok": Movimiento.objects.filter(
            equipo__persona=persona, resultado=Movimiento.RESULTADO_OK
        ).count() if persona else 0,
        "alertas": Movimiento.objects.filter(
            equipo__persona=persona, resultado=Movimiento.RESULTADO_ALERTA
        ).count() if persona else 0,
    }

    visita_actual = None
    nombre_dep = ""
    if persona and persona.es_personal_externo:
        visita_actual = visita_activa(persona)
        nombre_dep = nombre_dependencia_visita(visita_actual)

    return render(
        request,
        "accounts/mi_perfil.html",
        {
            "persona": persona,
            "equipos": equipos.filter(activo=True),
            "movimientos": movimientos,
            "metricas": metricas,
            "requiere_mfa": _usuario_requiere_mfa(request.user),
            "mfa_configurado": TOTPDevice.objects.filter(user=request.user, confirmed=True).exists(),
            "visita_actual": visita_actual,
            "nombre_dependencia_visita": nombre_dep,
        },
    )


def _mfa_pending_user(request):
    user_id = request.session.get(SESSION_MFA_USER_ID)
    if not user_id:
        return None
    return Usuario.objects.filter(pk=user_id, activo=True, is_active=True).first()


@ratelimit(key="ip", rate="10/m", method="POST", block=True)
def mfa_verify_view(request):
    """Segundo factor TOTP obligatorio para admin_sistema."""
    usuario = _mfa_pending_user(request)
    if request.user.is_authenticated and not usuario:
        return redirect(_post_login_redirect(request.user))
    if not usuario:
        messages.error(request, "Sesión MFA expirada. Inicie sesión de nuevo.")
        return redirect("accounts:login")

    if request.method == "POST":
        token = request.POST.get("token", "").strip()
        device = match_token(usuario, token)
        if device:
            backend = request.session.pop(SESSION_MFA_BACKEND, "django.contrib.auth.backends.ModelBackend")
            request.session.pop(SESSION_MFA_USER_ID, None)
            login(request, usuario, backend=backend)
            request.session["otp_device_id"] = device.persistent_id
            messages.success(request, "Verificación MFA correcta.")
            return redirect(_post_login_redirect(usuario))
        messages.error(request, "Código MFA incorrecto o expirado.")

    return render(request, "accounts/mfa_verify.html", {"usuario": usuario})


def mfa_setup_view(request):
    """Enrolamiento TOTP para administradores del sistema."""
    usuario = request.user if request.user.is_authenticated else _mfa_pending_user(request)
    if not usuario:
        messages.error(request, "Debe iniciar sesión para configurar MFA.")
        return redirect("accounts:login")
    if not _usuario_requiere_mfa(usuario):
        messages.error(request, "MFA solo es obligatorio para el rol admin_sistema.")
        return redirect("accounts:login")

    device = TOTPDevice.objects.filter(user=usuario, confirmed=False).first()
    if not device:
        device = TOTPDevice.objects.create(user=usuario, name="default", confirmed=False)

    if request.method == "POST":
        token = request.POST.get("token", "").strip()
        if device.verify_token(token):
            device.confirmed = True
            device.save(update_fields=["confirmed"])
            TOTPDevice.objects.filter(user=usuario, confirmed=False).exclude(pk=device.pk).delete()
            if not request.user.is_authenticated:
                backend = request.session.pop(
                    SESSION_MFA_BACKEND, "django.contrib.auth.backends.ModelBackend"
                )
                request.session.pop(SESSION_MFA_USER_ID, None)
                login(request, usuario, backend=backend)
            messages.success(request, "MFA configurado correctamente.")
            return redirect(_post_login_redirect(usuario))
        messages.error(request, "Código inválido. Escanee el QR e intente de nuevo.")

    config_url = device.config_url
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(config_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_data_uri = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")

    return render(
        request,
        "accounts/mfa_setup.html",
        {
            "usuario": usuario,
            "config_url": config_url,
            "device": device,
            "qr_data_uri": qr_data_uri,
        },
    )


@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def password_reset_request_view(request):
    """Solicitud de restablecimiento de contraseña (envía enlace por correo)."""
    if request.user.is_authenticated:
        return redirect("accounts:mi_perfil")

    if request.method == "POST":
        identificador = request.POST.get("identificador", "").strip()
        # Respuesta genérica anti-enumeración
        msg_ok = (
            "Si existe una cuenta asociada, enviamos un enlace para restablecer "
            "la contraseña. Revise su correo (y carpeta de spam)."
        )
        if identificador:
            from accounts.auth_utils import resolver_usuario_por_identificador
            from notifications.models import EmailToken
            from notifications.services.email_service import EmailService
            from notifications.services.token_service import create_email_token

            usuario = resolver_usuario_por_identificador(identificador)
            if usuario and usuario.email and usuario.is_active:
                _, raw = create_email_token(
                    usuario, EmailToken.Purpose.PASSWORD_RESET, hours=2
                )
                try:
                    EmailService.send_password_reset(usuario, raw)
                except Exception:
                    import logging

                    logging.getLogger(__name__).exception(
                        "Fallo al encolar/enviar password_reset user_id=%s",
                        getattr(usuario, "pk", None),
                    )
        messages.success(request, msg_ok)
        return redirect("accounts:login")

    return render(request, "accounts/password_reset_request.html")


@ratelimit(key="ip", rate="10/m", method="POST", block=True)
def password_reset_confirm_view(request):
    """Confirma el token y permite definir nueva contraseña."""
    from notifications.models import EmailToken
    from notifications.services.token_service import consume_email_token

    token = request.GET.get("token") or request.POST.get("token", "")
    if request.method == "POST":
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")
        errors = []
        if not token:
            errors.append("Falta el enlace de restablecimiento.")
        if not password or password != password_confirm:
            errors.append("Las contraseñas no coinciden.")
        elif password:
            try:
                validate_password(password)
            except ValidationError as exc:
                errors.extend(exc.messages)
        if errors:
            for err in errors:
                messages.error(request, err)
            return render(
                request,
                "accounts/password_reset_confirm.html",
                {"token": token},
            )

        email_token = consume_email_token(token, EmailToken.Purpose.PASSWORD_RESET)
        if not email_token:
            messages.error(
                request,
                "El enlace no es válido o ha expirado. Solicite uno nuevo.",
            )
            return redirect("accounts:password_reset")

        usuario = email_token.user
        usuario.set_password(password)
        usuario.save(update_fields=["password"])
        messages.success(
            request,
            "Contraseña actualizada. Ya puede iniciar sesión.",
        )
        return redirect("accounts:login")

    return render(
        request,
        "accounts/password_reset_confirm.html",
        {"token": token},
    )
