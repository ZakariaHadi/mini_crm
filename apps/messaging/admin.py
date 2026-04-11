from django.contrib import admin

from .models import OutgoingMessage


@admin.register(OutgoingMessage)
class OutgoingMessageAdmin(admin.ModelAdmin):
    list_display = ("phone", "status", "retry_count", "created_at")
    list_filter = ("status",)
    search_fields = ("phone", "provider_message_id")
    readonly_fields = ("content", "provider_message_id", "error_detail", "created_at")
