"""Backend de autenticación: username, correo o documento (cédula)."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from accounts.auth_utils import resolver_usuario_por_identificador


class DocumentoOUsuarioBackend(ModelBackend):
    """Autentica con username, email o Persona.numero_documento."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(get_user_model().USERNAME_FIELD)
        if username is None or password is None:
            return None

        user = resolver_usuario_por_identificador(username)
        if user is None:
            # Misma ruta de fallos que ModelBackend (evita revelar existencia)
            Usuario = get_user_model()
            Usuario().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
