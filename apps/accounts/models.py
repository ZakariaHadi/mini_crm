from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class Business(TimeStampedModel):
    name = models.CharField(max_length=255, verbose_name="Business Name")
    whatsapp_phone_number_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="WhatsApp Phone Number ID",
        help_text="Meta Business phone number ID.",
    )
    whatsapp_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="WhatsApp Display Number",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="businesses",
        verbose_name="Owner",
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")

    class Meta(TimeStampedModel.Meta):
        verbose_name = "business"
        verbose_name_plural = "businesses"
        indexes = [
            models.Index(fields=["whatsapp_number"]),
        ]

    def __str__(self) -> str:
        return self.name
