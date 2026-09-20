"""Tests del dashboard de administrador."""

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from control_acceso.models import Movimiento
from equipos.models import Equipo
from organizacion.models import Decanatura, Programa, Sede
from personas.models import Persona, TipoVinculo


@override_settings(AXES_ENABLED=False, RATELIMIT_ENABLE=False)
class DashboardTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.sede, _ = Sede.objects.get_or_create(
            codigo="DASH-UB",
            defaults={"nombre": "Sede Dashboard", "ciudad": "Ubaté"},
        )
        self.sede2, _ = Sede.objects.get_or_create(
            codigo="DASH-FUSA",
            defaults={"nombre": "Sede Fusa Test", "ciudad": "Fusagasugá"},
        )
        self.facultad, _ = Decanatura.objects.get_or_create(
            codigo="DASH-FAC",
            defaults={"nombre": "Facultad Dash"},
        )
        self.programa, _ = Programa.objects.get_or_create(
            codigo="DASH-IS",
            defaults={
                "nombre": "Programa Dash",
                "sede": self.sede,
                "facultad": self.facultad,
                "nivel": "pregrado",
            },
        )
        self.rol_miembro, _ = Rol.objects.get_or_create(
            nombre="miembro_comunidad",
            defaults={"descripcion": "Miembro"},
        )
        self.vinculo, _ = TipoVinculo.objects.get_or_create(
            codigo="creador_oportunidades",
            defaults={
                "nombre": "Creador",
                "permite_autoregistro": True,
                "rol_asignado": self.rol_miembro,
            },
        )
        self.persona, _ = Persona.objects.get_or_create(
            numero_documento="2099001122",
            defaults={
                "tipo_documento": "CC",
                "nombres": "Luis",
                "apellidos": "Dash",
                "tipo_vinculo": self.vinculo,
                "sede": self.sede,
                "programa": self.programa,
            },
        )
        self.perm_ver, _ = Permiso.objects.get_or_create(
            codigo="reportes.ver", defaults={"descripcion": "Ver reportes"}
        )
        self.perm_export, _ = Permiso.objects.get_or_create(
            codigo="reportes.exportar", defaults={"descripcion": "Exportar"}
        )
        self.perm_escanear, _ = Permiso.objects.get_or_create(
            codigo="control.escanear", defaults={"descripcion": "Escanear"}
        )

        self.rol_admin, _ = Rol.objects.get_or_create(
            nombre="dash_admin", defaults={"descripcion": "Dash admin"}
        )
        RolPermiso.objects.get_or_create(rol=self.rol_admin, permiso=self.perm_ver)
        RolPermiso.objects.get_or_create(rol=self.rol_admin, permiso=self.perm_export)

        self.admin, _ = Usuario.objects.get_or_create(
            username="dash_admin",
            defaults={"email": "dash_admin@test.com"},
        )
        self.admin.set_password("TestPass123!")
        self.admin.save()
        UsuarioRol.objects.get_or_create(usuario=self.admin, rol=self.rol_admin)

        self.sin_perm, _ = Usuario.objects.get_or_create(
            username="dash_sin",
            defaults={"email": "dash_sin@test.com"},
        )
        self.sin_perm.set_password("TestPass123!")
        self.sin_perm.save()

        self.solo_ver_rol, _ = Rol.objects.get_or_create(
            nombre="dash_solo_ver", defaults={"descripcion": "Solo ver"}
        )
        RolPermiso.objects.get_or_create(rol=self.solo_ver_rol, permiso=self.perm_ver)
        self.viewer, _ = Usuario.objects.get_or_create(
            username="dash_viewer",
            defaults={"email": "dash_viewer@test.com"},
        )
        self.viewer.set_password("TestPass123!")
        self.viewer.save()
        UsuarioRol.objects.get_or_create(usuario=self.viewer, rol=self.solo_ver_rol)

        self.celador, _ = Usuario.objects.get_or_create(
            username="dash_celador",
            defaults={"email": "dash_celador@test.com"},
        )
        self.celador.set_password("TestPass123!")
        self.celador.save()
        rol_cel, _ = Rol.objects.get_or_create(
            nombre="dash_celador_rol", defaults={"descripcion": "Celador"}
        )
        RolPermiso.objects.get_or_create(rol=rol_cel, permiso=self.perm_escanear)
        UsuarioRol.objects.get_or_create(usuario=self.celador, rol=rol_cel)

        self.equipo, _ = Equipo.objects.get_or_create(
            serial="DASH-TEST-001",
            defaults={
                "persona": self.persona,
                "tipo": Equipo.TIPO_PORTATIL,
                "marca": "Dell",
                "modelo": "XPS",
                "propiedad": Equipo.PROPIEDAD_PERSONAL,
            },
        )
        if not Movimiento.objects.filter(equipo=self.equipo, resultado=Movimiento.RESULTADO_OK).exists():
            Movimiento.objects.create(
                equipo=self.equipo,
                token_escaneado=str(self.equipo.token_qr),
                usuario_control=self.celador,
                resultado=Movimiento.RESULTADO_OK,
            )

    def test_dashboard_requiere_permiso(self):
        self.client.login(username="dash_sin", password="TestPass123!")
        resp = self.client.get(reverse("panel:dashboard"))
        self.assertEqual(resp.status_code, 302)

    def test_dashboard_hoy_ok(self):
        self.client.login(username="dash_admin", password="TestPass123!")
        resp = self.client.get(reverse("panel:dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Movimientos")
        self.assertContains(resp, "Dato actual")
        self.assertContains(resp, "En el periodo")

    def test_parcial_htmx(self):
        self.client.login(username="dash_admin", password="TestPass123!")
        resp = self.client.get(
            reverse("panel:dashboard_parcial"),
            {"preset": "hoy"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "chart-linea")

    def test_datos_json(self):
        self.client.login(username="dash_admin", password="TestPass123!")
        resp = self.client.get(reverse("panel:dashboard_datos"), {"preset": "hoy"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("linea", data)
        self.assertIn("dona", data)
        self.assertIn("sedes", data)
        self.assertIn("top_alertas", data)

    def test_top_alertas_vacio_sin_alertas(self):
        self.client.login(username="dash_admin", password="TestPass123!")
        resp = self.client.get(reverse("panel:dashboard_datos"), {"preset": "hoy"})
        data = resp.json()
        self.assertTrue(data["top_alertas"]["vacio"])

    def test_export_sigue_exigiendo_exportar(self):
        self.client.login(username="dash_viewer", password="TestPass123!")
        hoy = timezone.localdate()
        resp = self.client.post(
            reverse("reportes:exportar", args=["movimientos"]),
            {
                "fecha_inicio": hoy.isoformat(),
                "fecha_fin": hoy.isoformat(),
            },
        )
        self.assertEqual(resp.status_code, 302)

    def test_viewer_puede_ver_dashboard(self):
        self.client.login(username="dash_viewer", password="TestPass123!")
        resp = self.client.get(reverse("panel:dashboard"))
        self.assertEqual(resp.status_code, 200)
