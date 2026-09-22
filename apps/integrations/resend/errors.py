class ResendError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ResendTransientError(ResendError):
    """5xx, 429, timeout → Celery retry."""


class ResendPermanentError(ResendError):
    """400/401/403/422 → FAILED sin retry."""


def classify_resend_error(exc: Exception) -> ResendError:
    status = getattr(exc, "status_code", None)
    msg = str(exc) or "Resend request failed"
    if status in (408, 429) or (status and status >= 500):
        return ResendTransientError(msg, status_code=status)
    if status in (400, 401, 403, 404, 422):
        return ResendPermanentError(msg, status_code=status)
    lowered = msg.lower()
    if any(t in lowered for t in ("timeout", "connection", "rate limit")):
        return ResendTransientError(msg, status_code=status)
    return ResendTransientError(msg, status_code=status)
