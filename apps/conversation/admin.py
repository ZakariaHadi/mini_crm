from django.contrib import admin

from .models import Conversation


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("pk", "business", "user_phone", "completed_at")
    list_filter = ("business",)
    search_fields = ("user_phone",)
    readonly_fields = ("data", "completed_at", "created_at")
