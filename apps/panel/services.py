"""Reglas de negocio del panel de administración (Documento 07, sección 4)."""

from accounts.models import Rol, Usuario
from .models import LogCambioRol

ADMIN_ROL = "admin_sistema"

MODULOS_PERMISO = {
    "equipos": "Equipos",
    "control": "Control de acceso",
    "catalogos": "Catálogos",
    "personas": "Personas",
    "usuarios": "Usuarios",
    "roles": "Roles",
    "permisos": "Permisos",
    "perfil": "Perfil personal",
}


def modulo_permiso(codigo: str) -> str:
    prefijo = codigo.split(".")[0] if "." in codigo else "otros"
    return MODULOS_PERMISO.get(prefijo, "Otros")


def permisos_agrupados(queryset=None):
    from accounts.models import Permiso

    qs = queryset or Permiso.objects.prefetch_related("roles").order_by("codigo")
    grupos = {}
    for permiso in qs:
        modulo = modulo_permiso(permiso.codigo)
        grupos.setdefault(modulo, []).append(permiso)
    return grupos


def count_active_admin_users(exclude_user_id=None) -> int:
    qs = Usuario.objects.filter(
        activo=True,
        is_active=True,
        roles__nombre=ADMIN_ROL,
        roles__activo=True,
    )
    if exclude_user_id:
        qs = qs.exclude(pk=exclude_user_id)
    return qs.distinct().count()


def usuario_tiene_rol_admin(usuario) -> bool:
    return usuario.roles.filter(nombre=ADMIN_ROL, activo=True).exists()


def validate_user_deactivation(target_user) -> str | None:
    if not target_user.activo:
        return None
    if usuario_tiene_rol_admin(target_user) and count_active_admin_users(exclude_user_id=target_user.pk) == 0:
        return "No se puede inactivar el último usuario activo con rol admin_sistema."
    return None


def validate_self_admin_removal(actor, new_role_ids: set[int]) -> str | None:
    admin_rol = Rol.objects.filter(nombre=ADMIN_ROL, activo=True).first()
    if not admin_rol:
        return None
    actor_tiene_admin = actor.roles.filter(id=admin_rol.id).exists()
    conserva_admin = admin_rol.id in new_role_ids
    if actor.pk and actor_tiene_admin and not conserva_admin:
        if count_active_admin_users(exclude_user_id=actor.pk) == 0:
            return "No puede quitarse a sí mismo el rol admin_sistema: es el único administrador activo del sistema."
    return None


def validate_rol_deactivation(rol: Rol) -> str | None:
    activos = rol.usuarios.filter(activo=True, is_active=True).distinct().count()
    if activos:
        return (
            f"No se puede inactivar el rol '{rol.nombre}' porque tiene {activos} "
            f"usuario(s) activo(s) asignado(s). Reasigne esos usuarios primero."
        )
    return None


def validate_role_assignment_change(actor, target_user, new_role_ids: set[int]) -> str | None:
    if actor.pk == target_user.pk:
        return validate_self_admin_removal(actor, new_role_ids)
    return None


def registrar_cambio(usuario, descripcion: str):
    LogCambioRol.objects.create(usuario_que_modifico=usuario, descripcion=descripcion)
