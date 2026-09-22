from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from organizacion.models import AlcanceUsuario, Area, Decanatura, Programa, Sede


def _alcance_global(usuario):
    AlcanceUsuario.objects.get_or_create(
        usuario=usuario,
        nivel=AlcanceUsuario.NIVEL_GLOBAL,
        objeto_id=None,
        defaults={"activo": True},
    )
from personas.models import Persona, TipoVinculo
from panel.models import LogCambioRol


class PanelPermisosTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.sede = Sede.objects.create(codigo="UBATE", nombre="Seccional Ubaté", ciudad="Ubaté")
        self.vinculo, _ = TipoVinculo.objects.get_or_create(
            codigo="gestor_conocimiento", defaults={"nombre": "Gestor del Conocimiento"}
        )

        self.perm_personas, _ = Permiso.objects.get_or_create(
            codigo="personas.administrar", defaults={"descripcion": "Admin personas"}
        )
        self.perm_usuarios, _ = Permiso.objects.get_or_create(
            codigo="usuarios.administrar", defaults={"descripcion": "Admin usuarios"}
        )
        self.perm_roles, _ = Permiso.objects.get_or_create(
            codigo="roles.administrar", defaults={"descripcion": "Admin roles"}
        )
        self.perm_ver, _ = Permiso.objects.get_or_create(
            codigo="permisos.ver", defaults={"descripcion": "Ver permisos"}
        )

        self.rol_admin = Rol.objects.create(nombre="admin_sistema", descripcion="Admin")
        for p in (self.perm_personas, self.perm_usuarios, self.perm_roles, self.perm_ver):
            RolPermiso.objects.create(rol=self.rol_admin, permiso=p)

        self.rol_miembro, _ = Rol.objects.get_or_create(
            nombre="miembro_comunidad", defaults={"descripcion": "Miembro"}
        )

        self.admin = Usuario.objects.create_user(username="admin_panel", password="adminpass123", email="admin@test.com")
        UsuarioRol.objects.create(usuario=self.admin, rol=self.rol_admin)
        _alcance_global(self.admin)

        self.miembro = Usuario.objects.create_user(username="miembro1", password="miembropass123", email="m@test.com")
        UsuarioRol.objects.create(usuario=self.miembro, rol=self.rol_miembro)

    def test_panel_personas_requiere_permiso(self):
        """Usuario sin personas.administrar no puede acceder al panel de personas."""
        self.client.login(username="miembro1", password="miembropass123")
        response = self.client.get(reverse("panel:personas_list"))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("/panel/personas", response.url)

    def test_panel_personas_accesible_con_permiso(self):
        self.client.login(username="admin_panel", password="adminpass123")
        response = self.client.get(reverse("panel:personas_list"))
        self.assertEqual(response.status_code, 200)


class PanelReglasNegocioTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.sede = Sede.objects.create(codigo="UBATE", nombre="Seccional Ubaté", ciudad="Ubaté")
        self.vinculo, _ = TipoVinculo.objects.get_or_create(
            codigo="gestor_conocimiento", defaults={"nombre": "Gestor del Conocimiento"}
        )

        self.perm_usuarios, _ = Permiso.objects.get_or_create(
            codigo="usuarios.administrar", defaults={"descripcion": "Admin usuarios"}
        )
        self.perm_roles, _ = Permiso.objects.get_or_create(
            codigo="roles.administrar", defaults={"descripcion": "Admin roles"}
        )

        self.rol_admin = Rol.objects.create(nombre="admin_sistema", descripcion="Admin")
        RolPermiso.objects.create(rol=self.rol_admin, permiso=self.perm_usuarios)
        RolPermiso.objects.create(rol=self.rol_admin, permiso=self.perm_roles)

        self.rol_celador = Rol.objects.create(nombre="celador", descripcion="Celador")

        self.admin = Usuario.objects.create_user(
            username="unico_admin", password="adminpass123", email="unico@test.com", activo=True
        )
        UsuarioRol.objects.create(usuario=self.admin, rol=self.rol_admin)
        _alcance_global(self.admin)

    def test_no_puede_quitarse_propio_rol_admin(self):
        """Regla 4.1: admin no puede quitarse su propio rol admin_sistema si es el único."""
        self.client.login(username="unico_admin", password="adminpass123")
        response = self.client.post(
            reverse("panel:usuario_detail", kwargs={"pk": self.admin.pk}),
            {"action": "update_roles", "roles": [str(self.rol_celador.id)]},
        )
        self.assertRedirects(response, reverse("panel:usuario_detail", kwargs={"pk": self.admin.pk}))
        self.assertTrue(self.admin.roles.filter(nombre="admin_sistema").exists())

    def test_no_puede_inactivar_ultimo_admin(self):
        """Regla 4.2: no se puede inactivar el último admin_sistema activo."""
        self.client.login(username="unico_admin", password="adminpass123")
        response = self.client.post(reverse("panel:usuario_toggle", kwargs={"pk": self.admin.pk}))
        self.assertRedirects(response, reverse("panel:usuario_detail", kwargs={"pk": self.admin.pk}))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.activo)

    def test_no_puede_inactivar_rol_con_usuarios_activos(self):
        """Regla 4.5: rol con usuarios activos no se puede inactivar."""
        self.client.login(username="unico_admin", password="adminpass123")
        response = self.client.post(
            reverse("panel:rol_edit", kwargs={"pk": self.rol_admin.pk}),
            {"nombre": "admin_sistema", "descripcion": "Admin", "activo": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.rol_admin.refresh_from_db()
        self.assertTrue(self.rol_admin.activo)

    def test_cambio_roles_genera_log(self):
        """Regla 4.6: cambios de roles quedan registrados en log."""
        persona = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="123",
            nombres="Test",
            apellidos="User",
            tipo_vinculo=self.vinculo,
            sede=self.sede,
        )
        usuario = Usuario.objects.create_user(
            username="testuser", password="testpass123", email="testuser@test.com", persona=persona
        )
        UsuarioRol.objects.create(usuario=usuario, rol=self.rol_celador)

        self.client.login(username="unico_admin", password="adminpass123")
        self.client.post(
            reverse("panel:usuario_detail", kwargs={"pk": usuario.pk}),
            {"action": "update_roles", "roles": [str(self.rol_celador.id)]},
        )
        self.assertTrue(LogCambioRol.objects.filter(usuario_que_modifico=self.admin).exists())


class PanelOrganizacionTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.perm_cat, _ = Permiso.objects.get_or_create(
            codigo="catalogos.administrar", defaults={"descripcion": "Catálogos"}
        )
        self.perm_personas, _ = Permiso.objects.get_or_create(
            codigo="personas.administrar", defaults={"descripcion": "Personas"}
        )
        self.rol_admin = Rol.objects.create(nombre="admin_sistema", descripcion="Admin")
        RolPermiso.objects.create(rol=self.rol_admin, permiso=self.perm_cat)
        RolPermiso.objects.create(rol=self.rol_admin, permiso=self.perm_personas)
        self.admin = Usuario.objects.create_user(username="org_admin", password="adminpass123", email="org@test.com")
        UsuarioRol.objects.create(usuario=self.admin, rol=self.rol_admin)
        _alcance_global(self.admin)

        self.sede = Sede.objects.create(codigo="UBATE", nombre="Ubaté", ciudad="Ubaté")
        self.facultad = Decanatura.objects.create(codigo="FAC-ING", nombre="Facultad de Ingeniería")
        self.area = Area.objects.create(
            sede=self.sede, codigo="ISU", nombre="Interacción Social Universitaria"
        )
        self.vinculo_admin, _ = TipoVinculo.objects.get_or_create(
            codigo="gestor_administrativo", defaults={"nombre": "Administrativo"}
        )

    def test_crear_facultad_sin_sede(self):
        self.client.login(username="org_admin", password="adminpass123")
        response = self.client.post(
            reverse("panel:decanatura_create"),
            {"codigo": "FAC-ART", "nombre": "Facultad de Artes", "activo": "on"},
        )
        self.assertRedirects(response, reverse("panel:organizacion_list"))
        self.assertTrue(Decanatura.objects.filter(codigo="FAC-ART").exists())

    def test_persona_administrativa_con_area(self):
        self.client.login(username="org_admin", password="adminpass123")
        response = self.client.post(
            reverse("panel:persona_create"),
            {
                "tipo_documento": "CC",
                "numero_documento": "99887766",
                "nombres": "Ana",
                "apellidos": "Admin",
                "tipo_vinculo": str(self.vinculo_admin.id),
                "sede": str(self.sede.id),
                "area": str(self.area.id),
                "programa": "",
                "activo": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        persona = Persona.objects.get(numero_documento="99887766")
        self.assertEqual(persona.area.codigo, "ISU")
        self.assertIsNone(persona.programa_id)

    def test_persona_administrativa_sin_area(self):
        """Área pendiente: admin puede crear gestor sin área asignada."""
        self.client.login(username="org_admin", password="adminpass123")
        response = self.client.post(
            reverse("panel:persona_create"),
            {
                "tipo_documento": "CC",
                "numero_documento": "88776655",
                "nombres": "Luis",
                "apellidos": "Pendiente",
                "tipo_vinculo": str(self.vinculo_admin.id),
                "sede": str(self.sede.id),
                "area": "",
                "programa": "",
                "activo": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        persona = Persona.objects.get(numero_documento="88776655")
        self.assertIsNone(persona.area_id)
        self.assertIsNone(persona.programa_id)

    def test_filtro_sin_area(self):
        self.client.login(username="org_admin", password="adminpass123")
        Persona.objects.create(
            tipo_documento="CC",
            numero_documento="11223344",
            nombres="Sin",
            apellidos="Area",
            tipo_vinculo=self.vinculo_admin,
            sede=self.sede,
            area=None,
            activo=True,
        )
        Persona.objects.create(
            tipo_documento="CC",
            numero_documento="55667788",
            nombres="Con",
            apellidos="Area",
            tipo_vinculo=self.vinculo_admin,
            sede=self.sede,
            area=self.area,
            activo=True,
        )
        response = self.client.get(reverse("panel:personas_list"), {"sin_area": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "11223344")
        self.assertNotContains(response, "55667788")
        self.assertContains(response, "Sin área")

    def test_persona_rechaza_area_de_otra_sede(self):
        sede_otra = Sede.objects.create(codigo="FUSA", nombre="Fusagasugá", ciudad="Fusagasugá")
        area_otra = Area.objects.create(
            sede=sede_otra, codigo="ISU", nombre="ISU Fusa"
        )
        self.client.login(username="org_admin", password="adminpass123")
        response = self.client.post(
            reverse("panel:persona_create"),
            {
                "tipo_documento": "CC",
                "numero_documento": "77889900",
                "nombres": "Cruz",
                "apellidos": "Sede",
                "tipo_vinculo": str(self.vinculo_admin.id),
                "sede": str(self.sede.id),
                "area": str(area_otra.id),
                "programa": "",
                "activo": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Persona.objects.filter(numero_documento="77889900").exists())

    def test_mismo_codigo_area_en_sedes_distintas(self):
        sede_otra = Sede.objects.create(codigo="FUSA", nombre="Fusagasugá", ciudad="Fusagasugá")
        Area.objects.create(sede=sede_otra, codigo="ISU", nombre="ISU Fusa")
        self.assertEqual(Area.objects.filter(codigo="ISU").count(), 2)
        self.client.login(username="org_admin", password="adminpass123")
        response = self.client.post(
            reverse("panel:area_create"),
            {
                "codigo": "CGCA",
                "nombre": "Biblioteca Ubaté",
                "sede": str(self.sede.id),
                "activo": "on",
            },
        )
        self.assertRedirects(response, reverse("panel:organizacion_list"))
        self.assertTrue(
            Area.objects.filter(sede=self.sede, codigo="CGCA").exists()
        )


class PanelDesbloqueoAxesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.perm_desbloquear, _ = Permiso.objects.get_or_create(
            codigo="usuarios.desbloquear",
            defaults={"descripcion": "Desbloquear login Axes"},
        )
        self.perm_usuarios, _ = Permiso.objects.get_or_create(
            codigo="usuarios.administrar",
            defaults={"descripcion": "Admin usuarios"},
        )
        self.rol_admin, _ = Rol.objects.get_or_create(
            nombre="admin_sistema", defaults={"descripcion": "Admin", "activo": True}
        )
        RolPermiso.objects.get_or_create(rol=self.rol_admin, permiso=self.perm_desbloquear)
        RolPermiso.objects.get_or_create(rol=self.rol_admin, permiso=self.perm_usuarios)

        self.rol_miembro, _ = Rol.objects.get_or_create(
            nombre="miembro_comunidad", defaults={"descripcion": "Miembro", "activo": True}
        )

        self.admin = Usuario.objects.create_user(
            username="admin_unlock", password="adminpass123", email="admin_unlock@test.com"
        )
        UsuarioRol.objects.create(usuario=self.admin, rol=self.rol_admin)
        _alcance_global(self.admin)

        self.victima = Usuario.objects.create_user(
            username="usuario_bloqueado", password="testpass123!", email="bloqueado@test.com"
        )
        UsuarioRol.objects.create(usuario=self.victima, rol=self.rol_miembro)

        self.sin_perm = Usuario.objects.create_user(
            username="sin_desbloquear", password="testpass123!", email="sin@test.com"
        )
        UsuarioRol.objects.create(usuario=self.sin_perm, rol=self.rol_miembro)

    def test_desbloquear_limpia_intentos_axes(self):
        from django.conf import settings
        from axes.models import AccessAttempt

        AccessAttempt.objects.create(
            user_agent="test",
            ip_address="127.0.0.1",
            username=self.victima.username,
            http_accept="*/*",
            path_info="/accounts/login/",
            failures_since_start=settings.AXES_FAILURE_LIMIT,
        )
        self.client.login(username="admin_unlock", password="adminpass123")
        response = self.client.get(reverse("panel:usuario_detail", kwargs={"pk": self.victima.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login bloqueado")
        self.assertContains(response, "Desbloquear login")

        response = self.client.post(
            reverse("panel:usuario_desbloquear", kwargs={"pk": self.victima.pk})
        )
        self.assertRedirects(
            response, reverse("panel:usuario_detail", kwargs={"pk": self.victima.pk})
        )
        self.assertFalse(
            AccessAttempt.objects.filter(username=self.victima.username).exists()
        )

    def test_desbloquear_requiere_permiso(self):
        from django.conf import settings
        from axes.models import AccessAttempt

        AccessAttempt.objects.create(
            user_agent="test",
            ip_address="127.0.0.1",
            username=self.victima.username,
            http_accept="*/*",
            path_info="/accounts/login/",
            failures_since_start=settings.AXES_FAILURE_LIMIT,
        )
        self.client.login(username="sin_desbloquear", password="testpass123!")
        response = self.client.post(
            reverse("panel:usuario_desbloquear", kwargs={"pk": self.victima.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            AccessAttempt.objects.filter(username=self.victima.username).exists()
        )

    def test_lockout_template_configurado(self):
        from django.conf import settings
        from django.template.loader import get_template

        self.assertEqual(settings.AXES_LOCKOUT_TEMPLATE, "accounts/lockout.html")
        tpl = get_template("accounts/lockout.html")
        html = tpl.render({"failure_limit": 5, "username": "demo"})
        self.assertIn("1 hora", html)
        self.assertIn("bloqueado", html.lower())
