from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError

from accounts.models import Usuario, Rol, Permiso, RolPermiso, UsuarioRol
from organizacion.models import Area, Decanatura, Programa, Sede
from personas.models import Persona, TipoVinculo
from equipos.models import Equipo


class EquiposModelTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.sede = Sede.objects.create(codigo="UBATE", nombre="Seccional Ubaté", ciudad="Ubaté")
        self.facultad = Decanatura.objects.create(codigo="FAC-ING", nombre="Facultad de Ingeniería")
        self.programa = Programa.objects.create(
            codigo="IS-UBATE", nombre="Ingeniería de Sistemas", sede=self.sede, facultad=self.facultad, nivel="pregrado"
        )
        self.area, _ = Area.objects.get_or_create(
            sede=self.sede, codigo="CGCA", defaults={"nombre": "Biblioteca"}
        )
        self.vinculo_docente, _ = TipoVinculo.objects.get_or_create(
            codigo="gestor_conocimiento", defaults={"nombre": "Gestor del Conocimiento"}
        )
        self.persona = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="1234567890",
            nombres="Carlos",
            apellidos="Martínez",
            tipo_vinculo=self.vinculo_docente,
            sede=self.sede,
            programa=self.programa,
        )
        self.perm_ver, _ = Permiso.objects.get_or_create(
            codigo="equipos.ver_propios", defaults={"descripcion": "Ver propios"}
        )
        self.rol_miembro, _ = Rol.objects.get_or_create(
            nombre="miembro_comunidad", defaults={"descripcion": "Miembro", "activo": True}
        )
        RolPermiso.objects.get_or_create(rol=self.rol_miembro, permiso=self.perm_ver)
        self.dueno = Usuario.objects.create_user(
            username="dueno_eq", password="testpass123!", email="dueno@test.com", persona=self.persona
        )
        UsuarioRol.objects.create(usuario=self.dueno, rol=self.rol_miembro)

        self.otra_persona = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="9998887770",
            nombres="Otra",
            apellidos="Persona",
            tipo_vinculo=self.vinculo_docente,
            sede=self.sede,
            programa=self.programa,
        )
        self.ajeno = Usuario.objects.create_user(
            username="ajeno_eq", password="testpass123!", email="ajeno@test.com", persona=self.otra_persona
        )
        UsuarioRol.objects.create(usuario=self.ajeno, rol=self.rol_miembro)

    def test_creacion_equipo_y_qr_al_vuelo(self):
        equipo = Equipo.objects.create(
            persona=self.persona,
            tipo=Equipo.TIPO_PORTATIL,
            marca="Lenovo",
            modelo="ThinkPad T14",
            serial="HP-SERIAL-TEST-01",
            propiedad=Equipo.PROPIEDAD_PERSONAL,
        )
        self.assertIsNotNone(equipo.token_qr)
        self.assertTrue(equipo.activo)

        qr_data = equipo.generar_qr_base64()
        self.assertTrue(qr_data.startswith("data:image/png;base64,"))
        token_exh = equipo.generar_token_exhibicion()
        self.assertNotEqual(token_exh, str(equipo.token_qr))
        self.assertEqual(Equipo.resolver_token_escaneado(token_exh), equipo)

        self.client.login(username="dueno_eq", password="testpass123!")
        response = self.client.get(
            reverse("equipos:render_qr_image", kwargs={"token_qr": equipo.token_qr})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")

    def test_render_qr_requiere_auth_y_dueno(self):
        equipo = Equipo.objects.create(
            persona=self.persona,
            tipo=Equipo.TIPO_PORTATIL,
            marca="Acer",
            modelo="Aspire",
            serial="ACER-IDOR-01",
            propiedad=Equipo.PROPIEDAD_PERSONAL,
        )
        url = reverse("equipos:render_qr_image", kwargs={"token_qr": equipo.token_qr})
        # Anónimo -> login redirect
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(username="ajeno_eq", password="testpass123!")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        self.client.login(username="dueno_eq", password="testpass123!")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_mostrar_qr_pantalla_solo_dueno(self):
        equipo = Equipo.objects.create(
            persona=self.persona,
            tipo=Equipo.TIPO_PORTATIL,
            marca="HP",
            modelo="Pavilion",
            serial="HP-PANTALLA-01",
            propiedad=Equipo.PROPIEDAD_PERSONAL,
        )
        url = reverse("equipos:mostrar_qr_pantalla", kwargs={"token_qr": equipo.token_qr})
        self.client.login(username="ajeno_eq", password="testpass123!")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("equipos:mis_equipos"))

        self.client.login(username="dueno_eq", password="testpass123!")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_equipo_institucional_inventario_sin_persona(self):
        equipo = Equipo.objects.create(
            persona=None,
            tipo=Equipo.TIPO_PORTATIL,
            marca="Dell",
            modelo="Latitude",
            serial="INST-NO-DEP",
            propiedad=Equipo.PROPIEDAD_INSTITUCIONAL,
            unidad_tipo="area",
            unidad_id=self.area.pk,
            estado_inventario=Equipo.ESTADO_DISPONIBLE,
            dependencia=self.area,
        )
        self.assertEqual(equipo.propiedad, Equipo.PROPIEDAD_INSTITUCIONAL)
        self.assertIsNone(equipo.persona_id)

    def test_equipo_institucional_con_asignacion(self):
        from datetime import timedelta
        from django.utils import timezone
        from equipos.models import AsignacionEquipo
        from equipos.services import crear_asignacion, crear_equipo_inventario

        equipo = crear_equipo_inventario(
            tipo=Equipo.TIPO_PORTATIL,
            marca="Dell",
            modelo="Latitude",
            serial="INST-CON-DEP",
            unidad_tipo="area",
            unidad_id=self.area.pk,
            creado_por_usuario=self.dueno,
        )
        hoy = timezone.localdate()
        asig = crear_asignacion(
            equipo=equipo,
            persona=self.persona,
            fecha_inicio=hoy,
            fecha_fin=hoy + timedelta(days=30),
            asignado_por_usuario=self.dueno,
        )
        self.assertEqual(asig.estado, AsignacionEquipo.ESTADO_ACTIVA)
        equipo.refresh_from_db()
        self.assertEqual(equipo.dependencia_id, self.area.pk)
        self.assertEqual(equipo.estado_inventario, Equipo.ESTADO_ASIGNADO)
    def test_autoregistro_rechaza_institucional(self):
        perm_reg, _ = Permiso.objects.get_or_create(
            codigo="equipos.registrar", defaults={"descripcion": "Registrar"}
        )
        RolPermiso.objects.get_or_create(rol=self.rol_miembro, permiso=perm_reg)
        self.client.login(username="dueno_eq", password="testpass123!")
        response = self.client.post(
            reverse("equipos:equipo_create"),
            {
                "tipo": Equipo.TIPO_PORTATIL,
                "marca": "Hack",
                "modelo": "Attempt",
                "serial": "HACK-INST-01",
                "propiedad": "institucional",
                "dependencia": str(self.area.pk),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Equipo.objects.filter(serial="HACK-INST-01").exists())

    def test_miembro_ve_ficha_tras_registrar(self):
        """Dueño sin alcance admin debe ver /equipos/<pk>/ tras create (no 404)."""
        perm_reg, _ = Permiso.objects.get_or_create(
            codigo="equipos.registrar", defaults={"descripcion": "Registrar"}
        )
        RolPermiso.objects.get_or_create(rol=self.rol_miembro, permiso=perm_reg)
        self.client.login(username="dueno_eq", password="testpass123!")
        response = self.client.post(
            reverse("equipos:equipo_create"),
            {
                "tipo": Equipo.TIPO_PORTATIL,
                "marca": "Asus",
                "modelo": "VivoBook",
                "serial": "PERS-FICHA-01",
                "propiedad": Equipo.PROPIEDAD_PERSONAL,
            },
        )
        self.assertEqual(response.status_code, 302)
        equipo = Equipo.objects.get(serial="PERS-FICHA-01")
        self.assertEqual(
            response.url, reverse("equipos:equipo_detail", kwargs={"pk": equipo.pk})
        )
        detail = self.client.get(reverse("equipos:equipo_detail", kwargs={"pk": equipo.pk}))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Asus")

    def test_dar_de_baja_y_alta_personal(self):
        equipo = Equipo.objects.create(
            persona=self.persona,
            tipo=Equipo.TIPO_PORTATIL,
            marca="Lenovo",
            modelo="Yoga",
            serial="PERS-BAJA-ALTA-01",
            propiedad=Equipo.PROPIEDAD_PERSONAL,
            activo=True,
        )
        self.client.login(username="dueno_eq", password="testpass123!")
        response = self.client.post(reverse("panel:equipo_dar_de_baja", kwargs={"pk": equipo.pk}))
        self.assertEqual(response.status_code, 302)
        equipo.refresh_from_db()
        self.assertFalse(equipo.activo)

        response = self.client.get(reverse("equipos:mis_equipos"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "De baja")
        self.assertContains(response, "Dar de alta")

        response = self.client.post(reverse("panel:equipo_dar_de_alta", kwargs={"pk": equipo.pk}))
        self.assertEqual(response.status_code, 302)
        equipo.refresh_from_db()
        self.assertTrue(equipo.activo)

    def test_dar_de_alta_rechaza_ajeno_e_institucional(self):
        personal = Equipo.objects.create(
            persona=self.persona,
            tipo=Equipo.TIPO_PORTATIL,
            marca="HP",
            modelo="Elite",
            serial="PERS-AJENO-01",
            propiedad=Equipo.PROPIEDAD_PERSONAL,
            activo=False,
        )
        institucional = Equipo.objects.create(
            persona=None,
            tipo=Equipo.TIPO_PORTATIL,
            marca="Dell",
            modelo="Opti",
            serial="INST-NO-ALTA-01",
            propiedad=Equipo.PROPIEDAD_INSTITUCIONAL,
            unidad_tipo="area",
            unidad_id=self.area.pk,
            estado_inventario=Equipo.ESTADO_DE_BAJA,
            activo=False,
            dependencia=self.area,
        )

        self.client.login(username="ajeno_eq", password="testpass123!")
        response = self.client.post(reverse("panel:equipo_dar_de_alta", kwargs={"pk": personal.pk}))
        self.assertEqual(response.status_code, 302)
        personal.refresh_from_db()
        self.assertFalse(personal.activo)

        self.client.login(username="dueno_eq", password="testpass123!")
        response = self.client.post(
            reverse("panel:equipo_dar_de_alta", kwargs={"pk": institucional.pk})
        )
        self.assertEqual(response.status_code, 302)
        institucional.refresh_from_db()
        self.assertFalse(institucional.activo)
