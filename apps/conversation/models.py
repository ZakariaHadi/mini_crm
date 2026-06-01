from django.db import models

from apps.common.models import TimeStampedModel


class Conversation(TimeStampedModel):
    """Persisted record of a completed chatbot conversation."""

    business = models.ForeignKey(
        "main_crm.Business",
        on_delete=models.CASCADE,
        related_name="conversations",
        verbose_name="Business",
    )
    user_phone = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="User Phone Number",
    )
    data = models.JSONField(
        default=dict,
        verbose_name="Collected Data",
        help_text="All data collected during the conversation.",
    )
    completed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Completed At",
    )

    class Meta(TimeStampedModel.Meta):
        verbose_name = "conversation"
        verbose_name_plural = "conversations"
        indexes = [
            models.Index(fields=["business", "user_phone"]),
            models.Index(fields=["completed_at"]),
        ]

    def __str__(self) -> str:
        return f"Conversation {self.pk} — {self.user_phone}"
