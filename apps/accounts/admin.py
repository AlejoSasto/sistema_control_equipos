from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Rol, Permiso, RolPermiso, UsuarioRol


class RolPermisoInline(admin.TabularInline):
    model = RolPermiso
    extra = 1


@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "descripcion", "created_at")
    search_fields = ("codigo", "descripcion")


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion", "activo", "created_at")
    list_filter = ("activo",)
    search_fields = ("nombre", "descripcion")
    inlines = [RolPermisoInline]


class UsuarioRolInline(admin.TabularInline):
    model = UsuarioRol
    extra = 1


@admin.register(Usuario)
class CustomUsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Vínculo Institucional",
            {
                "fields": (
                    "persona",
                    "activo",
                )
            },
        ),
    )
    list_display = (
        "username",
        "email",
        "persona",
        "ver_roles",
        "is_active",
        "is_staff",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "activo", "roles")
    search_fields = ("username", "email", "persona__numero_documento", "persona__nombres", "persona__apellidos")
    inlines = [UsuarioRolInline]

    def ver_roles(self, obj):
        return ", ".join([r.nombre for r in obj.roles.all()]) or "Sin rol"
    ver_roles.short_description = "Roles Asignados"
