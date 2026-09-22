import base64
import hashlib
import hmac
import time


def _decode_svix_secret(secret: str) -> bytes:
    value = secret.strip()
    if value.startswith("whsec_"):
        value = value[len("whsec_") :]
    padding = "=" * (-len(value) % 4)
    return base64.b64decode(value + padding)


def verify_svix_signature(
    payload: bytes,
    *,
    secret: str,
    svix_id: str,
    svix_timestamp: str,
    svix_signature: str,
    tolerance_seconds: int = 300,
) -> bool:
    if not secret or not svix_id or not svix_timestamp or not svix_signature:
        return False
    try:
        ts = int(svix_timestamp)
    except (TypeError, ValueError):
        return False
    if abs(int(time.time()) - ts) > tolerance_seconds:
        return False
    try:
        key = _decode_svix_secret(secret)
    except (ValueError, TypeError):
        return False
    signed = f"{svix_id}.{svix_timestamp}.".encode() + payload
    expected_b64 = base64.b64encode(
        hmac.new(key, signed, hashlib.sha256).digest()
    ).decode()
    for part in svix_signature.split():
        if part.startswith("v1,") and hmac.compare_digest(part[3:], expected_b64):
            return True
    return False
