from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
from django_ratelimit.decorators import ratelimit
from accounts.decorators import requiere_permiso
from config.pagination import paginate_queryset
from equipos.models import Equipo
from .models import Movimiento
from .utils import normalizar_codigo_escaneado


@login_required
@requiere_permiso("control.escanear")
def control_salida_view(request):
    """
    Pantalla principal de Control de Salida en Portería para el celador.
    Recibe token por pistola (teclado), cámara del dispositivo o ingreso manual.
    """
    hoy = timezone.localdate()

    # Movimientos del día
    movimientos_hoy = Movimiento.objects.select_related(
        "equipo", "equipo__persona", "usuario_control"
    ).filter(timestamp__date=hoy)[:20]

    # Estadísticas rápidas del turno de control de salida
    total_hoy = Movimiento.objects.filter(timestamp__date=hoy).count()
    total_ok = Movimiento.objects.filter(timestamp__date=hoy, resultado=Movimiento.RESULTADO_OK).count()
    total_alertas = Movimiento.objects.filter(
        timestamp__date=hoy,
        resultado__in=[Movimiento.RESULTADO_ALERTA, Movimiento.RESULTADO_NO_ENCONTRADO]
    ).count()

    context = {
        "movimientos_hoy": movimientos_hoy,
        "total_hoy": total_hoy,
        "total_ok": total_ok,
        "total_alertas": total_alertas,
    }
    return render(request, "control_acceso/scanner.html", context)


@login_required
@requiere_permiso("control.escanear")
@require_POST
@ratelimit(key="user_or_ip", rate="60/m", method="POST", block=True)
def escanear_qr_salida(request):
    """
    Endpoint HTMX para resolver el escaneo en tiempo real:
    1. Recibe token de exhibición firmado, UUID legado o serial.
    2. Resuelve el Equipo y la Persona.
    3. Aplica reglas de negocio (ok / alerta / no_encontrado).
    """
    codigo_recibido = normalizar_codigo_escaneado(request.POST.get("codigo", ""))

    if not codigo_recibido:
        return render(
            request,
            "control_acceso/partials/resultado_escaneo.html",
            {"error_mensaje": "Por favor escanee el código QR presentado por la persona."},
        )

    equipo = Equipo.resolver_token_escaneado(codigo_recibido)

    hoy = timezone.localdate()

    # Caso 1: Código no encontrado en base de datos
    if not equipo:
        movimiento = Movimiento.objects.create(
            equipo=None,
            token_escaneado=codigo_recibido[:100],
            usuario_control=request.user,
            resultado=Movimiento.RESULTADO_NO_ENCONTRADO,
            observacion="Código no registrado en el sistema institucional.",
        )
        movimientos_actualizados = Movimiento.objects.select_related(
            "equipo", "equipo__persona", "usuario_control"
        ).filter(timestamp__date=hoy)[:20]

        return render(
            request,
            "control_acceso/partials/resultado_escaneo.html",
            {
                "codigo_buscado": codigo_recibido,
                "resultado": "no_encontrado",
                "movimiento": movimiento,
                "movimientos_hoy": movimientos_actualizados,
            },
        )

    persona = equipo.persona

    # Caso 2: Alerta por equipo o persona inactiva
    if not equipo.activo or not persona.activo:
        motivo = []
        if not equipo.activo:
            motivo.append("Equipo dado de baja o inactivo")
        if not persona.activo:
            motivo.append("Persona inactiva / desvinculada")
        motivo_str = " y ".join(motivo)

        movimiento = Movimiento.objects.create(
            equipo=equipo,
            token_escaneado=str(equipo.token_qr),
            usuario_control=request.user,
            resultado=Movimiento.RESULTADO_ALERTA,
            observacion=f"Alerta: {motivo_str}",
        )
        movimientos_actualizados = Movimiento.objects.select_related(
            "equipo", "equipo__persona", "usuario_control"
        ).filter(timestamp__date=hoy)[:20]

        return render(
            request,
            "control_acceso/partials/resultado_escaneo.html",
            {
                "equipo": equipo,
                "persona": persona,
                "resultado": "alerta",
                "motivo_alerta": motivo_str,
                "movimiento": movimiento,
                "movimientos_hoy": movimientos_actualizados,
            },
        )

    # Caso 3: Coincide y Autorizado (OK)
    movimiento = Movimiento.objects.create(
        equipo=equipo,
        token_escaneado=str(equipo.token_qr),
        usuario_control=request.user,
        resultado=Movimiento.RESULTADO_OK,
        observacion="Salida autorizada sin novedad.",
    )

    movimientos_actualizados = Movimiento.objects.select_related(
        "equipo", "equipo__persona", "usuario_control"
    ).filter(timestamp__date=hoy)[:20]

    return render(
        request,
        "control_acceso/partials/resultado_escaneo.html",
        {
            "equipo": equipo,
            "persona": persona,
            "resultado": "ok",
            "movimiento": movimiento,
            "movimientos_hoy": movimientos_actualizados,
        },
    )


@login_required
@requiere_permiso("control.ver_alertas")
def movimientos_list(request):
    """Vista de histórico de movimientos con filtros por fecha y resultado."""
    query = request.GET.get("q", "").strip()
    resultado_filtro = request.GET.get("resultado", "")
    fecha_filtro = request.GET.get("fecha", "")

    movimientos = Movimiento.objects.select_related(
        "equipo", "equipo__persona", "usuario_control"
    ).all()

    if query:
        movimientos = movimientos.filter(
            Q(equipo__serial__icontains=query)
            | Q(equipo__persona__nombres__icontains=query)
            | Q(equipo__persona__apellidos__icontains=query)
            | Q(equipo__persona__numero_documento__icontains=query)
            | Q(token_escaneado__icontains=query)
        )

    if resultado_filtro:
        movimientos = movimientos.filter(resultado=resultado_filtro)

    if fecha_filtro:
        movimientos = movimientos.filter(timestamp__date=fecha_filtro)

    page = paginate_queryset(request, movimientos)

    context = {
        "movimientos": page,
        "page_obj": page,
        "query": query,
        "resultado_filtro": resultado_filtro,
        "fecha_filtro": fecha_filtro,
        "opciones_resultado": Movimiento.OPCIONES_RESULTADO,
    }
    return render(request, "control_acceso/movimientos_list.html", context)
