import uuid
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Usuario, Rol, Permiso, RolPermiso, UsuarioRol
from organizacion.models import Sede, Decanatura, Programa
from personas.models import Persona, TipoVinculo
from equipos.models import Equipo
from control_acceso.models import Movimiento


class ControlSalidaTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.sede = Sede.objects.create(codigo="UBATE", nombre="Seccional Ubaté", ciudad="Ubaté")

        # Tipos de Vínculo (códigos canónicos)
        self.vinculo_docente, _ = TipoVinculo.objects.get_or_create(
            codigo="gestor_conocimiento", defaults={"nombre": "Gestor del Conocimiento"}
        )
        self.vinculo_graduado, _ = TipoVinculo.objects.get_or_create(
            codigo="egresado", defaults={"nombre": "Egresado"}
        )

        # Permisos y Rol Celador (pueden existir por migraciones de catálogo)
        self.perm_escanear, _ = Permiso.objects.get_or_create(
            codigo="control.escanear",
            defaults={"descripcion": "Acceder a la pantalla de control de salida"},
        )
        self.perm_alertas, _ = Permiso.objects.get_or_create(
            codigo="control.ver_alertas",
            defaults={"descripcion": "Ver histórico de alertas"},
        )
        self.rol_celador, _ = Rol.objects.get_or_create(
            nombre="celador", defaults={"descripcion": "Celador de Portería"}
        )
        RolPermiso.objects.get_or_create(rol=self.rol_celador, permiso=self.perm_escanear)
        RolPermiso.objects.get_or_create(rol=self.rol_celador, permiso=self.perm_alertas)

        # Usuario Celador
        self.celador = Usuario.objects.create_user(
            username="celador_test",
            password="testpassword123",
        )
        UsuarioRol.objects.create(usuario=self.celador, rol=self.rol_celador)

        # Persona Activa
        self.persona_activa = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="1070123456",
            nombres="Juan Camilo",
            apellidos="Rodríguez",
            tipo_vinculo=self.vinculo_docente,
            sede=self.sede,
            activo=True,
        )

        # Persona Inactiva (Regla 7)
        self.persona_inactiva = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="1070999999",
            nombres="Pedro",
            apellidos="Desvinculado",
            tipo_vinculo=self.vinculo_graduado,
            sede=self.sede,
            activo=False,
        )

        # Equipo Activo Autorizado
        self.equipo_ok = Equipo.objects.create(
            persona=self.persona_activa,
            tipo=Equipo.TIPO_PORTATIL,
            marca="Lenovo",
            modelo="ThinkPad T14",
            serial="LNV-OK-TEST-01",
            propiedad=Equipo.PROPIEDAD_PERSONAL,
            activo=True,
        )

        # Equipo Inactivo / Dado de baja (Regla 6)
        self.equipo_baja = Equipo.objects.create(
            persona=self.persona_activa,
            tipo=Equipo.TIPO_PORTATIL,
            marca="HP",
            modelo="EliteBook",
            serial="HP-BAJA-TEST-02",
            propiedad=Equipo.PROPIEDAD_PERSONAL,
            activo=False,
        )

        # Equipo con Persona Inactiva (Regla 7)
        self.equipo_persona_inactiva = Equipo.objects.create(
            persona=self.persona_inactiva,
            tipo=Equipo.TIPO_PORTATIL,
            marca="Dell",
            modelo="Latitude",
            serial="DELL-INACT-TEST-03",
            propiedad=Equipo.PROPIEDAD_PERSONAL,
            activo=True,
        )

    def test_salida_autorizada_ok(self):
        """Prueba salida normal: persona activa y equipo activo -> resultado 'ok'."""
        self.client.login(username="celador_test", password="testpassword123")
        response = self.client.post(
            reverse("control_acceso:verificar_codigo"),
            {"codigo": str(self.equipo_ok.token_qr)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "COINCIDE")
        self.assertContains(response, "Juan Camilo Rodríguez")
        self.assertContains(response, "LNV-OK-TEST-01")

        # Regla 5: Cada escaneo genera registro en Movimiento
        mov = Movimiento.objects.filter(equipo=self.equipo_ok).first()
        self.assertIsNotNone(mov)
        self.assertEqual(mov.resultado, Movimiento.RESULTADO_OK)
        self.assertEqual(mov.usuario_control, self.celador)

    def test_salida_alerta_equipo_inactivo(self):
        """Regla 6: Equipo dado de baja (activo=False) -> resultado 'alerta'."""
        self.client.login(username="celador_test", password="testpassword123")
        response = self.client.post(
            reverse("control_acceso:verificar_codigo"),
            {"codigo": str(self.equipo_baja.token_qr)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SALIDA NO AUTORIZADA")
        self.assertContains(response, "Equipo dado de baja o inactivo")

        mov = Movimiento.objects.filter(equipo=self.equipo_baja).first()
        self.assertIsNotNone(mov)
        self.assertEqual(mov.resultado, Movimiento.RESULTADO_ALERTA)

    def test_salida_alerta_persona_inactiva(self):
        """Regla 7: Persona inactiva -> resultado 'alerta'."""
        self.client.login(username="celador_test", password="testpassword123")
        response = self.client.post(
            reverse("control_acceso:verificar_codigo"),
            {"codigo": str(self.equipo_persona_inactiva.token_qr)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SALIDA NO AUTORIZADA")
        self.assertContains(response, "Persona inactiva")

        mov = Movimiento.objects.filter(equipo=self.equipo_persona_inactiva).first()
        self.assertIsNotNone(mov)
        self.assertEqual(mov.resultado, Movimiento.RESULTADO_ALERTA)

    def test_codigo_no_encontrado(self):
        """Código inexistente -> resultado 'no_encontrado' registrado en auditoría."""
        token_falso = str(uuid.uuid4())
        self.client.login(username="celador_test", password="testpassword123")
        response = self.client.post(
            reverse("control_acceso:verificar_codigo"),
            {"codigo": token_falso},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CÓDIGO NO REGISTRADO")

        mov = Movimiento.objects.filter(token_escaneado=token_falso).first()
        self.assertIsNotNone(mov)
        self.assertEqual(mov.resultado, Movimiento.RESULTADO_NO_ENCONTRADO)

    def test_salida_ok_uuid_con_apostrofos_layout_teclado(self):
        """Zebra DS22 US→ES: guiones del UUID llegan como apóstrofos -> ok."""
        self.client.login(username="celador_test", password="testpassword123")
        codigo_pistola = str(self.equipo_ok.token_qr).replace("-", "'")
        response = self.client.post(
            reverse("control_acceso:verificar_codigo"),
            {"codigo": codigo_pistola},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "COINCIDE")
        self.assertContains(response, "LNV-OK-TEST-01")

        mov = Movimiento.objects.filter(equipo=self.equipo_ok).first()
        self.assertIsNotNone(mov)
        self.assertEqual(mov.resultado, Movimiento.RESULTADO_OK)

    def test_salida_ok_uuid_hex_sin_separadores(self):
        """UUID de 32 hex sin guiones -> ok."""
        self.client.login(username="celador_test", password="testpassword123")
        codigo_hex = self.equipo_ok.token_qr.hex
        response = self.client.post(
            reverse("control_acceso:verificar_codigo"),
            {"codigo": codigo_hex},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "COINCIDE")
        self.assertContains(response, "LNV-OK-TEST-01")

        mov = Movimiento.objects.filter(equipo=self.equipo_ok).first()
        self.assertIsNotNone(mov)
        self.assertEqual(mov.resultado, Movimiento.RESULTADO_OK)

    def test_salida_ok_por_serial(self):
        """Fallback por serial físico intacto (demos / ingreso manual)."""
        self.client.login(username="celador_test", password="testpassword123")
        response = self.client.post(
            reverse("control_acceso:verificar_codigo"),
            {"codigo": "LNV-OK-TEST-01"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "COINCIDE")
        self.assertContains(response, "Juan Camilo Rodríguez")

        mov = Movimiento.objects.filter(equipo=self.equipo_ok).first()
        self.assertIsNotNone(mov)
        self.assertEqual(mov.resultado, Movimiento.RESULTADO_OK)

    def test_salida_ok_con_token_exhibicion_firmado(self):
        """QR con token de exhibición firmado (TTL) -> ok."""
        self.client.login(username="celador_test", password="testpassword123")
        token = self.equipo_ok.generar_token_exhibicion()
        response = self.client.post(
            reverse("control_acceso:verificar_codigo"),
            {"codigo": token},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "COINCIDE")
        mov = Movimiento.objects.filter(equipo=self.equipo_ok).first()
        self.assertIsNotNone(mov)
        self.assertEqual(mov.resultado, Movimiento.RESULTADO_OK)

    def test_salida_ok_token_firmado_zebra_apostrofos_y_ene(self):
        """Zebra US→ES: token firmado con '-'→\"'\" y ':'→'ñ' -> ok."""
        self.client.login(username="celador_test", password="testpassword123")
        token = self.equipo_ok.generar_token_exhibicion()
        codigo_pistola = token.replace("-", "'").replace(":", "ñ")
        response = self.client.post(
            reverse("control_acceso:verificar_codigo"),
            {"codigo": codigo_pistola},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "COINCIDE")
        self.assertContains(response, "LNV-OK-TEST-01")

        mov = Movimiento.objects.filter(equipo=self.equipo_ok).first()
        self.assertIsNotNone(mov)
        self.assertEqual(mov.resultado, Movimiento.RESULTADO_OK)

    def test_salida_ok_token_firmado_zebra_uuid_mayusculas_y_ene(self):
        """Zebra: UUID en mayúsculas + ':'→'ñ' en token firmado -> ok."""
        self.client.login(username="celador_test", password="testpassword123")
        token = self.equipo_ok.generar_token_exhibicion()
        uuid_part, resto = token.split(":", 1)
        codigo_pistola = f"{uuid_part.upper()}ñ{resto.replace(':', 'ñ')}"
        response = self.client.post(
            reverse("control_acceso:verificar_codigo"),
            {"codigo": codigo_pistola},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "COINCIDE")
        self.assertContains(response, "LNV-OK-TEST-01")

        mov = Movimiento.objects.filter(equipo=self.equipo_ok).first()
        self.assertIsNotNone(mov)
        self.assertEqual(mov.resultado, Movimiento.RESULTADO_OK)

    def test_salida_ok_token_firmado_firma_corrupta_fallback_uuid(self):
        """Pistola corrompe la firma (BadSignature) pero el UUID del segmento -> ok."""
        self.client.login(username="celador_test", password="testpassword123")
        token = self.equipo_ok.generar_token_exhibicion()
        uuid_part = token.split(":", 1)[0]
        codigo_pistola = f"{uuid_part}:1X85jy:koe7rvxdR0Kbu0rHlF3jFR7aRrbEZzNUTR8SPQiIu4y"
        response = self.client.post(
            reverse("control_acceso:verificar_codigo"),
            {"codigo": codigo_pistola},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "COINCIDE")
        self.assertContains(response, "LNV-OK-TEST-01")

        mov = Movimiento.objects.filter(equipo=self.equipo_ok).first()
        self.assertIsNotNone(mov)
        self.assertEqual(mov.resultado, Movimiento.RESULTADO_OK)
