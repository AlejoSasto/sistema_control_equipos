import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from notifications.models import EmailToken


def _hash_token(raw: str) -> str:
    key = (settings.EMAIL_TOKEN_SECRET or settings.SECRET_KEY).encode()
    return hmac.new(key, raw.encode(), hashlib.sha256).hexdigest()


def create_email_token(user, purpose: str, *, hours: int = 24) -> tuple[EmailToken, str]:
    raw = secrets.token_urlsafe(32)
    token = EmailToken.objects.create(
        user=user,
        purpose=purpose,
        token_hash=_hash_token(raw),
        email_sent_to=user.email,
        expires_at=timezone.now() + timedelta(hours=hours),
    )
    return token, raw


def consume_email_token(raw: str, purpose: str) -> EmailToken | None:
    if not raw:
        return None
    token = (
        EmailToken.objects.filter(
            purpose=purpose,
            token_hash=_hash_token(raw),
            used_at__isnull=True,
        )
        .select_related("user")
        .first()
    )
    if not token:
        return None
    if token.expires_at < timezone.now():
        return None
    token.used_at = timezone.now()
    token.save(update_fields=["used_at"])
    return token
