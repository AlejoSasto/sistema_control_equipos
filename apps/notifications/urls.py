from django.urls import path

from notifications.views_webhooks import resend_webhook

urlpatterns = [
    path("resend/", resend_webhook, name="webhook-resend"),
]
