from django.contrib import admin

from .models import Chatbot, Node, Option


class NodeInline(admin.TabularInline):
    model = Node
    extra = 0
    show_change_link = True


class OptionInline(admin.TabularInline):
    model = Option
    extra = 0
    fk_name = "node"


@admin.register(Chatbot)
class ChatbotAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "business__name")
    inlines = [NodeInline]


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ("pk", "chatbot", "type", "is_start")
    list_filter = ("type", "is_start")
    inlines = [OptionInline]


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ("label", "value", "type", "node", "next_node", "order")
    list_filter = ("type",)
