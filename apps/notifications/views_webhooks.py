import json
import logging

from django.conf import settings
from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from integrations.resend.signature import verify_svix_signature
from notifications.models import ResendWebhookEvent
from notifications.tasks import process_resend_webhook_event

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def resend_webhook(request):
    raw_body = request.body
    svix_id = request.headers.get("svix-id", "")
    svix_timestamp = request.headers.get("svix-timestamp", "")
    svix_signature = request.headers.get("svix-signature", "")

    ok = verify_svix_signature(
        raw_body,
        secret=settings.RESEND_WEBHOOK_SECRET,
        svix_id=svix_id,
        svix_timestamp=svix_timestamp,
        svix_signature=svix_signature,
    )
    if not ok and not settings.RESEND_MOCK_MODE:
        logger.warning("Resend webhook rejected svix_id=%s", svix_id)
        return JsonResponse({"error": "invalid signature"}, status=401)

    try:
        payload = json.loads(raw_body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid json"}, status=400)

    event_type = payload.get("type") or "unknown"
    idempotency_key = svix_id or str(payload.get("id") or "")
    if not idempotency_key:
        return JsonResponse({"error": "missing event id"}, status=400)

    try:
        event, created = ResendWebhookEvent.objects.get_or_create(
            svix_id=idempotency_key,
            defaults={"event_type": event_type, "payload": payload},
        )
    except IntegrityError:
        return JsonResponse({"status": "ok"})

    if created:
        process_resend_webhook_event.delay(str(event.id))
    return JsonResponse({"status": "ok"})
