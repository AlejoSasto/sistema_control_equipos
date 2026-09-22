import base64
import hashlib
import hmac
import json
import time
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from notifications.models import EmailLog, EmailToken, ResendWebhookEvent
from notifications.services.email_service import EmailService
from notifications.services.token_service import consume_email_token, create_email_token
from notifications.tasks import process_resend_webhook_event, send_email_task

Usuario = get_user_model()


def _svix_headers(payload: bytes, secret: str, svix_id: str = "msg_test_1"):
    ts = str(int(time.time()))
    key = base64.b64decode(secret[len("whsec_") :] + "=" * (-len(secret[len("whsec_") :]) % 4))
    signed = f"{svix_id}.{ts}.".encode() + payload
    sig = base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()
    return {
        "HTTP_SVIX_ID": svix_id,
        "HTTP_SVIX_TIMESTAMP": ts,
        "HTTP_SVIX_SIGNATURE": f"v1,{sig}",
    }


@override_settings(
    RESEND_MOCK_MODE=True,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    PUBLIC_BASE_URL="http://testserver",
    EMAIL_TOKEN_SECRET="test-email-token-secret",
)
class EmailMockModeTests(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(
            username="correo_user",
            email="correo@ucundinamarca.edu.co",
            password="TestPass123!",
            first_name="Ana",
            last_name="Prueba",
        )

    def test_welcome_enqueue_and_sent_mock(self):
        log = EmailService.send_welcome(self.user)
        log.refresh_from_db()
        self.assertEqual(log.email_type, "welcome")
        self.assertEqual(log.recipient, self.user.email)
        self.assertEqual(log.status, EmailLog.Status.SENT)
        self.assertTrue(log.resend_id.startswith("mock_"))


@override_settings(
    RESEND_MOCK_MODE=False,
    RESEND_WEBHOOK_SECRET="whsec_dGVzdF9zZWNyZXRfd2ViaG9va19rZXkxMjM",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class ResendWebhookTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.secret = "whsec_dGVzdF9zZWNyZXRfd2ViaG9va19rZXkxMjM"
        self.log = EmailLog.objects.create(
            email_type="welcome",
            recipient="a@example.com",
            status=EmailLog.Status.SENT,
            resend_id="re_abc123",
        )

    def test_webhook_invalid_signature_401(self):
        body = json.dumps(
            {"type": "email.delivered", "data": {"email_id": "re_abc123"}}
        ).encode()
        resp = self.client.post(
            "/webhooks/resend/",
            data=body,
            content_type="application/json",
            HTTP_SVIX_ID="msg_bad",
            HTTP_SVIX_TIMESTAMP=str(int(time.time())),
            HTTP_SVIX_SIGNATURE="v1,invalid",
        )
        self.assertEqual(resp.status_code, 401)

    def test_webhook_valid_and_idempotent(self):
        body = json.dumps(
            {
                "type": "email.delivered",
                "data": {"email_id": "re_abc123"},
            }
        ).encode()
        headers = _svix_headers(body, self.secret, svix_id="msg_ok_1")
        resp = self.client.post(
            "/webhooks/resend/",
            data=body,
            content_type="application/json",
            **headers,
        )
        self.assertEqual(resp.status_code, 200)
        self.log.refresh_from_db()
        self.assertEqual(self.log.status, EmailLog.Status.DELIVERED)
        self.assertEqual(ResendWebhookEvent.objects.filter(svix_id="msg_ok_1").count(), 1)

        resp2 = self.client.post(
            "/webhooks/resend/",
            data=body,
            content_type="application/json",
            **headers,
        )
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(ResendWebhookEvent.objects.filter(svix_id="msg_ok_1").count(), 1)


@override_settings(
    EMAIL_TOKEN_SECRET="test-email-token-secret",
    RESEND_MOCK_MODE=True,
    CELERY_TASK_ALWAYS_EAGER=True,
    PUBLIC_BASE_URL="http://testserver",
)
class PasswordResetTokenTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Usuario.objects.create_user(
            username="reset_user",
            email="reset@ucundinamarca.edu.co",
            password="OldPass123!",
            first_name="Luis",
            last_name="Reset",
        )

    def test_token_valid_consumes_and_sets_password(self):
        _, raw = create_email_token(
            self.user, EmailToken.Purpose.PASSWORD_RESET, hours=2
        )
        resp = self.client.post(
            reverse("accounts:password_reset_confirm"),
            {
                "token": raw,
                "password": "NewPass123!",
                "password_confirm": "NewPass123!",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass123!"))
        self.assertIsNone(
            consume_email_token(raw, EmailToken.Purpose.PASSWORD_RESET)
        )

    def test_token_invalid(self):
        resp = self.client.post(
            reverse("accounts:password_reset_confirm"),
            {
                "token": "token-inexistente",
                "password": "NewPass123!",
                "password_confirm": "NewPass123!",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldPass123!"))

    def test_token_expired(self):
        token, raw = create_email_token(
            self.user, EmailToken.Purpose.PASSWORD_RESET, hours=2
        )
        EmailToken.objects.filter(pk=token.pk).update(
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        resp = self.client.post(
            reverse("accounts:password_reset_confirm"),
            {
                "token": raw,
                "password": "NewPass123!",
                "password_confirm": "NewPass123!",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldPass123!"))
