from __future__ import annotations

from typing import Any

from rest_framework import serializers

from .models import Business


class BusinessSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Business
        fields = [
            "id",
            "name",
            "whatsapp_phone_number_id",
            "whatsapp_number",
            "owner",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data: dict[str, Any]) -> Business:
        return super().create(validated_data)
