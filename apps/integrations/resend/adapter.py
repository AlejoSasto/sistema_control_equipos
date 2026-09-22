from django.conf import settings

from integrations.resend.client import ResendHttpClient
from integrations.resend.mock_client import ResendMockClient


class ResendAdapter:
    def __init__(self, client=None):
        if client is not None:
            self.client = client
        elif settings.RESEND_MOCK_MODE:
            self.client = ResendMockClient()
        else:
            self.client = ResendHttpClient()

    def send_email(
        self,
        *,
        to: str,
        subject: str,
        html: str,
        text: str,
        from_email: str | None = None,
        from_name: str | None = None,
    ):
        return self.client.send_email(
            to=to,
            subject=subject,
            html=html,
            text=text,
            from_email=from_email or settings.RESEND_FROM_EMAIL,
            from_name=from_name or settings.RESEND_FROM_NAME,
        )
