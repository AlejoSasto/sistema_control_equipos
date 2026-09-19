from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import Rol, Permiso, Usuario, RolPermiso, UsuarioRol
from organizacion.models import Area, Decanatura, Programa, Sede
from personas.models import TipoVinculo, Persona
from equipos.models import Equipo


class Command(BaseCommand):
    help = "Poblar roles, permisos, catálogos y usuarios oficiales según Documentos 01, 02, 03 y 06"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando carga de datos institucionales (Docs 01, 02, 03 y 06)..."))

        with transaction.atomic():
            # 1. Permisos del Documento 01
            permisos_data = [
                ("equipos.registrar", "Registrar equipos propios"),
                ("equipos.ver_propios", "Ver y mostrar el QR de los equipos propios"),
                ("equipos.ver_todos", "Ver todos los equipos registrados (uso administrativo)"),
                ("control.escanear", "Acceder a la pantalla de control de salida (rol celador)"),
                ("control.ver_alertas", "Ver el histórico de alertas generadas"),
                ("catalogos.administrar", "Crear/editar sedes, facultades, programas, áreas y tipos de vínculo"),
                ("personas.administrar", "Crear/editar/inactivar personas de la comunidad académica"),
                ("usuarios.administrar", "Crear/editar/inactivar usuarios y resetear contraseñas"),
                ("roles.administrar", "Crear/editar roles y asignar permisos"),
                ("permisos.ver", "Ver el catálogo de permisos (solo lectura)"),
                ("perfil.ver_propio", "Ver información personal, equipos y métricas propias"),
            ]

            permisos_objs = {}
            for cod, desc in permisos_data:
                p, _ = Permiso.objects.get_or_create(codigo=cod, defaults={"descripcion": desc})
                permisos_objs[cod] = p
            self.stdout.write(self.style.SUCCESS(f"[OK] {len(permisos_objs)} Permisos configurados"))

            # 2. Roles del Documento 01
            roles_def = {
                "miembro_comunidad": (
                    "Miembro de la Comunidad Académica",
                    "Gestor del Conocimiento, Creador de Oportunidades, Administrativo y Graduado: "
                    "solo acceden a su perfil personal, equipos y métricas propias",
                    ["equipos.registrar", "equipos.ver_propios", "perfil.ver_propio"],
                ),
                "celador": (
                    "Celador / Personal de Control",
                    "Vigilancia en punto de salida que escanea el QR y verifica coincidencia",
                    ["control.escanear", "control.ver_alertas"],
                ),
                "admin_sistema": (
                    "Administrador del Sistema",
                    "Coordina el proceso institucional, gestiona catálogos, usuarios y auditoría",
                    list(permisos_objs.keys()),
                ),
            }

            roles_objs = {}
            for nom, (display_name, desc, perms_list) in roles_def.items():
                rol, _ = Rol.objects.get_or_create(
                    nombre=nom,
                    defaults={"descripcion": desc, "activo": True},
                )
                rol.descripcion = desc
                rol.save(update_fields=["descripcion"])
                for p_cod in perms_list:
                    RolPermiso.objects.get_or_create(rol=rol, permiso=permisos_objs[p_cod])
                roles_objs[nom] = rol
            self.stdout.write(self.style.SUCCESS(f"[OK] {len(roles_objs)} Roles configurados y asignados"))

            # 2.5 Catálogo TipoVinculo (Doc 06 + equivalencias institucionales)
            # nombre  = término que usa la universidad (visible en formularios)
            # codigo  = nombre técnico interno del sistema
            tipos_vinculo_data = [
                {
                    "codigo": "docente",
                    "nombre": "Gestor del Conocimiento",
                    "permite_autoregistro": True,
                    "dominio_correo_requerido": "@ucundinamarca.edu.co",
                    "rol_asignado": roles_objs["miembro_comunidad"],
                },
                {
                    "codigo": "estudiante",
                    "nombre": "Creador de Oportunidades",
                    "permite_autoregistro": True,
                    "dominio_correo_requerido": "@ucundinamarca.edu.co",
                    "rol_asignado": roles_objs["miembro_comunidad"],
                },
                {
                    "codigo": "gestor_administrativo",
                    "nombre": "Administrativo",
                    "permite_autoregistro": False,
                    "dominio_correo_requerido": "@ucundinamarca.edu.co",
                    "rol_asignado": roles_objs["miembro_comunidad"],
                },
                {
                    "codigo": "egresado",
                    "nombre": "Graduado",
                    "permite_autoregistro": True,
                    "dominio_correo_requerido": "@ucundinamarca.edu.co",
                    "rol_asignado": roles_objs["miembro_comunidad"],
                },
            ]

            # Códigos obsoletos → código canónico (migración de datos legacy)
            legacy_to_canonical = {
                "gestor_conocimiento": "docente",
                "creador_oportunidades": "estudiante",
                "administrativo": "gestor_administrativo",
                "graduado": "egresado",
            }

            tipos_objs = {}
            for tv_data in tipos_vinculo_data:
                tv, _ = TipoVinculo.objects.update_or_create(
                    codigo=tv_data["codigo"],
                    defaults={**tv_data, "activo": True},
                )
                tipos_objs[tv_data["codigo"]] = tv

            # Reasignar personas de tipos legacy al catálogo canónico
            for legacy_codigo, canonical_codigo in legacy_to_canonical.items():
                legacy = TipoVinculo.objects.filter(codigo=legacy_codigo).first()
                if legacy and legacy.codigo != canonical_codigo:
                    Persona.objects.filter(tipo_vinculo=legacy).update(
                        tipo_vinculo=tipos_objs[canonical_codigo]
                    )
                    legacy.activo = False
                    legacy.save(update_fields=["activo"])

            self.stdout.write(self.style.SUCCESS(f"[OK] {len(tipos_objs)} Tipos de Vínculo canónicos configurados"))

            # 3. Sedes (incluyendo Seccional Ubaté del ejemplo del Doc 01)
            sedes_data = [
                ("UBATE", "Seccional Ubaté", "Ubaté"),
                ("FUSA", "Sede Fusagasugá (Principal)", "Fusagasugá"),
                ("GIR", "Seccional Girardot", "Girardot"),
                ("CHIA", "Extensión Chía", "Chía"),
                ("FAC", "Extensión Facatativá", "Facatativá"),
            ]
            sedes_objs = {}
            for cod, nom, ciu in sedes_data:
                s, _ = Sede.objects.get_or_create(
                    codigo=cod,
                    defaults={"nombre": nom, "ciudad": ciu, "activo": True},
                )
                sedes_objs[cod] = s
            self.stdout.write(self.style.SUCCESS(f"[OK] {len(sedes_objs)} Sedes registradas"))

            # 4. Facultades (independientes de sede)
            facultades_data = [
                ("FAC-ING", "Facultad de Ingeniería"),
                ("FAC-CIEN", "Facultad de Ciencias Agropecuarias"),
                ("FAC-ADM", "Facultad de Ciencias Administrativas"),
            ]
            facultades_objs = {}
            for cod, nom in facultades_data:
                f, _ = Decanatura.objects.update_or_create(
                    codigo=cod,
                    defaults={"nombre": nom, "activo": True},
                )
                facultades_objs[cod] = f
            self.stdout.write(self.style.SUCCESS(f"[OK] {len(facultades_objs)} Facultades registradas"))

            # 5. Programas (sede + facultad)
            programas_data = [
                ("IS-UBATE", "Ingeniería de Sistemas y Computación", "UBATE", "FAC-ING", "pregrado"),
                ("IS-FUSA", "Ingeniería de Sistemas y Computación", "FUSA", "FAC-ING", "pregrado"),
                ("IA-FUSA", "Ingeniería Agronómica", "FUSA", "FAC-CIEN", "pregrado"),
            ]
            programas_objs = {}
            for cod, nom, sede_cod, fac_cod, niv in programas_data:
                prog, _ = Programa.objects.update_or_create(
                    codigo=cod,
                    defaults={
                        "nombre": nom,
                        "sede": sedes_objs[sede_cod],
                        "facultad": facultades_objs[fac_cod],
                        "nivel": niv,
                        "activo": True,
                    },
                )
                programas_objs[cod] = prog
            self.stdout.write(self.style.SUCCESS(f"[OK] {len(programas_objs)} Programas creados"))

            # 5.5 Áreas / Dependencias
            areas_data = [
                ("CGCA", "Biblioteca"),
                ("ISU", "Interacción Social Universitaria"),
                ("CTeI", "Ciencia, Tecnología e Innovación"),
            ]
            areas_objs = {}
            for cod, nom in areas_data:
                a, _ = Area.objects.update_or_create(
                    codigo=cod,
                    defaults={"nombre": nom, "activo": True},
                )
                areas_objs[cod] = a
            self.stdout.write(self.style.SUCCESS(f"[OK] {len(areas_objs)} Áreas registradas"))

            # 6. Personas de la Comunidad Académica
            persona_docente, _ = Persona.objects.get_or_create(
                numero_documento="1070123456",
                defaults={
                    "tipo_documento": "CC",
                    "nombres": "Juan Camilo",
                    "apellidos": "Rodríguez Castro",
                    "tipo_vinculo": tipos_objs["docente"],
                    "sede": sedes_objs["UBATE"],
                    "programa": programas_objs["IS-UBATE"],
                    "activo": True,
                },
            )

            persona_admin, _ = Persona.objects.update_or_create(
                numero_documento="1070654321",
                defaults={
                    "tipo_documento": "CC",
                    "nombres": "Diana Marcela",
                    "apellidos": "Morales Gómez",
                    "tipo_vinculo": tipos_objs["gestor_administrativo"],
                    "sede": sedes_objs["UBATE"],
                    "area": areas_objs["CGCA"],
                    "programa": None,
                    "activo": True,
                },
            )

            persona_inactiva, _ = Persona.objects.get_or_create(
                numero_documento="1070999999",
                defaults={
                    "tipo_documento": "CC",
                    "nombres": "Pedro Pablo",
                    "apellidos": "Pérez Desvinculado",
                    "tipo_vinculo": tipos_objs["egresado"],
                    "sede": sedes_objs["UBATE"],
                    "activo": False,  # Regla 7 del Doc 01: inactivo
                },
            )
            self.stdout.write(self.style.SUCCESS("[OK] Personas de la comunidad creadas"))

            # 7. Usuarios del Sistema
            # Administrador
            if not Usuario.objects.filter(username="admin").exists():
                u_admin = Usuario.objects.create_superuser(
                    username="admin",
                    email="admin@ucundinamarca.edu.co",
                    password="admin123",
                    first_name="Administrador",
                    last_name="General",
                )
                UsuarioRol.objects.create(usuario=u_admin, rol=roles_objs["admin_sistema"])
                self.stdout.write(self.style.SUCCESS("[OK] Superadmin 'admin' creado (pass: admin123)"))

            # Celador de Portería
            if not Usuario.objects.filter(username="celador1").exists():
                u_celador = Usuario.objects.create_user(
                    username="celador1",
                    email="vigilancia.ubate@ucundinamarca.edu.co",
                    password="celador123",
                    first_name="Marco",
                    last_name="Torres",
                    is_staff=True,
                )
                UsuarioRol.objects.create(usuario=u_celador, rol=roles_objs["celador"])
                self.stdout.write(self.style.SUCCESS("[OK] Celador 'celador1' creado (pass: celador123)"))

            # Docente (Miembro de la Comunidad)
            if not Usuario.objects.filter(username="docente1").exists():
                u_docente = Usuario.objects.create_user(
                    username="docente1",
                    email="juan.rodriguez@ucundinamarca.edu.co",
                    password="docente123",
                    first_name="Juan Camilo",
                    last_name="Rodríguez",
                    persona=persona_docente,
                )
                UsuarioRol.objects.create(usuario=u_docente, rol=roles_objs["miembro_comunidad"])
                self.stdout.write(self.style.SUCCESS("[OK] Docente 'docente1' creado (pass: docente123)"))

            # 8. Equipos de Prueba
            eq_personal, _ = Equipo.objects.get_or_create(
                serial="LNV-UBATE-2026-01",
                defaults={
                    "persona": persona_docente,
                    "tipo": Equipo.TIPO_PORTATIL,
                    "marca": "Lenovo",
                    "modelo": "ThinkPad T14 Gen 3",
                    "propiedad": Equipo.PROPIEDAD_PERSONAL,
                    "activo": True,
                },
            )

            eq_inst, _ = Equipo.objects.update_or_create(
                serial="DELL-INST-2026-99",
                defaults={
                    "persona": persona_docente,
                    "tipo": Equipo.TIPO_PORTATIL,
                    "marca": "Dell",
                    "modelo": "Latitude 5420",
                    "propiedad": Equipo.PROPIEDAD_INSTITUCIONAL,
                    "dependencia": areas_objs["CGCA"],
                    "activo": True,
                },
            )

            eq_inactivo, _ = Equipo.objects.get_or_create(
                serial="HP-BAJA-ALERT-00",
                defaults={
                    "persona": persona_docente,
                    "tipo": Equipo.TIPO_PORTATIL,
                    "marca": "HP",
                    "modelo": "EliteBook 840",
                    "propiedad": Equipo.PROPIEDAD_PERSONAL,
                    "activo": False,
                },
            )

            eq_persona_inactiva, _ = Equipo.objects.get_or_create(
                serial="ASUS-INACT-ALERT-77",
                defaults={
                    "persona": persona_inactiva,
                    "tipo": Equipo.TIPO_PORTATIL,
                    "marca": "Asus",
                    "modelo": "ZenBook 14",
                    "propiedad": Equipo.PROPIEDAD_PERSONAL,
                    "activo": True,
                },
            )

            self.stdout.write(self.style.SUCCESS(f"[OK] Equipo personal: {eq_personal.serial}"))
            self.stdout.write(self.style.SUCCESS(f"[OK] Equipo institucional: {eq_inst.serial}"))
            self.stdout.write(self.style.SUCCESS(f"[OK] Equipo inactivo (R6): {eq_inactivo.serial}"))
            self.stdout.write(self.style.SUCCESS(f"[OK] Equipo titular inactivo (R7): {eq_persona_inactiva.serial}"))

        self.stdout.write(self.style.SUCCESS("\n[EXITO] Seeder de datos oficiales completado!"))
