import logging

from django.conf import settings

from integrations.resend.errors import classify_resend_error
from integrations.resend.ports import SendEmailResult

logger = logging.getLogger(__name__)


class ResendHttpClient:
    def send_email(
        self,
        *,
        to: str,
        subject: str,
        html: str,
        text: str,
        from_email: str,
        from_name: str,
    ) -> SendEmailResult:
        import resend

        resend.api_key = settings.RESEND_API_KEY
        from_header = f"{from_name} <{from_email}>" if from_name else from_email
        try:
            response = resend.Emails.send(
                {
                    "from": from_header,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                    "text": text,
                }
            )
        except Exception as exc:
            raise classify_resend_error(exc) from exc

        email_id = ""
        raw = None
        if isinstance(response, dict):
            raw = response
            email_id = str(response.get("id") or "")
        else:
            email_id = str(getattr(response, "id", "") or "")
            raw = {"id": email_id}
        logger.info("Resend sent id=%s to=%s", email_id, to)
        return SendEmailResult(id=email_id, raw=raw)
