"""Tests del módulo de reportes Excel."""

from datetime import date, timedelta

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from auditoria.models import AuditoriaCambio
from control_acceso.models import Movimiento
from equipos.models import Equipo
from organizacion.models import Decanatura, Programa, Sede
from personas.models import Persona, TipoVinculo
from reportes.filtros import FiltroError, FiltroFecha
from reportes.generadores.base import UmbralExcedido, verificar_umbral
from reportes.umbrales import MAX_FILAS_SYNC


@override_settings(AXES_ENABLED=False, RATELIMIT_ENABLE=False)
class ReportesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.sede, _ = Sede.objects.get_or_create(
            codigo="REP-UBATE",
            defaults={"nombre": "Sede Reportes Test", "ciudad": "Ubaté"},
        )
        self.facultad, _ = Decanatura.objects.get_or_create(
            codigo="REP-FAC",
            defaults={"nombre": "Facultad Reportes"},
        )
        self.programa, _ = Programa.objects.get_or_create(
            codigo="REP-IS",
            defaults={
                "nombre": "Programa Reportes",
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
            numero_documento="1099001122",
            defaults={
                "tipo_documento": "CC",
                "nombres": "Ana",
                "apellidos": "Prueba",
                "tipo_vinculo": self.vinculo,
                "sede": self.sede,
                "programa": self.programa,
            },
        )
        self.perm_ver, _ = Permiso.objects.get_or_create(
            codigo="reportes.ver", defaults={"descripcion": "Ver reportes"}
        )
        self.perm_export, _ = Permiso.objects.get_or_create(
            codigo="reportes.exportar", defaults={"descripcion": "Exportar reportes"}
        )
        self.perm_escanear, _ = Permiso.objects.get_or_create(
            codigo="control.escanear", defaults={"descripcion": "Escanear"}
        )

        self.rol_admin, _ = Rol.objects.get_or_create(
            nombre="admin_reportes", defaults={"descripcion": "Admin reportes"}
        )
        RolPermiso.objects.get_or_create(rol=self.rol_admin, permiso=self.perm_ver)
        RolPermiso.objects.get_or_create(rol=self.rol_admin, permiso=self.perm_export)

        self.rol_solo_ver, _ = Rol.objects.get_or_create(
            nombre="solo_ver_reportes", defaults={"descripcion": "Solo ver"}
        )
        RolPermiso.objects.get_or_create(rol=self.rol_solo_ver, permiso=self.perm_ver)

        self.admin, _ = Usuario.objects.get_or_create(
            username="admin_rep",
            defaults={"email": "admin_rep@test.com"},
        )
        self.admin.set_password("TestPass123!")
        self.admin.save()
        UsuarioRol.objects.get_or_create(usuario=self.admin, rol=self.rol_admin)

        self.viewer, _ = Usuario.objects.get_or_create(
            username="viewer_rep",
            defaults={"email": "viewer_rep@test.com"},
        )
        self.viewer.set_password("TestPass123!")
        self.viewer.save()
        UsuarioRol.objects.get_or_create(usuario=self.viewer, rol=self.rol_solo_ver)

        self.sin_perm, _ = Usuario.objects.get_or_create(
            username="sin_rep",
            defaults={"email": "sin_rep@test.com"},
        )
        self.sin_perm.set_password("TestPass123!")
        self.sin_perm.save()

        self.celador, _ = Usuario.objects.get_or_create(
            username="celador_rep",
            defaults={"email": "celador_rep@test.com"},
        )
        self.celador.set_password("TestPass123!")
        self.celador.save()
        rol_cel, _ = Rol.objects.get_or_create(
            nombre="celador_rep", defaults={"descripcion": "Celador"}
        )
        RolPermiso.objects.get_or_create(rol=rol_cel, permiso=self.perm_escanear)
        UsuarioRol.objects.get_or_create(usuario=self.celador, rol=rol_cel)

        self.equipo, _ = Equipo.objects.get_or_create(
            serial="REP-TEST-001",
            defaults={
                "persona": self.persona,
                "tipo": Equipo.TIPO_PORTATIL,
                "marca": "Lenovo",
                "modelo": "T14",
                "propiedad": Equipo.PROPIEDAD_PERSONAL,
            },
        )
        if not Movimiento.objects.filter(equipo=self.equipo).exists():
            Movimiento.objects.create(
                equipo=self.equipo,
                token_escaneado=str(self.equipo.token_qr),
                usuario_control=self.celador,
                resultado=Movimiento.RESULTADO_OK,
            )
            Movimiento.objects.create(
                equipo=self.equipo,
                token_escaneado=str(self.equipo.token_qr),
                usuario_control=self.celador,
                resultado=Movimiento.RESULTADO_ALERTA,
                observacion="Prueba alerta",
            )

        hoy = timezone.localdate()
        self.fecha_inicio = (hoy - timedelta(days=7)).isoformat()
        self.fecha_fin = hoy.isoformat()

    def test_index_requiere_permiso(self):
        self.client.login(username="sin_rep", password="TestPass123!")
        resp = self.client.get(reverse("reportes:index"))
        self.assertEqual(resp.status_code, 302)

        self.client.login(username="admin_rep", password="TestPass123!")
        resp = self.client.get(reverse("reportes:index"))
        self.assertEqual(resp.status_code, 200)

    def test_export_requiere_permiso_exportar(self):
        self.client.login(username="viewer_rep", password="TestPass123!")
        resp = self.client.post(
            reverse("reportes:exportar", args=["movimientos"]),
            {"fecha_inicio": self.fecha_inicio, "fecha_fin": self.fecha_fin},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(
            AuditoriaCambio.objects.filter(accion=AuditoriaCambio.ACCION_EXPORTAR).exists()
        )

    def test_export_movimientos_ok_y_auditoria(self):
        self.client.login(username="admin_rep", password="TestPass123!")
        resp = self.client.post(
            reverse("reportes:exportar", args=["movimientos"]),
            {"fecha_inicio": self.fecha_inicio, "fecha_fin": self.fecha_fin},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertTrue(resp.content[:2] == b"PK")  # zip/xlsx magic
        self.assertGreater(len(resp.content), 1000)

        reg = AuditoriaCambio.objects.filter(
            accion=AuditoriaCambio.ACCION_EXPORTAR, entidad="reporte"
        ).first()
        self.assertIsNotNone(reg)
        self.assertEqual(reg.detalle.get("tipo_reporte"), "movimientos")
        self.assertIn("filtros_aplicados", reg.detalle)

    def test_export_equipos_smoke(self):
        self.client.login(username="admin_rep", password="TestPass123!")
        resp = self.client.post(reverse("reportes:exportar", args=["equipos"]), {})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.content[:2] == b"PK")

    def test_export_personas_smoke(self):
        self.client.login(username="admin_rep", password="TestPass123!")
        resp = self.client.post(reverse("reportes:exportar", args=["personas"]), {})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.content[:2] == b"PK")

    def test_export_alertas_smoke(self):
        self.client.login(username="admin_rep", password="TestPass123!")
        resp = self.client.post(
            reverse("reportes:exportar", args=["alertas"]),
            {"fecha_inicio": self.fecha_inicio, "fecha_fin": self.fecha_fin},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.content[:2] == b"PK")

    def test_export_ejecutivo_smoke(self):
        self.client.login(username="admin_rep", password="TestPass123!")
        resp = self.client.post(
            reverse("reportes:exportar", args=["ejecutivo"]),
            {"fecha_inicio": self.fecha_inicio, "fecha_fin": self.fecha_fin},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.content[:2] == b"PK")

    def test_filtro_fecha_max_90_dias(self):
        inicio = date.today() - timedelta(days=100)
        fin = date.today()
        f = FiltroFecha(fecha_inicio=inicio, fecha_fin=fin, obligatorio=True)
        with self.assertRaises(FiltroError):
            f.validar()

    def test_umbral_filas(self):
        with self.assertRaises(UmbralExcedido):
            verificar_umbral(MAX_FILAS_SYNC + 1)
        verificar_umbral(MAX_FILAS_SYNC)

    def test_export_rechaza_rango_largo(self):
        self.client.login(username="admin_rep", password="TestPass123!")
        inicio = (date.today() - timedelta(days=100)).isoformat()
        fin = date.today().isoformat()
        resp = self.client.post(
            reverse("reportes:exportar", args=["movimientos"]),
            {"fecha_inicio": inicio, "fecha_fin": fin},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(
            AuditoriaCambio.objects.filter(
                accion=AuditoriaCambio.ACCION_EXPORTAR, detalle__tipo_reporte="movimientos"
            ).exists()
        )
