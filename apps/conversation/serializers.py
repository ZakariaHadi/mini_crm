from rest_framework import serializers

from .models import Conversation


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = [
            "id",
            "business",
            "user_phone",
            "data",
            "completed_at",
            "created_at",
        ]
        read_only_fields = fields
