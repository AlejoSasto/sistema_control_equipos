"""
Carga inicial MVP para presentación.

Catálogos mínimos:
- Sede: Seccional Ubaté
- Facultad: Ingeniería
- Programa: Ingeniería de Sistemas y Computación
- Tipo de vínculo: Administrativo
- Roles: Administrador del sistema, Miembro de la comunidad
- Permisos en español

No crea usuarios de celador/docente ni equipos de prueba.
Tipos de vínculo canónicos (todos activos):
gestor_administrativo, creador_oportunidades, gestor_conocimiento, egresado.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from accounts.models import Rol, Permiso, Usuario, RolPermiso, UsuarioRol
from organizacion.models import Area, Decanatura, Programa, Sede
from personas.models import TipoVinculo, Persona
from equipos.models import Equipo
from control_acceso.models import Movimiento


# Datos de prueba antiguos a eliminar al reseedar
DEMO_USERNAMES = ("celador1", "docente1", "celador")
DEMO_DOCUMENTOS = ("1070123456", "1070654321", "1070999999")
DEMO_SERIALES = (
    "LNV-UBATE-2026-01",
    "DELL-INST-2026-99",
    "HP-BAJA-ALERT-00",
    "ASUS-INACT-ALERT-77",
)


class Command(BaseCommand):
    help = "Carga catálogos MVP (Ubaté / Ingeniería / Sistemas) y limpia datos de demostración"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Cargando datos MVP para presentación..."))

        with transaction.atomic():
            self._limpiar_datos_demostracion()
            permisos_objs = self._cargar_permisos()
            roles_objs = self._cargar_roles(permisos_objs)
            tipo_admin = self._cargar_tipos_vinculo(roles_objs)
            sede = self._cargar_organizacion()
            area = self._cargar_areas()
            self._asegurar_admin(roles_objs)

            self.stdout.write(self.style.SUCCESS(
                f"\n[LISTO] MVP listo — Sede: {sede.nombre} | "
                f"4 vínculos activos | Área: {area.nombre}"
            ))
            self.stdout.write(self.style.SUCCESS(
                "Acceso administrador: usuario 'admin' / contraseña 'Udec2026!Admin'"
            ))

    def _limpiar_datos_demostracion(self):
        personas_demo = Persona.objects.filter(numero_documento__in=DEMO_DOCUMENTOS)
        usuarios_demo = Usuario.objects.filter(username__in=DEMO_USERNAMES)
        equipos_qs = Equipo.objects.filter(Q(serial__in=DEMO_SERIALES) | Q(persona__in=personas_demo))
        movs = Movimiento.objects.filter(
            Q(equipo__in=equipos_qs) | Q(usuario_control__in=usuarios_demo)
        ).delete()[0]
        eliminados_eq = equipos_qs.delete()[0]
        eliminados_per = personas_demo.delete()[0]
        eliminados_usr = usuarios_demo.delete()[0]
        self.stdout.write(self.style.WARNING(
            f"[LIMPIEZA] Demostración eliminada — movimientos:{movs} equipos:{eliminados_eq} "
            f"personas:{eliminados_per} usuarios:{eliminados_usr}"
        ))

    def _cargar_permisos(self):
        permisos_data = [
            ("equipos.registrar", "Registrar equipos propios"),
            ("equipos.ver_propios", "Ver y mostrar el código QR de los equipos propios"),
            ("equipos.ver_todos", "Consultar el inventario completo de equipos"),
            ("control.escanear", "Usar el puesto de control de salida (escaneo QR)"),
            ("control.ver_alertas", "Consultar el historial de salidas y alertas"),
            ("catalogos.administrar", "Administrar sedes, facultades, programas, áreas y tipos de vínculo"),
            ("personas.administrar", "Administrar personas de la comunidad académica"),
            ("usuarios.administrar", "Administrar usuarios y restablecer contraseñas"),
            ("roles.administrar", "Administrar roles y asignar permisos"),
            ("permisos.ver", "Consultar el catálogo de permisos (solo lectura)"),
            ("perfil.ver_propio", "Ver el perfil personal, equipos y métricas propias"),
            ("reportes.ver", "Acceder al módulo de reportes y configurar filtros"),
            ("reportes.exportar", "Generar y descargar reportes Excel"),
        ]
        permisos_objs = {}
        for codigo, descripcion in permisos_data:
            permiso, created = Permiso.objects.get_or_create(
                codigo=codigo,
                defaults={"descripcion": descripcion},
            )
            if not created and permiso.descripcion != descripcion:
                permiso.descripcion = descripcion
                permiso.save(update_fields=["descripcion"])
            permisos_objs[codigo] = permiso
        self.stdout.write(self.style.SUCCESS(f"[OK] {len(permisos_objs)} permisos (descripciones en español)"))
        return permisos_objs

    def _cargar_roles(self, permisos_objs):
        roles_def = {
            "miembro_comunidad": (
                "Miembro de la comunidad académica: acceso solo a perfil y equipos propios",
                ["equipos.registrar", "equipos.ver_propios", "perfil.ver_propio"],
                True,
            ),
            "admin_sistema": (
                "Administrador del sistema: gestión completa de catálogos, usuarios y control de salida",
                list(permisos_objs.keys()),
                True,
            ),
            # Rol legado: se desactiva para el MVP (sin celador)
            "celador": (
                "Personal de portería (desactivado en MVP)",
                ["control.escanear", "control.ver_alertas"],
                False,
            ),
        }

        roles_objs = {}
        for nombre, (descripcion, perms, activo) in roles_def.items():
            rol, _ = Rol.objects.update_or_create(
                nombre=nombre,
                defaults={"descripcion": descripcion, "activo": activo},
            )
            RolPermiso.objects.filter(rol=rol).delete()
            if activo:
                for codigo in perms:
                    RolPermiso.objects.get_or_create(rol=rol, permiso=permisos_objs[codigo])
            roles_objs[nombre] = rol

        activos = sum(1 for r in roles_objs.values() if r.activo)
        self.stdout.write(self.style.SUCCESS(f"[OK] {activos} roles activos (celador desactivado)"))
        return roles_objs

    def _cargar_tipos_vinculo(self, roles_objs):
        """
        Solo 4 códigos canónicos, todos activos:
        gestor_administrativo, creador_oportunidades, gestor_conocimiento, egresado.
        """
        rol_miembro = roles_objs["miembro_comunidad"]
        tipos_data = [
            {
                "codigo": "gestor_administrativo",
                "nombre": "Administrativo",
                "permite_autoregistro": False,
            },
            {
                "codigo": "creador_oportunidades",
                "nombre": "Creador de Oportunidades",
                "permite_autoregistro": True,
            },
            {
                "codigo": "gestor_conocimiento",
                "nombre": "Gestor del Conocimiento",
                "permite_autoregistro": True,
            },
            {
                "codigo": "egresado",
                "nombre": "Egresado",
                "permite_autoregistro": True,
            },
        ]

        tipos_objs = {}
        for data in tipos_data:
            tv, _ = TipoVinculo.objects.update_or_create(
                codigo=data["codigo"],
                defaults={
                    "nombre": data["nombre"],
                    "permite_autoregistro": data["permite_autoregistro"],
                    "dominio_correo_requerido": "@ucundinamarca.edu.co",
                    "rol_asignado": rol_miembro,
                    "activo": True,
                },
            )
            tipos_objs[data["codigo"]] = tv

        # Reasignar personas desde códigos alias/legacy al canónico
        migracion = {
            "administrativo": "gestor_administrativo",
            "docente": "gestor_conocimiento",
            "estudiante": "creador_oportunidades",
            "graduado": "egresado",
        }
        for origen, destino in migracion.items():
            legacy = TipoVinculo.objects.filter(codigo=origen).first()
            if legacy:
                Persona.objects.filter(tipo_vinculo=legacy).update(
                    tipo_vinculo=tipos_objs[destino]
                )

        # Eliminar de la BD todo lo que no sea canónico
        eliminados, _ = TipoVinculo.objects.exclude(
            codigo__in=tipos_objs.keys()
        ).delete()
        self.stdout.write(self.style.SUCCESS(
            f"[OK] 4 tipos de vínculo activos (eliminados otros: {eliminados})"
        ))
        return tipos_objs["gestor_administrativo"]

    def _cargar_organizacion(self):
        sede, _ = Sede.objects.update_or_create(
            codigo="UBATE",
            defaults={"nombre": "Seccional Ubaté", "ciudad": "Ubaté", "activo": True},
        )
        Sede.objects.exclude(codigo="UBATE").update(activo=False)

        facultad, _ = Decanatura.objects.update_or_create(
            codigo="FAC-ING",
            defaults={"nombre": "Facultad de Ingeniería", "activo": True},
        )
        Decanatura.objects.exclude(codigo="FAC-ING").update(activo=False)

        Programa.objects.update_or_create(
            codigo="IS-UBATE",
            defaults={
                "nombre": "Ingeniería de Sistemas y Computación",
                "sede": sede,
                "facultad": facultad,
                "nivel": "pregrado",
                "activo": True,
            },
        )
        Programa.objects.exclude(codigo="IS-UBATE").update(activo=False)

        self.stdout.write(self.style.SUCCESS(
            "[OK] Organización: Ubaté · Ingeniería · Sistemas y Computación"
        ))
        return sede

    def _cargar_areas(self):
        area, _ = Area.objects.update_or_create(
            codigo="CGCA",
            defaults={"nombre": "Biblioteca", "activo": True},
        )
        Area.objects.exclude(codigo="CGCA").update(activo=False)
        self.stdout.write(self.style.SUCCESS("[OK] Área activa: Biblioteca"))
        return area

    def _asegurar_admin(self, roles_objs):
        password = "Udec2026!Admin"
        admin = Usuario.objects.filter(username="admin").first()
        if admin is None:
            admin = Usuario.objects.create_superuser(
                username="admin",
                email="admin@ucundinamarca.edu.co",
                password=password,
                first_name="Administrador",
                last_name="Sistema",
            )
            self.stdout.write(self.style.SUCCESS("[OK] Usuario administrador creado"))
        else:
            admin.set_password(password)
            admin.email = "admin@ucundinamarca.edu.co"
            admin.first_name = "Administrador"
            admin.last_name = "Sistema"
            admin.is_superuser = True
            admin.is_staff = True
            admin.activo = True
            admin.is_active = True
            admin.save()
            self.stdout.write(self.style.SUCCESS("[OK] Usuario administrador actualizado"))

        UsuarioRol.objects.filter(usuario=admin).exclude(rol=roles_objs["admin_sistema"]).delete()
        UsuarioRol.objects.get_or_create(usuario=admin, rol=roles_objs["admin_sistema"])
