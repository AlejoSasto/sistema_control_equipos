"""Tests del módulo de alcance jerárquico."""

from django.test import Client, TestCase
from django.urls import reverse

from accounts.alcance import (
    alcance_de,
    aplicar_alcance,
    personas_visibles,
    puede_ver_objeto,
)
from accounts.models import Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from organizacion.models import AlcanceUsuario, Decanatura, Programa, Sede
from personas.models import Persona, TipoVinculo


class AlcanceFiltradoTestCase(TestCase):
    def setUp(self):
        self.sede_ubate = Sede.objects.create(codigo="UBATE", nombre="Ubaté", ciudad="Ubaté")
        self.sede_fusa = Sede.objects.create(codigo="FUSA", nombre="Fusagasugá", ciudad="Fusagasugá")
        self.facultad = Decanatura.objects.create(codigo="FAC-ING", nombre="Ingeniería")
        self.prog_ubate = Programa.objects.create(
            codigo="ISC-UB",
            nombre="Ing. Ubaté",
            sede=self.sede_ubate,
            facultad=self.facultad,
        )
        self.prog_fusa = Programa.objects.create(
            codigo="ISC-FU",
            nombre="Ing. Fusa",
            sede=self.sede_fusa,
            facultad=self.facultad,
        )
        self.vinculo, _ = TipoVinculo.objects.get_or_create(
            codigo="creador_oportunidades",
            defaults={"nombre": "Estudiante"},
        )
        self.persona_ubate = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="1001",
            nombres="Ana",
            apellidos="Ubaté",
            tipo_vinculo=self.vinculo,
            sede=self.sede_ubate,
            programa=self.prog_ubate,
        )
        self.persona_fusa = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="1002",
            nombres="Luis",
            apellidos="Fusa",
            tipo_vinculo=self.vinculo,
            sede=self.sede_fusa,
            programa=self.prog_fusa,
        )
        self.admin = Usuario.objects.create_user(
            username="admin_g", password="pass12345", email="admin_g@test.com"
        )
        AlcanceUsuario.objects.create(
            usuario=self.admin,
            nivel=AlcanceUsuario.NIVEL_GLOBAL,
            objeto_id=None,
        )
        self.sede_admin = Usuario.objects.create_user(
            username="admin_ubate", password="pass12345", email="admin_ubate@test.com"
        )
        AlcanceUsuario.objects.create(
            usuario=self.sede_admin,
            nivel=AlcanceUsuario.NIVEL_SEDE,
            objeto_id=self.sede_ubate.pk,
        )

    def test_alcance_global_ve_todo(self):
        qs = aplicar_alcance(self.admin, Persona.objects.all())
        self.assertEqual(qs.count(), 2)

    def test_alcance_sede_filtra_personas(self):
        qs = personas_visibles(self.sede_admin)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().pk, self.persona_ubate.pk)

    def test_puede_ver_objeto_idor(self):
        self.assertTrue(puede_ver_objeto(self.sede_admin, self.persona_ubate))
        self.assertFalse(puede_ver_objeto(self.sede_admin, self.persona_fusa))

    def test_alcance_programa(self):
        user = Usuario.objects.create_user(
            username="prog", password="pass12345", email="prog@test.com"
        )
        AlcanceUsuario.objects.create(
            usuario=user,
            nivel=AlcanceUsuario.NIVEL_PROGRAMA,
            objeto_id=self.prog_ubate.pk,
        )
        alcance = alcance_de(user)
        self.assertIn(self.prog_ubate.pk, alcance.programas)
        qs = personas_visibles(user)
        self.assertEqual(qs.count(), 1)


class AlcancePanelTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.sede_ubate = Sede.objects.create(codigo="UBATE", nombre="Ubaté", ciudad="Ubaté")
        self.sede_fusa = Sede.objects.create(codigo="FUSA", nombre="Fusagasugá", ciudad="Fusagasugá")
        self.facultad = Decanatura.objects.create(codigo="FAC-ING", nombre="Ingeniería")
        self.prog_ubate = Programa.objects.create(
            codigo="ISC-UB",
            nombre="Ing. Ubaté",
            sede=self.sede_ubate,
            facultad=self.facultad,
        )
        self.prog_fusa = Programa.objects.create(
            codigo="ISC-FU",
            nombre="Ing. Fusa",
            sede=self.sede_fusa,
            facultad=self.facultad,
        )
        self.vinculo, _ = TipoVinculo.objects.get_or_create(
            codigo="creador_oportunidades",
            defaults={"nombre": "Estudiante"},
        )
        Persona.objects.create(
            tipo_documento="CC",
            numero_documento="2001",
            nombres="Ana",
            apellidos="Ubaté",
            tipo_vinculo=self.vinculo,
            sede=self.sede_ubate,
            programa=self.prog_ubate,
        )
        Persona.objects.create(
            tipo_documento="CC",
            numero_documento="2002",
            nombres="Luis",
            apellidos="Fusa",
            tipo_vinculo=self.vinculo,
            sede=self.sede_fusa,
            programa=self.prog_fusa,
        )
        perm, _ = Permiso.objects.get_or_create(
            codigo="personas.administrar",
            defaults={"descripcion": "Admin personas"},
        )
        rol, _ = Rol.objects.get_or_create(
            nombre="admin_sistema", defaults={"descripcion": "Admin"}
        )
        RolPermiso.objects.get_or_create(rol=rol, permiso=perm)
        self.user = Usuario.objects.create_user(
            username="sede_user", password="pass12345", email="sede_panel@test.com"
        )
        UsuarioRol.objects.create(usuario=self.user, rol=rol)
        AlcanceUsuario.objects.create(
            usuario=self.user,
            nivel=AlcanceUsuario.NIVEL_SEDE,
            objeto_id=self.sede_ubate.pk,
        )

    def test_listado_personas_no_muestra_otra_sede(self):
        self.client.login(username="sede_user", password="pass12345")
        response = self.client.get(reverse("panel:personas_list"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Ana", content)
        self.assertNotIn("Luis", content)

    def test_detalle_persona_idor_404(self):
        persona_fusa = Persona.objects.get(numero_documento="2002")
        self.client.login(username="sede_user", password="pass12345")
        response = self.client.get(
            reverse("panel:persona_edit", kwargs={"pk": persona_fusa.pk})
        )
        self.assertEqual(response.status_code, 404)


class AlcanceEscrituraTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.sede_ubate = Sede.objects.create(codigo="UBATE", nombre="Ubaté", ciudad="Ubaté")
        self.sede_fusa = Sede.objects.create(codigo="FUSA", nombre="Fusagasugá", ciudad="Fusagasugá")
        self.facultad = Decanatura.objects.create(codigo="FAC-ING", nombre="Ingeniería")
        self.prog_fusa = Programa.objects.create(
            codigo="ISC-FU",
            nombre="Ing. Fusa",
            sede=self.sede_fusa,
            facultad=self.facultad,
        )
        self.vinculo, _ = TipoVinculo.objects.get_or_create(
            codigo="creador_oportunidades",
            defaults={"nombre": "Estudiante"},
        )
        perm, _ = Permiso.objects.get_or_create(
            codigo="personas.administrar",
            defaults={"descripcion": "Admin personas"},
        )
        rol, _ = Rol.objects.get_or_create(
            nombre="admin_sistema", defaults={"descripcion": "Admin"}
        )
        RolPermiso.objects.get_or_create(rol=rol, permiso=perm)
        self.user = Usuario.objects.create_user(
            username="sede_user_w", password="pass12345", email="sede_write@test.com"
        )
        UsuarioRol.objects.create(usuario=self.user, rol=rol)
        AlcanceUsuario.objects.create(
            usuario=self.user,
            nivel=AlcanceUsuario.NIVEL_SEDE,
            objeto_id=self.sede_ubate.pk,
        )

    def test_no_crear_persona_fuera_de_alcance(self):
        self.client.login(username="sede_user_w", password="pass12345")
        response = self.client.post(
            reverse("panel:persona_create"),
            {
                "tipo_documento": "CC",
                "numero_documento": "3001",
                "nombres": "Nuevo",
                "apellidos": "Fusa",
                "tipo_vinculo": self.vinculo.pk,
                "sede": self.sede_fusa.pk,
                "programa": self.prog_fusa.pk,
                "activo": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Persona.objects.filter(numero_documento="3001").exists())
