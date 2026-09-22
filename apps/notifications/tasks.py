import logging

from celery import shared_task
from django.utils import timezone

from integrations.resend.adapter import ResendAdapter
from integrations.resend.errors import ResendPermanentError, ResendTransientError
from notifications.models import EmailLog, ResendWebhookEvent

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=5, queue="emails")
def send_email_task(self, log_id: str, recipient: str, subject: str, html: str, text: str):
    try:
        log = EmailLog.objects.get(id=log_id)
    except EmailLog.DoesNotExist:
        return
    try:
        result = ResendAdapter().send_email(
            to=recipient, subject=subject, html=html, text=text
        )
        log.status = EmailLog.Status.SENT
        log.resend_id = result.id
        log.error_message = ""
        log.save(update_fields=["status", "resend_id", "error_message"])
    except ResendTransientError as exc:
        log.error_message = str(exc)
        log.save(update_fields=["error_message"])
        raise self.retry(exc=exc, countdown=2 ** self.request.retries) from exc
    except ResendPermanentError as exc:
        log.status = EmailLog.Status.FAILED
        log.error_message = str(exc)
        log.save(update_fields=["status", "error_message"])
    except Exception as exc:
        logger.exception("Unexpected email send error log_id=%s", log_id)
        log.error_message = str(exc)
        log.save(update_fields=["error_message"])
        raise self.retry(exc=exc, countdown=2 ** self.request.retries) from exc


@shared_task(bind=True, max_retries=3, queue="emails")
def process_resend_webhook_event(self, event_id: str):
    try:
        event = ResendWebhookEvent.objects.get(id=event_id)
    except ResendWebhookEvent.DoesNotExist:
        return
    payload = event.payload or {}
    event_type = payload.get("type") or event.event_type
    data = payload.get("data") or {}
    resend_id = str(data.get("email_id") or data.get("id") or "")

    if event_type == "email.delivered" and resend_id:
        EmailLog.objects.filter(resend_id=resend_id).update(
            status=EmailLog.Status.DELIVERED
        )
    elif event_type == "email.bounced" and resend_id:
        EmailLog.objects.filter(resend_id=resend_id).update(
            status=EmailLog.Status.BOUNCED
        )
    elif event_type == "email.complained" and resend_id:
        EmailLog.objects.filter(resend_id=resend_id).update(
            status=EmailLog.Status.COMPLAINED
        )

    event.processed_at = timezone.now()
    event.save(update_fields=["processed_at"])
