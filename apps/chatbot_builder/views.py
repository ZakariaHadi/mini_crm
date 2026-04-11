from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Chatbot, Node, Option
from .serializers import (
    ChatbotListSerializer,
    ChatbotSerializer,
    NodeSerializer,
    NodeWriteSerializer,
    OptionSerializer,
)


class ChatbotViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self) -> type:
        if self.action == "list":
            return ChatbotListSerializer
        return ChatbotSerializer

    def get_queryset(self) -> QuerySet[Chatbot]:
        qs = Chatbot.objects.filter(
            business__owner=self.request.user
        ).select_related("business")
        if self.action != "list":
            qs = qs.prefetch_related("nodes__options")
        return qs


class NodeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self) -> type:
        if self.action in ("create", "update", "partial_update"):
            return NodeWriteSerializer
        return NodeSerializer

    def get_queryset(self) -> QuerySet[Node]:
        return (
            Node.objects.filter(chatbot__business__owner=self.request.user)
            .select_related("chatbot")
            .prefetch_related("options")
        )


class OptionViewSet(viewsets.ModelViewSet):
    serializer_class = OptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Option]:
        return Option.objects.filter(
            node__chatbot__business__owner=self.request.user
        ).select_related("node", "next_node")
