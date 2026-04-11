from django.db import models

from apps.common.models import TimeStampedModel


class OutgoingMessage(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    phone = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="Recipient Phone",
    )
    content = models.JSONField(verbose_name="Message Content")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="Delivery Status",
    )
    retry_count = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Retry Count",
    )
    provider_message_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Provider Message ID",
    )
    error_detail = models.TextField(
        blank=True,
        default="",
        verbose_name="Error Detail",
    )

    class Meta(TimeStampedModel.Meta):
        verbose_name = "outgoing message"
        verbose_name_plural = "outgoing messages"
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Message to {self.phone} [{self.status}]"
