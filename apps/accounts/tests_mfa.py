from django.test import TestCase, Client
from django.urls import reverse
from django_otp.plugins.otp_totp.models import TOTPDevice

from accounts.models import Usuario, Rol, Permiso, RolPermiso, UsuarioRol
from accounts.views import SESSION_MFA_USER_ID


class MfaAdminTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.rol_admin, _ = Rol.objects.get_or_create(
            nombre="admin_sistema", defaults={"descripcion": "Admin"}
        )
        self.perm, _ = Permiso.objects.get_or_create(
            codigo="usuarios.administrar", defaults={"descripcion": "Usuarios"}
        )
        RolPermiso.objects.get_or_create(rol=self.rol_admin, permiso=self.perm)
        self.admin = Usuario.objects.create_user(
            username="admin_mfa", password="AdminPass123!", email="admin_mfa@test.com"
        )
        UsuarioRol.objects.create(usuario=self.admin, rol=self.rol_admin)

        self.rol_miembro, _ = Rol.objects.get_or_create(
            nombre="miembro_comunidad", defaults={"descripcion": "Miembro"}
        )
        self.perm_perfil, _ = Permiso.objects.get_or_create(
            codigo="perfil.ver_propio", defaults={"descripcion": "Perfil"}
        )
        RolPermiso.objects.get_or_create(rol=self.rol_miembro, permiso=self.perm_perfil)
        self.miembro = Usuario.objects.create_user(
            username="miembro_mfa", password="MiembroPass123!", email="miembro_mfa@test.com"
        )
        UsuarioRol.objects.create(usuario=self.miembro, rol=self.rol_miembro)

    def test_admin_sin_mfa_redirige_a_setup(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "admin_mfa", "password": "AdminPass123!"},
        )
        self.assertRedirects(response, reverse("accounts:mfa_setup"))
        self.assertEqual(self.client.session.get(SESSION_MFA_USER_ID), self.admin.pk)
        # Aún no hay sesión autenticada completa
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_miembro_no_requiere_mfa(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "miembro_mfa", "password": "MiembroPass123!"},
            follow=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("mfa", response.url)
        self.assertIn("_auth_user_id", self.client.session)

    def test_admin_con_mfa_redirige_a_verify(self):
        TOTPDevice.objects.create(user=self.admin, name="default", confirmed=True)
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "admin_mfa", "password": "AdminPass123!"},
        )
        self.assertRedirects(response, reverse("accounts:mfa_verify"))
        self.assertEqual(self.client.session.get(SESSION_MFA_USER_ID), self.admin.pk)
