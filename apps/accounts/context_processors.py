"""Context processors de accounts."""

from accounts.alcance import etiqueta_alcance


def alcance_usuario(request):
    if request.user.is_authenticated:
        return {"alcance_etiqueta": etiqueta_alcance(request.user)}
    return {"alcance_etiqueta": ""}
