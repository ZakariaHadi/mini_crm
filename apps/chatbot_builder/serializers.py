from __future__ import annotations

from typing import Any

from rest_framework import serializers

from .models import Chatbot, Node, Option


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = [
            "id",
            "type",
            "label",
            "value",
            "next_node",
            "action",
            "order",
        ]


class NodeSerializer(serializers.ModelSerializer):
    options: OptionSerializer = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Node
        fields = [
            "id",
            "type",
            "content",
            "is_start",
            "options",
        ]


class NodeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = [
            "id",
            "chatbot",
            "type",
            "content",
            "is_start",
        ]
        read_only_fields = ["id"]


class ChatbotSerializer(serializers.ModelSerializer):
    nodes: NodeSerializer = NodeSerializer(many=True, read_only=True)

    class Meta:
        model = Chatbot
        fields = [
            "id",
            "business",
            "name",
            "is_active",
            "enable_back",
            "enable_restart",
            "nodes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        request = self.context.get("request")
        if request and not request.user.businesses.filter(
            pk=attrs.get("business", getattr(self.instance, "business_id", None))
        ).exists():
            raise serializers.ValidationError(
                {"business": "You do not own this business."}
            )
        return attrs


class ChatbotListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views — no nested nodes."""

    class Meta:
        model = Chatbot
        fields = [
            "id",
            "business",
            "name",
            "is_active",
            "created_at",
        ]
