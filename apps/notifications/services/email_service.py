import logging

from django.conf import settings
from django.template.loader import render_to_string

from notifications.models import EmailLog

logger = logging.getLogger(__name__)


class EmailService:
    @classmethod
    def _enqueue(cls, *, email_type, recipient, subject, template_name, context):
        if not recipient:
            logger.warning("Email skip type=%s: empty recipient", email_type)
            return None
        html = render_to_string(template_name, context)
        text = render_to_string(template_name.replace(".html", ".txt"), context)
        log = EmailLog.objects.create(
            email_type=email_type,
            recipient=recipient,
            status=EmailLog.Status.QUEUED,
        )
        from notifications.tasks import send_email_task

        args = (str(log.id), recipient, subject, html, text)
        # MVP / Render sin worker: envío síncrono en el request web.
        if not settings.EMAIL_USE_CELERY or settings.CELERY_TASK_ALWAYS_EAGER:
            send_email_task.apply(args=args)
            return log
        try:
            send_email_task.apply_async(args=args, queue="emails")
        except Exception:
            logger.exception(
                "Celery enqueue failed type=%s log_id=%s; sending inline",
                email_type,
                log.id,
            )
            send_email_task.apply(args=args)
        return log

    @classmethod
    def send_welcome(cls, user):
        name = user.get_full_name() or user.username
        return cls._enqueue(
            email_type="welcome",
            recipient=user.email,
            subject=f"Bienvenido — {settings.RESEND_FROM_NAME}",
            template_name="emails/welcome.html",
            context={
                "user_name": name,
                "login_url": f"{settings.PUBLIC_BASE_URL}/accounts/login/",
                "app_name": settings.RESEND_FROM_NAME,
            },
        )

    @classmethod
    def send_password_reset(cls, user, raw_token: str):
        name = user.get_full_name() or user.username
        reset_url = (
            f"{settings.PUBLIC_BASE_URL}/accounts/password-reset/confirmar/"
            f"?token={raw_token}"
        )
        return cls._enqueue(
            email_type="password_reset",
            recipient=user.email,
            subject=f"Restablecer contraseña — {settings.RESEND_FROM_NAME}",
            template_name="emails/password_reset.html",
            context={
                "user_name": name,
                "reset_url": reset_url,
                "app_name": settings.RESEND_FROM_NAME,
            },
        )

    @classmethod
    def send_account_unlocked(cls, user):
        name = user.get_full_name() or user.username
        return cls._enqueue(
            email_type="account_unlocked",
            recipient=user.email,
            subject=f"Cuenta desbloqueada — {settings.RESEND_FROM_NAME}",
            template_name="emails/account_unlocked.html",
            context={
                "user_name": name,
                "login_url": f"{settings.PUBLIC_BASE_URL}/accounts/login/",
                "app_name": settings.RESEND_FROM_NAME,
            },
        )
