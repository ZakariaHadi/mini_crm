from __future__ import annotations

from typing import Any

from apps.chatbot_builder.models import Node


def render_node(node: Node) -> str | dict[str, Any]:
    """
    Render a Node into a WhatsApp-ready payload.
    Returns plain text for simple messages, or a dict for structured payloads.
    """
    renderer = _RENDERERS.get(node.type)
    if renderer is None:
        return node.content.get("text", "")
    return renderer(node)


def _render_text(node: Node) -> str:
    return node.content.get("text", "")


def _render_menu(node: Node) -> str:
    lines = [node.content.get("text", ""), ""]
    for opt in node.options.all().order_by("order", "pk"):
        lines.append(f"{opt.value} - {opt.label}")
    lines.append("")
    lines.append("0 - Retour")
    return "\n".join(lines)


def _render_template(node: Node) -> dict[str, Any]:
    return {
        "type": "template",
        "template_name": node.content["template_name"],
        "language": node.content.get("language", "fr"),
    }


def _render_flow(node: Node) -> dict[str, Any]:
    return {
        "type": "flow",
        "flow_id": node.content["flow_id"],
    }


_RENDERERS: dict[str, Any] = {
    Node.NodeType.TEXT: _render_text,
    Node.NodeType.MENU: _render_menu,
    Node.NodeType.TEMPLATE: _render_template,
    Node.NodeType.FLOW: _render_flow,
}
