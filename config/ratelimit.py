"""Respuestas cuando se excede el rate limit."""

from django.http import HttpResponse
from django.shortcuts import render


def ratelimited_view(request, exception=None):
    if request.headers.get("HX-Request") == "true":
        return HttpResponse(
            '<div class="alert alert-warning" role="alert">'
            "Demasiadas solicitudes. Espere un momento e intente de nuevo."
            "</div>",
            status=429,
        )
    return render(
        request,
        "errors/ratelimited.html",
        status=429,
    )
