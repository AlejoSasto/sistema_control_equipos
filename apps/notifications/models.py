import uuid

from django.conf import settings
from django.db import models


class EmailLog(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "En cola"
        SENT = "sent", "Enviado"
        FAILED = "failed", "Fallido"
        DELIVERED = "delivered", "Entregado"
        BOUNCED = "bounced", "Rebotado"
        COMPLAINED = "complained", "Queja"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email_type = models.CharField(max_length=50)
    recipient = models.EmailField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.QUEUED
    )
    resend_id = models.CharField(max_length=100, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "email_log"
        indexes = [
            models.Index(fields=["resend_id"]),
            models.Index(fields=["recipient", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email_type} → {self.recipient} ({self.status})"


class ResendWebhookEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    svix_id = models.CharField(max_length=100, unique=True)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "resend_webhook_event"
        ordering = ["-created_at"]


class EmailToken(models.Model):
    class Purpose(models.TextChoices):
        EMAIL_CONFIRMATION = "email_confirmation", "Confirmación de correo"
        PASSWORD_RESET = "password_reset", "Restablecer contraseña"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_tokens",
    )
    purpose = models.CharField(max_length=30, choices=Purpose.choices)
    token_hash = models.CharField(max_length=64, db_index=True)
    email_sent_to = models.EmailField()
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "email_token"
        indexes = [
            models.Index(fields=["purpose", "token_hash"]),
        ]
