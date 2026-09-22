import logging
import uuid

from integrations.resend.ports import SendEmailResult

logger = logging.getLogger(__name__)


class ResendMockClient:
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
        email_id = f"mock_{uuid.uuid4().hex[:12]}"
        logger.info("MOCK email id=%s to=%s subject=%s", email_id, to, subject)
        return SendEmailResult(
            id=email_id,
            raw={"id": email_id, "mock": True, "to": to, "subject": subject},
        )
