from django.shortcuts import redirect


def sedes_list(request):
    """Redirige al CRUD del panel (solo administradores con catalogos.administrar)."""
    return redirect("panel:organizacion_list")
