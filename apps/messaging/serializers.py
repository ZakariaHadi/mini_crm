from rest_framework import serializers

from .models import OutgoingMessage


class OutgoingMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutgoingMessage
        fields = [
            "id",
            "phone",
            "content",
            "status",
            "retry_count",
            "provider_message_id",
            "error_detail",
            "created_at",
        ]
        read_only_fields = fields
