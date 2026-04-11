from django.contrib import admin

from .models import Business


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ("name", "whatsapp_number", "owner", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "whatsapp_number")
    raw_id_fields = ("owner",)
