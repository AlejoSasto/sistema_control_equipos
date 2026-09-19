from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError

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
        self.area, _ = Area.objects.get_or_create(codigo="CGCA", defaults={"nombre": "Biblioteca"})
        self.vinculo_docente, _ = TipoVinculo.objects.get_or_create(codigo="docente", defaults={"nombre": "Docente"})
        self.persona = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="1234567890",
            nombres="Carlos",
            apellidos="Martínez",
            tipo_vinculo=self.vinculo_docente,
            sede=self.sede,
            programa=self.programa,
        )

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

        # Verificar generación de QR al vuelo en Base64
        qr_data = equipo.generar_qr_base64()
        self.assertTrue(qr_data.startswith("data:image/png;base64,"))

        # Verificar endpoint de renderizado de imagen PNG
        response = self.client.get(
            reverse("equipos:render_qr_image", kwargs={"token_qr": equipo.token_qr})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")

    def test_equipo_institucional_requiere_dependencia(self):
        equipo = Equipo(
            persona=self.persona,
            tipo=Equipo.TIPO_PORTATIL,
            marca="Dell",
            modelo="Latitude",
            serial="INST-NO-DEP",
            propiedad=Equipo.PROPIEDAD_INSTITUCIONAL,
        )
        with self.assertRaises(ValidationError):
            equipo.save()

    def test_equipo_institucional_con_dependencia(self):
        equipo = Equipo.objects.create(
            persona=self.persona,
            tipo=Equipo.TIPO_PORTATIL,
            marca="Dell",
            modelo="Latitude",
            serial="INST-CON-DEP",
            propiedad=Equipo.PROPIEDAD_INSTITUCIONAL,
            dependencia=self.area,
        )
        self.assertEqual(equipo.dependencia.codigo, "CGCA")
