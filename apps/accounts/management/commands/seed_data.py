"""
Carga inicial MVP / catálogos institucionales.

Organización: sedes, facultades, programas y áreas desde
`seed_organizacion_data.py` (fuente Excel Universidad de Cundinamarca).

También: permisos, roles, tipos de vínculo canónicos y usuario admin.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from accounts.models import Rol, Permiso, Usuario, RolPermiso, UsuarioRol
from organizacion.models import AlcanceUsuario, Area, Decanatura, Programa, Sede
from personas.models import TipoVinculo, Persona
from equipos.models import Equipo
from control_acceso.models import Movimiento

from .seed_organizacion_data import AREAS, FACULTADES, PROGRAMAS, SEDES


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
    help = (
        "Upsert catálogos institucionales UCundinamarca (idempotente). "
        "No borra usuarios/personas/equipos reales; solo limpia demos fijos del MVP."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Cargando datos institucionales..."))

        with transaction.atomic():
            self._limpiar_datos_demostracion()
            permisos_objs = self._cargar_permisos()
            roles_objs = self._cargar_roles(permisos_objs)
            self._cargar_tipos_vinculo(roles_objs)
            self._desactivar_tipos_vinculo_legado()
            org = self._cargar_organizacion()
            areas_n = self._cargar_areas()
            self._asegurar_admin(roles_objs)

            self.stdout.write(self.style.SUCCESS(
                f"\n[LISTO] Catálogos listos — "
                f"{org['sedes']} sedes, {org['facultades']} facultades, "
                f"{org['programas']} programas, {areas_n} áreas | 6 vínculos"
            ))
            self.stdout.write(self.style.SUCCESS(
                "Acceso administrador: usuario 'admin' / contraseña 'Udec2026!Admin' "
                "(solo al crear admin; redeploy no resetea contraseña)"
            ))

    def _limpiar_datos_demostracion(self):
        """Solo elimina filas del MVP de demo (listas fijas). No toca datos reales."""
        personas_demo = Persona.objects.filter(numero_documento__in=DEMO_DOCUMENTOS)
        usuarios_demo = Usuario.objects.filter(username__in=DEMO_USERNAMES)
        equipos_qs = Equipo.objects.filter(Q(serial__in=DEMO_SERIALES) | Q(persona__in=personas_demo))
        movs = Movimiento.objects.filter(
            Q(equipo__in=equipos_qs) | Q(usuario_control__in=usuarios_demo)
        ).delete()[0]
        eliminados_eq = equipos_qs.delete()[0]
        eliminados_per = personas_demo.delete()[0]
        eliminados_usr = usuarios_demo.delete()[0]
        if movs or eliminados_eq or eliminados_per or eliminados_usr:
            self.stdout.write(self.style.WARNING(
                f"[LIMPIEZA] Demostración eliminada — movimientos:{movs} equipos:{eliminados_eq} "
                f"personas:{eliminados_per} usuarios:{eliminados_usr}"
            ))
        else:
            self.stdout.write(self.style.SUCCESS("[OK] Sin datos de demostración que limpiar"))

    def _cargar_permisos(self):
        permisos_data = [
            ("equipos.registrar", "Registrar equipos propios"),
            ("equipos.ver_propios", "Ver y mostrar el código QR de los equipos propios"),
            ("equipos.ver_todos", "Consultar el inventario completo de equipos"),
            (
                "equipos.asignar_institucional",
                "Asignar, renovar, reasignar o devolver equipos institucionales de su dependencia",
            ),
            (
                "equipos.inventario_institucional",
                "Dar de alta equipos institucionales en inventario de su dependencia (sin asignar persona)",
            ),
            (
                "equipos.gestionar_responsables",
                "Administrar responsables de dependencia (quién asigna equipos por unidad)",
            ),
            ("control.escanear", "Usar el puesto de control de salida (escaneo QR)"),
            ("control.ver_alertas", "Consultar el historial de salidas y alertas"),
            ("catalogos.administrar", "Administrar sedes, facultades, programas, áreas y tipos de vínculo"),
            ("personas.administrar", "Administrar personas de la comunidad académica"),
            ("usuarios.administrar", "Administrar usuarios y restablecer contraseñas"),
            (
                "usuarios.desbloquear",
                "Desbloquear cuentas bloqueadas por intentos fallidos de login",
            ),
            (
                "usuarios.gestionar_alcance",
                "Asignar y administrar el alcance jerárquico de otros usuarios",
            ),
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
            "responsable_dependencia": (
                "Responsable de dependencia: inventaria y asigna equipos institucionales en sus unidades",
                ["equipos.asignar_institucional", "equipos.inventario_institucional"],
                True,
            ),
            "vigilante": (
                "Personal de portería: control de salida en su sede",
                ["control.escanear", "control.ver_alertas"],
                True,
            ),
            # Rol legado: desactivado; usar vigilante
            "celador": (
                "Personal de portería (legado; usar rol vigilante)",
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
        self.stdout.write(self.style.SUCCESS(
            f"[OK] {activos} roles activos (celador legado inactivo)"
        ))
        return roles_objs

    def _cargar_tipos_vinculo(self, roles_objs):
        """
        Códigos canónicos de comunidad + personal_externo + vigilante (doc 16).
        """
        rol_miembro = roles_objs["miembro_comunidad"]
        rol_vigilante = roles_objs["vigilante"]
        tipos_data = [
            {
                "codigo": "gestor_administrativo",
                "nombre": "Gestor Administrativo",
                "permite_autoregistro": True,
                "dominio_correo_requerido": "@ucundinamarca.edu.co",
                "rol_asignado": rol_miembro,
            },
            {
                "codigo": "creador_oportunidades",
                "nombre": "Creador de Oportunidades",
                "permite_autoregistro": True,
                "dominio_correo_requerido": "@ucundinamarca.edu.co",
                "rol_asignado": rol_miembro,
            },
            {
                "codigo": "gestor_conocimiento",
                "nombre": "Gestor del Conocimiento",
                "permite_autoregistro": True,
                "dominio_correo_requerido": "@ucundinamarca.edu.co",
                "rol_asignado": rol_miembro,
            },
            {
                "codigo": "egresado",
                "nombre": "Egresado",
                "permite_autoregistro": True,
                "dominio_correo_requerido": "@ucundinamarca.edu.co",
                "rol_asignado": rol_miembro,
            },
            {
                "codigo": "personal_externo",
                "nombre": "Personal Externo",
                "permite_autoregistro": True,
                "dominio_correo_requerido": None,
                "rol_asignado": rol_miembro,
            },
            {
                "codigo": "vigilante",
                "nombre": "Vigilante",
                "permite_autoregistro": False,
                "dominio_correo_requerido": None,
                "rol_asignado": rol_vigilante,
            },
        ]

        tipos_objs = {}
        for data in tipos_data:
            tv, _ = TipoVinculo.objects.update_or_create(
                codigo=data["codigo"],
                defaults={
                    "nombre": data["nombre"],
                    "permite_autoregistro": data["permite_autoregistro"],
                    "dominio_correo_requerido": data["dominio_correo_requerido"],
                    "rol_asignado": data["rol_asignado"],
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
            "celador": "vigilante",
        }
        for origen, destino in migracion.items():
            legacy = TipoVinculo.objects.filter(codigo=origen).first()
            if legacy and destino in tipos_objs:
                Persona.objects.filter(tipo_vinculo=legacy).update(
                    tipo_vinculo=tipos_objs[destino]
                )

        # No desactivar vínculos creados fuera del seed (preserva datos en producción).
        # Solo se desactivan códigos legado conocidos en _desactivar_tipos_vinculo_legado.
        self.stdout.write(self.style.SUCCESS(
            f"[OK] {len(tipos_objs)} tipos de vínculo canónicos asegurados"
        ))
        return tipos_objs["gestor_administrativo"]

    def _desactivar_tipos_vinculo_legado(self):
        """Desactiva códigos de la migración 0002 (MVP) por si quedaron activos."""
        legacy_codes = ("estudiante", "graduado", "administrativo", "docente")
        n = TipoVinculo.objects.filter(codigo__in=legacy_codes).update(
            activo=False,
            permite_autoregistro=False,
        )
        if n:
            self.stdout.write(self.style.WARNING(
                f"[LIMPIEZA] Tipos de vínculo legado desactivados: {n}"
            ))
        else:
            self.stdout.write(self.style.SUCCESS("[OK] Sin tipos de vínculo legado activos"))

    def _cargar_organizacion(self):
        """Upsert sedes/facultades/programas del catálogo. No desactiva filas ajenas al seed."""
        sede_objs = {}
        for data in SEDES:
            sede, _ = Sede.objects.update_or_create(
                codigo=data["codigo"],
                defaults={
                    "nombre": data["nombre"],
                    "ciudad": data["ciudad"],
                    "activo": True,
                },
            )
            sede_objs[data["codigo"]] = sede

        fac_objs = {}
        for data in FACULTADES:
            fac, _ = Decanatura.objects.update_or_create(
                codigo=data["codigo"],
                defaults={"nombre": data["nombre"], "activo": True},
            )
            fac_objs[data["codigo"]] = fac

        prog_codes = set()
        for data in PROGRAMAS:
            Programa.objects.update_or_create(
                codigo=data["codigo"],
                defaults={
                    "nombre": data["nombre"],
                    "sede": sede_objs[data["sede"]],
                    "facultad": fac_objs[data["facultad"]],
                    "nivel": data.get("nivel", Programa.NIVEL_PREGRADO),
                    "activo": True,
                },
            )
            prog_codes.add(data["codigo"])

        # Alias legado del MVP anterior (solo código IS-UBATE → ISC-UBATE)
        if "IS-UBATE" not in prog_codes and "ISC-UBATE" in prog_codes:
            legado = Programa.objects.filter(codigo="IS-UBATE").first()
            if legado and legado.activo:
                Persona.objects.filter(programa=legado).update(
                    programa_id=Programa.objects.get(codigo="ISC-UBATE").pk
                )
                legado.activo = False
                legado.save(update_fields=["activo"])

        self.stdout.write(self.style.SUCCESS(
            f"[OK] Organización upsert: {len(sede_objs)} sedes · "
            f"{len(fac_objs)} facultades · {len(prog_codes)} programas "
            f"(no se desactivan sedes/programas fuera del catálogo)"
        ))
        return {
            "sedes": len(sede_objs),
            "facultades": len(fac_objs),
            "programas": len(prog_codes),
        }

    def _cargar_areas(self):
        """Upsert áreas del catálogo por (sede, codigo). No desactiva áreas ajenas."""
        sedes = list(Sede.objects.filter(activo=True))
        if not sedes:
            self.stdout.write(self.style.WARNING(
                "[AVISO] Sin sedes activas; no se cargan áreas"
            ))
            return 0
        n = 0
        for sede in sedes:
            for data in AREAS:
                Area.objects.update_or_create(
                    sede=sede,
                    codigo=data["codigo"],
                    defaults={"nombre": data["nombre"], "activo": True},
                )
                n += 1
        self.stdout.write(self.style.SUCCESS(
            f"[OK] {n} áreas upsert ({len(sedes)} sedes × {len(AREAS)} códigos, "
            f"sin desactivar otras)"
        ))
        return n

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
            self.stdout.write(self.style.SUCCESS(
                "[OK] Usuario administrador creado (admin / Udec2026!Admin)"
            ))
        else:
            # No resetear contraseña en re-seed (p. ej. cada deploy en Render)
            admin.email = "admin@ucundinamarca.edu.co"
            admin.first_name = "Administrador"
            admin.last_name = "Sistema"
            admin.is_superuser = True
            admin.is_staff = True
            admin.activo = True
            admin.is_active = True
            admin.save(update_fields=[
                "email", "first_name", "last_name",
                "is_superuser", "is_staff", "activo", "is_active",
            ])
            self.stdout.write(self.style.SUCCESS(
                "[OK] Usuario administrador verificado (contraseña sin cambios)"
            ))

        UsuarioRol.objects.filter(usuario=admin).exclude(rol=roles_objs["admin_sistema"]).delete()
        UsuarioRol.objects.get_or_create(usuario=admin, rol=roles_objs["admin_sistema"])
        AlcanceUsuario.objects.get_or_create(
            usuario=admin,
            nivel=AlcanceUsuario.NIVEL_GLOBAL,
            objeto_id=None,
            defaults={"activo": True},
        )
