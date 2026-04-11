from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import OutgoingMessage
from .serializers import OutgoingMessageSerializer


class OutgoingMessageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OutgoingMessageSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "phone"]

    def get_queryset(self) -> QuerySet[OutgoingMessage]:
        return OutgoingMessage.objects.all()
