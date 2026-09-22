from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import Usuario, Rol, Permiso, RolPermiso, UsuarioRol
from control_acceso.models import Movimiento
from equipos.models import Equipo
from organizacion.models import AlcanceUsuario, Area, Decanatura, Programa, Sede
from personas.models import (
    Persona,
    TipoVinculo,
    VisitaExterno,
    CODIGO_VINCULO_EXTERNO,
    CODIGO_VINCULO_VIGILANTE,
)
from personas.services import (
    registrar_visita,
    cerrar_visitas_vencidas_batch,
    visita_activa,
)


class PersonalExternoVisitaTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.sede = Sede.objects.create(codigo="UBATE-T16", nombre="Seccional Ubaté T16", ciudad="Ubaté")
        self.sede2 = Sede.objects.create(codigo="FUSA-T16", nombre="Seccional Fusagasugá T16", ciudad="Fusa")
        self.facultad = Decanatura.objects.create(codigo="FAC-ING-T16", nombre="Ingeniería T16")
        self.programa = Programa.objects.create(
            codigo="ISC-UBATE-T16",
            nombre="Ingeniería de Sistemas T16",
            sede=self.sede,
            facultad=self.facultad,
            nivel="pregrado",
        )
        self.programa2 = Programa.objects.create(
            codigo="ISC-FUSA-T16",
            nombre="Ingeniería de Sistemas T16 Fusa",
            sede=self.sede2,
            facultad=self.facultad,
            nivel="pregrado",
        )
        self.area = Area.objects.create(
            sede=self.sede, codigo="CGCA-T16", nombre="Control T16"
        )
        self.area2 = Area.objects.create(
            sede=self.sede2, codigo="CGCA-T16", nombre="Control T16 Fusa"
        )

        self.perm_perfil, _ = Permiso.objects.get_or_create(
            codigo="perfil.ver_propio", defaults={"descripcion": "perfil"}
        )
        self.perm_reg, _ = Permiso.objects.get_or_create(
            codigo="equipos.registrar", defaults={"descripcion": "reg"}
        )
        self.perm_ver, _ = Permiso.objects.get_or_create(
            codigo="equipos.ver_propios", defaults={"descripcion": "ver"}
        )
        self.perm_scan, _ = Permiso.objects.get_or_create(
            codigo="control.escanear", defaults={"descripcion": "scan"}
        )
        self.perm_alertas, _ = Permiso.objects.get_or_create(
            codigo="control.ver_alertas", defaults={"descripcion": "alertas"}
        )
        self.perm_personas, _ = Permiso.objects.get_or_create(
            codigo="personas.administrar", defaults={"descripcion": "personas"}
        )

        self.rol_miembro, _ = Rol.objects.get_or_create(
            nombre="miembro_comunidad", defaults={"descripcion": "miembro", "activo": True}
        )
        self.rol_miembro.activo = True
        self.rol_miembro.save(update_fields=["activo"])
        for p in (self.perm_perfil, self.perm_reg, self.perm_ver):
            RolPermiso.objects.get_or_create(rol=self.rol_miembro, permiso=p)

        self.rol_vigilante, _ = Rol.objects.get_or_create(
            nombre="vigilante", defaults={"descripcion": "vigilante", "activo": True}
        )
        self.rol_vigilante.activo = True
        self.rol_vigilante.save(update_fields=["activo"])
        RolPermiso.objects.get_or_create(rol=self.rol_vigilante, permiso=self.perm_scan)
        RolPermiso.objects.get_or_create(rol=self.rol_vigilante, permiso=self.perm_alertas)

        self.rol_admin, _ = Rol.objects.get_or_create(
            nombre="admin_sistema", defaults={"descripcion": "admin", "activo": True}
        )
        self.rol_admin.activo = True
        self.rol_admin.save(update_fields=["activo"])
        RolPermiso.objects.get_or_create(rol=self.rol_admin, permiso=self.perm_personas)

        self.vinculo_ext, _ = TipoVinculo.objects.update_or_create(
            codigo=CODIGO_VINCULO_EXTERNO,
            defaults={
                "nombre": "Personal Externo",
                "permite_autoregistro": True,
                "dominio_correo_requerido": None,
                "rol_asignado": self.rol_miembro,
                "activo": True,
            },
        )
        self.vinculo_vig, _ = TipoVinculo.objects.update_or_create(
            codigo=CODIGO_VINCULO_VIGILANTE,
            defaults={
                "nombre": "Vigilante",
                "permite_autoregistro": False,
                "dominio_correo_requerido": None,
                "rol_asignado": self.rol_vigilante,
                "activo": True,
            },
        )
        self.vinculo_est, _ = TipoVinculo.objects.get_or_create(
            codigo="creador_oportunidades",
            defaults={
                "nombre": "Creador",
                "permite_autoregistro": True,
                "dominio_correo_requerido": "@ucundinamarca.edu.co",
                "rol_asignado": self.rol_miembro,
            },
        )
        self.vinculo_est.permite_autoregistro = True
        self.vinculo_est.dominio_correo_requerido = "@ucundinamarca.edu.co"
        self.vinculo_est.rol_asignado = self.rol_miembro
        self.vinculo_est.save()

        hoy = timezone.localdate()
        self.hoy = hoy
        self.fin = hoy + timedelta(days=7)

    def test_registro_externo_sin_dominio_institucional(self):
        data = {
            "nombres": "Carlos",
            "apellidos": "Visitante",
            "tipo_documento": "CC",
            "numero_documento": "900100200",
            "tipo_vinculo": str(self.vinculo_ext.id),
            "correo": "carlos.visita@gmail.com",
            "sede": str(self.sede.id),
            "unidad_tipo": "facultad",
            "unidad_id": str(self.facultad.id),
            "fecha_inicio": self.hoy.isoformat(),
            "fecha_fin": self.fin.isoformat(),
            "password": "PasswordSegura123!",
            "password_confirm": "PasswordSegura123!",
            "acepta_tratamiento": "on",
        }
        response = self.client.post(reverse("accounts:registro"), data)
        self.assertRedirects(response, reverse("accounts:login"))
        persona = Persona.objects.get(numero_documento="900100200")
        self.assertEqual(persona.tipo_vinculo.codigo, CODIGO_VINCULO_EXTERNO)
        self.assertTrue(Usuario.objects.filter(email="carlos.visita@gmail.com").exists())
        visita = visita_activa(persona)
        self.assertIsNotNone(visita)
        self.assertEqual(visita.sede_id, self.sede.id)
        self.assertEqual(visita.unidad_tipo, "facultad")

    def test_documento_duplicado_externo_hint_login(self):
        persona = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="900100201",
            nombres="Ana",
            apellidos="Externa",
            tipo_vinculo=self.vinculo_ext,
            sede=self.sede,
            activo=True,
        )
        Usuario.objects.create_user(
            username="ana.ext@gmail.com",
            email="ana.ext@gmail.com",
            password="PasswordSegura123!",
            persona=persona,
        )
        data = {
            "nombres": "Ana",
            "apellidos": "Otra",
            "tipo_documento": "CC",
            "numero_documento": "900100201",
            "tipo_vinculo": str(self.vinculo_ext.id),
            "correo": "otra@gmail.com",
            "sede": str(self.sede.id),
            "unidad_tipo": "area",
            "unidad_id": str(self.area.id),
            "fecha_inicio": self.hoy.isoformat(),
            "fecha_fin": self.fin.isoformat(),
            "password": "PasswordSegura123!",
            "password_confirm": "PasswordSegura123!",
            "acepta_tratamiento": "on",
        }
        response = self.client.post(reverse("accounts:registro"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Registrar nueva visita")

    def test_nueva_visita_cierra_activa_previa(self):
        persona = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="900100202",
            nombres="Luis",
            apellidos="Externo",
            tipo_vinculo=self.vinculo_ext,
            sede=self.sede,
            activo=True,
        )
        usuario = Usuario.objects.create_user(
            username="luis@gmail.com",
            email="luis@gmail.com",
            password="PasswordSegura123!",
            persona=persona,
        )
        UsuarioRol.objects.create(usuario=usuario, rol=self.rol_miembro)
        v1 = registrar_visita(
            persona=persona,
            sede=self.sede,
            unidad_tipo="facultad",
            unidad_id=self.facultad.id,
            fecha_inicio=self.hoy,
            fecha_fin=self.fin,
        )
        self.assertEqual(v1.estado, VisitaExterno.ESTADO_ACTIVA)
        self.client.login(username="luis@gmail.com", password="PasswordSegura123!")
        response = self.client.post(
            reverse("accounts:registrar_visita"),
            {
                "sede": str(self.sede2.id),
                "unidad_tipo": "area",
                "unidad_id": str(self.area2.id),
                "fecha_inicio": self.hoy.isoformat(),
                "fecha_fin": self.fin.isoformat(),
            },
        )
        self.assertRedirects(response, reverse("accounts:mi_perfil"))
        v1.refresh_from_db()
        self.assertEqual(v1.estado, VisitaExterno.ESTADO_FINALIZADA)
        persona.refresh_from_db()
        self.assertEqual(persona.sede_id, self.sede2.id)
        self.assertEqual(visita_activa(persona).sede_id, self.sede2.id)

    def test_vigilante_no_en_autoregistro(self):
        response = self.client.get(reverse("accounts:registro"))
        self.assertNotContains(response, self.vinculo_vig.nombre)
        self.assertContains(response, self.vinculo_ext.nombre)

    def test_alta_interna_vigilante(self):
        admin = Usuario.objects.create_user(
            username="admin_vig",
            email="admin_vig@ucundinamarca.edu.co",
            password="PasswordSegura123!",
        )
        UsuarioRol.objects.create(usuario=admin, rol=self.rol_admin)
        AlcanceUsuario.objects.create(
            usuario=admin, nivel=AlcanceUsuario.NIVEL_GLOBAL, objeto_id=None
        )
        self.client.login(username="admin_vig", password="PasswordSegura123!")
        response = self.client.post(
            reverse("panel:vigilante_create"),
            {
                "nombres": "Pedro",
                "apellidos": "Portero",
                "tipo_documento": "CC",
                "numero_documento": "800700600",
                "sede": str(self.sede.id),
                "correo": "pedro.portero@gmail.com",
                "password": "PasswordSegura123!",
                "password_confirm": "PasswordSegura123!",
            },
        )
        persona = Persona.objects.get(numero_documento="800700600")
        self.assertEqual(persona.tipo_vinculo.codigo, CODIGO_VINCULO_VIGILANTE)
        self.assertEqual(persona.sede_id, self.sede.id)
        usuario = Usuario.objects.get(email="pedro.portero@gmail.com")
        self.assertTrue(usuario.es_vigilante)
        self.assertRedirects(response, reverse("panel:persona_edit", kwargs={"pk": persona.pk}))

    def _equipo_para(self, persona, serial="EXT-QR-001"):
        return Equipo.objects.create(
            persona=persona,
            marca="Dell",
            modelo="XPS",
            serial=serial,
            tipo=Equipo.TIPO_PORTATIL,
            propiedad=Equipo.PROPIEDAD_PERSONAL,
            activo=True,
        )

    def test_kiosco_visita_vigente_y_otra_sede(self):
        persona = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="900100203",
            nombres="Eva",
            apellidos="Visitante",
            tipo_vinculo=self.vinculo_ext,
            sede=self.sede2,
            activo=True,
        )
        registrar_visita(
            persona=persona,
            sede=self.sede2,
            unidad_tipo="facultad",
            unidad_id=self.facultad.id,
            fecha_inicio=self.hoy,
            fecha_fin=self.fin,
        )
        equipo = self._equipo_para(persona)

        vig_persona = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="800700601",
            nombres="Vig",
            apellidos="Local",
            tipo_vinculo=self.vinculo_vig,
            sede=self.sede,
            activo=True,
        )
        vig_user = Usuario.objects.create_user(
            username="vig@local.com",
            email="vig@local.com",
            password="PasswordSegura123!",
            persona=vig_persona,
        )
        UsuarioRol.objects.create(usuario=vig_user, rol=self.rol_vigilante)
        self.client.login(username="vig@local.com", password="PasswordSegura123!")
        response = self.client.post(
            reverse("control_acceso:verificar_codigo"),
            {"codigo": str(equipo.token_qr)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visitante externo")
        self.assertContains(response, "Otra sede")
        mov = Movimiento.objects.latest("id")
        self.assertEqual(mov.resultado, Movimiento.RESULTADO_OK)
        self.assertTrue(mov.otra_sede)

    def test_kiosco_sin_visita_activa(self):
        persona = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="900100204",
            nombres="Sin",
            apellidos="Visita",
            tipo_vinculo=self.vinculo_ext,
            sede=self.sede,
            activo=True,
        )
        equipo = self._equipo_para(persona, serial="EXT-QR-002")
        vig_persona = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="800700602",
            nombres="Vig2",
            apellidos="Local",
            tipo_vinculo=self.vinculo_vig,
            sede=self.sede,
            activo=True,
        )
        vig_user = Usuario.objects.create_user(
            username="vig2@local.com",
            email="vig2@local.com",
            password="PasswordSegura123!",
            persona=vig_persona,
        )
        UsuarioRol.objects.create(usuario=vig_user, rol=self.rol_vigilante)
        self.client.login(username="vig2@local.com", password="PasswordSegura123!")
        response = self.client.post(
            reverse("control_acceso:verificar_codigo"),
            {"codigo": str(equipo.token_qr)},
        )
        self.assertContains(response, "SIN VISITA ACTIVA")
        mov = Movimiento.objects.latest("id")
        self.assertEqual(mov.motivo_alerta, Movimiento.MOTIVO_SIN_VISITA_ACTIVA)

    def test_kiosco_visita_vencida_cierra(self):
        persona = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="900100205",
            nombres="Ven",
            apellidos="Cida",
            tipo_vinculo=self.vinculo_ext,
            sede=self.sede,
            activo=True,
        )
        VisitaExterno.objects.create(
            persona=persona,
            sede=self.sede,
            unidad_tipo="area",
            unidad_id=self.area.id,
            fecha_inicio=self.hoy - timedelta(days=10),
            fecha_fin=self.hoy - timedelta(days=1),
            estado=VisitaExterno.ESTADO_ACTIVA,
        )
        equipo = self._equipo_para(persona, serial="EXT-QR-003")
        vig_persona = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="800700603",
            nombres="Vig3",
            apellidos="Local",
            tipo_vinculo=self.vinculo_vig,
            sede=self.sede,
            activo=True,
        )
        vig_user = Usuario.objects.create_user(
            username="vig3@local.com",
            email="vig3@local.com",
            password="PasswordSegura123!",
            persona=vig_persona,
        )
        UsuarioRol.objects.create(usuario=vig_user, rol=self.rol_vigilante)
        self.client.login(username="vig3@local.com", password="PasswordSegura123!")
        response = self.client.post(
            reverse("control_acceso:verificar_codigo"),
            {"codigo": str(equipo.token_qr)},
        )
        self.assertContains(response, "VISITA DE PERSONAL EXTERNO VENCIDA")
        self.assertTrue(persona.activo)
        self.assertIsNone(visita_activa(persona))
        mov = Movimiento.objects.latest("id")
        self.assertEqual(mov.motivo_alerta, Movimiento.MOTIVO_VISITA_VENCIDA)

    def test_batch_cierra_visitas_vencidas(self):
        persona = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="900100206",
            nombres="Batch",
            apellidos="Ext",
            tipo_vinculo=self.vinculo_ext,
            sede=self.sede,
            activo=True,
        )
        VisitaExterno.objects.create(
            persona=persona,
            sede=self.sede,
            unidad_tipo="area",
            unidad_id=self.area.id,
            fecha_inicio=self.hoy - timedelta(days=5),
            fecha_fin=self.hoy - timedelta(days=1),
            estado=VisitaExterno.ESTADO_ACTIVA,
        )
        n = cerrar_visitas_vencidas_batch(hoy=self.hoy)
        self.assertEqual(n, 1)
        self.assertIsNone(visita_activa(persona))
        self.assertTrue(Persona.objects.get(pk=persona.pk).activo)
