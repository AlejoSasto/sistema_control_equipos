from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib import messages

from .models import Usuario, UsuarioRol
from .decorators import requiere_permiso
from personas.models import Persona, TipoVinculo
from organizacion.models import Sede, Programa
from equipos.models import Equipo
from control_acceso.models import Movimiento


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        # Redirigir según roles o permisos del usuario
        if self.request.user.tiene_permiso("control.escanear"):
            return reverse_lazy("control_acceso:escanear")
        if self.request.user.tiene_permiso("perfil.ver_propio"):
            return reverse_lazy("accounts:mi_perfil")
        if self.request.user.tiene_permiso("personas.administrar"):
            return reverse_lazy("panel:personas_list")
        if self.request.user.tiene_permiso("usuarios.administrar"):
            return reverse_lazy("panel:usuarios_list")
        if self.request.user.tiene_permiso("catalogos.administrar"):
            return reverse_lazy("panel:organizacion_list")
        return reverse_lazy("equipos:mis_equipos")


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


def registro_externo_view(request):
    """
    Vista pública de autorregistro para la comunidad académica (Documento 06).
    Crea atómicamente la Persona, el Usuario y asigna el Rol definido en TipoVinculo.
    """
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

        errors = []

        if not all([nombres, apellidos, tipo_documento, numero_documento, tipo_vinculo_id, correo, sede_id, password, password_confirm]):
            errors.append("Por favor complete todos los campos obligatorios (*).")

        if password != password_confirm:
            errors.append("Las contraseñas no coinciden.")
        elif len(password) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres.")
        elif numero_documento and password == numero_documento:
            errors.append("La contraseña no puede ser igual al número de documento.")

        if numero_documento and Persona.objects.filter(numero_documento=numero_documento).exists():
            errors.append(f"Ya existe una persona registrada con el documento de identidad {numero_documento}.")

        if correo:
            if Usuario.objects.filter(username__iexact=correo).exists() or Usuario.objects.filter(email__iexact=correo).exists():
                errors.append(f"Ya existe una cuenta registrada con el correo institucional {correo}.")

        tipo_vinculo = None
        if tipo_vinculo_id:
            tipo_vinculo = (
                TipoVinculo.objects.filter(id=tipo_vinculo_id, activo=True, permite_autoregistro=True)
                .select_related("rol_asignado")
                .first()
            )
            if not tipo_vinculo:
                errors.append("El tipo de vínculo seleccionado no es válido o no permite autorregistro público.")
            elif tipo_vinculo.dominio_correo_requerido:
                dominio = tipo_vinculo.dominio_correo_requerido.strip().lower()
                if not correo.endswith(dominio):
                    errors.append(
                        f"Para el perfil '{tipo_vinculo.nombre}', el correo electrónico debe pertenecer al dominio institucional ({dominio})."
                    )

        sede = None
        if sede_id:
            sede = Sede.objects.filter(id=sede_id, activo=True).first()
            if not sede:
                errors.append("La sede seleccionada no es válida.")

        programa = None
        if programa_id:
            programa = Programa.objects.filter(id=programa_id, activo=True).first()
            if programa and sede and programa.sede_id != sede.id:
                errors.append("El programa seleccionado no pertenece a la sede indicada.")

        if errors:
            for err in errors:
                messages.error(request, err)
            tipos_vinculo = TipoVinculo.objects.filter(activo=True, permite_autoregistro=True).order_by("nombre")
            sedes = Sede.objects.filter(activo=True).order_by("nombre")
            programas = Programa.objects.filter(activo=True).select_related("sede", "facultad").order_by("nombre")
            return render(
                request,
                "accounts/registro.html",
                {
                    "tipos_vinculo": tipos_vinculo,
                    "sedes": sedes,
                    "programas": programas,
                    "form_data": request.POST,
                },
            )

        # Creación atómica de Persona, Usuario y Asignación de Rol
        with transaction.atomic():
            persona = Persona.objects.create(
                tipo_documento=tipo_documento,
                numero_documento=numero_documento,
                nombres=nombres,
                apellidos=apellidos,
                tipo_vinculo=tipo_vinculo,
                sede=sede,
                programa=programa,
                activo=True,
            )

            usuario = Usuario.objects.create_user(
                username=correo,
                email=correo,
                first_name=nombres,
                last_name=apellidos,
                password=password,
                persona=persona,
                activo=True,
            )

            if tipo_vinculo.rol_asignado:
                UsuarioRol.objects.create(usuario=usuario, rol=tipo_vinculo.rol_asignado)

        messages.success(
            request,
            f"¡Registro exitoso, {nombres}! Su cuenta ha sido creada correctamente. Ya puede iniciar sesión con su correo institucional.",
        )
        return redirect("accounts:login")

    tipos_vinculo = TipoVinculo.objects.filter(activo=True, permite_autoregistro=True).order_by("nombre")
    sedes = Sede.objects.filter(activo=True).order_by("nombre")
    programas = Programa.objects.filter(activo=True).select_related("sede", "facultad").order_by("nombre")

    return render(
        request,
        "accounts/registro.html",
        {
            "tipos_vinculo": tipos_vinculo,
            "sedes": sedes,
            "programas": programas,
            "form_data": {},
        },
    )


@login_required
@requiere_permiso("perfil.ver_propio")
def mi_perfil_view(request):
    """
    Vista del miembro de comunidad: solo su Persona, Usuario, equipos y métricas propias.
    Gestor del Conocimiento, Creador de Oportunidades, Administrativo y Graduado comparten
    el rol miembro_comunidad y acceden únicamente a esta información personal.
    """
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

    return render(
        request,
        "accounts/mi_perfil.html",
        {
            "persona": persona,
            "equipos": equipos.filter(activo=True),
            "movimientos": movimientos,
            "metricas": metricas,
        },
    )
