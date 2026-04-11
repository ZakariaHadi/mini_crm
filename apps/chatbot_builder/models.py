from django.db import models

from apps.common.models import TimeStampedModel


class Chatbot(TimeStampedModel):
    business = models.ForeignKey(
        "accounts.Business",
        on_delete=models.CASCADE,
        related_name="chatbots",
        verbose_name="Business",
    )
    name = models.CharField(max_length=255, verbose_name="Chatbot Name")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    enable_back = models.BooleanField(
        default=True,
        verbose_name="Enable Back Navigation",
    )
    enable_restart = models.BooleanField(
        default=True,
        verbose_name="Enable Restart Command",
    )

    class Meta(TimeStampedModel.Meta):
        verbose_name = "chatbot"
        verbose_name_plural = "chatbots"
        constraints = [
            models.UniqueConstraint(
                fields=["business"],
                condition=models.Q(is_active=True),
                name="unique_active_chatbot_per_business",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.business})"


class Node(TimeStampedModel):
    class NodeType(models.TextChoices):
        MENU = "menu", "Menu"
        TEXT = "text", "Text"
        TEMPLATE = "template", "Template"
        FLOW = "flow", "Flow"
        ACTION = "action", "Action"
        END = "end", "End"

    chatbot = models.ForeignKey(
        Chatbot,
        on_delete=models.CASCADE,
        related_name="nodes",
        verbose_name="Chatbot",
    )
    type = models.CharField(
        max_length=20,
        choices=NodeType.choices,
        verbose_name="Node Type",
    )
    content = models.JSONField(
        default=dict,
        verbose_name="Node Content",
        help_text="Flexible JSON content depending on node type.",
    )
    is_start = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Start Node",
    )

    class Meta(TimeStampedModel.Meta):
        verbose_name = "node"
        verbose_name_plural = "nodes"
        indexes = [
            models.Index(fields=["chatbot", "type"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["chatbot"],
                condition=models.Q(is_start=True),
                name="unique_start_node_per_chatbot",
            ),
        ]

    def __str__(self) -> str:
        return f"Node {self.pk} [{self.type}] — {self.chatbot.name}"


class Option(TimeStampedModel):
    class OptionType(models.TextChoices):
        TEXT = "text", "Text"
        BUTTON = "button", "Button"
        LIST = "list", "List"
        CHECKBOX = "checkbox", "Checkbox"

    node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="Parent Node",
    )
    type = models.CharField(
        max_length=20,
        choices=OptionType.choices,
        verbose_name="Option Type",
    )
    label = models.CharField(max_length=255, verbose_name="Label")
    value = models.CharField(max_length=50, verbose_name="Value")
    next_node = models.ForeignKey(
        Node,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incoming_options",
        verbose_name="Next Node",
    )
    action = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Action Payload",
        help_text="Optional action to trigger when this option is selected.",
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Display Order",
    )

    class Meta(TimeStampedModel.Meta):
        verbose_name = "option"
        verbose_name_plural = "options"
        ordering = ["order", "pk"]
        indexes = [
            models.Index(fields=["node", "value"]),
        ]

    def __str__(self) -> str:
        return f"{self.value}: {self.label}"
