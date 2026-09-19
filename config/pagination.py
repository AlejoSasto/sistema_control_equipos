"""Utilidades de paginación server-side (máx. ~50 filas por página)."""
from django.core.paginator import Paginator

DEFAULT_PAGE_SIZE = 50


def paginate_queryset(request, queryset, per_page=DEFAULT_PAGE_SIZE):
    """Devuelve un Page de Django a partir del queryset y ?page=."""
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))
