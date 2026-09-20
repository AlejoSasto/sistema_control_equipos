from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import Usuario, Rol, Permiso, RolPermiso, UsuarioRol
from organizacion.models import (
    Area,
    Decanatura,
    Programa,
    Sede,
    ResponsableDependencia,
    UNIDAD_AREA,
    UNIDAD_PROGRAMA,
)
from personas.models import Persona, TipoVinculo
from equipos.models import Equipo, AsignacionEquipo
from equipos.services import (
    VENCIDA,
    VIGENTE,
    NO_VIGENTE,
    cerrar_asignaciones_vencidas_batch,
    crear_asignacion,
    crear_equipo_inventario,
    devolver_al_inventario,
    liberar_asignacion_vencida,
    persona_pertenece_a,
    puede_gestionar_equipo_institucional,
    unidades_de,
    vigencia_asignacion,
)


class ServiciosAsignacionTestCase(TestCase):
    def setUp(self):
        self.sede = Sede.objects.create(codigo="ASIG-UB", nombre="Sede Asig", ciudad="Ubaté")
        self.facultad = Decanatura.objects.create(codigo="FAC-ASIG", nombre="Facultad Asig")
        self.programa = Programa.objects.create(
            codigo="PROG-ASIG",
            nombre="Programa Asig",
            sede=self.sede,
            facultad=self.facultad,
            nivel="pregrado",
        )
        self.area, _ = Area.objects.get_or_create(
            codigo="AREA-ASIG", defaults={"nombre": "Área Asig"}
        )
        self.vinculo, _ = TipoVinculo.objects.get_or_create(
            codigo="gestor_conocimiento",
            defaults={"nombre": "Gestor del Conocimiento"},
        )
        self.persona = Persona.objects.create(
            tipo_documento="CC",
            numero_documento="111222333",
            nombres="Ana",
            apellidos="López",
            tipo_vinculo=self.vinculo,
            sede=self.sede,
            programa=self.programa,
        )
        self.perm, _ = Permiso.objects.get_or_create(
            codigo="equipos.asignar_institucional",
            defaults={"descripcion": "Asignar"},
        )
        self.perm_inv, _ = Permiso.objects.get_or_create(
            codigo="equipos.inventario_institucional",
            defaults={"descripcion": "Inventario"},
        )
        self.rol, _ = Rol.objects.get_or_create(
            nombre="responsable_dependencia_test",
            defaults={"descripcion": "Test responsable", "activo": True},
        )
        RolPermiso.objects.get_or_create(rol=self.rol, permiso=self.perm)
        RolPermiso.objects.get_or_create(rol=self.rol, permiso=self.perm_inv)
        self.usuario = Usuario.objects.create_user(
            username="resp1", password="testpass123!", email="resp1@test.com"
        )
        UsuarioRol.objects.create(usuario=self.usuario, rol=self.rol)
        ResponsableDependencia.objects.create(
            usuario=self.usuario,
            unidad_tipo=UNIDAD_PROGRAMA,
            unidad_id=self.programa.pk,
            activo=True,
        )

    def test_persona_pertenece_programa(self):
        self.assertTrue(persona_pertenece_a(self.persona, UNIDAD_PROGRAMA, self.programa.pk))
        self.assertFalse(persona_pertenece_a(self.persona, UNIDAD_AREA, self.area.pk))

    def test_unidades_de_responsable(self):
        unidades = unidades_de(self.usuario)
        self.assertEqual(len(unidades), 1)
        self.assertEqual(unidades[0].tipo, UNIDAD_PROGRAMA)

    def test_inventario_sin_persona_luego_asignar(self):
        equipo = crear_equipo_inventario(
            tipo=Equipo.TIPO_PORTATIL,
            marca="Lenovo",
            modelo="T14",
            serial="SRV-INV-01",
            unidad_tipo=UNIDAD_PROGRAMA,
            unidad_id=self.programa.pk,
            creado_por_usuario=self.usuario,
        )
        self.assertIsNone(equipo.persona_id)
        self.assertEqual(equipo.estado_inventario, Equipo.ESTADO_DISPONIBLE)

        hoy = timezone.localdate()
        asig = crear_asignacion(
            equipo=equipo,
            persona=self.persona,
            fecha_inicio=hoy,
            fecha_fin=hoy + timedelta(days=30),
            asignado_por_usuario=self.usuario,
        )
        equipo.refresh_from_db()
        self.assertEqual(vigencia_asignacion(asig, hoy), VIGENTE)
        self.assertEqual(equipo.estado_inventario, Equipo.ESTADO_ASIGNADO)
        self.assertEqual(equipo.persona_id, self.persona.pk)
        self.assertTrue(puede_gestionar_equipo_institucional(self.usuario, equipo))

        nueva = crear_asignacion(
            equipo=equipo,
            persona=self.persona,
            fecha_inicio=hoy,
            fecha_fin=hoy + timedelta(days=60),
            asignado_por_usuario=self.usuario,
        )
        asig.refresh_from_db()
        self.assertEqual(asig.estado, AsignacionEquipo.ESTADO_REVOCADA)
        self.assertEqual(nueva.estado, AsignacionEquipo.ESTADO_ACTIVA)

    def test_devolver_y_cierre_auto_vencida(self):
        equipo = crear_equipo_inventario(
            tipo=Equipo.TIPO_PORTATIL,
            marca="HP",
            modelo="Elite",
            serial="SRV-VIG-02",
            unidad_tipo=UNIDAD_PROGRAMA,
            unidad_id=self.programa.pk,
            creado_por_usuario=self.usuario,
        )
        hoy = timezone.localdate()
        vencida = crear_asignacion(
            equipo=equipo,
            persona=self.persona,
            fecha_inicio=hoy - timedelta(days=60),
            fecha_fin=hoy - timedelta(days=1),
            asignado_por_usuario=self.usuario,
        )
        self.assertEqual(vigencia_asignacion(vencida, hoy), VENCIDA)

        liberar_asignacion_vencida(equipo, hoy=hoy)
        equipo.refresh_from_db()
        vencida.refresh_from_db()
        self.assertEqual(vencida.estado, AsignacionEquipo.ESTADO_FINALIZADA)
        self.assertEqual(equipo.estado_inventario, Equipo.ESTADO_DISPONIBLE)
        self.assertIsNone(equipo.persona_id)

        # Reasignar y devolver manualmente
        crear_asignacion(
            equipo=equipo,
            persona=self.persona,
            fecha_inicio=hoy,
            fecha_fin=hoy + timedelta(days=10),
            asignado_por_usuario=self.usuario,
        )
        devolver_al_inventario(equipo)
        equipo.refresh_from_db()
        self.assertEqual(equipo.estado_inventario, Equipo.ESTADO_DISPONIBLE)

    def test_batch_cierra_vencidas(self):
        equipo = crear_equipo_inventario(
            tipo=Equipo.TIPO_PORTATIL,
            marca="Acer",
            modelo="A1",
            serial="SRV-BATCH-01",
            unidad_tipo=UNIDAD_PROGRAMA,
            unidad_id=self.programa.pk,
            creado_por_usuario=self.usuario,
        )
        hoy = timezone.localdate()
        crear_asignacion(
            equipo=equipo,
            persona=self.persona,
            fecha_inicio=hoy - timedelta(days=10),
            fecha_fin=hoy - timedelta(days=1),
            asignado_por_usuario=self.usuario,
        )
        n = cerrar_asignaciones_vencidas_batch(hoy=hoy)
        self.assertEqual(n, 1)
        equipo.refresh_from_db()
        self.assertEqual(equipo.estado_inventario, Equipo.ESTADO_DISPONIBLE)

    def test_vigencia_futura(self):
        equipo = crear_equipo_inventario(
            tipo=Equipo.TIPO_PORTATIL,
            marca="Asus",
            modelo="X",
            serial="SRV-FUT-01",
            unidad_tipo=UNIDAD_PROGRAMA,
            unidad_id=self.programa.pk,
            creado_por_usuario=self.usuario,
        )
        hoy = timezone.localdate()
        futura = crear_asignacion(
            equipo=equipo,
            persona=self.persona,
            fecha_inicio=hoy + timedelta(days=5),
            fecha_fin=hoy + timedelta(days=40),
            asignado_por_usuario=self.usuario,
        )
        self.assertEqual(vigencia_asignacion(futura, hoy), NO_VIGENTE)
