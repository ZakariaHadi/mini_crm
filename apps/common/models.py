import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base providing created/updated timestamps on every model."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class UUIDModel(models.Model):
    """Abstract base using UUID as primary key — hides sequential IDs from API."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
