from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Usuario, Rol, Permiso, RolPermiso, UsuarioRol
from organizacion.models import Sede, Decanatura, Programa, Area
from personas.models import Persona, TipoVinculo


class RegistroExternoTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Sedes y Programas
        self.sede = Sede.objects.create(codigo="UBATE", nombre="Seccional Ubaté", ciudad="Ubaté")
        self.facultad = Decanatura.objects.create(codigo="FAC-ING", nombre="Facultad de Ingeniería")
        self.programa = Programa.objects.create(
            codigo="IS-UBATE", nombre="Ingeniería de Sistemas", sede=self.sede, facultad=self.facultad, nivel="pregrado"
        )

        # Roles y Permisos (pueden existir por migraciones de catálogo)
        self.perm_registrar, _ = Permiso.objects.get_or_create(
            codigo="equipos.registrar", defaults={"descripcion": "Registrar equipos"}
        )
        self.perm_ver_propios, _ = Permiso.objects.get_or_create(
            codigo="equipos.ver_propios", defaults={"descripcion": "Ver QR propios"}
        )
        self.perm_perfil, _ = Permiso.objects.get_or_create(
            codigo="perfil.ver_propio", defaults={"descripcion": "Ver perfil propio"}
        )
        self.perm_admin_cat, _ = Permiso.objects.get_or_create(
            codigo="catalogos.administrar", defaults={"descripcion": "Administrar catálogos"}
        )

        self.rol_miembro, _ = Rol.objects.get_or_create(
            nombre="miembro_comunidad", defaults={"descripcion": "Miembro de la comunidad"}
        )
        RolPermiso.objects.get_or_create(rol=self.rol_miembro, permiso=self.perm_registrar)
        RolPermiso.objects.get_or_create(rol=self.rol_miembro, permiso=self.perm_ver_propios)
        RolPermiso.objects.get_or_create(rol=self.rol_miembro, permiso=self.perm_perfil)

        self.rol_admin, _ = Rol.objects.get_or_create(
            nombre="admin_sistema", defaults={"descripcion": "Administrador"}
        )
        RolPermiso.objects.get_or_create(rol=self.rol_admin, permiso=self.perm_admin_cat)

        self.rol_celador, _ = Rol.objects.get_or_create(
            nombre="celador", defaults={"descripcion": "Celador"}
        )

        # Tipos de Vínculo:
        # Note: migration 0002 already created standard records, so get_or_create ensures no duplicate error
        self.vinculo_estudiante, _ = TipoVinculo.objects.get_or_create(
            codigo="creador_oportunidades",
            defaults={
                "nombre": "Creador de Oportunidades",
                "permite_autoregistro": True,
                "dominio_correo_requerido": "@ucundinamarca.edu.co",
                "rol_asignado": self.rol_miembro,
            },
        )
        self.vinculo_estudiante.permite_autoregistro = True
        self.vinculo_estudiante.dominio_correo_requerido = "@ucundinamarca.edu.co"
        self.vinculo_estudiante.rol_asignado = self.rol_miembro
        self.vinculo_estudiante.save()

        self.vinculo_docente, _ = TipoVinculo.objects.get_or_create(
            codigo="gestor_conocimiento",
            defaults={
                "nombre": "Gestor del Conocimiento",
                "permite_autoregistro": False,
                "rol_asignado": self.rol_miembro,
            },
        )
        self.vinculo_docente.permite_autoregistro = False
        self.vinculo_docente.save()

        self.area = Area.objects.create(codigo="CGCA-TEST", nombre="Área Test Registro")
        self.vinculo_admin, _ = TipoVinculo.objects.get_or_create(
            codigo="gestor_administrativo",
            defaults={
                "nombre": "Gestor Administrativo",
                "permite_autoregistro": True,
                "dominio_correo_requerido": "@ucundinamarca.edu.co",
                "rol_asignado": self.rol_miembro,
            },
        )
        self.vinculo_admin.permite_autoregistro = True
        self.vinculo_admin.dominio_correo_requerido = "@ucundinamarca.edu.co"
        self.vinculo_admin.rol_asignado = self.rol_miembro
        self.vinculo_admin.nombre = "Gestor Administrativo"
        self.vinculo_admin.save()

    def test_registro_exitoso_con_correo_institucional(self):
        """Autorregistro exitoso con correo @ucundinamarca.edu.co: crea Persona, Usuario y Rol."""
        data = {
            "nombres": "Ana María",
            "apellidos": "Gómez Suárez",
            "tipo_documento": "CC",
            "numero_documento": "1010202303",
            "tipo_vinculo": str(self.vinculo_estudiante.id),
            "correo": "ana.gomez@ucundinamarca.edu.co",
            "sede": str(self.sede.id),
            "programa": str(self.programa.id),
            "password": "PasswordSegura123!",
            "password_confirm": "PasswordSegura123!",
            "acepta_tratamiento": "on",
        }

        response = self.client.post(reverse("accounts:registro"), data)
        self.assertRedirects(response, reverse("accounts:login"))

        # Validar creación de Persona
        persona = Persona.objects.filter(numero_documento="1010202303").first()
        self.assertIsNotNone(persona)
        self.assertEqual(persona.nombres, "Ana María")
        self.assertEqual(persona.tipo_vinculo, self.vinculo_estudiante)
        self.assertTrue(persona.activo)

        # Validar creación de Usuario: username = parte local del correo institucional
        usuario = Usuario.objects.filter(email="ana.gomez@ucundinamarca.edu.co").first()
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario.username, "ana.gomez")
        self.assertEqual(usuario.persona, persona)

        # Validar asignación de Rol según TipoVinculo.rol_asignado
        self.assertTrue(usuario.roles.filter(id=self.rol_miembro.id).exists())
        self.assertTrue(usuario.tiene_permiso("equipos.registrar"))
        self.assertTrue(usuario.tiene_permiso("perfil.ver_propio"))
        self.assertFalse(usuario.tiene_permiso("personas.administrar"))
        self.assertFalse(usuario.tiene_permiso("catalogos.administrar"))

        # Login por username local, correo y cédula
        self.assertTrue(
            self.client.login(username="ana.gomez", password="PasswordSegura123!")
        )
        self.client.logout()
        self.assertTrue(
            self.client.login(
                username="ana.gomez@ucundinamarca.edu.co", password="PasswordSegura123!"
            )
        )
        self.client.logout()
        self.assertTrue(
            self.client.login(username="1010202303", password="PasswordSegura123!")
        )

    def test_registro_rechazado_por_dominio_no_institucional(self):
        """Se rechaza el registro si el correo no termina en @ucundinamarca.edu.co."""
        data = {
            "nombres": "Pedro",
            "apellidos": "Pérez",
            "tipo_documento": "CC",
            "numero_documento": "1020304050",
            "tipo_vinculo": str(self.vinculo_estudiante.id),
            "correo": "pedro.perez@gmail.com",
            "sede": str(self.sede.id),
            "password": "PasswordSegura123!",
            "password_confirm": "PasswordSegura123!",
            "acepta_tratamiento": "on",
        }

        response = self.client.post(reverse("accounts:registro"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "@ucundinamarca.edu.co")

        # No debe haberse creado ni Persona ni Usuario
        self.assertFalse(Persona.objects.filter(numero_documento="1020304050").exists())
        self.assertFalse(Usuario.objects.filter(email="pedro.perez@gmail.com").exists())

    def test_registro_rechazado_tipo_vinculo_no_permite_autoregistro(self):
        """No se permite autorregistro con tipos de vínculo donde permite_autoregistro=False (ej. Docente)."""
        data = {
            "nombres": "Profesor",
            "apellidos": "Intruso",
            "tipo_documento": "CC",
            "numero_documento": "999888777",
            "tipo_vinculo": str(self.vinculo_docente.id),
            "correo": "prof.intruso@ucundinamarca.edu.co",
            "sede": str(self.sede.id),
            "password": "PasswordSegura123!",
            "password_confirm": "PasswordSegura123!",
            "acepta_tratamiento": "on",
        }

        response = self.client.post(reverse("accounts:registro"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no es válido o no permite autorregistro")
        self.assertFalse(Persona.objects.filter(numero_documento="999888777").exists())

    def test_registro_rechazado_contrasena_igual_documento(self):
        """La contraseña no puede ser igual al número de documento."""
        data = {
            "nombres": "Laura",
            "apellidos": "Vega",
            "tipo_documento": "CC",
            "numero_documento": "777666555",
            "tipo_vinculo": str(self.vinculo_estudiante.id),
            "correo": "laura.vega@ucundinamarca.edu.co",
            "sede": str(self.sede.id),
            "password": "777666555",
            "password_confirm": "777666555",
            "acepta_tratamiento": "on",
        }

        response = self.client.post(reverse("accounts:registro"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no puede ser igual al número de documento")
        self.assertFalse(Persona.objects.filter(numero_documento="777666555").exists())

    def test_registro_rechazado_contrasenas_no_coinciden(self):
        """Contraseñas distintas deben ser rechazadas."""
        data = {
            "nombres": "Carlos",
            "apellidos": "Díaz",
            "tipo_documento": "CC",
            "numero_documento": "888777666",
            "tipo_vinculo": str(self.vinculo_estudiante.id),
            "correo": "carlos.diaz@ucundinamarca.edu.co",
            "sede": str(self.sede.id),
            "password": "PasswordSegura123!",
            "password_confirm": "OtraPasswordDistinta",
            "acepta_tratamiento": "on",
        }

        response = self.client.post(reverse("accounts:registro"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Las contraseñas no coinciden")
        self.assertFalse(Persona.objects.filter(numero_documento="888777666").exists())

    def test_seguridad_regla_3_2_prevenir_rol_sensible_en_autoregistro(self):
        """
        Regla 3.2: En la administración de tipos de vínculo, no se puede asociar
        un rol sensible (admin_sistema, celador) a un tipo que tenga autorregistro activado.
        """
        admin_user = Usuario.objects.create_superuser(
            username="admin_test", password="adminpassword123", email="admin@test.com"
        )
        UsuarioRol.objects.create(usuario=admin_user, rol=self.rol_admin)
        self.client.login(username="admin_test", password="adminpassword123")

        data = {
            "codigo": "vulnerable_test",
            "nombre": "Vínculo Inseguro",
            "permite_autoregistro": "on",
            "dominio_correo_requerido": "@ucundinamarca.edu.co",
            "rol_asignado": str(self.rol_admin.id),  # Intento de asociar admin_sistema
            "activo": "on",
        }

        response = self.client.post(reverse("personas:tipo_vinculo_create"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "motivos de seguridad institucional")
        self.assertFalse(TipoVinculo.objects.filter(codigo="vulnerable_test").exists())

    def test_registro_rechazado_sin_consentimiento(self):
        data = {
            "nombres": "Ana",
            "apellidos": "Sin Consentir",
            "tipo_documento": "CC",
            "numero_documento": "555444333",
            "tipo_vinculo": str(self.vinculo_estudiante.id),
            "correo": "ana.sin@ucundinamarca.edu.co",
            "sede": str(self.sede.id),
            "programa": str(self.programa.id),
            "password": "PasswordSegura123!",
            "password_confirm": "PasswordSegura123!",
        }
        response = self.client.post(reverse("accounts:registro"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "política de tratamiento de datos")
        self.assertFalse(Persona.objects.filter(numero_documento="555444333").exists())

    def test_registro_gestor_administrativo_sin_area(self):
        """El gestor se registra sin área; la asigna después un admin en el panel."""
        data = {
            "nombres": "Luis",
            "apellidos": "Admin",
            "tipo_documento": "CC",
            "numero_documento": "3030303030",
            "tipo_vinculo": str(self.vinculo_admin.id),
            "correo": "luis.admin@ucundinamarca.edu.co",
            "sede": str(self.sede.id),
            "password": "PasswordSegura123!",
            "password_confirm": "PasswordSegura123!",
            "acepta_tratamiento": "on",
        }
        response = self.client.post(reverse("accounts:registro"), data)
        self.assertRedirects(response, reverse("accounts:login"))
        persona = Persona.objects.get(numero_documento="3030303030")
        self.assertEqual(persona.tipo_vinculo, self.vinculo_admin)
        self.assertIsNone(persona.area_id)
        self.assertIsNone(persona.programa_id)
        usuario = persona.usuario
        self.assertEqual(usuario.username, "luis.admin")
        self.assertEqual(usuario.email, "luis.admin@ucundinamarca.edu.co")

    def test_registro_gestor_administrativo_ignora_area_en_post(self):
        """Si alguien envía área en el POST de autorregistro, se ignora."""
        data = {
            "nombres": "Luis",
            "apellidos": "SinArea",
            "tipo_documento": "CC",
            "numero_documento": "4040404040",
            "tipo_vinculo": str(self.vinculo_admin.id),
            "correo": "luis.sinarea@ucundinamarca.edu.co",
            "sede": str(self.sede.id),
            "area": str(self.area.id),
            "password": "PasswordSegura123!",
            "password_confirm": "PasswordSegura123!",
            "acepta_tratamiento": "on",
        }
        response = self.client.post(reverse("accounts:registro"), data)
        self.assertRedirects(response, reverse("accounts:login"))
        persona = Persona.objects.get(numero_documento="4040404040")
        self.assertIsNone(persona.area_id)
