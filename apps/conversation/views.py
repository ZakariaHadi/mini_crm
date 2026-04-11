from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Conversation
from .serializers import ConversationSerializer


class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Conversation]:
        return Conversation.objects.filter(
            business__owner=self.request.user
        ).select_related("business")
