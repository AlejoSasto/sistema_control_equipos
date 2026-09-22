from dataclasses import dataclass
from typing import Protocol


@dataclass
class SendEmailResult:
    id: str
    raw: dict | None = None


class ResendPort(Protocol):
    def send_email(
        self,
        *,
        to: str,
        subject: str,
        html: str,
        text: str,
        from_email: str,
        from_name: str,
    ) -> SendEmailResult: ...
