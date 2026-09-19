from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied


def requiere_permiso(codigo_permiso: str):
    """
    Decorador para vistas que valida si el usuario autenticado
    cuenta con el permiso dinámico especificado en sus roles.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("accounts:login")

            if request.user.tiene_permiso(codigo_permiso):
                return view_func(request, *args, **kwargs)

            messages.error(
                request,
                f"No cuenta con el permiso requerido ({codigo_permiso}) para acceder a esta función."
            )
            # Redireccionar según el perfil
            if request.user.tiene_permiso("control.escanear"):
                return redirect("control_acceso:escanear")
            return redirect("equipos:mis_equipos")

        return _wrapped_view
    return decorator
